"""
Tests for the database connection dialog
"""

import unittest
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from PyQt6.QtWidgets import QApplication, QDialogButtonBox
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.ui.connection_dialog import ConnectionDialog


class TestConnectionDialog(unittest.TestCase):
    """Test cases for the ConnectionDialog class"""
    
    # Add type annotations for instance attributes
    dialog: ConnectionDialog
    
    def setUp(self):
        """Set up test fixtures"""
        self.dialog = ConnectionDialog()
    
    def test_ui_components_created(self):
        """Test that UI components were created"""
        self.assertIsNotNone(self.dialog.name_edit)
        self.assertIsNotNone(self.dialog.conn_tabs)
        
        # Check MySQL tab components
        self.assertIsNotNone(self.dialog.mysql_host)
        self.assertIsNotNone(self.dialog.mysql_port)
        self.assertIsNotNone(self.dialog.mysql_user)
        self.assertIsNotNone(self.dialog.mysql_password)
        self.assertIsNotNone(self.dialog.mysql_save_password)  # Check for save password checkbox
        self.assertIsNotNone(self.dialog.mysql_database)
        
        # Check PostgreSQL tab components
        self.assertIsNotNone(self.dialog.pg_host)
        self.assertIsNotNone(self.dialog.pg_port)
        self.assertIsNotNone(self.dialog.pg_user)
        self.assertIsNotNone(self.dialog.pg_password)
        self.assertIsNotNone(self.dialog.pg_save_password)  # Check for save password checkbox
        self.assertIsNotNone(self.dialog.pg_database)
        
        # Check SQLite tab components
        self.assertIsNotNone(self.dialog.sqlite_file)
    
    def test_default_values(self):
        """Test default values in the dialog"""
        # Check MySQL defaults
        self.assertEqual(self.dialog.mysql_host.text(), "localhost")
        self.assertEqual(self.dialog.mysql_port.value(), 3306)
        self.assertFalse(self.dialog.mysql_save_password.isChecked())  # Save password should be unchecked by default
        
        # Check PostgreSQL defaults
        self.assertEqual(self.dialog.pg_host.text(), "localhost")
        self.assertEqual(self.dialog.pg_port.value(), 5432)
        self.assertFalse(self.dialog.pg_save_password.isChecked())  # Save password should be unchecked by default
    
    def test_get_connection_params_mysql(self):
        """Test getting MySQL connection parameters"""
        # Set the connection name
        self.dialog.name_edit.setText("Test MySQL Connection")
        
        # Select the MySQL tab
        self.dialog.conn_tabs.setCurrentIndex(0)
        
        # Set MySQL connection parameters
        self.dialog.mysql_host.setText("mysql.example.com")
        self.dialog.mysql_port.setValue(3307)
        self.dialog.mysql_user.setText("testuser")
        self.dialog.mysql_password.setText("testpass")
        self.dialog.mysql_database.setText("testdb")
        self.dialog.mysql_save_password.setChecked(True)  # Set save password to true
        
        # Get the connection parameters
        params = self.dialog.get_connection_params()
        
        # Check the parameters
        self.assertEqual(params['name'], "Test MySQL Connection")
        self.assertEqual(params['type'], "MySQL")
        self.assertEqual(params['host'], "mysql.example.com")
        self.assertEqual(params['port'], 3307)
        self.assertEqual(params['user'], "testuser")
        self.assertEqual(params['password'], "testpass")
        self.assertEqual(params['database'], "testdb")
        self.assertTrue(params['save_password'])  # Check save_password parameter
        
    def test_get_connection_params_mysql_without_database(self):
        """Test getting MySQL connection parameters without a database name"""
        # Set the connection name
        self.dialog.name_edit.setText("Test MySQL Connection No DB")
        
        # Select the MySQL tab
        self.dialog.conn_tabs.setCurrentIndex(0)
        
        # Set MySQL connection parameters (without database)
        self.dialog.mysql_host.setText("mysql.example.com")
        self.dialog.mysql_port.setValue(3307)
        self.dialog.mysql_user.setText("testuser")
        self.dialog.mysql_password.setText("testpass")
        self.dialog.mysql_database.setText("")  # Empty database name
        
        # Get the connection parameters
        params = self.dialog.get_connection_params()
        
        # Check the parameters
        self.assertEqual(params['name'], "Test MySQL Connection No DB")
        self.assertEqual(params['type'], "MySQL")
        self.assertEqual(params['host'], "mysql.example.com")
        self.assertEqual(params['port'], 3307)
        self.assertEqual(params['user'], "testuser")
        self.assertEqual(params['password'], "testpass")
        self.assertEqual(params['database'], "")
    
    def test_get_connection_params_postgresql(self):
        """Test getting PostgreSQL connection parameters"""
        # Set the connection name
        self.dialog.name_edit.setText("Test PostgreSQL Connection")
        
        # Select the PostgreSQL tab
        self.dialog.conn_tabs.setCurrentIndex(1)
        
        # Set PostgreSQL connection parameters
        self.dialog.pg_host.setText("pg.example.com")
        self.dialog.pg_port.setValue(5433)
        self.dialog.pg_user.setText("testuser")
        self.dialog.pg_password.setText("testpass")
        self.dialog.pg_database.setText("testdb")
        self.dialog.pg_save_password.setChecked(True)  # Set save password to true
        
        # Get the connection parameters
        params = self.dialog.get_connection_params()
        
        # Check the parameters
        self.assertEqual(params['name'], "Test PostgreSQL Connection")
        self.assertEqual(params['type'], "PostgreSQL")
        self.assertEqual(params['host'], "pg.example.com")
        self.assertEqual(params['port'], 5433)
        self.assertEqual(params['user'], "testuser")
        self.assertEqual(params['password'], "testpass")
        self.assertEqual(params['database'], "testdb")
        self.assertTrue(params['save_password'])  # Check save_password parameter
        
    def test_get_connection_params_postgresql_without_database(self):
        """Test getting PostgreSQL connection parameters without a database name"""
        # Set the connection name
        self.dialog.name_edit.setText("Test PostgreSQL Connection No DB")
        
        # Select the PostgreSQL tab
        self.dialog.conn_tabs.setCurrentIndex(1)
        
        # Set PostgreSQL connection parameters (without database)
        self.dialog.pg_host.setText("pg.example.com")
        self.dialog.pg_port.setValue(5433)
        self.dialog.pg_user.setText("testuser")
        self.dialog.pg_password.setText("testpass")
        self.dialog.pg_database.setText("")  # Empty database name
        
        # Get the connection parameters
        params = self.dialog.get_connection_params()
        
        # Check the parameters
        self.assertEqual(params['name'], "Test PostgreSQL Connection No DB")
        self.assertEqual(params['type'], "PostgreSQL")
        self.assertEqual(params['host'], "pg.example.com")
        self.assertEqual(params['port'], 5433)
        self.assertEqual(params['user'], "testuser")
        self.assertEqual(params['password'], "testpass")
        self.assertEqual(params['database'], "")
    
    def test_get_connection_params_sqlite(self):
        """Test getting SQLite connection parameters"""
        # Set the connection name
        self.dialog.name_edit.setText("Test SQLite Connection")
        
        # Select the SQLite tab
        self.dialog.conn_tabs.setCurrentIndex(2)
        
        # Set SQLite connection parameters
        self.dialog.sqlite_file.setText("/path/to/test.db")
        
        # Get the connection parameters
        params = self.dialog.get_connection_params()
        
        # Check the parameters
        self.assertEqual(params['name'], "Test SQLite Connection")
        self.assertEqual(params['type'], "SQLite")
        self.assertEqual(params['database'], "/path/to/test.db")
    
    def test_browse_sqlite_file(self):
        """Test browsing for a SQLite database file"""
        # Mock QFileDialog.getOpenFileName to return a test file path
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', 
                  return_value=("/path/to/test.db", "SQLite Database (*.db *.sqlite)")) as mock_dialog:
            
            # Call the browse method
            self.dialog._browse_sqlite_file()
            
            # Check that the dialog was shown
            mock_dialog.assert_called_once()
            
            # Check that the file path was set
            self.assertEqual(self.dialog.sqlite_file.text(), "/path/to/test.db")
    
    def test_validate_connection_input(self):
        """Test validating connection input"""
        # Mock QMessageBox.warning to avoid showing dialogs during tests
        with patch('PyQt6.QtWidgets.QMessageBox.warning'):
            # Test with empty connection name
            self.dialog.name_edit.setText("")
            self.assertFalse(self.dialog._validate_connection_input())
            
            # Test MySQL with valid input but no database
            self.dialog.name_edit.setText("Test Connection")
            self.dialog.conn_tabs.setCurrentIndex(0)  # MySQL tab
            self.dialog.mysql_host.setText("localhost")
            self.dialog.mysql_user.setText("testuser")
            self.dialog.mysql_database.setText("")  # Empty database name
            
            # This should now pass with our changes
            self.assertTrue(self.dialog._validate_connection_input())
            
            # Test PostgreSQL with valid input but no database
            self.dialog.conn_tabs.setCurrentIndex(1)  # PostgreSQL tab
            self.dialog.pg_host.setText("localhost")
            self.dialog.pg_user.setText("testuser")
            self.dialog.pg_database.setText("")  # Empty database name
            
            # This should now pass with our changes
            self.assertTrue(self.dialog._validate_connection_input())
            
            # Test SQLite with empty file path (should fail)
            self.dialog.conn_tabs.setCurrentIndex(2)  # SQLite tab
            self.dialog.sqlite_file.setText("")
            self.assertFalse(self.dialog._validate_connection_input())
            
            # Test SQLite with valid file path
            self.dialog.sqlite_file.setText("/path/to/test.db")
            self.assertTrue(self.dialog._validate_connection_input())
    
    def test_test_connection(self):
        """Test the test connection functionality"""
        # This is just a placeholder test since the method is not implemented
        # In a real implementation, we would mock the connection test and verify the results
        self.dialog._test_connection()
        
    def test_populate_fields_mysql(self):
        """Test populating fields with existing MySQL connection parameters"""
        # Create connection parameters with save_password=True
        connection_params = {
            'name': 'Existing MySQL Connection',
            'type': 'MySQL',
            'host': 'mysql.example.org',
            'port': 3308,
            'user': 'existinguser',
            'password': 'existingpass',
            'save_password': True,
            'database': 'existingdb'
        }
        
        # Create a new dialog with these parameters
        dialog = ConnectionDialog(None, connection_params)
        
        # Check that the fields were populated correctly
        self.assertEqual(dialog.name_edit.text(), 'Existing MySQL Connection')
        self.assertEqual(dialog.conn_tabs.currentIndex(), 0)  # MySQL tab
        self.assertEqual(dialog.mysql_host.text(), 'mysql.example.org')
        self.assertEqual(dialog.mysql_port.value(), 3308)
        self.assertEqual(dialog.mysql_user.text(), 'existinguser')
        self.assertEqual(dialog.mysql_password.text(), 'existingpass')
        self.assertTrue(dialog.mysql_save_password.isChecked())
        self.assertEqual(dialog.mysql_database.text(), 'existingdb')
        
    def test_populate_fields_postgresql(self):
        """Test populating fields with existing PostgreSQL connection parameters"""
        # Create connection parameters with save_password=False
        connection_params = {
            'name': 'Existing PostgreSQL Connection',
            'type': 'PostgreSQL',
            'host': 'pg.example.org',
            'port': 5434,
            'user': 'existinguser',
            'password': 'existingpass',
            'save_password': False,
            'database': 'existingdb'
        }
        
        # Create a new dialog with these parameters
        dialog = ConnectionDialog(None, connection_params)
        
        # Check that the fields were populated correctly
        self.assertEqual(dialog.name_edit.text(), 'Existing PostgreSQL Connection')
        self.assertEqual(dialog.conn_tabs.currentIndex(), 1)  # PostgreSQL tab
        self.assertEqual(dialog.pg_host.text(), 'pg.example.org')
        self.assertEqual(dialog.pg_port.value(), 5434)
        self.assertEqual(dialog.pg_user.text(), 'existinguser')
        self.assertEqual(dialog.pg_password.text(), 'existingpass')
        self.assertFalse(dialog.pg_save_password.isChecked())
        self.assertEqual(dialog.pg_database.text(), 'existingdb')
        
    def test_populate_fields_sqlite(self):
        """Test populating fields with existing SQLite connection parameters"""
        # Create connection parameters
        connection_params = {
            'name': 'Existing SQLite Connection',
            'type': 'SQLite',
            'database': '/path/to/existing.db'
        }
        
        # Create a new dialog with these parameters
        dialog = ConnectionDialog(None, connection_params)
        
        # Check that the fields were populated correctly
        self.assertEqual(dialog.name_edit.text(), 'Existing SQLite Connection')
        self.assertEqual(dialog.conn_tabs.currentIndex(), 2)  # SQLite tab
        self.assertEqual(dialog.sqlite_file.text(), '/path/to/existing.db')


if __name__ == '__main__':
    unittest.main()