import main
import uuid
from main import log
from main import traceback_func

user_credentials = main.user_credentials
active_clients = main.active_clients

def authenticate_client(client_socket, client_addr):
    try:
        #client_socket.sendall(b"Please provide your username:")
        username = client_socket.recv(1024).decode().strip()

        #client_socket.sendall(b"Please provide your password:")
        password = client_socket.recv(1024).decode().strip()

        if username in user_credentials and user_credentials[username] == password:
            token = str(uuid.uuid4())  # Generate a unique token for the client
            client_socket.sendall(f"Authentication successful. Your token: {token}".encode())
            log(f"Client {client_addr} authenticated successfully.", 1)
            active_clients[token] = client_addr
            return token
        else:
            client_socket.sendall(b"Authentication failed.")
            log(f"Authentication failed for client {client_addr}.", 1)
            client_socket.close()
            return None
    except Exception as e:
        log(f"ERROR-CA-AC-00-01-01: Auth error: {e}", 4)
        log(f"Client {client_addr} disconnected during authentication.", 1)
        traceback_func()
        client_socket.close()
        return None
