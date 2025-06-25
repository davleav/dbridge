"""
Connection dialog for database connections
"""

from typing import Dict, Any, Union, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QComboBox, QSpinBox, QDialogButtonBox,
    QTabWidget, QWidget, QLabel, QCheckBox, QFileDialog,
    QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt

class ConnectionDialog(QDialog):
    """Dialog for creating and editing database connections"""
    
    connection_params: Optional[Dict[str, Any]]
    
    def __init__(self, parent=None, connection_params: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        
        self.setWindowTitle("Database Connection")
        self.setMinimumWidth(450)
        self.connection_params = connection_params
        
        self._create_ui()
        
        # If editing an existing connection, populate the fields
        if self.connection_params:
            self._populate_fields()
    
    def _create_ui(self) -> None:
        """Create the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Connection name
        name_layout = QFormLayout()
        self.name_edit = QLineEdit()
        name_layout.addRow("Connection Name:", self.name_edit)
        layout.addLayout(name_layout)
        
        # Connection type tabs
        self.conn_tabs = QTabWidget()
        
        # MySQL tab
        mysql_tab = QWidget()
        mysql_layout = QFormLayout(mysql_tab)
        
        self.mysql_host = QLineEdit("localhost")
        mysql_layout.addRow("Host:", self.mysql_host)
        
        self.mysql_port = QSpinBox()
        self.mysql_port.setRange(1, 65535)
        self.mysql_port.setValue(3306)
        mysql_layout.addRow("Port:", self.mysql_port)
        
        self.mysql_user = QLineEdit()
        mysql_layout.addRow("Username:", self.mysql_user)
        
        self.mysql_password = QLineEdit()
        self.mysql_password.setEchoMode(QLineEdit.EchoMode.Password)
        mysql_layout.addRow("Password:", self.mysql_password)
        
        self.mysql_save_password = QCheckBox("Save password (encrypted)")
        mysql_layout.addRow("", self.mysql_save_password)
        
        self.mysql_database = QLineEdit()
        mysql_layout.addRow("Database (optional):", self.mysql_database)
        
        self.conn_tabs.addTab(mysql_tab, "MySQL")
        
        # PostgreSQL tab
        pg_tab = QWidget()
        pg_layout = QFormLayout(pg_tab)
        
        self.pg_host = QLineEdit("localhost")
        pg_layout.addRow("Host:", self.pg_host)
        
        self.pg_port = QSpinBox()
        self.pg_port.setRange(1, 65535)
        self.pg_port.setValue(5432)
        pg_layout.addRow("Port:", self.pg_port)
        
        self.pg_user = QLineEdit()
        pg_layout.addRow("Username:", self.pg_user)
        
        self.pg_password = QLineEdit()
        self.pg_password.setEchoMode(QLineEdit.EchoMode.Password)
        pg_layout.addRow("Password:", self.pg_password)
        
        self.pg_save_password = QCheckBox("Save password (encrypted)")
        pg_layout.addRow("", self.pg_save_password)
        
        self.pg_database = QLineEdit()
        pg_layout.addRow("Database (optional):", self.pg_database)
        
        self.conn_tabs.addTab(pg_tab, "PostgreSQL")
        
        # SQLite tab
        sqlite_tab = QWidget()
        sqlite_layout = QFormLayout(sqlite_tab)
        
        sqlite_file_layout = QHBoxLayout()
        self.sqlite_file = QLineEdit()
        sqlite_file_layout.addWidget(self.sqlite_file)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_sqlite_file)
        sqlite_file_layout.addWidget(browse_button)
        
        sqlite_layout.addRow("Database File:", sqlite_file_layout)
        
        self.conn_tabs.addTab(sqlite_tab, "SQLite")
        
        layout.addWidget(self.conn_tabs)
        
        # Test connection button
        test_button = QPushButton("Test Connection")
        test_button.setMinimumHeight(30)
        test_button.setStyleSheet("font-weight: bold;")
        test_button.clicked.connect(self._test_connection)
        layout.addWidget(test_button)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _browse_sqlite_file(self) -> None:
        """Open file dialog to select SQLite database file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select SQLite Database", "", "SQLite Database (*.db *.sqlite);;All Files (*)"
        )
        if file_path:
            self.sqlite_file.setText(file_path)
    
    def _test_connection(self) -> None:
        """Test the current connection settings"""
        from PyQt6.QtWidgets import QMessageBox
        from src.core.connection_manager import DatabaseConnection
        # Import the patch to handle string values for port and save_password
        import src.core.connection_manager_patch
        
        # Validate input before testing
        if not self._validate_connection_input():
            return
            
        try:
            # Get the current connection parameters
            connection_params = self.get_connection_params()
            
            # Create a temporary connection to test
            temp_connection = DatabaseConnection(connection_params)
            
            # If we get here, the connection was successful
            
            # Get database name (might be empty)
            db_name = connection_params.get('database', '').strip()
            
            # Try to get tables to further verify the connection
            tables = []
            if db_name:  # Only try to get tables if a database is selected
                try:
                    tables = temp_connection.get_tables()
                except Exception:
                    # If we can't get tables, it might be because no database is selected
                    pass
            
            # Close the temporary connection
            temp_connection.close()
            
            # Show success message
            if db_name:
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    f"Successfully connected to {connection_params['type']} database.\n"
                    f"Database: {db_name}\n"
                    f"Tables found: {len(tables)}"
                )
            else:
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    f"Successfully connected to {connection_params['type']} server.\n"
                    f"No database selected. You can create or select a database using SQL commands."
                )
            
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Failed to connect to the database.\nError: {str(e)}"
            )
    
    def _validate_connection_input(self) -> bool:
        """Validate the connection input fields
        
        Returns:
            bool: True if all required fields are valid, False otherwise
        """
        from PyQt6.QtWidgets import QMessageBox
        
        # Check connection name
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a connection name.")
            return False
            
        # Get the current connection type
        conn_type = self.conn_tabs.tabText(self.conn_tabs.currentIndex())
        
        # Validate based on connection type
        if conn_type == 'MySQL':
            if not self.mysql_host.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter a host name.")
                return False
            if not self.mysql_user.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter a username.")
                return False
            # Database name is now optional
                
        elif conn_type == 'PostgreSQL':
            if not self.pg_host.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter a host name.")
                return False
            if not self.pg_user.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter a username.")
                return False
            # Database name is now optional
                
        elif conn_type == 'SQLite':
            if not self.sqlite_file.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please select a database file.")
                return False
                
        return True
    
    def _on_accept(self) -> None:
        """Validate input and accept the dialog if valid"""
        if self._validate_connection_input():
            self.accept()
    
    def _populate_fields(self) -> None:
        """Populate the dialog fields with existing connection parameters"""
        if not self.connection_params:
            return
            
        # Set connection name
        # We've already checked that connection_params is not None
        assert self.connection_params is not None
        self.name_edit.setText(self.connection_params.get('name', ''))
        
        # Set the appropriate tab based on connection type
        conn_type = self.connection_params.get('type', '')
        if conn_type == 'MySQL':
            self.conn_tabs.setCurrentIndex(0)  # MySQL tab
            self.mysql_host.setText(self.connection_params.get('host', 'localhost'))
            self.mysql_port.setValue(int(self.connection_params.get('port', 3306)))
            self.mysql_user.setText(self.connection_params.get('user', ''))
            self.mysql_password.setText(self.connection_params.get('password', ''))
            
            # Handle save_password which could be boolean or string
            save_password = self.connection_params.get('save_password', False)
            if isinstance(save_password, bool):
                self.mysql_save_password.setChecked(save_password)
            else:
                # Handle string representation
                self.mysql_save_password.setChecked(str(save_password).lower() == 'true')
                
            self.mysql_database.setText(self.connection_params.get('database', ''))
        elif conn_type == 'PostgreSQL':
            self.conn_tabs.setCurrentIndex(1)  # PostgreSQL tab
            self.pg_host.setText(self.connection_params.get('host', 'localhost'))
            self.pg_port.setValue(int(self.connection_params.get('port', 5432)))
            self.pg_user.setText(self.connection_params.get('user', ''))
            self.pg_password.setText(self.connection_params.get('password', ''))
            
            # Handle save_password which could be boolean or string
            save_password = self.connection_params.get('save_password', False)
            if isinstance(save_password, bool):
                self.pg_save_password.setChecked(save_password)
            else:
                # Handle string representation
                self.pg_save_password.setChecked(str(save_password).lower() == 'true')
                
            self.pg_database.setText(self.connection_params.get('database', ''))
        elif conn_type == 'SQLite':
            self.conn_tabs.setCurrentIndex(2)  # SQLite tab
            self.sqlite_file.setText(self.connection_params.get('database', ''))
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get the connection parameters from the dialog
        
        Returns:
            Dict[str, Any]: A dictionary containing connection parameters.
                           Note: Port values are returned as integers and save_password as boolean.
        """
        connection_params = {
            'name': self.name_edit.text(),
            'type': self.conn_tabs.tabText(self.conn_tabs.currentIndex())
        }
        
        if connection_params['type'] == 'MySQL':
            connection_params['host'] = self.mysql_host.text()
            connection_params['port'] = self.mysql_port.value()  # Return as integer
            connection_params['user'] = self.mysql_user.text()
            connection_params['password'] = self.mysql_password.text()
            connection_params['save_password'] = self.mysql_save_password.isChecked()  # Return as boolean
            connection_params['database'] = self.mysql_database.text()
        elif connection_params['type'] == 'PostgreSQL':
            connection_params['host'] = self.pg_host.text()
            connection_params['port'] = self.pg_port.value()  # Return as integer
            connection_params['user'] = self.pg_user.text()
            connection_params['password'] = self.pg_password.text()
            connection_params['save_password'] = self.pg_save_password.isChecked()  # Return as boolean
            connection_params['database'] = self.pg_database.text()
        elif connection_params['type'] == 'SQLite':
            connection_params['database'] = self.sqlite_file.text()
        
        return connection_params