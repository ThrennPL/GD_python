"""
Moduł integracji PDF z generatorem diagramów PlantUML/XMI.

Umożliwia wykorzystanie dokumentów PDF jako źródła kontekstu biznesowego
dla generowania bardziej precyzyjnych i kompletnych diagramów.
"""

from .pdf_processor import (
    PDFProcessor,
    PDFDocument, 
    ProcessContext,
    enhance_prompt_with_pdf_context
)

try:
    from .streamlit_pdf_integration import PDFUploadManager
    STREAMLIT_INTEGRATION_AVAILABLE = True
except ImportError:
    PDFUploadManager = None
    STREAMLIT_INTEGRATION_AVAILABLE = False

__version__ = "1.0.0"
__author__ = "GD_python Team"

__all__ = [
    'PDFProcessor',
    'PDFDocument', 
    'ProcessContext',
    'enhance_prompt_with_pdf_context',
    'PDFUploadManager',
    'STREAMLIT_INTEGRATION_AVAILABLE'
]