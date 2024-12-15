import hashlib
import os
import json
import socket
import ssl
import pickle

user_verified = False
token = ""
configuration = {}

def receive_file(socket):
    try:
        clear_console()

        # Receive metadata
        metadata = socket.recv(1024).decode()
        if not metadata:
            log("Failed to receive metadata.", 2)
            return False
        
        filename, filesize = metadata.split('|')
        filename = os.path.basename(filename)  # Prevent path traversal
        filesize = int(filesize)

        log(f"Receiving file: {filename}, ({filesize} bytes)", 3)

        # Ensure the directory exists
        os.makedirs("files/receive", exist_ok=True)

        # Receive the file
        filepath = os.path.join("files/receive", filename)
        with open(filepath, "wb") as file:
            received = 0
            while received < filesize:
                data = socket.recv(min(1024, filesize - received))
                if not data:
                    log("Connection lost during file transfer.", 1)
                    return False
                file.write(data)
                received += len(data)
                log(f"Received {received}/{filesize} bytes", 3)

        log("File transfer complete.", 3)
        return True

    except Exception as e:
        log(f"Error receiving file: {e}", 1)
        return False


def send_file(socket, filepath):
    try:
        # Validate file
        if not os.path.isfile(filepath):
            log(f"File does not exist: {filepath}", 1)
            return False

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        # Send metadata
        metadata = f"{filename}|{filesize}"
        socket.sendall(metadata.encode())
        log(f"Sending file: {filename}, ({filesize} bytes)", 3)

        # Send the file
        with open(filepath, "rb") as file:
            while (chunk := file.read(1024)):
                socket.sendall(chunk)
        
        log("File sent successfully.", 3)
        return True

    except Exception as e:
        log(f"Error sending file: {e}", 1)
        return False

def send_server_action(socket, action, sub_action, username=None):
    data_to_send = {}
    data_to_send["token"] = token
    data_to_send["action"] = action
    data_to_send["sub-action"] = sub_action
    if not username == None:
        data_to_send["username"] = username

    try:
        # Serialize the dictionary
        serialized_data = pickle.dumps(data_to_send)
        
        # Send the length of the serialized data first to allow the server to know how much data to expect
        socket.sendall(len(serialized_data).to_bytes(4, 'big'))  # Send size in 4 bytes
        
        # Send the serialized dictionary
        socket.sendall(serialized_data)

        if sub_action != 1:
            return

        data_length = int.from_bytes(socket.recv(4), 'big')

        serialized_data = socket.recv(data_length)

        received_list = pickle.loads(serialized_data)

        print(received_list)

        return received_list
    except Exception as e:
        log(f"Error sending data to server: Error: {e}", 1)

def server_connection_establisher(username, password):
    global token

    server_ip = configuration["server_ip_address"]

    server_port = configuration["server_port"]

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_stream:
        socket_stream.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket_stream.connect((server_ip, server_port))
        with context.wrap_socket(socket_stream, server_hostname=server_ip) as ssl_client_connection:
            ssl_client_connection.sendall(username.encode())
            ssl_client_connection.sendall(password.encode())
            token = ssl_client_connection.recv(1024)
            log("Received token, proceeding with program", 4)
            server_communication_handler_session(token, ssl_client_connection)

def server_communication_handler_session(token, ssl_client_connection):
    options = [None, "Upload File", "Receive File","Domain Request"]
    
    while True:
        clear_console()

        # Display options menu
        print("Select an option:")
        index = 1
        for option in options:
            if option is not None:
                print(f"{index}. {option}")
                index += 1
        
        try:
            # Get user input and process it
            user_choice = int(input("Option: "))
            if user_choice == 1: #MISC ACTIONS = 1 - REQ ACTIVE USERS, 2-ACTUAL FILE SENDING
                # Case 1: Upload File
                files = os.listdir("files/send")
                if files:
                    print("Available files to upload:")
                    index = 1
                    for file in files:
                        print(f"{index}. {file}")
                        index += 1

                    try:
                        file_to_send_index = int(input("Select file to send: "))
                        if 1 <= file_to_send_index <= len(files):
                            file_to_send = files[file_to_send_index - 1]
                            print(f"Selected file: {file_to_send}")
                            active_users = send_server_action(ssl_client_connection, 1, 1)
                            index = 1
                            for active_user in active_users:
                                if active_user is not None:
                                    print(f"{index}. {active_user}")
                                    index += 1
                            try:
                                selected_user = int(input("Select: "))
                                send_server_action(ssl_client_connection, 1, 3, active_users[selected_user - 1])
                                send_file(ssl_client_connection, f"files/send/{file_to_send}")
                            except Exception as e:
                                print(e)
                        else:
                            print("Invalid file selection.")
                    except ValueError:
                        print("Invalid input, please enter a valid number.")
                else:
                    print("No files available to upload.")
            elif user_choice == 2:
                input("Press enter to start receiving a file...")
                send_server_action(ssl_client_connection, 1, 2)
                if receive_file(ssl_client_connection):
                    input()
                    continue
            elif user_choice == 3:
                # Case 2: Domain Request
                input("Press Enter to continue with Domain Request...")  # Implement domain request logic here
                
            else:
                print("Invalid option. Please select a valid option.")

        except ValueError:
            log("Incorrect option, please enter a valid number.", 1)        

def hash_credentials(username, password):
    credentials = f"{username}:{password}"
    credentials_hash_object = hashlib.sha256(credentials.encode())  # Encode text to bytes
    credentials_hash_hex = credentials_hash_object.hexdigest()
    return credentials_hash_hex

def get_hashed_credentials():
    with open("credentials/user_credentials.json", "r") as credentials_file:
        return json.load(credentials_file)

def login(username, password):
    if hash_credentials(username, password) == get_hashed_credentials():
        return True
    else:
        return False

def register(username, password):
    #dodat password checks
    if not os.path.exists("credentials/user_credentials.json"):
        os.makedirs("credentials")
        with open("credentials/user_credentials.json", "w") as credentials_file:
            pass
    with open("credentials/user_credentials.json", "w") as credentials_file:
        hashed_credentials = hash_credentials(username, password)
        json.dump(hashed_credentials, credentials_file)
        return True
        
def main():
    global user_verified
    #username = input("Username: ")
    #password = input("Password: ")
    username = "admin"
    password = "Pa$$w0rd"
    if input("Registering (y/n):").lower() == "y":
        if register(username, password):
            if login(username, password):
                user_verified = True
                print("Registered in successfully!")
                server_connection_establisher(username, password)
            else:
                print("Failed to register!")
                main()
        else:
            print("Register unsuccessful")
            main()
    else:
        if login(username, password):
            user_verified = True
            print("Logged in successfully!")
            server_connection_establisher(username, password)
        else:
            print("Failed to login.")
            main()

from logging import log
from logging import clear_console
from config_handler import configuration_handler

if __name__ == "__main__":
    configuration = configuration_handler()
    if configuration:
        main()
    else:
        log("Failed!")