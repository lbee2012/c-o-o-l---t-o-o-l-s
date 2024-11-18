import os
import subprocess
import sys
import time
import winsound
from pathlib import Path
import logging
from datetime import datetime
from pywinauto import Application

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
        print(f"Processing: {setup_file}\n")
        try:
            setup_path = str(installation_folder_path / setup_file)
            # Start the installer
            app = Application(backend="win32").start(setup_path)
            time.sleep(2)  # Wait for the installer to initialize

            # Look for the installer window
            window = None
            for _ in range(30):  # Retry for up to 30 seconds
                try:
                    window = app.window(best_match='*Setup*')
                    if window.exists():
                        break
                except:
                    pass
                time.sleep(1)
            if not window:
                raise Exception("Installer window not found.")

            # Automate the installation steps
            while True:
                window.wait('visible', timeout=10)
                window.set_focus()
                
                # Define possible button texts
                button_texts = ['Next >', 'Next', '&Next', 'I &Agree', '&Install', 'Install', '&Finish', 'Finish', 'Close']
                clicked = False

                for btn_text in button_texts:
                    if window.child_window(title=btn_text, control_type="Button").exists():
                        window.child_window(title=btn_text, control_type="Button").click()
                        clicked = True
                        break

                if not clicked:
                    # Check if installation is complete
                    if not window.exists():
                        break
                time.sleep(1)
                
            statuses[setup_file] = "Succeeded"
            print(f"\nStatus: Succeeded\n")
        except Exception as e:
            statuses[setup_file] = "Error"
            print(f"\nStatus: Error - {e}\n")
            logging.error("Failed to run %s: %s", setup_file, e)

        # Countdown before moving to the next file
        countdown("Moving to the next file in", 3)
        
# Main execution
if __name__ == "__main__":
    process_setup_files()
    print_summary()
    
    # Sound notification
    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)

    # Reboot after completion
    logging.info("Setup completed. System will reboot.")
    countdown("Rebooting in", 5)
    subprocess.run("shutdown /r /t 0", shell=True)