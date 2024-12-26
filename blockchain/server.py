import hashlib
import sys
import threading
import time
import random
import base64
import json

import rsa

from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class Transaction:
    def __init__(self, sender, message, timestamp=None):
        self.sender = sender
        self.message = message
        self.timestamp = timestamp or int(time.time())
    
    def __repr__(self):  
        return '{ "sender": "%s", "message": "%s", "timestamp": "%s" }' % (
            self.sender, self.message, self.timestamp)

    def to_dict(self):
        return {
            'sender': self.sender,
            'message': self.message,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data['sender'], data['message'])

class Block:
    def __init__(self, previous_hash, difficulty, miner, miner_rewards):
        self.previous_hash = previous_hash
        self.hash = ''
        self.difficulty = difficulty
        self.nonce = 0
        self.timestamp = int(time.time())
        self.transactions = []
        self.miner = miner
        self.miner_rewards = miner_rewards

    def __repr__(self):  
        return '{ "hash": "%s", "transactions": %s }' % (self.hash, str(self.transactions))
    
    def to_dict(self):
        """將 Block 轉換為字典格式以便 JSON 序列化"""
        return {
            'previous_hash': self.previous_hash,
            'hash': self.hash,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'miner': self.miner,
            'miner_rewards': self.miner_rewards
        }

class BlockChain:
    def __init__(self):
        self.adjust_difficulty_blocks = 10
        self.difficulty = 1
        self.block_time = 3
        self.miner_rewards = 10
        self.block_limitation = 5
        self.chain = []
        self.pending_transactions = []

        self.receive_verified_block = False
        self.authorized_senders = set()  # 儲存已授權的發送者公鑰

    def create_genesis_block(self):
        print("Create genesis block...")
        new_block = Block('IoT Final!', self.difficulty, '暖暖豬', self.miner_rewards)
        new_block.hash = self.get_hash(new_block, 0)
        self.chain.append(new_block)

    def initialize_transaction(self, sender, message):
        new_transaction = Transaction(sender, message)
        return new_transaction

    def transaction_to_string(self, transaction):
        transaction_dict = {
            'sender': str(transaction.sender),
            'message': transaction.message
        }
        return str(transaction_dict)

    def get_transactions_string(self, block):
        transaction_str = ''
        for transaction in block.transactions:
            transaction_str += self.transaction_to_string(transaction)
        return transaction_str

    def get_hash(self, block, nonce):
        s = hashlib.sha1()
        s.update(
            (
                block.previous_hash
                + str(block.timestamp)
                + self.get_transactions_string(block)
                + str(nonce)
            ).encode("utf-8")
        )
        h = s.hexdigest()
        return h

    def add_transaction_to_block(self, block):
        if len(self.pending_transactions) > self.block_limitation:
            transaction_accepted = self.pending_transactions[:self.block_limitation]
            self.pending_transactions = self.pending_transactions[self.block_limitation:]
        else:
            transaction_accepted = self.pending_transactions
            self.pending_transactions = []
        block.transactions = transaction_accepted

    def mine_block(self, miner):
        start = time.process_time()

        last_block = self.chain[-1]
        new_block = Block(last_block.hash, self.difficulty, miner, self.miner_rewards)

        self.add_transaction_to_block(new_block)
        new_block.previous_hash = last_block.hash
        new_block.difficulty = self.difficulty
        new_block.hash = self.get_hash(new_block, new_block.nonce)
        new_block.nonce = random.getrandbits(32)

        while new_block.hash[0: self.difficulty] != '0' * self.difficulty:
            new_block.nonce += 1
            new_block.hash = self.get_hash(new_block, new_block.nonce)
            if self.receive_verified_block:
                print(f"[**] Verified received block. Mine next!")
                self.receive_verified_block = False
                return False

        time_consumed = round(time.process_time() - start, 5)
        print(f"Hash: {new_block.hash} @ diff {self.difficulty}; {time_consumed}s")
        self.chain.append(new_block)

    def adjust_difficulty(self):
        if len(self.chain) % self.adjust_difficulty_blocks != 1:
            return self.difficulty
        elif len(self.chain) <= self.adjust_difficulty_blocks:
            return self.difficulty
        else:
            start = self.chain[-1*self.adjust_difficulty_blocks-1].timestamp
            finish = self.chain[-1].timestamp
            average_time_consumed = round((finish - start) / (self.adjust_difficulty_blocks), 2)
            # if average_time_consumed > self.block_time:
            if self.difficulty == 6:
                # print(f"Average block time:{average_time_consumed}s. Lower the difficulty")
                # self.difficulty -= 1
                print(f"Average block time:{average_time_consumed}s.")
                self.difficulty += 0
            else:
                # print(f"Average block time:{average_time_consumed}s. High up the difficulty")
                print(f"Average block time:{average_time_consumed}s.")
                self.difficulty += 1

    def get_balance(self, account):
        return 999999

    def verify_blockchain(self):
        previous_hash = ''
        for idx,block in enumerate(self.chain):
            if self.get_hash(block, block.nonce) != block.hash:
                print("Error:Hash not matched!")
                return False
            elif previous_hash != block.previous_hash and idx:
                print("Error:Hash not matched to previous_hash")
                return False
            previous_hash = block.hash
        print("Hash correct!")
        return True

    def add_transaction(self, transaction, signature):
        """驗證並添加交易"""
        # 檢查發送者是否已授權
        if transaction.sender not in self.authorized_senders:
            return False, "Sender not authorized!"

        # 驗證簽名
        public_key = '-----BEGIN RSA PUBLIC KEY-----\n'
        public_key += transaction.sender
        public_key += '\n-----END RSA PUBLIC KEY-----\n'
        public_key_pkcs = rsa.PublicKey.load_pkcs1(public_key.encode('utf-8'))
        
        # 生成交易字符串（包含時間戳以防重放攻擊）
        transaction_str = self.transaction_to_string(transaction)
        
        try:
            # 驗證簽名
            rsa.verify(transaction_str.encode('utf-8'), signature, public_key_pkcs)
            
            # 檢查是否是重複交易
            for pending_tx in self.pending_transactions:
                if (pending_tx.sender == transaction.sender and 
                    pending_tx.message == transaction.message and 
                    abs(pending_tx.timestamp - transaction.timestamp) < 300):  # 5分鐘內的相同交易視為重複
                    return False, "Duplicate transaction!"
            
            self.pending_transactions.append(transaction)
            return True, "Transaction authorized successfully!"
        except Exception as e:
            return False, f"RSA Verification failed: {str(e)}"

    def mining(self):
        address, private = self.generate_address()
        print(f"Miner address: {address}")
        print(f"Miner private: {private}")

        while(True):
            self.mine_block(address)
            self.adjust_difficulty()

    def start(self):
        if len(sys.argv) < 3:
            self.create_genesis_block()

        thread = threading.Thread(target=self.mining)
        thread.start()

    # def request_balance(self, data):
    #     try:
    #         address = data["address"]
    #         balance = self.get_balance(address)
    #         response = {
    #             "address": address,
    #             "balance": balance,
    #             "message": "success"
    #         }

    #         return response
    #     except:
    #         print("Cannot Request Balance!")
    #         return { "message": "error" }

    def request_chain(self):
        """修改這個方法來返回可序列化的數據"""
        clean_chain = [block.to_dict() for block in self.chain]
        
        response = {
            "chain": clean_chain
        }

        return response
    
    # def request_transaction(self, data):
    #     try:
    #         new_transaction = Transaction.from_dict(data["data"])

    #         result, result_message = self.add_transaction(
    #             new_transaction,
    #             base64.b64decode(data["signature"].encode("utf-8"))
    #         )

    #         response = {
    #             "data": result,
    #             "message": result_message
    #         }

    #         return response
    #     except Exception as e:
    #         print("Cannot Add Transaction!")
    #         print(e)
    #         return { "message": "error" }
        
    def generate_address(self):
        public, private = rsa.newkeys(512)
        public_key = public.save_pkcs1()
        private_key = private.save_pkcs1()
        return self.get_address_from_public(public_key), \
            self.extract_from_private(private_key)

    def get_address_from_public(self, public):
        address = str(public).replace('\\n','')
        address = address.replace("b'-----BEGIN RSA PUBLIC KEY-----", '')
        address = address.replace("-----END RSA PUBLIC KEY-----'", '')
        return address

    def extract_from_private(self, private):
        private_key = str(private).replace('\\n','')
        private_key = private_key.replace("b'-----BEGIN RSA PRIVATE KEY-----", '')
        private_key = private_key.replace("-----END RSA PRIVATE KEY-----'", '')
        return private_key

    def add_authorized_sender(self, public_key):
        """添加授權的發送者"""
        self.authorized_senders.add(public_key)
        return True

