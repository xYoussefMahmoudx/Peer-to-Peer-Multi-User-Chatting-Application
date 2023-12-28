'''
    ##  Implementation of peer
    ##  Each peer has a client and a server side that runs on different threads
    ##  150114822 - Eren Ulaş
'''

from socket import *
import threading
import time
import select
import logging
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Server side of peer
class PeerServer(threading.Thread):


    # Peer server initialization
    def __init__(self, username, peerServerPort):
        
        threading.Thread.__init__(self)
        
        # keeps the username of the peer
        self.username = username
        # tcp socket for peer server
        self.tcpServerSocket = socket(AF_INET, SOCK_STREAM)
        # port number of the peer server
        self.peerServerPort = peerServerPort
        # if 1, then user is already chatting with someone
        # if 0, then user is not chatting with anyone
        self.isChatRequested = 0
        # keeps the socket for the peer that is connected to this peer
        self.connectedPeerSocket = None
        # keeps the ip of the peer that is connected to this peer's server
        self.connectedPeerIP = None
        # keeps the port number of the peer that is connected to this peer's server
        self.connectedPeerPort = None
        # online status of the peer
        self.isOnline = True
        # keeps the username of the peer that this peer is chatting with
        self.chattingClientName = None
        # Tracks if the user is in a chat room
        self.inChatroom = False


    

    # main method of the peer server thread
    def run(self):

        print(f"{Fore.GREEN}Peer server started...{Style.RESET_ALL}")

        # gets the ip address of this peer
        # first checks to get it for windows devices
        # if the device that runs this application is not windows
        # it checks to get it for macos devices
        hostname=gethostname()
        try:
            self.peerServerHostname=gethostbyname(hostname)
        except gaierror:
            import netifaces as ni
            self.peerServerHostname = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

        # ip address of this peer
        #self.peerServerHostname = 'localhost'
        # socket initializations for the server of the peer
        self.tcpServerSocket.bind((self.peerServerHostname, self.peerServerPort))
        self.tcpServerSocket.listen(4)
        # inputs sockets that should be listened
        inputs = [self.tcpServerSocket]
        # server listens as long as there is a socket to listen in the inputs list and the user is online
        while inputs and self.isOnline:
            # monitors for the incoming connections
            try:
                readable, writable, exceptional = select.select(inputs, [], [])
                # If a server waits to be connected enters here
                for s in readable:
                    # if the socket that is receiving the connection is 
                    # the tcp socket of the peer's server, enters here
                    if s is self.tcpServerSocket:
                        # accepts the connection, and adds its connection socket to the inputs list
                        # so that we can monitor that socket as well
                        connected, addr = s.accept()
                        connected.setblocking(0)
                        inputs.append(connected)
                        # if the user is not chatting, then the ip and the socket of
                        # this peer is assigned to server variables
                        if self.isChatRequested == 0:     
                            print(f"{Fore.GREEN}{self.username} is connected from {str(addr)}{Style.RESET_ALL}")
                            self.connectedPeerSocket = connected
                            self.connectedPeerIP = addr[0]
                    # if the socket that receives the data is the one that
                    # is used to communicate with a connected peer, then enters here
                    else:
                        # message is received from connected peer
                        messageReceived = s.recv(1024).decode()
                        if "GROUP_CHAT " in messageReceived:
                            print(messageReceived[messageReceived.find("GROUP_CHAT "):])
                        # logs the received message
                        logging.info(f"{Fore.GREEN}Received from {str(self.connectedPeerIP)} -> {str(messageReceived)}")
                        # if message is a request message it means that this is the receiver side peer server
                        # so evaluate the chat request
                        if len(messageReceived) > 11 and messageReceived[:12] == "CHAT-REQUEST":
                            # text for proper input choices is printed however OK or REJECT is taken as input in main process of the peer
                            # if the socket that we received the data belongs to the peer that we are chatting with,
                            # enters here
                            if s is self.connectedPeerSocket:
                                # parses the message
                                messageReceived = messageReceived.split()
                                # gets the port of the peer that sends the chat request message
                                self.connectedPeerPort = int(messageReceived[1])
                                # gets the username of the peer sends the chat request message
                                self.chattingClientName = messageReceived[2]
                                # prints prompt for the incoming chat request
                                print(f"{Fore.GREEN}Incoming chat request from {self.chattingClientName} >> {Style.RESET_ALL}")
                                print(f"{Fore.CYAN}Enter OK to accept or REJECT to reject: {Style.RESET_ALL}")
                                # makes isChatRequested = 1 which means that peer is chatting with someone
                                self.isChatRequested = 1
                            # if the socket that we received the data does not belong to the peer that we are chatting with
                            # and if the user is already chatting with someone else(isChatRequested = 1), then enters here
                            elif s is not self.connectedPeerSocket and self.isChatRequested == 1:
                                # sends a busy message to the peer that sends a chat request when this peer is 
                                # already chatting with someone else
                                message = "BUSY"
                                s.send(message.encode())
                                # remove the peer from the inputs list so that it will not monitor this socket
                                inputs.remove(s)
                        # if an OK message is received then ischatrequested is made 1 and then next messages will be shown to the peer of this server
                        elif messageReceived == "OK":
                            self.isChatRequested = 1
                        # if an REJECT message is received then ischatrequested is made 0 so that it can receive any other chat requests
                        elif messageReceived == "REJECT":
                            self.isChatRequested = 0
                            inputs.remove(s)
                        # if a message is received, and if this is not a quit message ':q' and 
                        # if it is not an empty message, show this message to the user
                        elif messageReceived[:2] != ":q" and len(messageReceived)!= 0:
                            #print(self.chattingClientName + ": " + messageReceived)
                             print(f"{Fore.MAGENTA}{self.chattingClientName}  :   {messageReceived} {Style.RESET_ALL}")
                        # if the message received is a quit message ':q',
                        # makes ischatrequested 1 to receive new incoming request messages
                        # removes the socket of the connected peer from the inputs list
                        elif messageReceived[:2] == ":q":
                            self.isChatRequested = 0
                            inputs.clear()
                            inputs.append(self.tcpServerSocket)
                            # connected peer ended the chat
                            if len(messageReceived) == 2:
                                print(f"{Fore.RED}User you're chatting with ended the chat{Style.RESET_ALL}")
                                print(f"{Fore.CYAN}Press enter to quit the chat: {Style.RESET_ALL}")
                        # if the message is an empty one, then it means that the
                        # connected user suddenly ended the chat(an error occurred)
                        elif len(messageReceived) == 0:
                            self.isChatRequested = 0
                            inputs.clear()
                            inputs.append(self.tcpServerSocket)
                            print(f"{Fore.RED}User you're chatting with suddenly ended the chat{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}Press enter to quit the chat: {Style.RESET_ALL}")
            # handles the exceptions, and logs them
            except OSError as oErr:
                logging.error(f"{Fore.RED}OSError: 0.{format(oErr)}{Style.RESET_ALL}")
            except ValueError as vErr:
                logging.error(f"{Fore.RED}ValueError: {0}.{format(vErr)}{Style.RESET_ALL}")
            

