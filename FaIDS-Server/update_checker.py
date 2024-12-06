import time
import os
import sys
import requests
from datetime import datetime
from git import Repo
import main

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_REPO_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, "../"))
# Remote repository URL
REMOTE_REPO_URL = "https://github.com/RumixPumix/CentralizedFaIDS.git"

def log(message, opcode):
    try:
        if opcode == 4:
            if main.configuration["debug_mode"] != True:
                return
    except Exception:
        pass
    def get_current_date_time():
        current_datetime = datetime.now()
        return current_datetime.strftime("%Y-%m-%d %H:%M:%S") 
    opcodes = ["None","ERROR", "WARNING", "INFO", "DEBUG"]
    print(f"[{get_current_date_time()}] [{opcodes[opcode]}]: {message}")

def check_updates():
    if not os.path.exists(LOCAL_REPO_PATH):
        log(f"Local repository not found at {LOCAL_REPO_PATH}. Cloning instead.", 4)
        update()
        return False  # No updates; just cloned the repo.

    repo = Repo(LOCAL_REPO_PATH)

    # Fetch the latest changes from the remote
    repo.remotes.origin.fetch()

    # Get the latest commit hashes for the default branch
    local_hash = repo.head.commit.hexsha
    remote_hash = repo.remotes.origin.refs[repo.active_branch.name].commit.hexsha

    if local_hash != remote_hash:
        log("Updates are available.", 4)
        return True
    else:
        log("Repository is up to date.", 4)
        return False

def update():
    if not os.path.exists(LOCAL_REPO_PATH):
        try:
            log("Cloning the repository...", 4)
            Repo.clone_from(REMOTE_REPO_URL, LOCAL_REPO_PATH)
            log("Repository cloned successfully.", 4)
            return True
        except Exception as error:
            log(f"Unknown error - uc - update 1- {error}", 1)
    else:
        try:
            log("Pulling the latest changes...", 4)
            repo = Repo(LOCAL_REPO_PATH)
            repo.remotes.origin.pull()
            log("Repository updated successfully.", 4)
            return True
        except Exception as error:
            log(f"Unknown error - uc - update 2- {error}", 1)

def update_main():
    if check_updates():
        log("New update found! Do you wish to update?", 3)
        try:
            if input("Y/N:").lower() == "y":
                if update():
                    log("Successfully updated! Restarting...", 3)
                    time.sleep(3)
                    main.self_restart()
                else:
                    log("Failed to update.", 2)
            else:
                exit()
        except Exception as error:
            log(f"Unknown error: uc - update_main - {error}", 1)
    else:
        log("No updates required.", 3)

# Main logic for testing
if __name__ == "__main__":
    log("This script is usually run by the main program. Proceed only if you know what you're doing.", 2)
    try:
        if input("Y/N: ").lower() == "y":
            if check_updates():
                log("New update found! Do you wish to update?", 3)
                try:
                    if input("Y/N:").lower() == "y":
                        update()
                    else:
                        exit()
                except Exception as error:
                    log(f"Unknown error: uc - main - {error}", 1)
            else:
                log("No updates required.", 3)
        else:
            exit()
    except ValueError:
        exit()
