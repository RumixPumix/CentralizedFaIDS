import hashlib
import os
import json
import socket
import ssl
import traceback
import time
from chunk_size_calculator import get_optimal_chunk_size

user_verified = False
token = ""
configuration = {}

def recv_all(socket, length):
    data = b""
    while len(data) < length:
        packet = socket.recv(length - len(data))
        if not packet:
            raise ConnectionError("Socket connection closed prematurely")
        data += packet
    return data

def receive_file(socket):
    try:
        clear_console()
        print("Waiting for file...")

        # Receive metadata
        try:
            metadata_length = int.from_bytes(socket.recv(4), 'big')  # Metadata length
            metadata = recv_all(socket, metadata_length)
        except (ValueError, ConnectionError) as e:
            log(f"Error receiving metadata: {e}", 1)
            return False
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata.decode())
            filename = metadata_dict.get("filename")
            filesize = metadata_dict.get("filesize")
            if not filename or not filesize:
                raise ValueError("Missing required metadata fields.")
        except (json.JSONDecodeError, ValueError) as e:
            log(f"Invalid metadata format: {e}", 1)
            return False

        filename = os.path.basename(filename)  # Prevent path traversal
        filesize = int(filesize)
        chunk_size = get_optimal_chunk_size(filesize)  # Calculate chunk size dynamically
        log(f"Receiving file: {filename}, ({filesize} bytes) in chunks of {chunk_size} bytes", 3)

        # Ensure the directory exists
        try:
            os.makedirs("files/receive", exist_ok=True)
        except OSError as e:
            log(f"Error creating directory: {e}", 1)
            return False

        # Receive the file
        filepath = os.path.join("files/receive", filename)
        try:
            with open(filepath, "wb") as file:
                received = 0
                start_time = time.time()  # Start timing
                while received < filesize:
                    data = socket.recv(min(chunk_size, filesize - received))
                    if not data:
                        log("Connection lost during file transfer.", 1)
                        return False
                    file.write(data)
                    received += len(data)

                    # Calculate elapsed time and speed
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 0:
                        speed_in_mb = (received / (1024 * 1024)) / elapsed_time  # Speed in MB/s
                        speed_in_kb = (received / 1024) / elapsed_time  # Speed in KB/s
                    clear_console()
                    # Determine if the file size should be displayed in KB or MB
                    if filesize < 1024 * 1024:  # Less than 1 MB
                        if 0.1 <= speed_in_mb <= 0.9:
                            log(f"Downloaded {received / 1024:.2f} KB of {filesize / 1024:.2f} KB "
                                f"at {speed_in_kb:.2f} KB/s", 3)
                        else:
                            log(f"Downloaded {received / 1024:.2f} KB of {filesize / 1024:.2f} KB "
                                f"at {speed_in_mb:.2f} MB/s", 3)
                    else:  # 1 MB or more
                        if 0.1 <= speed_in_mb <= 0.9:
                            log(f"Downloaded {received / (1024 * 1024):.2f} MB of {filesize / (1024 * 1024):.2f} MB "
                                f"at {speed_in_kb:.2f} KB/s", 3)
                        else:
                            log(f"Downloaded {received / (1024 * 1024):.2f} MB of {filesize / (1024 * 1024):.2f} MB "
                                f"at {speed_in_mb:.2f} MB/s", 3)
        except (OSError, IOError) as e:
            log(f"Error writing file: {e}", 1)
            return False

        log("File transfer complete.", 3)
        return True

    except Exception as e:
        log(f"Unexpected error in receive_file: {e}", 1)
        return False


def send_file(socket, filepath):
    try:
        # Validate file existence
        if not os.path.isfile(filepath):
            log(f"File does not exist: {filepath}", 1)
            return False

        filename = os.path.basename(filepath)
        try:
            filesize = os.path.getsize(filepath)
        except OSError as e:
            log(f"Error getting file size: {e}", 1)
            return False

        chunk_size = get_optimal_chunk_size(filesize)  # Calculate chunk size dynamically

        # Send metadata
        try:
            metadata = json.dumps({"filename": filename, "filesize": filesize})
            socket.sendall(len(metadata).to_bytes(4, 'big'))  # Metadata length
            socket.sendall(metadata.encode())
        except (OSError, ConnectionError) as e:
            log(f"Error sending metadata: {e}", 1)
            return False

        log(f"Sending file: {filename}, ({filesize} bytes) in chunks of {chunk_size} bytes", 3)

        # Send the file
        try:
            with open(filepath, "rb") as file:
                while (chunk := file.read(chunk_size)):
                    socket.sendall(chunk)
        except (OSError, IOError, ConnectionError) as e:
            log(f"Error sending file data: {e}", 1)
            return False

        log("File sent successfully.", 3)
        return True

    except Exception as e:
        log(f"Unexpected error in send_file: {e}", 1)
        return False

