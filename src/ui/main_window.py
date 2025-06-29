"""
Main window for the DBridge application
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeView, QTableView, QTextEdit, QPushButton,
    QComboBox, QLabel, QMessageBox, QFileDialog, QToolBar, QStatusBar,
    QDockWidget, QMenu, QMenuBar, QInputDialog, QListWidget, QDialog,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QFont, QIcon, QPixmap, QActionGroup

from src.ui.connection_dialog import ConnectionDialog
from src.ui.connection_tab import ConnectionTab
from src.ui.import_export_dialog import ImportExportDialog
from src.ui.database_manager import DatabaseManagerDialog
from src.ui.theme_manager import ThemeManager, LIGHT_DEFAULT, LIGHT_BLUE, DARK_DEFAULT, DARK_BLUE
from src.core.connection_manager import ConnectionManager
from src import __version__

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.connection_manager = ConnectionManager()
        self.theme_manager = ThemeManager()
        
        self.setWindowTitle(f"DBridge Beta {__version__}")
        self.setMinimumSize(1000, 700)
        
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()
        self._create_central_widget()
        
        # Load saved connections
        self._populate_connections_menu()
        
        # Apply the current theme
        self.theme_manager.set_theme(self.theme_manager.get_current_theme())
    
    def _create_menu_bar(self):
        """Create the application menu bar"""
        menu_bar = self.menuBar()
        
        # Check if menu_bar is not None before accessing its methods
        if menu_bar is None:
            return
            
        # Add context menu to menu bar
        menu_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        menu_bar.customContextMenuRequested.connect(self._show_toolbar_context_menu)
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        if file_menu is None:
            return
            
        new_conn_action = QAction("&New Connection", self)
        new_conn_action.setShortcut("Ctrl+N")
        new_conn_action.triggered.connect(self._new_connection)
        file_menu.addAction(new_conn_action)
        
        # Connections submenu
        self.connections_menu = QMenu("Saved Connections", self)
        file_menu.addMenu(self.connections_menu)
        
        file_menu.addSeparator()
        
        # Import/Export submenu
        import_export_menu = QMenu("Import/Export", self)
        
        import_sql_action = QAction("Import SQL File...", self)
        import_sql_action.triggered.connect(self._import_sql_file)
        import_export_menu.addAction(import_sql_action)
        
        import_export_menu.addSeparator()
        
        export_db_action = QAction("Export Database...", self)
        export_db_action.triggered.connect(self._export_database)
        import_export_menu.addAction(export_db_action)
        
        file_menu.addMenu(import_export_menu)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        # Check if edit_menu is None
        if edit_menu is None:
            pass  # Skip edit menu if it's None
        else:
            # Add "Show System Databases" option
            self.show_system_db_action = QAction("Show System Databases", self)
            self.show_system_db_action.setCheckable(True)
            self.show_system_db_action.setChecked(self.connection_manager.get_show_system_databases())
            self.show_system_db_action.triggered.connect(self._toggle_system_databases)
            edit_menu.addAction(self.show_system_db_action)
            
            edit_menu.addSeparator()
            
            # Add theme submenu
            theme_menu = QMenu("Theme", self)
            edit_menu.addMenu(theme_menu)
            
            # Create action group for themes to make them exclusive
            theme_group = QActionGroup(self)
            theme_group.setExclusive(True)
            
            # Add theme actions
            light_default_action = QAction(LIGHT_DEFAULT, self)
            light_default_action.setCheckable(True)
            light_default_action.setChecked(self.theme_manager.get_current_theme() == LIGHT_DEFAULT)
            light_default_action.triggered.connect(lambda: self._change_theme(LIGHT_DEFAULT))
            theme_group.addAction(light_default_action)
            theme_menu.addAction(light_default_action)
            
            light_blue_action = QAction(LIGHT_BLUE, self)
            light_blue_action.setCheckable(True)
            light_blue_action.setChecked(self.theme_manager.get_current_theme() == LIGHT_BLUE)
            light_blue_action.triggered.connect(lambda: self._change_theme(LIGHT_BLUE))
            theme_group.addAction(light_blue_action)
            theme_menu.addAction(light_blue_action)
            
            theme_menu.addSeparator()
            
            dark_default_action = QAction(DARK_DEFAULT, self)
            dark_default_action.setCheckable(True)
            dark_default_action.setChecked(self.theme_manager.get_current_theme() == DARK_DEFAULT)
            dark_default_action.triggered.connect(lambda: self._change_theme(DARK_DEFAULT))
            theme_group.addAction(dark_default_action)
            theme_menu.addAction(dark_default_action)
            
            dark_blue_action = QAction(DARK_BLUE, self)
            dark_blue_action.setCheckable(True)
            dark_blue_action.setChecked(self.theme_manager.get_current_theme() == DARK_BLUE)
            dark_blue_action.triggered.connect(lambda: self._change_theme(DARK_BLUE))
            theme_group.addAction(dark_blue_action)
            theme_menu.addAction(dark_blue_action)
        
        # Query menu
        query_menu = menu_bar.addMenu("&Query")
        if query_menu is None:
            pass  # Skip query menu if it's None
        else:
            self.run_query_action = QAction("&Run Query", self)
            self.run_query_action.setShortcut("F5")
            self.run_query_action.triggered.connect(self._run_query)
            self.run_query_action.setEnabled(False)  # Initially disabled until a connection is established
            query_menu.addAction(self.run_query_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        if tools_menu is None:
            pass  # Skip tools menu if it's None
        else:
            # Add database manager action
            db_manager_action = QAction("Database Manager", self)
            db_manager_action.triggered.connect(self._open_database_manager)
            tools_menu.addAction(db_manager_action)
            
            tools_menu.addSeparator()
            
            # Add show/hide toolbar action
            self.show_toolbar_action = QAction("Hide Main Toolbar", self)
            self.show_toolbar_action.setCheckable(True)
            self.show_toolbar_action.setChecked(True)
            self.show_toolbar_action.triggered.connect(self._toggle_toolbar)
            tools_menu.addAction(self.show_toolbar_action)
            
            # Add show/hide database browser action
            self.show_db_browser_action = QAction("Hide Database Browser", self)
            self.show_db_browser_action.setCheckable(True)
            self.show_db_browser_action.setChecked(True)
            self.show_db_browser_action.triggered.connect(self._toggle_database_browser)
            tools_menu.addAction(self.show_db_browser_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        if help_menu is None:
            pass  # Skip help menu if it's None
        else:
            about_action = QAction("&About", self)
            about_action.triggered.connect(self._show_about)
            help_menu.addAction(about_action)
    
    def _create_toolbar(self):
        """Create the main toolbar"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(self.toolbar)
        
        # Connection actions
        new_conn_action = QAction("New Connection", self)
        new_conn_action.triggered.connect(self._new_connection)
        self.toolbar.addAction(new_conn_action)
        
        # Query actions
        self.toolbar.addSeparator()
        self.run_action = QAction("Run Query", self)
        self.run_action.triggered.connect(self._run_query)
        self.run_action.setEnabled(False)  # Initially disabled until a connection is established
        self.toolbar.addAction(self.run_action)
        
        # Add context menu to toolbar
        self.toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.toolbar.customContextMenuRequested.connect(self._show_toolbar_context_menu)
    
    def _create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.connection_label = QLabel("Not connected")
        self.status_bar.addPermanentWidget(self.connection_label)
    
    def _create_central_widget(self):
        """Create the central widget with connection tabs"""
        self.connection_tabs = QTabWidget()
        self.connection_tabs.setTabsClosable(True)
        self.connection_tabs.tabCloseRequested.connect(self._close_connection_tab)
        self.connection_tabs.currentChanged.connect(self._tab_changed)
        
        # Add a welcome tab
        welcome_widget = self._create_welcome_widget()
        self.connection_tabs.addTab(welcome_widget, "Welcome")
        
        # Initially disable the database browser action since we start with the welcome tab
        self.show_db_browser_action.setEnabled(False)
        
        self.setCentralWidget(self.connection_tabs)
    
    def _is_dark_theme(self):
        """Check if the current theme is a dark theme"""
        current_theme = self.theme_manager.get_current_theme()
        return current_theme in [DARK_DEFAULT, DARK_BLUE]
    
    def _create_welcome_widget(self):
        """Create a welcome widget for the initial tab"""
        welcome_widget = QWidget()
        layout = QVBoxLayout(welcome_widget)
        
        # Welcome message
        welcome_label = QLabel(f"Welcome to DBridge Beta {__version__}")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Create font with family and point size
        font = QFont("", 16)
        # Set bold weight
        font.setBold(True)
        welcome_label.setFont(font)
        layout.addWidget(welcome_label)
        
        # Description
        desc_label = QLabel("A user-friendly SQL client for database management")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        layout.addSpacing(20)
        
        # Connection options
        options_layout = QHBoxLayout()
        options_layout.addStretch()
        
        # Create a container for both the new connection and saved connections
        connections_container = QWidget()
        connections_layout = QHBoxLayout(connections_container)
        connections_layout.setContentsMargins(0, 0, 0, 0)
        
        # New connection section with logo above button
        new_conn_widget = QWidget()
        new_conn_layout = QVBoxLayout(new_conn_widget)
        new_conn_layout.setContentsMargins(0, 0, 0, 0)
        # Set spacing to 0 to remove any space between widgets
        new_conn_layout.setSpacing(0)
        
        # Create a container for the logo and button to ensure they're together
        logo_button_container = QWidget()
        logo_button_layout = QVBoxLayout(logo_button_container)
        logo_button_layout.setContentsMargins(0, 0, 0, 0)
        logo_button_layout.setSpacing(0)  # No spacing between elements
        
        # Add DBridge logo above the new connection button
        logo_label = QLabel()
        # Try to load the logo from different possible locations
        import os
        
        # Choose the appropriate logo based on the theme
        logo_filename = "DBridge-w.png" if self._is_dark_theme() else "DBridge.png"
        
        possible_paths = [
            logo_filename,  # Current directory
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../{logo_filename}"),  # Project root
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../resources/{logo_filename}")  # Resources folder
        ]
        
        logo_loaded = False
        for path in possible_paths:
            logo_pixmap = QPixmap(path)
            if not logo_pixmap.isNull():
                # Scale the logo to match the width of the button (150px width, keeping aspect ratio)
                logo_pixmap = logo_pixmap.scaledToWidth(150, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(logo_pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                logo_button_layout.addWidget(logo_label)
                logo_loaded = True
                print(f"Loaded logo from: {path}")
                break
        
        # If the preferred logo isn't found, try the alternative logo
        if not logo_loaded:
            alt_logo_filename = "DBridge.png" if self._is_dark_theme() else "DBridge-w.png"
            alt_possible_paths = [
                alt_logo_filename,  # Current directory
                os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../{alt_logo_filename}"),  # Project root
                os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../resources/{alt_logo_filename}")  # Resources folder
            ]
            
            for path in alt_possible_paths:
                logo_pixmap = QPixmap(path)
                if not logo_pixmap.isNull():
                    # Scale the logo to match the width of the button (150px width, keeping aspect ratio)
                    logo_pixmap = logo_pixmap.scaledToWidth(150, Qt.TransformationMode.SmoothTransformation)
                    logo_label.setPixmap(logo_pixmap)
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    logo_button_layout.addWidget(logo_label)
                    logo_loaded = True
                    print(f"Loaded alternative logo from: {path}")
                    break
        
        if not logo_loaded:
            print(f"Warning: Could not load logo from any of the expected locations")
        
        # New connection button
        new_conn_button = QPushButton("New Connection")
        new_conn_button.setMinimumWidth(150)
        new_conn_button.clicked.connect(self._new_connection)
        logo_button_layout.addWidget(new_conn_button)
        
        # Add the logo-button container to the layout with bottom alignment
        new_conn_layout.addWidget(logo_button_container, 0, Qt.AlignmentFlag.AlignBottom)
        
        connections_layout.addWidget(new_conn_widget)
        
        # Saved connections section
        if self.connection_manager.get_connection_names():
            # List of saved connections
            saved_conn_widget = QWidget()
            saved_conn_layout = QVBoxLayout(saved_conn_widget)
            saved_conn_layout.setContentsMargins(0, 0, 0, 0)
            
            saved_label = QLabel("Saved Connections:")
            saved_conn_layout.addWidget(saved_label)
            
            conn_list = QListWidget()
            conn_list.setMinimumHeight(100)  # Set a minimum height for the list
            for name in self.connection_manager.get_connection_names():
                conn_list.addItem(name)
            conn_list.itemDoubleClicked.connect(
                lambda item: self._connect_to_saved(item.text())
            )
            saved_conn_layout.addWidget(conn_list)
            
            connections_layout.addWidget(saved_conn_widget)
        
        options_layout.addWidget(connections_container)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        layout.addStretch()
        
        return welcome_widget
    
    def _populate_connections_menu(self):
        """Populate the connections menu with saved connections"""
        if self.connections_menu is None:
            return
            
        self.connections_menu.clear()
        
        # Add all saved connections
        for name in self.connection_manager.get_connection_names():
            action = QAction(name, self)
            action.triggered.connect(lambda checked, n=name: self._connect_to_saved(n))
            self.connections_menu.addAction(action)
        
        # Add separator and manage connections action if there are connections
        if self.connection_manager.get_connection_names():
            self.connections_menu.addSeparator()
        
        manage_action = QAction("Manage Connections...", self)
        manage_action.triggered.connect(self._manage_connections)
        self.connections_menu.addAction(manage_action)
    
    def _new_connection(self):
        """Open the connection dialog to create a new database connection"""
        dialog = ConnectionDialog(self)
        if dialog.exec():
            connection_params = dialog.get_connection_params()
            try:
                # Create the connection
                connection = self.connection_manager.create_connection(connection_params)
                
                # Create a new tab for this connection
                self._add_connection_tab(connection)
                
                # Update the connections menu
                self._populate_connections_menu()
                
                # Update the welcome tab to show the new connection
                welcome_widget = self._create_welcome_widget()
                self.connection_tabs.removeTab(0)
                self.connection_tabs.insertTab(0, welcome_widget, "Welcome")
                
                # Update status bar
                self.status_bar.showMessage(f"Connected to {connection_params['name']}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", str(e))
    
    def _connect_to_saved(self, connection_name):
        """Connect to a saved connection"""
        try:
            # Check if this connection is already open in a tab
            for i in range(self.connection_tabs.count()):
                tab = self.connection_tabs.widget(i)
                if tab is not None and hasattr(tab, 'get_connection_name'):
                    # Use getattr to get the method, which will satisfy Pylance
                    get_name_method = getattr(tab, 'get_connection_name')
                    if get_name_method() == connection_name:
                        # Connection already open, just switch to that tab
                        self.connection_tabs.setCurrentIndex(i)
                        return
            
            # Get the connection parameters
            if connection_name in self.connection_manager.connection_params:
                conn_params = self.connection_manager.connection_params[connection_name].copy()
                
                # Check if this is a connection type that needs a password
                needs_password = False
                if conn_params['type'] in ['MySQL', 'PostgreSQL'] and ('password' not in conn_params or not conn_params['password']):
                    needs_password = True
                
                # Prompt for password if needed
                if needs_password:
                    from PyQt6.QtWidgets import QInputDialog, QLineEdit
                    password, ok = QInputDialog.getText(
                        self, 
                        f"Password for {connection_name}", 
                        f"Enter password for {conn_params['user']}@{conn_params['host']}:",
                        QLineEdit.EchoMode.Password
                    )
                    if not ok:
                        # User cancelled
                        return
                    
                    # Update the password
                    conn_params['password'] = password
                    
                    # Create the connection with the updated parameters
                    connection = self.connection_manager.create_connection(conn_params)
                else:
                    # Get the connection using the stored parameters
                    connection = self.connection_manager.get_connection(connection_name)
                
                if connection:
                    # Create a new tab for this connection
                    self._add_connection_tab(connection)
                    
                    # Update status bar
                    self.status_bar.showMessage(f"Connected to {connection_name}", 3000)
                else:
                    QMessageBox.critical(self, "Connection Error", f"Failed to connect to {connection_name}")
            else:
                QMessageBox.critical(self, "Connection Error", f"Connection '{connection_name}' not found")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))
    
    def _add_connection_tab(self, connection):
        """Add a new tab for the given connection"""
        # Create a new connection tab
        connection_tab = ConnectionTab(connection)
        connection_tab.connection_closed.connect(self._handle_connection_closed)
        
        # Add the tab
        tab_index = self.connection_tabs.addTab(connection_tab, connection.params['name'])
        
        # Switch to the new tab
        self.connection_tabs.setCurrentIndex(tab_index)
        
        # Update the connection label
        self.connection_label.setText(f"Connected: {connection.params['name']}")
        
        # Enable the run query button
        self._update_run_query_button_state()
    
    def _close_connection_tab(self, index):
        """Close the connection tab at the given index"""
        # Skip the welcome tab
        if index == 0 and self.connection_tabs.tabText(index) == "Welcome":
            return
        
        # Get the tab widget
        tab = self.connection_tabs.widget(index)
        
        # Check if the user has permission to disconnect
        # For now, we'll always allow disconnecting as it's a UI operation
        # and doesn't affect the database server
        
        # Close the connection
        if tab is not None and hasattr(tab, 'close_connection'):
            # Use getattr to get the method, which will satisfy Pylance
            close_method = getattr(tab, 'close_connection')
            close_method()
        
        # Remove the tab
        self.connection_tabs.removeTab(index)
        
        # Update the connection label and run query button state
        self._update_connection_label()
    
    def _handle_connection_closed(self, connection_name):
        """Handle when a connection is closed from within a tab"""
        # Find and remove the tab for this connection
        for i in range(self.connection_tabs.count()):
            tab = self.connection_tabs.widget(i)
            if tab is not None and hasattr(tab, 'get_connection_name'):
                # Use getattr to get the method, which will satisfy Pylance
                get_name_method = getattr(tab, 'get_connection_name')
                if get_name_method() == connection_name:
                    self.connection_tabs.removeTab(i)
                    break
        
        # Update the connection label and run query button state
        self._update_connection_label()
    
    def _tab_changed(self, index):
        """Handle when the current tab changes"""
        self._update_connection_label()
        
        # Update the database browser visibility action state
        if index >= 0:
            current_tab = self.connection_tabs.widget(index)
            if current_tab is not None and hasattr(current_tab, 'is_database_browser_visible'):
                # Use getattr to get the method, which will satisfy Pylance
                is_visible_method = getattr(current_tab, 'is_database_browser_visible')
                visible = is_visible_method()
                self.show_db_browser_action.setText("Hide Database Browser" if visible else "Show Database Browser")
                self.show_db_browser_action.setChecked(visible)
                self.show_db_browser_action.setEnabled(True)
            else:
                self.show_db_browser_action.setEnabled(False)
        
        # Update the run query button state
        self._update_run_query_button_state()
    
    def _update_connection_label(self):
        """Update the connection label based on the current tab"""
        current_index = self.connection_tabs.currentIndex()
        if current_index >= 0:
            current_tab = self.connection_tabs.widget(current_index)
            if current_tab is not None and hasattr(current_tab, 'get_connection_name'):
                # Use getattr to get the method, which will satisfy Pylance
                get_name_method = getattr(current_tab, 'get_connection_name')
                self.connection_label.setText(f"Connected: {get_name_method()}")
            else:
                self.connection_label.setText("Not connected")
        else:
            self.connection_label.setText("Not connected")
        
        # Update the run query button state
        self._update_run_query_button_state()
    
    def _update_run_query_button_state(self):
        """Update the state of the run query button based on the current tab"""
        current_index = self.connection_tabs.currentIndex()
        is_connected = False
        
        if current_index >= 0:
            current_tab = self.connection_tabs.widget(current_index)
            # Check if this is a connection tab (has run_query method)
            if current_tab is not None and hasattr(current_tab, 'run_query'):
                is_connected = True
        
        # Update both the toolbar button and menu action
        self.run_action.setEnabled(is_connected)
        self.run_query_action.setEnabled(is_connected)
    
    def _run_query(self):
        """Execute the current query in the active connection tab"""
        current_index = self.connection_tabs.currentIndex()
        if current_index >= 0:
            current_tab = self.connection_tabs.widget(current_index)
            if current_tab is not None and hasattr(current_tab, 'run_query'):
                # Use getattr to get the run_query method, which will satisfy Pylance
                run_query_method = getattr(current_tab, 'run_query')
                success, message = run_query_method()
                if success:
                    self.status_bar.showMessage(message, 3000)
            else:
                QMessageBox.warning(self, "Not Connected", "Please connect to a database first")
    
    def _manage_connections(self):
        """Open the connection management dialog"""
        # Get the list of saved connections
        connection_names = self.connection_manager.get_connection_names()
        if not connection_names:
            QMessageBox.information(self, "Manage Connections", "No saved connections found.")
            return
        
        # Create a dialog with options to edit or remove connections
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Connections")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Connection selection
        layout.addWidget(QLabel("Select a connection:"))
        connection_list = QListWidget()
        connection_list.addItems(connection_names)
        layout.addWidget(connection_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        edit_button = QPushButton("Edit")
        remove_button = QPushButton("Remove")
        button_layout.addWidget(edit_button)
        button_layout.addWidget(remove_button)
        layout.addLayout(button_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Connect signals
        def on_edit():
            current_item = connection_list.currentItem()
            if not current_item:
                return
                
            connection_name = current_item.text()
            self._edit_connection(connection_name)
            
        def on_remove():
            current_item = connection_list.currentItem()
            if not current_item:
                return
                
            connection_name = current_item.text()
            
            # Confirm deletion
            confirm = QMessageBox.question(
                dialog, "Confirm Deletion",
                f"Are you sure you want to remove the connection '{connection_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                # Close any open tabs for this connection
                for i in range(self.connection_tabs.count()):
                    tab = self.connection_tabs.widget(i)
                    if tab is not None and hasattr(tab, 'get_connection_name'):
                        # Use getattr to get the method, which will satisfy Pylance
                        get_name_method = getattr(tab, 'get_connection_name')
                        if get_name_method() == connection_name:
                            self.connection_tabs.removeTab(i)
                            break
                
                # Remove the connection
                self.connection_manager.remove_connection(connection_name)
                
                # Update the connections menu
                self._populate_connections_menu()
                
                # Update the welcome tab
                welcome_widget = self._create_welcome_widget()
                self.connection_tabs.removeTab(0)
                self.connection_tabs.insertTab(0, welcome_widget, "Welcome")
                
                # Update the connection label
                self._update_connection_label()
                
                # Remove from the list
                connection_list.takeItem(connection_list.currentRow())
                
                # Close the dialog if no more connections
                if connection_list.count() == 0:
                    dialog.accept()
        
        edit_button.clicked.connect(on_edit)
        remove_button.clicked.connect(on_remove)
        
        # Show the dialog
        dialog.exec()
        
    def _edit_connection(self, connection_name):
        """Edit an existing connection"""
        # Get the connection parameters
        connection_params = self.connection_manager.connection_params.get(connection_name)
        if not connection_params:
            return
            
        # Create a connection dialog with the existing parameters
        from src.ui.connection_dialog import ConnectionDialog
        dialog = ConnectionDialog(self, connection_params)
        
        if dialog.exec():
            # Get the updated parameters
            updated_params = dialog.get_connection_params()
            
            # Update the connection
            self.connection_manager.connection_params[connection_name] = updated_params
            self.connection_manager.save_connections()
            
            # Update the connections menu
            self._populate_connections_menu()
            
            # Update the welcome tab to reflect the changes
            welcome_widget = self._create_welcome_widget()
            self.connection_tabs.removeTab(0)
            self.connection_tabs.insertTab(0, welcome_widget, "Welcome")
            
            # If the connection is currently open, close and reopen it
            for i in range(self.connection_tabs.count()):
                tab = self.connection_tabs.widget(i)
                if tab is not None and hasattr(tab, 'get_connection_name'):
                    # Use getattr to get the method, which will satisfy Pylance
                    get_name_method = getattr(tab, 'get_connection_name')
                    if get_name_method() == connection_name:
                        # Close the connection
                        self.connection_manager.close_connection(connection_name)
                        # Remove the tab
                        self.connection_tabs.removeTab(i)
                    # Show a message to the user
                    QMessageBox.information(
                        self, 
                        "Connection Updated", 
                        f"The connection '{connection_name}' has been updated. You'll need to reconnect to apply the changes."
                    )
                    break
    
    def _open_database_manager(self):
        """Open the database manager dialog"""
        # Get the current connection tab
        current_tab = self.connection_tabs.currentWidget()
        
        # Check if we have an active connection
        if current_tab is None or not hasattr(current_tab, 'connection'):
            QMessageBox.warning(
                self,
                "No Connection",
                "Please connect to a database first before using the Database Manager."
            )
            return
            
        # Get the connection using getattr to satisfy Pylance
        connection = getattr(current_tab, 'connection')
        if not connection:
            QMessageBox.warning(
                self,
                "No Connection",
                "Please connect to a database first before using the Database Manager."
            )
            return
        
        # Create and show the database manager dialog
        # We already have the connection from getattr above
        if not hasattr(current_tab, 'database_manager_dialog'):
            current_tab.database_manager_dialog = None
            
        # Create a new dialog or reuse the existing one
        if current_tab.database_manager_dialog is None:
            current_tab.database_manager_dialog = DatabaseManagerDialog(connection, self)
            
        # Show the dialog
        current_tab.database_manager_dialog.exec()
        
        # Refresh the database browser if it's visible
        if current_tab is not None and hasattr(current_tab, 'database_browser'):
            # Use getattr to get the database_browser, which will satisfy Pylance
            db_browser = getattr(current_tab, 'database_browser')
            db_browser.tree_model.refresh()
    
    def _show_about(self):
        """Show the about dialog"""
        QMessageBox.about(
            self,
            "About DBridge",
            "DBridge - A user-friendly SQL client for Linux\n\n"
            f"Beta Version {__version__}\n\n"
            "A simple, intuitive SQL client for database management.\n"
            "Features tabbed interface for multiple connections and\n"
            "customizable interface with show/hide options for toolbar and database browser.\n\n"
            "Developed by: David Leavitt\n"
            "Email: david@leavitt.pro\n"
            "GitHub: https://github.com/davleav/dbridge\n\n"
            "© 2023-2024 David Leavitt. All rights reserved."
        )
    
    def _import_sql_file(self):
        """Import a SQL file into the current database"""
        # Check if there's an active connection tab
        current_tab = self.connection_tabs.currentWidget()
        if current_tab is None or not hasattr(current_tab, 'connection'):
            QMessageBox.warning(
                self,
                "Import Error",
                "Please connect to a database first before importing."
            )
            return
        
        # Open the import dialog
        # Get the connection using getattr to satisfy Pylance
        connection = getattr(current_tab, 'connection')
        dialog = ImportExportDialog(connection, "import", self)
        if dialog.exec():
            # Refresh the database browser after import
            if current_tab is not None and hasattr(current_tab, 'db_browser'):
                # Use getattr to get the db_browser, which will satisfy Pylance
                db_browser = getattr(current_tab, 'db_browser')
                db_browser.tree_model.refresh()
    
    def _export_database(self):
        """Export the current database"""
        # Check if there's an active connection tab
        current_tab = self.connection_tabs.currentWidget()
        if current_tab is None or not hasattr(current_tab, 'connection'):
            QMessageBox.warning(
                self,
                "Export Error",
                "Please connect to a database first before exporting."
            )
            return
        
        # Open the export dialog
        # Get the connection using getattr to satisfy Pylance
        connection = getattr(current_tab, 'connection')
        dialog = ImportExportDialog(connection, "export", self)
        dialog.exec()
    
    def _show_toolbar_context_menu(self, position):
        """Show context menu for the toolbar"""
        menu = QMenu()
        
        # Add show/hide toolbar action
        action_text = "Hide Main Toolbar" if self.toolbar.isVisible() else "Show Main Toolbar"
        show_action = QAction(action_text, self)
        show_action.setCheckable(True)
        show_action.setChecked(self.toolbar.isVisible())
        show_action.triggered.connect(self._toggle_toolbar)
        
        if menu is not None:
            menu.addAction(show_action)
            menu.exec(self.toolbar.mapToGlobal(position))
    
    def _toggle_toolbar(self):
        """Toggle the visibility of the main toolbar"""
        if self.toolbar.isVisible():
            self.toolbar.hide()
            self.show_toolbar_action.setText("Show Main Toolbar")
            self.show_toolbar_action.setChecked(False)
        else:
            self.toolbar.show()
            self.show_toolbar_action.setText("Hide Main Toolbar")
            self.show_toolbar_action.setChecked(True)
    
    def _toggle_database_browser(self):
        """Toggle the visibility of the database browser in the current connection tab"""
        current_index = self.connection_tabs.currentIndex()
        if current_index >= 0:
            current_tab = self.connection_tabs.widget(current_index)
            if current_tab is not None and hasattr(current_tab, 'toggle_database_browser'):
                # Use getattr to get the method, which will satisfy Pylance
                toggle_method = getattr(current_tab, 'toggle_database_browser')
                visible = toggle_method()
                self.show_db_browser_action.setText("Hide Database Browser" if visible else "Show Database Browser")
                self.show_db_browser_action.setChecked(visible)
            elif current_index > 0:  # Not the welcome tab
                QMessageBox.information(self, "Database Browser", "Database browser not available in this tab.")
    
    # _tab_changed method has been merged with the one at line 442
    
    def _toggle_system_databases(self, checked):
        """Toggle the visibility of system databases application-wide"""
        # Set the global setting - this will emit the signal to all listeners
        self.connection_manager.set_show_system_databases(checked)
        
        # Show a message in the status bar
        if checked:
            self.status_bar.showMessage("System databases are now visible", 3000)
        else:
            self.status_bar.showMessage("System databases are now hidden", 3000)
    
    def _force_refresh_database_views(self):
        """Force refresh all open database views to reflect the system database setting"""
        # Refresh all tabs, not just the current one
        for i in range(self.connection_tabs.count()):
            tab = self.connection_tabs.widget(i)
            
            # Skip the welcome tab
            if self.connection_tabs.tabText(i) == "Welcome":
                continue
                
            # If it's a connection tab, force refresh its database browser
            if hasattr(tab, 'database_browser'):
                # Directly call the _refresh_databases method if it exists
                if hasattr(tab.database_browser, '_refresh_databases'):
                    tab.database_browser._refresh_databases()
                # Otherwise fall back to refreshing the tree model
                elif hasattr(tab.database_browser, 'tree_model'):
                    tab.database_browser.tree_model.refresh()
                    
                    # Expand the database node to show available databases
                    if tab.database_browser.tree_model.rowCount() > 0:
                        root_index = tab.database_browser.tree_model.index(0, 0)
                        tab.database_browser.tree_view.expand(root_index)
                        
                        # If there's a "Available Databases" folder, expand it too
                        for row in range(tab.database_browser.tree_model.rowCount(root_index)):
                            child_index = tab.database_browser.tree_model.index(row, 0, root_index)
                            item_type = tab.database_browser.tree_model.data(child_index, Qt.ItemDataRole.UserRole)
                            if item_type == "databases_folder":
                                tab.database_browser.tree_view.expand(child_index)
                                break
            
            # Also refresh any open database manager dialogs
            if hasattr(tab, 'database_manager_dialog') and tab.database_manager_dialog is not None:
                if tab.database_manager_dialog.isVisible():
                    tab.database_manager_dialog._populate_databases()
                    tab.database_manager_dialog._populate_db_selector()
    
    def _refresh_database_views(self):
        """Refresh all open database views to reflect the system database setting"""
        # This is a less aggressive refresh that doesn't directly call methods
        # Refresh all tabs, not just the current one
        for i in range(self.connection_tabs.count()):
            tab = self.connection_tabs.widget(i)
            
            # Skip the welcome tab
            if self.connection_tabs.tabText(i) == "Welcome":
                continue
                
            # If it's a connection tab, refresh its database browser
            if hasattr(tab, 'database_browser'):
                if hasattr(tab.database_browser, 'tree_model'):
                    # Refresh the tree model
                    tab.database_browser.tree_model.refresh()
                    
                    # Expand the database node to show available databases
                    if tab.database_browser.tree_model.rowCount() > 0:
                        root_index = tab.database_browser.tree_model.index(0, 0)
                        tab.database_browser.tree_view.expand(root_index)
                        
                        # If there's a "Available Databases" folder, expand it too
                        for row in range(tab.database_browser.tree_model.rowCount(root_index)):
                            child_index = tab.database_browser.tree_model.index(row, 0, root_index)
                            item_type = tab.database_browser.tree_model.data(child_index, Qt.ItemDataRole.UserRole)
                            if item_type == "databases_folder":
                                tab.database_browser.tree_view.expand(child_index)
                                break
            
            # Also refresh any open database manager dialogs
            if hasattr(tab, 'database_manager_dialog') and tab.database_manager_dialog is not None:
                if tab.database_manager_dialog.isVisible():
                    tab.database_manager_dialog._populate_databases()
                    tab.database_manager_dialog._populate_db_selector()
    
    def _change_theme(self, theme_name):
        """Change the application theme"""
        if self.theme_manager.set_theme(theme_name):
            # Show a message in the status bar
            self.status_bar.showMessage(f"Theme changed to {theme_name}", 3000)
            
            # Refresh the welcome tab to update the logo
            if self.connection_tabs.count() > 0 and self.connection_tabs.tabText(0) == "Welcome":
                welcome_widget = self._create_welcome_widget()
                self.connection_tabs.removeTab(0)
                self.connection_tabs.insertTab(0, welcome_widget, "Welcome")
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Close all connections
        self.connection_manager.close_all()
        event.accept()