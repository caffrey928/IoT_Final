import requests
import json
import base64
import rsa
import time
import sys

class BlockchainTester:
    def __init__(self, server_url="http://192.168.50.175:8000"):
        self.server_url = server_url
        self.public_key = rsa.PublicKey(10048947812472266664638391495251721679601827544331931703009324071175416385290118553345010548316624398410509311915206366936222993532193604244306989089885931,65537)
        self.private_key = rsa.PrivateKey(10048947812472266664638391495251721679601827544331931703009324071175416385290118553345010548316624398410509311915206366936222993532193604244306989089885931, 65537, 7211837762055336532105560303151951988623103845462991527218831322209813296173993946645941071026441913830948672513013751343518680825478660355207467988842577, 5833660642847181891774551351110650120823777978300501751423186888902970407278395693, 1722580113533612705701464771087061713001070058172718180160419971921096567)
        
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
    payload_sensor = {"temperature": data[0], "humidity": data[1], "PM2.5": data[2]}
    messages = [
        str(payload_sensor)
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
