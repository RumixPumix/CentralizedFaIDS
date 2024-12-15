
def traceback_func():
    try:
        debug_mode = configuration.get("debug_mode", True)
    except:
        debug_mode = True
    if debug_mode == True:
        tb = traceback.format_exc()  # Get the full exception traceback as a string
        log(tb, 4)

def get_current_date():
            """Get the current date in 'YYYYMMDD' format."""
            current_date = datetime.now()
            return current_date.strftime("%Y-%m-%d-server")

def check_for_old_logs():
    """Check for old logs in the 'logs' folder and zip them if necessary."""
    for file in os.listdir("logs"):
        file_path = os.path.join("logs", file)
        if os.path.isfile(file_path) and file != f"{get_current_date()}.txt":
            zip_and_move(file, file_path)

def zip_and_move(file_name, log_path):
    """Zip a file and move it to the 'logs/old_logs' folder."""
    old_logs_dir = "logs/old_logs"
    os.makedirs(old_logs_dir, exist_ok=True)  # Ensure the 'old_logs' folder exists

    zip_path = os.path.join(old_logs_dir, f"{file_name}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(log_path, arcname=file_name)  # Add the file to the zip with its original name

    os.remove(log_path)  # Delete the original file

def write_log_to_file(logged_message):
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

def get_current_date_time():
    current_datetime = datetime.now()
    return current_datetime.strftime("%Y-%m-%d %H:%M:%S") 

def log(message, opcode=3):
    opcodes = [None,"ERROR", "WARNING", "INFO", "DEBUG"]
    color_codes = [None, colorama.Fore.RED, colorama.Fore.YELLOW, colorama.Fore.WHITE, colorama.Fore.MAGENTA]
    message_to_log = f"[{get_current_date_time()}] [{opcodes[opcode]}]: {message}"
    message_to_log_colored = f"{color_codes[opcode]}[{get_current_date_time()}] [{opcodes[opcode]}]: {message}{colorama.Fore.WHITE}"
    print(message_to_log_colored)
    write_log_to_file(message_to_log)

def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

import os
import zipfile
import traceback
import colorama
import platform
from datetime import datetime
from main import configuration