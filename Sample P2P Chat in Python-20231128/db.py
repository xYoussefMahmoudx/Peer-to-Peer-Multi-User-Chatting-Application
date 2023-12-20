from pymongo import MongoClient
from cryptography.fernet import Fernet
import base64
# Includes database operations
class DB:


    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['p2p-chat']


    # checks if an account with the username exists
    def is_account_exist(self, username):
        user_exists = self.db.accounts.find_one({'username': username})
        if user_exists is not None:
            return True
        else:
            return False
    

    # registers a user
    def register(self, username, password):
        custom_key_bytes = b'qwertyuiopasdfghjklzxcvbnmmnbvcx'
        custom_key = base64.urlsafe_b64encode(custom_key_bytes)
        cipher = Fernet(custom_key)
        encoded_data = password.encode()  # Convert string to bytes before encryption
        encrypted_data = cipher.encrypt(encoded_data)
        account = {
            "username": username,
            "password": encrypted_data
        }
        self.db.accounts.insert_one(account)


    # retrieves the password for a given username
    def get_password(self, username):
        custom_key_bytes = b'qwertyuiopasdfghjklzxcvbnmmnbvcx'
        custom_key = base64.urlsafe_b64encode(custom_key_bytes)
        cipher = Fernet(custom_key)
        encrypted_data = self.db.accounts.find_one({"username": username})["password"]
        decrypted_data = cipher.decrypt(encrypted_data)
        decrypted_data_string = decrypted_data.decode()
        return decrypted_data_string


    # checks if an account with the username online
    def is_account_online(self, username):
        if self.db.online_peers.find_one({"username": username}) is not None:
            return True
        else:
            return False

    
    # logs in the user
    def user_login(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert_one(online_peer)
    

    # logs out the user 
    def user_logout(self, username):
        self.db.online_peers.delete_one({"username": username})


    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, username):
        res = self.db.online_peers.find_one({"username": username})
        return (res["ip"], res["port"])