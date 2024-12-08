configuration = {}
user_credentials = {}
active_clients = {}
CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"
import subprocess
import socket
import ssl
import os
import sys
import time
import platform
from datetime import datetime
import threading
import json
import zipfile
import traceback
import psutil
import colorama

#Regarding ERROR CODES:
#ERROR FF-NF-NT-NE
#F - File the error occured in
#F - Function name: first two letters of all words of the function name
#- separator
#NF - nested function name if it exists. If not 00
#NT - Number of the try function inside the function
#NE - Number of the exception where it occured.

def traceback_func():
    try:
        debug_mode = configuration.get("debug_mode", True)
    except:
        debug_mode = True
    if debug_mode == True:
        tb = traceback.format_exc()  # Get the full exception traceback as a string
        log(tb, 4)

def log(message, opcode=3):
    def write_log_to_file(logged_message):
        def zip_and_move(file_name, log_path):
            """Zip a file and move it to the 'logs/old_logs' folder."""
            old_logs_dir = "logs/old_logs"
            os.makedirs(old_logs_dir, exist_ok=True)  # Ensure the 'old_logs' folder exists

            zip_path = os.path.join(old_logs_dir, f"{file_name}.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(log_path, arcname=file_name)  # Add the file to the zip with its original name

            os.remove(log_path)  # Delete the original file

        def check_for_old_logs():
            """Check for old logs in the 'logs' folder and zip them if necessary."""
            for file in os.listdir("logs"):
                file_path = os.path.join("logs", file)
                if os.path.isfile(file_path) and file != f"{get_current_date()}.txt":
                    zip_and_move(file, file_path)

        def get_current_date():
            """Get the current date in 'YYYYMMDD' format."""
            current_date = datetime.now()
            return current_date.strftime("%Y-%m-%d-server")

        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Check for old logs before writing new logs
        check_for_old_logs()

        # Write the log message to today's log file
        log_name = get_current_date()
        try:
            with open(f"logs/{log_name}.txt", "a") as file_log:
                file_log.write(f"{logged_message}\n")
        except Exception as error:
            log(f"ERROR-M-L0-WLTF-01-01: Unexpected error: {error}", 4)
            log("Unexpected error on logging", 1)
            traceback_func()
    try:
        if opcode == 4:
            if configuration.get("debug_mode", True) != True:
                return
    except KeyError as error:
        log(f"ERROR-M-L0-00-02-01: Dictionary key error: {error}", 4)
        log("No debug mode key in config!", 1)
        traceback_func()
    except Exception as error:
        log(f"ERROR-M-L0-00-02-02: Unexpected error: {error}", 4)
        log("Unexpected error on looking for debug_mode value", 1)
        traceback_func()
    def get_current_date_time():
        current_datetime = datetime.now()
        return current_datetime.strftime("%Y-%m-%d %H:%M:%S") 
    opcodes = [None,"ERROR", "WARNING", "INFO", "DEBUG"]
    color_codes = [None, Fore.RED, Fore.YELLOW, Fore.WHITE, Fore.PURPLE]
    message_to_log = f"[{get_current_date_time()}] [{opcodes[opcode]}]: {message}"
    print(message_to_log)
    write_log_to_file(message_to_log)

def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def self_restart():
    log("Restarting the script...", 3)
    time.sleep(3)
    os.execv(sys.executable, ["python"] + sys.argv)

def generate_self_signed_certificate(cert_file="cert.pem", key_file="key.pem"):
    """Generates a self-signed SSL certificate."""
    try:
        # Ensure the OpenSSL command is available
        if subprocess.call(["which", "openssl"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) != 0:
            log("ERROR-M-GSSC-00-01-00: OpenSSL Error (Check if its installed)", 1)
            input()
            exit()

        # Create the SSL certificate and key using OpenSSL
        subprocess.check_call([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-keyout", key_file,
            "-out", cert_file, "-days", "365", "-nodes", "-subj", "/CN=localhost"
        ])

        log(f"Self-signed certificate generated: {cert_file} and {key_file}", 3)

    except FileNotFoundError as error:
        # This error occurs when openssl is not found on the system
        log(f"ERROR-M-GSSC-00-01-01: OpenSSL Error (Check if its installed): {error}", 4)
        log("OpenSSL might not be installed. You have to install it and then proceed.", 1)
        log("Or place 'cert.pem' and 'key.pem' files into root folder.", 1)

        traceback_func()
        #TODO moramo dodat mogucnost da ga vrati nazad i kaze mu da nemoze bez ssl certificatea.
        input("Press Enter to exit.")
        exit()
    except subprocess.CalledProcessError as error:
        log(f"ERROR-M-GSSC-00-01-02: Certificate generation error: {error}", 4)
        log("Certificate generation failed.", 1)
        traceback_func()
        exit()
    except Exception as error:
        log(f"ERROR-M-GSSC-00-01-03: Unexpected error: {error}", 4)
        log("Unexpected error on generating certificate.", 1)
        traceback_func()
        exit()

def ssl_certificate():
    """Handles SSL certificate creation and user interaction."""
    log("Do you wish to generate a self-signed certificate? (y/n)", 3)
    user_input = input().strip().lower()

    if user_input == "y":
        # Generate certificate in the current directory
        cert_file = "cert.pem"
        key_file = "key.pem"
        
        log(f"Generating self-signed SSL certificate in the current directory...", 3)
        generate_self_signed_certificate(cert_file, key_file)

        log(f"Certificate and key generated as {cert_file} and {key_file}.", 3)
        log(f"Please import {cert_file} into the main directory of your FaIDS client and start the program.", 3)

    elif user_input == "n":
        log("This program doesn't support non-SSL configurations. Exiting...", 2)
        input("Press Enter to exit.")
        exit()

    else:
        log("Invalid input. Please respond with 'y' or 'n'.", 1)
        ssl_certificate()  # Recursive call in case of invalid input

    input("Press Enter to continue...")
    main()

def get_local_ips_and_ips_with_gateway():
    log("Verifying bound IP's validity...", 3)
    valid_ips = []
    ips_with_gateway = []
    # Get the list of all network interfaces
    gateways = psutil.net_if_addrs()
    gateways_info = psutil.net_connections(kind='inet')

    for interface, addrs in gateways.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:  # IPv4 address
                ip_address = addr.address
                if ip_address not in valid_ips:
                    valid_ips.append(ip_address)
                # Check if a gateway is associated with this interface
                if psutil.net_if_stats().get(interface, None):
                    for conn in gateways_info:
                        if conn.status == 'ESTABLISHED' and conn.laddr.ip == ip_address:
                            if ip_address not in ips_with_gateway and not str(ip_address).startswith("127"):
                                ips_with_gateway.append(ip_address)
    return valid_ips, ips_with_gateway

def cleanup_existing_sockets():
    bind_address = configuration.get("server_bind_address")
    bind_port = configuration.get("server_port")

    if not bind_port:
        log("Server Port not set, exiting cleanup... Please set the server port.", 2)
        return

    log("Checking for existing sockets to clean up...", 3)

    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr and conn.laddr.ip == bind_address and conn.laddr.port == bind_port:
                log(f"Found conflicting socket on {bind_address}:{bind_port} (PID: {conn.pid})", 4)

                # Provide detailed information about the process
                if conn.pid:
                    proc = psutil.Process(conn.pid)
                    log(f"Conflicting process details: {proc.name()} (PID: {proc.pid}, Status: {proc.status()})", 4)
                    
                    # Ask the user if the process should be terminated
                    user_input = input(f"The process '{proc.name()}' (PID: {proc.pid}) is using the port. "
                                       f"Do you want to terminate it? (y/N): ").strip().lower()
                    
                    if user_input == 'y':
                        try:
                            log(f"Terminating process {proc.name()} (PID: {proc.pid})...", 3)
                            proc.terminate()
                            proc.wait(timeout=5)  # Wait for the process to terminate
                            log(f"Successfully terminated process {proc.name()} (PID: {proc.pid}).", 3)
                        except psutil.TimeoutExpired as error:
                            log(f"ERROR-M-CES-00-02-01: Timeout for terminating process: {error}", 4)
                            log(f"Failed to terminate process {proc.name()} (PID: {proc.pid}) in time.", 1)
                            traceback_func()
                        except Exception as error:
                            log(f"ERROR-M-CES-00-02-02: Unexpected error: {error}", 4)
                            log(f"Error terminating process {proc.name()} (PID: {proc.pid}): {error}", 1)
                            traceback_func()
                    else:
                        log("User chose not to terminate the conflicting process.", 2)

        log("Socket cleanup completed.", 3)
    except Exception as e:
        log(f"ERROR-M-CES-00-01-01: Unexpected error: {e}", 4)
        log("Unexpected error on cleaning up sockets", 1)
        traceback_func()
        log("Socket cleanup failed...", 1)



def attempt_recovery(context):
    if context == "socket":
        try:
            log("Attempting to recover from a socket error. Cleaning up existing sockets", 3)

            cleanup_existing_sockets()
            valid_ips, ips_with_gateway = get_local_ips_and_ips_with_gateway()
            if configuration["server_bind_address"] not in valid_ips:
                log(f"Found error! {configuration["server_bind_address"]} isn't an existing IP on this device.",1)
                log(f"Suggested IPs for binding:", 3)

                index = 1
                ips_with_gateway.insert(0, None)
                for ip in ips_with_gateway:
                    if ip == None:
                        continue
                    log(f"{index} - {ip}", 3)
                    index += 1
                def choose():
                    try:
                        index_choice = int(input("Index: "))
                        if index_choice > len(ips_with_gateway):
                            log("No IP with that index.", 2)
                            choose()
                        configuration["server_bind_address"] = ips_with_gateway[index_choice]
                        config_handler.apply_current_config(configuration)
                        log(f"Set server bind address to: {configuration["server_bind_address"]}", 3)
                        time.sleep(3)
                        self_restart()
                    except Exception:
                        choose()
                choose()
                #DODAMO OPCIJU DA SE LISTA KROZ SUGGESTED IPS I DA USER MOZE BIRAT KOJU ZELI, KADA ODABERE UZME TRENUTNI CONFIG, MODIYFYA GA I SAVEA NOVI CONFIG.
                input()
                exit()

            # 2. Recreate the socket
            log("Reinitializing the server socket...", 3)
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # 3. Re-bind to the configured address and port
            log("Rebinding to the server address and port...", 3)
            server_sock.bind((configuration["server_bind_address"], int(configuration["server_port"])))

            # 4. Resume listening for connections
            log("Reconfiguring the server socket to listen for connections...", 3)
            server_sock.listen(5)
            log("Socket recovery successful. Resuming normal operations.", 3)

            return server_sock  # Pass the new socket back to the calling code if necessary
        except OSError as error:
            log(f"ERROR-M-AR-00-01-01: Operating System threw and error: {error}", 4)
            log("The server was unable to recover from the socket error.", 1)
            traceback_func()
            return None  # Optionally handle graceful shutdown or further retries
        except Exception as error:
            log(f"ERROR-M-CES-00-01-02: Unexpected error: {error}", 4)
            log("Unexpected error on attempting recovery", 1)
            traceback_func()
    elif context == "":
        pass
    else:
        log(f"No recovery logic defined for context: {context}", 4)
        log("Unable to recover from the encountered issue.", 1)

def main():
    log(f"Initializing server...", 3)
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if not os.path.isfile(CERT_FILE):
            raise FileNotFoundError(f"Certificate file not found: {CERT_FILE}")
        if not os.path.isfile(KEY_FILE):
            raise FileNotFoundError(f"Key file not found: {KEY_FILE}")
        context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    except FileNotFoundError as e:
        log(f"ERROR-M-M-00-01-01: File not found: {e}", 4)
        log("You have no certificates generated...", 1)
        traceback_func()
        ssl_certificate()
    except PermissionError as e:
        log(f"ERROR-M-M-00-01-02: Permission denied: {e}", 4)
        log("This program must be run with administrator privileges.", 1)
        traceback_func()
    except ssl.SSLError as e:
        log(f"ERROR-M-M-00-01-03: SSL error: {e}", 4)
        log("SSL couldn't configure. For more info enable debug in config.", 1)
        traceback_func()
    except Exception as e:
        log(f"ERROR-M-M-00-01-04: Unexpected error: {e}", 4)
        log("Unexpected error inside on creating socket.", 1)
        traceback_func()
        input()
        exit()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((configuration["server_bind_address"], int(configuration["server_port"])))
            server_sock.listen(5)
            log("Server started...", 3)
            load_users_credentials()
            try:
                with context.wrap_socket(server_sock, server_side=True) as secure_server_sock:
                    while True:
                        try:
                            client_connection, client_addr_port = secure_server_sock.accept()
                            log(f"Connection from {client_addr_port}", 3)

                            token = client_authentication.authenticate_client(client_connection, client_addr_port)
                            if token:
                                # Start client thread upon successful authentication
                                client_thread = threading.Thread(target=client_thread_handler.handle_client, args=(client_connection, client_addr_port, token))
                                client_thread.daemon = True
                                client_thread.start()
                            else:
                                log(f"Failed authentication for client {client_addr_port[0]}. Connection closed.", 1)

                        except ConnectionResetError as e:
                            log(f"ERROR-M-M-00-04-01: Client connection reset: {e}", 4)
                            log("The client abruptly disconnected during communication.", 1)
                            traceback_func()
                        except ssl.SSLError as e:
                            log(f"ERROR-M-M-00-04-02: SSL handshake failed: {e}", 4)
                            log("An error occurred during the SSL handshake with the client.", 1)
                            traceback_func()
                        except Exception as e:
                            log(f"ERROR-M-M-00-04-03: Unexpected error: {e}", 4)
                            log("Unexpected error with client", 1)
                            traceback_func()
            except ssl.SSLError as e:
                log(f"ERROR-M-M-00-03-01: SSL error: {e}", 4)
                log("An issue occurred while setting up the secure socket.", 1)
                traceback_func()
            except Exception as e:
                log(f"ERROR-M-M-00-03-02: Unexpected error: {e}", 4)
                log("An unknown error occurred in the secure socket operation.", 1)
                traceback_func()
    except KeyError as e:
        log(f"ERROR-M-M-00-02-01: Configuration error: {e}", 4)
        log("A required configuration key is missing or incorrect. Deleting the config file might fix this.", 1)
        traceback_func()
        input()
        exit()
    except socket.gaierror as e:
        log(f"ERROR-M-M-00-02-02: Invalid bind address: {e}", 4)
        log("The server bind address could not be resolved to a valid IP.", 1)
        traceback_func()
        input()
        exit()
    except OSError as e:
        log(f"ERROR-M-M-00-02-03: Socket error: {e}", 4)
        log("A system-level socket error occurred, possibly due to port issues.", 1)
        traceback_func()
        attempt_recovery("socket")
    except Exception as e:
        log(f"ERROR-M-M-00-02-04: Unexpected error: {e}", 4)
        log("An unknown error occurred during server initialization.", 1)
        traceback_func()
    input()


def load_users_credentials():
    global user_credentials
    if not os.path.exists("credentials"):
        os.makedirs("credentials")
    if not os.path.exists("credentials/users_creds.json"):
        try:
            with open("credentials/users_creds.json", "w") as user_cred_file:
                default_creds = {"admin": "Pa$$w0rd"}
                log("Default credentials set: admin - Pa$$w0rd", 3)
                json.dump(default_creds, user_cred_file)  # Use json.dump to write to the file
        except PermissionError as perm_error:
            log(f"ERROR-M-LUC-00-01-01: Permission error: {perm_error}", 4)
            log("Unable to write to the credentials file due to insufficient permissions.", 1)
            traceback_func()
            return False
        except OSError as os_error:
            log(f"ERROR-M-LUC-00-01-02: OS error: {os_error}", 4)
            log("Failed to create or write to the credentials file due to a system issue.", 1)
            traceback_func()
            return False
        except Exception as error:
            log(f"ERROR-M-LUC-00-01-03: Unexpected error: {error}", 4)
            log("Unexpected error on loading credentials!", 1)
            traceback_func()
    try:
        with open("credentials/users_creds.json", "r") as user_cred_file:
            user_credentials = json.load(user_cred_file)
            return True

    except json.JSONDecodeError as error:
        log(f"ERROR-M-LUC-00-02-01: JSON file format: {error}", 4)
        log("User credentials file is malformed. Creating a backup and resetting it.", 2)
        traceback_func()
        try:
            with open("credentials/user_creds.json", "r") as recover_file:
                recovered_file_contents = recover_file.readline()
                log(f"Recovered the following: {recovered_file_contents}", 2)
                with open("credentials/backed_up.txt", "w") as backup_file:
                    backup_file.writelines(recovered_file_contents)
        except Exception as error:
            log(f"ERROR-M-LUC-00-03-01: Exception thrown while attempting to handle previous exception: {error}", 4)
            log("ERROR thrown when handling the above error!", 1)
            traceback_func()
        return False
    except FileNotFoundError as fnf_error:
        log(f"ERROR-M-LUC-00-02-02: File not found: {fnf_error}", 4)
        log("The credentials file is missing.", 1)
        traceback_func()
        return False
    except PermissionError as perm_error:
        log(f"ERROR-M-LUC-00-02-03: Permission error: {perm_error}", 4)
        log("Unable to read the credentials file due to insufficient permissions.", 1)
        traceback_func()
        return False
    except OSError as os_error:
        log(f"ERROR-M-LUC-00-02-04: OS error: {os_error}", 4)
        log("Failed to open or read the credentials file due to a system issue.", 1)
        traceback_func()
        return False
    except Exception as error:
        log(f"ERROR-M-LUC-00-02-05: Unexpected error: {error}", 4)
        log("Unexpected error on loading user credentials.", 1)
        traceback_func()

import config_handler
import update_checker
import client_authentication
import client_thread_handler

if __name__ == "__main__":
    update_checker.update_main()
    configuration = config_handler.configuration_handler()
    if configuration:
        print("Configuration loaded...")
        for key, value in configuration.items():
            print(f"{key}:{value}")
    main()