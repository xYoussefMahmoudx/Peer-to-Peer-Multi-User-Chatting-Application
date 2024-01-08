import subprocess
import time
import random
import string


dictpeers = []

def run_registry():
    subprocess.Popen([ "python", "registry.py"],  shell=True)

def run_peer():
    #return subprocess.Popen(['python', 'peer.py', str(peer_id), registry_ip])
    proc=subprocess.Popen([ "python", "peer.py"], stdin=subprocess.PIPE,stdout=subprocess.PIPE, shell=True)
    proc.stdin.write('192.168.56.1\n'.encode())
    proc.stdin.flush()
    #proc.communicate()
    
    dictpeers.append(proc)
    

def create_account(peer_id):
    username = ''.join(random.choices(string.ascii_lowercase, k=8))
    password = '1234567'
    port = f"{random.randint(5000, 6000)}"
    dictpeers[peer_id].stdin.write("1\n".encode())
    dictpeers[peer_id].stdin.flush()
    dictpeers[peer_id].stdin.write(username.encode()+'\n'.encode())
    dictpeers[peer_id].stdin.flush()
    dictpeers[peer_id].stdin.write(password.encode()+'\n'.encode())
    dictpeers[peer_id].stdin.flush()
    return username, password, port

def login(peer_id, username, password, port):
    print("login func")
   # subprocess.Popen(['python', 'peer.py', str(peer_id), registry_ip, '2', username, password, str(port)])
    dictpeers[peer_id].stdin.write("2\n".encode())
    dictpeers[peer_id].stdin.flush()
    dictpeers[peer_id].stdin.write(username.encode()+'\n'.encode())
    dictpeers[peer_id].stdin.flush()
    dictpeers[peer_id].stdin.write(password.encode()+'\n'.encode())
    dictpeers[peer_id].stdin.flush()
    dictpeers[peer_id].stdin.write(port.encode()+'\n'.encode())
    dictpeers[peer_id].stdin.flush()

def create_chat_room(peer_id):
    print("create room func")
    room_name = ''.join(random.choices(string.ascii_lowercase, k=8))
    dictpeers[peer_id].stdin.write("6\n".encode())
    dictpeers[peer_id].stdin.flush()
    dictpeers[peer_id].stdin.write(room_name.encode()+'\n'.encode())
    dictpeers[peer_id].stdin.flush()
    return room_name
    #subprocess.Popen(['python', 'peer.py', str(peer_id), registry_ip, '6', room_name])

def join_chat_room(peer_id, room_name):
    print("join func")
    dictpeers[peer_id].stdin.write("7\n".encode())
    dictpeers[peer_id].stdin.flush()
    dictpeers[peer_id].stdin.write(room_name.encode()+'\n'.encode())
    dictpeers[peer_id].stdin.flush()

def send_message(peer_id,  message):
     print("i sent a massage")
     dictpeers[peer_id].stdin.write(message.encode()+'\n'.encode())
     dictpeers[peer_id].stdin.flush()
    #subprocess.Popen(['python', 'peer.py', str(peer_id), registry_ip, '8', room_name, message])

def logout(peer_id):
     print("i loged out")
     dictpeers[peer_id].stdin.write("3\n".encode())
     dictpeers[peer_id].stdin.flush()
    #subprocess.Popen(['python', 'peer.py', str(peer_id), registry_ip, '8', room_name, message])
def test_chat_room_performance():
    # Create chat room
    

    # Join chat room for each peer
    room_name = create_chat_room(0)  # Replace with the actual room name
    for peer_id in range(0, 3):

        join_chat_room(peer_id, room_name)
        print(peer_id)
        time.sleep(1)

    # Measure time to send messages to the chat room
    start_time = time.time()
    message = "Testing chat room functionality"
    
    for peer_id in range(0, 3):
     send_message(peer_id, message)
     
     time.sleep(1)
           
    end_time = time.time()

    # Assert that the time to send messages is within an expected range (e.g., less than 5 seconds)
    time_taken = end_time - start_time
    assert time_taken < 5.0, f"Performance test failed: Time taken to send messages is {time_taken} seconds."
    
    print(f"Performance test passed: Time taken to send messages is {time_taken} seconds.")
    
    for peer_id in range(0, 3):
     
      send_message(peer_id, ":q")
     
      time.sleep(1)
      
    for peer_id in range(0, 3):
     
      logout(peer_id)
     
      time.sleep(1)
    
     

def main():
    # Run registry
    run_registry()
    time.sleep(1)  # Wait for registry to start

    # Define the number of peers you want to test
    num_peers = 3

    # Run peers
    
   # peers = []
    for peer_id in range(0, num_peers):
        run_peer()
        
        uname,passw,port=create_account(peer_id)
        
        time.sleep(3)
        login(peer_id,username=uname,password=passw,port=port)
        
        time.sleep(3)  # Wait for each peer to start
       # peers.append(peer_process)

    # Create accounts and login for each peer
   

    # Test chat room functionality
    
    test_chat_room_performance()
    
    exit()
    
    
    


if __name__ == "__main__":
    main()