@app.route('/')
def hello_world():
    return 'Hello World'

# @app.route('/get_balance', methods=['GET'])
# def get_balance():
#     if request.method == 'GET':
#         req = request.get_json()
#         res = block.request_balance(req)

#         return res

@app.route('/transaction', methods=['POST'])
def transaction():
    if request.method == 'POST':
        try:
            req = request.get_json()
            # 從請求中獲取交易數據
            transaction_data = req.get("data")
            signature = req.get("signature")
            
            if not transaction_data or not signature:
                return {
                    "success": False,
                    "message": "Missing transaction data or signature"
                }
            
            # 創建交易對象
            new_transaction = Transaction.from_dict(transaction_data)
            
            # 解碼簽名
            decoded_signature = base64.b64decode(signature.encode("utf-8"))
            
            # 添加交易並獲取結果
            success, message = block.add_transaction(new_transaction, decoded_signature)
            
            return {
                "success": success,
                "message": message
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing transaction: {str(e)}"
            }

@app.route('/get_chain', methods=['GET'])
def get_chain():
    if request.method == 'GET':
        res = block.request_chain()
        return json.dumps(res)  # 確保返回的是 JSON 字符串

@app.route('/register_sender', methods=['POST'])
def register_sender():
    if request.method == 'POST':
        try:
            data = request.get_json()
            public_key = data.get('public_key')
            if not public_key:
                return {
                    "success": False,
                    "message": "Public key is required"
                }
            
            success = block.add_authorized_sender(public_key)
            return {
                "success": success,
                "message": "Sender registered successfully" if success else "Registration failed"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

if __name__ == '__main__':
    block = BlockChain()
    block.start()

    app.run(host='0.0.0.0', port=8000, debug=False)