# Client side of peer
class PeerClient(threading.Thread):
    # variable initializations for the client side of the peer
    def __init__(self, ipToConnect, portToConnect, username, peerServer, responseReceived,msg='None'):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.ipToConnect = ipToConnect
        # keeps the username of the peer
        self.username = username
        # keeps the port number that this client should connect
        self.portToConnect = portToConnect
        # client side tcp socket initialization
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived
        # keeps if this client is ending the chat or not
        self.isEndingChat = False
        self.msg = msg
  


    # main method of the peer client thread
    def run(self):
        
        print(f"{Fore.GREEN}Peer client started...")
        # connects to the server of other peer
        self.tcpClientSocket.connect((self.ipToConnect, self.portToConnect))
        # if the server of this peer is not connected by someone else and if this is the requester side peer client then enters here
        if self.msg is not None:
            requestMessage = "GROUP-CHAT " + self.username + " : " + self.msg
            self.tcpClientSocket.send(requestMessage.encode())
        elif self.peerServer.isChatRequested == 0 and self.responseReceived is None:
            # composes a request message and this is sent to server and then this waits a response message from the server this client connects
            requestMessage = "CHAT-REQUEST " + str(self.peerServer.peerServerPort)+ " " + self.username
            # logs the chat request sent to other peer
            logging.info(f"{Fore.GREEN}Send to   {self.ipToConnect}  :  {str(self.portToConnect)}   ->   {requestMessage}")
            # sends the chat request
            self.tcpClientSocket.send(requestMessage.encode())
            print(f"{Fore.GREEN}Request message {requestMessage} is sent...")
            # received a response from the peer which the request message is sent to
            self.responseReceived = self.tcpClientSocket.recv(1024).decode()
            # logs the received message
            logging.info(f"{Fore.GREEN}Received from  + {self.ipToConnect}  :  {str(self.portToConnect)}   ->   {self.responseReceived}")
            print("Response is " + self.responseReceived)
            # parses the response for the chat request
            self.responseReceived = self.responseReceived.split()
            # if response is ok then incoming messages will be evaluated as client messages and will be sent to the connected server
            if self.responseReceived[0] == "OK":
                # changes the status of this client's server to chatting
                self.peerServer.isChatRequested = 1
                # sets the server variable with the username of the peer that this one is chatting
                self.peerServer.chattingClientName = self.responseReceived[1]
                # as long as the server status is chatting, this client can send messages
                while self.peerServer.isChatRequested == 1:
                    # message input prompt
                    messageSent = input(self.username + ": ")
                    # sends the message to the connected peer, and logs it
                    self.tcpClientSocket.send(messageSent.encode())
                    logging.info(f"{Fore.GREEN}Send to   {self.ipToConnect}  :  {str(self.portToConnect)}  ->  + {messageSent}")
                    # if the quit message is sent, then the server status is changed to not chatting
                    # and this is the side that is ending the chat
                    if messageSent == ":q":
                        self.peerServer.isChatRequested = 0
                        self.isEndingChat = True
                        break
                # if peer is not chatting, checks if this is not the ending side
                if self.peerServer.isChatRequested == 0:
                    if not self.isEndingChat:
                        # tries to send a quit message to the connected peer
                        # logs the message and handles the exception
                        try:
                            self.tcpClientSocket.send(":q ending-side".encode())
                            logging.info(f"{Fore.GREEN}Send to   {self.ipToConnect}  :  {str(self.portToConnect)}   -> :q")
                        except BrokenPipeError as bpErr:
                            logging.error(f"BrokenPipeError: {0} .{format(bpErr)}")
                    # closes the socket
                    self.responseReceived = None
                    self.tcpClientSocket.close()
            # if the request is rejected, then changes the server status, sends a reject message to the connected peer's server
            # logs the message and then the socket is closed       
            elif self.responseReceived[0] == "REJECT":
                self.peerServer.isChatRequested = 0
                print("client of requester is closing...")
                self.tcpClientSocket.send("REJECT".encode())
                logging.info(f"{Fore.RED}Send to   {self.ipToConnect}  :  {str(self.portToConnect)}   -> REJECT")
                self.tcpClientSocket.close()
            # if a busy response is received, closes the socket
            elif self.responseReceived[0] == "BUSY":
                print(f"{Fore.RED}Receiver peer is busy")
                self.tcpClientSocket.close()
        # if the client is created with OK message it means that this is the client of receiver side peer
        # so it sends an OK message to the requesting side peer server that it connects and then waits for the user inputs.
        elif self.responseReceived == "OK":
            # server status is changed
            self.peerServer.isChatRequested = 1
            # ok response is sent to the requester side
            okMessage = "OK"
            self.tcpClientSocket.send(okMessage.encode())
            logging.info(f"{Fore.GREEN}Send to   {self.ipToConnect}  :  {str(self.portToConnect)}   ->  + {okMessage}")
            print(f"{Fore.GREEN}Client with OK message is created... and sending messages")
            # client can send messsages as long as the server status is chatting
            while self.peerServer.isChatRequested == 1:
                # input prompt for user to enter message
                messageSent = input(self.username + ": ")
                self.tcpClientSocket.send(messageSent.encode())
                logging.info(f"{Fore.GREEN}Send to   {self.ipToConnect}  :  {str(self.portToConnect)}   ->   {messageSent}")
                # if a quit message is sent, server status is changed
                if messageSent == ":q":
                    self.peerServer.isChatRequested = 0
                    self.isEndingChat = True
                    break
            # if server is not chatting, and if this is not the ending side
            # sends a quitting message to the server of the other peer
            # then closes the socket
            if self.peerServer.isChatRequested == 0:
                if not self.isEndingChat:
                    self.tcpClientSocket.send(":q ending-side".encode())
                    logging.info(f"{Fore.RED}Send to   {self.ipToConnect}  :  {str(self.portToConnect)}   -> :q")
                self.responseReceived = None
                self.tcpClientSocket.close()
                

