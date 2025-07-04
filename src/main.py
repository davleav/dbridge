#!/usr/bin/env python3
"""
DBridge - A user-friendly SQL client
Main entry point for the application
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    """Main entry point for the application"""
    # Create the application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create and show the main window
    main_window = MainWindow()
    main_window.show()
    
    # Start the application event loop
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
