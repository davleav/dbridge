#!/bin/bash
# Simplified script to build an AppImage for DBridge

set -e  # Exit on error

# Check if running as root and warn
if [ "$(id -u)" -eq 0 ]; then
    echo "WARNING: Running this script as root is not recommended."
    echo "PyInstaller in particular warns against running as root."
    echo "Consider running this script as a regular user."
    echo "Press Enter to continue anyway, or Ctrl+C to abort."
    read
fi

# Get the directory where this script is located
if [ -n "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
else
    SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
fi
echo "Script located at: $SCRIPT_DIR"

# Set version number and application details
VERSION="0.8.0"
APP_NAME="DBridge-Beta"
ARCH="x86_64"
APPIMAGE_FILENAME="${APP_NAME}-${VERSION}-${ARCH}.AppImage"
echo "Building AppImage: $APPIMAGE_FILENAME"

# Determine which Python command to use
if command -v python &>/dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    echo "Error: No Python interpreter found. Please install Python."
    exit 1
fi
echo "Using Python command: $PYTHON_CMD"

# Create a temporary build directory
BUILD_DIR="$HOME/dbridge_build_tmp"
echo "Creating temporary build directory at $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy the entire project to the temporary directory
echo "Copying project files to temporary directory..."
cp -r "$SCRIPT_DIR"/* "$BUILD_DIR/"

# Change to the build directory for all operations
cd "$BUILD_DIR"

# Prepare main.py file
echo "Preparing main.py file..."
MAIN_FILE="$(pwd)/src/main.py"

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
if [ ! -r "$MAIN_FILE" ]; then
    echo "Error: main.py exists but is not readable. Trying to fix permissions."
    chmod 777 "$MAIN_FILE"
    if [ ! -r "$MAIN_FILE" ]; then
        echo "Error: Still not readable after chmod. Cannot continue."
        exit 1
    fi
fi

echo "Using main Python file: $MAIN_FILE"

# Clean up any previous build artifacts
echo "Cleaning up previous build artifacts..."
rm -rf venv AppDir dist build *.AppImage resources/icon.png
mkdir -p resources

# Create a virtual environment
echo "Creating Python virtual environment..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Verify the virtual environment is active
which python
which pip

# Install dependencies
if [ -f requirements.txt ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found. Installing minimal dependencies..."
    pip install PyQt6 SQLAlchemy
fi

# Install PyInstaller
pip install pyinstaller

# Install system dependencies for Qt XCB platform plugin
echo "Installing system dependencies for Qt..."
# Create a directory for bundled libraries
mkdir -p AppDir/usr/lib/

# Check if we can find the required libraries on the system
echo "Checking for required XCB libraries..."
XCB_LIBS=$(find /usr/lib* -name "libxcb-cursor.so*" 2>/dev/null)
if [ -z "$XCB_LIBS" ]; then
    echo "Warning: libxcb-cursor not found on the system. Trying to install it..."
    # Try to install the package if we have apt-get
    if command -v apt-get &>/dev/null; then
        echo "Using apt-get to install libxcb-cursor0..."
        apt-get update -y || true
        apt-get install -y libxcb-cursor0 || true
    elif command -v dnf &>/dev/null; then
        echo "Using dnf to install libxcb-cursor..."
        dnf install -y libxcb-cursor || true
    elif command -v yum &>/dev/null; then
        echo "Using yum to install libxcb-cursor..."
        yum install -y libxcb-cursor || true
    elif command -v pacman &>/dev/null; then
        echo "Using pacman to install libxcb-cursor..."
        pacman -S --noconfirm libxcb || true
    else
        echo "Warning: Could not install libxcb-cursor automatically."
        echo "The AppImage may not work without this dependency."
    fi
    
    # Check again after attempted installation
    XCB_LIBS=$(find /usr/lib* -name "libxcb-cursor.so*" 2>/dev/null)
fi

# Copy XCB libraries if found
if [ -n "$XCB_LIBS" ]; then
    echo "Found XCB libraries, copying to AppDir..."
    for lib in $XCB_LIBS; do
        cp -L "$lib" AppDir/usr/lib/
        echo "Copied $lib to AppDir/usr/lib/"
    done
    
    # Also copy other potentially needed XCB libraries
    for xcb_lib in $(find /usr/lib* -name "libxcb*.so*" 2>/dev/null | grep -v "libxcb-cursor"); do
        cp -L "$xcb_lib" AppDir/usr/lib/ 2>/dev/null || true
        echo "Copied $xcb_lib to AppDir/usr/lib/"
    done
    
    # Copy X11 libraries that might be needed
    for x11_lib in $(find /usr/lib* -name "libX*.so*" 2>/dev/null); do
        cp -L "$x11_lib" AppDir/usr/lib/ 2>/dev/null || true
        echo "Copied $x11_lib to AppDir/usr/lib/"
    done
else
    echo "Warning: Could not find libxcb-cursor libraries."
    echo "The AppImage may not work without this dependency."
fi

# Create AppDir structure
echo "Creating AppDir structure..."
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

# Use the custom DBridge.png icon
echo "Setting up application icon..."
mkdir -p resources
cp DBridge.png resources/icon.png 2>/dev/null || echo "Warning: DBridge.png not found"

# Copy icon to AppDir in multiple required locations
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
if [ -f "resources/icon.png" ]; then
    cp resources/icon.png AppDir/usr/share/icons/hicolor/256x256/apps/dbridge.png
    cp resources/icon.png AppDir/dbridge.png
else
    echo "Warning: Icon file not found. AppImage will not have an icon."
fi

# Create desktop file in both required locations
echo "Creating desktop entry file..."
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

# Ensure desktop file has correct permissions
chmod 755 AppDir/dbridge.desktop
chmod 755 AppDir/usr/share/applications/dbridge.desktop

# Create AppRun script
echo "Creating AppRun script..."
cat > AppDir/AppRun << 'APPRUNEOF'
#!/bin/bash

# Find the AppDir location
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
export PYTHONPATH="${HERE}/usr/lib/python3.10/site-packages:${HERE}/usr/lib/python3.10:${PYTHONPATH}"
export PYTHONHOME="${HERE}/usr"
export PATH="${HERE}/usr/bin:${PATH}"

# Library paths - make sure our libraries are found first
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Debug: List available libraries
echo "Available libraries in AppDir:"
echo "XCB libraries:"
ls -la ${HERE}/usr/lib/libxcb* 2>/dev/null || echo "No XCB libraries found!"
echo "X11 libraries:"
ls -la ${HERE}/usr/lib/libX* 2>/dev/null || echo "No X11 libraries found!"

# Qt paths - try both PyQt6 location and standard location
export QT_PLUGIN_PATH="${HERE}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins:${HERE}/usr/plugins:${QT_PLUGIN_PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${HERE}/usr/lib/python3.10/site-packages/PyQt6/Qt6/plugins/platforms:${HERE}/usr/plugins/platforms:${QT_QPA_PLATFORM_PLUGIN_PATH}"

# Additional Qt environment variables
export QT_DEBUG_PLUGINS=1
export QT_XCB_GL_INTEGRATION=xcb_glx
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Try to use wayland if xcb fails
export QT_QPA_PLATFORM=xcb;wayland;wayland-egl;eglfs;minimal

# Find Python executable
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
echo "Creating launcher script..."
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

# Run PyInstaller with the verified main.py file
echo "Running PyInstaller on: $MAIN_FILE"
pyinstaller --onedir \
    --name dbridge \
    --hidden-import=PyQt6 \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=sqlalchemy \
    "$MAIN_FILE"

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
    if [ -f "$MAIN_FILE" ]; then
        echo "Copying main.py to AppDir/usr/bin/"
        cp -v "$MAIN_FILE" AppDir/usr/bin/
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

# Create the AppImage
echo "Running AppImageTool..."
ARCH=${ARCH} ./appimagetool-x86_64.AppImage AppDir ${APPIMAGE_FILENAME}

# Ensure the AppImage is executable
chmod +x ${APPIMAGE_FILENAME}

# Copy the resulting AppImage back to the original location
if [ -f "${APPIMAGE_FILENAME}" ]; then
    echo "Build successful! Copying AppImage to script location..."
    # Copy the AppImage to both the script location and home directory
    cp "${APPIMAGE_FILENAME}" "$SCRIPT_DIR/"
    cp "${APPIMAGE_FILENAME}" ~/"${APPIMAGE_FILENAME}"
    # Make sure the copied AppImage is executable
    chmod +x "$SCRIPT_DIR/${APPIMAGE_FILENAME}"
    chmod +x ~/"${APPIMAGE_FILENAME}"
    echo "AppImage is now available at: $SCRIPT_DIR/${APPIMAGE_FILENAME}"
    echo "A copy is also available at: ~/${APPIMAGE_FILENAME} (use this one to execute)"
    echo "Permissions have been set to make the AppImage executable."
else
    echo "Build failed. Check the logs for errors."
    exit 1
fi

# Ask if the user wants to clean up the temporary directory
echo -n "Do you want to clean up the temporary build directory? (y/n) "
read REPLY
echo

if [ "$REPLY" = "y" ] || [ "$REPLY" = "Y" ]; then
    echo "Cleaning up temporary directory..."
    cd "$SCRIPT_DIR"  # Move out of the directory before removing it
    rm -rf "$BUILD_DIR"
    echo "Cleanup complete."
else
    echo "Temporary directory kept at: $BUILD_DIR"
fi

echo "Build process completed successfully!"