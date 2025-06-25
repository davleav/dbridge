"""
Dialog for displaying detailed row data in a list format
"""

import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFormLayout, QTextEdit, QDialogButtonBox,
    QApplication, QSizePolicy, QSplitter, QSlider, QFrame, QToolButton
)
from PyQt6.QtCore import Qt, QSize, QEvent
from PyQt6.QtGui import QFont, QAction, QKeySequence, QIcon, QPalette
from PyQt6.QtGui import QShowEvent

class RowDetailDialog(QDialog):
    """Dialog for displaying detailed row data in a list format"""
    
    def __init__(self, row_data, column_names, parent=None):
        """
        Initialize the dialog with row data
        
        Args:
            row_data: List of values for the row
            column_names: List of column names
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.row_data = row_data
        self.column_names = column_names
        self.value_edits = []  # Store references to value editors
        self.raw_content = {}  # Store raw content for toggling
        self.is_rendered = {}  # Track rendering state for each field
        
        self.setWindowTitle("Row Details")
        self.resize(700, 600)  # Set a reasonable default size
        self.setMinimumSize(500, 400)  # Set minimum size
        self.setSizeGripEnabled(True)  # Enable size grip for easy resizing
        
        self._create_ui()
        self._setup_shortcuts()
    
    def _contains_html(self, text):
        """
        Check if the text contains HTML markup
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if the text contains HTML markup
        """
        if not isinstance(text, str):
            return False
            
        # Simple pattern to detect HTML tags
        html_pattern = r'<[a-zA-Z][^>]*>|</[a-zA-Z][^>]*>'
        return bool(re.search(html_pattern, text))
    
    def _contains_markdown(self, text):
        """
        Check if the text contains Markdown formatting
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if the text contains Markdown formatting
        """
        if not isinstance(text, str):
            return False
            
        # Check for common Markdown patterns
        md_patterns = [
            r'\[.+?\]\(.+?\)',  # Links
            r'!\[.+?\]\(.+?\)',  # Images
            r'#{1,6}\s+.+',     # Headers
            r'\*\*.+?\*\*',     # Bold
            r'__.+?__',         # Bold
            r'\*.+?\*',         # Italic
            r'_.+?_',           # Italic
            r'```[\s\S]*?```',  # Code blocks
            r'`[^`]+`',         # Inline code
            r'^\s*[-*+]\s+',    # Unordered lists
            r'^\s*\d+\.\s+',    # Ordered lists
            r'^\s*>\s+'         # Blockquotes
        ]
        
        for pattern in md_patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
                
        return False
    
    def _has_formatting(self, text):
        """
        Check if the text contains HTML or Markdown formatting
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if the text contains formatting
        """
        if not isinstance(text, str):
            return False
            
        return self._contains_html(text) or self._contains_markdown(text)
    
    def _toggle_rendering(self, index):
        """
        Toggle between rendered and raw view for a field
        
        Args:
            index: Index of the field to toggle
        """
        if index not in self.is_rendered:
            return
            
        # Toggle the rendering state
        self.is_rendered[index] = not self.is_rendered[index]
        
        # Get the text edit widget
        text_edit = self.value_edits[index]
        
        # Find the toggle button for this field
        toggle_button = None
        row_container = text_edit.parent()
        if row_container:
            for button in row_container.findChildren(QToolButton):
                # We assume the first tool button in the row container is our toggle button
                toggle_button = button
                break
        
        # Get the current theme
        app = QApplication.instance()
        is_dark_theme = False
        if app:
            palette = app.palette()
            is_dark_theme = palette.color(QPalette.ColorRole.Window).lightness() < 128
        
        # Save the current stylesheet
        current_style = text_edit.styleSheet()
        
        if self.is_rendered[index]:
            # Switch to rendered view
            text_edit.setHtml(self.raw_content[index])
            if toggle_button:
                toggle_button.setText("Raw")
        else:
            # Switch to raw view
            text_edit.setPlainText(self.raw_content[index])
            if toggle_button:
                toggle_button.setText("Render")
        
        # Reapply the stylesheet to ensure theme consistency
        if is_dark_theme:
            text_edit.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #555;
                    border-radius: 2px;
                    background-color: #252525;
                    color: #FFFFFF;
                }
            """)
        else:
            text_edit.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #999;
                    border-radius: 2px;
                    background-color: #f8f8f8;
                }
            """)
    
    def _create_ui(self):
        """Create the UI components"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Row Details")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Create a vertical splitter to hold all the rows
        # This allows each row to be resized independently
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setChildrenCollapsible(False)  # Prevent collapsing sections
        main_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)  # Allow vertical expansion
        
        # Add each field to the splitter
        for i, (column, value) in enumerate(zip(self.column_names, self.row_data)):
            # Create a container for each row
            row_container = QWidget()
            row_layout = QVBoxLayout(row_container)
            row_layout.setContentsMargins(10, 5, 10, 5)
            row_layout.setSpacing(5)
            
            # Create a header layout for the column name and toggle button
            header_layout = QHBoxLayout()
            
            # Create label for the column name
            label = QLabel(f"{column}:")
            label_font = QFont()
            label_font.setBold(True)
            label.setFont(label_font)
            header_layout.addWidget(label)
            
            # Create a text edit for the value
            value_edit = QTextEdit()
            value_edit.setReadOnly(True)
            value_edit.setProperty("column_name", column)  # Store column name for reference
            
            # Configure the text edit
            value_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            value_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            value_edit.setFrameShape(QTextEdit.Shape.StyledPanel)
            value_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            
            # Make it visually distinct but respect the current theme
            # We'll use the palette to determine if we're in a dark theme
            app = QApplication.instance()
            if app:
                palette = app.palette()
                is_dark_theme = palette.color(QPalette.ColorRole.Window).lightness() < 128
                
                if is_dark_theme:
                    # Dark theme styling
                    value_edit.setStyleSheet("""
                        QTextEdit {
                            border: 1px solid #555;
                            border-radius: 2px;
                            background-color: #252525;
                            color: #FFFFFF;
                        }
                    """)
                else:
                    # Light theme styling
                    value_edit.setStyleSheet("""
                        QTextEdit {
                            border: 1px solid #999;
                            border-radius: 2px;
                            background-color: #f8f8f8;
                        }
                    """)
            
            # Add context menu for copying
            value_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            value_edit.customContextMenuRequested.connect(
                lambda pos, edit=value_edit: self._show_context_menu(pos, edit)
            )
            
            # Convert value to string and handle None/NULL values
            if value is None:
                value_str = "NULL"
            else:
                value_str = str(value)
            
            # Check if the content has HTML or Markdown formatting
            has_formatting = self._has_formatting(value_str)
            
            # Store the raw content for toggling
            if has_formatting:
                self.raw_content[i] = value_str
                self.is_rendered[i] = True
                
                # Create a toggle button
                toggle_button = QToolButton()
                toggle_button.setText("Raw")
                toggle_button.setToolTip("Toggle between rendered and raw view")
                toggle_button.setCheckable(True)
                toggle_button.setFixedWidth(60)
                
                # Style the toggle button based on the current theme
                app = QApplication.instance()
                if app:
                    palette = app.palette()
                    is_dark_theme = palette.color(QPalette.ColorRole.Window).lightness() < 128
                    
                    if is_dark_theme:
                        # Dark theme styling
                        toggle_button.setStyleSheet("""
                            QToolButton {
                                border: 1px solid #555;
                                border-radius: 3px;
                                background-color: #454545;
                                color: #FFFFFF;
                                padding: 3px;
                            }
                            QToolButton:checked {
                                background-color: #353535;
                                border: 1px solid #666;
                            }
                            QToolButton:hover {
                                background-color: #505050;
                            }
                        """)
                    else:
                        # Light theme styling
                        toggle_button.setStyleSheet("""
                            QToolButton {
                                border: 1px solid #999;
                                border-radius: 3px;
                                background-color: #f0f0f0;
                                padding: 3px;
                            }
                            QToolButton:checked {
                                background-color: #e0e0e0;
                                border: 1px solid #777;
                            }
                            QToolButton:hover {
                                background-color: #e5e5e5;
                            }
                        """)
                
                # Connect the toggle button to the toggle function
                toggle_button.clicked.connect(lambda checked, idx=i: self._toggle_rendering(idx))
                
                # Add the toggle button to the header layout
                header_layout.addWidget(toggle_button)
                
                # Set the content as HTML to render it
                value_edit.setHtml(value_str)
            else:
                # Set the content as plain text
                value_edit.setPlainText(value_str)
            
            # Add stretch to push the toggle button to the right
            header_layout.addStretch()
            
            # Set a reasonable initial height based on content
            lines = min(value_str.count('\n') + 1, 5)  # Start with 5 lines by default
            line_height = value_edit.fontMetrics().lineSpacing()
            initial_height = lines * line_height + 20  # Add some padding
            
            # Set minimum height
            value_edit.setMinimumHeight(line_height * 2)  # Minimum height of 2 lines
            
            # Add tooltip to inform users they can resize the section
            value_edit.setToolTip("You can resize this section by dragging the handle below it")
            
            # Store reference to the value edit
            self.value_edits.append(value_edit)
            
            # Add widgets to the row layout
            row_layout.addLayout(header_layout)
            row_layout.addWidget(value_edit)
            
            # Add the row container to the splitter
            main_splitter.addWidget(row_container)
        
        # Add an empty widget at the end to ensure the last box can be resized
        # This gives the last real widget a splitter handle below it
        empty_widget = QWidget()
        empty_widget.setMinimumHeight(5)  # Very small, just enough to be functional
        empty_widget.setMaximumHeight(5)  # Keep it small
        empty_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        empty_widget.setStyleSheet("background-color: transparent;")  # Make it invisible
        main_splitter.addWidget(empty_widget)
        
        # Set initial sizes for the splitter sections
        sizes = []
        for i, value_edit in enumerate(self.value_edits):
            # Calculate a reasonable initial height
            lines = min(str(self.row_data[i]).count('\n') + 1, 5)
            line_height = value_edit.fontMetrics().lineSpacing()
            sizes.append(lines * line_height + 50)  # Add padding for the label and margins
        
        # Add a small size for the empty widget
        sizes.append(5)
        
        main_splitter.setSizes(sizes)
        
        # Create a scroll area to hold the splitter
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create a container widget for the splitter
        # This is necessary to allow the splitter to expand beyond the visible area
        self.scroll_container = QWidget()
        self.scroll_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # We'll set the initial height in showEvent to match the dialog size
        
        container_layout = QVBoxLayout(self.scroll_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(main_splitter)
        
        # Add a stretch at the bottom to push everything up
        # and ensure there's always scrollable space below
        container_layout.addStretch()
        
        # Set the container as the scroll area's widget
        scroll_area.setWidget(self.scroll_container)
        
        # Add the scroll area to the main layout
        layout.addWidget(scroll_area)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Add a slider to control the scrollable height
        height_layout = QHBoxLayout()
        
        height_label = QLabel("Scrollable Height:")
        height_layout.addWidget(height_label)
        
        self.height_slider = QSlider(Qt.Orientation.Horizontal)
        self.height_slider.setMinimum(100)    # Minimum height (100 pixels)
        self.height_slider.setMaximum(5000)   # Maximum height (5000 pixels)
        # Initial value will be set in showEvent
        self.height_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.height_slider.setTickInterval(500)
        self.height_slider.valueChanged.connect(self._update_scrollable_height)
        height_layout.addWidget(self.height_slider)
        
        self.height_value_label = QLabel("")  # Will be set in showEvent
        self.height_slider.valueChanged.connect(
            lambda value: self.height_value_label.setText(f"{value}px")
        )
        height_layout.addWidget(self.height_value_label)
        
        layout.addLayout(height_layout)
        
        # Add buttons at the bottom
        button_layout = QHBoxLayout()
        
        # Copy All button
        copy_all_button = QPushButton("Copy All")
        copy_all_button.clicked.connect(self._copy_all_data)
        button_layout.addWidget(copy_all_button)
        
        button_layout.addStretch()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # Escape key to close the dialog
        close_action = QAction("Close", self)
        close_action.setShortcut(QKeySequence.StandardKey.Cancel)
        close_action.triggered.connect(self.accept)
        self.addAction(close_action)
        
        # Ctrl+C to copy selected text
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._copy_selected)
        self.addAction(copy_action)
        
        # Ctrl+Shift+C to copy all data
        copy_all_action = QAction("Copy All", self)
        copy_all_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        copy_all_action.triggered.connect(self._copy_all_data)
        self.addAction(copy_all_action)
    
    def _show_context_menu(self, pos, edit):
        """Show context menu for a text edit"""
        menu = edit.createStandardContextMenu()
        
        # Add custom actions
        menu.addSeparator()
        
        # Copy with column name
        column_name = edit.property("column_name")
        copy_with_name_action = QAction(f"Copy with Column Name", self)
        copy_with_name_action.triggered.connect(
            lambda: self._copy_with_column_name(edit)
        )
        menu.addAction(copy_with_name_action)
        
        # Find the index of this edit in the value_edits list
        try:
            index = self.value_edits.index(edit)
            
            # If this field has formatting, add toggle option to the context menu
            if index in self.raw_content:
                menu.addSeparator()
                
                # Create the toggle action with appropriate text
                if self.is_rendered[index]:
                    toggle_action = QAction("Show Raw Content", self)
                else:
                    toggle_action = QAction("Show Rendered Content", self)
                    
                toggle_action.triggered.connect(lambda: self._toggle_rendering(index))
                menu.addAction(toggle_action)
        except ValueError:
            # Edit not found in value_edits list
            pass
        
        # Show the menu
        menu.exec(edit.mapToGlobal(pos))
    
    def _copy_selected(self):
        """Copy selected text from the focused widget"""
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QTextEdit):
            focused_widget.copy()
    
    def _copy_with_column_name(self, edit):
        """Copy the value with its column name"""
        column_name = edit.property("column_name")
        value = edit.toPlainText()
        text = f"{column_name}: {value}"
        
        # Get clipboard with null check
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)
    
    def _copy_all_data(self):
        """Copy all data in a formatted way"""
        lines = []
        for i, (column, value_edit) in enumerate(zip(self.column_names, self.value_edits)):
            value = value_edit.toPlainText()
            lines.append(f"{column}: {value}")
        
        text = "\n".join(lines)
        
        # Get clipboard with null check
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)
    
    def _update_scrollable_height(self, height):
        """Update the scrollable height of the container"""
        self.scroll_container.setMinimumHeight(height)
    
    def showEvent(self, event: QShowEvent):
        """Handle the dialog show event to set the initial scrollable height"""
        super().showEvent(event)
        
        # Wait for the dialog to be fully shown and sized
        QApplication.processEvents()
        
        # Calculate the available height for the scroll area
        # We subtract some space for the title, slider, and buttons
        available_height = self.height() - 150  # Approximate space for other widgets
        
        # Ensure a minimum reasonable height
        initial_height = max(available_height, 300)
        
        # Set the initial height of the scroll container
        self.scroll_container.setMinimumHeight(initial_height)
        
        # Update the slider value to match
        self.height_slider.setValue(initial_height)
        
    def changeEvent(self, event):
        """Handle palette and style changes"""
        if event.type() == QEvent.Type.PaletteChange or event.type() == QEvent.Type.StyleChange:
            # Update styling for all text edits when the theme changes
            self._update_theme_styling()
        
        # Call the parent class implementation
        super().changeEvent(event)
        
    def _update_theme_styling(self):
        """Update styling for all widgets based on the current theme"""
        app = QApplication.instance()
        if not app:
            return
            
        palette = app.palette()
        is_dark_theme = palette.color(QPalette.ColorRole.Window).lightness() < 128
        
        # Update all text edits
        for value_edit in self.value_edits:
            if is_dark_theme:
                # Dark theme styling
                value_edit.setStyleSheet("""
                    QTextEdit {
                        border: 1px solid #555;
                        border-radius: 2px;
                        background-color: #252525;
                        color: #FFFFFF;
                    }
                """)
            else:
                # Light theme styling
                value_edit.setStyleSheet("""
                    QTextEdit {
                        border: 1px solid #999;
                        border-radius: 2px;
                        background-color: #f8f8f8;
                    }
                """)
        
        # Update all toggle buttons
        for i in range(len(self.value_edits)):
            if i in self.is_rendered:
                # Find the toggle button for this field
                value_edit = self.value_edits[i]
                row_container = value_edit.parent()
                if row_container:
                    for button in row_container.findChildren(QToolButton):
                        # We assume the first tool button in the row container is our toggle button
                        if is_dark_theme:
                            # Dark theme styling
                            button.setStyleSheet("""
                                QToolButton {
                                    border: 1px solid #555;
                                    border-radius: 3px;
                                    background-color: #454545;
                                    color: #FFFFFF;
                                    padding: 3px;
                                }
                                QToolButton:checked {
                                    background-color: #353535;
                                    border: 1px solid #666;
                                }
                                QToolButton:hover {
                                    background-color: #505050;
                                }
                            """)
                        else:
                            # Light theme styling
                            button.setStyleSheet("""
                                QToolButton {
                                    border: 1px solid #999;
                                    border-radius: 3px;
                                    background-color: #f0f0f0;
                                    padding: 3px;
                                }
                                QToolButton:checked {
                                    background-color: #e0e0e0;
                                    border: 1px solid #777;
                                }
                                QToolButton:hover {
                                    background-color: #e5e5e5;
                                }
                            """)
                        break