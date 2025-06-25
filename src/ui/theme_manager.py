"""
Theme manager for the DBridge application
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import QSettings

# Define theme constants
LIGHT_DEFAULT = "Light Default"
LIGHT_BLUE = "Light Blue"
DARK_DEFAULT = "Dark Default"
DARK_BLUE = "Dark Blue"

class ThemeManager:
    """Manages application themes"""
    
    def __init__(self):
        self.settings = QSettings("DBridge", "DBridge")
        self.current_theme = self.settings.value("theme", LIGHT_DEFAULT)
    
    def get_available_themes(self):
        """Return a list of available themes"""
        return [LIGHT_DEFAULT, LIGHT_BLUE, DARK_DEFAULT, DARK_BLUE]
    
    def get_current_theme(self):
        """Return the current theme name"""
        return self.current_theme
    
    def set_theme(self, theme_name):
        """Set the application theme"""
        if theme_name not in self.get_available_themes():
            return False
        
        self.current_theme = theme_name
        self.settings.setValue("theme", theme_name)
        self._apply_theme(theme_name)
        
        # Force a refresh of all syntax highlighters
        app = QApplication.instance()
        if app:
            # Emit a style change event to force UI updates
            app.setStyleSheet(app.styleSheet())
        
        return True
    
    def _apply_theme(self, theme_name):
        """Apply the selected theme to the application"""
        app = QApplication.instance()
        if not app:
            return
        
        if theme_name == LIGHT_DEFAULT:
            self._apply_light_default_theme(app)
        elif theme_name == LIGHT_BLUE:
            self._apply_light_blue_theme(app)
        elif theme_name == DARK_DEFAULT:
            self._apply_dark_default_theme(app)
        elif theme_name == DARK_BLUE:
            self._apply_dark_blue_theme(app)
    
    def _apply_light_default_theme(self, app):
        """Apply the light default theme"""
        app.setStyle("Fusion")
        
        # Use default palette
        app.setPalette(QPalette())
        
        # Set stylesheet for additional customization
        app.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #F5F5F5;
            }
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                border: 1px solid #C0C0C0;
                padding: 5px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                border-bottom-color: #FFFFFF;
            }
            QTableView, QTreeView, QListWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F5F5F5;
                border: 1px solid #C0C0C0;
            }
            QHeaderView::section {
                background-color: #E0E0E0;
                border: 1px solid #C0C0C0;
                padding: 4px;
            }
            QPushButton {
                background-color: #E0E0E0;
                border: 1px solid #C0C0C0;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QPushButton:pressed {
                background-color: #C0C0C0;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #C0C0C0;
                padding: 3px;
            }
        """)
    
    def _apply_light_blue_theme(self, app):
        """Apply the light blue theme"""
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 245, 250))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(233, 243, 253))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(226, 236, 246))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(66, 133, 244))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
        
        app.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #F0F5FA;
            }
            QTabWidget::pane {
                border: 1px solid #B8D6F5;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #DCE8F5;
                border: 1px solid #B8D6F5;
                padding: 5px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                border-bottom-color: #FFFFFF;
            }
            QTableView, QTreeView, QListWidget {
                background-color: #FFFFFF;
                alternate-background-color: #E9F3FD;
                border: 1px solid #B8D6F5;
            }
            QHeaderView::section {
                background-color: #DCE8F5;
                border: 1px solid #B8D6F5;
                padding: 4px;
            }
            QPushButton {
                background-color: #E2ECF6;
                border: 1px solid #B8D6F5;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #D2E2F0;
            }
            QPushButton:pressed {
                background-color: #C2D8EA;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #B8D6F5;
                padding: 3px;
            }
        """)
    
    def _apply_dark_default_theme(self, app):
        """Apply the dark default theme"""
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
        
        app.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #353535;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #252525;
            }
            QTabBar::tab {
                background-color: #454545;
                border: 1px solid #555555;
                padding: 5px;
                min-width: 80px;
                color: #FFFFFF;
            }
            QTabBar::tab:selected {
                background-color: #252525;
                border-bottom-color: #252525;
            }
            QTableView, QTreeView, QListWidget {
                background-color: #252525;
                alternate-background-color: #2D2D2D;
                border: 1px solid #555555;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #454545;
                border: 1px solid #555555;
                padding: 4px;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #454545;
                border: 1px solid #555555;
                padding: 5px;
                min-width: 80px;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                background-color: #252525;
                border: 1px solid #555555;
                padding: 3px;
                color: #FFFFFF;
            }
            QMenu {
                background-color: #353535;
                color: #FFFFFF;
            }
            QMenu::item:selected {
                background-color: #454545;
            }
            QMenuBar {
                background-color: #353535;
                color: #FFFFFF;
            }
            QMenuBar::item:selected {
                background-color: #454545;
            }
        """)
    
    def _apply_dark_blue_theme(self, app):
        """Apply the dark blue theme"""
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(25, 35, 45))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(15, 25, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 30, 40))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(15, 25, 35))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(25, 35, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(66, 133, 244))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(66, 133, 244))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
        
        app.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #19232D;
            }
            QTabWidget::pane {
                border: 1px solid #455364;
                background-color: #0F1923;
            }
            QTabBar::tab {
                background-color: #263642;
                border: 1px solid #455364;
                padding: 5px;
                min-width: 80px;
                color: #FFFFFF;
            }
            QTabBar::tab:selected {
                background-color: #0F1923;
                border-bottom-color: #0F1923;
            }
            QTableView, QTreeView, QListWidget {
                background-color: #0F1923;
                alternate-background-color: #141E28;
                border: 1px solid #455364;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #263642;
                border: 1px solid #455364;
                padding: 4px;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #263642;
                border: 1px solid #455364;
                padding: 5px;
                min-width: 80px;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #344B5E;
            }
            QPushButton:pressed {
                background-color: #425F7A;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                background-color: #0F1923;
                border: 1px solid #455364;
                padding: 3px;
                color: #FFFFFF;
            }
            QMenu {
                background-color: #19232D;
                color: #FFFFFF;
            }
            QMenu::item:selected {
                background-color: #263642;
            }
            QMenuBar {
                background-color: #19232D;
                color: #FFFFFF;
            }
            QMenuBar::item:selected {
                background-color: #263642;
            }
        """)