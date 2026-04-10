#!/bin/bash
# Script to build an AppImage for DBridge with fixes for permission issues

# Check if running as root and warn
if [ "$(id -u)" -eq 0 ]; then
    echo "WARNING: Running this script as root is not recommended."
    echo "PyInstaller in particular warns against running as root."
    echo "Consider running this script as a regular user."
    echo "Press Enter to continue anyway, or Ctrl+C to abort."
    read
fi

# Get the directory where this script is located
# Use BASH_SOURCE if available (for Fedora/newer bash), otherwise fallback to $0 (for Ubuntu/older bash)
if [ -n "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
else
    SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
fi
echo "Script located at: $SCRIPT_DIR"

# Set version number (can be updated in one place)
VERSION="0.9.0"
APP_NAME="DBridge-Beta"
ARCH="x86_64"
APPIMAGE_FILENAME="${APP_NAME}-${VERSION}-${ARCH}.AppImage"
echo "Building AppImage: $APPIMAGE_FILENAME"

# Determine which Python command to use (python3 on Ubuntu, python on Fedora)
if command -v python &>/dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    echo "Error: No Python interpreter found. Please install Python."
    exit 1
fi
echo "Using Python command: $PYTHON_CMD"

# Create a temporary directory in the user's home directory
BUILD_DIR="$HOME/dbridge_build_tmp"
echo "Creating temporary build directory at $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy the entire project to the temporary directory
echo "Copying project files to temporary directory..."
cp -r "$SCRIPT_DIR"/* "$BUILD_DIR/"

# Copy the prepare_main.sh script to the build directory
if [ -f "/media/david/Data/david/apps/dbridge/prepare_main.sh" ]; then
    echo "Copying prepare_main.sh to build directory..."
    cp -v "/media/david/Data/david/apps/dbridge/prepare_main.sh" "$BUILD_DIR/"
    chmod +x "$BUILD_DIR/prepare_main.sh"
else
    echo "Warning: prepare_main.sh not found, creating it in the build directory..."
    cat > "$BUILD_DIR/prepare_main.sh" << 'PREPAREMAINEOF'
#!/bin/bash
# Script to prepare the main.py file for the AppImage build

# Set the path to the main.py file
MAIN_FILE="$(pwd)/src/main.py"
echo "Using main.py at: $MAIN_FILE"

# Check if the file exists
if [ -f "$MAIN_FILE" ]; then
    echo "Found main.py at: $MAIN_FILE"
    ls -la "$MAIN_FILE"
else
    echo "main.py not found. Creating it..."
    mkdir -p "$(pwd)/src"
    cat > "$MAIN_FILE" << 'MAINPYEOF'
#!/usr/bin/env python3
"""
DBridge - A user-friendly SQL client
Main entry point for the application
"""

def main():
    """Main entry point for the application"""
    print("DBridge - A user-friendly SQL client")
    print("This is a placeholder main.py file created by the build script.")
    print("The actual application code was not found during the build process.")

if __name__ == "__main__":
    main()
MAINPYEOF
    chmod 777 "$MAIN_FILE"
    echo "Created main.py at: $MAIN_FILE"
    ls -la "$MAIN_FILE"
fi

# Verify the file is readable
if [ -r "$MAIN_FILE" ]; then
    echo "File is readable. First few lines:"
    head -n 3 "$MAIN_FILE"
else
    echo "Error: File exists but is not readable."
    exit 1
fi

# Output the path for the calling script to use
echo "$MAIN_FILE"
PREPAREMAINEOF
    chmod +x "$BUILD_DIR/prepare_main.sh"
fi

# Pass variables to the build script
cat > "$BUILD_DIR/build_local.sh" << EOL
#!/bin/bash
# Script to build an AppImage for DBridge

# Set version information from parent script
VERSION="${VERSION}"
APP_NAME="${APP_NAME}"
ARCH="${ARCH}"
APPIMAGE_FILENAME="${APPIMAGE_FILENAME}"
PYTHON_CMD="${PYTHON_CMD}"
SCRIPT_DIR="${SCRIPT_DIR}"

set -e

# Clean up any previous build artifacts
echo "Cleaning up previous build artifacts..."
rm -rf venv AppDir dist build *.AppImage resources/icon.png
mkdir -p resources

# Use the Python command passed from the parent script
echo "Using Python command: \${PYTHON_CMD}"

# Create a virtual environment
\${PYTHON_CMD} -m venv venv
source venv/bin/activate

# Verify the virtual environment is active
which python
which python3 || echo "python3 command not available in venv"
which pip

# Install dependencies
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found. Installing minimal dependencies..."
    pip install PyQt6 SQLAlchemy
fi

# Create AppDir structure
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

# Use the custom DBridge.png icon
echo "Using custom DBridge.png icon..."
mkdir -p resources
cp DBridge.png resources/icon.png

# Copy icon to AppDir in multiple required locations
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
cp resources/icon.png AppDir/usr/share/icons/hicolor/256x256/apps/dbridge.png
# Also copy to the root of AppDir as required by some AppImage tools
cp resources/icon.png AppDir/dbridge.png

# Create desktop file in both required locations
cat > AppDir/usr/share/applications/dbridge.desktop << DESKTOPEOF
[Desktop Entry]
Version=1.0
Type=Application
Name=${APP_NAME}
Comment=A user-friendly SQL client (Beta ${VERSION})
Exec=dbridge
Icon=dbridge
Categories=Development;Database;
Terminal=false
StartupNotify=true
DESKTOPEOF

# AppImageTool also looks for the desktop file in the root of AppDir
cp AppDir/usr/share/applications/dbridge.desktop AppDir/dbridge.desktop

# Ensure desktop file has correct permissions and format
chmod 755 AppDir/dbridge.desktop
chmod 755 AppDir/usr/share/applications/dbridge.desktop

# Validate desktop file
echo "Validating desktop file..."
cat AppDir/dbridge.desktop

# Create AppRun script
cat > AppDir/AppRun << 'APPRUNEOF'
#!/bin/bash

# More robust way to find the AppDir location
if [ -z "$APPDIR" ]; then
    # APPDIR isn't set, try to determine it
    if [ -n "$OWD" ]; then
        # OWD is set by newer AppImage runtime
        APPDIR="$OWD"
    else
        # Try to use various methods to find our location
        SELF=$(readlink -f "$0" 2>/dev/null)
        if [ -z "$SELF" ]; then
            # readlink -f doesn't work, try dirname
            SELF="$0"
            APPDIR=$(dirname "$SELF" 2>/dev/null)
        else
            APPDIR=${SELF%/*}
        fi
        
        # If still empty, try /proc approach
        if [ -z "$APPDIR" ] || [ "$APPDIR" = "." ]; then
            APPDIR=$(dirname "$(readlink -f /proc/$$/exe)" 2>/dev/null)
        fi
        
        # Last resort, use the mount point
        if [ -z "$APPDIR" ] || [ "$APPDIR" = "." ]; then
            for i in /tmp/.mount_*; do
                if [ -d "$i" ]; then
                    APPDIR="$i"
                    break
                fi
            done
        fi
    fi
fi

# Set HERE to APPDIR for compatibility
HERE="$APPDIR"

# Debug information
echo "Starting AppRun script..."
echo "AppDir location: ${HERE}"

# Python paths
export PYTHONPATH="${HERE}/usr/lib/python3.10/site-packages:${HERE}/usr/lib/python3.10:${HERE}/usr/lib/python3.10/site-packages:${HERE}/usr/lib/python3.10:${PYTHONPATH}"
export PYTHONHOME="${HERE}/usr"
export PATH="${HERE}/usr/bin:${PATH}"

# Debug Python paths
echo "Python path configuration:"
echo "  PYTHONHOME = '${PYTHONHOME}'"
echo "  PYTHONPATH = '${PYTHONPATH}'"

# Library paths - make sure our libraries are found first
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Debug: List available libraries
echo "Available Python libraries in AppDir:"
ls -la ${HERE}/usr/lib/libpython* 2>/dev/null || echo "No Python libraries found!"

# Qt paths - try both PyQt6 location and standard location
export QT_PLUGIN_PATH="${HERE}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins:${HERE}/usr/plugins:${QT_PLUGIN_PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${HERE}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins/platforms:${HERE}/usr/plugins/platforms:${QT_QPA_PLATFORM_PLUGIN_PATH}"

# Additional Qt environment variables
export QT_DEBUG_PLUGINS=1
export QT_XCB_GL_INTEGRATION=xcb_glx
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Execute the application with proper Python path
if [ -f "${HERE}/usr/bin/python3" ]; then
  export PYTHON="${HERE}/usr/bin/python3"
elif [ -f "${HERE}/usr/bin/python" ]; then
  export PYTHON="${HERE}/usr/bin/python"
else
  # Try to find Python in PATH
  PYTHON_PATH=$(which python3 2>/dev/null || which python 2>/dev/null)
  if [ -n "$PYTHON_PATH" ]; then
    export PYTHON="$PYTHON_PATH"
  else
    echo "Error: Python executable not found"
    exit 1
  fi
fi

# Check if the dbridge executable exists
if [ -f "${HERE}/usr/bin/dbridge" ]; then
    # Execute the application
    exec "${HERE}/usr/bin/dbridge" "$@"
else
    # Try to find the executable
    echo "Warning: Could not find ${HERE}/usr/bin/dbridge"
    echo "Searching for dbridge executable..."
    
    # Try to find the executable in the AppDir
    DBRIDGE_EXEC=$(find "${HERE}" -name "dbridge" -type f -executable 2>/dev/null | head -1)
    
    if [ -n "$DBRIDGE_EXEC" ]; then
        echo "Found executable at: $DBRIDGE_EXEC"
        exec "$DBRIDGE_EXEC" "$@"
    else
        # Last resort: try to run the Python module directly
        echo "Trying to run Python module directly..."
        if [ -n "$PYTHON" ]; then
            # Look for main.py
            MAIN_PY=$(find "${HERE}" -name "main.py" 2>/dev/null | head -1)
            if [ -n "$MAIN_PY" ]; then
                echo "Found main.py at: $MAIN_PY"
                exec "$PYTHON" "$MAIN_PY" "$@"
            else
                echo "Error: Could not find main.py"
                exit 1
            fi
        else
            echo "Error: No Python executable and no dbridge executable found"
            exit 1
        fi
    fi
fi
APPRUNEOF
chmod +x AppDir/AppRun

# Create launcher script
cat > AppDir/usr/bin/dbridge << 'LAUNCHEREOF'
#!/bin/bash
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
APP_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo "Launcher starting from: $SCRIPT_DIR"
echo "Application directory: $APP_DIR"

# Try to find the main.py file
MAIN_PY=""
for search_path in "$APP_DIR/usr/bin/src/main.py" "$APP_DIR/src/main.py" "$SCRIPT_DIR/src/main.py"; do
    if [ -f "$search_path" ]; then
        MAIN_PY="$search_path"
        echo "Found main.py at: $MAIN_PY"
        break
    fi
done

# If we couldn't find main.py, search for it
if [ -z "$MAIN_PY" ]; then
    echo "Searching for main.py..."
    MAIN_PY=$(find "$APP_DIR" -name "main.py" 2>/dev/null | head -1)
    if [ -n "$MAIN_PY" ]; then
        echo "Found main.py at: $MAIN_PY"
    fi
fi

# Try python3 first, then fall back to python if needed
if [ -n "$MAIN_PY" ]; then
    # We found main.py, run it directly
    if command -v python3 &>/dev/null; then
        echo "Running with python3: $MAIN_PY"
        exec python3 "$MAIN_PY" "$@"
    elif command -v python &>/dev/null; then
        echo "Running with python: $MAIN_PY"
        exec python "$MAIN_PY" "$@"
    else
        echo "Error: No Python interpreter found"
        exit 1
    fi
else
    # Try to run as a module
    if command -v python3 &>/dev/null; then
        echo "Running module with python3"
        exec python3 -m src.main "$@"
    elif command -v python &>/dev/null; then
        echo "Running module with python"
        exec python -m src.main "$@"
    else
        echo "Error: No Python interpreter found"
        exit 1
    fi
fi
LAUNCHEREOF
chmod +x AppDir/usr/bin/dbridge

# Use PyInstaller to bundle the application
pip install pyinstaller

# Debug: Show current directory and files
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la
echo "Files in src directory (if it exists):"
ls -la src 2>/dev/null || echo "src directory not found"
echo "Files in original script directory:"
ls -la "$SCRIPT_DIR"
echo "Files in original script src directory (if it exists):"
ls -la "$SCRIPT_DIR/src" 2>/dev/null || echo "src directory not found in original script directory"

# Use the prepare_main.sh script to handle the main.py file
echo "Running prepare_main.sh to handle the main.py file..."
if [ -f "prepare_main.sh" ]; then
    # Run the script and capture its output (the path to main.py)
    MAIN_PY=$(./prepare_main.sh)
    
    # Check if the script ran successfully
    if [ $? -ne 0 ]; then
        echo "Error: prepare_main.sh failed. Cannot continue."
        exit 1
    fi
    
    # Check if we got a valid path
    if [ -z "$MAIN_PY" ]; then
        echo "Error: prepare_main.sh did not return a valid path. Cannot continue."
        exit 1
    fi
    
    echo "prepare_main.sh returned path: $MAIN_PY"
else
    # Fallback if the script doesn't exist
    echo "prepare_main.sh not found. Using hardcoded path."
    MAIN_PY="$(pwd)/src/main.py"
    
    # Check if the file exists
    if [ ! -f "$MAIN_PY" ]; then
        echo "Error: main.py not found at $MAIN_PY. Cannot continue."
        exit 1
    fi
    
    # Check if the file is readable
    if [ ! -r "$MAIN_PY" ]; then
        echo "Error: main.py exists but is not readable. Trying to fix permissions."
        chmod 777 "$MAIN_PY"
        if [ ! -r "$MAIN_PY" ]; then
            echo "Error: Still not readable after chmod. Cannot continue."
            exit 1
        fi
    fi
fi

# Final verification
echo "Final verification - Using main.py at: $MAIN_PY"

echo "Using main Python file: $MAIN_PY"

# Make sure the path is absolute if it's not already
if [ "${MAIN_PY#/}" = "$MAIN_PY" ]; then
    # Path doesn't start with /, so it's relative
    MAIN_PY="$(pwd)/$MAIN_PY"
fi

# Verify the file exists
if [ ! -f "$MAIN_PY" ]; then
    echo "Error: The main Python file '$MAIN_PY' does not exist."
    exit 1
fi

echo "Using main Python file: $MAIN_PY"

# Run PyInstaller with additional options for better compatibility
echo "Running PyInstaller on: $MAIN_PY"

# Final verification before running PyInstaller
if [ ! -f "$MAIN_PY" ]; then
    echo "Error: The main Python file '$MAIN_PY' does not exist at PyInstaller execution time."
    exit 1
fi

# Run PyInstaller with the verified main.py file
echo "Running PyInstaller with command: pyinstaller --onedir --name dbridge \"$MAIN_PY\""
pyinstaller --onedir \
    --name dbridge \
    --hidden-import=PyQt6 \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=sqlalchemy \
    "$MAIN_PY"

# Verify the PyInstaller output
if [ -d "dist/dbridge" ]; then
    echo "PyInstaller successfully created dist/dbridge directory"
    ls -la dist/dbridge
else
    echo "Warning: PyInstaller output directory not found as expected"
    # Try to find it
    DIST_DIR=$(find . -name "dbridge" -type d | grep dist | head -1)
    if [ -n "$DIST_DIR" ]; then
        echo "Found alternative dist directory: $DIST_DIR"
    else
        echo "Error: Could not find PyInstaller output directory"
        exit 1
    fi
fi

# Copy the bundled application to AppDir
echo "Copying PyInstaller output to AppDir..."
if [ -d "dist/dbridge" ]; then
    # Create src directory in AppDir/usr/bin to ensure module imports work
    mkdir -p AppDir/usr/bin/src
    
    # Copy all files from dist/dbridge to AppDir/usr/bin
    cp -rv dist/dbridge/* AppDir/usr/bin/
    
    # Also copy the original source files to ensure imports work correctly
    if [ -d "src" ]; then
        echo "Copying original source files to ensure imports work..."
        cp -rv src/* AppDir/usr/bin/src/
    fi
    
    # Copy the main.py file to the root of AppDir/usr/bin
    if [ -f "$MAIN_PY" ]; then
        echo "Copying main.py to AppDir/usr/bin/"
        cp -v "$MAIN_PY" AppDir/usr/bin/
    fi
else
    echo "Error: dist/dbridge directory not found"
    exit 1
fi

# Ensure all Python files are executable
find AppDir/usr/bin -name "*.py" -exec chmod +x {} \;

# Download and use appimagetool
echo "Downloading AppImageTool..."
wget -c "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
chmod +x appimagetool-x86_64.AppImage

# Verify AppDir structure before running AppImageTool
echo "Verifying AppDir structure..."
echo "Contents of AppDir:"
find AppDir -type f | sort

echo "Checking for desktop file:"
ls -la AppDir/*.desktop AppDir/usr/share/applications/*.desktop

echo "Checking for icon file:"
ls -la AppDir/*.png AppDir/usr/share/icons/hicolor/256x256/apps/*.png

echo "Running AppImageTool..."
ARCH=${ARCH} ./appimagetool-x86_64.AppImage AppDir ${APPIMAGE_FILENAME}

# Ensure the AppImage is executable
chmod +x ${APPIMAGE_FILENAME}

echo "AppImage created: \${APPIMAGE_FILENAME}"
EOL

# Make the script executable
chmod +x "$BUILD_DIR/build_local.sh"

# Run the build script
echo "Running the build script in the temporary directory..."
cd "$BUILD_DIR"
./build_local.sh

# Copy the resulting AppImage back to the original location
if [ -f "$BUILD_DIR/$APPIMAGE_FILENAME" ]; then
    echo "Build successful! Copying AppImage to script location..."
    # Make the AppImage executable in the build directory
    chmod +x "$BUILD_DIR/$APPIMAGE_FILENAME"
    # Copy the AppImage to both the script location and home directory
    cp "$BUILD_DIR/$APPIMAGE_FILENAME" "$SCRIPT_DIR/"
    cp "$BUILD_DIR/$APPIMAGE_FILENAME" ~/"$APPIMAGE_FILENAME"
    # Make sure the copied AppImage is executable (though it won't work on noexec filesystem)
    chmod +x "$SCRIPT_DIR/$APPIMAGE_FILENAME"
    chmod +x ~/"$APPIMAGE_FILENAME"
    echo "AppImage is now available at: $SCRIPT_DIR/$APPIMAGE_FILENAME"
    echo "A copy is also available at: ~/$APPIMAGE_FILENAME (use this one to execute)"
    echo "Permissions have been set to make the AppImage executable."
else
    echo "Build failed. Check the logs for errors."
fi

# Ask if the user wants to clean up the temporary directory
# Try to use read with -p for Fedora/newer bash, fall back to echo for Ubuntu/older bash
if read -p "Do you want to clean up the temporary build directory? (y/n) " -n 1 -r REPLY 2>/dev/null; then
    echo
else
    # Fallback for systems where read -p doesn't work
    echo -n "Do you want to clean up the temporary build directory? (y/n) "
    read REPLY
    echo
fi

# Support both [[ ]] syntax (Fedora) and [ ] syntax (Ubuntu)
if (command -v [[ >/dev/null 2>&1 && [[ $REPLY =~ ^[Yy]$ ]]) || [ "$REPLY" = "y" ] || [ "$REPLY" = "Y" ]; then
    echo "Cleaning up temporary directory..."
    rm -rf "$BUILD_DIR"
    echo "Cleanup complete."
else
    echo "Temporary directory kept at: $BUILD_DIR"
fi