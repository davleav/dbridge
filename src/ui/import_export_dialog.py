"""
Dialog for database import and export operations
"""

import os
import subprocess

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFileDialog, QListWidget, QCheckBox,
    QRadioButton, QButtonGroup, QGroupBox, QMessageBox,
    QProgressDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QSize

class ImportExportDialog(QDialog):
    """Dialog for importing and exporting database data"""
    
    def __init__(self, connection, mode="export", parent=None):
        """
        Initialize the dialog
        
        Args:
            connection: The database connection
            mode (str): Either "export" or "import"
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.connection = connection
        self.mode = mode
        self.selected_tables = []
        self.file_path = ""
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI components"""
        if self.mode == "export":
            self.setWindowTitle("Export Database")
            self.setMinimumSize(500, 400)
        else:
            self.setWindowTitle("Import SQL File")
            self.setMinimumSize(500, 200)
        
        layout = QVBoxLayout(self)
        
        # Export-specific UI
        if self.mode == "export":
            # Export options
            export_options_group = QGroupBox("Export Options")
            export_options_layout = QVBoxLayout(export_options_group)
            
            # Export scope selection
            scope_layout = QHBoxLayout()
            scope_layout.addWidget(QLabel("Export:"))
            
            self.scope_group = QButtonGroup(self)
            
            self.full_db_radio = QRadioButton("Entire Database")
            self.full_db_radio.setChecked(True)
            self.full_db_radio.toggled.connect(self._toggle_table_selection)
            self.scope_group.addButton(self.full_db_radio)
            scope_layout.addWidget(self.full_db_radio)
            
            self.selected_tables_radio = QRadioButton("Selected Tables")
            self.selected_tables_radio.toggled.connect(self._toggle_table_selection)
            self.scope_group.addButton(self.selected_tables_radio)
            scope_layout.addWidget(self.selected_tables_radio)
            
            scope_layout.addStretch()
            export_options_layout.addLayout(scope_layout)
            
            # Table selection
            self.tables_list = QListWidget()
            self.tables_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            self.tables_list.setEnabled(False)
            
            # Populate the table list
            for table in self.connection.get_tables():
                self.tables_list.addItem(table)
            
            export_options_layout.addWidget(self.tables_list)
            
            layout.addWidget(export_options_group)
        
        # File selection
        file_layout = QHBoxLayout()
        
        if self.mode == "export":
            file_layout.addWidget(QLabel("Export to:"))
            self.browse_button = QPushButton("Browse...")
        else:
            file_layout.addWidget(QLabel("Import from:"))
            self.browse_button = QPushButton("Browse...")
        
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_button)
        
        self.file_path_label = QLabel("No file selected")
        file_layout.addWidget(self.file_path_label, 1)
        
        layout.addLayout(file_layout)
        
        # Format selection for export
        if self.mode == "export":
            format_layout = QHBoxLayout()
            format_layout.addWidget(QLabel("Format:"))
            
            self.format_combo = QComboBox()
            self.format_combo.addItem("SQL", "sql")
            self.format_combo.addItem("CSV", "csv")
            self.format_combo.addItem("Excel", "xlsx")
            self.format_combo.currentIndexChanged.connect(self._update_file_extension)
            format_layout.addWidget(self.format_combo)
            
            format_layout.addStretch()
            layout.addLayout(format_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        if self.mode == "export":
            self.export_button = QPushButton("Export")
            self.export_button.clicked.connect(self._handle_export)
            button_layout.addWidget(self.export_button)
        else:
            self.import_button = QPushButton("Import")
            self.import_button.clicked.connect(self._handle_import)
            button_layout.addWidget(self.import_button)
        
        layout.addLayout(button_layout)
    
    def _toggle_table_selection(self, checked):
        """Enable/disable table selection based on radio button state"""
        self.tables_list.setEnabled(self.selected_tables_radio.isChecked())
        
    def _update_file_extension(self, index):
        """Update the file path when the format changes"""
        if not self.file_path:
            return
            
        # Get the new format
        format_data = self.format_combo.itemData(index)
        
        # Only update if we have a file path already
        if self.file_path:
            # Get the directory and base filename without extension
            directory = os.path.dirname(self.file_path)
            filename = os.path.basename(self.file_path)
            base_name = os.path.splitext(filename)[0]
            
            # Create new filename with the new extension
            new_filename = f"{base_name}.{format_data}"
            new_path = os.path.join(directory, new_filename)
            
            # Update the file path
            self.file_path = new_path
            self.file_path_label.setText(new_path)
    
    def _browse_file(self):
        """Open file dialog to select a file or directory"""
        if self.mode == "export":
            # First, select a directory
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Export Directory",
                ""
            )
            
            if not directory:
                return
                
            # Get the current format
            format_index = self.format_combo.currentIndex()
            format_data = self.format_combo.itemData(format_index)
            
            # Set default extension based on format
            if format_data == "sql":
                extension = "sql"
                filter_text = "SQL Files (*.sql)"
            elif format_data == "csv":
                extension = "csv"
                filter_text = "CSV Files (*.csv)"
            elif format_data == "xlsx":
                extension = "xlsx"
                filter_text = "Excel Files (*.xlsx)"
            
            # Now, get a filename
            filename, ok = QInputDialog.getText(
                self,
                "Enter Filename",
                f"Enter filename (with .{extension} extension):",
                text=f"export.{extension}"
            )
            
            if not ok or not filename:
                return
                
            # Add extension if not present
            if not filename.lower().endswith(f".{extension}"):
                filename = f"{filename}.{extension}"
                
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
        else:
            # For import, use the standard file open dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import SQL File",
                "",
                "SQL Files (*.sql);;All Files (*)"
            )
        
        if file_path:
            self.file_path = file_path
            self.file_path_label.setText(file_path)
            
            # Update format combo based on file extension for export
            if self.mode == "export":
                extension = file_path.split('.')[-1].lower()
                if extension == "sql":
                    self.format_combo.setCurrentIndex(0)
                elif extension == "csv":
                    self.format_combo.setCurrentIndex(1)
                elif extension in ["xlsx", "xls"]:
                    self.format_combo.setCurrentIndex(2)
    
    def _handle_export(self):
        """Handle the export operation"""
        if not self.file_path:
            QMessageBox.warning(self, "Export Error", "Please select a file to export to.")
            return
        
        try:
            # Get selected format
            format_data = self.format_combo.currentData()
            
            # Get selected tables if applicable
            tables = None
            if self.selected_tables_radio.isChecked():
                tables = [item.text() for item in self.tables_list.selectedItems()]
                if not tables:
                    QMessageBox.warning(self, "Export Error", "Please select at least one table to export.")
                    return
            
            # Show progress dialog
            progress = QProgressDialog("Exporting database...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setValue(10)
            
            # Perform export based on format
            if format_data == "sql":
                # SQL export
                db_type = self.connection.params['type']
                progress.setLabelText(f"Exporting database as SQL ({db_type})...")
                # File existence is already checked in _browse_file
                self.connection.export_database_to_sql(self.file_path, tables)
            else:
                # CSV or Excel export
                if tables is None:
                    # Export all tables
                    tables = self.connection.get_tables()
                
                if len(tables) == 1:
                    # Single table export
                    table = tables[0]
                    progress.setLabelText(f"Fetching data from {table}...")
                    data = self.connection.execute_query(f"SELECT * FROM {table}")
                    
                    progress.setValue(50)
                    progress.setLabelText(f"Writing {format_data.upper()} file...")
                    
                    # File existence is already checked in _browse_file
                    if format_data == "csv":
                        data.to_csv(self.file_path, index=False)
                    else:  # xlsx
                        data.to_excel(self.file_path, index=False)
                else:
                    # Multiple tables export
                    import pandas as pd
                    
                    if format_data == "csv":
                        # For CSV, we'll create a zip file containing multiple CSVs
                        import zipfile
                        import os
                        
                        # Change extension to .zip
                        directory = os.path.dirname(self.file_path)
                        filename = os.path.basename(self.file_path)
                        base_name = os.path.splitext(filename)[0]
                        zip_path = os.path.join(directory, f"{base_name}.zip")
                        
                        # Check if zip file exists and confirm overwrite
                        if os.path.exists(zip_path):
                            confirm = QMessageBox.question(
                                self,
                                "File Exists",
                                f"The file '{os.path.basename(zip_path)}' already exists. Do you want to replace it?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No
                            )
                            
                            if confirm != QMessageBox.StandardButton.Yes:
                                return
                        
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            total_tables = len(tables)
                            for i, table in enumerate(tables):
                                # Update progress
                                progress_value = 10 + int(80 * (i / total_tables))
                                progress.setValue(progress_value)
                                progress.setLabelText(f"Exporting table: {table} ({i+1}/{total_tables})")
                                
                                data = self.connection.execute_query(f"SELECT * FROM {table}")
                                
                                # Create a temporary CSV file
                                temp_csv = os.path.join(os.path.dirname(self.file_path), f"{table}.csv")
                                data.to_csv(temp_csv, index=False)
                                
                                # Add to zip and remove temp file
                                zipf.write(temp_csv, f"{table}.csv")
                                os.remove(temp_csv)
                        
                        self.file_path = zip_path
                    else:  # xlsx
                        # For Excel, we'll create a workbook with multiple sheets
                        # File existence is already checked in _browse_file
                        with pd.ExcelWriter(self.file_path) as writer:
                            total_tables = len(tables)
                            for i, table in enumerate(tables):
                                # Update progress
                                progress_value = 10 + int(80 * (i / total_tables))
                                progress.setValue(progress_value)
                                progress.setLabelText(f"Exporting table: {table} ({i+1}/{total_tables})")
                                
                                data = self.connection.execute_query(f"SELECT * FROM {table}")
                                data.to_excel(writer, sheet_name=table[:31], index=False)  # Excel limits sheet names to 31 chars
            
            progress.setValue(100)
            
            QMessageBox.information(self, "Export Complete", f"Database exported successfully to {self.file_path}")
            self.accept()
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
            error_msg = f"Failed to export database: {str(e)}"
            QMessageBox.critical(self, "Export Error", error_msg)
    
    def _handle_import(self):
        """Handle the import operation"""
        if not self.file_path:
            QMessageBox.warning(self, "Import Error", "Please select a file to import.")
            return
        
        # Confirm import
        confirm = QMessageBox.question(
            self,
            "Confirm Import",
            "Importing SQL may modify or delete existing data. Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Show progress dialog
            progress = QProgressDialog("Importing SQL file...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setValue(10)
            
            # Update progress dialog with database type
            db_type = self.connection.params['type']
            progress.setLabelText(f"Importing SQL file into {db_type} database...")
            
            # Perform import
            self.connection.import_sql_file(self.file_path)
            
            progress.setValue(100)
            
            QMessageBox.information(self, "Import Complete", "SQL file imported successfully.")
            self.accept()
        except subprocess.CalledProcessError as e:
            # Handle command-line tool errors
            error_msg = f"Import failed with error code {e.returncode}.\n\n"
            
            if hasattr(e, 'stderr') and e.stderr:
                error_details = e.stderr.decode('utf-8', errors='replace')
                error_msg += f"Error details:\n{error_details}"
            else:
                error_msg += "No additional error details available."
            
            QMessageBox.critical(self, "Import Error", error_msg)
        except Exception as e:
            # Handle other errors
            error_msg = f"Failed to import SQL file: {str(e)}"
            QMessageBox.critical(self, "Import Error", error_msg)