import threading
import json
from main import log, traceback_func
from chunk_size_calculator import get_optimal_chunk_size

active_clients = {}
file_receive_users = {}
file_receive_lock = threading.Lock()  # Create a lock to manage access to the file_receive_users dictionary
active_clients_lock = threading.Lock()

def recv_all(socket, length):
    """
    Helper function to receive exactly `length` bytes from a socket.
    """
    data = b""
    while len(data) < length:
        packet = socket.recv(length - len(data))
        if not packet:
            raise ConnectionError("Connection lost while receiving data.")
        data += packet
    return data

def transfer_file(from_socket, to_socket):
    try:
        # Receive metadata length and metadata
        metadata_length = int.from_bytes(from_socket.recv(4), 'big')
        metadata = recv_all(from_socket, metadata_length).decode()

        # Parse and validate metadata
        try:
            metadata_dict = json.loads(metadata)
            filename = metadata_dict.get("filename")
            filesize = metadata_dict.get("filesize")
            if not filename or not filesize:
                raise ValueError("Invalid metadata received.")
            filesize = int(filesize)
        except (json.JSONDecodeError, ValueError) as e:
            log(f"Error parsing file metadata: {e}", 1)
            return

        # Send metadata to the destination socket
        to_socket.sendall(len(metadata).to_bytes(4, 'big'))  # Send metadata length
        to_socket.sendall(metadata.encode())  # Send metadata

        # Determine optimal chunk size dynamically
        chunk_size = get_optimal_chunk_size(filesize)
        log(f"Starting file transfer: {filename} ({filesize} bytes) in chunks of {chunk_size} bytes", 3)

        # Transfer the file
        transferred = 0
        while transferred < filesize:
            data = from_socket.recv(min(chunk_size, filesize - transferred))
            if not data:
                log("Connection lost during file transfer.", 1)
                break
            to_socket.sendall(data)
            transferred += len(data)

        # Log completion status
        if transferred == filesize:
            log(f"File transfer completed: {filename} ({transferred}/{filesize} bytes)", 3)
        else:
            log(f"File transfer incomplete: {filename} ({transferred}/{filesize} bytes)", 1)

    except Exception as e:
        log(f"Error during file transfer: {e}", 1)
        traceback_func()


def handle_client(client_socket, client_addr, token, username):
    log(f"Client {client_addr} authenticated with token {token}. Starting communication thread.", 3)
    with active_clients_lock:
        active_clients[username] = [token, client_socket]
    try:
        while True:
            # Print the current active users (for debugging purposes)

            try:
                # Receive the data length and the actual data
                data_length = int.from_bytes(client_socket.recv(4), "big")
                serialized_data = recv_all(client_socket, data_length)
                received_dict = json.loads(serialized_data.decode())

                # Handle the action
                match received_dict["action"]:
                    case 1:
                        # Handle action 1 (request for users)
                        match received_dict["sub-action"]:
                            case 1:
                                log(f"User {username} requested active users for file transfer.", 3)
                                # Lock the dictionary while reading it
                                with file_receive_lock:
                                    username_list = list(file_receive_users.keys())
                                serialized_data = json.dumps(username_list).encode()
                                client_socket.sendall(len(serialized_data).to_bytes(4, 'big'))
                                log(f"Sending usernames: {serialized_data}", 4)
                                client_socket.sendall(serialized_data)
                            case 2:
                                log(f"User {username} requested files to be sent over.", 3)
                                # Lock the dictionary while modifying it (add user to the file receive users)
                                with file_receive_lock:
                                    file_receive_users[username] = client_socket
                                    log(f"Current users waiting for files: {file_receive_users}", 4)
                            case 3:
                                # File transfer request
                                target_user = received_dict.get("username")
                                if target_user in file_receive_users:
                                    log(f"File transfer initiated - From: {username} To: {target_user}", 3)
                                    transfer_file(client_socket, file_receive_users[target_user])

            except Exception as e:
                log(f"Error while handling client {client_addr}: {e}", 4)
                traceback_func()
                break  # Exit loop if there's an error in receiving data

    except Exception as e:  
        log(f"ERROR-CTH-HC-00-01-01: Error handling client {client_addr}: {e}", 4)
        log(f"Client {client_addr} connection closed due to an error.", 1)
        traceback_func()

    finally:
        # Clean up and close the socket after processing is complete
        try:
            active_clients.pop(token, None)
        except KeyError:
            log(f"Unknown error when removing client {token} from active clients.", 1)

        client_socket.close()
        log(f"Connection to client {client_addr} closed.")
