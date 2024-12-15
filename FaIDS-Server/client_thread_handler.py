import threading
import pickle
from main import log, traceback_func, active_clients

file_receive_users = {}
file_receive_lock = threading.Lock()  # Create a lock to manage access to the file_receive_users dictionary

def transfer_file(from_socket, to_socket):
    try:
        # Receive metadata (filename and filesize)
        metadata = from_socket.recv(1024).decode()
        filename, filesize = metadata.split('|')
        filesize = int(filesize)

        # Send metadata to the destination socket
        to_socket.sendall(metadata.encode())

        # Initialize a variable to track the amount of data received
        received = 0

        # Start receiving and transferring the file
        while received < filesize:
            data = from_socket.recv(1024)
            if not data:
                print("Error: File transfer interrupted.")
                break
            to_socket.sendall(data)
            received += len(data)

        print(f"File transfer completed: {filename} ({received}/{filesize} bytes)")
        
    except Exception as e:
        print(f"Error during file transfer: {e}")
        from_socket.close()
        to_socket.close()

def handle_client(client_socket, client_addr, token, username):
    log(f"Client {client_addr} authenticated with token {token}. Starting communication thread.", 3)
    try:
        while True:
            print(file_receive_users)
            data_length = int.from_bytes(client_socket.recv(4), "big")
            serialized_data = client_socket.recv(data_length)
            received_dict = pickle.loads(serialized_data)

            match received_dict["action"]:
                case 1:
                    match received_dict["sub-action"]:
                        case 1:
                            # Lock the dictionary while reading it
                            with file_receive_lock:
                                username_list = [username for username in file_receive_users]
                            serialized_data = pickle.dumps(username_list)
                            client_socket.sendall(len(serialized_data).to_bytes(4, 'big'))
                            client_socket.sendall(serialized_data)
                        case 2:
                            # Lock the dictionary while modifying it
                            with file_receive_lock:
                                file_receive_users[username] = client_socket
                        case 3:
                            target_user = received_dict.get("username")
                            if target_user in file_receive_users:
                                log(f"Sending a file to {target_user} from {username}")
                                transfer_file(client_socket, file_receive_users[target_user])

    except Exception as e:
        log(f"ERROR-CTH-HC-00-01-01: Error handling client {client_addr}: {e}", 4)
        log(f"Client {client_addr} connection closed due to an error.", 1)
        traceback_func()
        try:
            active_clients.pop(token, None)
        except KeyError:
            log(f"Unknown error when removing client {token} from active clients.", 1)
            print(active_clients)
            client_socket.close()
    finally:
        client_socket.close()
        active_clients.pop(token, None)
