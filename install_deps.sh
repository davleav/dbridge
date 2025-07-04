#!/bin/bash
# Script to install dependencies needed for DBridge AppImage

echo "Checking for required dependencies..."

# Check for libxcb-cursor
if ! ldconfig -p | grep -q libxcb-cursor.so; then
    echo "libxcb-cursor not found. Attempting to install..."
    
    # Try different package managers
    if command -v apt-get &>/dev/null; then
        echo "Using apt-get to install libxcb-cursor0..."
        sudo apt-get update
        sudo apt-get install -y libxcb-cursor0
    elif command -v dnf &>/dev/null; then
        echo "Using dnf to install libxcb-cursor..."
        sudo dnf install -y libxcb-cursor
    elif command -v yum &>/dev/null; then
        echo "Using yum to install libxcb-cursor..."
        sudo yum install -y libxcb-cursor
    elif command -v pacman &>/dev/null; then
        echo "Using pacman to install libxcb-cursor..."
        sudo pacman -S --noconfirm libxcb
    else
        echo "ERROR: Could not install libxcb-cursor automatically."
        echo "Please install libxcb-cursor manually for your distribution."
        exit 1
    fi
else
    echo "libxcb-cursor is already installed."
fi

# Check if installation was successful
if ldconfig -p | grep -q libxcb-cursor.so; then
    echo "All dependencies are installed. You can now run the DBridge AppImage."
else
    echo "ERROR: Failed to install required dependencies."
    echo "Please install libxcb-cursor manually for your distribution."
    exit 1
fi