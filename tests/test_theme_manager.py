"""
Tests for the theme manager
"""

import unittest
import os
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.ui.theme_manager import ThemeManager, LIGHT_DEFAULT, LIGHT_BLUE, DARK_DEFAULT, DARK_BLUE


class TestThemeManager(unittest.TestCase):
    """Test cases for the ThemeManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock QSettings to avoid writing to disk during tests
        self.settings_patcher = patch('src.ui.theme_manager.QSettings')
        self.mock_settings_class = self.settings_patcher.start()
        
        # Configure the mock settings
        self.mock_settings = MagicMock()
        self.mock_settings.value.return_value = LIGHT_DEFAULT
        self.mock_settings_class.return_value = self.mock_settings
        
        # Create the theme manager
        self.theme_manager = ThemeManager()
    
    def tearDown(self):
        """Clean up after tests"""
        self.settings_patcher.stop()
    
    def test_get_available_themes(self):
        """Test getting the list of available themes"""
        themes = self.theme_manager.get_available_themes()
        self.assertEqual(len(themes), 4)
        self.assertIn(LIGHT_DEFAULT, themes)
        self.assertIn(LIGHT_BLUE, themes)
        self.assertIn(DARK_DEFAULT, themes)
        self.assertIn(DARK_BLUE, themes)
    
    def test_get_current_theme(self):
        """Test getting the current theme"""
        # The default theme should be LIGHT_DEFAULT as set in the mock
        self.assertEqual(self.theme_manager.get_current_theme(), LIGHT_DEFAULT)
        
        # Change the theme and check again
        self.theme_manager.current_theme = DARK_DEFAULT
        self.assertEqual(self.theme_manager.get_current_theme(), DARK_DEFAULT)
    
    def test_set_theme_valid(self):
        """Test setting a valid theme"""
        # Set up the app instance mock
        app_mock = MagicMock()
        
        with patch('src.ui.theme_manager.QApplication.instance', return_value=app_mock):
            # Set a valid theme
            result = self.theme_manager.set_theme(DARK_BLUE)
            
            # Check that the theme was set
            self.assertTrue(result)
            self.assertEqual(self.theme_manager.current_theme, DARK_BLUE)
            
            # Check that the settings were updated
            self.mock_settings.setValue.assert_called_with("theme", DARK_BLUE)
            
            # Check that the theme was applied to the application
            self.assertTrue(app_mock.setStyle.called)
            self.assertTrue(app_mock.setPalette.called)
            self.assertTrue(app_mock.setStyleSheet.called)
    
    def test_set_theme_invalid(self):
        """Test setting an invalid theme"""
        # Try to set an invalid theme
        result = self.theme_manager.set_theme("Invalid Theme")
        
        # Check that the theme was not set
        self.assertFalse(result)
        self.assertEqual(self.theme_manager.current_theme, LIGHT_DEFAULT)
        
        # Check that the settings were not updated
        self.mock_settings.setValue.assert_not_called()
    
    def test_apply_light_default_theme(self):
        """Test applying the light default theme"""
        app_mock = MagicMock()
        
        # Call the method directly
        self.theme_manager._apply_light_default_theme(app_mock)
        
        # Check that the style and stylesheet were set
        app_mock.setStyle.assert_called_with("Fusion")
        self.assertTrue(app_mock.setPalette.called)
        self.assertTrue(app_mock.setStyleSheet.called)
    
    def test_apply_light_blue_theme(self):
        """Test applying the light blue theme"""
        app_mock = MagicMock()
        
        # Call the method directly
        self.theme_manager._apply_light_blue_theme(app_mock)
        
        # Check that the style and stylesheet were set
        app_mock.setStyle.assert_called_with("Fusion")
        self.assertTrue(app_mock.setPalette.called)
        self.assertTrue(app_mock.setStyleSheet.called)
    
    def test_apply_dark_default_theme(self):
        """Test applying the dark default theme"""
        app_mock = MagicMock()
        
        # Call the method directly
        self.theme_manager._apply_dark_default_theme(app_mock)
        
        # Check that the style and stylesheet were set
        app_mock.setStyle.assert_called_with("Fusion")
        self.assertTrue(app_mock.setPalette.called)
        self.assertTrue(app_mock.setStyleSheet.called)
    
    def test_apply_dark_blue_theme(self):
        """Test applying the dark blue theme"""
        app_mock = MagicMock()
        
        # Call the method directly
        self.theme_manager._apply_dark_blue_theme(app_mock)
        
        # Check that the style and stylesheet were set
        app_mock.setStyle.assert_called_with("Fusion")
        self.assertTrue(app_mock.setPalette.called)
        self.assertTrue(app_mock.setStyleSheet.called)


if __name__ == '__main__':
    unittest.main()