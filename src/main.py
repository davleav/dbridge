#!/usr/bin/env python3
"""
DBridge - A user-friendly SQL client for multiple platforms
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from src import __version__
from src.ui.main_window import MainWindow
from src.ui.theme_manager import ThemeManager
# Import the patch to handle string values for port and save_password
import src.core.connection_manager_patch

def get_icon_path():
    """Get the appropriate icon path based on the platform and packaging"""
    # Check if we're running from a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # If running as PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = getattr(sys, '_MEIPASS')  # Use getattr to avoid linting issues
        else:
            base_path = os.path.dirname(sys.executable)
        
        # Look for the icon in various locations
        icon_paths = [
            os.path.join(base_path, "icon.png"),
            os.path.join(base_path, "resources", "icon.png"),
            os.path.join(base_path, "DBridge.png")
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                return path
    
    # Default location for development environment
    return os.path.join(os.path.dirname(__file__), "../resources/icon.png")

def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    app.setApplicationName(f"DBridge Beta {__version__}")
    
    # Set the application icon
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Initialize theme manager and apply the saved theme
    theme_manager = ThemeManager()
    theme_manager.set_theme(theme_manager.get_current_theme())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()