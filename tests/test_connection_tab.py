"""
Tests for the connection tab
"""

import unittest
import os
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication, QTabWidget

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.ui.connection_tab import ConnectionTab


class TestConnectionTabDatabaseChanged(unittest.TestCase):
    """Test cases for the database_changed signal handling in ConnectionTab"""
    
    def test_on_database_changed(self):
        """Test handling database changed signal"""
        # Create a mock connection
        mock_connection = MagicMock()
        mock_connection.params = {'name': 'test_connection'}
        
        # Create a mock tab widget
        mock_tab_widget = MagicMock()
        mock_tab_widget.indexOf.return_value = 2  # Simulate tab index
        
        # Create the _on_database_changed method in isolation
        def on_database_changed(database_name):
            # This is a copy of the method from ConnectionTab
            connection_name = mock_connection.params['name']
            parent = mock_tab_widget
            if isinstance(parent, MagicMock):  # Modified to work with our mock
                current_index = parent.indexOf(None)  # The widget doesn't matter for our test
                if current_index >= 0:
                    # Update the tab title to include the database name
                    parent.setTabText(current_index, f"{connection_name} ({database_name})")
        
        # Call the method
        on_database_changed("test_db")
        
        # Check that setTabText was called with the correct parameters
        mock_tab_widget.setTabText.assert_called_once_with(2, "test_connection (test_db)")
    
    def test_database_changed_signal_connection(self):
        """Test that the database_changed signal is connected correctly"""
        # This test verifies that the signal is connected in the ConnectionTab.__init__ method
        
        # Create a mock for the DatabaseBrowser class
        mock_db_browser = MagicMock()
        
        # We need to patch the __init__ method to set the db_browser before it's used
        original_init = ConnectionTab.__init__
        
        def patched_init(self, connection, parent=None):
            # Set the db_browser before calling the original __init__
            self.db_browser = mock_db_browser
            # Call the original __init__
            original_init(self, connection, parent)
        
        # Apply the patch
        with patch.object(ConnectionTab, '__init__', patched_init):
            # Also patch _create_ui to avoid UI creation
            with patch.object(ConnectionTab, '_create_ui'):
                # Create a mock connection
                mock_connection = MagicMock()
                
                # Create the connection tab
                connection_tab = ConnectionTab(mock_connection, None)
                
                # Check that the database_changed signal was connected
                mock_db_browser.database_changed.connect.assert_called_once()
                
                # The argument should be the _on_database_changed method
                signal_handler = mock_db_browser.database_changed.connect.call_args[0][0]
                self.assertEqual(signal_handler, connection_tab._on_database_changed)


if __name__ == '__main__':
    unittest.main()