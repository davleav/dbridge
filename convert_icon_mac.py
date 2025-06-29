#!/usr/bin/env python3
"""
Script to convert the DBridge.png icon to ICNS format for macOS
"""

import os
import subprocess
from PIL import Image

def create_iconset():
    """Create an iconset from the DBridge.png file"""
    print("Converting DBridge.png to ICNS format...")
    
    # Create iconset directory if it doesn't exist
    if not os.path.exists('icon.iconset'):
        os.makedirs('icon.iconset')
    
    # Load the source image
    source_image = 'DBridge.png'
    if not os.path.exists(source_image):
        print(f"Error: {source_image} not found")
        return False
    
    # Define the icon sizes needed for macOS
    icon_sizes = [
        (16, 16, 'icon_16x16.png'),
        (32, 32, 'icon_16x16@2x.png'),
        (32, 32, 'icon_32x32.png'),
        (64, 64, 'icon_32x32@2x.png'),
        (128, 128, 'icon_128x128.png'),
        (256, 256, 'icon_128x128@2x.png'),
        (256, 256, 'icon_256x256.png'),
        (512, 512, 'icon_256x256@2x.png'),
        (512, 512, 'icon_512x512.png'),
        (1024, 1024, 'icon_512x512@2x.png')
    ]
    
    # Create each size
    for width, height, filename in icon_sizes:
        img = Image.open(source_image)
        img = img.resize((width, height), Image.LANCZOS)
        img.save(os.path.join('icon.iconset', filename))
        print(f"Created {filename} ({width}x{height})")
    
    # Convert the iconset to ICNS using iconutil (macOS only)
    if os.path.exists('/usr/bin/iconutil'):
        print("Converting iconset to ICNS...")
        subprocess.run(['iconutil', '-c', 'icns', 'icon.iconset'], check=True)
        print("ICNS file created: DBridge.icns")
        return True
    else:
        print("Warning: iconutil not found. This script must be run on macOS to create the ICNS file.")
        print("The iconset has been created, but you'll need to convert it to ICNS on a macOS system.")
        return False

if __name__ == "__main__":
    create_iconset()