import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

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


# Class to handle folder movement
class FolderEventHandler(FileSystemEventHandler):
    def __init__(self, folder_monitor):
        self.folder_monitor = folder_monitor

    def on_moved(self, event):
        if event.src_path == str(self.folder_monitor[0]):
            print(f"Folder moved to: {event.dest_path}")
            self.folder_monitor[0] = Path(event.dest_path)


# Start monitoring folder movement
def monitor_folder(folder_monitor):
    observer = Observer()
    handler = FolderEventHandler(folder_monitor)
    observer.schedule(handler, path=str(folder_monitor[0].parent), recursive=False)
    observer.start()
    return observer


# Main logic
if __name__ == "__main__":
    # Ensure the folder exists in the Documents directory
    folder_path = [ensure_setup_folder()]

    # Start monitoring folder movement
    observer = monitor_folder(folder_path)

    try:
        while True:
            # List all setup files
            setup_files = [
                file for file in os.listdir(folder_path[0]) if file.endswith(('.exe', '.msi'))
            ]
            setup_files.sort()

            # Process each setup file
            for setup_file in setup_files:
                setup_path = folder_path[0] / setup_file
                try:
                    while True:  # Wait for user command
                        print(f"Ready to run {setup_file}.\n"
                              "Continue [n]\n"
                              "Exit [0].")
                        user_input = input().strip().lower()

                        if user_input in ['n', 'next']:
                            print(f"Running {setup_file}...")
                            subprocess.run(setup_path, shell=True)
                            print(f"{setup_file} has done.")
                            break
                        elif user_input == '0':
                            print("Exiting program...")
                            exit(0)
                        else:
                            print("Invalid input. Please try again.")
                except Exception as e:
                    print(f"Failed to run {setup_file}: {e}")

            print("All setup files have been processed.")
            input("Press [Enter] to exit the program.")
            break
    finally:
        observer.stop()
        observer.join()
