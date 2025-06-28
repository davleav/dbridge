#!/usr/bin/env python3
"""
Convert PNG icon to ICO format for Windows
"""

from PIL import Image
import os

def convert_png_to_ico(png_file, ico_file):
    """Convert PNG to ICO format"""
    if not os.path.exists(png_file):
        print(f"Error: {png_file} not found")
        return False
    
    try:
        img = Image.open(png_file)
        # Create ICO file with multiple sizes
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_file, format='ICO', sizes=icon_sizes)
        print(f"Successfully converted {png_file} to {ico_file}")
        return True
    except Exception as e:
        print(f"Error converting icon: {e}")
        return False

if __name__ == "__main__":
    convert_png_to_ico("DBridge.png", "DBridge.ico")