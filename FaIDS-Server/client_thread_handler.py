import main
from main import log
from main import traceback_func

def handle_client(client_socket, client_addr, token):
    log(f"Client {client_addr} authenticated with token {token}. Starting communication thread.", 3)
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                log(f"Client {client_addr} disconnected.", 3)
                break
            log(f"Received data from {client_addr}: {data.decode()}", 4)
            client_socket.sendall(b"Server received your message.")
    except Exception as e:
        log(f"ERROR-CTH-HC-00-01-01: Error handling client {client_addr}: {e}", 4)
        log(f"Client {client_addr} connection closed due to an error.", 1)
        traceback_func()
        main.active_clients.pop(token)
    finally:
        client_socket.close()
        main.active_clients.pop(token, None)