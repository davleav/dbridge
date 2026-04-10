"""
Results view for displaying query results
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView,
    QToolBar, QLabel, QPushButton, QFileDialog,
    QHBoxLayout, QTabWidget, QTreeView, QMenu
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QAction, QFont, QStandardItemModel, QStandardItem

import csv
import json
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
            try:
                if pd.isna(value):
                    return "NULL"
            except (TypeError, ValueError):
                pass
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


class MongoDocumentTreeModel(QStandardItemModel):
    """Tree model for displaying MongoDB documents in a hierarchical view"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(["Field", "Value"])

    def populate(self, data):
        """Populate the tree with MongoDB documents from a DataFrame"""
        self.clear()
        self.setHorizontalHeaderLabels(["Field", "Value"])

        for i in range(len(data)):
            _id_str = ""
            if '_id' in data.columns:
                _id_val = data.iloc[i]['_id']
                try:
                    if not pd.isna(_id_val):
                        _id_str = f" ({_id_val})"
                except (TypeError, ValueError):
                    _id_str = f" ({_id_val})"

            doc_item = QStandardItem(f"Document {i + 1}{_id_str}")
            doc_item.setData(i, Qt.ItemDataRole.UserRole)
            doc_item.setEditable(False)
            val_placeholder = QStandardItem("")
            val_placeholder.setEditable(False)

            for col in data.columns:
                value = data.iloc[i][col]
                try:
                    if pd.isna(value):
                        value = None
                except (TypeError, ValueError):
                    pass
                self._add_field(doc_item, str(col), value)

            self.appendRow([doc_item, val_placeholder])

    def _add_field(self, parent_item, key, value):
        """Recursively add a field to a parent item"""
        key_item = QStandardItem(str(key))
        key_item.setEditable(False)

        if isinstance(value, dict):
            val_item = QStandardItem("{...}")
            val_item.setEditable(False)
            for k, v in value.items():
                self._add_field(key_item, str(k), v)
        elif isinstance(value, list):
            val_item = QStandardItem(f"[{len(value)} items]")
            val_item.setEditable(False)
            for idx, v in enumerate(value):
                self._add_field(key_item, str(idx), v)
        elif value is None:
            val_item = QStandardItem("null")
            val_item.setEditable(False)
        else:
            val_item = QStandardItem(str(value))
            val_item.setEditable(False)

        parent_item.appendRow([key_item, val_item])


