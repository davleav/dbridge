"""
Connection tab for managing a single database connection
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QTabWidget, QLabel,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.ui.query_editor import QueryEditor
from src.ui.results_view import ResultsView
from src.ui.database_browser import DatabaseBrowser

class ConnectionTab(QWidget):
    """Widget representing a single database connection tab"""
    
    # Signal emitted when the connection is closed
    connection_closed = pyqtSignal(str)
    
    def __init__(self, connection, parent=None):
        """Initialize with a database connection"""
        super().__init__(parent)
        
        self.connection = connection
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
        
        # Query editor
        self.query_editor = QueryEditor()
        editor_results_splitter.addWidget(self.query_editor)
        
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
        self.query_editor.set_query(query)
        # Automatically run the query after setting it and return the result
        return self.run_query()
    
    def run_query(self):
        """Execute the current query in the editor"""
        query = self.query_editor.get_query()
        if not query.strip():
            return
        
        try:
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