"""
SQL query editor with syntax highlighting
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPlainTextEdit, QApplication
from PyQt6.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter, QPalette
from PyQt6.QtCore import Qt, QRegularExpression

class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """SQL syntax highlighter for the query editor"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._highlighting_rules = []
        self._setup_highlighting_rules()
    
    def _is_dark_theme(self):
        """Check if the application is using a dark theme"""
        app = QApplication.instance()
        if app:
            # Check if the application palette's window color is dark
            window_color = app.palette().color(QPalette.ColorRole.Window)
            # Calculate brightness (0-255) using the formula: 0.299*R + 0.587*G + 0.114*B
            brightness = (0.299 * window_color.red() + 
                         0.587 * window_color.green() + 
                         0.114 * window_color.blue())
            return brightness < 128
        return False
    
    def _setup_highlighting_rules(self):
        """Set up syntax highlighting rules based on the current theme"""
        self._highlighting_rules = []
        
        is_dark = self._is_dark_theme()
        
        # SQL keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6" if is_dark else "#0000FF"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            "\\bSELECT\\b", "\\bFROM\\b", "\\bWHERE\\b", "\\bAND\\b", "\\bOR\\b",
            "\\bINSERT\\b", "\\bUPDATE\\b", "\\bDELETE\\b", "\\bCREATE\\b", "\\bALTER\\b",
            "\\bDROP\\b", "\\bTABLE\\b", "\\bINDEX\\b", "\\bVIEW\\b", "\\bJOIN\\b",
            "\\bINNER\\b", "\\bLEFT\\b", "\\bRIGHT\\b", "\\bOUTER\\b", "\\bFULL\\b",
            "\\bON\\b", "\\bAS\\b", "\\bORDER\\b", "\\bBY\\b", "\\bGROUP\\b",
            "\\bHAVING\\b", "\\bLIMIT\\b", "\\bOFFSET\\b", "\\bUNION\\b", "\\bALL\\b",
            "\\bIN\\b", "\\bIS\\b", "\\bNULL\\b", "\\bNOT\\b", "\\bLIKE\\b",
            "\\bCASE\\b", "\\bWHEN\\b", "\\bTHEN\\b", "\\bELSE\\b", "\\bEND\\b",
            "\\bDISTINCT\\b", "\\bCOUNT\\b", "\\bSUM\\b", "\\bAVG\\b", "\\bMAX\\b",
            "\\bMIN\\b", "\\bBETWEEN\\b", "\\bEXISTS\\b", "\\bTRUE\\b", "\\bFALSE\\b",
            "\\bPRIMARY\\b", "\\bKEY\\b", "\\bFOREIGN\\b", "\\bCONSTRAINT\\b", "\\bDEFAULT\\b",
            "\\bAUTO_INCREMENT\\b", "\\bSERIAL\\b", "\\bREFERENCES\\b", "\\bCASCADE\\b", "\\bRESTRICT\\b",
            "\\bSET\\b", "\\bVALUES\\b", "\\bINTO\\b", "\\bBEGIN\\b", "\\bCOMMIT\\b",
            "\\bROLLBACK\\b", "\\bTRANSACTION\\b", "\\bTRIGGER\\b", "\\bPROCEDURE\\b", "\\bFUNCTION\\b"
        ]
        
        for pattern in keywords:
            regex = QRegularExpression(pattern)
            regex.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
            self._highlighting_rules.append((regex, keyword_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8" if is_dark else "#008000"))
        number_regex = QRegularExpression("\\b[0-9]+\\b")
        self._highlighting_rules.append((number_regex, number_format))
        
        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178" if is_dark else "#A31515"))
        string_regex = QRegularExpression("'[^']*'|\"[^\"]*\"")
        self._highlighting_rules.append((string_regex, string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955" if is_dark else "#008000"))
        comment_format.setFontItalic(True)
        
        # Single line comments
        comment_regex = QRegularExpression("--[^\n]*")
        self._highlighting_rules.append((comment_regex, comment_format))
        
        # Multi-line comments
        self._multi_line_comment_format = QTextCharFormat()
        self._multi_line_comment_format.setForeground(QColor("#6A9955" if is_dark else "#008000"))
        self._multi_line_comment_format.setFontItalic(True)
        
        self._comment_start_regex = QRegularExpression("/\\*")
        self._comment_end_regex = QRegularExpression("\\*/")
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text"""
        # Refresh highlighting rules to adapt to theme changes
        self._setup_highlighting_rules()
        
        # Apply regular expression highlighting rules
        for pattern, format in self._highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        
        # Handle multi-line comments
        self.setCurrentBlockState(0)
        
        start_index = 0
        if self.previousBlockState() != 1:
            match = self._comment_start_regex.match(text)
            start_index = match.capturedStart() if match.hasMatch() else -1
        
        while start_index >= 0:
            end_match = self._comment_end_regex.match(text[start_index:])
            end_index = end_match.capturedStart() + start_index if end_match.hasMatch() else -1
            comment_length = 0
            
            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + end_match.capturedLength()
            
            self.setFormat(start_index, comment_length, self._multi_line_comment_format)
            
            next_match = self._comment_start_regex.match(text[start_index + comment_length:])
            start_index = next_match.capturedStart() + start_index + comment_length if next_match.hasMatch() else -1


class QueryEditor(QWidget):
    """SQL query editor widget with syntax highlighting"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.editor = QPlainTextEdit()
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Set a monospaced font
        font = QFont("Courier New", 10)
        self.editor.setFont(font)
        
        # Apply syntax highlighting
        self.highlighter = SQLSyntaxHighlighter(self.editor.document())
        
        layout.addWidget(self.editor)
    
    def get_query(self):
        """Get the current query text"""
        return self.editor.toPlainText()
    
    def set_query(self, query):
        """Set the query text"""
        self.editor.setPlainText(query)