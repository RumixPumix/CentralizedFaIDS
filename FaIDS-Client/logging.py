import main

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

def get_current_date_time():
    current_datetime = datetime.now()
    return current_datetime.strftime("%Y-%m-%d %H:%M:%S") 

def log():
    opcodes = [None,"ERROR", "WARNING", "INFO", "DEBUG"]
    color_codes = [None, colorama.Fore.RED, colorama.Fore.YELLOW, colorama.Fore.WHITE, colorama.Fore.MAGENTA]
    message_to_log = f"[{get_current_date_time()}] [{opcodes[opcode]}]: {message}"
    message_to_log_colored = f"{color_codes[opcode]}[{get_current_date_time()}] [{opcodes[opcode]}]: {message}{colorama.Fore.WHITE}"
    print(message_to_log_colored)
    write_log_to_file(message_to_log)


























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