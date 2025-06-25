"""
Integration tests for the database manager with the main window
"""

import unittest
import os
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt6.QtCore import Qt

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.ui.main_window import MainWindow
from src.ui.database_manager import DatabaseManagerDialog, set_global_test_mode


class TestDatabaseManagerIntegration(unittest.TestCase):
    """Test cases for the integration of the database manager with the main window"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests"""
        # Enable global test mode
        set_global_test_mode(True)
        
        # Patch QMainWindow.show to prevent windows from showing
        cls.window_show_patcher = patch('PyQt6.QtWidgets.QMainWindow.show')
        cls.mock_window_show = cls.window_show_patcher.start()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        cls.window_show_patcher.stop()
    
    def setUp(self):
        """Set up test fixtures for each test"""
        # Create a mock connection manager
        with patch('src.core.connection_manager.ConnectionManager') as mock_cm:
            # Create the main window without showing it
            self.main_window = MainWindow()
            
            # Mock the connection tab
            self.mock_tab = MagicMock()
            self.mock_connection = MagicMock()
            self.mock_tab.connection = self.mock_connection
            
            # Mock the database browser
            self.mock_browser = MagicMock()
            self.mock_tab.database_browser = self.mock_browser
            
            # Set the mock tab as the current widget
            self.main_window.connection_tabs.currentWidget = MagicMock(return_value=self.mock_tab)
    
    def test_open_database_manager(self):
        """Test opening the database manager from the main window"""
        # Mock the DatabaseManagerDialog
        with patch('src.ui.main_window.DatabaseManagerDialog') as mock_dialog:
            # Mock the exec method to return a value
            mock_dialog_instance = MagicMock()
            mock_dialog.return_value = mock_dialog_instance
            
            # Call the method to open the database manager
            self.main_window._open_database_manager()
            
            # Check that the dialog was created with the correct connection
            mock_dialog.assert_called_once_with(self.mock_connection, self.main_window)
            
            # Check that exec was called on the dialog
            mock_dialog_instance.exec.assert_called_once()
            
            # Check that the database browser was refreshed
            self.mock_browser.tree_model.refresh.assert_called_once()
    
    def test_open_database_manager_no_connection(self):
        """Test opening the database manager when there's no active connection"""
        # Mock the connection tab to have no connection
        mock_tab_no_conn = MagicMock()
        mock_tab_no_conn.connection = None
        self.main_window.connection_tabs.currentWidget = MagicMock(return_value=mock_tab_no_conn)
        
        # Mock QMessageBox.warning
        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call the method to open the database manager
            self.main_window._open_database_manager()
            
            # Check that the warning was shown
            mock_warning.assert_called_once()
            
            # Check the warning message
            self.assertIn("Please connect to a database first", mock_warning.call_args[0][2])


if __name__ == '__main__':
    unittest.main()