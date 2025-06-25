#!/usr/bin/env python3
"""
Test runner for DBridge application with all necessary patches to avoid popups
"""

import unittest
import sys
import os
from unittest.mock import patch

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Create patches for all dialog classes to avoid popups during tests
patches = [
    patch('PyQt6.QtWidgets.QInputDialog.getText', return_value=("test_password", True)),
    patch('PyQt6.QtWidgets.QInputDialog.getItem', return_value=("Test Connection", True)),
    patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=("/path/to/file", "")),
    patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', return_value=("/path/to/file", "")),
    patch('PyQt6.QtWidgets.QMessageBox.information', return_value=None),
    patch('PyQt6.QtWidgets.QMessageBox.critical', return_value=None),
    patch('PyQt6.QtWidgets.QMessageBox.question', return_value=None),
    patch('PyQt6.QtWidgets.QMessageBox.about', return_value=None)
]

if __name__ == '__main__':
    # Start all patches
    for p in patches:
        p.start()
    
    try:
        # Discover and run all tests
        test_loader = unittest.TestLoader()
        
        if len(sys.argv) > 1:
            # Run specific test file
            test_suite = test_loader.discover('tests', pattern=f'test_{sys.argv[1]}.py')
        else:
            # Run all tests
            test_suite = test_loader.discover('tests', pattern='test_*.py')
        
        # Run the tests
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        
        # Exit with non-zero code if tests failed
        sys.exit(not result.wasSuccessful())
    finally:
        # Stop all patches
        for p in patches:
            p.stop()