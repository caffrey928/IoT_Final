import requests
import json
import base64
import rsa
import time
import sys

class BlockchainTester:
    def __init__(self, server_url="http://192.168.50.175:8000"):
        self.server_url = server_url
        self.public_key = rsa.PublicKey(7122932945098157357279636326045052075559622381757169139013779866390509569671420275920313266020962154482002208164227466505820315800423406336986371186720361, 65537)
        self.private_key = rsa.PrivateKey(7122932945098157357279636326045052075559622381757169139013779866390509569671420275920313266020962154482002208164227466505820315800423406336986371186720361, 65537, 2702143199734964801817085285230207130362441546839903247542008255461813156189621942640127974751773583489963720750041333907754356344062569214359060404743425, 4181948258498044566806837879380290047676297208130165095214164957528929454565728913, 1703257071778399661587845521971501214038413757641972848349467513445636697)
        
    def get_public_key_str(self):
        """獲取格式化的公鑰字符串"""
        public_key = self.public_key.save_pkcs1()
        public_key_str = str(public_key).replace('\\n','')
        public_key_str = public_key_str.replace("b'-----BEGIN RSA PUBLIC KEY-----", '')
        public_key_str = public_key_str.replace("-----END RSA PUBLIC KEY-----'", '')
        return public_key_str

    def register_sender(self):
        """註冊發送者"""
        url = f"{self.server_url}/register_sender"
        data = {
            "public_key": self.get_public_key_str()
        }
        response = requests.post(url, json=data)
        print("Register Sender Response:", response.json())
        return response.json()

    def create_and_sign_transaction(self, message):
        """創建並簽名交易"""
        # 建交易數據
        transaction_data = {
            "sender": self.get_public_key_str(),
            "message": message,
            "timestamp": int(time.time())
        }
        
        # 生成交易字符串
        transaction_str = str({
            "sender": transaction_data["sender"],
            "message": transaction_data["message"]
        })
        
        # 簽名
        signature = rsa.sign(
            transaction_str.encode('utf-8'),
            self.private_key,
            'SHA-1'
        )
        
        # Base64編碼簽名
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        return transaction_data, signature_b64

    def send_transaction(self, message):
        """發送交易"""
        url = f"{self.server_url}/transaction"
        transaction_data, signature = self.create_and_sign_transaction(message)
        
        data = {
            "data": transaction_data,
            "signature": signature
        }
        
        response = requests.post(url, json=data)
        print("Send Transaction Response:", response.json())
        return response.json()

    def get_chain(self):
        """獲取區塊鏈"""
        url = f"{self.server_url}/get_chain"
        response = requests.get(url)
        try:
            chain_data = response.json()
            print("\nBlockchain:")
            for block in chain_data["chain"]:
                print(f"Block Hash: {block['hash']}")
                print(f"Miner: {block['miner']}")
                print(f"Difficulty: {block['difficulty']}")
                if block['transactions']:
                    print("Transactions:")
                    for tx in block['transactions']:
                        print(f"  - From: {tx['sender'][:30]}...")
                        print(f"    Message: {tx['message']}")
                print("---")
            return chain_data
        except Exception as e:
            print(f"Error getting chain: {e}")
            print(f"Response text: {response.text}")
            return None

def main():
    tester = BlockchainTester()
    
    print("\n1. Testing Register Sender...")
    tester.register_sender()
    
    print("\n2. Testing Send Transaction...")
    # 發送多個交易
    data = sys.argv[1].replace("\n","").split(" ")
    messages_payload = {"id": data[0], "weight": data[1]}
    messages = [
        str(messages_payload)
    ]
    
    for message in messages:
        tester.send_transaction(message)
        time.sleep(1)  # 等待1秒
    
    print("\n3. Testing Get Chain...")
    # 等待一些區塊被挖出
    time.sleep(10)
    tester.get_chain()

if __name__ == "__main__":
    main() 
