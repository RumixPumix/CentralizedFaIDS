import time
import os
from git import Repo
from main import log
from main import self_restart
from main import traceback_func

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_REPO_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, "../"))
# Remote repository URL
REMOTE_REPO_URL = "https://github.com/RumixPumix/CentralizedFaIDS.git"

def check_updates():
    if not os.path.exists(LOCAL_REPO_PATH):
        log(f"Local repository not found at {LOCAL_REPO_PATH}. Cloning instead.", 4)
        log("You only installed this script? Really?", 3)
        update()
        return False  # No updates; just cloned the repo.

    repo = Repo(LOCAL_REPO_PATH)

    # Fetch the latest changes from the remote
    repo.remotes.origin.fetch()

    # Get the latest commit hashes for the default branch
    local_hash = repo.head.commit.hexsha
    remote_hash = repo.remotes.origin.refs[repo.active_branch.name].commit.hexsha

    if local_hash != remote_hash:
        log("Updates are available.", 3)
        return True
    else:
        log("Repository is up to date.", 3)
        return False

def update():
    if not os.path.exists(LOCAL_REPO_PATH):
        try:
            log("Cloning the repository...", 1)
            Repo.clone_from(REMOTE_REPO_URL, LOCAL_REPO_PATH)
            log("Repository cloned successfully.", 1)
            return True
        except Exception as error:
            log(f"ERROR-UC-U0-00-01-01: Unexpected error: {error}", 4)
            log("Failed to clone the repository.", 1)
            traceback_func()
    else:
        try:
            log("Pulling the latest changes...", 3)
            repo = Repo(LOCAL_REPO_PATH)
            repo.remotes.origin.pull()
            log("Repository updated successfully.", 3)
            return True
        except Exception as error:
            log(f"ERROR-UC-U0-00-02-01: Unexpected error: {error}", 4)
            log("Failed to clone the repository.", 1)
            traceback_func()

def update_main():
    if check_updates():
        log("New update found! Do you wish to update?", 3)
        try:
            if input("Y/N:").lower() == "y":
                if update():
                    log("Successfully updated! Restarting...", 3)
                    time.sleep(3)
                    self_restart()
                else:
                    log("Failed to update.", 2)
            else:
                exit()
        except Exception as error:
            log(f"ERROR-UC-UM-00-01-01: Unexpected error: {error}", 4)
            log("Unexpected error occured. ", 1)
            traceback_func()
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
                except Exception:
                    exit()
            else:
                log("No updates required.", 3)
        else:
            exit()
    except ValueError:
        exit()
