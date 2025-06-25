"""
Tests for the database browser
"""

import unittest
import os
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtCore import Qt, QModelIndex, QPoint
from PyQt6.QtGui import QStandardItem, QAction

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.ui.database_browser import DatabaseBrowser, DatabaseTreeModel


class TestDatabaseTreeModel(unittest.TestCase):
    """Test cases for the DatabaseTreeModel class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = DatabaseTreeModel()
        
        # Create a mock connection
        self.mock_connection = MagicMock()
        self.mock_connection.get_database_name.return_value = "test_db"
        self.mock_connection.get_tables.return_value = ["table1", "table2"]
        self.mock_connection.get_views.return_value = ["view1"]
        self.mock_connection.get_available_databases.return_value = ["db1", "db2", "db3"]
        
        # Mock get_columns to return test columns
        self.mock_connection.get_columns.return_value = [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "TEXT"}
        ]
        
        # Mock get_indexes to return test indexes
        self.mock_connection.get_indexes.return_value = [
            {"name": "idx_id", "columns": ["id"]}
        ]
    
    def test_set_connection(self):
        """Test setting a connection and refreshing the model"""
        # Set the connection
        with patch.object(self.model, 'refresh') as mock_refresh:
            self.model.set_connection(self.mock_connection)
            
            # Check that the connection was set
            self.assertEqual(self.model.connection, self.mock_connection)
            
            # Check that refresh was called
            mock_refresh.assert_called_once()
    
    def test_refresh(self):
        """Test refreshing the model with database structure"""
        # Set the connection
        self.model.connection = self.mock_connection
        
        # Refresh the model
        self.model.refresh()
        
        # Check that the model was populated correctly
        self.assertEqual(self.model.rowCount(), 1)  # Database root item
        
        # Get the database item
        db_item = self.model.item(0)
        self.assertIsNotNone(db_item, "Database item should not be None")
        # Use if check to satisfy Pylance
        if db_item is not None:
            self.assertEqual(db_item.text(), "test_db")
            self.assertEqual(db_item.data(Qt.ItemDataRole.UserRole), "database")
            
            # Check tables folder
            self.assertEqual(db_item.rowCount(), 2)  # Tables and Views folders
            tables_item = db_item.child(0)
            self.assertIsNotNone(tables_item, "Tables item should not be None")
            # Use if check to satisfy Pylance
            if tables_item is not None:
                self.assertEqual(tables_item.text(), "Tables")
                self.assertEqual(tables_item.data(Qt.ItemDataRole.UserRole), "tables_folder")
        
        # Check tables
        if tables_item is not None:
            self.assertEqual(tables_item.rowCount(), 2)  # table1 and table2
            table1_item = tables_item.child(0)
            self.assertIsNotNone(table1_item, "Table1 item should not be None")
            if table1_item is not None:
                self.assertEqual(table1_item.text(), "table1")
                self.assertEqual(table1_item.data(Qt.ItemDataRole.UserRole), "table")
                
                # Check columns folder for table1
                self.assertEqual(table1_item.rowCount(), 2)  # Columns and Indexes folders
                columns_item = table1_item.child(0)
                self.assertIsNotNone(columns_item, "Columns item should not be None")
                if columns_item is not None:
                    self.assertEqual(columns_item.text(), "Columns")
                    self.assertEqual(columns_item.data(Qt.ItemDataRole.UserRole), "columns_folder")
                    
                    # Check columns for table1
                    self.assertEqual(columns_item.rowCount(), 2)  # id and name columns
                    id_column_item = columns_item.child(0)
                    self.assertIsNotNone(id_column_item, "ID column item should not be None")
                    if id_column_item is not None:
                        self.assertEqual(id_column_item.text(), "id (INTEGER)")
                        self.assertEqual(id_column_item.data(Qt.ItemDataRole.UserRole), "column")
                
                # Check indexes folder for table1
                indexes_item = table1_item.child(1)
                self.assertIsNotNone(indexes_item, "Indexes item should not be None")
                if indexes_item is not None:
                    self.assertEqual(indexes_item.text(), "Indexes")
                    self.assertEqual(indexes_item.data(Qt.ItemDataRole.UserRole), "indexes_folder")
                    
                    # Check indexes for table1
                    self.assertEqual(indexes_item.rowCount(), 1)  # idx_id index
                    index_item = indexes_item.child(0)
                    self.assertIsNotNone(index_item, "Index item should not be None")
                    if index_item is not None:
                        self.assertEqual(index_item.text(), "idx_id")
                        self.assertEqual(index_item.data(Qt.ItemDataRole.UserRole), "index")
        
        # Check views folder
        if db_item is not None:
            views_item = db_item.child(1)
            self.assertIsNotNone(views_item, "Views item should not be None")
            if views_item is not None:
                self.assertEqual(views_item.text(), "Views")
                self.assertEqual(views_item.data(Qt.ItemDataRole.UserRole), "views_folder")
                
                # Check views
                self.assertEqual(views_item.rowCount(), 1)  # view1
                view_item = views_item.child(0)
                self.assertIsNotNone(view_item, "View item should not be None")
                if view_item is not None:
                    self.assertEqual(view_item.text(), "view1")
                    self.assertEqual(view_item.data(Qt.ItemDataRole.UserRole), "view")
    
    def test_refresh_no_connection(self):
        """Test refreshing the model with no connection"""
        # Clear the connection
        self.model.connection = None
        
        # Refresh the model
        self.model.refresh()
        
        # Check that the model is empty
        self.assertEqual(self.model.rowCount(), 0)
        
    def test_refresh_no_database_selected(self):
        """Test refreshing the model when no database is selected"""
        # Set up a connection with no database selected
        mock_connection_no_db = MagicMock()
        mock_connection_no_db.get_database_name.return_value = "(No database selected)"
        mock_connection_no_db.get_available_databases.return_value = ["db1", "db2", "db3"]
        
        # Set the connection
        self.model.connection = mock_connection_no_db
        
        # Refresh the model
        self.model.refresh()
        
        # Check that the model was populated correctly
        self.assertEqual(self.model.rowCount(), 1)  # Database root item
        
        # Get the database item
        db_item = self.model.item(0)
        self.assertIsNotNone(db_item, "Database item should not be None")
        if db_item is not None:
            self.assertEqual(db_item.text(), "(No database selected)")
            self.assertEqual(db_item.data(Qt.ItemDataRole.UserRole), "database")
            
            # Check that the database item has the correct children - only Available Databases folder
            self.assertEqual(db_item.rowCount(), 1)  # Only Available Databases folder
            
            # Check Available Databases folder
            databases_item = db_item.child(0)
            self.assertIsNotNone(databases_item, "Databases item should not be None")
            if databases_item is not None:
                self.assertEqual(databases_item.text(), "Available Databases")
                self.assertEqual(databases_item.data(Qt.ItemDataRole.UserRole), "databases_folder")
                
                # Check that the Available Databases folder has the correct children
                self.assertEqual(databases_item.rowCount(), 3)  # db1, db2, db3
                
                # Check the first database
                db1_item = databases_item.child(0)
                self.assertIsNotNone(db1_item, "DB1 item should not be None")
                if db1_item is not None:
                    self.assertEqual(db1_item.text(), "db1")
                    self.assertEqual(db1_item.data(Qt.ItemDataRole.UserRole), "available_database")
                    self.assertEqual(db1_item.data(Qt.ItemDataRole.UserRole + 1), "db1")


class TestDatabaseBrowser(unittest.TestCase):
    """Test cases for the DatabaseBrowser class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.browser = DatabaseBrowser()
        
        # Create a mock connection
        self.mock_connection = MagicMock()
        self.mock_connection.get_database_name.return_value = "test_db"
        self.mock_connection.get_available_databases.return_value = ["db1", "db2", "db3"]
    
    def test_ui_components_created(self):
        """Test that UI components were created"""
        self.assertIsNotNone(self.browser.tree_view)
        self.assertIsNotNone(self.browser.tree_model)
    
    def test_set_connection(self):
        """Test setting a connection"""
        # Set the connection
        with patch.object(self.browser.tree_model, 'set_connection') as mock_set_connection:
            self.browser.set_connection(self.mock_connection)
            
            # Check that set_connection was called on the model
            mock_set_connection.assert_called_once_with(self.mock_connection)
    
    def test_clear_connection(self):
        """Test clearing the connection"""
        # Set the connection
        with patch.object(self.browser.tree_model, 'set_connection') as mock_set_connection:
            self.browser.clear_connection()
            
            # Check that set_connection was called with None
            mock_set_connection.assert_called_once_with(None)
    
    def test_show_context_menu(self):
        """Test showing the context menu"""
        # Create a mock index
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        
        # Create a mock item
        mock_item = MagicMock()
        # Set up the data method to return different values based on the role
        mock_item.data.side_effect = lambda role: "table" if role == Qt.ItemDataRole.UserRole else "test_table"
        
        # Mock itemFromIndex to return our mock item
        self.browser.tree_model.itemFromIndex = MagicMock(return_value=mock_item)
        
        # Mock tree_view.indexAt to return our mock index
        self.browser.tree_view.indexAt = MagicMock(return_value=mock_index)
        
        # Mock QMenu.exec to return None (no action selected)
        with patch('PyQt6.QtWidgets.QMenu.exec') as mock_exec:
            # Call the context menu method
            self.browser._show_context_menu(QPoint(0, 0))
            
            # Check that exec was called (we don't assert_called_once because it depends on implementation)
            self.assertTrue(mock_exec.called, "QMenu.exec should have been called")
    
    def test_handle_double_click(self):
        """Test handling double-click on a tree item"""
        # Create a mock index
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        
        # Create a mock item
        mock_item = MagicMock()
        mock_item.data.return_value = "table"  # Item type
        mock_item.data.side_effect = lambda role: "table" if role == Qt.ItemDataRole.UserRole else "test_table"
        
        # Mock itemFromIndex to return our mock item
        self.browser.tree_model.itemFromIndex = MagicMock(return_value=mock_item)
        
        # Mock _generate_select_query
        with patch.object(self.browser, '_generate_select_query') as mock_generate:
            # Call the double-click handler
            self.browser._handle_double_click(mock_index)
            
            # Check that _generate_select_query was called with the table name
            mock_generate.assert_called_once_with("test_table")
    
    def test_generate_select_query(self):
        """Test generating a SELECT query"""
        # Set up a signal spy to capture the emitted signal
        signal_spy = []
        self.browser.query_generated.connect(lambda query: signal_spy.append(query))
        
        # Call the method
        self.browser._generate_select_query("test_table")
        
        # Check that the signal was emitted with the correct query
        self.assertEqual(len(signal_spy), 1)
        self.assertEqual(signal_spy[0], "SELECT * FROM test_table LIMIT 50;")
    
    def test_show_table_structure(self):
        """Test showing table structure"""
        # Mock print to capture the output
        with patch('builtins.print') as mock_print:
            # Call the method
            self.browser._show_table_structure("test_table")
            
            # Check that print was called with the correct message
            mock_print.assert_called_once_with("Show structure for table: test_table")
    
    def test_show_view_definition(self):
        """Test showing view definition"""
        # Mock print to capture the output
        with patch('builtins.print') as mock_print:
            # Call the method
            self.browser._show_view_definition("test_view")
            
            # Check that print was called with the correct message
            mock_print.assert_called_once_with("Show definition for view: test_view")
    
    def test_handle_double_click_on_available_database(self):
        """Test handling double-click on an available database"""
        # Create a mock index
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        
        # Create a mock item for an available database
        mock_item = MagicMock()
        mock_item.data.side_effect = lambda role: "available_database" if role == Qt.ItemDataRole.UserRole else "test_db"
        
        # Mock itemFromIndex to return our mock item
        self.browser.tree_model.itemFromIndex = MagicMock(return_value=mock_item)
        
        # Mock _use_database
        with patch.object(self.browser, '_use_database') as mock_use_database:
            # Call the double-click handler
            self.browser._handle_double_click(mock_index)
            
            # Check that _use_database was called with the database name
            mock_use_database.assert_called_once_with("test_db")
    
    def test_use_database(self):
        """Test using a database"""
        # Set up the mock connection
        self.browser.tree_model.connection = self.mock_connection
        self.mock_connection.use_database.return_value = True
        
        # Mock the refresh method
        with patch.object(self.browser.tree_model, 'refresh') as mock_refresh:
            # Set up a signal spy to capture the emitted signal
            signal_spy = []
            self.browser.database_changed.connect(lambda db: signal_spy.append(db))
            
            # Call the method
            self.browser._use_database("test_db")
            
            # Check that use_database was called on the connection
            self.mock_connection.use_database.assert_called_once_with("test_db")
            
            # Check that refresh was called on the model
            mock_refresh.assert_called_once()
            
            # Check that the signal was emitted with the correct database name
            self.assertEqual(len(signal_spy), 1)
            self.assertEqual(signal_spy[0], "test_db")
    
    def test_use_database_failure(self):
        """Test using a database when it fails"""
        # Set up the mock connection
        self.browser.tree_model.connection = self.mock_connection
        self.mock_connection.use_database.return_value = False
        
        # Mock the refresh method and QMessageBox.warning
        with patch.object(self.browser.tree_model, 'refresh') as mock_refresh, \
             patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call the method
            self.browser._use_database("test_db")
            
            # Check that use_database was called on the connection
            self.mock_connection.use_database.assert_called_once_with("test_db")
            
            # Check that refresh was not called on the model
            mock_refresh.assert_not_called()
            
            # Check that a warning message was shown
            mock_warning.assert_called_once()
    
    def test_deselect_database(self):
        """Test deselecting a database"""
        # Set up the mock connection
        self.browser.tree_model.connection = self.mock_connection
        self.mock_connection.deselect_database.return_value = True
        
        # Mock the refresh method
        with patch.object(self.browser.tree_model, 'refresh') as mock_refresh:
            # Set up a signal spy to capture the emitted signal
            signal_spy = []
            self.browser.database_changed.connect(lambda db: signal_spy.append(db))
            
            # Call the method
            self.browser._deselect_database()
            
            # Check that deselect_database was called on the connection
            self.mock_connection.deselect_database.assert_called_once()
            
            # Check that refresh was called on the model
            mock_refresh.assert_called_once()
            
            # Check that the signal was emitted with the correct database name
            self.assertEqual(len(signal_spy), 1)
            self.assertEqual(signal_spy[0], "(No database selected)")
    
    def test_deselect_database_failure(self):
        """Test deselecting a database when it fails"""
        # Set up the mock connection
        self.browser.tree_model.connection = self.mock_connection
        self.mock_connection.deselect_database.return_value = False
        
        # Mock the refresh method and QMessageBox.warning
        with patch.object(self.browser.tree_model, 'refresh') as mock_refresh, \
             patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call the method
            self.browser._deselect_database()
            
            # Check that deselect_database was called on the connection
            self.mock_connection.deselect_database.assert_called_once()
            
            # Check that refresh was not called on the model
            mock_refresh.assert_not_called()
            
            # Check that a warning message was shown
            mock_warning.assert_called_once()
    
    def test_context_menu_for_available_database(self):
        """Test showing context menu for an available database"""
        # Create a mock index
        mock_index = MagicMock()
        mock_index.isValid.return_value = True
        
        # Create a mock item for an available database
        mock_item = MagicMock()
        mock_item.data.side_effect = lambda role: (
            "available_database" if role == Qt.ItemDataRole.UserRole else 
            "test_db" if role == Qt.ItemDataRole.UserRole + 1 else 
            "test_db"
        )
        
        # Mock itemFromIndex to return our mock item
        self.browser.tree_model.itemFromIndex = MagicMock(return_value=mock_item)
        
        # Mock tree_view.indexAt to return our mock index
        self.browser.tree_view.indexAt = MagicMock(return_value=mock_index)
        
        # Mock _use_database
        with patch.object(self.browser, '_use_database') as mock_use_database, \
             patch.object(QMenu, 'exec') as mock_exec, \
             patch.object(QAction, 'triggered') as mock_triggered:
            
            # Call the context menu method
            self.browser._show_context_menu(QPoint(0, 0))
            
            # Check that the menu was executed
            self.assertTrue(mock_exec.called)


if __name__ == '__main__':
    unittest.main()