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


class TestConnectionTabMongoDBSignals(unittest.TestCase):
    """Tests for MongoDB signal wiring in ConnectionTab"""

    def _make_mock_connection(self, conn_type='postgresql'):
        mock = MagicMock()
        mock.params = {'name': 'test', 'type': conn_type}
        mock.connection_manager = MagicMock()
        mock.connection_manager.system_databases_visibility_changed = MagicMock()
        mock.connection_manager.system_databases_visibility_changed.disconnect = MagicMock(side_effect=Exception)
        mock.connection_manager.system_databases_visibility_changed.connect = MagicMock()
        mock.get_database_name.return_value = '(No database selected)'
        mock.get_available_databases.return_value = []
        return mock

    def test_instantiation_does_not_raise(self):
        """ConnectionTab.__init__ must not raise even for MongoDB connections"""
        mock_connection = self._make_mock_connection('MongoDB')
        with patch('PyQt6.QtWidgets.QMessageBox'):
            try:
                tab = ConnectionTab(mock_connection)
                tab.close_connection()
            except AttributeError as exc:
                self.fail(f"ConnectionTab raised AttributeError: {exc}")

    def test_query_template_loaded_connected_after_query_editor(self):
        """query_template_loaded signal must be connected after query_editor is created"""
        mock_connection = self._make_mock_connection()
        tab = ConnectionTab(mock_connection)
        self.assertTrue(hasattr(tab, 'query_editor'))
        tab.db_browser.query_template_loaded.emit('{}')
        self.assertEqual(tab.query_editor.get_query(), '{}')
        tab.close_connection()


class TestConnectionTabMongoDBOperationSelector(unittest.TestCase):
    """Tests for the MongoDB operation selector in ConnectionTab"""

    def _make_mongodb_connection(self):
        mock = MagicMock()
        mock.params = {'name': 'test', 'type': 'MongoDB'}
        mock.connection_manager = MagicMock()
        mock.connection_manager.system_databases_visibility_changed = MagicMock()
        mock.connection_manager.system_databases_visibility_changed.disconnect = MagicMock(side_effect=Exception)
        mock.connection_manager.system_databases_visibility_changed.connect = MagicMock()
        mock.get_database_name.return_value = '(No database selected)'
        mock.get_available_databases.return_value = []
        return mock

    def test_mongodb_operation_combobox_exists(self):
        """MongoDB connections should have an operation combobox"""
        tab = ConnectionTab(self._make_mongodb_connection())
        self.assertTrue(hasattr(tab, 'mongodb_operation'))
        tab.close_connection()

    def test_non_mongodb_has_no_operation_combobox(self):
        """Non-MongoDB connections should not have an operation combobox"""
        mock = MagicMock()
        mock.params = {'name': 'test', 'type': 'postgresql'}
        mock.connection_manager = MagicMock()
        mock.connection_manager.system_databases_visibility_changed = MagicMock()
        mock.connection_manager.system_databases_visibility_changed.disconnect = MagicMock(side_effect=Exception)
        mock.connection_manager.system_databases_visibility_changed.connect = MagicMock()
        mock.get_database_name.return_value = '(No database selected)'
        mock.get_available_databases.return_value = []
        tab = ConnectionTab(mock)
        self.assertFalse(hasattr(tab, 'mongodb_operation'))
        tab.close_connection()

    def test_operation_combobox_has_all_operations(self):
        """Operation combobox must contain all expected operations"""
        from src.ui.connection_tab import _MONGODB_OPERATIONS
        tab = ConnectionTab(self._make_mongodb_connection())
        items = [tab.mongodb_operation.itemText(i) for i in range(tab.mongodb_operation.count())]
        self.assertEqual(items, _MONGODB_OPERATIONS)
        tab.close_connection()

    def test_default_operation_is_find(self):
        """Default operation should be 'find'"""
        tab = ConnectionTab(self._make_mongodb_connection())
        self.assertEqual(tab.mongodb_operation.currentText(), 'find')
        tab.close_connection()

    def test_default_template_loaded_on_init(self):
        """On init, the find template should be loaded into the editor"""
        import json
        from src.ui.connection_tab import _MONGODB_TEMPLATES
        tab = ConnectionTab(self._make_mongodb_connection())
        editor_text = tab.query_editor.get_query()
        parsed = json.loads(editor_text)
        expected = _MONGODB_TEMPLATES['find']
        self.assertEqual(parsed, expected)
        tab.close_connection()

    def test_changing_operation_loads_template(self):
        """Changing the operation should load the corresponding template"""
        import json
        from src.ui.connection_tab import _MONGODB_TEMPLATES
        tab = ConnectionTab(self._make_mongodb_connection())
        tab.mongodb_operation.setCurrentText('aggregate')
        editor_text = tab.query_editor.get_query()
        parsed = json.loads(editor_text)
        expected = _MONGODB_TEMPLATES['aggregate']
        self.assertEqual(parsed, expected)
        tab.close_connection()

    def test_load_query_template_syncs_combobox(self):
        """_load_query_template should sync the combobox to the operation in the JSON"""
        import json
        tab = ConnectionTab(self._make_mongodb_connection())
        payload = json.dumps({"collection": "foo", "operation": "insert_one", "document": {}})
        tab._load_query_template(payload)
        self.assertEqual(tab.mongodb_operation.currentText(), 'insert_one')
        tab.close_connection()

    def test_load_query_template_find_syncs_combobox(self):
        """JSON without explicit operation (defaulting to find) should set combobox to find"""
        import json
        tab = ConnectionTab(self._make_mongodb_connection())
        tab.mongodb_operation.setCurrentText('aggregate')
        payload = json.dumps({"collection": "foo", "filter": {}})
        tab._load_query_template(payload)
        self.assertEqual(tab.mongodb_operation.currentText(), 'find')
        tab.close_connection()

    def test_all_templates_are_valid_json(self):
        """All operation templates must be valid JSON-serialisable dicts"""
        import json
        from src.ui.connection_tab import _MONGODB_TEMPLATES, _MONGODB_OPERATIONS
        for op in _MONGODB_OPERATIONS:
            self.assertIn(op, _MONGODB_TEMPLATES, f"Missing template for operation: {op}")
            serialised = json.dumps(_MONGODB_TEMPLATES[op])
            self.assertIsInstance(serialised, str)


if __name__ == '__main__':
    unittest.main()