
'''
    ##  Implementation of registry
    ##  150114822 - Eren Ulaş
'''
import hashlib
from socket import *
import threading
import select
import logging
import db
from colorama import Fore, init


init(autoreset=True)

# This class is used to process the peer messages sent to registry
# for each peer connected to registry, a new client thread is created
class ClientThread(threading.Thread):
    # initializations for client thread
    def __init__(self, ip, port, tcpClientSocket):
        threading.Thread.__init__(self)
        # ip of the connected peer
        self.ip = ip
        # port number of the connected peer
        self.port = port
        # socket of the peer
        self.tcpClientSocket = tcpClientSocket
        # username, online status, and udp server initializations
        self.username = None
        self.isOnline = True
        self.udpServer = None


        # Phase 3

        # Print thread start message in green
        print(f"{Fore.GREEN}New thread started for {ip}:{port}")

    # main of the thread
    def run(self):
        # locks for thread which will be used for thread synchronization
        self.lock = threading.Lock()
        print(f"{Fore.GREEN}Connection from: {self.ip}:{self.port}")
        print(f"{Fore.GREEN}IP Connected: {self.ip}")

        while True:
            try:
                # waits for incoming messages from peers
                message = self.tcpClientSocket.recv(1024).decode().split()
                logging.info(f"{Fore.GREEN}Received from {self.ip}:{str(self.port)} -> {' '.join(message)}")
                #   JOIN    #
                if message[0] == "JOIN":
                    # join-exist is sent to peer,
                    # if an account with this username already exists
                    if db.is_account_exist(message[1]):
                        response = "join-exist"
                        print(f"From-> {self.ip}:{self.port} {Fore.RED}{response}")
                        logging.info(f"{Fore.RED}Send to {self.ip}:{str(self.port)} -> {response}")
                        self.tcpClientSocket.send(response.encode())
                    # join-success is sent to peer,
                    # if an account with this username is not exist, and the account is created
                    else:
                        db.register(message[1], message[2])
                        response = "join-success"
                        logging.info(f"{Fore.GREEN}Send to {self.ip}:{str(self.port)} -> {response}")
                        self.tcpClientSocket.send(response.encode())
                #   LOGIN    #
                elif message[0] == "LOGIN":
                    # login-account-not-exist is sent to peer,
                    # if an account with the username does not exist
                    if not db.is_account_exist(message[1]):
                        response = "login-account-not-exist"
                        logging.info(f"{Fore.RED}Send to {self.ip}:{str(self.port)} -> {response}")
                        self.tcpClientSocket.send(response.encode())
                    # login-online is sent to peer,
                    # if an account with the username already online
                    elif db.is_account_online(message[1]):
                        response = "login-online"
                        logging.info(f"{Fore.RED}Send to {self.ip}:{str(self.port)} -> {response}")
                        self.tcpClientSocket.send(response.encode())
                    # login-success is sent to peer,
                    # if an account with the username exists and not online
                    else:
                        # retrieves the account's password, and checks if the one entered by the user is correct
                        retrievedPass = db.get_password(message[1])
                        new_password = hashlib.sha256(message[2].encode('utf-8')).hexdigest()
                        # if password is correct, then peer's thread is added to threads list
                        # peer is added to db with its username, port number, and ip address
                        if retrievedPass == new_password:
                            self.username = message[1]
                            self.lock.acquire()
                            try:
                                tcpThreads[self.username] = self
                            finally:
                                self.lock.release()

                            db.user_login(message[1], self.ip, message[3])
                            # login-success is sent to peer,
                            # and a udp server thread is created for this peer, and thread is started
                            # timer thread of the udp server is started
                            response = "login-success"
                            logging.info(f"{Fore.GREEN}Send to {self.ip}:{str(self.port)} -> {response}")
                            self.tcpClientSocket.send(response.encode())
                            self.udpServer = UDPServer(self.username, self.tcpClientSocket)
                            self.udpServer.start()
                            self.udpServer.timer.start()
                        # if password not matches and then login-wrong-password response is sent
                        else:
                            response = "login-wrong-password"
                            logging.info(f"{Fore.RED}Send to {self.ip}:{str(self.port)} -> {response}")
                            self.tcpClientSocket.send(response.encode())
                #   LOGOUT  #
                elif message[0] == "LOGOUT":
                    # if user is online,
                    # removes the user from onlinePeers list
                    # and removes the thread for this user from tcpThreads
                    # socket is closed and timer thread of the udp for this
                    # user is cancelled
                    if len(message) > 1 and message[1] is not None and db.is_account_online(message[1]):
                        db.user_logout(message[1])
                        self.lock.acquire()
                        try:
                            if message[1] in tcpThreads:
                                del tcpThreads[message[1]]
                        finally:
                            self.lock.release()
                        print(f"{self.ip}:{self.port} {Fore.RED}is logged out")
                        self.tcpClientSocket.close()
                        self.udpServer.timer.cancel()
                        break
                    else:
                        self.tcpClientSocket.close()
                        break
                #   SEARCH  #
                elif message[0] == "SEARCH":
                    # checks if an account with the username exists
                    if db.is_account_exist(message[1]):
                        # checks if the account is online
                        # and sends the related response to peer
                        if db.is_account_online(message[1]):
                            peer_info = db.get_peer_ip_port(message[1])
                            response = f"search-success {peer_info[0]}:{peer_info[1]}"
                            logging.info(f"{Fore.GREEN}Send to {self.ip}:{str(self.port)} -> {response}")
                            self.tcpClientSocket.send(response.encode())
                        else:
                            response = "search-user-not-online"
                            logging.info(f"{Fore.RED}Send to {self.ip}:{str(self.port)} -> {response}")
                            self.tcpClientSocket.send(response.encode())
                    # enters if username does not exist
                    else:
                        response = "search-user-not-found"
                        logging.info(f"{Fore.RED}Send to {self.ip}:{str(self.port)} -> {response}")
                        self.tcpClientSocket.send(response.encode())

                #  CHAT ROOM CREATION  #
                elif message[0] == "CREATE_CHAT_ROOM":
                    if db.is_chat_room_exist(message[1]):
                        response = "chat-room-exists"
                        logging.info(f"{Fore.RED}Send to {self.ip}:{str(self.port)} -> {response}")
                        self.tcpClientSocket.send(response.encode())
                    else:
                        response = "chat-room-creation-successful"
                        logging.info(f"{Fore.GREEN}Send to {self.ip}:{str(self.port)} -> {response}")
                        self.tcpClientSocket.send(response.encode())
                        db.create_chat_room(message[1])
                #  CHAT ROOM JOINING  #
                elif message[0] == "JOIN_CHAT_ROOM":
                    if db.is_chat_room_exist(message[1]):
                        response = "chat-room-found"
                        logging.info(f"{Fore.RED}Send to {self.ip}:{str(self.port)} -> {response}")
                        response += " " + db.get_chat_room_participants(message[1])
                        self.tcpClientSocket.send(response.encode())
                        db.join_chat_room(message[1],message[2])
                    else:
                        response = "chat-room-not-found"
                        logging.info(f"{Fore.RED}Send to {self.ip}:{str(self.port)} -> {response}")
                        self.tcpClientSocket.send(response.encode())
                # CHAT ROOM LIST #
                elif message[0] == "GET_CHAT_ROOM_LIST":
                    response = "chat-room-list"
                    response += " " + db.get_chat_room_participants(message[1])
                    self.tcpClientSocket.send(response.encode())
                # CHAT ROOM QUITTING #
                elif message[0] == "QUIT_CHAT_ROOM":
                    response = "chat-room-quit" 
                    db.remove_chat_room_user(message[2],message[1])
                    self.tcpClientSocket.send(response.encode())


            except OSError as oErr:
                logging.error(f"{Fore.RED}OSError: {oErr}")


    # function for resettin the timeout for the udp timer thread
    def resetTimeout(self):
        self.udpServer.resetTimer()


