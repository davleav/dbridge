"""
Connection tab for managing a single database connection
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget, QLabel,
    QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.ui.query_editor import QueryEditor
from src.ui.results_view import ResultsView
from src.ui.database_browser import DatabaseBrowser

_MONGODB_OPERATIONS = [
    'find', 'aggregate',
    'insert_one', 'insert_many',
    'update_one', 'update_many',
    'delete_one', 'delete_many',
    'create_collection', 'drop_collection',
]

_MONGODB_TEMPLATES = {
    'find': {
        "collection": "collection_name",
        "filter": {},
        "projection": None,
        "limit": 50,
        "sort": None,
    },
    'aggregate': {
        "collection": "collection_name",
        "operation": "aggregate",
        "pipeline": [
            {"$match": {}},
            {"$limit": 50},
        ],
    },
    'insert_one': {
        "collection": "collection_name",
        "operation": "insert_one",
        "document": {"field1": "value1"},
    },
    'insert_many': {
        "collection": "collection_name",
        "operation": "insert_many",
        "documents": [
            {"field1": "value1"},
            {"field1": "value2"},
        ],
    },
    'update_one': {
        "collection": "collection_name",
        "operation": "update_one",
        "filter": {"_id": "document_id"},
        "update": {"$set": {"field": "new_value"}},
    },
    'update_many': {
        "collection": "collection_name",
        "operation": "update_many",
        "filter": {},
        "update": {"$set": {"field": "new_value"}},
    },
    'delete_one': {
        "collection": "collection_name",
        "operation": "delete_one",
        "filter": {"_id": "document_id"},
    },
    'delete_many': {
        "collection": "collection_name",
        "operation": "delete_many",
        "filter": {},
    },
    'create_collection': {
        "operation": "create_collection",
        "name": "new_collection_name",
    },
    'drop_collection': {
        "operation": "drop_collection",
        "name": "collection_name",
    },
}


class ConnectionTab(QWidget):
    """Widget representing a single database connection tab"""
    
    # Signal emitted when the connection is closed
    connection_closed = pyqtSignal(str)
    
    def __init__(self, connection, parent=None):
        """Initialize with a database connection"""
        super().__init__(parent)
        
        self.connection = connection
        self.database_manager_dialog = None
        self._create_ui()
        
        # Connect to the database browser's signals
        self.db_browser.database_changed.connect(self._on_database_changed)
    
    def _create_ui(self):
        """Create the UI components for this connection tab"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a splitter for the main components
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Database browser on the left
        self.db_browser = DatabaseBrowser()
        self.db_browser.set_connection(self.connection)
        self.db_browser.query_generated.connect(self._set_query_text)
        self.main_splitter.addWidget(self.db_browser)
        
        # Query and results on the right
        self.right_widget = QWidget()
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a vertical splitter for query editor and results
        editor_results_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Query editor area
        is_mongodb = self.connection.params.get('type') == 'MongoDB'
        query_editor_widget = QWidget()
        query_editor_layout = QVBoxLayout(query_editor_widget)
        query_editor_layout.setContentsMargins(0, 0, 0, 0)
        query_editor_layout.setSpacing(2)

        if is_mongodb:
            op_row = QHBoxLayout()
            op_label = QLabel("Operation:")
            self.mongodb_operation = QComboBox()
            self.mongodb_operation.addItems(_MONGODB_OPERATIONS)
            op_row.addWidget(op_label)
            op_row.addWidget(self.mongodb_operation)
            op_row.addStretch()
            query_editor_layout.addLayout(op_row)

        self.query_editor = QueryEditor()
        if is_mongodb:
            self.query_editor.set_mode('mongodb')
            self.mongodb_operation.currentTextChanged.connect(self._on_mongodb_operation_changed)
            self._on_mongodb_operation_changed('find')
        query_editor_layout.addWidget(self.query_editor)
        editor_results_splitter.addWidget(query_editor_widget)
        self.db_browser.query_template_loaded.connect(self._load_query_template)
        
        # Results area with tabs
        self.results_tabs = QTabWidget()
        self.results_view = ResultsView()
        # Set the connection on the results view
        self.results_view.set_connection(self.connection)
        self.results_tabs.addTab(self.results_view, "Results")
        editor_results_splitter.addWidget(self.results_tabs)
        
        # Set initial sizes for the vertical splitter
        editor_results_splitter.setSizes([300, 400])
        
        right_layout.addWidget(editor_results_splitter)
        self.main_splitter.addWidget(self.right_widget)
        
        # Set initial sizes for the main splitter (30% left, 70% right)
        self.main_splitter.setSizes([300, 700])
        
        # Store the original sizes for restoring later
        self._db_browser_visible = True
        self._original_sizes = self.main_splitter.sizes()
        
        layout.addWidget(self.main_splitter)
    
    def _set_query_text(self, query):
        """Set the query text in the editor and automatically run it"""
        self._load_query_template(query)
        return self.run_query()

    def _load_query_template(self, query):
        """Load a query template into the editor, syncing the operation combobox for MongoDB."""
        self.query_editor.set_query(query)
        if hasattr(self, 'mongodb_operation'):
            import json as _json
            try:
                parsed = _json.loads(query)
                op = parsed.get('operation', 'find')
                idx = self.mongodb_operation.findText(op)
                if idx >= 0:
                    self.mongodb_operation.blockSignals(True)
                    self.mongodb_operation.setCurrentIndex(idx)
                    self.mongodb_operation.blockSignals(False)
            except (ValueError, AttributeError):
                pass

    def _on_mongodb_operation_changed(self, operation):
        """Load a JSON template for the selected MongoDB operation into the editor."""
        import json as _json
        template = _MONGODB_TEMPLATES.get(operation, {})
        self.query_editor.set_query(_json.dumps(template, indent=2))
    
    def run_query(self):
        """Execute the current query in the editor"""
        query = self.query_editor.get_query()
        if not query.strip():
            return

        try:
            is_mongodb = self.connection.params.get('type') == 'MongoDB'

            if is_mongodb:
                return self._run_mongodb_query(query)

            # Determine if this is a SELECT query or a non-query statement
            split_query = query.strip().upper().split(None, 1)
            query_type = split_query[0] if split_query else ""
            
            if query_type in ('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN'):
                # For queries that return data
                result = self.connection.execute_query(query)
                self.results_view.set_data(result)
                return True, f"Query executed successfully on {self.connection.params['name']}"
            else:
                # For non-query statements (INSERT, UPDATE, DELETE, etc.)
                affected_rows = self.connection.execute_non_query(query)
                # Create a DataFrame to show the result
                import pandas as pd
                result = pd.DataFrame([{'Affected Rows': affected_rows}])
                self.results_view.set_data(result)
                
                # Refresh the database browser to show updated data
                if hasattr(self, 'db_browser') and self.db_browser:
                    # Refresh the tree model
                    if hasattr(self.db_browser, 'tree_model') and self.db_browser.tree_model:
                        self.db_browser.tree_model.refresh()
                
                return True, f"{affected_rows} row(s) affected on {self.connection.params['name']}"
        except Exception as e:
            QMessageBox.critical(self, "Query Error", str(e))
            return False, "Query failed"

    def _run_mongodb_query(self, query):
        """Execute a MongoDB JSON query string."""
        import json
        import pandas as pd

        try:
            parsed = json.loads(query)
        except (json.JSONDecodeError, ValueError) as e:
            QMessageBox.critical(self, "Query Error", f"Invalid JSON: {e}")
            return False, "Query failed"

        operation = parsed.get('operation', 'find')
        read_operations = {'find', 'aggregate'}

        try:
            if operation in read_operations:
                result = self.connection.execute_query(query)
                self.results_view.set_data(result)
                return True, f"Query executed successfully on {self.connection.params['name']}"
            else:
                affected_rows = self.connection.execute_non_query(query)
                result = pd.DataFrame([{'Affected Rows': affected_rows}])
                self.results_view.set_data(result)

                if hasattr(self, 'db_browser') and self.db_browser:
                    if hasattr(self.db_browser, 'tree_model') and self.db_browser.tree_model:
                        self.db_browser.tree_model.refresh()

                return True, f"{affected_rows} row(s) affected on {self.connection.params['name']}"
        except Exception as e:
            QMessageBox.critical(self, "Query Error", str(e))
            return False, "Query failed"
    
    def get_connection_name(self):
        """Get the name of the connection"""
        return self.connection.params['name']
    
    def toggle_database_browser(self):
        """Toggle the visibility of the database browser
        
        Returns:
            bool: True if the database browser is now visible, False otherwise
        """
        if self._db_browser_visible:
            # Hide the database browser
            self._original_sizes = self.main_splitter.sizes()
            self.main_splitter.setSizes([0, sum(self.main_splitter.sizes())])
            self.db_browser.hide()
            self._db_browser_visible = False
        else:
            # Show the database browser
            self.db_browser.show()
            if self._original_sizes:
                self.main_splitter.setSizes(self._original_sizes)
            else:
                # Default sizes if original sizes are not available
                total_width = sum(self.main_splitter.sizes())
                self.main_splitter.setSizes([int(total_width * 0.3), int(total_width * 0.7)])
            self._db_browser_visible = True
        
        return self._db_browser_visible
    
    def is_database_browser_visible(self):
        """Check if the database browser is currently visible
        
        Returns:
            bool: True if the database browser is visible, False otherwise
        """
        return self._db_browser_visible
    
    def _on_database_changed(self, database_name):
        """Handle when the database is changed in the browser"""
        # Update the tab title to include the database name
        connection_name = self.connection.params['name']
        parent = self.parent()
        if isinstance(parent, QTabWidget):
            current_index = parent.indexOf(self)
            if current_index >= 0:
                # Update the tab title to include the database name
                parent.setTabText(current_index, f"{connection_name} ({database_name})")
    
    def close_connection(self):
        """Close the database connection"""
        try:
            connection_name = self.connection.params['name']
            self.connection.close()
            self.db_browser.clear_connection()
            # Clear the connection in the results view as well
            if hasattr(self, 'results_view') and self.results_view:
                self.results_view.set_connection(None)
            self.connection_closed.emit(connection_name)
            return True
        except Exception as e:
            print(f"Error closing connection: {e}")
            return False