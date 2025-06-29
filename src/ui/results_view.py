"""
Results view for displaying query results
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView,
    QToolBar, QLabel, QComboBox, QPushButton, QFileDialog,
    QHBoxLayout
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QAction

import csv
import pandas as pd

from src.ui.row_detail_dialog import RowDetailDialog

class ResultsTableModel(QAbstractTableModel):
    """Table model for displaying SQL query results"""
    
    def __init__(self, data=None):
        super().__init__()
        self._data = data if data is not None else pd.DataFrame()
    
    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows"""
        if parent.isValid():
            return 0
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns"""
        if parent.isValid():
            return 0
        return len(self._data.columns)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Return the data at the given index"""
        if not index.isValid():
            return None
        
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            # Handle None/NaN values
            if pd.isna(value):
                return "NULL"
            return str(value)
        
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Return the header data"""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(section + 1)
        
        return None
    
    def set_data(self, data):
        """Set the model data"""
        self.beginResetModel()
        self._data = data if data is not None else pd.DataFrame()
        self.endResetModel()


class ResultsView(QWidget):
    """Widget for displaying query results in a table"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar for results actions
        toolbar = QToolBar()
        
        # View details action
        view_details_action = QAction("View Details", self)
        view_details_action.setToolTip("View detailed information for the selected row")
        view_details_action.triggered.connect(self._view_details_action)
        toolbar.addAction(view_details_action)
        
        # Export action
        export_action = QAction("Export", self)
        export_action.setToolTip("Export results to CSV or Excel")
        export_action.triggered.connect(self._export_data)
        toolbar.addAction(export_action)
        
        # Row count label
        toolbar.addSeparator()
        self.row_count_label = QLabel("0 rows")
        toolbar.addWidget(self.row_count_label)
        
        layout.addWidget(toolbar)
        
        # Results table
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        
        # Configure horizontal header with null check
        header = self.table_view.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            header.setStretchLastSection(True)
            
        self.table_view.setToolTip("Double-click on a row to view detailed information")
        
        # Connect double-click signal to show row details
        self.table_view.doubleClicked.connect(self._show_row_details)
        
        self.table_model = ResultsTableModel()
        self.table_view.setModel(self.table_model)
        
        layout.addWidget(self.table_view)
    
    def set_data(self, data):
        """Set the results data"""
        self.table_model.set_data(data)
        self.row_count_label.setText(f"{len(data)} rows")
        
        # Auto-resize columns to content
        self.table_view.resizeColumnsToContents()
    
    def _view_details_action(self):
        """Show details for the currently selected row (triggered from toolbar)"""
        # Get the selected row
        selection_model = self.table_view.selectionModel()
        if selection_model is None:
            return
            
        selected_indexes = selection_model.selectedRows()
        if not selected_indexes:
            # If no row is selected, try to get the current index
            current_index = self.table_view.currentIndex()
            if current_index.isValid():
                self._show_row_details(current_index)
            return
            
        # Use the first selected row
        if selected_indexes:
            self._show_row_details(selected_indexes[0])
    
    def _show_row_details(self, index):
        """Show detailed view of a row when double-clicked"""
        if not index.isValid() or self.table_model.rowCount() == 0:
            return
            
        # Get the row data
        row_index = index.row()
        row_data = []
        column_names = []
        
        # Extract column names and row values
        for col in range(self.table_model.columnCount()):
            column_names.append(str(self.table_model._data.columns[col]))
            value = self.table_model._data.iloc[row_index, col]
            row_data.append(value)
        
        # Create and show the detail dialog
        dialog = RowDetailDialog(row_data, column_names, self)
        
        # Connect the data_updated signal to handle updates
        dialog.data_updated.connect(lambda columns, data: self._update_row_data(row_index, columns, data))
        
        dialog.exec()
    
    def _update_row_data(self, row_index, columns, data):
        """
        Update the row data in the table model
        
        Args:
            row_index: Index of the row to update
            columns: List of column names
            data: List of updated values
        """
        if row_index < 0 or row_index >= self.table_model.rowCount():
            return
            
        # Update the data in the pandas DataFrame
        for col_idx, (col_name, value) in enumerate(zip(columns, data)):
            # Find the column index in the DataFrame
            if col_name in self.table_model._data.columns:
                self.table_model._data.iloc[row_index, col_idx] = value
        
        # Notify the model that data has changed
        top_left = self.table_model.index(row_index, 0)
        bottom_right = self.table_model.index(row_index, self.table_model.columnCount() - 1)
        self.table_model.dataChanged.emit(top_left, bottom_right)
        
        # If we have a connection, update the database
        if hasattr(self, 'connection') and self.connection is not None:
            self._update_database_row(row_index, columns, data)
    
    def _update_database_row(self, row_index, columns, data):
        """
        Update the row in the database
        
        Args:
            row_index: Index of the row to update
            columns: List of column names
            data: List of updated values
        """
        # This method would need to be implemented based on your database structure
        # and how you're executing queries. For now, we'll just log a message.
        print(f"Database update would happen here for row {row_index}")
        print(f"Columns: {columns}")
        print(f"Data: {data}")
        
        # In a real implementation, you would:
        # 1. Get the table name and primary key
        # 2. Build an UPDATE SQL statement
        # 3. Execute the statement with the connection
        
        # Example (pseudocode):
        # table_name = self.current_table
        # primary_key_col = self.get_primary_key_column(table_name)
        # primary_key_val = self.get_primary_key_value(row_index)
        # 
        # update_cols = []
        # update_vals = []
        # for col, val in zip(columns, data):
        #     if col != primary_key_col:  # Don't update the primary key
        #         update_cols.append(col)
        #         update_vals.append(val)
        # 
        # sql = f"UPDATE {table_name} SET "
        # sql += ", ".join([f"{col} = ?" for col in update_cols])
        # sql += f" WHERE {primary_key_col} = ?"
        # 
        # params = update_vals + [primary_key_val]
        # self.connection.execute(sql, params)
        # self.connection.commit()
    
    def _export_data(self):
        """Export the results data to a file"""
        if self.table_model.rowCount() == 0:
            return
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            data = self.table_model._data
            
            if file_path.endswith('.csv'):
                data.to_csv(file_path, index=False)
            elif file_path.endswith('.xlsx'):
                data.to_excel(file_path, index=False)
            else:
                # Default to CSV if no extension is specified
                if '.' not in file_path:
                    file_path += '.csv'
                data.to_csv(file_path, index=False)
        except Exception as e:
            print(f"Export error: {e}")