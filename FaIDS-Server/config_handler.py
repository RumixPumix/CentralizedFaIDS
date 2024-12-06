import json
import os
import sys
import time
from datetime import datetime

configuration = {}
config_updated_bool = False

# Logging function
def log(message, opcode):
    def get_current_date_time():
        current_datetime = datetime.now()
        return current_datetime.strftime("%Y-%m-%d %H:%M:%S") 
    opcodes = ["None", "ERROR", "WARNING", "INFO", "DEBUG"]
    print(f"[{get_current_date_time()}] [{opcodes[opcode]}]: {message}")

# Self-restart function
def self_restart():
    log("Restarting the script...", 3)
    time.sleep(3)
    os.execv(sys.executable, ["python"] + sys.argv)

# Apply configuration by reading the config file
def apply_configuration():
    global configuration
    try:
        with open("config.json", "r") as config_file:
            configuration = json.load(config_file)
            return configuration
    except FileNotFoundError:
        log("config.json file not found.", 1)
        return False
    except json.JSONDecodeError:
        log("Error decoding JSON from config.json.", 1)
        return False
    except Exception as error:
        log(f"Unknown error while applying configuration: {error}", 1)
        return False

# First time configuration setup
def configuration_first_time_setup():
    temp_config = {}
    if config_updated_bool and os.path.exists("config.json"):
        current_config = apply_configuration()
        if current_config:
            temp_config.update(current_config)
    
    try:
        # More configuration addition settings
        if "server_bind_address" not in temp_config:
            server_bind_address = input("Input bind IP: ")
            temp_config["server_bind_address"] = server_bind_address
        
        if "server_port" not in temp_config:
            server_port = int(input("Input server port: "))
            temp_config["server_port"] = server_port

        if "debug_test" not in temp_config:
            debug_test = int(input("Input debug num: "))
            temp_config["debug_test"] = debug_test
        
        # Save the new configuration to the file
        try:
            with open("config.json", "w") as config_file:
                json.dump(temp_config, config_file)
                log("Config file saved.", 4)
        except PermissionError:
            log("Permission error: Unable to write to config.json.", 1)
            return False
        except IOError as error:
            log(f"I/O error while saving config: {error}", 1)
            return False
        except Exception as error:
            log(f"Unknown error while saving config: {error}", 1)
            return False
        
        return True
    except (ValueError, Exception) as error:
        log(f"Error during input or configuration: {error}", 1)
        return False

# Main configuration handler
def configuration_handler():
    global config_updated_bool

    if os.path.exists("config.json"):
        if config_updated_bool:
            log("New configuration options! ", 3)
            if configuration_first_time_setup():
                log("Updated the config file.", 4)
                # Update the script to reset the `config_updated_bool`
                with open(__file__, "r+") as program_code:
                    lines = program_code.readlines()
                    for i, line in enumerate(lines):
                        if "config_updated_bool =" in line:
                            lines[i] = "config_updated_bool = False\n"
                            break
                    program_code.seek(0)
                    program_code.writelines(lines)
                    program_code.truncate()
        
        # Apply configuration
        if apply_configuration():
            log("Configuration applied successfully.", 3)
            return (True, configuration)
    else:
        log("config.json not found. Proceeding with initial setup.", 2)
        configuration_first_time_setup()

# Run the configuration handler
if __name__ == "__main__":
    log("This script is usually run by the main program. Proceed only if you know what you're doing.", 2)
    try:
        if input("Y/N: ").lower() == "y":
            configuration_handler()
        else:
            exit()
    except Exception:
        exit()
