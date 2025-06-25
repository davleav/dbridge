"""
Tests for the database manager interface
"""

import unittest
import os
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any

from PyQt6.QtWidgets import QApplication, QDialog, QTableWidgetItem, QCheckBox, QMessageBox
from PyQt6.QtCore import Qt

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

# Import the module we'll be creating
from src.ui.database_manager import DatabaseManagerDialog, set_global_test_mode


class TestDatabaseManagerDialog(unittest.TestCase):
    """Test cases for the DatabaseManagerDialog class"""
    
    # Add type annotations for instance attributes
    mock_connection: MagicMock
    dialog: DatabaseManagerDialog
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests"""
        # Enable global test mode
        set_global_test_mode(True)
    
    def setUp(self):
        """Set up test fixtures for each test"""
        # Create a mock connection
        self.mock_connection = MagicMock()
        self.mock_connection.get_database_name.return_value = "test_db"
        self.mock_connection.get_tables.return_value = ["table1", "table2"]
        self.mock_connection.get_columns.return_value = [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "TEXT"}
        ]
        self.mock_connection.get_indexes.return_value = [
            {"name": "idx_id", "columns": ["id"]}
        ]
        
        # Create the dialog with the mock connection
        self.dialog = DatabaseManagerDialog(self.mock_connection)
    
    def test_dialog_creation(self):
        """Test that the dialog is created correctly"""
        self.assertIsInstance(self.dialog, QDialog)
        self.assertEqual(self.dialog.windowTitle(), "Database Manager")
    
    def test_ui_components_created(self):
        """Test that UI components were created"""
        # Check that the main components exist
        self.assertTrue(hasattr(self.dialog, 'tabs'))
        self.assertTrue(hasattr(self.dialog, 'database_tab'))
        self.assertTrue(hasattr(self.dialog, 'tables_tab'))
        self.assertTrue(hasattr(self.dialog, 'columns_tab'))
        self.assertTrue(hasattr(self.dialog, 'indexes_tab'))
    
    def test_database_tab_components(self):
        """Test that the database tab components exist"""
        # Check that the database tab has the necessary components
        self.assertTrue(hasattr(self.dialog.database_tab, 'create_db_button'))
        self.assertTrue(hasattr(self.dialog.database_tab, 'drop_db_button'))
        self.assertTrue(hasattr(self.dialog.database_tab, 'databases_list'))
    
    def test_tables_tab_components(self):
        """Test that the tables tab components exist"""
        # Check that the tables tab has the necessary components
        self.assertTrue(hasattr(self.dialog.tables_tab, 'create_table_button'))
        self.assertTrue(hasattr(self.dialog.tables_tab, 'drop_table_button'))
        self.assertTrue(hasattr(self.dialog.tables_tab, 'tables_list'))
        self.assertTrue(hasattr(self.dialog.tables_tab, 'db_selector'))
    
    def test_columns_tab_components(self):
        """Test that the columns tab components exist"""
        # Check that the columns tab has the necessary components
        self.assertTrue(hasattr(self.dialog.columns_tab, 'add_column_button'))
        self.assertTrue(hasattr(self.dialog.columns_tab, 'modify_column_button'))
        self.assertTrue(hasattr(self.dialog.columns_tab, 'drop_column_button'))
        self.assertTrue(hasattr(self.dialog.columns_tab, 'table_selector'))
        self.assertTrue(hasattr(self.dialog.columns_tab, 'columns_list'))
    
    def test_indexes_tab_components(self):
        """Test that the indexes tab components exist"""
        # Check that the indexes tab has the necessary components
        self.assertTrue(hasattr(self.dialog.indexes_tab, 'create_index_button'))
        self.assertTrue(hasattr(self.dialog.indexes_tab, 'drop_index_button'))
        self.assertTrue(hasattr(self.dialog.indexes_tab, 'table_selector'))
        self.assertTrue(hasattr(self.dialog.indexes_tab, 'indexes_list'))
    
    def test_create_database(self):
        """Test creating a database"""
        # Mock the input dialog to return a database name
        with patch('PyQt6.QtWidgets.QInputDialog.getText', return_value=("new_database", True)):
            # Mock the connection's execute_non_query method
            with patch.object(self.mock_connection, 'execute_non_query') as mock_execute:
                # Call the create database method
                self.dialog._create_database()
                
                # Check that execute_non_query was called with the correct SQL
                mock_execute.assert_called_once_with("CREATE DATABASE new_database;")
    
    def test_drop_database(self):
        """Test dropping a database"""
        # Mock the message box to return Yes (StandardButton.Yes)
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            # Mock the connection's execute_non_query method
            with patch.object(self.mock_connection, 'execute_non_query') as mock_execute:
                # Add an item to the databases list
                self.dialog.database_tab.databases_list.addItem("test_db")
                
                # Set the selected database
                self.dialog.database_tab.databases_list.setCurrentRow(0)
                
                # Call the drop database method
                self.dialog._drop_database()
                
                # Check that execute_non_query was called with the correct SQL
                mock_execute.assert_called_once_with("DROP DATABASE test_db;")
    
    def test_create_table(self):
        """Test creating a table"""
        # Set up the database selector in the tables tab
        self.dialog.tables_tab.db_selector.addItem("test_db")
        self.dialog.tables_tab.db_selector.setCurrentText("test_db")
        
        # Mock the create table dialog to return a table definition
        with patch('src.ui.database_manager.CreateTableDialog.exec', return_value=True):
            with patch('src.ui.database_manager.CreateTableDialog.get_table_definition', return_value={
                'name': 'new_table',
                'columns': [
                    {'name': 'id', 'type': 'INTEGER', 'primary_key': True, 'nullable': False},
                    {'name': 'name', 'type': 'TEXT', 'primary_key': False, 'nullable': True}
                ]
            }):
                # Mock the connection's execute_non_query method
                with patch.object(self.mock_connection, 'execute_non_query') as mock_execute:
                    # Mock the populate methods
                    with patch.object(self.dialog, '_populate_tables') as mock_populate_tables:
                        with patch.object(self.dialog, '_populate_table_selectors') as mock_populate_table_selectors:
                            # Call the create table method
                            self.dialog._create_table()
                            
                            # Check that execute_non_query was called with the correct SQL
                            mock_execute.assert_called_once()
                            # The SQL should contain CREATE TABLE and the column definitions
                            self.assertIn("CREATE TABLE", mock_execute.call_args[0][0])
                            self.assertIn("id INTEGER NOT NULL PRIMARY KEY", mock_execute.call_args[0][0])
                            self.assertIn("name TEXT", mock_execute.call_args[0][0])
                            
                            # Check that the populate methods were called with the correct database
                            mock_populate_tables.assert_called_once_with("test_db")
                            mock_populate_table_selectors.assert_called_once_with("test_db")
    
    def test_drop_table(self):
        """Test dropping a table"""
        # Set up the database selector in the tables tab
        self.dialog.tables_tab.db_selector.addItem("test_db")
        self.dialog.tables_tab.db_selector.setCurrentText("test_db")
        
        # Mock the message box to return Yes
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            # Mock the connection's execute_non_query method
            with patch.object(self.mock_connection, 'execute_non_query') as mock_execute:
                # Mock the populate methods
                with patch.object(self.dialog, '_populate_tables') as mock_populate_tables:
                    with patch.object(self.dialog, '_populate_table_selectors') as mock_populate_table_selectors:
                        # Add an item to the tables list
                        self.dialog.tables_tab.tables_list.addItem("table1")
                        
                        # Set the selected table
                        self.dialog.tables_tab.tables_list.setCurrentRow(0)
                        
                        # Call the drop table method
                        self.dialog._drop_table()
                        
                        # Check that execute_non_query was called with the correct SQL
                        mock_execute.assert_called_once_with("DROP TABLE table1;")
                        
                        # Check that the populate methods were called with the correct database
                        mock_populate_tables.assert_called_once_with("test_db")
                        mock_populate_table_selectors.assert_called_once_with("test_db")
    
    def test_add_column(self):
        """Test adding a column to a table"""
        # Mock the add column dialog to return a column definition
        with patch('src.ui.database_manager.AddColumnDialog.exec', return_value=True):
            with patch('src.ui.database_manager.AddColumnDialog.get_column_definition', return_value={
                'name': 'new_column',
                'type': 'TEXT',
                'nullable': True,
                'default': None
            }):
                # Mock the connection's execute_non_query method
                with patch.object(self.mock_connection, 'execute_non_query') as mock_execute:
                    # Set up the database selector in the tables tab
                    self.dialog.tables_tab.db_selector.addItem("test_db")
                    self.dialog.tables_tab.db_selector.setCurrentText("test_db")
                    
                    # Set the selected table
                    self.dialog.columns_tab.table_selector.setCurrentText("table1")
                    
                    # Mock the get_database_name method to return the test database
                    self.mock_connection.get_database_name.return_value = "test_db"
                    
                    # Call the add column method
                    self.dialog._add_column()
                    
                    # Check that execute_non_query was called with the correct SQL
                    mock_execute.assert_called_once()
                    self.assertIn("ALTER TABLE table1 ADD COLUMN new_column TEXT", mock_execute.call_args[0][0])
    
    def test_drop_column(self):
        """Test dropping a column from a table"""
        # Mock the message box to return Yes
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            # Mock the connection's execute_non_query method
            with patch.object(self.mock_connection, 'execute_non_query') as mock_execute:
                # Set up the database selector in the tables tab
                self.dialog.tables_tab.db_selector.addItem("test_db")
                self.dialog.tables_tab.db_selector.setCurrentText("test_db")
                
                # Set up the table selector and columns list
                self.dialog.columns_tab.table_selector.addItem("table1")
                self.dialog.columns_tab.table_selector.setCurrentText("table1")
                self.dialog.columns_tab.columns_list.addItem("id (INTEGER)")
                self.dialog.columns_tab.columns_list.setCurrentRow(0)
                
                # Mock the get_database_name method to return the test database
                self.mock_connection.get_database_name.return_value = "test_db"
                
                # Set the database type to MySQL for this test (to avoid SQLite version check)
                self.mock_connection.params = {'type': 'MySQL'}
                
                # Call the drop column method
                self.dialog._drop_column()
                
                # Check that execute_non_query was called with the correct SQL
                mock_execute.assert_called_once()
                self.assertIn("ALTER TABLE table1 DROP COLUMN id", mock_execute.call_args[0][0])
    
    def test_create_index(self):
        """Test creating an index"""
        # Mock the create index dialog to return an index definition
        with patch('src.ui.database_manager.CreateIndexDialog.exec', return_value=True):
            with patch('src.ui.database_manager.CreateIndexDialog.get_index_definition', return_value={
                'name': 'idx_name',
                'table': 'table1',
                'columns': ['name'],
                'unique': False
            }):
                # Mock the connection's execute_non_query method
                with patch.object(self.mock_connection, 'execute_non_query') as mock_execute:
                    # Set up the database selector in the tables tab
                    self.dialog.tables_tab.db_selector.addItem("test_db")
                    self.dialog.tables_tab.db_selector.setCurrentText("test_db")
                    
                    # Set the selected table
                    self.dialog.indexes_tab.table_selector.setCurrentText("table1")
                    
                    # Mock the get_database_name method to return the test database
                    self.mock_connection.get_database_name.return_value = "test_db"
                    
                    # Call the create index method
                    self.dialog._create_index()
                    
                    # Check that execute_non_query was called with the correct SQL
                    mock_execute.assert_called_once()
                    self.assertIn("CREATE INDEX idx_name ON table1 (name)", mock_execute.call_args[0][0])
    
    def test_drop_index(self):
        """Test dropping an index"""
        # Mock the message box to return Yes
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            # Mock the connection's execute_non_query method
            with patch.object(self.mock_connection, 'execute_non_query') as mock_execute:
                # Set up the database selector in the tables tab
                self.dialog.tables_tab.db_selector.addItem("test_db")
                self.dialog.tables_tab.db_selector.setCurrentText("test_db")
                
                # Set up the table selector and indexes list
                self.dialog.indexes_tab.table_selector.addItem("table1")
                self.dialog.indexes_tab.table_selector.setCurrentText("table1")
                self.dialog.indexes_tab.indexes_list.addItem("idx_id")
                self.dialog.indexes_tab.indexes_list.setCurrentRow(0)
                
                # Mock the get_database_name method to return the test database
                self.mock_connection.get_database_name.return_value = "test_db"
                
                # Set the database type to SQLite for this test
                self.mock_connection.params = {'type': 'SQLite'}
                
                # Call the drop index method
                self.dialog._drop_index()
                
                # Check that execute_non_query was called with the correct SQL
                mock_execute.assert_called_once()
                self.assertIn("DROP INDEX idx_id", mock_execute.call_args[0][0])
    
    def test_populate_db_selector(self):
        """Test populating the database selector in the tables tab"""
        # Mock the connection's get_available_databases method
        self.mock_connection.get_available_databases.return_value = ["db1", "db2", "test_db"]
        
        # Call the populate method
        self.dialog._populate_db_selector()
        
        # Check that the database selector was populated correctly
        self.assertEqual(self.dialog.tables_tab.db_selector.count(), 3)
        self.assertEqual(self.dialog.tables_tab.db_selector.itemText(0), "db1")
        self.assertEqual(self.dialog.tables_tab.db_selector.itemText(1), "db2")
        self.assertEqual(self.dialog.tables_tab.db_selector.itemText(2), "test_db")
        
        # Check that the current database is selected
        self.assertEqual(self.dialog.tables_tab.db_selector.currentText(), "test_db")
    
    def test_on_database_selection_changed(self):
        """Test handling database selection change in the database tab"""
        # Add items to the databases list
        self.dialog.database_tab.databases_list.addItem("db1")
        self.dialog.database_tab.databases_list.addItem("db2")
        
        # Add items to the tables tab database selector
        self.dialog.tables_tab.db_selector.addItem("db1")
        self.dialog.tables_tab.db_selector.addItem("db2")
        
        # Select a database in the database tab
        self.dialog.database_tab.databases_list.setCurrentRow(1)  # Select "db2"
        
        # Call the method
        self.dialog._on_database_selection_changed()
        
        # Check that the database selector in the tables tab was updated
        self.assertEqual(self.dialog.tables_tab.db_selector.currentText(), "db2")
    
    def test_on_tables_db_changed(self):
        """Test handling database selection change in the tables tab"""
        # Mock the populate methods
        with patch.object(self.dialog, '_populate_tables') as mock_populate_tables:
            with patch.object(self.dialog, '_populate_table_selectors') as mock_populate_table_selectors:
                # Call the method with a database name
                self.dialog._on_tables_db_changed("test_db")
                
                # Check that the populate methods were called with the correct database
                mock_populate_tables.assert_called_once_with("test_db")
                mock_populate_table_selectors.assert_called_once_with("test_db")
    
    def test_on_tab_changed(self):
        """Test handling tab changes"""
        # Set up the database tab
        self.dialog.database_tab.databases_list.addItem("test_db")
        self.dialog.database_tab.databases_list.setCurrentRow(0)
        
        # Set up the tables tab
        self.dialog.tables_tab.db_selector.addItem("test_db")
        self.dialog.tables_tab.tables_list.addItem("table1")
        self.dialog.tables_tab.tables_list.setCurrentRow(0)
        
        # Set up the columns tab
        self.dialog.columns_tab.table_selector.addItem("table1")
        
        # Set up the indexes tab
        self.dialog.indexes_tab.table_selector.addItem("table1")
        
        # Test switching to the tables tab
        self.dialog._on_tab_changed(1)  # Index 1 is the tables tab
        self.assertEqual(self.dialog.tables_tab.db_selector.currentText(), "test_db")
        
        # Test switching to the columns tab
        self.dialog._on_tab_changed(2)  # Index 2 is the columns tab
        self.assertEqual(self.dialog.columns_tab.table_selector.currentText(), "table1")
        
        # Test switching to the indexes tab
        self.dialog._on_tab_changed(3)  # Index 3 is the indexes tab
        self.assertEqual(self.dialog.indexes_tab.table_selector.currentText(), "table1")


class TestCreateTableDialog(unittest.TestCase):
    """Test cases for the CreateTableDialog class"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests"""
        # Enable global test mode
        set_global_test_mode(True)
    
    def setUp(self):
        """Set up test fixtures for each test"""
        # Import the dialog class
        from src.ui.database_manager import CreateTableDialog
        
        # Create the dialog
        self.dialog = CreateTableDialog()
    
    def test_dialog_creation(self):
        """Test that the dialog is created correctly"""
        self.assertIsInstance(self.dialog, QDialog)
        self.assertEqual(self.dialog.windowTitle(), "Create Table")
    
    def test_ui_components_created(self):
        """Test that UI components were created"""
        # Check that the main components exist
        self.assertTrue(hasattr(self.dialog, 'table_name_edit'))
        self.assertTrue(hasattr(self.dialog, 'columns_table'))
        self.assertTrue(hasattr(self.dialog, 'add_column_button'))
        self.assertTrue(hasattr(self.dialog, 'remove_column_button'))
    
    def test_add_column(self):
        """Test adding a column to the table definition"""
        # Get the initial row count
        initial_rows = self.dialog.columns_table.rowCount()
        
        # Call the add column method
        self.dialog._add_column()
        
        # Check that a row was added
        self.assertEqual(self.dialog.columns_table.rowCount(), initial_rows + 1)
    
    def test_remove_column(self):
        """Test removing a column from the table definition"""
        # Add a column first
        self.dialog._add_column()
        
        # Get the row count after adding
        rows_after_add = self.dialog.columns_table.rowCount()
        
        # Select the row
        self.dialog.columns_table.selectRow(0)
        
        # Call the remove column method
        self.dialog._remove_column()
        
        # Check that a row was removed
        self.assertEqual(self.dialog.columns_table.rowCount(), rows_after_add - 1)
    
    def test_get_table_definition(self):
        """Test getting the table definition"""
        # Set the table name
        self.dialog.table_name_edit.setText("test_table")
        
        # Add a column
        self.dialog._add_column()
        
        # Set the column values
        self.dialog.columns_table.setItem(0, 0, QTableWidgetItem("id"))
        self.dialog.columns_table.setItem(0, 1, QTableWidgetItem("INTEGER"))
        
        # Set the primary key checkbox
        pk_checkbox = QCheckBox()
        pk_checkbox.setChecked(True)
        self.dialog.columns_table.setCellWidget(0, 2, pk_checkbox)
        
        # Set the nullable checkbox
        nullable_checkbox = QCheckBox()
        nullable_checkbox.setChecked(False)
        self.dialog.columns_table.setCellWidget(0, 3, nullable_checkbox)
        
        # Get the table definition
        definition = self.dialog.get_table_definition()
        
        # Check the definition
        self.assertEqual(definition['name'], "test_table")
        self.assertEqual(len(definition['columns']), 1)
        self.assertEqual(definition['columns'][0]['name'], "id")
        self.assertEqual(definition['columns'][0]['type'], "INTEGER")
        self.assertTrue(definition['columns'][0]['primary_key'])
        self.assertFalse(definition['columns'][0]['nullable'])


