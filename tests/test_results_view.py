"""
Tests for the query results view
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock, call
from typing import List, Dict, Any, Optional

import pandas as pd
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt, QModelIndex, QPoint

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.ui.results_view import ResultsView, ResultsTableModel
from src.ui.row_detail_dialog import RowDetailDialog


class TestResultsTableModel(unittest.TestCase):
    """Test cases for the ResultsTableModel class"""
    
    # Add type annotations for instance attributes
    df_test_data: pd.DataFrame  # Renamed to avoid conflict with test_data method
    model: ResultsTableModel
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a test DataFrame
        self.df_test_data = pd.DataFrame({  # Renamed to avoid conflict with test_data method
            'id': [1, 2, 3],
            'name': ['Test1', 'Test2', 'Test3'],
            'value': [10.5, 20.5, None]
        })
        
        self.model = ResultsTableModel(self.df_test_data)
    
    def test_row_count(self):
        """Test the rowCount method"""
        self.assertEqual(self.model.rowCount(), 3)
        
        # Test with an invalid parent
        invalid_parent = QModelIndex()  # This is actually a valid root index in Qt6
        self.assertEqual(self.model.rowCount(invalid_parent), 3)
    
    def test_column_count(self):
        """Test the columnCount method"""
        self.assertEqual(self.model.columnCount(), 3)
        
        # Test with an invalid parent
        invalid_parent = QModelIndex()  # This is actually a valid root index in Qt6
        self.assertEqual(self.model.columnCount(invalid_parent), 3)
    
    def test_data(self):
        """Test the data method"""
        # Test valid data
        index = self.model.index(0, 0)
        self.assertEqual(self.model.data(index), "1")
        
        index = self.model.index(1, 1)
        self.assertEqual(self.model.data(index), "Test2")
        
        # Test None/NaN value
        index = self.model.index(2, 2)
        self.assertEqual(self.model.data(index), "NULL")
        
        # Test invalid index
        invalid_index = QModelIndex()
        self.assertIsNone(self.model.data(invalid_index))
        
        # Test with a role other than DisplayRole
        self.assertIsNone(self.model.data(index, Qt.ItemDataRole.EditRole))
    
    def test_header_data(self):
        """Test the headerData method"""
        # Test horizontal headers (column names)
        self.assertEqual(self.model.headerData(0, Qt.Orientation.Horizontal), "id")
        self.assertEqual(self.model.headerData(1, Qt.Orientation.Horizontal), "name")
        self.assertEqual(self.model.headerData(2, Qt.Orientation.Horizontal), "value")
        
        # Test vertical headers (row numbers)
        self.assertEqual(self.model.headerData(0, Qt.Orientation.Vertical), "1")
        self.assertEqual(self.model.headerData(1, Qt.Orientation.Vertical), "2")
        
        # Test with a role other than DisplayRole
        self.assertIsNone(self.model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.EditRole))
    
    def test_set_data(self):
        """Test the set_data method"""
        # Create a new test DataFrame
        new_data = pd.DataFrame({
            'col1': [1, 2],
            'col2': ['A', 'B']
        })
        
        # Set the new data
        self.model.set_data(new_data)
        
        # Check that the model was updated
        self.assertEqual(self.model.rowCount(), 2)
        self.assertEqual(self.model.columnCount(), 2)
        self.assertEqual(self.model.headerData(0, Qt.Orientation.Horizontal), "col1")
        self.assertEqual(self.model.data(self.model.index(0, 1)), "A")
        
        # Test setting None
        self.model.set_data(None)
        self.assertEqual(self.model.rowCount(), 0)
        self.assertEqual(self.model.columnCount(), 0)


class TestResultsView(unittest.TestCase):
    """Test cases for the ResultsView class"""
    
    # Add type annotations for instance attributes
    results_view: ResultsView
    test_data: pd.DataFrame
    
    def setUp(self):
        """Set up test fixtures"""
        self.results_view = ResultsView()
        
        # Create a test DataFrame
        self.test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Test1', 'Test2', 'Test3'],
            'value': [10.5, 20.5, 30.5]
        })
    
    def test_ui_components_created(self):
        """Test that UI components were created"""
        self.assertIsNotNone(self.results_view.table_view)
        self.assertIsNotNone(self.results_view.table_model)
        self.assertIsNotNone(self.results_view.row_count_label)
        
        # Check that the table view has a tooltip about double-clicking
        self.assertIn("Double-click", self.results_view.table_view.toolTip())
    
    def test_set_data(self):
        """Test setting data in the view"""
        # Set the test data
        self.results_view.set_data(self.test_data)
        
        # Check that the model was updated
        self.assertEqual(self.results_view.table_model.rowCount(), 3)
        self.assertEqual(self.results_view.table_model.columnCount(), 3)
        
        # Check that the row count label was updated
        self.assertEqual(self.results_view.row_count_label.text(), "3 rows")
    
    @patch('src.ui.results_view.RowDetailDialog')
    def test_show_row_details(self, mock_dialog):
        """Test showing row details when a row is double-clicked"""
        # Set up the mock dialog
        mock_dialog_instance = MagicMock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Set the test data
        self.results_view.set_data(self.test_data)
        
        # Create a model index for the first row
        index = self.results_view.table_model.index(0, 0)
        
        # Call the show row details method
        self.results_view._show_row_details(index)
        
        # Check that the dialog was created with the correct data
        mock_dialog.assert_called_once()
        args, kwargs = mock_dialog.call_args
        
        # Check that the row data and column names were passed correctly
        self.assertEqual(len(args[0]), 3)  # 3 columns
        self.assertEqual(args[0][0], 1)    # First value in row
        self.assertEqual(args[0][1], 'Test1')  # Second value in row
        self.assertEqual(args[0][2], 10.5)  # Third value in row
        
        self.assertEqual(len(args[1]), 3)  # 3 column names
        self.assertEqual(args[1][0], 'id')
        self.assertEqual(args[1][1], 'name')
        self.assertEqual(args[1][2], 'value')
        
        # Check that the data_updated signal is connected
        self.assertEqual(mock_dialog_instance.data_updated.connect.call_count, 1)
        
        # Check that the dialog's exec method was called
        mock_dialog_instance.exec.assert_called_once()
        
        # Test with an invalid index
        invalid_index = QModelIndex()
        self.results_view._show_row_details(invalid_index)
        
        # The dialog should not be created again
        self.assertEqual(mock_dialog.call_count, 1)
    
    @patch('src.ui.results_view.RowDetailDialog')
    def test_view_details_action(self, mock_dialog):
        """Test the view details action from the toolbar"""
        # Set up the mock dialog
        mock_dialog_instance = MagicMock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Set the test data
        self.results_view.set_data(self.test_data)
        
        # Mock the selection model
        mock_selection_model = MagicMock()
        self.results_view.table_view.selectionModel = MagicMock(return_value=mock_selection_model)
        
        # Create a model index for the first row
        index = self.results_view.table_model.index(0, 0)
        
        # Set up the selection model to return our index
        mock_selection_model.selectedRows.return_value = [index]
        
        # Call the view details action
        self.results_view._view_details_action()
        
        # Check that the dialog was created with the correct data
        mock_dialog.assert_called_once()
        
        # Check that the dialog's exec method was called
        mock_dialog_instance.exec.assert_called_once()
        
        # Test with no selection
        mock_dialog.reset_mock()
        mock_dialog_instance.exec.reset_mock()
        mock_selection_model.selectedRows.return_value = []
        
        # Mock the current index
        self.results_view.table_view.currentIndex = MagicMock(return_value=index)
        
        # Call the view details action again
        self.results_view._view_details_action()
        
        # Check that the dialog was created with the correct data
        mock_dialog.assert_called_once()
        
        # Check that the dialog's exec method was called
        mock_dialog_instance.exec.assert_called_once()
        
        # Test with no selection and no current index
        mock_dialog.reset_mock()
        mock_dialog_instance.exec.reset_mock()
        mock_selection_model.selectedRows.return_value = []
        
        # Mock an invalid current index
        invalid_index = QModelIndex()
        self.results_view.table_view.currentIndex = MagicMock(return_value=invalid_index)
        
        # Call the view details action again
        self.results_view._view_details_action()
        
        # The dialog should not be created
        mock_dialog.assert_not_called()
    
    def test_update_row_data(self):
        """Test updating row data from the row detail dialog"""
        # Set the test data
        self.results_view.set_data(self.test_data)
        
        # Define the row index and updated data
        row_index = 1
        columns = ['id', 'name', 'value']
        updated_data = [2, 'Updated Name', 20.5]
        
        # Mock the dataChanged signal
        with patch.object(self.results_view.table_model, 'dataChanged') as mock_data_changed:
            # Call the update method
            self.results_view._update_row_data(row_index, columns, updated_data)
            
            # Check that the data was updated in the model
            self.assertEqual(self.results_view.table_model._data.iloc[row_index, 0], 2)
            self.assertEqual(self.results_view.table_model._data.iloc[row_index, 1], 'Updated Name')
            self.assertEqual(self.results_view.table_model._data.iloc[row_index, 2], 20.5)
            
            # Check that the dataChanged signal was emitted
            mock_data_changed.emit.assert_called_once()
    
    def test_update_database_row(self):
        """Test the database update method"""
        # Set the test data
        self.results_view.set_data(self.test_data)
        
        # Define the row index and updated data
        row_index = 1
        columns = ['id', 'name', 'value']
        updated_data = [2, 'Updated Name', 20.5]
        
        # Mock print to check the output
        with patch('builtins.print') as mock_print:
            # Call the update method
            self.results_view._update_database_row(row_index, columns, updated_data)
            
            # Check that the print statements were called with the correct data
            mock_print.assert_any_call(f"Database update would happen here for row {row_index}")
            mock_print.assert_any_call(f"Columns: {columns}")
            mock_print.assert_any_call(f"Data: {updated_data}")
    
    def test_export_data(self):
        """Test exporting data to a file"""
        # Set the test data
        self.results_view.set_data(self.test_data)
        
        # Mock QFileDialog.getSaveFileName to return a test file path
        with tempfile.NamedTemporaryFile(suffix='.csv') as temp_file:
            with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
                      return_value=(temp_file.name, "CSV Files (*.csv)")) as mock_dialog:
                
                # Call the export method
                self.results_view._export_data()
                
                # Check that the dialog was shown
                mock_dialog.assert_called_once()
                
                # Check that the file was created with the correct content
                df = pd.read_csv(temp_file.name)
                pd.testing.assert_frame_equal(df, self.test_data)
        
        # Test with no data
        empty_view = ResultsView()
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            # Call the export method
            empty_view._export_data()
            
            # Check that the dialog was not shown
            mock_dialog.assert_not_called()


if __name__ == '__main__':
    unittest.main()