# implementation of the udp server thread for clients
class UDPServer(threading.Thread):


    # udp server thread initializations
    def __init__(self, username, clientSocket):
        threading.Thread.__init__(self)
        self.username = username
        # timer thread for the udp server is initialized
        self.timer = threading.Timer(3, self.waitHelloMessage)
        self.tcpClientSocket = clientSocket


    # if hello message is not received before timeout
    # then peer is disconnected
    def waitHelloMessage(self):
        if self.username is not None:
            db.user_logout(self.username)
            db.remove_chat_room_user(self.username) # Remove user from any chat rooms they were in.
            if self.username in tcpThreads:
                del tcpThreads[self.username]
        self.tcpClientSocket.close()
        print(f"Removed {Fore.RED}{self.username} from online peers")

    def send_chatroom_users(self,room_name):
        return db.get_chat_room_participants(room_name)




    # resets the timer for udp server
    def resetTimer(self):
        self.timer.cancel()
        self.timer = threading.Timer(1500, self.waitHelloMessage)
        self.timer.start()


# tcp and udp server port initializations
print("Registy started...")
port = 15501
portUDP = 15401

# db initialization:q
db = db.DB()

# gets the ip address of this peer
# first checks to get it for windows devices
# if the device that runs this application is not windows
# it checks to get it for macos devices
hostname=gethostname()
try:
    host=gethostbyname(hostname)
except gaierror:
    import netifaces as ni
    host = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']


print(f"{Fore.GREEN}Registry IP address: {host}")
print(f"{Fore.GREEN}Registry port number: {str(port)}")

# onlinePeers list for online account
onlinePeers = {}
# accounts list for accounts
accounts = {}
# tcpThreads list for online client's thread
tcpThreads = {}

#tcp and udp socket initializations
tcpSocket = socket(AF_INET, SOCK_STREAM)
udpSocket = socket(AF_INET, SOCK_DGRAM)
tcpSocket.bind((host,port))
udpSocket.bind((host,portUDP))
tcpSocket.listen(5)

# input sockets that are listened
inputs = [tcpSocket, udpSocket]

# log file initialization
logging.basicConfig(filename="registry.log", level=logging.INFO)

# as long as at least a socket exists to listen registry runs
while inputs:

    print(f"{Fore.GREEN}Listening for incoming connections...")
    # monitors for the incoming connections
    readable, writable, exceptional = select.select(inputs, [], [])
    for s in readable:
        # if the message received comes to the tcp socket
        # the connection is accepted and a thread is created for it, and that thread is started
        if s is tcpSocket:
            tcpClientSocket, addr = tcpSocket.accept()
            newThread = ClientThread(addr[0], addr[1], tcpClientSocket)
            newThread.start()
        # if the message received comes to the udp socket
        elif s is udpSocket:
            # received the incoming udp message and parses it
            message, clientAddress = s.recvfrom(1024)
            message = message.decode().split()
            # checks if it is a hello message
            if message[0] == "HELLO":
                # checks if the account that this hello message
                # is sent from is online
                if message[1] in tcpThreads:
                    # resets the timeout for that peer since the hello message is received
                    tcpThreads[message[1]].resetTimeout()
                    print(f"Hello is received from {Fore.GREEN}{message[1]}")
                    logging.info(f"{Fore.GREEN}Received from {clientAddress[0]}:{str(clientAddress[1])} -> {' '.join(message)}")

# registry tcp socket is closed
tcpSocket.close()

