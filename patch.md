# Automatic-Setup
An application for users who frequently reinstall ưyndoz.

# Update 1.1

- When finish a previous file:
    - Ask user to press keyword 'n', 'next' or various types of 'Next' (lowerCase / upperCase) to proceed to the next file.
    - Or press key '0' to exit the program immediately.

- Do not allow the script to run without user's command.

- When all the setup files are completed. Add "All setup files have been finished."

- User need to press 'Enter' to exit program. Add "Press [Enter] to exit the program."

***15.11.24 | 14:02***
***

# Update 1.2 (Bug fix)

- **Fix**

    - Press key '0' still process the next file
        - Description: 
            ``` 
            Exiting program...
            Failed to run C-TestApp.exe: name 'exit' is not defined
            Ready to run D-TestApp.msi. ...
            ```

    - When 'Access is denied' so can not use 'completed.' word, use 'has done.' instead.
        - Description:
            ```
            Access is denied.
            A-TestApp.exe completed.
            ```

    - Using *'All setup files have been processed.'* replace for ~~'All setup files have been finished'~~ when they are all done.

- **Features**

    - Bring 'Not Yet' to version 1.2
        - Create folder name "Automatic Setup Folder" in 
            > C:\Users\"Your_Username"\Documents
        - Automatically update folder's path whenever user moves it.

***15.11.24 | 23:51***
***

# Update 1.3 (Bug fix)

- **Fix**

    - After press key '0'
        - "Exiting program..."
        - Counting for 3 second then auto close program and do not appear any sentence after "Exiting program..."

    - Last file has done
        - Only appear
            ```
            print("All setup files have been processed.")
            input("Press [Enter] to exit the program.")
            ```
            when the last file has been processed
    - Fix UI, more clean than previous version

***16.11.24 | 00:22***
***
## Future

- Sample UX, UI
    - Start (button)
    - Next file / Auto run (button)
    - Interaction with the setup files.

***
# Note: Private

Syntax for transfer code to an .exe application.

> pyinstaller --onefile AutomaticSetup.py

Remember, always push code after adjusted.