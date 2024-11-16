import os
import subprocess
import sys
import time
import winsound  # For sound notification
from pathlib import Path
import msvcrt  # To capture keypresses (Enter and Esc)

# Define default folder name and location
default_folder_name = "Automatic Setup Folder"
documents_path = Path.home() / "Documents"  # Path to 'Documents' directory
default_folder_path = documents_path / default_folder_name

# Function to ensure the folder exists
def ensure_setup_folder():
    if not default_folder_path.exists():
        print(f"Creating folder at: {default_folder_path}")
        default_folder_path.mkdir(parents=True, exist_ok=True)
    return default_folder_path

# Function to detect keypress (Enter/ESC)
def wait_for_keypress():
    print("\nPress Enter to restart the system or Esc to exit.\n")
    while True:
        key = msvcrt.getch()  # Wait for key press
        if key == b'\r':  # Enter key
            return "Enter"
        elif key == b'\x1b':  # Escape key
            return "Esc"

# Main logic
if __name__ == "__main__":
    # Ensure the folder exists in the Documents directory
    folder_path = [ensure_setup_folder()]

    # Check if there are any setup files in the folder
    setup_files = [
        file for file in os.listdir(folder_path[0]) if file.endswith(('.exe', '.msi'))
    ]
    setup_files.sort()

    if not setup_files:  # If the folder is empty
        print(f"Folder is empty at: {folder_path[0]}")
        print("\nReturn when you have added the list of setup files to process.")
        input("Press [Enter] to exit the program.")
        sys.exit(0)

    # Process each setup file
    for setup_file in setup_files:
        setup_path = folder_path[0] / setup_file
        try:
            print(f"\nReady to run {setup_file}.")
            print("\nOptions:")
            print("[c] Continue")
            print("[s] Skip")
            print("[0] Exit")
            user_input = input("\nEnter your choice: ").strip().lower()

            if user_input in ['c', 'continue']:
                print(f"\nRunning {setup_file}...")
                subprocess.run(setup_path, shell=True)
                print(f"\n{setup_file} has done.")
            elif user_input in ['s', 'skip']:
                print(f"\nSkipping {setup_file}...")
            elif user_input == '0':
                for i in range(3, 0, -1):
                    print(f"Exiting program in {i} seconds...", end="\r")
                    time.sleep(1)
                print("Exiting now!                    ", end="\r")
                sys.exit(0)
            else:
                print("\nInvalid input. Please try again.")
        except Exception as e:
            print(f"\nFailed to run {setup_file}: {e}")

    # Sound notification after all files are processed
    print("\nAll setup files have been processed.")
    print("\nYou might reboot your system.")
    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)  # Windows Boom sound

    # Reboot management
    user_choice = wait_for_keypress()
    
    if user_choice == "Enter":
        for i in range(5, 0, -1):  # Countdown for reboot
            print(f"Rebooting system in {i} seconds...", end="\r")
            time.sleep(1)
        print("Restarting now!            ", end="\r")
        subprocess.run("shutdown /r /t 0", shell=True)  # Reboot command
    elif user_choice == "Esc":
        for i in range(3, 0, -1):  # Countdown for exit
            print(f"Exiting program in {i} seconds...", end="\r")
            time.sleep(1)
        print("Exiting now!                    ", end="\r")
        sys.exit(0)