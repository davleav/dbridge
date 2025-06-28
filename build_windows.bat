@echo off
echo Building DBridge for Windows...

REM Create a clean build environment
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist installer mkdir installer

REM Install required dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller pillow

REM Convert icon to ICO format
echo Converting icon to ICO format...
python convert_icon.py

REM Create Windows executable
echo Creating Windows executable...
pyinstaller dbridge_windows.spec

REM Check if Inno Setup is installed
echo Checking for Inno Setup...
if exist "%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe" (
    echo Inno Setup found. Creating installer...
    
    REM Get version from __version__ in src/__init__.py
    for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('.'); from src import __version__; print(__version__)"') do set VERSION=%%a
    
    REM Create a temporary Inno Setup script with the version
    echo Creating Inno Setup script with version %VERSION%...
    powershell -Command "(Get-Content dbridge_installer.iss) -replace '#define AppVersion.*', '#define AppVersion \"%VERSION%\"' | Set-Content dbridge_installer_temp.iss"
    
    REM Compile the installer
    "%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe" /Q dbridge_installer_temp.iss
    
    echo Installer created successfully in the 'installer' folder.
) else (
    echo Inno Setup not found. Please install Inno Setup and run this script again.
    echo You can download Inno Setup from: https://jrsoftware.org/isdl.php
    echo Alternatively, you can manually create an installer using the executable in the 'dist' folder.
)

echo Build process completed.