def parse_server_response_data(data):
    log(f"Parsing server response...", 4)
    return data.get("response", None)

def send_server_action(socket, action, sub_action, username=None):
    log("Preparing data to send to the server.", 4)

    # Prepare the data dictionary
    data_to_send = {
        "token": str(token),  # Ensure the token is a string
        "action": action,
        "sub-action": sub_action
    }
    if username is not None:
        data_to_send["username"] = username
        log(f"Added username to data: {username}", 4)

    try:
        # Serialize the dictionary
        serialized_data = json.dumps(data_to_send).encode()

        # Send the length of the serialized data
        serialized_length = len(serialized_data).to_bytes(4, 'big')
        socket.sendall(serialized_length)

        # Send the serialized dictionary
        socket.sendall(serialized_data)

        # Only handle server responses if sub_action == 1
        if sub_action != 1:
            return None
        log(f"Waiting server response for user ready for file transfer list.", 4)
        return parse_server_response_data(receive_server_response(socket))

    except Exception as e:
        log(f"Error sending data to server: {e}", 1)
        log(traceback.format_exc(), 4)  # Log full traceback for debugging

def receive_server_response(server_socket):
    try:
        log(f"Receiving data", 4)
        data_length = int.from_bytes(server_socket.recv(4), "big")
        serialized_data = recv_all(server_socket, data_length)
        received_dict = json.loads(serialized_data.decode())
        log(f"Returning given list", 4)
        return received_dict
    except Exception as data_receiving_error:
        log(f"Error receiving data: {data_receiving_error}", 4)
        log(f"Data received: {serialized_data}")

def server_communication_handler_session(ssl_client_connection):
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
            if user_choice == 1: #File transfer option
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
                            if not active_users:
                                log(f"Server didn't send any users ready for file transfer!", 3)
                                continue
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
                send_server_action(ssl_client_connection, 1, 2)
                input("Enter file receiving mode? Press Enter...")
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










def server_connection_establisher(username, password):
    global token

    server_ip = configuration.get("server_ip_address", None)
    if not server_ip:
        log(f"No server IP set! Exiting...", 1)
        return None

    server_port = configuration.get("server_port", None)
    if not server_ip:
        log(f"No server port set! Exiting...", 1)
        return None
    
    try:

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    except Exception as ssl_creation_error:
        log(f"Error occured during SSL context creation.", 1)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_stream:
            socket_stream.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                socket_stream.connect((server_ip, server_port))
            except TimeoutError:
                log("Server didn't respond...", 2)
                input("Enter to exit program...")
                return None
            with context.wrap_socket(socket_stream, server_hostname=server_ip) as ssl_client_connection:
                ssl_client_connection.sendall(username.encode())
                ssl_client_connection.sendall(password.encode())
                token = ssl_client_connection.recv(1024)
                log("Received token, proceeding with program", 4)
                server_communication_handler_session(ssl_client_connection)
    except Exception as general_except_error:
        log(f"General error occured: {general_except_error}", 1)
        input("Enter to exit program...")

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
        os.makedirs("credentials", exist_ok=True)
        with open("credentials/user_credentials.json", "w") as credentials_file:
            pass
    with open("credentials/user_credentials.json", "w") as credentials_file:
        hashed_credentials = hash_credentials(username, password)
        json.dump(hashed_credentials, credentials_file)
        return True
        
def main():
    global user_verified
    if not os.path.exists("credentials/user_credentials.json"):
        username = input("Username: ")
        password = input("Password: ")
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
        if input("Logout (y/n)?").lower() == "y":
            os.remove("credentials/user_credentials.json")
            main()
        username = input("Username: ")
        password = input("Password: ")
        username, password = "admin", "Pa$$w0rd"
        if login(username, password):
            user_verified = True
            print("Logged in successfully!")
            server_connection_establisher(username, password)
        else:
            print("Failed to login.")
            main()

from logging import log, clear_console
from config_handler import configuration_handler

if __name__ == "__main__":
    configuration = configuration_handler()
    if configuration:
        main()
    else:
        log("Failed!")