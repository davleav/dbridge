#!/usr/bin/env python3
"""
Run main_window tests with all necessary patches to avoid popups
"""

import unittest
import sys
import os
from unittest.mock import patch

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Import the test module
from tests.test_main_window import TestMainWindow

if __name__ == '__main__':
    # Create a test suite with just the TestMainWindow class
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestMainWindow)
    
    # Run the tests with patches applied
    with patch('PyQt6.QtWidgets.QInputDialog.getText', return_value=("test_password", True)), \
         patch('PyQt6.QtWidgets.QInputDialog.getItem', return_value=("Test Connection", True)), \
         patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=("/path/to/file", "")), \
         patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', return_value=("/path/to/file", "")), \
         patch('PyQt6.QtWidgets.QMessageBox.information', return_value=None), \
         patch('PyQt6.QtWidgets.QMessageBox.critical', return_value=None), \
         patch('PyQt6.QtWidgets.QMessageBox.question', return_value=None), \
         patch('PyQt6.QtWidgets.QMessageBox.about', return_value=None):
        
        # Run the tests
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        
        # Exit with non-zero code if tests failed
        sys.exit(not result.wasSuccessful())