class TestAddColumnDialog(unittest.TestCase):
    """Test cases for the AddColumnDialog class"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests"""
        # Enable global test mode
        set_global_test_mode(True)
    
    def setUp(self):
        """Set up test fixtures for each test"""
        # Import the dialog class
        from src.ui.database_manager import AddColumnDialog
        
        # Create the dialog
        self.dialog = AddColumnDialog()
    
    def test_dialog_creation(self):
        """Test that the dialog is created correctly"""
        self.assertIsInstance(self.dialog, QDialog)
        self.assertEqual(self.dialog.windowTitle(), "Add Column")
    
    def test_ui_components_created(self):
        """Test that UI components were created"""
        # Check that the main components exist
        self.assertTrue(hasattr(self.dialog, 'column_name_edit'))
        self.assertTrue(hasattr(self.dialog, 'column_type_combo'))
        self.assertTrue(hasattr(self.dialog, 'nullable_checkbox'))
        self.assertTrue(hasattr(self.dialog, 'default_value_edit'))
    
    def test_get_column_definition(self):
        """Test getting the column definition"""
        # Set the column values
        self.dialog.column_name_edit.setText("test_column")
        self.dialog.column_type_combo.setCurrentText("TEXT")
        self.dialog.nullable_checkbox.setChecked(True)
        self.dialog.default_value_edit.setText("'default'")
        
        # Get the column definition
        definition = self.dialog.get_column_definition()
        
        # Check the definition
        self.assertEqual(definition['name'], "test_column")
        self.assertEqual(definition['type'], "TEXT")
        self.assertTrue(definition['nullable'])
        self.assertEqual(definition['default'], "'default'")


