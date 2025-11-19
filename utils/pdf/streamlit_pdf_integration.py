"""
Komponenty interfejsu użytkownika dla obsługi plików PDF w Streamlit.
"""

import streamlit as st
import tempfile
import os
from typing import List, Optional
from pathlib import Path
from utils.pdf.pdf_processor import PDFProcessor, enhance_prompt_with_pdf_context

class PDFUploadManager:
    """Manager do obsługi uploadu i przetwarzania plików PDF w Streamlit."""
    
    def __init__(self):
        self.processor = PDFProcessor()
        
        # Inicjalizacja session state
        if 'uploaded_pdfs' not in st.session_state:
            st.session_state.uploaded_pdfs = []
        if 'pdf_contexts' not in st.session_state:
            st.session_state.pdf_contexts = {}
    
    def render_pdf_upload_section(self) -> None:
        """Renderuje sekcję uploadu plików PDF."""
        
        with st.expander("📄 Dodatkowy kontekst z plików PDF", expanded=False):
            st.markdown("""
            **Wgraj pliki PDF zawierające:**
            - Dokumentację procesów biznesowych
            - Specyfikacje techniczne
            - Diagramy i schematy
            - Instrukcje operacyjne
            - Polityki i procedury
            """)
            
            # Upload plików
            uploaded_files = st.file_uploader(
                "Wybierz pliki PDF",
                type=['pdf'],
                accept_multiple_files=True,
                key="pdf_uploader",
                help="Pliki PDF zostaną przeanalizowane i użyte jako kontekst dla generowania diagramów"
            )
            
            if uploaded_files:
                self._process_uploaded_files(uploaded_files)
            
            # Pokaż aktualnie załadowane pliki
            self._display_loaded_files()
            
            # Opcje przetwarzania
            self._render_processing_options()
    
    def _process_uploaded_files(self, uploaded_files) -> None:
        """Przetwarza wgrane pliki PDF."""
        
        new_files = []
        
        for uploaded_file in uploaded_files:
            # Sprawdź czy plik już został przetworzony
            file_id = f"{uploaded_file.name}_{len(uploaded_file.getvalue())}"
            
            if file_id not in [pdf['id'] for pdf in st.session_state.uploaded_pdfs]:
                # Zapisz plik tymczasowo
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                new_files.append({
                    'id': file_id,
                    'name': uploaded_file.name,
                    'path': tmp_file_path,
                    'size': len(uploaded_file.getvalue())
                })
        
        if new_files:
            with st.spinner("Przetwarzanie plików PDF..."):
                for file_info in new_files:
                    try:
                        # Przetwórz PDF
                        pdf_doc = self.processor.process_pdf(file_info['path'])
                        
                        # Dodaj do session state
                        file_info['processed'] = True
                        file_info['pages'] = pdf_doc.total_pages
                        file_info['title'] = pdf_doc.title
                        
                        st.session_state.uploaded_pdfs.append(file_info)
                        st.session_state.pdf_contexts[file_info['id']] = pdf_doc
                        
                        st.success(f"✅ Przetworzono: {file_info['name']} ({pdf_doc.total_pages} stron)")
                        
                    except Exception as e:
                        st.error(f"❌ Błąd przetwarzania {file_info['name']}: {str(e)}")
                        # Usuń tymczasowy plik
                        try:
                            os.unlink(file_info['path'])
                        except:
                            pass
    
    def _display_loaded_files(self) -> None:
        """Wyświetla listę załadowanych plików PDF."""
        
        if st.session_state.uploaded_pdfs:
            st.markdown("**Załadowane pliki PDF:**")
            
            for i, pdf_info in enumerate(st.session_state.uploaded_pdfs):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.text(f"📄 {pdf_info['name']}")
                    if 'title' in pdf_info and pdf_info['title'] != pdf_info['name']:
                        st.caption(f"Tytuł: {pdf_info['title']}")
                
                with col2:
                    if 'pages' in pdf_info:
                        st.caption(f"{pdf_info['pages']} stron")
                
                with col3:
                    if st.button("🗑️", key=f"remove_pdf_{i}", help="Usuń plik"):
                        self._remove_pdf(i)
                        st.experimental_rerun()
    
    def _remove_pdf(self, index: int) -> None:
        """Usuwa plik PDF z listy."""
        
        if 0 <= index < len(st.session_state.uploaded_pdfs):
            pdf_info = st.session_state.uploaded_pdfs[index]
            
            # Usuń tymczasowy plik
            try:
                os.unlink(pdf_info['path'])
            except:
                pass
            
            # Usuń z session state
            del st.session_state.uploaded_pdfs[index]
            if pdf_info['id'] in st.session_state.pdf_contexts:
                del st.session_state.pdf_contexts[pdf_info['id']]
    
    def _render_processing_options(self) -> None:
        """Renderuje opcje przetwarzania PDF."""
        
        if st.session_state.uploaded_pdfs:
            st.markdown("**Opcje kontekstu:**")
            
            context_mode = st.radio(
                "Jak używać kontekstu z PDF:",
                [
                    "Automatycznie dostosuj do typu diagramu",
                    "Użyj pełnego tekstu jako kontekst",
                    "Tylko kluczowe elementy (aktorzy, procesy, systemy)"
                ],
                key="pdf_context_mode",
                help="Wybierz sposób wykorzystania informacji z plików PDF"
            )
            
            if st.button("🔄 Odśwież analizę plików", key="refresh_pdf_analysis"):
                self._refresh_analysis()
    
    def _refresh_analysis(self) -> None:
        """Odświeża analizę wszystkich plików PDF."""
        
        with st.spinner("Odświeżanie analizy..."):
            for pdf_info in st.session_state.uploaded_pdfs:
                try:
                    # Przetwórz ponownie bez użycia cache
                    pdf_doc = self.processor.process_pdf(pdf_info['path'], use_cache=False)
                    st.session_state.pdf_contexts[pdf_info['id']] = pdf_doc
                except Exception as e:
                    st.error(f"Błąd odświeżania {pdf_info['name']}: {str(e)}")
        
        st.success("✅ Analiza została odświeżona")
    
    def get_enhanced_prompt(self, original_prompt: str, diagram_type: str) -> str:
        """Zwraca prompt wzbogacony o kontekst z plików PDF."""
        
        if not st.session_state.uploaded_pdfs:
            return original_prompt
        
        # Pobierz ścieżki do plików
        pdf_files = [pdf_info['path'] for pdf_info in st.session_state.uploaded_pdfs if pdf_info.get('processed', False)]
        
        if not pdf_files:
            return original_prompt
        
        try:
            enhanced = enhance_prompt_with_pdf_context(original_prompt, pdf_files, diagram_type)
            return enhanced
        except Exception as e:
            st.warning(f"Nie udało się użyć kontekstu PDF: {str(e)}")
            return original_prompt
    
    def show_context_preview(self, diagram_type: str) -> None:
        """Pokazuje podgląd kontekstu, który zostanie użyty."""
        
        if not st.session_state.uploaded_pdfs:
            return
        
        with st.expander("🔍 Podgląd kontekstu z PDF", expanded=False):
            for pdf_info in st.session_state.uploaded_pdfs:
                if pdf_info['id'] in st.session_state.pdf_contexts:
                    pdf_doc = st.session_state.pdf_contexts[pdf_info['id']]
                    
                    st.markdown(f"**{pdf_doc.title}**")
                    
                    # Pokaż kontekst dla danego typu diagramu
                    context = self.processor.get_context_for_diagram_type(pdf_doc, diagram_type)
                    
                    # Skróć kontekst do wyświetlenia
                    preview = context[:500] + "..." if len(context) > 500 else context
                    st.text_area(
                        f"Kontekst z {pdf_info['name']}:",
                        value=preview,
                        height=150,
                        disabled=True,
                        key=f"context_preview_{pdf_info['id']}"
                    )
    
    def get_context_stats(self) -> dict:
        """Zwraca statystyki kontekstu z plików PDF."""
        
        if not st.session_state.uploaded_pdfs:
            return {}
        
        stats = {
            'total_files': len(st.session_state.uploaded_pdfs),
            'total_pages': sum(pdf.get('pages', 0) for pdf in st.session_state.uploaded_pdfs),
            'processed_files': len([pdf for pdf in st.session_state.uploaded_pdfs if pdf.get('processed', False)])
        }
        
        return stats

# Funkcja pomocnicza do integracji z istniejącym kodem streamlit_app.py
def integrate_pdf_upload_to_streamlit():
    """
    Przykład integracji z istniejącym interfejsem Streamlit.
    Ta funkcja pokazuje jak dodać obsługę PDF do głównej aplikacji.
    """
    
    # Zainicjalizuj manager PDF
    pdf_manager = PDFUploadManager()
    
    # W głównym interfejsie, po sekcji wyboru typu diagramu
    pdf_manager.render_pdf_upload_section()
    
    # Przy generowaniu promptu (w funkcji generate_diagram lub podobnej)
    # enhanced_prompt = pdf_manager.get_enhanced_prompt(original_prompt, diagram_type)
    
    # Opcjonalnie: pokaż podgląd kontekstu
    # pdf_manager.show_context_preview(diagram_type)
    
    return pdf_manager