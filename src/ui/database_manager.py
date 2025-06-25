"""
Database manager interface for creating and modifying databases, tables, columns, and indexes
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QPushButton,
    QListWidget, QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QCheckBox, QLineEdit, QMessageBox, QInputDialog, QDialogButtonBox,
    QGroupBox, QFormLayout, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
import sys
from typing import Dict, Any, Union, Optional, List, cast


# Global test mode flag
_TEST_MODE = False

# Dictionary to store original methods
_original_methods = {}

def set_global_test_mode(enabled=True):
    """Set test mode globally for all dialogs"""
    global _TEST_MODE
    _TEST_MODE = enabled
    
    # Override QMessageBox and QInputDialog methods in test mode
    if enabled:
        # Store original methods if not already stored
        if not _original_methods:
            _original_methods['information'] = QMessageBox.information
            _original_methods['warning'] = QMessageBox.warning
            _original_methods['critical'] = QMessageBox.critical
            _original_methods['question'] = QMessageBox.question
            _original_methods['getText'] = QInputDialog.getText
            _original_methods['exec'] = QDialog.exec
        
        # Override with test versions
        QMessageBox.information = lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        QMessageBox.warning = lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        QMessageBox.critical = lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        QMessageBox.question = lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        QInputDialog.getText = lambda *args, **kwargs: ("test_value", True)
        QDialog.exec = lambda self: True
    else:
        # Restore original methods if they exist
        if _original_methods:
            QMessageBox.information = _original_methods['information']
            QMessageBox.warning = _original_methods['warning']
            QMessageBox.critical = _original_methods['critical']
            QMessageBox.question = _original_methods['question']
            QInputDialog.getText = _original_methods['getText']
            QDialog.exec = _original_methods['exec']


class DatabaseTab(QWidget):
    """Tab for database management"""
    databases_list: QListWidget
    create_db_button: QPushButton
    drop_db_button: QPushButton

class TablesTab(QWidget):
    """Tab for tables management"""
    db_selector: QComboBox
    tables_list: QListWidget
    create_table_button: QPushButton
    drop_table_button: QPushButton

class ColumnsTab(QWidget):
    """Tab for columns management"""
    table_selector: QComboBox
    columns_list: QListWidget
    add_column_button: QPushButton
    modify_column_button: QPushButton
    drop_column_button: QPushButton

class IndexesTab(QWidget):
    """Tab for indexes management"""
    table_selector: QComboBox
    indexes_list: QListWidget
    create_index_button: QPushButton
    drop_index_button: QPushButton

class DatabaseManagerDialog(QDialog):
    """Dialog for managing database structure"""
    
    # Class variable to control test mode
    _test_mode = False
    
    # Tab widgets with proper type annotations
    database_tab: DatabaseTab
    tables_tab: TablesTab
    columns_tab: ColumnsTab
    indexes_tab: IndexesTab
    
    @classmethod
    def set_test_mode(cls, enabled=True):
        """Set test mode to prevent UI operations during tests"""
        cls._test_mode = enabled
    
    def __init__(self, connection, parent=None, debug_mode=False):
        super().__init__(parent)
        
        self.connection = connection
        self._debug_mode = debug_mode  # Add debug mode flag
        self.setWindowTitle("Database Manager")
        self.resize(800, 600)
        
        self._create_ui()
        self._populate_data()
        self._connect_signals()
        
        # Don't show the dialog in test mode
        if self._test_mode:
            self.setVisible(False)
    
    def _create_ui(self):
        """Create the UI components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs for different management functions
        self.database_tab = self._create_database_tab()
        self.tables_tab = self._create_tables_tab()
        self.columns_tab = self._create_columns_tab()
        self.indexes_tab = self._create_indexes_tab()
        
        # Add tabs to the tab widget
        self.tabs.addTab(self.database_tab, "Databases")
        self.tabs.addTab(self.tables_tab, "Tables")
        self.tabs.addTab(self.columns_tab, "Columns")
        self.tabs.addTab(self.indexes_tab, "Indexes")
        
        layout.addWidget(self.tabs)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_database_tab(self):
        """Create the database management tab"""
        tab = DatabaseTab()
        layout = QVBoxLayout(tab)
        
        # Database list
        layout.addWidget(QLabel("Available Databases:"))
        databases_list = QListWidget()
        layout.addWidget(databases_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        create_db_button = QPushButton("Create Database")
        drop_db_button = QPushButton("Drop Database")
        
        # Only show buttons if user has permissions
        create_db_button.setVisible(self.connection.can_create_database())
        drop_db_button.setVisible(self.connection.can_drop_database())
        
        buttons_layout.addWidget(create_db_button)
        buttons_layout.addWidget(drop_db_button)
        layout.addLayout(buttons_layout)
        
        # Store references to the widgets
        tab.databases_list = databases_list
        tab.create_db_button = create_db_button
        tab.drop_db_button = drop_db_button
        
        return tab
    
    def _create_tables_tab(self):
        """Create the tables management tab"""
        tab = TablesTab()
        layout = QVBoxLayout(tab)
        
        # Database selector
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Database:"))
        db_selector = QComboBox()
        db_layout.addWidget(db_selector)
        layout.addLayout(db_layout)
        
        # Tables list
        layout.addWidget(QLabel("Tables:"))
        tables_list = QListWidget()
        layout.addWidget(tables_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        create_table_button = QPushButton("Create Table")
        drop_table_button = QPushButton("Drop Table")
        buttons_layout.addWidget(create_table_button)
        buttons_layout.addWidget(drop_table_button)
        layout.addLayout(buttons_layout)
        
        # Store references to the widgets
        tab.db_selector = db_selector
        tab.tables_list = tables_list
        tab.create_table_button = create_table_button
        tab.drop_table_button = drop_table_button
        
        return tab
    
    def _create_columns_tab(self):
        """Create the columns management tab"""
        tab = ColumnsTab()
        layout = QVBoxLayout(tab)
        
        # Table selector
        table_layout = QHBoxLayout()
        table_layout.addWidget(QLabel("Table:"))
        table_selector = QComboBox()
        table_layout.addWidget(table_selector)
        layout.addLayout(table_layout)
        
        # Columns list
        layout.addWidget(QLabel("Columns:"))
        columns_list = QListWidget()
        layout.addWidget(columns_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        add_column_button = QPushButton("Add Column")
        modify_column_button = QPushButton("Modify Column")
        drop_column_button = QPushButton("Drop Column")
        buttons_layout.addWidget(add_column_button)
        buttons_layout.addWidget(modify_column_button)
        buttons_layout.addWidget(drop_column_button)
        layout.addLayout(buttons_layout)
        
        # Store references to the widgets
        tab.table_selector = table_selector
        tab.columns_list = columns_list
        tab.add_column_button = add_column_button
        tab.modify_column_button = modify_column_button
        tab.drop_column_button = drop_column_button
        
        return tab
    
    def _create_indexes_tab(self):
        """Create the indexes management tab"""
        tab = IndexesTab()
        layout = QVBoxLayout(tab)
        
        # Table selector
        table_layout = QHBoxLayout()
        table_layout.addWidget(QLabel("Table:"))
        table_selector = QComboBox()
        table_layout.addWidget(table_selector)
        layout.addLayout(table_layout)
        
        # Indexes list
        layout.addWidget(QLabel("Indexes:"))
        indexes_list = QListWidget()
        layout.addWidget(indexes_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        create_index_button = QPushButton("Create Index")
        drop_index_button = QPushButton("Drop Index")
        buttons_layout.addWidget(create_index_button)
        buttons_layout.addWidget(drop_index_button)
        layout.addLayout(buttons_layout)
        
        # Store references to the widgets
        tab.table_selector = table_selector
        tab.indexes_list = indexes_list
        tab.create_index_button = create_index_button
        tab.drop_index_button = drop_index_button
        
        return tab
    
    def _populate_data(self):
        """Populate the UI with data from the database"""
        # Populate databases list
        self._populate_databases()
        
        # Populate database selector in tables tab
        self._populate_db_selector()
        
        # Initially disable tables, columns, and indexes tabs until selections are made
        self._update_tab_states()
        
        # If a database is already selected, populate tables and select the first table
        current_db = self.connection.get_database_name()
        if current_db != "(No database selected)":
            # Make sure tables are populated
            self._populate_tables(current_db)
            
            # If there are tables, select the first one and populate its columns
            if self.tables_tab.tables_list.count() > 0:
                # Select the first table
                self.tables_tab.tables_list.setCurrentRow(0)
                first_item = self.tables_tab.tables_list.item(0)
                if first_item is not None:
                    selected_table = first_item.text()
                    
                    # Update the table selectors in columns and indexes tabs
                    index = self.columns_tab.table_selector.findText(selected_table)
                    if index >= 0:
                        self.columns_tab.table_selector.setCurrentIndex(index)
                    
                    index = self.indexes_tab.table_selector.findText(selected_table)
                    if index >= 0:
                        self.indexes_tab.table_selector.setCurrentIndex(index)
                    
                    # Explicitly populate columns and indexes for the selected table
                    self._populate_columns(selected_table)
                    self._populate_indexes(selected_table)
            
            # Switch to the Tables tab
            self.tabs.setCurrentIndex(1)  # Index 1 is the tables tab
    
    def _populate_databases(self):
        """Populate the databases list"""
        self.database_tab.databases_list.clear()
        
        try:
            databases = self.connection.get_available_databases()
            for db in databases:
                self.database_tab.databases_list.addItem(db)
                
            # Select the current database in the list if one is selected
            current_db = self.connection.get_database_name()
            if current_db != "(No database selected)":
                items = self.database_tab.databases_list.findItems(current_db, Qt.MatchFlag.MatchExactly)
                if items:
                    self.database_tab.databases_list.setCurrentItem(items[0])
        except Exception as e:
            if not self._test_mode:
                QMessageBox.warning(self, "Error", f"Failed to retrieve databases: {str(e)}")
    
    def _populate_db_selector(self):
        """Populate the database selector in the tables tab"""
        self.tables_tab.db_selector.clear()
        
        try:
            databases = self.connection.get_available_databases()
            self.tables_tab.db_selector.addItems(databases)
            
            # Set the current database if one is selected
            current_db = self.connection.get_database_name()
            if current_db != "(No database selected)":
                index = self.tables_tab.db_selector.findText(current_db)
                if index >= 0:
                    # Temporarily disconnect the signal to avoid triggering _on_tables_db_changed
                    self.tables_tab.db_selector.blockSignals(True)
                    self.tables_tab.db_selector.setCurrentIndex(index)
                    self.tables_tab.db_selector.blockSignals(False)
                    
                    # Manually populate the tables for the selected database
                    self._populate_tables(current_db)
                    self._populate_table_selectors(current_db)
        except Exception as e:
            if not self._test_mode:
                QMessageBox.warning(self, "Error", f"Failed to retrieve databases: {str(e)}")
    
    def _populate_tables(self, database_name=None):
        """Populate the tables list for the selected database"""
        self.tables_tab.tables_list.clear()
        
        if not database_name:
            return
        
        try:
            # Save current database
            current_db = self.connection.get_database_name()
            
            # Switch to the selected database temporarily
            if current_db != database_name:
                self.connection.use_database(database_name)
            
            # Get tables
            tables = self.connection.get_tables()
            
            for table in tables:
                self.tables_tab.tables_list.addItem(table)
            
            # Switch back to the original database if needed
            if current_db != database_name and current_db != "(No database selected)":
                self.connection.use_database(current_db)
        except Exception as e:
            if not self._test_mode:
                QMessageBox.warning(self, "Error", f"Failed to retrieve tables: {str(e)}")
    
    def _populate_table_selectors(self, database_name=None):
        """Populate the table selectors in columns and indexes tabs"""
        # Block signals to prevent triggering _populate_columns with empty table names
        self.columns_tab.table_selector.blockSignals(True)
        self.indexes_tab.table_selector.blockSignals(True)
        
        # Clear the selectors
        self.columns_tab.table_selector.clear()
        self.indexes_tab.table_selector.clear()
        
        if not database_name:
            # Unblock signals before returning
            self.columns_tab.table_selector.blockSignals(False)
            self.indexes_tab.table_selector.blockSignals(False)
            return
        
        try:
            # Save current database
            current_db = self.connection.get_database_name()
            
            # Switch to the selected database temporarily
            if current_db != database_name:
                self.connection.use_database(database_name)
            
            # Get tables
            tables = self.connection.get_tables()
            for table in tables:
                self.columns_tab.table_selector.addItem(table)
                self.indexes_tab.table_selector.addItem(table)
            
            # Switch back to the original database if needed
            if current_db != database_name and current_db != "(No database selected)":
                self.connection.use_database(current_db)
                
            # Unblock signals after populating
            self.columns_tab.table_selector.blockSignals(False)
            self.indexes_tab.table_selector.blockSignals(False)
            
            # If we have tables, select the first one
            if tables:
                self.columns_tab.table_selector.setCurrentIndex(0)
                self.indexes_tab.table_selector.setCurrentIndex(0)
        except Exception as e:
            # Unblock signals even if there's an error
            self.columns_tab.table_selector.blockSignals(False)
            self.indexes_tab.table_selector.blockSignals(False)
            
            if not self._test_mode:
                QMessageBox.warning(self, "Error", f"Failed to retrieve tables: {str(e)}")
    
    def _update_tab_states(self):
        """Update the enabled state of tabs based on selections"""
        # Check if a database is selected in the database tab
        selected_db = None
        selected_items = self.database_tab.databases_list.selectedItems()
        if selected_items:
            selected_db = selected_items[0].text()
        
        # Also check if a database is selected in the tables tab dropdown
        current_db = self.tables_tab.db_selector.currentText()
        has_db_selected = current_db != ""
        
        # Check if the selected database is a system database
        is_system_db = False
        if has_db_selected:
            is_system_db = self.connection.is_system_database(current_db)
        
        # Check if a table is selected in the tables tab
        selected_table = None
        selected_items = self.tables_tab.tables_list.selectedItems()
        if selected_items:
            selected_table = selected_items[0].text()
        
        # Update tables tab buttons based on permissions
        # Disable operations on system databases
        can_create_tables = has_db_selected and not is_system_db
        can_drop_tables = has_db_selected and selected_table is not None and not is_system_db
        
        # Only enable buttons if user has appropriate permissions
        self.tables_tab.create_table_button.setEnabled(can_create_tables)
        self.tables_tab.drop_table_button.setEnabled(can_drop_tables)
        
        # If we have a database selected but no tables showing, refresh the tables list
        if has_db_selected and self.tables_tab.tables_list.count() == 0:
            db_name = self.tables_tab.db_selector.currentText()
            self._populate_tables(db_name)
        
        # Update columns tab
        has_table_selected_for_columns = self.columns_tab.table_selector.currentText() != ""
        has_column_selected = len(self.columns_tab.columns_list.selectedItems()) > 0
        
        # Only enable buttons if user has appropriate permissions and not a system database
        can_alter_table = has_table_selected_for_columns and not is_system_db
        can_alter_column = has_table_selected_for_columns and has_column_selected and not is_system_db
        
        self.columns_tab.add_column_button.setEnabled(can_alter_table)
        self.columns_tab.modify_column_button.setEnabled(can_alter_column)
        self.columns_tab.drop_column_button.setEnabled(can_alter_column)
        
        # Update indexes tab
        has_table_selected_for_indexes = self.indexes_tab.table_selector.currentText() != ""
        has_index_selected = len(self.indexes_tab.indexes_list.selectedItems()) > 0
        
        # Only enable buttons if user has appropriate permissions and not a system database
        can_create_index = has_table_selected_for_indexes and not is_system_db
        can_drop_index = has_table_selected_for_indexes and has_index_selected and not is_system_db
        
        self.indexes_tab.create_index_button.setEnabled(can_create_index)
        self.indexes_tab.drop_index_button.setEnabled(can_drop_index)
        
        # If this is a system database, show a warning label
        if is_system_db:
            # Check if we already have a warning label
            if not hasattr(self, 'system_db_warning_shown') or not self.system_db_warning_shown:
                QMessageBox.information(
                    self, 
                    "System Database", 
                    f"'{current_db}' is a system database. Modifications are disabled to prevent system damage."
                )
                self.system_db_warning_shown = True
        else:
            # Reset the warning flag when switching to a non-system database
            self.system_db_warning_shown = False
    
    def _populate_columns(self, table_name):
        """Populate the columns list for the selected table"""
        self.columns_tab.columns_list.clear()
        
        # Skip if table name is empty
        if not table_name:
            return
            
        try:
            # Get the current database from the tables tab
            database_name = self.tables_tab.db_selector.currentText()
            if not database_name:
                return
                
            # Save current database
            current_db = self.connection.get_database_name()
            
            # Try to get columns without switching databases first
            try:
                # Get columns using current connection
                columns = self.connection.get_columns(table_name)
                for column in columns:
                    # Format the column type display to clearly show size/precision
                    column_type = str(column['type'])
                    self.columns_tab.columns_list.addItem(f"{column['name']} ({column_type})")
                return
            except Exception as first_error:
                # If that fails, try the original approach with database switching
                # Only log detailed errors in debug mode
                if hasattr(self, '_debug_mode') and self._debug_mode:
                    print(f"First attempt to get columns failed for table '{table_name}': {first_error}")
                
                # Only try to switch database if we're not already in the right one
                if current_db != database_name:
                    try:
                        self.connection.use_database(database_name)
                        
                        # Get columns
                        columns = self.connection.get_columns(table_name)
                        for column in columns:
                            # Format the column type display to clearly show size/precision
                            column_type = str(column['type'])
                            self.columns_tab.columns_list.addItem(f"{column['name']} ({column_type})")
                            
                        # Switch back to the original database if needed
                        if current_db != "(No database selected)":
                            self.connection.use_database(current_db)
                    except Exception as e:
                        # If switching databases fails, show the error
                        if not self._test_mode:
                            QMessageBox.warning(self, "Error", f"Failed to retrieve columns for table '{table_name}': {str(e)}")
                else:
                    # We're already in the right database but still failed
                    if not self._test_mode:
                        QMessageBox.warning(self, "Error", f"Failed to retrieve columns for table '{table_name}': {str(first_error)}")
        except Exception as e:
            if not self._test_mode:
                QMessageBox.warning(self, "Error", f"Failed to retrieve columns for table '{table_name}': {str(e)}")
    
    def _populate_indexes(self, table_name):
        """Populate the indexes list for the selected table"""
        self.indexes_tab.indexes_list.clear()
        
        # Skip if table name is empty
        if not table_name:
            return
            
        try:
            # Get the current database from the tables tab
            database_name = self.tables_tab.db_selector.currentText()
            if not database_name:
                return
                
            # Save current database
            current_db = self.connection.get_database_name()
            
            # Try to get indexes without switching databases first
            try:
                # Get indexes using current connection
                indexes = self.connection.get_indexes(table_name)
                for index in indexes:
                    self.indexes_tab.indexes_list.addItem(index['name'])
                return
            except Exception as first_error:
                # If that fails, try the original approach with database switching
                # Only log detailed errors in debug mode
                if hasattr(self, '_debug_mode') and self._debug_mode:
                    print(f"First attempt to get indexes failed for table '{table_name}': {first_error}")
                
                # Only try to switch database if we're not already in the right one
                if current_db != database_name:
                    try:
                        self.connection.use_database(database_name)
                        
                        # Get indexes
                        indexes = self.connection.get_indexes(table_name)
                        for index in indexes:
                            self.indexes_tab.indexes_list.addItem(index['name'])
                            
                        # Switch back to the original database if needed
                        if current_db != "(No database selected)":
                            self.connection.use_database(current_db)
                    except Exception as e:
                        # If switching databases fails, show the error
                        if not self._test_mode:
                            QMessageBox.warning(self, "Error", f"Failed to retrieve indexes for table '{table_name}': {str(e)}")
                else:
                    # We're already in the right database but still failed
                    if not self._test_mode:
                        QMessageBox.warning(self, "Error", f"Failed to retrieve indexes for table '{table_name}': {str(first_error)}")
        except Exception as e:
            if not self._test_mode:
                QMessageBox.warning(self, "Error", f"Failed to retrieve indexes for table '{table_name}': {str(e)}")
    
    def _connect_signals(self):
        """Connect signals to slots"""
        # Database tab
        self.database_tab.create_db_button.clicked.connect(self._create_database)
        self.database_tab.drop_db_button.clicked.connect(self._drop_database)
        self.database_tab.databases_list.itemSelectionChanged.connect(self._on_database_selection_changed)
        self.database_tab.databases_list.itemDoubleClicked.connect(self._on_database_double_clicked)
        
        # Tables tab
        self.tables_tab.db_selector.currentTextChanged.connect(self._on_tables_db_changed)
        self.tables_tab.create_table_button.clicked.connect(self._create_table)
        self.tables_tab.drop_table_button.clicked.connect(self._drop_table)
        self.tables_tab.tables_list.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.tables_tab.tables_list.itemDoubleClicked.connect(self._on_table_double_clicked)
        
        # Columns tab
        self.columns_tab.table_selector.currentTextChanged.connect(self._populate_columns)
        self.columns_tab.add_column_button.clicked.connect(self._add_column)
        self.columns_tab.modify_column_button.clicked.connect(self._modify_column)
        self.columns_tab.drop_column_button.clicked.connect(self._drop_column)
        
        # Indexes tab
        self.indexes_tab.table_selector.currentTextChanged.connect(self._populate_indexes)
        self.indexes_tab.create_index_button.clicked.connect(self._create_index)
        self.indexes_tab.drop_index_button.clicked.connect(self._drop_index)
        
        # Tab widget
        self.tabs.currentChanged.connect(self._on_tab_changed)
    
    def _create_database(self):
        """Create a new database"""
        # Check if user has permission to create databases
        if not self.connection.can_create_database():
            if not self._test_mode:
                QMessageBox.warning(self, "Permission Denied", "You do not have permission to create databases.")
            return
            
        if self._test_mode:
            # In test mode, use a predefined value
            db_name, ok = "new_database", True
        else:
            db_name, ok = QInputDialog.getText(self, "Create Database", "Database name:")
            
        if ok and db_name:
            try:
                # Execute the CREATE DATABASE statement
                self.connection.execute_non_query(f"CREATE DATABASE {db_name};")
                
                # Refresh the databases list
                self._populate_databases()
                
                if not self._test_mode:
                    QMessageBox.information(self, "Success", f"Database '{db_name}' created successfully.")
            except Exception as e:
                if not self._test_mode:
                    QMessageBox.critical(self, "Error", f"Failed to create database: {str(e)}")
    
    def _drop_database(self):
        """Drop the selected database"""
        # Check if user has permission to drop databases
        if not self.connection.can_drop_database():
            if not self._test_mode:
                QMessageBox.warning(self, "Permission Denied", "You do not have permission to drop databases.")
            return
            
        # Get the selected database
        selected_items = self.database_tab.databases_list.selectedItems()
        if not selected_items:
            if not self._test_mode:
                QMessageBox.warning(self, "Warning", "Please select a database to drop.")
            return
        
        db_name = selected_items[0].text()
        
        # Check if this is a system database
        if self.connection.is_system_database(db_name):
            if not self._test_mode:
                QMessageBox.warning(
                    self, 
                    "System Database", 
                    f"'{db_name}' is a system database. Dropping system databases is not allowed to prevent system damage."
                )
            return
        
        # Confirm the drop operation
        if self._test_mode:
            reply = QMessageBox.StandardButton.Yes
        else:
            reply = QMessageBox.question(
                self, "Confirm Drop",
                f"Are you sure you want to drop the database '{db_name}'?\nThis action cannot be undone!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Execute the DROP DATABASE statement
                self.connection.execute_non_query(f"DROP DATABASE {db_name};")
                
                # Refresh the databases list
                self._populate_databases()
                
                if not self._test_mode:
                    QMessageBox.information(self, "Success", f"Database '{db_name}' dropped successfully.")
            except Exception as e:
                if not self._test_mode:
                    QMessageBox.critical(self, "Error", f"Failed to drop database: {str(e)}")
    
    def _create_table(self):
        """Create a new table"""
        # Get the selected database from the tables tab
        database_name = self.tables_tab.db_selector.currentText()
        if not database_name:
            QMessageBox.warning(self, "Warning", "Please select a database first.")
            return
            
        # Check if this is a system database
        if self.connection.is_system_database(database_name):
            QMessageBox.warning(
                self, 
                "System Database", 
                f"'{database_name}' is a system database. Creating tables is not allowed to prevent system damage."
            )
            return
        
        dialog = CreateTableDialog(self)
        
        # In test mode, we'll simulate the dialog result
        if self._test_mode:
            # Create a mock table definition
            table_def = {
                'name': 'test_table',
                'columns': [
                    {'name': 'id', 'type': 'INTEGER', 'primary_key': True, 'nullable': False},
                    {'name': 'name', 'type': 'TEXT', 'primary_key': False, 'nullable': True}
                ]
            }
            
            # Build the CREATE TABLE statement
            sql = f"CREATE TABLE {table_def['name']} (\n"
            
            # Add column definitions
            column_defs = []
            for col in table_def['columns']:
                # Handle types that require length/precision
                col_type = col['type']
                if col_type == 'VARCHAR' and '(' not in col_type:
                    col_type = 'VARCHAR(255)'  # Default to 255 if no length specified
                elif col_type == 'DOUBLE' and '(' not in col_type:
                    col_type = 'DOUBLE(10,2)'  # Default precision for DOUBLE
                elif col_type == 'DECIMAL' and '(' not in col_type:
                    col_type = 'DECIMAL(10,2)'  # Default precision for DECIMAL
                
                col_def = f"{col['name']} {col_type}"
                
                if not col['nullable']:
                    col_def += " NOT NULL"
                
                if col['primary_key']:
                    col_def += " PRIMARY KEY"
                
                column_defs.append(col_def)
            
            sql += ",\n".join(column_defs)
            sql += "\n);"
            
            # Save current database
            current_db = self.connection.get_database_name()
            
            # Switch to the selected database temporarily
            if current_db != database_name:
                self.connection.use_database(database_name)
            
            # Execute the CREATE TABLE statement
            self.connection.execute_non_query(sql)
            
            # Ensure the database selector shows the correct database
            index = self.tables_tab.db_selector.findText(database_name)
            if index >= 0:
                self.tables_tab.db_selector.setCurrentIndex(index)
            
            # Refresh the tables list
            self._populate_tables(database_name)
            self._populate_table_selectors(database_name)
            
            # Switch back to the original database if needed
            if current_db != database_name and current_db != "(No database selected)":
                self.connection.use_database(current_db)
                
            # Force the UI to update
            self.tables_tab.tables_list.update()
            
            return
        
        # Normal mode - show the dialog
        if dialog.exec():
            try:
                # Get the table definition
                table_def = dialog.get_table_definition()
                
                # Build the CREATE TABLE statement
                sql = f"CREATE TABLE {table_def['name']} (\n"
                
                # Add column definitions
                column_defs = []
                for col in table_def['columns']:
                    # Handle types that require length/precision
                    col_type = col['type']
                    if col_type == 'VARCHAR' and '(' not in col_type:
                        col_type = 'VARCHAR(255)'  # Default to 255 if no length specified
                    elif col_type == 'DOUBLE' and '(' not in col_type:
                        col_type = 'DOUBLE(10,2)'  # Default precision for DOUBLE
                    elif col_type == 'DECIMAL' and '(' not in col_type:
                        col_type = 'DECIMAL(10,2)'  # Default precision for DECIMAL
                    
                    col_def = f"{col['name']} {col_type}"
                    
                    if not col['nullable']:
                        col_def += " NOT NULL"
                    
                    if col['primary_key']:
                        col_def += " PRIMARY KEY"
                    
                    column_defs.append(col_def)
                
                sql += ",\n".join(column_defs)
                sql += "\n);"
                
                # Save current database
                current_db = self.connection.get_database_name()
                
                # Switch to the selected database temporarily
                if current_db != database_name:
                    self.connection.use_database(database_name)
                
                # Execute the CREATE TABLE statement
                self.connection.execute_non_query(sql)
                
                # Ensure the database selector shows the correct database
                index = self.tables_tab.db_selector.findText(database_name)
                if index >= 0:
                    self.tables_tab.db_selector.setCurrentIndex(index)
                
                # Refresh the tables list
                self._populate_tables(database_name)
                self._populate_table_selectors(database_name)
                
                # Switch back to the original database if needed
                if current_db != database_name and current_db != "(No database selected)":
                    self.connection.use_database(current_db)
                
                # Force the UI to update
                self.tables_tab.tables_list.update()
                
                QMessageBox.information(self, "Success", f"Table '{table_def['name']}' created successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create table: {str(e)}")
    
    def _drop_table(self):
        """Drop the selected table"""
        # Get the selected database and table
        database_name = self.tables_tab.db_selector.currentText()
        if not database_name:
            QMessageBox.warning(self, "Warning", "Please select a database first.")
            return
            
        # Check if this is a system database
        if self.connection.is_system_database(database_name):
            QMessageBox.warning(
                self, 
                "System Database", 
                f"'{database_name}' is a system database. Dropping tables is not allowed to prevent system damage."
            )
            return
            
        selected_items = self.tables_tab.tables_list.selectedItems()
        if not selected_items:
            if not self._test_mode:
                QMessageBox.warning(self, "Warning", "Please select a table to drop.")
            return
        
        table_name = selected_items[0].text()
        
        # Confirm the drop operation
        if self._test_mode:
            reply = QMessageBox.StandardButton.Yes
        else:
            reply = QMessageBox.question(
                self, "Confirm Drop",
                f"Are you sure you want to drop the table '{table_name}'?\nThis action cannot be undone!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Save current database
                current_db = self.connection.get_database_name()
                
                # Switch to the selected database temporarily
                if current_db != database_name:
                    self.connection.use_database(database_name)
                
                # Execute the DROP TABLE statement
                self.connection.execute_non_query(f"DROP TABLE {table_name};")
                
                # Refresh the tables list
                self._populate_tables(database_name)
                self._populate_table_selectors(database_name)
                
                # Switch back to the original database if needed
                if current_db != database_name and current_db != "(No database selected)":
                    self.connection.use_database(current_db)
                
                if not self._test_mode:
                    QMessageBox.information(self, "Success", f"Table '{table_name}' dropped successfully.")
            except Exception as e:
                if not self._test_mode:
                    QMessageBox.critical(self, "Error", f"Failed to drop table: {str(e)}")
    
    def _add_column(self):
        """Add a column to the selected table"""
        # Get the selected table
        table_name = self.columns_tab.table_selector.currentText()
        if not table_name:
            QMessageBox.warning(self, "Warning", "Please select a table.")
            return
            
        # Get the current database
        database_name = self.tables_tab.db_selector.currentText()
        
        # Check if this is a system database
        if self.connection.is_system_database(database_name):
            QMessageBox.warning(
                self, 
                "System Database", 
                f"'{database_name}' is a system database. Adding columns is not allowed to prevent system damage."
            )
            return
        
        # Show the add column dialog
        dialog = AddColumnDialog(self)
        if dialog.exec():
            try:
                # Get the column definition
                column_def = dialog.get_column_definition()
                
                # Build the ALTER TABLE statement
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_def['name']} {column_def['type']}"
                
                if not column_def['nullable']:
                    sql += " NOT NULL"
                
                if column_def['default'] is not None:
                    # For numeric types, ensure the default value is properly formatted
                    default_value = column_def['default']
                    
                    # Check if it's a numeric type with a numeric default value
                    numeric_types = ["INT", "INTEGER", "SMALLINT", "TINYINT", "BIGINT", 
                                    "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL"]
                    
                    is_numeric_type = any(column_def['type'].upper().startswith(t) for t in numeric_types)
                    
                    # If it's a numeric type and the default isn't already quoted, don't add quotes
                    if is_numeric_type and not (default_value.startswith("'") and default_value.endswith("'")):
                        sql += f" DEFAULT {default_value}"
                    else:
                        # For other types or already quoted values, use as is
                        sql += f" DEFAULT {default_value}"
                
                sql += ";"
                
                # Get the current database from the tables tab
                database_name = self.tables_tab.db_selector.currentText()
                if not database_name:
                    QMessageBox.warning(self, "Warning", "No database selected.")
                    return
                
                # Save current database
                current_db = self.connection.get_database_name()
                
                try:
                    # Switch to the selected database temporarily if needed
                    if current_db != database_name:
                        self.connection.use_database(database_name)
                    
                    # Execute the ALTER TABLE statement
                    self.connection.execute_non_query(sql)
                    
                    # Refresh the columns list
                    self._populate_columns(table_name)
                finally:
                    # Switch back to the original database if needed
                    if current_db != database_name and current_db != "(No database selected)":
                        self.connection.use_database(current_db)
                
                QMessageBox.information(self, "Success", f"Column '{column_def['name']}' added successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add column: {str(e)}")
    
    def _modify_column(self):
        """Modify the selected column"""
        # Get the selected table and column
        table_name = self.columns_tab.table_selector.currentText()
        selected_items = self.columns_tab.columns_list.selectedItems()
        
        if not table_name:
            QMessageBox.warning(self, "Warning", "Please select a table.")
            return
        
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a column to modify.")
            return
            
        # Get the current database
        database_name = self.tables_tab.db_selector.currentText()
        
        # Check if this is a system database
        if self.connection.is_system_database(database_name):
            QMessageBox.warning(
                self, 
                "System Database", 
                f"'{database_name}' is a system database. Modifying columns is not allowed to prevent system damage."
            )
            return
        
        # Extract the column name from the list item text (format: "name (type)")
        column_text = selected_items[0].text()
        column_name = column_text.split(" (")[0]
        
        # Get the current column definition
        columns = self.connection.get_columns(table_name)
        current_column = next((col for col in columns if col['name'] == column_name), None)
        
        if not current_column:
            QMessageBox.warning(self, "Warning", f"Column '{column_name}' not found.")
            return
        
        # Show the modify column dialog
        dialog = AddColumnDialog(self)
        dialog.setWindowTitle("Modify Column")
        dialog.column_name_edit.setText(current_column['name'])
        
        # Parse the column type to extract size and precision if present
        column_type_str = str(current_column['type'])
        base_type = column_type_str
        size = ""
        precision = ""
        
        # Check if the type has size/precision specifications
        if "(" in column_type_str and ")" in column_type_str:
            base_type = column_type_str.split("(")[0]
            size_part = column_type_str.split("(")[1].split(")")[0]
            
            if "," in size_part:
                # Handle types with both size and precision (e.g., DECIMAL(10,2))
                size, precision = size_part.split(",")
            else:
                # Handle types with just size (e.g., VARCHAR(255))
                size = size_part
        
        # Set the base type in the combo box
        dialog.column_type_combo.setCurrentText(base_type)
        
        # Set size and precision if they exist
        if size:
            dialog.size_edit.setText(size)
        if precision:
            dialog.precision_edit.setText(precision)
        
        if dialog.exec():
            try:
                # Get the new column definition
                new_column_def = dialog.get_column_definition()
                
                # Build the ALTER TABLE statement
                # Note: The exact syntax varies by database type
                db_type = self.connection.params['type']
                
                if db_type == 'SQLite':
                    # SQLite doesn't support ALTER COLUMN directly, need to use a workaround
                    QMessageBox.warning(
                        self, "Not Supported",
                        "Modifying columns is not directly supported in SQLite. "
                        "You would need to create a new table with the desired schema, "
                        "copy the data, and rename the tables."
                    )
                    return
                elif db_type == 'MySQL':
                    sql = f"ALTER TABLE {table_name} MODIFY COLUMN {new_column_def['name']} {new_column_def['type']}"
                elif db_type == 'PostgreSQL':
                    # For PostgreSQL, we need separate statements for different modifications
                    if new_column_def['name'] != current_column['name']:
                        sql = f"ALTER TABLE {table_name} RENAME COLUMN {current_column['name']} TO {new_column_def['name']};"
                        self.connection.execute_non_query(sql)
                    
                    sql = f"ALTER TABLE {table_name} ALTER COLUMN {new_column_def['name']} TYPE {new_column_def['type']}"
                else:
                    QMessageBox.warning(self, "Not Supported", f"Modifying columns is not supported for {db_type}.")
                    return
                
                if not new_column_def['nullable']:
                    sql += " NOT NULL"
                
                if new_column_def['default'] is not None:
                    # Get the default value
                    default_value = new_column_def['default']
                    
                    # Check if it's a numeric type with a numeric default value
                    numeric_types = ["INT", "INTEGER", "SMALLINT", "TINYINT", "BIGINT", 
                                    "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL"]
                    
                    is_numeric_type = any(new_column_def['type'].upper().startswith(t) for t in numeric_types)
                    
                    if db_type == 'PostgreSQL':
                        # For PostgreSQL, default is a separate statement
                        sql += ";"
                        sql += f"ALTER TABLE {table_name} ALTER COLUMN {new_column_def['name']} SET DEFAULT {default_value}"
                    else:
                        # For other database types
                        sql += f" DEFAULT {default_value}"
                
                sql += ";"
                
                # Get the current database from the tables tab
                database_name = self.tables_tab.db_selector.currentText()
                if not database_name:
                    QMessageBox.warning(self, "Warning", "No database selected.")
                    return
                
                # Save current database
                current_db = self.connection.get_database_name()
                
                try:
                    # Switch to the selected database temporarily if needed
                    if current_db != database_name:
                        self.connection.use_database(database_name)
                    
                    # Execute the ALTER TABLE statement
                    self.connection.execute_non_query(sql)
                    
                    # Refresh the columns list
                    self._populate_columns(table_name)
                finally:
                    # Switch back to the original database if needed
                    if current_db != database_name and current_db != "(No database selected)":
                        self.connection.use_database(current_db)
                
                QMessageBox.information(self, "Success", f"Column '{new_column_def['name']}' modified successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to modify column: {str(e)}")
    
    def _drop_column(self):
        """Drop the selected column"""
        # Get the selected table and column
        table_name = self.columns_tab.table_selector.currentText()
        selected_items = self.columns_tab.columns_list.selectedItems()
        
        if not table_name:
            QMessageBox.warning(self, "Warning", "Please select a table.")
            return
        
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a column to drop.")
            return
            
        # Get the current database
        database_name = self.tables_tab.db_selector.currentText()
        
        # Check if this is a system database
        if self.connection.is_system_database(database_name):
            QMessageBox.warning(
                self, 
                "System Database", 
                f"'{database_name}' is a system database. Dropping columns is not allowed to prevent system damage."
            )
            return
        
        # Extract the column name from the list item text (format: "name (type)")
        column_text = selected_items[0].text()
        column_name = column_text.split(" (")[0]
        
        # Confirm the drop operation
        reply = QMessageBox.question(
            self, "Confirm Drop",
            f"Are you sure you want to drop the column '{column_name}' from table '{table_name}'?\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Check if the database type supports dropping columns
                db_type = self.connection.params['type']
                
                if db_type == 'SQLite':
                    # SQLite doesn't support DROP COLUMN directly in older versions
                    sqlite_version = self.connection.execute_query("SELECT sqlite_version();").iloc[0, 0]
                    if sqlite_version < "3.35.0":
                        QMessageBox.warning(
                            self, "Not Supported",
                            f"Dropping columns is not supported in SQLite version {sqlite_version}. "
                            "You would need to create a new table without the column, "
                            "copy the data, and rename the tables."
                        )
                        return
                
                # Get the current database from the tables tab
                database_name = self.tables_tab.db_selector.currentText()
                if not database_name:
                    QMessageBox.warning(self, "Warning", "No database selected.")
                    return
                
                # Save current database
                current_db = self.connection.get_database_name()
                
                try:
                    # Switch to the selected database temporarily if needed
                    if current_db != database_name:
                        self.connection.use_database(database_name)
                    
                    # Execute the ALTER TABLE statement
                    self.connection.execute_non_query(f"ALTER TABLE {table_name} DROP COLUMN {column_name};")
                    
                    # Refresh the columns list
                    self._populate_columns(table_name)
                finally:
                    # Switch back to the original database if needed
                    if current_db != database_name and current_db != "(No database selected)":
                        self.connection.use_database(current_db)
                
                QMessageBox.information(self, "Success", f"Column '{column_name}' dropped successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to drop column: {str(e)}")
    
    def _create_index(self):
        """Create a new index"""
        # Get the selected table
        table_name = self.indexes_tab.table_selector.currentText()
        if not table_name:
            QMessageBox.warning(self, "Warning", "Please select a table.")
            return
            
        # Get the current database from the tables tab
        database_name = self.tables_tab.db_selector.currentText()
        if not database_name:
            QMessageBox.warning(self, "Warning", "No database selected.")
            return
            
        # Check if this is a system database
        if self.connection.is_system_database(database_name):
            QMessageBox.warning(
                self, 
                "System Database", 
                f"'{database_name}' is a system database. Creating indexes is not allowed to prevent system damage."
            )
            return
            
        # Save current database
        current_db = self.connection.get_database_name()
        
        try:
            # Switch to the selected database temporarily if needed
            if current_db != database_name:
                self.connection.use_database(database_name)
            
            # Show the create index dialog
            dialog = CreateIndexDialog(self.connection, self)
            
            # Set the selected table
            dialog.table_combo.setCurrentText(table_name)
            
            # Store the database name and current_db for later use
            dialog.database_name = database_name
            dialog.original_db = current_db
            
            if dialog.exec():
                try:
                    # Get the index definition
                    index_def = dialog.get_index_definition()
                    
                    # Build the CREATE INDEX statement
                    if index_def['unique']:
                        sql = f"CREATE UNIQUE INDEX {index_def['name']} ON {index_def['table']} "
                    else:
                        sql = f"CREATE INDEX {index_def['name']} ON {index_def['table']} "
                    
                    sql += f"({', '.join(index_def['columns'])});"
                    
                    # Execute the CREATE INDEX statement
                    self.connection.execute_non_query(sql)
                    
                    # Refresh the indexes list
                    self._populate_indexes(table_name)
                    
                    QMessageBox.information(self, "Success", f"Index '{index_def['name']}' created successfully.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create index: {str(e)}")
        finally:
            # Switch back to the original database if needed
            if current_db != database_name and current_db != "(No database selected)":
                self.connection.use_database(current_db)
    
    def _on_database_selection_changed(self):
        """Handle database selection change in the database tab"""
        selected_items = self.database_tab.databases_list.selectedItems()
        if selected_items:
            selected_db = selected_items[0].text()
            
            # Update the database selector in the tables tab
            index = self.tables_tab.db_selector.findText(selected_db)
            if index >= 0:
                self.tables_tab.db_selector.setCurrentIndex(index)
        
        self._update_tab_states()
    
    def _on_database_double_clicked(self, item):
        """Handle database double-click in the database tab"""
        selected_db = item.text()
        
        # Update the database selector in the tables tab
        index = self.tables_tab.db_selector.findText(selected_db)
        if index >= 0:
            self.tables_tab.db_selector.setCurrentIndex(index)
        
        # Switch to the tables tab
        self.tabs.setCurrentIndex(1)  # Index 1 is the tables tab
    
    def _on_tables_db_changed(self, database_name):
        """Handle database selection change in the tables tab"""
        if database_name:
            # Populate tables for the selected database
            self._populate_tables(database_name)
            
            # Update table selectors in columns and indexes tabs
            self._populate_table_selectors(database_name)
        else:
            # Clear tables list if no database is selected
            self.tables_tab.tables_list.clear()
            self.columns_tab.table_selector.clear()
            self.indexes_tab.table_selector.clear()
        
        self._update_tab_states()
    
    def _on_table_selection_changed(self):
        """Handle table selection change in the tables tab"""
        selected_items = self.tables_tab.tables_list.selectedItems()
        if selected_items:
            selected_table = selected_items[0].text()
            
            # Update the table selectors in the columns and indexes tabs
            index = self.columns_tab.table_selector.findText(selected_table)
            if index >= 0:
                # Block signals to prevent triggering multiple updates
                self.columns_tab.table_selector.blockSignals(True)
                self.columns_tab.table_selector.setCurrentIndex(index)
                self.columns_tab.table_selector.blockSignals(False)
                
                # Explicitly populate columns for the selected table
                self._populate_columns(selected_table)
            
            index = self.indexes_tab.table_selector.findText(selected_table)
            if index >= 0:
                # Block signals to prevent triggering multiple updates
                self.indexes_tab.table_selector.blockSignals(True)
                self.indexes_tab.table_selector.setCurrentIndex(index)
                self.indexes_tab.table_selector.blockSignals(False)
                
                # Explicitly populate indexes for the selected table
                self._populate_indexes(selected_table)
        
        self._update_tab_states()
    
    def _on_table_double_clicked(self, item):
        """Handle table double-click in the tables tab"""
        selected_table = item.text()
        
        # Update the table selector in the columns tab
        index = self.columns_tab.table_selector.findText(selected_table)
        if index >= 0:
            self.columns_tab.table_selector.setCurrentIndex(index)
        
        # Switch to the columns tab
        self.tabs.setCurrentIndex(2)  # Index 2 is the columns tab
    
    def _on_tab_changed(self, index):
        """Handle tab change"""
        if index == 1:  # Tables tab
            # If a database is selected in the database tab, update the tables tab
            selected_items = self.database_tab.databases_list.selectedItems()
            if selected_items:
                selected_db = selected_items[0].text()
                
                # Update the database selector in the tables tab
                db_index = self.tables_tab.db_selector.findText(selected_db)
                if db_index >= 0:
                    self.tables_tab.db_selector.setCurrentIndex(db_index)
                    
                    # Make sure tables are populated
                    if self.tables_tab.tables_list.count() == 0:
                        self._populate_tables(selected_db)
        
        elif index == 2:  # Columns tab
            # If a table is selected in the tables tab, update the columns tab
            selected_items = self.tables_tab.tables_list.selectedItems()
            if selected_items:
                selected_table = selected_items[0].text()
                
                # Update the table selector in the columns tab
                table_index = self.columns_tab.table_selector.findText(selected_table)
                if table_index >= 0:
                    # Block signals to prevent triggering multiple updates
                    self.columns_tab.table_selector.blockSignals(True)
                    self.columns_tab.table_selector.setCurrentIndex(table_index)
                    self.columns_tab.table_selector.blockSignals(False)
                    
                    # Explicitly populate columns for the selected table
                    self._populate_columns(selected_table)
        
        elif index == 3:  # Indexes tab
            # If a table is selected in the tables tab, update the indexes tab
            selected_items = self.tables_tab.tables_list.selectedItems()
            if selected_items:
                selected_table = selected_items[0].text()
                
                # Update the table selector in the indexes tab
                table_index = self.indexes_tab.table_selector.findText(selected_table)
                if table_index >= 0:
                    # Block signals to prevent triggering multiple updates
                    self.indexes_tab.table_selector.blockSignals(True)
                    self.indexes_tab.table_selector.setCurrentIndex(table_index)
                    self.indexes_tab.table_selector.blockSignals(False)
                    
                    # Explicitly populate indexes for the selected table
                    self._populate_indexes(selected_table)
    
    def _drop_index(self):
        """Drop the selected index"""
        # Get the selected table and index
        table_name = self.indexes_tab.table_selector.currentText()
        selected_items = self.indexes_tab.indexes_list.selectedItems()
        
        if not table_name:
            QMessageBox.warning(self, "Warning", "Please select a table.")
            return
        
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select an index to drop.")
            return
            
        # Get the current database
        database_name = self.tables_tab.db_selector.currentText()
        
        # Check if this is a system database
        if self.connection.is_system_database(database_name):
            QMessageBox.warning(
                self, 
                "System Database", 
                f"'{database_name}' is a system database. Dropping indexes is not allowed to prevent system damage."
            )
            return
        
        index_name = selected_items[0].text()
        
        # Confirm the drop operation
        reply = QMessageBox.question(
            self, "Confirm Drop",
            f"Are you sure you want to drop the index '{index_name}'?\nThis action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Execute the DROP INDEX statement
                # Note: The exact syntax varies by database type
                db_type = self.connection.params['type']
                
                if db_type == 'SQLite':
                    sql = f"DROP INDEX {index_name};"
                elif db_type == 'MySQL':
                    sql = f"DROP INDEX {index_name} ON {table_name};"
                elif db_type == 'PostgreSQL':
                    sql = f"DROP INDEX {index_name};"
                else:
                    QMessageBox.warning(self, "Not Supported", f"Dropping indexes is not supported for {db_type}.")
                    return
                
                # Get the current database from the tables tab
                database_name = self.tables_tab.db_selector.currentText()
                if not database_name:
                    QMessageBox.warning(self, "Warning", "No database selected.")
                    return
                
                # Save current database
                current_db = self.connection.get_database_name()
                
                try:
                    # Switch to the selected database temporarily if needed
                    if current_db != database_name:
                        self.connection.use_database(database_name)
                    
                    # Execute the DROP INDEX statement
                    self.connection.execute_non_query(sql)
                    
                    # Refresh the indexes list
                    self._populate_indexes(table_name)
                finally:
                    # Switch back to the original database if needed
                    if current_db != database_name and current_db != "(No database selected)":
                        self.connection.use_database(current_db)
                
                QMessageBox.information(self, "Success", f"Index '{index_name}' dropped successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to drop index: {str(e)}")


class CreateTableDialog(QDialog):
    """Dialog for creating a new table"""
    
    # Class variable to control test mode
    _test_mode = False
    
    @classmethod
    def set_test_mode(cls, enabled=True):
        """Set test mode to prevent UI operations during tests"""
        cls._test_mode = enabled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Create Table")
        self.resize(600, 400)
        
        self._create_ui()
        self._connect_signals()
        
        # Don't show the dialog in test mode
        if self._test_mode:
            self.setVisible(False)
    
    def _create_ui(self):
        """Create the UI components"""
        layout = QVBoxLayout(self)
        
        # Table name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Table Name:"))
        self.table_name_edit = QLineEdit()
        name_layout.addWidget(self.table_name_edit)
        layout.addLayout(name_layout)
        
        # Columns
        layout.addWidget(QLabel("Columns:"))
        
        # Columns table
        self.columns_table = QTableWidget()
        self.columns_table.setColumnCount(4)
        self.columns_table.setHorizontalHeaderLabels(["Name", "Type", "Primary Key", "Nullable"])
        header = self.columns_table.horizontalHeader()
        if header:
            header.setStretchLastSection(True)
        layout.addWidget(self.columns_table)
        
        # Column buttons
        column_buttons_layout = QHBoxLayout()
        self.add_column_button = QPushButton("Add Column")
        self.remove_column_button = QPushButton("Remove Column")
        column_buttons_layout.addWidget(self.add_column_button)
        column_buttons_layout.addWidget(self.remove_column_button)
        layout.addLayout(column_buttons_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _connect_signals(self):
        """Connect signals to slots"""
        self.add_column_button.clicked.connect(self._add_column)
        self.remove_column_button.clicked.connect(self._remove_column)
    
    def _add_column(self):
        """Add a new column to the table"""
        row_count = self.columns_table.rowCount()
        self.columns_table.setRowCount(row_count + 1)
        
        # Add column name cell
        self.columns_table.setItem(row_count, 0, QTableWidgetItem(""))
        
        # Add column type cell with common SQL types
        type_combo = QComboBox()
        type_combo.addItems([
            "INTEGER", "BIGINT", "SMALLINT", "TINYINT",
            "FLOAT", "DOUBLE(10,2)", "DECIMAL(10,2)",
            "CHAR(1)", "VARCHAR(255)", "TEXT",
            "DATE", "TIME", "DATETIME", "TIMESTAMP",
            "BOOLEAN", "BLOB"
        ])
        self.columns_table.setCellWidget(row_count, 1, type_combo)
        
        # Add primary key checkbox
        pk_checkbox = QCheckBox()
        pk_checkbox.setChecked(False)
        self.columns_table.setCellWidget(row_count, 2, pk_checkbox)
        
        # Add nullable checkbox
        nullable_checkbox = QCheckBox()
        nullable_checkbox.setChecked(True)
        self.columns_table.setCellWidget(row_count, 3, nullable_checkbox)
    
    def _remove_column(self):
        """Remove the selected column from the table"""
        selected_rows = self.columns_table.selectedIndexes()
        if not selected_rows:
            return
        
        # Get the row of the first selected cell
        row = selected_rows[0].row()
        self.columns_table.removeRow(row)
    
    def get_table_definition(self):
        """Get the table definition from the dialog"""
        table_def = {
            'name': self.table_name_edit.text(),
            'columns': []
        }
        
        # Get column definitions
        for row in range(self.columns_table.rowCount()):
            # Get column name
            name_item = self.columns_table.item(row, 0)
            if not name_item or not name_item.text():
                continue
            
            # Get column type
            type_combo = self.columns_table.cellWidget(row, 1)
            if not type_combo:
                continue
            
            # Get primary key flag
            pk_checkbox = self.columns_table.cellWidget(row, 2)
            if not pk_checkbox:
                continue
            
            # Get nullable flag
            nullable_checkbox = self.columns_table.cellWidget(row, 3)
            if not nullable_checkbox:
                continue
            
            # Add column definition
            table_def['columns'].append({
                'name': name_item.text(),
                'type': cast(QComboBox, type_combo).currentText(),
                'primary_key': cast(QCheckBox, pk_checkbox).isChecked(),
                'nullable': cast(QCheckBox, nullable_checkbox).isChecked()
            })
        
        return table_def


class AddColumnDialog(QDialog):
    """Dialog for adding a column to a table"""
    
    # Class variable to control test mode
    _test_mode = False
    
    @classmethod
    def set_test_mode(cls, enabled=True):
        """Set test mode to prevent UI operations during tests"""
        cls._test_mode = enabled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Add Column")
        self.resize(400, 200)
        
        self._create_ui()
        
        # Don't show the dialog in test mode
        if self._test_mode:
            self.setVisible(False)
    
    def _create_ui(self):
        """Create the UI components"""
        layout = QVBoxLayout(self)
        
        # Form layout for column properties
        form_layout = QFormLayout()
        
        # Column name
        self.column_name_edit = QLineEdit()
        form_layout.addRow("Column Name:", self.column_name_edit)
        
        # Column type
        self.column_type_combo = QComboBox()
        self.column_type_combo.addItems([
            "INTEGER", "BIGINT", "SMALLINT", "TINYINT",
            "FLOAT", "DOUBLE", "DECIMAL",
            "CHAR", "VARCHAR", "TEXT",
            "DATE", "TIME", "DATETIME", "TIMESTAMP",
            "BOOLEAN", "BLOB"
        ])
        form_layout.addRow("Column Type:", self.column_type_combo)
        
        # Size/precision options layout
        size_layout = QHBoxLayout()
        
        # Size/length field
        self.size_edit = QLineEdit()
        self.size_edit.setPlaceholderText("Size")
        size_layout.addWidget(self.size_edit)
        
        # Precision field (for DECIMAL, DOUBLE, etc.)
        self.precision_edit = QLineEdit()
        self.precision_edit.setPlaceholderText("Precision")
        self.precision_edit.setVisible(False)
        size_layout.addWidget(self.precision_edit)
        
        form_layout.addRow("Size/Precision:", size_layout)
        
        # Nullable
        self.nullable_checkbox = QCheckBox()
        self.nullable_checkbox.setChecked(True)
        form_layout.addRow("Nullable:", self.nullable_checkbox)
        
        # Default value
        self.default_value_edit = QLineEdit()
        form_layout.addRow("Default Value:", self.default_value_edit)
        
        layout.addLayout(form_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect signals
        self.column_type_combo.currentTextChanged.connect(self._on_column_type_changed)
        
        # Initialize size fields visibility
        self._on_column_type_changed(self.column_type_combo.currentText())
    
    def _on_column_type_changed(self, column_type):
        """Handle column type changes to show/hide size and precision fields"""
        # Types that need size specification
        size_types = ["VARCHAR", "CHAR", "NVARCHAR", "NCHAR"]
        # Types that need both size and precision
        precision_types = ["DECIMAL", "NUMERIC", "FLOAT", "DOUBLE"]
        
        if column_type in size_types:
            self.size_edit.setVisible(True)
            self.precision_edit.setVisible(False)
            self.size_edit.setPlaceholderText("Length (1-255)")
            
            # Set reasonable defaults for string types
            if not self.size_edit.text() and column_type in ["VARCHAR", "NVARCHAR"]:
                self.size_edit.setText("255")  # Common default for VARCHAR
            elif not self.size_edit.text() and column_type in ["CHAR", "NCHAR"]:
                self.size_edit.setText("1")    # Common default for CHAR
                
        elif column_type in precision_types:
            self.size_edit.setVisible(True)
            self.precision_edit.setVisible(True)
            
            # Set appropriate placeholder text based on the type
            if column_type == "DECIMAL" or column_type == "NUMERIC":
                self.size_edit.setPlaceholderText("Precision (1-65)")
                self.precision_edit.setPlaceholderText("Scale (0-30)")
                
                # Set reasonable defaults for DECIMAL/NUMERIC
                if not self.size_edit.text():
                    self.size_edit.setText("10")
                if not self.precision_edit.text():
                    self.precision_edit.setText("2")
            else:  # FLOAT or DOUBLE
                self.size_edit.setPlaceholderText("Digits (1-53)")
                self.precision_edit.setPlaceholderText("Decimals (0-30)")
                
                # Set reasonable defaults for FLOAT/DOUBLE
                if not self.size_edit.text():
                    self.size_edit.setText("10")
                if not self.precision_edit.text():
                    self.precision_edit.setText("2")
        else:
            self.size_edit.setVisible(False)
            self.precision_edit.setVisible(False)
            
    def accept(self):
        """Override accept to validate input before closing the dialog"""
        # Validate column name
        if not self.column_name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Column name cannot be empty.")
            return
            
        # Validate size/precision for types that require it
        column_type = self.column_type_combo.currentText()
        size_types = ["VARCHAR", "CHAR", "NVARCHAR", "NCHAR"]
        precision_types = ["DECIMAL", "NUMERIC", "FLOAT", "DOUBLE"]
        
        if column_type in size_types and self.size_edit.isVisible():
            try:
                size = int(self.size_edit.text())
                if size <= 0:
                    QMessageBox.warning(self, "Validation Error", "Size must be a positive number.")
                    return
                    
                # Specific validation for different types
                if column_type in ["VARCHAR", "NVARCHAR"] and size > 65535:
                    QMessageBox.warning(self, "Validation Error", "Maximum VARCHAR length is 65535.")
                    return
            except ValueError:
                if self.size_edit.text():  # Only show error if user entered something
                    QMessageBox.warning(self, "Validation Error", "Size must be a valid number.")
                    return
                
        elif column_type in precision_types and self.size_edit.isVisible():
            try:
                if self.size_edit.text():
                    digits = int(self.size_edit.text())
                    if digits <= 0:
                        QMessageBox.warning(self, "Validation Error", "Digits must be a positive number.")
                        return
                        
                if self.precision_edit.text():
                    decimals = int(self.precision_edit.text())
                    if decimals < 0:
                        QMessageBox.warning(self, "Validation Error", "Decimals cannot be negative.")
                        return
                        
                    # If both are specified, validate their relationship
                    if self.size_edit.text() and decimals > int(self.size_edit.text()):
                        QMessageBox.warning(self, "Validation Error", 
                                           "Decimals cannot be greater than total digits.")
                        return
            except ValueError:
                QMessageBox.warning(self, "Validation Error", 
                                   "Digits and decimals must be valid numbers.")
                return
                
        # If all validation passes, accept the dialog
        super().accept()
    
    def get_column_definition(self):
        """Get the column definition from the dialog"""
        default_value = self.default_value_edit.text()
        if not default_value:
            default_value = None
        
        # Get the base type
        column_type = self.column_type_combo.currentText()
        
        # Add size/precision if applicable
        size_types = ["VARCHAR", "CHAR", "NVARCHAR", "NCHAR"]
        precision_types = ["DECIMAL", "NUMERIC", "FLOAT", "DOUBLE"]
        
        # Track if we're using a numeric type with precision for default value formatting
        is_precise_numeric = False
        precision_value = "0"
        
        if column_type in size_types and self.size_edit.text():
            column_type = f"{column_type}({self.size_edit.text()})"
        elif column_type in precision_types:
            size = self.size_edit.text() or "10"  # Default size if not specified
            precision = self.precision_edit.text() or "0"  # Default precision if not specified
            precision_value = precision
            if self.size_edit.text() or self.precision_edit.text():
                column_type = f"{column_type}({size},{precision})"
                is_precise_numeric = True
        
        # Format default value appropriately for the data type
        if default_value is not None:
            # For numeric types with precision, ensure default value matches the format
            if is_precise_numeric and column_type in precision_types:
                try:
                    # Try to format the number with the specified precision
                    num_value = float(default_value)
                    # Format as string with the correct number of decimal places
                    default_value = f"{num_value:.{precision_value}f}"
                except ValueError:
                    # If it's not a valid number, leave it as is
                    pass
            
            # For string types, add quotes if not already present
            elif column_type.startswith(("CHAR", "VARCHAR", "TEXT")):
                if not (default_value.startswith("'") and default_value.endswith("'")):
                    default_value = f"'{default_value}'"
        
        return {
            'name': self.column_name_edit.text(),
            'type': column_type,
            'nullable': self.nullable_checkbox.isChecked(),
            'default': default_value
        }


class CreateIndexDialog(QDialog):
    """Dialog for creating an index"""
    
    # Class variable to control test mode
    _test_mode = False
    
    @classmethod
    def set_test_mode(cls, enabled=True):
        """Set test mode to prevent UI operations during tests"""
        cls._test_mode = enabled
    
    def __init__(self, connection, parent=None):
        super().__init__(parent)
        
        self.connection = connection
        self.database_name: Optional[str] = None  # Initialize database_name attribute
        self.original_db: Optional[str] = None    # Initialize original_db attribute
        
        self.setWindowTitle("Create Index")
        self.resize(400, 300)
        
        self._create_ui()
        self._connect_signals()
        self._populate_tables()
        
        # Don't show the dialog in test mode
        if self._test_mode:
            self.setVisible(False)
    
    def _create_ui(self):
        """Create the UI components"""
        layout = QVBoxLayout(self)
        
        # Form layout for index properties
        form_layout = QFormLayout()
        
        # Index name
        self.index_name_edit = QLineEdit()
        form_layout.addRow("Index Name:", self.index_name_edit)
        
        # Table
        self.table_combo = QComboBox()
        form_layout.addRow("Table:", self.table_combo)
        
        layout.addLayout(form_layout)
        
        # Columns
        layout.addWidget(QLabel("Columns:"))
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.columns_list)
        
        # Unique index
        self.unique_checkbox = QCheckBox("Unique Index")
        layout.addWidget(self.unique_checkbox)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _connect_signals(self):
        """Connect signals to slots"""
        self.table_combo.currentTextChanged.connect(self._populate_columns)
    
    def _populate_tables(self):
        """Populate the tables combo box"""
        self.table_combo.clear()
        
        try:
            # If we have a specific database set, make sure we're using it
            if hasattr(self, 'database_name'):
                # We're already in the correct database context because
                # the parent dialog switched to it before creating this dialog
                tables = self.connection.get_tables()
            else:
                # Just use whatever database is currently selected
                tables = self.connection.get_tables()
                
            self.table_combo.addItems(tables)
        except Exception as e:
            print(f"Error populating tables: {e}")
    
    def _populate_columns(self, table_name):
        """Populate the columns list for the selected table"""
        self.columns_list.clear()
        
        if not table_name:
            return
        
        try:
            # If we have a specific database set, make sure we're using it
            if hasattr(self, 'database_name'):
                # We're already in the correct database context because
                # the parent dialog switched to it before creating this dialog
                columns = self.connection.get_columns(table_name)
            else:
                # Just use whatever database is currently selected
                columns = self.connection.get_columns(table_name)
                
            for column in columns:
                self.columns_list.addItem(column['name'])
        except Exception as e:
            print(f"Error populating columns: {e}")
    
    def get_index_definition(self):
        """Get the index definition from the dialog"""
        # Get selected columns
        selected_columns = []
        for item in self.columns_list.selectedItems():
            selected_columns.append(item.text())
        
        return {
            'name': self.index_name_edit.text(),
            'table': self.table_combo.currentText(),
            'columns': selected_columns,
            'unique': self.unique_checkbox.isChecked()
        }