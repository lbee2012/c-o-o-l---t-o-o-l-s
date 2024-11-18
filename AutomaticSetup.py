import os
import subprocess
import sys
import time
import winsound
from pathlib import Path
import msvcrt
import logging
from datetime import datetime

# Define folders
main_folder_name = "Automatic Setup"
documents_path = Path.home() / "Documents"
main_folder_path = documents_path / main_folder_name
installation_folder_name = "Ngot"
log_folder_name = "log"
installation_folder_path = main_folder_path / installation_folder_name
log_folder_path = main_folder_path / log_folder_name

# Ensure folders exist
main_folder_path.mkdir(parents=True, exist_ok=True)
installation_folder_path.mkdir(parents=True, exist_ok=True)
log_folder_path.mkdir(parents=True, exist_ok=True)

# Logging configuration
current_time = datetime.now().strftime("%d-%m-%y %H-%M-%S")
log_file = log_folder_path / f"{current_time}.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("Program started.")

# Status dictionary for tracking setup file statuses
statuses = {}

def check_storage():
    """Check if storage folder exists and is not empty."""
    if not installation_folder_path.exists():
        logging.info("Creating installation folder.")
        installation_folder_path.mkdir(parents=True, exist_ok=True)

    setup_files = [
        file for file in os.listdir(installation_folder_path) if file.endswith(('.exe', '.msi'))
    ]
    if not setup_files:
        logging.warning("Storage folder is empty.")
        print(f"\nStorage folder is empty: {installation_folder_path}")
        print("Please add setup files to the folder and try again.")
        input("Press [ENTER] to exit.")
        sys.exit(0)
    return setup_files

def print_summary():
    """Print the summary of setup statuses."""
    os.system('cls')  # Clear screen
    print("\nSummary of setup files:")
    print("=" * 60)
    for file, status in statuses.items():
        print(f"  {file.ljust(50)}: {status}")
    print("=" * 60)
    print("\nSetup process completed.")

def wait_for_keypress():
    """Prompt user to reboot or exit."""
    print("\nWould you like to:")
    print("[ENTER] Reboot")
    print("[ESC] Exit\n")
    while True:
        key = msvcrt.getch()
        if key == b'\r':  # Enter
            return "Reboot"
        elif key == b'\x1b':  # Escape
            return "Exit"

def countdown(message, seconds=3):
    """Display a countdown message on the same line."""
    for i in range(seconds, 0, -1):
        print(f"\r{message} {i} seconds...{' ' * 10}", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 50, end="\r")  # Clear the line after countdown

def process_setup_files():
    """Process each setup file in the storage folder."""
    setup_files = check_storage()
    setup_files.sort()

    for setup_file in setup_files:
        statuses[setup_file] = "In progress"
        os.system('cls')  # Clear screen
        print(f"Ready to run {setup_file}\n")
        print("Options:")
        print("[c] Continue")
        print("[s] Skip")
        print("[0] Exit")
        user_input = input("\nEnter your choice: ").strip().lower()

        if user_input in ['c', 'continue']:
            print(f"\nProcessing: {setup_file}")
            try:
                # Run the setup file
                subprocess.run(str(installation_folder_path / setup_file), shell=True)
                statuses[setup_file] = "Successed"
                print(f"\nStatus: Successed\n")
            except Exception as e:
                statuses[setup_file] = "Error"
                print(f"\nStatus: Error\n")
                logging.error("Failed to run %s: %s", setup_file, e)
            
            # Countdown before moving to the next file in the same line
            countdown("Moving to the next file in", 3)

        elif user_input in ['s', 'skip']:
            statuses[setup_file] = "Skipped"
            print(f"\nStatus: Skipped\n")
            logging.info("Skipped %s", setup_file)
            
            # Countdown for skipping in the same line
            countdown("Skipping in", 1)

        elif user_input == '0':
            logging.info("User chose to exit.")
            
            # Countdown for exiting in the same line
            countdown("Exiting in", 3)
            sys.exit(0)

        else:
            print("\nInvalid choice. Please try again.")
            statuses[setup_file] = "Error"

# Main execution
if __name__ == "__main__":
    process_setup_files()
    print_summary()
    
    # Sound notification
    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)

    # Reboot or exit
    choice = wait_for_keypress()
    if choice == "Reboot":
        logging.info("User chose to reboot.")
        countdown("Rebooting in", 5)
        subprocess.run("shutdown /r /t 0", shell=True)
    elif choice == "Exit":
        logging.info("User chose to exit without rebooting.")
        countdown("Exiting in", 3)
        sys.exit(0)