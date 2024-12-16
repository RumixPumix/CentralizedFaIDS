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

def send_client_action(client_socket, action, sub_action, response):
    data_to_send = {
        "action": action,
        "sub-action": sub_action,
        "response": response
    }

    #Serializing the data
    try:
        serialized_data = json.dumps(data_to_send).encode()

        serialized_data_length = len(serialized_data).to_bytes(4, 'big')
        client_socket.sendall(serialized_data_length)
        client_socket.sendall(serialized_data)
    except Exception as json_error:
        log(f"Error serializing data: {json_error}", 4)
        try:
            log(f"Serialized data: {serialized_data}", 4)
        except:
            pass
        try:
            log(f"Raw data: {data_to_send}", 4)
        except:
            pass

def receive_client_response(client_socket):
    try:
        data_length = int.from_bytes(client_socket.recv(4), "big")
        serialized_data = recv_all(client_socket, data_length)
        received_dict = json.loads(serialized_data.decode())
        return received_dict
    except Exception as data_receiving_error:
        log(f"Error receiving data: {data_receiving_error}", 4)
        log(f"Data received: {serialized_data}")

def send_file_transfer_ready_users(client_socket):
    with file_receive_lock:
        username_list = list(file_receive_users.keys())
    send_client_action(client_socket, 1, 1, username_list)

def set_user_file_transfer_ready_state(client_socket, username):
    with file_receive_lock:
        file_receive_users[username] = client_socket

def file_action_handler(client_socket, received_dict, username):
    match received_dict["sub-action"]:
        case 1: # Handle action 1 (request for users)
            log(f"User '{username}' requested users for file transfer", 3)
            send_file_transfer_ready_users(client_socket)
        case 2: #Set user to file transfer ready state
            log(f"User '{username}' set to file transfer state", 3)
            set_user_file_transfer_ready_state(client_socket, username)
        case 3:
            # File transfer begin.
            target_user = received_dict.get("username")
            if target_user in file_receive_users:
                log(f"File transfer initiated - From: {username} To: {target_user}", 3)
                send_client_action(client_socket, 1, 3, 1)
                transfer_file(client_socket, file_receive_users[target_user])
            else:
                send_client_action(client_socket, 1, 3, 0)


def handle_client(client_socket, client_addr, token, username):
    log(f"Client {client_addr} authenticated with token {token}. Starting communication thread.", 3)
    with active_clients_lock:
        active_clients[username] = [token, client_socket]
    try:
        while True:
            try:
                received_dict = receive_client_response(client_socket)
                # Handle the action
                match received_dict["action"]:
                    case 1: #File action
                        file_action_handler(client_socket, received_dict, username)
                    case 2: #Domain change
                        pass
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
