@echo off

@echo Google Drive Uploader/Downloader - by Andy N Le 0908.231181 

REM Check if Python launcher is available
py --version >nul 2>&1
if "%ERRORLEVEL%" == "0" (
    echo Python launcher is available. Generating Python 3.10 VENV
    py -3.10 -m venv venv
) else (
    echo Python launcher is not available, generating VENV with default Python. Make sure that it is 3.10
    python -m venv venv
)

REM Activate virtual environment
call .\venv\Scripts\activate.bat

REM Ensure pip is installed and updated
python -m ensurepip --upgrade
pip install --upgrade pip

REM Install dependencies with verbose output
pip install -r requirements.txt -v

REM Show completion message
echo GDrive Downloader installation completed, check messages for any errors

REM Pause to keep the command prompt open
pause
