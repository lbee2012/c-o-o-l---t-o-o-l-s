# Automatic-Setup
An application for users who frequently reinstall ưyndoz.

# Update 1.1

**Features**

- When finish a previous file:
    - Ask user to press keyword 'n', 'next' or various types of 'Next' (lowerCase / upperCase) to proceed to the next file.
    - Or press key '0' to exit the program immediately.

- Do not allow the script to run without user's command.

- When all the setup files are completed. Add "All setup files have been finished."

- User need to press 'Enter' to exit program. Add "Press [Enter] to exit the program."

***15.11.24 | 14:02***
***

# Update 1.2 (Bug fix)

**Fix**

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

**Features**

- Bring 'Not Yet' to version 1.2
    - Create folder name "Automatic Setup Folder" in 
        `C:\Users\"Your_Username"\Documents`
    - Automatically update folder's path whenever user moves it.

***15.11.24 | 23:51***
***

# Update 1.3 (Bug fix)

**Fix**

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

# Update 1.4 (Patch)

**Features**

- Skip button
    - Before choose to run the setup file, user could decide to run or skip that file
        
**Additional**

- Application icon

- C - Continue button instead of N - Next

***10:53 16/11***
***

# Update 1.5 (Patch)

**What's new**

- Temperature remove application icon

- Remove feature update folder's path automatically (Many bug)

**Features**

- Notice user when all of the installations have proceed
	- Windows sound (Boom)

- Reboot management
	- Ask for reboot
		- Enter: restart command counting down for 5 seconds
		- Esc: exit the program, counting down for 3 seconds

***14:44 16/11***
***

# Update 1.6

**What's new**

- New main folder in `Document`: **Automatic Setup**
    - Two branches folder
        - **Ngot:** for process setup files
        - **log**: for generation log files

**Features**

- Log details from now will recorded at
    `C:\Users\longg\Documents\Automatic Setup\log`

***17:57 16/11***
***

# Update 1.7

**What's new**

- Create system restore point to protect your PC before adjust

- Fix UI, cleaner and clearly than the previous version.

- Log details more clearly

**Features**

- Create a system restore point
    - Ask user for create a restore point
        - y - yes = create
        - n - no = non-create

***10:23 17/11***
***

# Update 1.8 (Big update)

***What's new***

- Next file will replace the previous with new information as new window
- Remove create system restore point

***Features***

- Replace previous screen with new clear screen

    - For example, previous version:
        -   ```
            File A
                Option
                a
                b

                Process

            File B
                Option
                a
                b

                Process

            File n (Loop)
            ```
        
    - Replace all of it with only one file on a windows
        -   ```
            Ready to run A.exe

            Options:
            [c] Continue
            [s] Skip
            [0] Exit

            Enter your choice: c

            Processing: A.exe
            Status: In progress / Skipped / Error / ....

            Press [ENTER] to continue to the next file.

            (Loop)
            ```
    - At the end, make the overall view for user to check about their setup-files
        - File A [Done]
        - File B [Error]
        - File C [Skip]

***22:45 17/11***
***

# Update 1.9

**What's new**

- Adjust for better UI, run smoother, OCD'er would love this app...

# Future Features

- Interaction with the setup files
- Retry failed installations
- Progress status on taskbar, animate on installations
- Custom Setup File Order


- Multi-Threaded installations ///

- Check for update of those files
- Multi-Language support
    - EN-US
    - VI-VN

***
# Note: Private

Syntax for transfer code to an .exe application.

```
+---------------------------------------+
|pyinstaller --onefile AutomaticSetup.py|
+---------------------------------------+
```
`pyinstaller --onefile AutomaticSetup.py`

Remember, always push code after adjusted.