# main process of the peer
class peerMain:

    # peer initializations
    def __init__(self):
        # ip address of the registry
        self.registryName = input("Enter IP address of registry: ")
        #self.registryName = 'localhost'
        # port number of the registry
        self.registryPort = 15600
        # tcp socket connection to registry
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.connect((self.registryName,self.registryPort))
        # initializes udp socket which is used to send hello messages
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        # udp port of the registry
        self.registryUDPPort = 15500
        # login info of the peer
        self.loginCredentials = (None, None)
        # online status of the peer
        self.isOnline = False
        # server port number of this peer
        self.peerServerPort = None
        # server of this peer
        self.peerServer = None
        # client of this peer
        self.peerClient = None
        # timer initialization
        self.timer = None
        # Tracks the current users in the chatroom
        self.chatroomUsers = []
        self.chatroomName = ''
        
        
        choice = "0"
        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        while choice != "3":
            # menu selection prompt
            choice = input(f"{Fore.CYAN}Choose: \nCreate account: 1\nLogin: 2\nLogout: 3\nSearch: 4\nStart a chat: 5\nCreate Chat-Room: 6\nJoin Chat-Room: 7\n")
            # if choice is 1, creates an account with the username
            # and password entered by the user
            if choice =="1":
                username = input(f"{Fore.CYAN}username: ")
                password = input(f"{Fore.CYAN}password: ")
                
                self.createAccount(username, password)
            # if choice is 2 and user is not logged in, asks for the username
            # and the password to login
            elif choice == "2" and not self.isOnline:
                username = input(f"{Fore.CYAN}username: ")
                password = input(f"{Fore.CYAN}password: ")
                # asks for the port number for server's tcp socket
                peerServerPort = int(input(f"{Fore.CYAN}Enter a port number for peer server: "))
                
                status = self.login(username, password, peerServerPort)
                # is user logs in successfully, peer variables are set
                if status == 1:
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort
                    # creates the server thread for this peer, and runs it
                    self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort)
                    self.peerServer.start()
                    # hello message is sent to registry
                    self.sendHelloMessage()
            # if choice is 3 and user is logged in, then user is logged out
            # and peer variables are set, and server and client sockets are closed
            elif choice == "3" and self.isOnline:
                self.logout(1)
                self.isOnline = False
                self.loginCredentials = (None, None)
                self.peerServer.isOnline = False
                self.peerServer.tcpServerSocket.close()
                if self.peerClient is not None:
                    self.peerClient.tcpClientSocket.close()
                print(f"{Fore.GREEN}Logged out successfully")
            # is peer is not logged in and exits the program
            elif choice == "3":
                self.logout(2)
            # if choice is 4 and user is online, then user is asked
            # for a username that is wanted to be searched
            elif choice == "4" and self.isOnline:
                username = input(f"{Fore.CYAN}Username to be searched: ")
                searchStatus = self.searchUser(username)
                # if user is found its ip address is shown to user
                if searchStatus is not None and searchStatus != 0:
                    print(f"{Fore.GREEN}IP address of   {username}   is   {searchStatus}")
            # if choice is 5 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted
            elif choice == "5" and self.isOnline:
                username = input(f"{Fore.CYAN}Enter the username of user to start chat: ")
                searchStatus = self.searchUser(username)
                # if searched user is found, then its ip address and port number is retrieved
                # and a client thread is created
                # main process waits for the client thread to finish its chat
                if searchStatus is not None :
                    searchStatus = searchStatus.split(":")
                    self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]) , self.loginCredentials[0], self.peerServer, None)
                    self.peerClient.start()
                    self.peerClient.join()   
            elif choice == "6" and self.isOnline:
                chat_room_name = input(f"{Fore.CYAN}Enter the name of the chat room you want to create: ")
                self.createChatRoom(chat_room_name)
            elif choice == "7" and self.isOnline:
                chat_room_name = input(f"{Fore.CYAN}Enter the name of the chat room you want to join: ")
                self.joinChatRoom(chat_room_name)
                
            elif choice == "8" and self.isOnline:
                msg = input("Enter the message you want to send : ")
                if self.chatroomUsers is not None:
                    for user in self.chatroomUsers:
                        self.initiate_chat(user,msg)
                                
                                 
            # if this is the receiver side then it will get the prompt to accept an incoming request during the main loop
            # that's why response is evaluated in main process not the server thread even though the prompt is printed by server
            # if the response is ok then a client is created for this peer with the OK message and that's why it will directly
            # sent an OK message to the requesting side peer server and waits for the user input
            # main process waits for the client thread to finish its chat
            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info(f"{Fore.GREEN}Send to   {self.peerServer.connectedPeerIP}   ->   {okMessage}")
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort , self.loginCredentials[0], self.peerServer, "OK")
                self.peerClient.start()
                self.peerClient.join()
            # if user rejects the chat request then reject message is sent to the requester side
            elif choice == "REJECT" and self.isOnline:
                self.peerServer.connectedPeerSocket.send("REJECT".encode())
                self.peerServer.isChatRequested = 0
                logging.info(f"{Fore.RED}Send to   {self.peerServer.connectedPeerIP}  -> REJECT")
            # if choice is cancel timer for hello message is cancelled
            elif choice == "CANCEL":
                self.timer.cancel()
                break
        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()

    # account creation function
    def createAccount(self, username, password):
        # join message to create an account is composed and sent to registry
        # if response is success then informs the user for account creation
        # if response is exist then informs the user for account existence
        message = "JOIN " + username + " " + password
        logging.info(f"{Fore.GREEN}Send to   {self.registryName}  :  {str(self.registryPort)}   ->   {message}")
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info(f"{Fore.GREEN}Received from  {self.registryName}  ->  {response}")
        if response == "join-success":
            print(f"{Fore.GREEN}Account created...")
        elif response == "join-exist":
            print(f"{Fore.RED}choose another username or login...")

    # login function
    def login(self, username, password, peerServerPort):
        # a login message is composed and sent to registry
        # an integer is returned according to each response
        message = "LOGIN " + username + " " + password + " " + str(peerServerPort)
        logging.info(f"{Fore.GREEN}Send to  {self.registryName} : {str(self.registryPort)}  ->  + {message}")
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info(f"{Fore.GREEN}Received from  {self.registryName}  ->  {response}")
        if response == "login-success":
            print(f"{Fore.GREEN}Logged in successfully...")
            return 1
        elif response == "login-account-not-exist":
            print(f"{Fore.RED}Account does not exist...")
            return 0
        elif response == "login-online":
            print(f"{Fore.RED}Account is already online...")
            return 2
        elif response == "login-wrong-password":
            print(f"{Fore.RED}Wrong password...")
            return 3
    
    # logout function
    def logout(self, option):
        # a logout message is composed and sent to registry
        # timer is stopped
        if option == 1:
            message = "LOGOUT " + self.loginCredentials[0]
            self.timer.cancel()
        else:
            message = "LOGOUT"
        logging.info(f"Send to {self.registryName} : {str(self.registryPort)}  ->  + {message}")
        self.tcpClientSocket.send(message.encode())
        

    # function for searching an online user
    def searchUser(self, username):
        # a search message is composed and sent to registry
        # custom value is returned according to each response
        # to this search message
        message = "SEARCH " + username
        logging.info(f"{Fore.GREEN}Send to  {self.registryName} : {str(self.registryPort)}  ->  {message}")
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info(f"{Fore.GREEN}Received from  {self.registryName}   ->"  .join(response))
        if response[0] == "search-success":
            print(username + f"{Fore.GREEN} is found successfully...")
            return response[1]
        elif response[0] == "search-user-not-online":
            print(username +f"{Fore.RED} is not online...")
            return 0
        elif response[0] == "search-user-not-found":
            print(username + f"{Fore.RED} is not found")
            return None
    # function for creating a chat room
    def createChatRoom(self, room_name):
        message = "CREATE_CHAT_ROOM " + room_name
        logging.info(f"{Fore.GREEN}Send to  {self.registryName} : {str(self.registryPort)}  ->  {message}")
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info(f"{Fore.GREEN}Received from  {self.registryName}   ->"  .join(response))
        if response[0] == "chat-room-exists":
            print(f"{Fore.RED} Chat room name already exists... Please choose another name")
            return 0
        elif response[0] == "chat-room-creation-successful":
            print(f"{Fore.GREEN} Chat room created successfully")
            self.inChatroom = True
    # function for joining a chat room
    def joinChatRoom(self, room_name):
        message = "JOIN_CHAT_ROOM " + room_name + " " + self.loginCredentials[0]
        logging.info(f"{Fore.GREEN}Send to  {self.registryName} : {str(self.registryPort)}  ->  {message}")
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info(f"{Fore.GREEN}Received from  {self.registryName}   ->"  .join(response))
        if  response[0] == "chat-room-not-found":
            print(f"{Fore.RED} Chat room not found")
            return 0
        elif response[0] == "chat-room-found":
            print(f"{Fore.GREEN} Chat room joined successfully\n")
            self.inChatroom = True
            self.chatroomName = room_name
            self.chat_room_list_thread = threading.Thread(target=self.updateChatRoomList(self.chatroomName))
            self.chat_room_list_thread.start()
            print(f"{Fore.MAGENTA} The current users in this chat room are :- \n")
            for user in (response[1:]):
                print(f"{Fore.MAGENTA}{user}")  
                self.chatroomUsers.append(user)
            # Handle Chat Room Joining #  
            
            
    def initiate_chat(self,username,message):
        searchStatus = self.searchUser(username)
        # if searched user is found, then its ip address and port number is retrieved
        # and a client thread is created
        # main process waits for the client thread to finish its chat
        if searchStatus is not None :
            searchStatus = searchStatus.split(":")
            self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]) , self.loginCredentials[0], self.peerServer, None,message)
            self.peerClient.start()
            self.peerClient.join()
            
    def updateChatRoomList(self, room_name):
        while self.isOnline:
            # Send a request to the registry to get the latest chat room list
            message = "GET_CHAT_ROOM_LIST " + room_name
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode().split()
        # Process the received chat room list
        if response[0] == "chat-room-list":
            self.chatroomUsers = response[1:]

        # Sleep for a certain period before sending the next request
        time.sleep(3)  # Sleep for 60 seconds (adjust as needed)   
       

            
        

    
    # function for sending hello message
    # a timer thread is used to send hello messages to udp socket of registry
    def sendHelloMessage(self): 
        message = "HELLO " + self.loginCredentials[0]
        logging.info(f"{Fore.YELLOW}Send to   {self.registryName} :  {str(self.registryUDPPort)}   ->   {message}")
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()

# peer is started
main = peerMain()