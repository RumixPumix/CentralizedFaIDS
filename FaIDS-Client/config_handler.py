import json
import os
import re
from logging import log
from logging import traceback_func
config_updated_bool = False

# Logging function

def apply_current_config(configuration):
        try:
            with open("config.json", "w") as config_file:
                json.dump(configuration, config_file)
                log("Config file saved.", 4)
        except PermissionError as error:
            log(f"ERROR-CH-ACC-00-01-01: Permission error: {error}", 4)
            log("Unable to write config to file config.json", 1)
            return False
        except IOError as error:
            log(f"ERROR-CH-ACC-00-01-02: I/O error: {error}", 4)
            log("I/O Error while saving config", 1)
            return False
        except Exception as error:
            log(f"ERROR-CH-ACC-00-01-03: Unknown error: {error}", 1)
            log("Unknown error occured on config applying", 1)
            return False

def validate_config(configuration):
    def is_valid_ip(ip_address):
        try:
            # Regex for valid IPv4 excluding any octet being 255
            ipv4_pattern = r"^(?!255(\.|\b))(?!\d{1,3}\.255(\.|\b))(\d{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-4])\.(\d{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-4])\.(\d{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-4])\.(\d{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-4])$"
            
            # Check if it matches the IPv4 regex
            if re.match(ipv4_pattern, ip_address):
                return True  # Valid IPv4 address
            return False
        except Exception as error:
            log(f"Validating IP failed: {error}", 4)
            return False
    def is_valid_port(port):
        try:
            if port >= 1 and port <= 65535:
                return True
            else:
                return False
        except Exception as error:
            log(f"Validating port failed: {error}", 4)
            return False
    def is_valid_debug_mode(debug):
        try:
            if debug == True or debug == False or debug.lower() == "true" or debug.lower() == "false":
                return True
            else:
                return False
        except Exception as error:
            log(f"Validating debug mode failed: {error}", 4)
    try:
        ip_address = configuration["server_ip_address"]
        if not is_valid_ip(ip_address):
            log("Invalid IP address. Please check the server_ip_address configuration.", 1)
            return False
        port = configuration["server_port"]
        if not is_valid_port(port):
            log("Invalid port. Port should be between 1 and 65535.", 1)
            return False
        debug = configuration["debug_mode"]
        if not is_valid_debug_mode(debug):
            log("Invalid debug mode value. It should be either 'True' or 'False'.", 1)
            return False
        return True
    except KeyError as error:
        # First there is a debug statement giving us the error code. Number 4 signifies that when this log gets printed there's a debug statement next to it.
        log(f"ERROR-CH-VC-00-01-01: Error on validating config: {error}", 4)
        # Then there's the user error, that gives a brief description of what might've happened. Number 1 signifies the "Error" statement.
        log("Config file is not configured properly. Keys were tampered with.", 1)
        
    except TypeError as error:
        # Debug log for the technical details of the TypeError
        log(f"ERROR-CH-VC-00-01-02: Unexpected type encountered: {error}", 4)
        # User-friendly message for TypeError
        log("A type mismatch occurred while processing the data. Please check the data types in the configuration.", 1)
        traceback_func()
        
    except ValueError as error:
        # Debug log for the technical details of the ValueError
        log(f"ERROR-CH-VC-00-01-03: Invalid value encountered: {error}", 4)
        # User-friendly message for ValueError
        log("An invalid value was encountered. Please verify the values in the configuration.", 1)
        traceback_func()
        
    except AttributeError as error:
        # Debug log for the technical details of the AttributeError
        log(f"ERROR-CH-VC-00-01-04: Attribute not found: {error}", 4)
        # User-friendly message for AttributeError
        log("An attribute is missing or misconfigured in the configuration file. Please review the setup.", 1)
        traceback_func()
        
    except IndexError as error:
        # Debug log for the technical details of the IndexError
        log(f"ERROR-CH-VC-00-01-05: Index out of range: {error}", 4)
        # User-friendly message for IndexError
        log("An index out of range error occurred. Please check array or list indexes in the configuration.", 1)
        traceback_func()
        
    except Exception as error:
        # Debug log for the technical details of the unknown error
        log(f"ERROR-CH-VC-00-01-01: Unexpected error: {error}", 4)
        # User-friendly message for any unexpected errors
        log("An unexpected error occurred. Please check the configuration and try again.", 1)
        traceback_func()
# Apply configuration by reading the config file
def get_configuration():
    try:
        with open("config.json", "r") as config_file:
            configuration = json.load(config_file)
            if validate_config(configuration):
                return configuration
            else:
                log("Configuration wasn't validated", 1)
                try:
                    if input("Do you wish to reset the config? (Y/N): ").lower() == "y":
                        return configuration_first_time_setup() 
                    else:
                        exit()
                except:
                    exit()
    except FileNotFoundError:
        log(f"ERROR-CH-AC-00-01-01: File not found: {error}", 4)
        log("File not found when applying the config.", 1)
        return False
    except json.JSONDecodeError as error:
        log(f"ERROR-CH-AC-00-01-02: JSON Error: {error}", 4)
        log("JSON error occured on applying config.", 1)
        return False
    except Exception as error:
        log(f"ERROR-CH-AC-00-01-03: Unexpected error: {error}", 4)
        log("Unexpected error occured on applying config.", 1)
        traceback_func()
        return False

# First time configuration setup
def configuration_first_time_setup():
    temp_config = {}
    if config_updated_bool and os.path.exists("config.json"):
        current_config = get_configuration()
        if current_config:
            temp_config.update(current_config)
    
    try:
        # More configuration addition settings
        if "server_ip_address" not in temp_config:
            server_ip_address = input("Input centralized server IP: ")
            temp_config["server_ip_address"] = server_ip_address
        
        if "server_port" not in temp_config:
            server_port = int(input("Input server port: "))
            temp_config["server_port"] = server_port

        if "debug_mode" not in temp_config:
            debug_mode = ""
            while debug_mode.upper() != "T" and debug_mode.upper() != "F":
                debug_mode = input("Debug mode (T/F): ")
            if debug_mode.upper() == "T":
                temp_config["debug_mode"] = True
            else:
                temp_config["debug_mode"] = False

        if not validate_config(temp_config):
            log("Config wasn't validated! Want to try again?")
            try:
                if input("Y/N:").lower() == "y":
                    configuration_first_time_setup()
                else:
                    exit()
            except:
                exit()
        
        # Save the new configuration to the file
        return temp_config
    except (ValueError, Exception) as error:
        log(f"ERROR-CH-CFTS-00-01-01: Unexpected error: {error}", 4)
        log("Unexpected error on config input!", 1)
        traceback_func()
        return False

# Main configuration handler
def configuration_handler():
    global config_updated_bool

    if os.path.exists("config.json"):
        if config_updated_bool:
            log("New configuration options! ", 3)
            configuration = configuration_first_time_setup()
            if configuration:
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
                apply_current_config(configuration)
                return
        
        # Apply configuration
        configuration = get_configuration()
        if configuration:
            log("Configuration applied successfully.", 3)
            return configuration
        else:
            log(f"No configuration was returned by apply_configuration function. ", 1)
    else:
        log("config.json not found. Proceeding with initial setup.", 2)
        configuration = configuration_first_time_setup()
        apply_current_config(configuration)
        return configuration

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