class ResultsView(QWidget):
    """Widget for displaying query results in a table"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.connection = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        toolbar = QToolBar()
        
        view_details_action = QAction("View Details", self)
        view_details_action.setToolTip("View detailed information for the selected row")
        view_details_action.triggered.connect(self._view_details_action)
        toolbar.addAction(view_details_action)
        
        export_action = QAction("Export", self)
        export_action.setToolTip("Export results to CSV or Excel")
        export_action.triggered.connect(self._export_data)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        self.row_count_label = QLabel("0 rows")
        toolbar.addWidget(self.row_count_label)
        
        layout.addWidget(toolbar)
        
        self.view_tabs = QTabWidget()

        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        
        header = self.table_view.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            header.setStretchLastSection(True)
            
        self.table_view.setToolTip("Double-click on a row to view detailed information")
        
        self.table_view.doubleClicked.connect(self._show_row_details)
        self.table_view.clicked.connect(self._on_table_row_clicked)
        
        self.table_model = ResultsTableModel()
        self.table_view.setModel(self.table_model)

        self.view_tabs.addTab(self.table_view, "Table")

        self.mongo_tree_model = MongoDocumentTreeModel()
        self.mongo_tree_view = QTreeView()
        self.mongo_tree_view.setModel(self.mongo_tree_model)
        self.mongo_tree_view.setAlternatingRowColors(True)
        self.mongo_tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.mongo_tree_view.customContextMenuRequested.connect(self._show_tree_context_menu)
        self.mongo_tree_view.doubleClicked.connect(self._tree_view_double_clicked)

        tree_header = self.mongo_tree_view.header()
        if tree_header is not None:
            tree_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            tree_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.view_tabs.addTab(self.mongo_tree_view, "Document Tree")

        layout.addWidget(self.view_tabs)
    
    def set_data(self, data):
        """Set the results data"""
        self.table_model.set_data(data)
        self.row_count_label.setText(f"{len(data)} rows")

        is_mongodb = (
            self.connection is not None
            and hasattr(self.connection, 'params')
            and self.connection.params.get('type') == 'MongoDB'
        )

        if is_mongodb and len(data) > 0:
            self.mongo_tree_model.populate(data)
            self.mongo_tree_view.expandToDepth(0)
            self.view_tabs.setCurrentIndex(1)
        else:
            self.mongo_tree_model.clear()
            self.mongo_tree_model.setHorizontalHeaderLabels(["Field", "Value"])

        self.table_view.resizeColumnsToContents()

    def _on_table_row_clicked(self, index):
        """Sync tree view selection when a row is clicked in the table view"""
        if not index.isValid() or self.table_model.rowCount() == 0:
            return

        is_mongodb = (
            self.connection is not None
            and hasattr(self.connection, 'params')
            and self.connection.params.get('type') == 'MongoDB'
        )

        if not is_mongodb:
            return

        row_index = index.row()
        tree_index = self.mongo_tree_model.index(row_index, 0)
        if tree_index.isValid():
            self.mongo_tree_view.setCurrentIndex(tree_index)
            self.mongo_tree_view.scrollTo(tree_index)

    def _get_tree_selected_row_index(self):
        """Return the DataFrame row index for the currently selected tree item, or None"""
        sel_model = self.mongo_tree_view.selectionModel()
        if sel_model is None:
            return None

        indexes = sel_model.selectedIndexes()
        if not indexes:
            current = self.mongo_tree_view.currentIndex()
            if not current.isValid():
                return None
            indexes = [current]

        index = indexes[0]
        item = self.mongo_tree_model.itemFromIndex(index)
        if item is None:
            return None

        while item.parent() is not None:
            item = item.parent()

        row_data = item.data(Qt.ItemDataRole.UserRole)
        if row_data is None:
            return None
        return int(row_data)

    def _tree_view_double_clicked(self, index):
        """Open view details dialog when a tree item is double-clicked"""
        if not index.isValid():
            return

        item = self.mongo_tree_model.itemFromIndex(index)
        if item is None:
            return

        while item.parent() is not None:
            item = item.parent()

        row_index = item.data(Qt.ItemDataRole.UserRole)
        if row_index is None:
            return

        self._show_row_details_for_index(int(row_index))

    def _show_tree_context_menu(self, position):
        """Show a context menu for tree view items"""
        index = self.mongo_tree_view.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)
        view_details_action = menu.addAction("View Details")
        action = menu.exec(self.mongo_tree_view.viewport().mapToGlobal(position))
        if action == view_details_action:
            self._tree_view_double_clicked(index)
        
    def set_connection(self, connection):
        """Set the database connection for this results view"""
        self.connection = connection
    
    def _view_details_action(self):
        """Show details for the currently selected row (triggered from toolbar)"""
        current_tab = self.view_tabs.currentIndex()

        if current_tab == 1:
            row_index = self._get_tree_selected_row_index()
            if row_index is not None:
                self._show_row_details_for_index(row_index)
            return

        selection_model = self.table_view.selectionModel()
        if selection_model is None:
            return
            
        selected_indexes = selection_model.selectedRows()
        if not selected_indexes:
            current_index = self.table_view.currentIndex()
            if current_index.isValid():
                self._show_row_details(current_index)
            return
            
        if selected_indexes:
            self._show_row_details(selected_indexes[0])

    def _show_row_details_for_index(self, row_index):
        """Show detailed view for a given DataFrame row index"""
        if row_index < 0 or row_index >= self.table_model.rowCount():
            return

        row_data = []
        column_names = []

        for col in range(self.table_model.columnCount()):
            column_names.append(str(self.table_model._data.columns[col]))
            value = self.table_model._data.iloc[row_index, col]
            row_data.append(value)

        dialog = RowDetailDialog(row_data, column_names, self)
        dialog.data_updated.connect(lambda columns, data: self._update_row_data(row_index, columns, data))
        dialog.exec()
    
    def _show_row_details(self, index):
        """Show detailed view of a row when double-clicked"""
        if not index.isValid() or self.table_model.rowCount() == 0:
            return
            
        self._show_row_details_for_index(index.row())
    
    def _update_row_data(self, row_index, columns, data):
        """Update the row data in the table model"""
        if row_index < 0 or row_index >= self.table_model.rowCount():
            return
            
        for col_idx, (col_name, value) in enumerate(zip(columns, data)):
            if col_name in self.table_model._data.columns:
                self.table_model._data.iloc[row_index, col_idx] = value
        
        top_left = self.table_model.index(row_index, 0)
        bottom_right = self.table_model.index(row_index, self.table_model.columnCount() - 1)
        self.table_model.dataChanged.emit(top_left, bottom_right)
        
        if hasattr(self, 'connection') and self.connection is not None:
            self._update_database_row(row_index, columns, data)
    
    def _update_database_row(self, row_index, columns, data):
        """Update the row in the database"""
        print(f"Database update would happen here for row {row_index}")
        print(f"Columns: {columns}")
        print(f"Data: {data}")
    
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
                if '.' not in file_path:
                    file_path += '.csv'
                data.to_csv(file_path, index=False)
        except Exception as e:
            print(f"Export error: {e}")
