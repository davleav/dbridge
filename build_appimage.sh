#!/bin/bash
# Script to build an AppImage for DBridge with fixes for permission issues

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script located at: $SCRIPT_DIR"

# Create a temporary directory in the user's home directory
BUILD_DIR="$HOME/dbridge_build_tmp"
echo "Creating temporary build directory at $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy the entire project to the temporary directory
echo "Copying project files to temporary directory..."
cp -r "$SCRIPT_DIR"/* "$BUILD_DIR/"

# Create the fixed build script
cat > "$BUILD_DIR/build_local.sh" << 'EOL'
#!/bin/bash
# Script to build an AppImage for DBridge

set -e

# Clean up any previous build artifacts
echo "Cleaning up previous build artifacts..."
rm -rf venv AppDir dist build *.AppImage resources/icon.png
mkdir -p resources

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Verify the virtual environment is active
which python
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
cat > AppDir/usr/share/applications/dbridge.desktop << 'DESKTOPEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=DBridge Beta
Comment=A user-friendly SQL client (Beta 0.8.0)
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
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3.13/site-packages:${PYTHONPATH}"
exec "${HERE}/usr/bin/dbridge" "$@"
APPRUNEOF
chmod +x AppDir/AppRun

# Create launcher script
cat > AppDir/usr/bin/dbridge << 'LAUNCHEREOF'
#!/bin/bash
python -m src.main
LAUNCHEREOF
chmod +x AppDir/usr/bin/dbridge

# Use PyInstaller to bundle the application
pip install pyinstaller
if [ -f src/main.py ]; then
    pyinstaller --onedir --name dbridge src/main.py
else
    echo "Error: src/main.py not found. Looking for alternative entry points..."
    MAIN_PY=$(find . -name "main.py" | head -1)
    if [ -n "$MAIN_PY" ]; then
        echo "Found alternative entry point: $MAIN_PY"
        pyinstaller --onedir --name dbridge "$MAIN_PY"
    else
        echo "Error: No main.py found. Cannot continue."
        exit 1
    fi
fi

# Copy the bundled application to AppDir
cp -r dist/dbridge/* AppDir/usr/bin/

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
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir DBridge-Beta-0.8.0-x86_64.AppImage

# Ensure the AppImage is executable
chmod +x DBridge-Beta-0.8.0-x86_64.AppImage

echo "AppImage created: DBridge-Beta-0.8.0-x86_64.AppImage"
EOL

# Make the script executable
chmod +x "$BUILD_DIR/build_local.sh"

# Run the build script
echo "Running the build script in the temporary directory..."
cd "$BUILD_DIR"
./build_local.sh

# Copy the resulting AppImage back to the original location
if [ -f "$BUILD_DIR/DBridge-Beta-0.8.0-x86_64.AppImage" ]; then
    echo "Build successful! Copying AppImage to original location..."
    # Make the AppImage executable in the build directory
    chmod +x "$BUILD_DIR/DBridge-Beta-0.8.0-x86_64.AppImage"
    # Copy the AppImage to both the original location and home directory
    cp "$BUILD_DIR/DBridge-Beta-0.8.0-x86_64.AppImage" "$SCRIPT_DIR/"
    cp "$BUILD_DIR/DBridge-Beta-0.8.0-x86_64.AppImage" ~/DBridge-Beta-0.8.0-x86_64.AppImage
    # Make sure the copied AppImage is executable (though it won't work on noexec filesystem)
    chmod +x "$SCRIPT_DIR/DBridge-Beta-0.8.0-x86_64.AppImage"
    chmod +x ~/DBridge-Beta-0.8.0-x86_64.AppImage
    echo "AppImage is now available at: $SCRIPT_DIR/DBridge-Beta-0.8.0-x86_64.AppImage"
    echo "A copy is also available at: ~/DBridge-Beta-0.8.0-x86_64.AppImage (use this one to execute)"
    echo "Permissions have been set to make the AppImage executable."
else
    echo "Build failed. Check the logs for errors."
fi

# Ask if the user wants to clean up the temporary directory
read -p "Do you want to clean up the temporary build directory? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleaning up temporary directory..."
    rm -rf "$BUILD_DIR"
    echo "Cleanup complete."
else
    echo "Temporary directory kept at: $BUILD_DIR"
fi