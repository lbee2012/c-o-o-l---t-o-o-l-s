import os
import subprocess

# Specify the path to your "Automatic Setup" folder where the setup files are stored
automatic_setup_folder = r"S:\. Automatic Setup Folder"  # Update this path to match your folder location

# Get a list of all setup files in the folder
setup_files = [file for file in os.listdir(automatic_setup_folder) if file.endswith(('.exe', '.msi'))]

# Sort the files in alphabetical order
setup_files.sort()

# Run each setup file one by one
for setup_file in setup_files:
    setup_path = os.path.join(automatic_setup_folder, setup_file)
    try:
        print(f"Running {setup_file}...")
        subprocess.run(setup_path, shell=True)
        print(f"{setup_file} completed.")
    except Exception as e:
        print(f"Failed to run {setup_file}: {e}")
