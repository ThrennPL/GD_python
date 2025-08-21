from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re

class XMLHighlighter(QSyntaxHighlighter):
    """Klasa definiująca reguły kolorowania składni XML."""
    def __init__(self, document):
        super(XMLHighlighter, self).__init__(document)
        self.highlighting_rules = []

        # Definicje reguł kolorowania
        self.add_highlighting_rule(r"<\?xml.*?\?>", QColor("gray"))  # Deklaracja XML
        self.add_highlighting_rule(r"</?\w+.*?>", QColor("blue"))    # Tag otwierający/zamykający
        self.add_highlighting_rule(r"\".*?\"", QColor("red"))        # Wartości atrybutów
        self.add_highlighting_rule(r"=\s*\".*?\"", QColor("green"))  # Atrybuty


    def add_highlighting_rule(self, pattern, color):
        """Dodaje regułę kolorowania."""
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        text_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((re.compile(pattern), text_format))

    def highlightBlock(self, text):
        """Koloruje blok tekstu."""
        for pattern, text_format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, length = match.span()
                self.setFormat(start, length, text_format)