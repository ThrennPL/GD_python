"""
Moduł do przetwarzania plików PDF i ekstrakcji kontekstu dla diagramów.
"""

import PyPDF2
import fitz  # PyMuPDF
import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from datetime import datetime

@dataclass
class PDFDocument:
    """Klasa reprezentująca dokument PDF z wyekstraktowanym kontekstem."""
    file_path: str
    title: str
    total_pages: int
    text_content: str
    structured_content: Dict
    metadata: Dict
    hash: str
    processed_date: str

@dataclass
class ProcessContext:
    """Kontekst procesu wyekstraktowany z PDF."""
    process_name: str
    actors: List[str]
    activities: List[str]
    decisions: List[str]
    data_flows: List[str]
    business_rules: List[str]
    systems: List[str]

class PDFProcessor:
    """Główna klasa do przetwarzania plików PDF dla kontekstu diagramów."""
    
    def __init__(self, cache_dir: str = "cache/pdf"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Wzorce dla różnych typów kontekstu
        self.patterns = {
            'actors': [
                r'(?:użytkownik|klient|pracownik|administrator|operator|analityk)',
                r'(?:user|client|employee|admin|operator|analyst)',
                r'(?:role|rola):\s*([^.\n]+)',
            ],
            'activities': [
                r'(?:krok|etap|czynność|operacja):\s*([^.\n]+)',
                r'(?:step|stage|activity|operation):\s*([^.\n]+)',
                r'(?:proces|procedure):\s*([^.\n]+)',
            ],
            'decisions': [
                r'(?:jeśli|gdy|w przypadku gdy|decyzja)',
                r'(?:if|when|in case of|decision)',
                r'(?:warunek|condition):\s*([^.\n]+)',
            ],
            'systems': [
                r'(?:system|aplikacja|baza danych|serwis)',
                r'(?:system|application|database|service)',
                r'(?:API|interface|interfejs)',
            ]
        }
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Oblicza hash pliku do cache'owania."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def get_cache_path(self, file_hash: str) -> Path:
        """Zwraca ścieżkę do pliku cache."""
        return self.cache_dir / f"{file_hash}.json"
    
    def load_from_cache(self, file_path: str) -> Optional[PDFDocument]:
        """Ładuje przetworzone dane z cache."""
        file_hash = self.calculate_file_hash(file_path)
        cache_path = self.get_cache_path(file_hash)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return PDFDocument(**data)
            except Exception:
                pass
        return None
    
    def save_to_cache(self, pdf_doc: PDFDocument) -> None:
        """Zapisuje przetworzone dane do cache."""
        cache_path = self.get_cache_path(pdf_doc.hash)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(pdf_doc.__dict__, f, indent=2, ensure_ascii=False)
    
    def extract_text_pymupdf(self, file_path: str) -> Tuple[str, Dict]:
        """Ekstraktuje tekst używając PyMuPDF (lepiej obsługuje formatting)."""
        doc = fitz.open(file_path)
        text_content = ""
        structured_content = {
            'pages': [],
            'toc': [],
            'images': [],
            'tables': []
        }
        
        # Spis treści
        toc = doc.get_toc()
        structured_content['toc'] = toc
        
        # Ekstraktuj tekst z każdej strony
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            text_content += f"\n--- Strona {page_num + 1} ---\n{page_text}"
            
            # Dodatkowe informacje o stronie
            page_info = {
                'page_num': page_num + 1,
                'text': page_text,
                'word_count': len(page_text.split())
            }
            structured_content['pages'].append(page_info)
        
        doc.close()
        return text_content, structured_content
    
    def extract_text_pypdf2(self, file_path: str) -> str:
        """Backup ekstraktora używający PyPDF2."""
        text_content = ""
        
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text_content += f"\n--- Strona {page_num + 1} ---\n{page.extract_text()}"
        
        return text_content
    
    def analyze_process_context(self, text: str) -> ProcessContext:
        """Analizuje tekst i wyciąga kontekst procesu biznesowego."""
        context = ProcessContext(
            process_name="",
            actors=[],
            activities=[],
            decisions=[],
            data_flows=[],
            business_rules=[],
            systems=[]
        )
        
        # Znajdź nazwę procesu (pierwszy nagłówek lub tytuł)
        title_patterns = [
            r'^#\s*(.+)$',
            r'^\*\*(.+)\*\*$',
            r'^([A-ZĄĆĘŁŃÓŚŹŻ][^.\n]{10,60})$'
        ]
        
        lines = text.split('\n')
        for line in lines[:10]:  # Sprawdź pierwsze 10 linii
            for pattern in title_patterns:
                match = re.search(pattern, line.strip(), re.MULTILINE)
                if match and not context.process_name:
                    context.process_name = match.group(1).strip()
                    break
        
        # Wyciągnij aktorów
        for pattern in self.patterns['actors']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                actor = match.group(0) if match.lastindex is None else match.group(1)
                if actor and len(actor.strip()) > 2:
                    context.actors.append(actor.strip())
        
        # Wyciągnij aktywności
        for pattern in self.patterns['activities']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                activity = match.group(0) if match.lastindex is None else match.group(1)
                if activity and len(activity.strip()) > 3:
                    context.activities.append(activity.strip())
        
        # Wyciągnij decyzje
        for pattern in self.patterns['decisions']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                decision = match.group(0) if match.lastindex is None else match.group(1)
                if decision and len(decision.strip()) > 3:
                    context.decisions.append(decision.strip())
        
        # Wyciągnij systemy
        for pattern in self.patterns['systems']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                system = match.group(0) if match.lastindex is None else match.group(1)
                if system and len(system.strip()) > 2:
                    context.systems.append(system.strip())
        
        # Deduplikacja
        context.actors = list(set(context.actors))
        context.activities = list(set(context.activities))
        context.decisions = list(set(context.decisions))
        context.systems = list(set(context.systems))
        
        return context
    
    def process_pdf(self, file_path: str, use_cache: bool = True) -> PDFDocument:
        """Główna metoda do przetwarzania pliku PDF."""
        
        # Sprawdź cache
        if use_cache:
            cached = self.load_from_cache(file_path)
            if cached:
                return cached
        
        # Pobierz metadane pliku
        file_stats = os.stat(file_path)
        file_hash = self.calculate_file_hash(file_path)
        
        try:
            # Preferuj PyMuPDF
            text_content, structured_content = self.extract_text_pymupdf(file_path)
        except Exception:
            # Fallback do PyPDF2
            text_content = self.extract_text_pypdf2(file_path)
            structured_content = {'pages': [], 'method': 'pypdf2'}
        
        # Pobierz podstawowe metadane
        title = Path(file_path).stem
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata
            if metadata.get('title'):
                title = metadata['title']
            total_pages = len(doc)
            doc.close()
        except Exception:
            total_pages = len(text_content.split('--- Strona'))
            metadata = {}
        
        # Utwórz dokument PDF
        pdf_doc = PDFDocument(
            file_path=file_path,
            title=title,
            total_pages=total_pages,
            text_content=text_content,
            structured_content=structured_content,
            metadata=metadata,
            hash=file_hash,
            processed_date=datetime.now().isoformat()
        )
        
        # Zapisz do cache
        if use_cache:
            self.save_to_cache(pdf_doc)
        
        return pdf_doc
    
    def get_context_for_diagram_type(self, pdf_doc: PDFDocument, diagram_type: str) -> str:
        """Zwraca kontekst dostosowany do typu diagramu."""
        
        process_context = self.analyze_process_context(pdf_doc.text_content)
        
        if diagram_type.lower() in ['sequence', 'sekwencji']:
            return self._get_sequence_context(process_context, pdf_doc)
        elif diagram_type.lower() in ['activity', 'aktywności']:
            return self._get_activity_context(process_context, pdf_doc)
        elif diagram_type.lower() in ['class', 'klas']:
            return self._get_class_context(process_context, pdf_doc)
        elif diagram_type.lower() in ['component', 'komponentów']:
            return self._get_component_context(process_context, pdf_doc)
        else:
            return self._get_general_context(process_context, pdf_doc)
    
    def _get_sequence_context(self, context: ProcessContext, pdf_doc: PDFDocument) -> str:
        """Kontekst dla diagramu sekwencji."""
        return f"""
**KONTEKST Z DOKUMENTU PDF: {pdf_doc.title}**

**PROCES:** {context.process_name}

**UCZESTNICY PROCESU:**
{chr(10).join(f"- {actor}" for actor in context.actors[:10])}

**GŁÓWNE AKTYWNOŚCI:**
{chr(10).join(f"- {activity}" for activity in context.activities[:15])}

**SYSTEMY I KOMPONENTY:**
{chr(10).join(f"- {system}" for system in context.systems[:10])}

**PUNKTY DECYZYJNE:**
{chr(10).join(f"- {decision}" for decision in context.decisions[:8])}

**DODATKOWE INFORMACJE:**
- Dokument zawiera {pdf_doc.total_pages} stron
- Data przetwarzania: {pdf_doc.processed_date}
"""
    
    def _get_activity_context(self, context: ProcessContext, pdf_doc: PDFDocument) -> str:
        """Kontekst dla diagramu aktywności."""
        return f"""
**KONTEKST PROCESU Z PDF: {pdf_doc.title}**

**NAZWA PROCESU:** {context.process_name}

**ROLE I AKTORZY:**
{chr(10).join(f"- {actor}" for actor in context.actors)}

**SEKWENCJA DZIAŁAŃ:**
{chr(10).join(f"{i+1}. {activity}" for i, activity in enumerate(context.activities[:20]))}

**DECYZJE I WARUNKI:**
{chr(10).join(f"- {decision}" for decision in context.decisions)}

**SYSTEMY ZAANGAŻOWANE:**
{chr(10).join(f"- {system}" for system in context.systems)}
"""
    
    def _get_class_context(self, context: ProcessContext, pdf_doc: PDFDocument) -> str:
        """Kontekst dla diagramu klas."""
        return f"""
**ANALIZA DOMENY Z PDF: {pdf_doc.title}**

**PROCES BIZNESOWY:** {context.process_name}

**GŁÓWNE BYTY/ENCJE:**
{chr(10).join(f"- {system}" for system in context.systems)}

**ROLE W SYSTEMIE:**
{chr(10).join(f"- {actor}" for actor in context.actors)}

**OPERACJE BIZNESOWE:**
{chr(10).join(f"- {activity}" for activity in context.activities)}
"""
    
    def _get_component_context(self, context: ProcessContext, pdf_doc: PDFDocument) -> str:
        """Kontekst dla diagramu komponentów."""
        return f"""
**ARCHITEKTURA SYSTEMU Z PDF: {pdf_doc.title}**

**SYSTEM/PROCES:** {context.process_name}

**KOMPONENTY I SYSTEMY:**
{chr(10).join(f"- {system}" for system in context.systems)}

**UŻYTKOWNICY I ROLE:**
{chr(10).join(f"- {actor}" for actor in context.actors)}

**FUNKCJONALNOŚCI:**
{chr(10).join(f"- {activity}" for activity in context.activities[:15])}
"""
    
    def _get_general_context(self, context: ProcessContext, pdf_doc: PDFDocument) -> str:
        """Ogólny kontekst."""
        return f"""
**KONTEKST DOKUMENTU: {pdf_doc.title}**

**PROCES:** {context.process_name}
**AKTORZY:** {', '.join(context.actors[:5])}
**SYSTEMY:** {', '.join(context.systems[:5])}
**KLUCZOWE AKTYWNOŚCI:** {', '.join(context.activities[:8])}

Dokument zawiera szczegółowe informacje biznesowe, które mogą być użyte jako kontekst dla generowania diagramu.
"""

# Funkcje pomocnicze dla integracji z istniejącym kodem
def enhance_prompt_with_pdf_context(original_prompt: str, pdf_files: List[str], diagram_type: str) -> str:
    """Wzbogaca prompt o kontekst z plików PDF."""
    
    if not pdf_files:
        return original_prompt
    
    processor = PDFProcessor()
    pdf_contexts = []
    
    for pdf_file in pdf_files:
        try:
            pdf_doc = processor.process_pdf(pdf_file)
            context = processor.get_context_for_diagram_type(pdf_doc, diagram_type)
            pdf_contexts.append(context)
        except Exception as e:
            print(f"Błąd przetwarzania {pdf_file}: {e}")
    
    if pdf_contexts:
        enhanced_prompt = f"""
{original_prompt}

**DODATKOWY KONTEKST Z DOKUMENTÓW PDF:**

{chr(10).join(pdf_contexts)}

**INSTRUKCJA:** Wykorzystaj powyższy kontekst z dokumentów PDF do wzbogacenia diagramu o dodatkowe szczegóły, aktorów, systemy i procesy, które mogą być istotne dla kompletnego przedstawienia.
"""
        return enhanced_prompt
    
    return original_prompt