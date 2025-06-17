@echo off
echo Creating executable...
pip install -r requirements.txt

:: Create the executable with PyInstaller
pyinstaller --onefile --windowed --icon=icon.ico --name HeadsetTracker main.py

:: Check if Inno Setup is installed
echo.
echo Checking for Inno Setup...
where iscc >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Inno Setup found. Creating installer...
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup_script.iss
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo Installation package created successfully!
        echo The installer is located in the current directory as 'HeadsetTracker_Setup.exe'
    ) else (
        echo Error creating installer. Please check the messages above.
    )
) else (
    echo.
    echo Inno Setup not found. Please install it from http://www.jrsoftware.org/isdl.php
    echo Then run this script again to create the installer.
)

pause
