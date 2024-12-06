import socket
import ssl
import json
import os
import sys
import time
from datetime import datetime
import config_handler
import update_checker

configuration = {}

def log(message, opcode):
    try:
        if opcode == 4:
            if configuration["debug_mode"] != True:
                return
    except Exception:
        pass
    def get_current_date_time():
        current_datetime = datetime.now()
        return current_datetime.strftime("%Y-%m-%d %H:%M:%S") 
    opcodes = ["None","ERROR", "WARNING", "INFO", "DEBUG"]
    print(f"[{get_current_date_time()}] [{opcodes[opcode]}]: {message}")

def self_restart():
    log("Restarting the script...", 3)
    time.sleep(3)
    os.execv(sys.executable, ["python"] + sys.argv)

def main():
    print("Done test 1 passed")
    print(configuration)
    input()

if __name__ == "__main__":
    update_checker.update_main()
    try:
        status, config = config_handler.configuration_handler()
        if status:
            configuration = config
            main()
        else:
            log("Configuration failed, delete the config.json file and try again. Check for updates if the previous didn't fix the issue.", 1)
            input()
    except Exception as error:
        log(f"Unknown error - main - {error}", 1)