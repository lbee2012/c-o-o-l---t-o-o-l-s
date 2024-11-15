import os
import subprocess

# Specify the path to your "Automatic Setup" folder where the setup files are stored
automatic_setup_folder = r"S:\. Automatic Setup Folder"  # Update this path to match your folder location

# Get a list of all setup files in the folder
setup_files = [file for file in os.listdir(automatic_setup_folder) if file.endswith(('.exe', '.msi'))]

# Sort the files in alphabetical order
setup_files.sort()

# Process each setup file one by one
for setup_file in setup_files:
    setup_path = os.path.join(automatic_setup_folder, setup_file)
    try:
        while True:  # Wait for user command
            user_input = input(f"Ready to run {setup_file}. Type 'n', 'next', or 'Next' to continue, or '0' to exit: ").strip().lower()
            
            if user_input in ['n', 'N', 'next', 'Next', 'nExt', 'neXt', 'nexT', 'NExt', 'NeXt', 'NexT', 'nEXt', 'nExT', 'neXT', 'NEXT']:
                print(f"Running {setup_file}...")
                subprocess.run(setup_path, shell=True)
                print(f"{setup_file} completed.")
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
