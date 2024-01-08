from pymongo import MongoClient
import hashlib
import unittest
from colorama import Fore, Style, init
from db import DB


class TestDBManual(unittest.TestCase):

    def setUp(self):
        # Connect to the test database
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['test-p2p-chat']
        self.db.accounts.drop()
        self.db.online_peers.drop()
        self.db.chat_rooms.drop()

        # Initialize the DB instance
        self.db_instance = DB()

    def tearDown(self):
        # Drop the collections after each test
        self.db.accounts.drop()
        self.db.online_peers.drop()
        self.db.chat_rooms.drop()
        
        
        if self._outcome.success:
            print(f"{Fore.GREEN + Style.BRIGHT}Test passed successfully")
        else:
            print(f"{Fore.RED + Style.BRIGHT}Some Tests have failed.")

    def test_register_and_get_password(self):
        # Test user registration and password retrieval
        username = 'test_user'
        password = 'test_password'
        self.db_instance.register(username, password)

        # Check if the account exists
        self.assertTrue(self.db_instance.is_account_exist(username))

        # Check if the password is correct
        stored_password = self.db_instance.get_password(username)
        expected_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        self.assertEqual(stored_password, expected_password)

    def test_user_login_and_logout(self):
        # Test user login and logout
        username = 'test_user'
        ip = '192.168.1.1'
        port = '1234'

        # User login
        self.db_instance.user_login(username, ip, port)
        self.assertTrue(self.db_instance.is_account_online(username))

        # Get peer IP and port
        stored_ip, stored_port = self.db_instance.get_peer_ip_port(username)
        self.assertEqual(stored_ip, ip)
        self.assertEqual(stored_port, port)

        # User logout
        self.db_instance.user_logout(username)
        self.assertFalse(self.db_instance.is_account_online(username))

    def test_create_and_join_chat_room(self):
        # Test chat room creation and joining
        room_name = 'test_room'
        username = 'test_user'

        # Create a chat room
        self.db_instance.create_chat_room(room_name)
        self.assertTrue(self.db_instance.is_chat_room_exist(room_name))

        # Join the chat room
        self.db_instance.join_chat_room(room_name, username)
        participants = self.db_instance.get_chat_room_participants(room_name)
        self.assertIn(username, participants)

        # Remove user from chat room
        self.db_instance.remove_chat_room_user(room_name, username)
        updated_participants = self.db_instance.get_chat_room_participants(room_name)
        self.assertNotIn(username, updated_participants)
        
        


if __name__ == '__main__':
    unittest.main()
