#!/bin/bash
# Script to build a macOS application bundle and DMG for DBridge

set -e

echo "Building DBridge for macOS..."

# Clean up any previous build artifacts
rm -rf build dist *.dmg

# Install required dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller pillow py2app

# Convert icon to ICNS format (macOS icon format)
echo "Converting icon to ICNS format..."
mkdir -p icon.iconset
# This assumes you have the DBridge.png icon in the root directory
# You need to create multiple sizes for a proper macOS icon
sips -z 16 16 DBridge.png --out icon.iconset/icon_16x16.png
sips -z 32 32 DBridge.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32 DBridge.png --out icon.iconset/icon_32x32.png
sips -z 64 64 DBridge.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128 DBridge.png --out icon.iconset/icon_128x128.png
sips -z 256 256 DBridge.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256 DBridge.png --out icon.iconset/icon_256x256.png
sips -z 512 512 DBridge.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512 DBridge.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 DBridge.png --out icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset -o DBridge.icns

# Create macOS application bundle using PyInstaller
echo "Creating macOS application bundle..."
pyinstaller dbridge_macos.spec

# Get version from __version__ in src/__init__.py
VERSION=$(python -c "import sys; sys.path.append('.'); from src import __version__; print(__version__)")

# Create a DMG file
echo "Creating DMG installer..."
mkdir -p dist/dmg
cp -R "dist/DBridge.app" dist/dmg/
# Create a symbolic link to the Applications folder
ln -s /Applications dist/dmg/

# Create the DMG
hdiutil create -volname "DBridge $VERSION" -srcfolder dist/dmg -ov -format UDZO "dist/DBridge-$VERSION.dmg"

# Sign the application (if certificates are available)
if [ -n "$(security find-identity -v -p codesigning | grep 'Developer ID Application')" ]; then
    echo "Signing the application..."
    IDENTITY=$(security find-identity -v -p codesigning | grep 'Developer ID Application' | awk -F '"' '{print $2}')
    codesign --force --options runtime --sign "$IDENTITY" "dist/DBridge.app"
    
    # Notarize the app (requires Apple Developer account)
    if [ -n "$APPLE_ID" ] && [ -n "$APPLE_PASSWORD" ]; then
        echo "Notarizing the application..."
        xcrun altool --notarize-app --primary-bundle-id "com.dbridge.app" --username "$APPLE_ID" --password "$APPLE_PASSWORD" --file "dist/DBridge-$VERSION.dmg"
    else
        echo "Skipping notarization - Apple ID credentials not provided"
    fi
else
    echo "Skipping code signing - No Developer ID certificate found"
fi

echo "Build process completed. DMG installer is available at: dist/DBridge-$VERSION.dmg"