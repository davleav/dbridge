"""
Database browser for exploring database structure
"""

import os
import subprocess

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QMenu,
    QInputDialog, QMessageBox, QFileDialog,
    QPushButton, QHBoxLayout, QFrame, QLabel, QListWidget
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon

from src.ui.import_export_dialog import ImportExportDialog
from src.ui.database_manager import DatabaseManagerDialog

class DatabaseTreeModel(QStandardItemModel):
    """Tree model for displaying database structure"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(["Database Objects"])
        self.connection = None
    
    def set_connection(self, connection):
        """Set the database connection and refresh the model"""
        self.connection = connection
        # If connection is None, completely clear the model
        if connection is None:
            # First remove all rows
            self.removeRows(0, self.rowCount())
            # Then clear any remaining data
            self.clear()
            # Reset the header
            self.setHorizontalHeaderLabels(["Database Objects"])
        else:
            self.refresh()
    
    def refresh(self):
        """Refresh the database structure"""
        self.clear()
        self.setHorizontalHeaderLabels(["Database Objects"])
        
        if not self.connection:
            # Ensure the model is completely empty when there's no connection
            return
        
        # Add database root item
        db_name = self.connection.get_database_name()
        db_item = QStandardItem(db_name)
        db_item.setData("database", Qt.ItemDataRole.UserRole)
        self.appendRow(db_item)
        
        # Check if a database is selected
        has_database_selected = db_name != "(No database selected)"
        
        if not has_database_selected:
            # If no database is selected, only show available databases folder
            # 1. Available Databases folder
            databases_item = QStandardItem("Available Databases")
            databases_item.setData("databases_folder", Qt.ItemDataRole.UserRole)
            db_item.appendRow(databases_item)
            
            # Get available databases
            try:
                databases = self.connection.get_available_databases()
                for db in databases:
                    db_item_child = QStandardItem(db)
                    db_item_child.setData("available_database", Qt.ItemDataRole.UserRole)
                    db_item_child.setData(db, Qt.ItemDataRole.UserRole + 1)
                    databases_item.appendRow(db_item_child)
            except Exception as e:
                print(f"Error getting available databases: {e}")
                error_item = QStandardItem("Error loading databases")
                error_item.setData("message", Qt.ItemDataRole.UserRole)
                databases_item.appendRow(error_item)
        else:
            # Only show tables and views when a database is selected
            
            # Add tables folder
            tables_item = QStandardItem("Tables")
            tables_item.setData("tables_folder", Qt.ItemDataRole.UserRole)
            db_item.appendRow(tables_item)
            
            # Get tables
            try:
                tables = self.connection.get_tables()
                for table in tables:
                    table_item = QStandardItem(table)
                    table_item.setData("table", Qt.ItemDataRole.UserRole)
                    table_item.setData(table, Qt.ItemDataRole.UserRole + 1)
                    tables_item.appendRow(table_item)
                    
                    # Add columns folder
                    columns_item = QStandardItem("Columns")
                    columns_item.setData("columns_folder", Qt.ItemDataRole.UserRole)
                    table_item.appendRow(columns_item)
                    
                    # Add columns
                    columns = self.connection.get_columns(table)
                    for column in columns:
                        column_item = QStandardItem(f"{column['name']} ({column['type']})")
                        column_item.setData("column", Qt.ItemDataRole.UserRole)
                        column_item.setData(column, Qt.ItemDataRole.UserRole + 1)
                        columns_item.appendRow(column_item)
                    
                    # Add indexes folder
                    indexes_item = QStandardItem("Indexes")
                    indexes_item.setData("indexes_folder", Qt.ItemDataRole.UserRole)
                    table_item.appendRow(indexes_item)
                    
                    # Add indexes
                    indexes = self.connection.get_indexes(table)
                    for index in indexes:
                        index_item = QStandardItem(index['name'])
                        index_item.setData("index", Qt.ItemDataRole.UserRole)
                        index_item.setData(index, Qt.ItemDataRole.UserRole + 1)
                        indexes_item.appendRow(index_item)
            except Exception as e:
                # If we can't get tables, add a placeholder item to indicate this
                no_db_item = QStandardItem("No tables found")
                no_db_item.setData("message", Qt.ItemDataRole.UserRole)
                tables_item.appendRow(no_db_item)
            
            # Add views folder
            views_item = QStandardItem("Views")
            views_item.setData("views_folder", Qt.ItemDataRole.UserRole)
            db_item.appendRow(views_item)
            
            # Get views
            try:
                views = self.connection.get_views()
                for view in views:
                    view_item = QStandardItem(view)
                    view_item.setData("view", Qt.ItemDataRole.UserRole)
                    view_item.setData(view, Qt.ItemDataRole.UserRole + 1)
                    views_item.appendRow(view_item)
            except Exception as e:
                # If we can't get views, add a placeholder item to indicate this
                no_db_item = QStandardItem("No views found")
                no_db_item.setData("message", Qt.ItemDataRole.UserRole)
                views_item.appendRow(no_db_item)


class DatabaseBrowser(QWidget):
    """Widget for browsing database structure"""
    
    # Signal to emit when a query is generated
    query_generated = pyqtSignal(str)
    
    # Signal to emit when the database is changed
    database_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tree view for database structure
        self.tree_view = QTreeView()
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_view.doubleClicked.connect(self._handle_double_click)
        
        self.tree_model = DatabaseTreeModel()
        self.tree_view.setModel(self.tree_model)
        
        layout.addWidget(self.tree_view)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Create button container
        self.button_container = QVBoxLayout()
        self.button_container.setContentsMargins(0, 5, 0, 5)
        
        # Create buttons for when no database is selected
        self.no_db_buttons = QVBoxLayout()
        
        # Refresh Available Databases button
        self.refresh_btn = QPushButton("Refresh Available Databases")
        self.refresh_btn.clicked.connect(self._refresh_databases)
        self.no_db_buttons.addWidget(self.refresh_btn)
        
        # Import SQL File button
        self.import_sql_btn = QPushButton("Import SQL File")
        self.import_sql_btn.clicked.connect(self._import_sql_file)
        self.no_db_buttons.addWidget(self.import_sql_btn)
        
        # Database Manager button
        self.db_manager_btn = QPushButton("Database Manager")
        self.db_manager_btn.clicked.connect(self._open_database_manager)
        self.no_db_buttons.addWidget(self.db_manager_btn)
        
        # Create buttons for when a database is selected
        self.db_selected_buttons = QVBoxLayout()
        
        # Deselect Database button
        self.deselect_db_btn = QPushButton("Deselect Database")
        self.deselect_db_btn.clicked.connect(self._deselect_database)
        self.db_selected_buttons.addWidget(self.deselect_db_btn)
        
        # Export Database button
        self.export_db_btn = QPushButton("Export Database")
        self.export_db_btn.clicked.connect(self._export_database)
        self.db_selected_buttons.addWidget(self.export_db_btn)
        
        # Export All Tables button
        self.export_tables_btn = QPushButton("Export All Tables")
        self.export_tables_btn.clicked.connect(self._export_all_tables)
        self.db_selected_buttons.addWidget(self.export_tables_btn)
        
        # Import SQL File button (for db selected state)
        self.import_sql_db_btn = QPushButton("Import SQL File")
        self.import_sql_db_btn.clicked.connect(self._import_sql_file)
        self.db_selected_buttons.addWidget(self.import_sql_db_btn)
        
        # Database Manager button (for db selected state)
        self.db_manager_db_btn = QPushButton("Database Manager")
        self.db_manager_db_btn.clicked.connect(self._open_database_manager)
        self.db_selected_buttons.addWidget(self.db_manager_db_btn)
                
        # Add button layouts to container
        self.button_container.addLayout(self.no_db_buttons)
        self.button_container.addLayout(self.db_selected_buttons)
        
        # Add button container to main layout
        layout.addLayout(self.button_container)
        
        # Initially hide all buttons until a connection is set
        self._update_button_visibility(None)
        
    def clear(self):
        """Clear the database tree view completely by recreating it from scratch"""
        # Save the current connection if it exists
        connection = None
        if hasattr(self, 'tree_model') and self.tree_model and hasattr(self.tree_model, 'connection'):
            connection = self.tree_model.connection
        
        # First disconnect all signals from the old tree view
        if hasattr(self, 'tree_view'):
            self.tree_view.setModel(None)
            self.tree_view.doubleClicked.disconnect()
            self.tree_view.customContextMenuRequested.disconnect()
            self.tree_view.deleteLater()
        
        # Delete the old model if it exists
        if hasattr(self, 'tree_model') and self.tree_model:
            self.tree_model.deleteLater()
        
        # Completely recreate the UI
        self._create_ui()
        
        # Restore the connection if it existed
        if connection:
            self.set_connection(connection)
        
        # Force a repaint
        self.update()
    
    def set_connection(self, connection):
        """Set the database connection"""
        # Check if the model is a DatabaseTreeModel
        if not hasattr(self.tree_model, 'set_connection'):
            # If not, recreate the model as a DatabaseTreeModel
            self.tree_model = DatabaseTreeModel(self)
            self.tree_view.setModel(self.tree_model)
        
        # Now set the connection
        self.tree_model.set_connection(connection)
        self.tree_view.expandToDepth(0)
        
        # Update button visibility based on connection state
        self._update_button_visibility(connection)
        
    def clear_connection(self):
        """Clear the current connection"""
        print("Using the updated clear_connection method")
        try:
            # Simply set the connection to None in the tree model
            if hasattr(self, 'tree_model') and self.tree_model:
                self.tree_model.set_connection(None)
            
            # Update button visibility
            self._update_button_visibility(None)
            
            # Force a repaint
            self.update()
        except Exception as e:
            print(f"Error in clear_connection: {e}")
            # If there's an error, try to recreate the tree view and model
            self.clear()
    
    def _show_context_menu(self, position):
        """Show context menu for tree items"""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return
        
        item = self.tree_model.itemFromIndex(index)
        if item is None:
            return
        item_type = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        
        # Database root item context menu
        if item_type == "database":
            # Database context menu
            export_db_action = QAction("Export Database...", self)
            export_db_action.triggered.connect(self._export_database)
            menu.addAction(export_db_action)
            
            import_sql_action = QAction("Import SQL File...", self)
            import_sql_action.triggered.connect(self._import_sql_file)
            menu.addAction(import_sql_action)
            
            # Get the current database name
            if self.tree_model.connection is None:
                db_name = "(No database selected)"
            else:
                db_name = self.tree_model.connection.get_database_name()
            
            menu.addSeparator()
            
            # If no database is selected, add a refresh action to update available databases
            if db_name == "(No database selected)":
                refresh_action = QAction("Refresh Available Databases", self)
                refresh_action.triggered.connect(lambda: self.tree_model.refresh())
                menu.addAction(refresh_action)
            else:
                # If a database is selected, add an option to deselect it if user has permissions
                # Always allow deselecting the database, as this is a UI operation
                deselect_action = QAction("Deselect Database", self)
                deselect_action.triggered.connect(self._deselect_database)
                menu.addAction(deselect_action)
        
        # Available database context menu
        elif item_type == "available_database":
            database_name = item.data(Qt.ItemDataRole.UserRole + 1)
            if database_name is None:
                return
            
            use_db_action = QAction(f"Use Database '{database_name}'", self)
            use_db_action.triggered.connect(lambda: self._use_database(database_name))
            menu.addAction(use_db_action)
        
        # Databases folder context menu
        elif item_type == "databases_folder":
            refresh_action = QAction("Refresh Available Databases", self)
            refresh_action.triggered.connect(lambda: self.tree_model.refresh())
            menu.addAction(refresh_action)
        
        # Tables folder context menu
        elif item_type == "tables_folder":
            export_tables_action = QAction("Export All Tables...", self)
            export_tables_action.triggered.connect(self._export_database)
            menu.addAction(export_tables_action)
        
        # Table context menu
        elif item_type == "table":
            table_name = item.data(Qt.ItemDataRole.UserRole + 1)
            if table_name is None:
                return
            
            select_action = QAction("Select All Rows", self)
            select_action.triggered.connect(lambda: self._generate_select_query(table_name))
            menu.addAction(select_action)
            
            menu.addSeparator()
            
            structure_action = QAction("Show Structure", self)
            structure_action.triggered.connect(lambda: self._show_table_structure(table_name))
            menu.addAction(structure_action)
            
            menu.addSeparator()
            
            # Export options
            export_menu = QMenu("Export", menu)
            
            export_sql_action = QAction("Export as SQL...", self)
            export_sql_action.triggered.connect(lambda: self._export_table(table_name, "sql"))
            export_menu.addAction(export_sql_action)
            
            export_csv_action = QAction("Export as CSV...", self)
            export_csv_action.triggered.connect(lambda: self._export_table(table_name, "csv"))
            export_menu.addAction(export_csv_action)
            
            export_excel_action = QAction("Export as Excel...", self)
            export_excel_action.triggered.connect(lambda: self._export_table(table_name, "xlsx"))
            export_menu.addAction(export_excel_action)
            
            menu.addMenu(export_menu)
        
        # View context menu
        elif item_type == "view":
            view_name = item.data(Qt.ItemDataRole.UserRole + 1)
            if view_name is None:
                return
            
            select_action = QAction("Select All Rows", self)
            select_action.triggered.connect(lambda: self._generate_select_query(view_name))
            menu.addAction(select_action)
            
            menu.addSeparator()
            
            show_def_action = QAction("Show Definition", self)
            show_def_action.triggered.connect(lambda: self._show_view_definition(view_name))
            menu.addAction(show_def_action)
            
            menu.addSeparator()
            
            # Export options
            export_menu = QMenu("Export", menu)
            
            export_csv_action = QAction("Export as CSV...", self)
            export_csv_action.triggered.connect(lambda: self._export_table(view_name, "csv"))
            export_menu.addAction(export_csv_action)
            
            export_excel_action = QAction("Export as Excel...", self)
            export_excel_action.triggered.connect(lambda: self._export_table(view_name, "xlsx"))
            export_menu.addAction(export_excel_action)
            
            menu.addMenu(export_menu)
        
        if menu.actions() and self.tree_view:
            viewport = self.tree_view.viewport()
            if viewport:
                menu.exec(viewport.mapToGlobal(position))
    
    def _handle_double_click(self, index):
        """Handle double-click on tree items"""
        if not index.isValid():
            return
        
        item = self.tree_model.itemFromIndex(index)
        if item is None:
            return
        item_type = item.data(Qt.ItemDataRole.UserRole)
        
        if item_type == "table":
            # Generate SELECT query for the table
            table_name = item.data(Qt.ItemDataRole.UserRole + 1)
            if table_name is not None:
                self._generate_select_query(table_name)
        elif item_type == "available_database":
            # Switch to the selected database
            database_name = item.data(Qt.ItemDataRole.UserRole + 1)
            if database_name is not None:
                self._use_database(database_name)
    
    def _use_database(self, database_name):
        """Switch to the selected database"""
        if not self.tree_model.connection:
            return
            
        try:
            # Use the database
            success = self.tree_model.connection.use_database(database_name)
            
            if success:
                # Refresh the tree view to show the new database structure
                self.tree_model.refresh()
                
                # Expand the database node to show its contents
                root_index = self.tree_model.index(0, 0)
                self.tree_view.expand(root_index)
                
                # Update button visibility to show database-selected buttons
                self._update_button_visibility(self.tree_model.connection)
                
                # Emit the database_changed signal
                self.database_changed.emit(database_name)
                
                # Show a message in the status bar
                self._show_status_message(f"Connected to database: {database_name}")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Database Error", f"Failed to switch to database: {database_name}")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Database Error", f"Error switching to database: {str(e)}")
    
    def _deselect_database(self):
        """Deselect the current database and show available databases"""
        if not self.tree_model.connection:
            return
            
        try:
            # Deselect the database
            success = self.tree_model.connection.deselect_database()
            
            if success:
                # Refresh the tree view to show available databases
                self.tree_model.refresh()
                
                # Expand the database node to show available databases
                root_index = self.tree_model.index(0, 0)
                self.tree_view.expand(root_index)
                
                # Also expand the Available Databases folder
                if root_index.isValid() and self.tree_model.rowCount(root_index) > 0:
                    databases_folder_index = self.tree_model.index(0, 0, root_index)
                    if databases_folder_index.isValid():
                        self.tree_view.expand(databases_folder_index)
                
                # Update button visibility to show no-database-selected buttons
                self._update_button_visibility(self.tree_model.connection)
                
                # Emit the database_changed signal with "(No database selected)"
                self.database_changed.emit("(No database selected)")
                
                # Show a message in the status bar
                self._show_status_message("Database deselected. Showing available databases.")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Database Error", "Failed to deselect database.")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Database Error", f"Error deselecting database: {str(e)}")
    
    def _generate_select_query(self, table_name):
        """Generate a SELECT query for the table/view"""
        query = f"SELECT * FROM {table_name} LIMIT 50;"
        
        # Emit the signal with the generated query
        self.query_generated.emit(query)
    
    def _show_table_structure(self, table_name):
        """Show the table structure"""
        # This would display the table structure in a dialog or new tab
        print(f"Show structure for table: {table_name}")
    
    def _show_view_definition(self, view_name):
        """Show the view definition"""
        # This would display the view definition in a dialog or new tab
        print(f"Show definition for view: {view_name}")
    
    def _export_database(self):
        """Export the entire database"""
        if not hasattr(self.tree_model, 'connection') or not self.tree_model.connection:
            QMessageBox.warning(self, "Export Error", "No active database connection.")
            return
        
        # Open the export dialog
        dialog = ImportExportDialog(self.tree_model.connection, "export", self)
        dialog.exec()
    
    def _import_sql_file(self):
        """Import a SQL file into the database"""
        if not hasattr(self.tree_model, 'connection') or not self.tree_model.connection:
            QMessageBox.warning(self, "Import Error", "No active database connection.")
            return
        
        # Open the import dialog
        dialog = ImportExportDialog(self.tree_model.connection, "import", self)
        if dialog.exec():
            # Refresh the database browser after import
            self.tree_model.refresh()
    
    def _show_status_message(self, message, timeout=3000):
        """Show a message in the status bar if available
        
        Args:
            message: The message to show
            timeout: The timeout in milliseconds
        """
        parent = self.parent()
        while parent:
            if hasattr(parent, 'status_bar'):
                # Use getattr to avoid type checking issues
                status_bar = getattr(parent, 'status_bar', None)
                if status_bar and hasattr(status_bar, 'showMessage'):
                    status_bar.showMessage(message, timeout)
                    break
            parent = parent.parent()
    
    def _update_button_visibility(self, connection):
        """Update button visibility based on connection state"""
        # Hide all button layouts first
        for i in range(self.no_db_buttons.count()):
            item = self.no_db_buttons.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget:
                    widget.hide()
                
        for i in range(self.db_selected_buttons.count()):
            item = self.db_selected_buttons.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget:
                    widget.hide()
        
        # If no connection, hide all buttons
        if not connection:
            return
            
        # Get the database name to determine if a database is selected
        db_name = connection.get_database_name()
        has_database_selected = db_name != "(No database selected)"
        
        # Show appropriate buttons based on database selection state
        if has_database_selected:
            # Show buttons for when a database is selected
            for i in range(self.db_selected_buttons.count()):
                item = self.db_selected_buttons.itemAt(i)
                if item is not None:
                    widget = item.widget()
                    if widget:
                        widget.show()
        else:
            # Show buttons for when no database is selected
            for i in range(self.no_db_buttons.count()):
                item = self.no_db_buttons.itemAt(i)
                if item is not None:
                    widget = item.widget()
                    if widget:
                        widget.show()
    
    def _refresh_databases(self):
        """Refresh the list of available databases"""
        if not hasattr(self.tree_model, 'connection') or not self.tree_model.connection:
            QMessageBox.warning(self, "Refresh Error", "No active database connection.")
            return
            
        # Refresh the tree model
        self.tree_model.refresh()
        
        # Expand the database node to show available databases
        root_index = self.tree_model.index(0, 0)
        self.tree_view.expand(root_index)
        
        # Also expand the Available Databases folder
        if root_index.isValid() and self.tree_model.rowCount(root_index) > 0:
            databases_folder_index = self.tree_model.index(0, 0, root_index)
            if databases_folder_index.isValid():
                self.tree_view.expand(databases_folder_index)
    
    def _open_database_manager(self):
        """Open the database manager dialog"""
        if not hasattr(self.tree_model, 'connection') or not self.tree_model.connection:
            QMessageBox.warning(
                self,
                "No Connection",
                "Please connect to a database first before using the Database Manager."
            )
            return
        
        # Create and show the database manager dialog
        # Set debug_mode to False to reduce console output
        dialog = DatabaseManagerDialog(self.tree_model.connection, self, debug_mode=False)
        if dialog.exec():
            # Refresh the tree view after changes
            self.tree_model.refresh()
    
    def _export_all_tables(self):
        """Export all tables in the database"""
        # This is essentially the same as _export_database
        self._export_database()
    
    def _export_table(self, table_name, format_type):
        """Export a single table"""
        if not hasattr(self.tree_model, 'connection') or not self.tree_model.connection:
            QMessageBox.warning(self, "Export Error", "No active database connection.")
            return
        
        connection = self.tree_model.connection
        
        # Determine file extension
        if format_type == "sql":
            file_filter = "SQL Files (*.sql)"
            default_ext = ".sql"
        elif format_type == "csv":
            file_filter = "CSV Files (*.csv)"
            default_ext = ".csv"
        else:  # xlsx
            file_filter = "Excel Files (*.xlsx)"
            default_ext = ".xlsx"
        
        # First, select a directory
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            ""
        )
        
        if not directory:
            return
            
        # Now, get a filename
        filename, ok = QInputDialog.getText(
            self,
            "Enter Filename",
            f"Enter filename (with {default_ext} extension):",
            text=f"{table_name}{default_ext}"
        )
        
        if not ok or not filename:
            return
            
        # Add extension if not present
        if not filename.lower().endswith(default_ext):
            filename = f"{filename}{default_ext}"
            
        # Construct full file path
        file_path = os.path.join(directory, filename)
        
        # Check if file exists and confirm overwrite
        if os.path.exists(file_path):
            confirm = QMessageBox.question(
                self,
                "File Exists",
                f"The file '{filename}' already exists. Do you want to replace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if confirm != QMessageBox.StandardButton.Yes:
                return
        
        try:
            # Show a progress dialog
            from PyQt6.QtWidgets import QProgressDialog
            from PyQt6.QtCore import Qt
            
            progress = QProgressDialog(f"Exporting table {table_name}...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setValue(10)
            
            if format_type == "sql":
                # SQL export for a single table
                db_type = connection.params['type']
                progress.setLabelText(f"Exporting {table_name} as SQL ({db_type})...")
                connection.export_database_to_sql(file_path, [table_name])
            else:
                # CSV or Excel export
                progress.setLabelText(f"Fetching data from {table_name}...")
                data = connection.execute_query(f"SELECT * FROM {table_name}")
                
                progress.setValue(50)
                progress.setLabelText(f"Writing {format_type.upper()} file...")
                
                if format_type == "csv":
                    data.to_csv(file_path, index=False)
                else:  # xlsx
                    data.to_excel(file_path, index=False)
            
            progress.setValue(100)
            QMessageBox.information(self, "Export Complete", f"Table '{table_name}' exported successfully to {file_path}")
        except subprocess.CalledProcessError as e:
            # Handle command-line tool errors
            error_msg = f"Export failed with error code {e.returncode}.\n\n"
            
            if hasattr(e, 'stderr') and e.stderr:
                error_details = e.stderr.decode('utf-8', errors='replace')
                error_msg += f"Error details:\n{error_details}"
            else:
                error_msg += "No additional error details available."
            
            QMessageBox.critical(self, "Export Error", error_msg)
        except Exception as e:
            # Handle other errors
            error_msg = f"Failed to export table: {str(e)}"
            QMessageBox.critical(self, "Export Error", error_msg)