class TestCreateIndexDialog(unittest.TestCase):
    """Test cases for the CreateIndexDialog class"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests"""
        # Enable global test mode
        set_global_test_mode(True)
    
    def setUp(self):
        """Set up test fixtures for each test"""
        # Import the dialog class
        from src.ui.database_manager import CreateIndexDialog
        
        # Create a mock connection
        self.mock_connection = MagicMock()
        self.mock_connection.get_tables.return_value = ["table1", "table2"]
        self.mock_connection.get_columns.return_value = [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "TEXT"}
        ]
        
        # Create the dialog
        self.dialog = CreateIndexDialog(self.mock_connection)
    
    def test_dialog_creation(self):
        """Test that the dialog is created correctly"""
        self.assertIsInstance(self.dialog, QDialog)
        self.assertEqual(self.dialog.windowTitle(), "Create Index")
    
    def test_ui_components_created(self):
        """Test that UI components were created"""
        # Check that the main components exist
        self.assertTrue(hasattr(self.dialog, 'index_name_edit'))
        self.assertTrue(hasattr(self.dialog, 'table_combo'))
        self.assertTrue(hasattr(self.dialog, 'columns_list'))
        self.assertTrue(hasattr(self.dialog, 'unique_checkbox'))
    
    def test_table_selection_updates_columns(self):
        """Test that selecting a table updates the columns list"""
        # Set the table selection
        self.dialog.table_combo.setCurrentText("table1")
        
        # Check that the columns list was updated
        self.assertEqual(self.dialog.columns_list.count(), 2)
        
        # Get items with null checks
        item0 = self.dialog.columns_list.item(0)
        self.assertIsNotNone(item0, "First item should not be None")
        # Use assert to help Pylance understand item0 is not None
        assert item0 is not None
        self.assertEqual(item0.text(), "id")
        
        item1 = self.dialog.columns_list.item(1)
        self.assertIsNotNone(item1, "Second item should not be None")
        # Use assert to help Pylance understand item1 is not None
        assert item1 is not None
        self.assertEqual(item1.text(), "name")
    
    def test_get_index_definition(self):
        """Test getting the index definition"""
        # Set the index values
        self.dialog.index_name_edit.setText("idx_test")
        self.dialog.table_combo.setCurrentText("table1")
        
        # Select a column
        item = self.dialog.columns_list.item(0)
        self.assertIsNotNone(item, "First item should not be None")
        # Use assert to help Pylance understand item is not None
        assert item is not None
        item.setSelected(True)
        
        # Set the unique checkbox
        self.dialog.unique_checkbox.setChecked(True)
        
        # Get the index definition
        definition = self.dialog.get_index_definition()
        
        # Check the definition
        self.assertEqual(definition['name'], "idx_test")
        self.assertEqual(definition['table'], "table1")
        self.assertEqual(definition['columns'], ["id"])
        self.assertTrue(definition['unique'])


if __name__ == '__main__':
    unittest.main()