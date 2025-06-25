#!/usr/bin/env python3
"""
DBridge - A user-friendly SQL client for Linux
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
import os

from src import __version__
from src.ui.main_window import MainWindow
from src.ui.theme_manager import ThemeManager
# Import the patch to handle string values for port and save_password
import src.core.connection_manager_patch

def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    app.setApplicationName(f"DBridge Beta {__version__}")
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "../resources/icon.png")))
    
    # Initialize theme manager and apply the saved theme
    theme_manager = ThemeManager()
    theme_manager.set_theme(theme_manager.get_current_theme())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()