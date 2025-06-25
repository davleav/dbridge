"""
Type stub file for connection_dialog.py
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
    
    def __init__(self, parent=None, connection_params: Optional[Dict[str, Any]] = None) -> None: ...
    
    def _create_ui(self) -> None: ...
    
    def _browse_sqlite_file(self) -> None: ...
    
    def _test_connection(self) -> None: ...
    
    def _validate_connection_input(self) -> bool: ...
    
    def _on_accept(self) -> None: ...
    
    def _populate_fields(self) -> None: ...
    
    def get_connection_params(self) -> Dict[str, Any]: ...