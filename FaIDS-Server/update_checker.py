import time
import os
import sys
import requests
from datetime import datetime
from git import Repo
import main

# Set your GitHub repository details
OWNER = "RumixPumix"
REPO_NAME = "FaIDS"
REPO_PATH = "../../CentralizedFaIDS"
BRANCH = "main"  # Name of the current script
CURRENT_VERSION = "1.0.0"  # Current version of your script (hardcoded or from a version file)
REMOTE_URL = "https://github.com/RumixPumix/CentralizedFaIDS.git"

# GitHub API URL for releases
RELEASES_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/releases/latest"

def log(message, opcode):
    def get_current_date_time():
        current_datetime = datetime.now()
        return current_datetime.strftime("%Y-%m-%d %H:%M:%S") 
    opcodes = ["None","ERROR", "WARNING", "INFO", "DEBUG"]
    print(f"[{get_current_date_time()}] [{opcodes[opcode]}]: {message}")

# Function to check for updates
def check_updates():
    """
    Check if the local repository is up-to-date with the remote repository.
    Returns True if updates are available, otherwise False.
    """
    try:
        # Get the latest commit hash from GitHub
        api_url = f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/commits/{BRANCH}"
        response = requests.get(api_url)
        response.raise_for_status()
        remote_commit_hash = response.json()["sha"]

        # Get the latest commit hash from the local repository
        if os.path.exists(REPO_PATH):
            repo = Repo(REPO_PATH)
            local_commit_hash = repo.head.commit.hexsha
        else:
            log("Local repository does not exist. Updates are required.", 4)
            return True  # If the repo doesn't exist locally, assume updates are needed

        # Compare hashes
        if remote_commit_hash != local_commit_hash:
            log("Updates are available.", 4)
            return True
        else:
            log("No updates available. Local repository is up-to-date.", 4)
            return False

    except Exception as e:
        print(f"Error checking updates: {e}")
        return False

# Function to update the local repository
def update():
    """
    Pull updates from the remote repository.
    """
    try:
        if not os.path.exists(REPO_PATH):
            log(f"Cloning repository to {REPO_PATH}...", 4)
            Repo.clone_from(REMOTE_URL, REPO_PATH)
        else:
            log(f"Pulling updates into {REPO_PATH}...", 4)
            repo = Repo(REPO_PATH)
            repo.remotes.origin.pull()
        log("Repository updated successfully!", 4)
        main.self_restart()
    except Exception as e:
        log(f"Error updating repository: {e}", 2)

def update_main():
    if check_updates():
        log("New update found! Do you wish to update?", 3)
        try:
            if input("Y/N:").lower() == "y":
                update()
            else:
                exit()
        except Exception as error:
            log(f"Unknown error: uc - update_main - {error}")
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
                    log(f"Unknown error: uc - main - {error}")
            else:
                log("No updates required.", 3)
        else:
            exit()
    except ValueError:
        exit()



















def update():
    pass

def check_update():
    return False