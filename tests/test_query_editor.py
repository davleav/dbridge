"""
Tests for the SQL query editor
"""

import unittest
import os
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtTest import QTest

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.ui.query_editor import QueryEditor, SQLSyntaxHighlighter


class TestQueryEditor(unittest.TestCase):
    """Test cases for the QueryEditor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.query_editor = QueryEditor()
    
    def test_get_set_query(self):
        """Test getting and setting query text"""
        # Set a test query
        test_query = "SELECT * FROM test WHERE id = 1"
        self.query_editor.set_query(test_query)
        
        # Check that the query was set correctly
        self.assertEqual(self.query_editor.get_query(), test_query)
    
    def test_editor_created(self):
        """Test that the editor widget was created"""
        self.assertIsNotNone(self.query_editor.editor)
    
    def test_syntax_highlighter_created(self):
        """Test that the syntax highlighter was created"""
        self.assertIsNotNone(self.query_editor.highlighter)
        self.assertIsInstance(self.query_editor.highlighter, SQLSyntaxHighlighter)


class TestSQLSyntaxHighlighter(unittest.TestCase):
    """Test cases for the SQLSyntaxHighlighter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a real QTextDocument instead of a mock
        from PyQt6.QtGui import QTextDocument
        self.document = QTextDocument()
        self.highlighter = SQLSyntaxHighlighter(self.document)
    
    def test_highlighting_rules_created(self):
        """Test that highlighting rules were created"""
        self.assertTrue(len(self.highlighter._highlighting_rules) > 0)
    
    def test_keyword_highlighting(self):
        """Test that SQL keywords are highlighted"""
        # Find a keyword rule
        keyword_rule = None
        for rule in self.highlighter._highlighting_rules:
            pattern, format = rule
            if pattern.pattern() == "\\bSELECT\\b":
                keyword_rule = rule
                break
        
        self.assertIsNotNone(keyword_rule, "SELECT keyword rule not found")
        
        # Check the format
        pattern, format = keyword_rule
        self.assertEqual(format.foreground().color().name(), "#569cd6")
        self.assertEqual(format.fontWeight(), QFont.Weight.Bold)
    
    def test_string_highlighting(self):
        """Test that string literals are highlighted"""
        # Find the string rule
        string_rule = None
        for rule in self.highlighter._highlighting_rules:
            pattern, format = rule
            if pattern.pattern() == "'[^']*'|\"[^\"]*\"":
                string_rule = rule
                break
        
        self.assertIsNotNone(string_rule, "String literal rule not found")
        
        # Check the format
        pattern, format = string_rule
        self.assertEqual(format.foreground().color().name(), "#ce9178")
    
    def test_comment_highlighting(self):
        """Test that comments are highlighted"""
        # Find the comment rule
        comment_rule = None
        for rule in self.highlighter._highlighting_rules:
            pattern, format = rule
            if pattern.pattern() == "--[^\n]*":
                comment_rule = rule
                break
        
        self.assertIsNotNone(comment_rule, "Comment rule not found")
        
        # Check the format
        pattern, format = comment_rule
        self.assertEqual(format.foreground().color().name(), "#6a9955")
        self.assertTrue(format.fontItalic())


if __name__ == '__main__':
    unittest.main()