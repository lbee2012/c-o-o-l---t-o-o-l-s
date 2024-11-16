import os
import subprocess
import sys
import time
import winsound  # For sound notification
from pathlib import Path
import msvcrt  # To capture keypresses (Enter and Esc)
import logging  # For log file generation
from datetime import datetime  # To generate timestamped log file names

# Define default main and branch folder names and locations
main_folder_name = "Automatic Setup"
documents_path = Path.home() / "Documents"  # Path to 'Documents' directory
main_folder_path = documents_path / main_folder_name
branch_installation_folder_name = "Ngot"
branch_log_folder_name = "log"
branch_installation_folder_path = main_folder_path / branch_installation_folder_name
branch_log_folder_path = main_folder_path / branch_log_folder_name

# Ensure the main and branch folders exist
main_folder_path.mkdir(parents=True, exist_ok=True)
branch_installation_folder_path.mkdir(parents=True, exist_ok=True)
branch_log_folder_path.mkdir(parents=True, exist_ok=True)

# Generate a unique log file name based on the current date and time
current_time = datetime.now().strftime("%d-%m-%y %H-%M-%S")
log_file = branch_log_folder_path / f"{current_time}.log"

# Configure logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("Log file created at: %s", log_file)

# Function to ensure the folder exists
def ensure_installation_folder():
    if not branch_installation_folder_path.exists():
        logging.info("Creating installation folder at: %s", branch_installation_folder_path)
        print(f"Creating installation folder at: {branch_installation_folder_path}")
        branch_installation_folder_path.mkdir(parents=True, exist_ok=True)
    return branch_installation_folder_path

# Function to detect keypress (Enter/ESC)
def wait_for_keypress():
    print("\nPress [ENTER] to restart the system or [ESC] to exit.\n")
    while True:
        key = msvcrt.getch()  # Wait for key press
        if key == b'\r':  # Enter key
            return "Enter"
        elif key == b'\x1b':  # Escape key
            return "Esc"

# Main logic
if __name__ == "__main__":
    logging.info("Program started.")

    # Ensure the installation folder exists
    folder_path = [ensure_installation_folder()]

    # Check if there are any setup files in the folder
    setup_files = [
        file for file in os.listdir(folder_path[0]) if file.endswith(('.exe', '.msi'))
    ]
    setup_files.sort()

    if not setup_files:  # If the folder is empty
        logging.warning("Folder is empty at: %s", folder_path[0])
        print(f"Folder is empty at: {folder_path[0]}")
        print("\nReturn when you have added the list of setup files to process.")
        input("Press [ENTER] to exit the program.")
        logging.info("Program exited due to empty folder.")
        sys.exit(0)

    # Process each setup file
    for setup_file in setup_files:
        setup_path = folder_path[0] / setup_file
        try:
            print(f"\nReady to run {setup_file}.")
            logging.info("Ready to run %s", setup_file)
            print("\nOptions:")
            print("[c] Continue")
            print("[s] Skip")
            print("[0] Exit")
            user_input = input("\nEnter your choice: ").strip().lower()

            if user_input in ['c', 'continue']:
                logging.info("Running %s", setup_file)
                print(f"\nRunning {setup_file}...")
                subprocess.run(setup_path, shell=True)
                logging.info("%s has been installed successfully.", setup_file)
                print(f"\n{setup_file} has done.")
            elif user_input in ['s', 'skip']:
                logging.info("Skipping %s", setup_file)
                print(f"\nSkipping {setup_file}...")
            elif user_input == '0':
                logging.info("User chose to exit during setup file processing.")
                for i in range(3, 0, -1):
                    print(f"Exiting program in {i} seconds...", end="\r")
                    time.sleep(1)
                print("Exiting now!                      ", end="\r")
                logging.info("Program exited by user choice.")
                sys.exit(0)
            else:
                logging.warning("Invalid input from user: %s", user_input)
                print("\nInvalid input. Please try again.")
        except Exception as e:
            logging.error("Failed to run %s: %s", setup_file, e)
            print(f"\nFailed to run {setup_file}: {e}")

    # Sound notification after all files are processed
    print("\nAll setup files have been processed.")
    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)  # Windows Boom sound
    print("\nYou might reboot your system.")
    logging.info("All setup files processed.")

    # Reboot management
    user_choice = wait_for_keypress()
    
    if user_choice == "Enter":
        logging.info("User chose to reboot the system.")
        for i in range(5, 0, -1):  # Countdown for reboot
            print(f"Rebooting system in {i} seconds...    ", end="\r")
            time.sleep(1)
        print("Restarting now!                      ", end="\r")
        logging.info("System restarting now.")
        subprocess.run("shutdown /r /t 0", shell=True)  # Reboot command
    elif user_choice == "Esc":
        logging.info("User chose to exit without rebooting.")
        for i in range(3, 0, -1):  # Countdown for exit
            print(f"Exiting program in {i} seconds...", end="\r")
            time.sleep(1)
        print("Exiting now!                      ", end="\r")
        logging.info("Program exited without rebooting.")
        sys.exit(0)