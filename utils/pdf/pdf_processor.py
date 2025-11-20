"""
Moduł do przetwarzania plików PDF i ekstrakcji kontekstu dla diagramów.
Zawiera zarówno lokalną analizę wzorcami jak i integrację z AI.
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
        
        # Sprawdź tryb analizy PDF z .env
        self.analysis_mode = os.getenv("PDF_ANALYSIS_MODE", "local").lower()
        
        # Inicjalizuj AI analyzer jeśli dostępny
        self._ai_analyzer = None
        if self.analysis_mode == "ai":
            try:
                from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer
                self._ai_analyzer = AIPDFAnalyzer()
            except ImportError:
                print("Warning: AI PDF analysis not available, falling back to local mode")
                self.analysis_mode = "local"
        
        # Wzorce dla różnych typów kontekstu - znacznie rozszerzone
        self.patterns = {
            'actors': [
                r'(?:użytkownik|klient|pracownik|administrator|operator|analityk|student|dziekan|dziekanat)',
                r'(?:user|client|employee|admin|operator|analyst|student|dean)',
                r'(?:role|rola):\s*([^.\n]+)',
                r'(?:aktor|actor):\s*([^.\n]+)',
                r'(?:uczestnik|participant):\s*([^.\n]+)',
                # Dodatkowe wzorce dla ról akademickich
                r'(?:rektor|prorektor|kierownik|sekretarz|dyrektor)',
                r'(?:wykładowca|profesor|doktor|magister)',
                r'(?:BOS|dziekanat|sekretariat)',
            ],
            'activities': [
                # Podstawowe wzorce aktywności
                r'(?:krok|etap|czynność|operacja|działanie):\s*([^.\n]+)',
                r'(?:step|stage|activity|operation|action):\s*([^.\n]+)',
                r'(?:proces|procedura|procedure):\s*([^.\n]+)',
                # Czasowniki wskazujące na operacje
                r'(?:składa|przyjmuje|przekazuje|rozpatruje|akceptuje|odrzuca|zwraca|informuje|archiwizuje)',
                r'(?:submit|receive|transfer|review|accept|reject|return|inform|archive)',
                r'(?:wykonuje|realizuje|przeprowadza|dokonuje|sprawdza|weryfikuje|zatwierdza)',
                r'(?:execute|perform|conduct|carry out|check|verify|approve)',
                # Wzorce dla operacji biznesowych
                r'(?:może|można|należy|trzeba|powinien)\s+([^.\n]+)',
                r'(?:can|may|should|must|need to)\s+([^.\n]+)',
                # Wzorce dla procesów
                r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s]{5,50})(?:\s+(?:podania|procesu|dokumentu))',
                r'([A-Z][a-z\s]{5,50})(?:\s+(?:application|process|document))',
            ],
            'decisions': [
                r'(?:jeśli|gdy|w przypadku gdy|decyzja|warunek)',
                r'(?:if|when|in case of|decision|condition)',
                r'(?:może|można):\s*([^.\n]+)',
                r'(?:can|may):\s*([^.\n]+)',
                r'(?:reguła biznesowa|business rule):\s*([^.\n]+)',
                r'(?:zaakceptować|odrzucić|zwrócić|approve|reject|return)',
                r'(?:pozytywna|negatywna)\s+(?:opinia|opinion)',
            ],
            'systems': [
                r'(?:system|aplikacja|baza danych|serwis|platforma)',
                r'(?:system|application|database|service|platform)',
                r'(?:API|interface|interfejs|portal)',
                r'(?:dziekanat|sekretariat|biuro|office|department)',
                r'(?:moduł|module|komponent|component)',
            ],
            'business_objects': [
                # Obiekty biznesowe - dokumenty, formularze, etc.
                r'(?:podanie|wniosek|formularz|dokument|zaświadczenie)',
                r'(?:application|form|document|certificate|request)',
                r'(?:umowa|kontrakt|contract|agreement)',
                r'(?:raport|report|sprawozdanie)',
                r'(?:załącznik|attachment|appendix)',
            ],
            'business_rules': [
                r'(?:reguła|rule|zasada|principle|warunek|condition)',
                r'(?:wymaganie|requirement|kryterium|criterion)',
                r'(?:ograniczenie|constraint|limitation)',
                r'(?:termin|deadline|czas|time limit)',
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
        """Analizuje tekst i wyciąga kontekst procesu biznesowego - ulepszona wersja."""
        context = ProcessContext(
            process_name="",
            actors=[],
            activities=[],
            decisions=[],
            data_flows=[],
            business_rules=[],
            systems=[]
        )
        
        # Normalizuj tekst
        text_normalized = re.sub(r'\s+', ' ', text.lower())
        
        # Znajdź nazwę procesu (ulepszona logika)
        title_patterns = [
            r'proces\s*biznesowy:\s*([^.\n]{10,100})',
            r'business\s*process:\s*([^.\n]{10,100})',
            r'proces:\s*([^.\n]{10,100})',
            r'^#\s*(.+)$',
            r'^\*\*(.+)\*\*$',
            r'^([A-ZĄĆĘŁŃÓŚŹŻ][^.\n]{10,80})$'
        ]
        
        lines = text.split('\n')
        for line in lines[:15]:  # Sprawdź pierwsze 15 linii
            for pattern in title_patterns:
                match = re.search(pattern, line.strip(), re.IGNORECASE)
                if match and not context.process_name:
                    context.process_name = match.group(1).strip()
                    break
            if context.process_name:
                break
        
        # Wyciągnij aktorów (ulepszone)
        for pattern in self.patterns['actors']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                actor = match.group(0) if match.lastindex is None else match.group(1)
                if actor and len(actor.strip()) > 2:
                    context.actors.append(actor.strip().title())
        
        # Wyciągnij aktywności i operacje biznesowe (znacznie ulepszone)
        activity_patterns = self.patterns['activities']
        
        # Dodatkowe wzorce specyficzne dla operacji biznesowych
        business_operation_patterns = [
            r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s]{2,}(?:podanie|wniosek|dokument|formularz)[a-ząćęłńóśźż\s]*)',
            r'([a-ząćęłńóśźż\s]*(?:składa|przyjmuje|przekazuje|rozpatruje|zatwierdza|odrzuca|archiwizuje)[a-ząćęłńóśźż\s]{5,50})',
            r'([a-ząćęłńóśźż\s]*(?:informuje|powiadamia|sprawdza|weryfikuje|kontroluje)[a-ząćęłńóśźż\s]{5,50})',
            r'((?:może|można|należy|powinien)[a-ząćęłńóśźż\s]{5,80})',
            # Wzorce dla pełnych zdań opisujących operacje
            r'([A-ZĄĆĘŁŃÓŚŹŻ][^.!?]*(?:wykonuje|realizuje|przeprowadza|dokonuje)[^.!?]*[.!?])',
            r'([A-ZĄĆĘŁŃÓŚŹŻ][^.!?]*(?:process|execute|perform|handle)[^.!?]*[.!?])',
        ]
        
        for pattern in activity_patterns + business_operation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                activity = match.group(0) if match.lastindex is None else match.group(1)
                if activity and len(activity.strip()) > 3:
                    # Oczyść i dodaj
                    activity_clean = re.sub(r'^\W+|\W+$', '', activity.strip())
                    # Filtruj zbyt krótkie lub niepotrzebne
                    if (len(activity_clean) > 8 and 
                        not any(skip in activity_clean.lower() for skip in 
                               ['system', 'może być', 'można', 'należy używać', 'diagram', 'notacja']) and
                        not re.match(r'^[a-z\s]*$', activity_clean)):  # Usuń same małe litery
                        context.activities.append(activity_clean.strip())
        
        # Wyciągnij decyzje i reguły biznesowe
        for pattern in self.patterns['decisions']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                decision = match.group(0) if match.lastindex is None else match.group(1)
                if decision and len(decision.strip()) > 3:
                    context.decisions.append(decision.strip())
        
        # Wyciągnij reguły biznesowe (nowa kategoria)
        if 'business_rules' in self.patterns:
            for pattern in self.patterns['business_rules']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    rule = match.group(0) if match.lastindex is None else match.group(1)
                    if rule and len(rule.strip()) > 3:
                        context.business_rules.append(rule.strip())
        
        # Wyciągnij systemy i komponenty
        for pattern in self.patterns['systems']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                system = match.group(0) if match.lastindex is None else match.group(1)
                if system and len(system.strip()) > 2:
                    context.systems.append(system.strip().title())
        
        # Wyciągnij obiekty biznesowe jeśli wzorzec istnieje
        if 'business_objects' in self.patterns:
            for pattern in self.patterns['business_objects']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    obj = match.group(0) if match.lastindex is None else match.group(1)
                    if obj and len(obj.strip()) > 2:
                        context.data_flows.append(obj.strip().title())
        
        # Deduplikacja i filtrowanie
        context.actors = list(set(filter(lambda x: len(x) > 2, context.actors)))[:15]
        context.activities = list(set(filter(lambda x: len(x) > 5, context.activities)))[:25]
        context.decisions = list(set(filter(lambda x: len(x) > 3, context.decisions)))[:15]
        context.systems = list(set(filter(lambda x: len(x) > 2, context.systems)))[:15]
        context.business_rules = list(set(filter(lambda x: len(x) > 3, context.business_rules)))[:15]
        context.data_flows = list(set(filter(lambda x: len(x) > 2, context.data_flows)))[:15]
        
        return context
    
    def debug_extraction(self, pdf_doc: PDFDocument) -> str:
        """Metoda debugująca - pokazuje co zostało wyekstraktowane z PDF."""
        context = self.analyze_process_context(pdf_doc.text_content)
        
        debug_info = f"""
**DEBUG: Analiza ekstraktów z PDF: {pdf_doc.title}**

**PROCES:** {context.process_name}

**AKTORZY ({len(context.actors)}):**
{chr(10).join(f"- {actor}" for actor in context.actors)}

**AKTYWNOŚCI ({len(context.activities)}):**
{chr(10).join(f"- {activity}" for activity in context.activities)}

**SYSTEMY ({len(context.systems)}):**
{chr(10).join(f"- {system}" for system in context.systems)}

**DECYZJE ({len(context.decisions)}):**
{chr(10).join(f"- {decision}" for decision in context.decisions)}

**REGUŁY BIZNESOWE ({len(context.business_rules)}):**
{chr(10).join(f"- {rule}" for rule in context.business_rules)}

**OBIEKTY BIZNESOWE ({len(context.data_flows)}):**
{chr(10).join(f"- {obj}" for obj in context.data_flows)}

**PIERWSZE 500 ZNAKÓW TEKSTU:**
{pdf_doc.text_content[:500]}...
"""
        return debug_info
    
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
    
    def get_context_for_diagram_type(self, pdf_doc: PDFDocument, diagram_type: str, progress_callback=None) -> str:
        """Zwraca kontekst dostosowany do typu diagramu - z wyborem trybu AI lub lokalnego."""
        
        # Jeśli tryb AI i analyzer dostępny
        if self.analysis_mode == "ai" and self._ai_analyzer:
            try:
                return self._ai_analyzer.get_enhanced_context_for_diagram(pdf_doc, diagram_type, progress_callback)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ AI analysis failed: {e}, przełączanie na tryb lokalny")
                print(f"AI analysis failed: {e}, falling back to local")
        
        # Fallback lub tryb lokalny
        if progress_callback:
            progress_callback("📝 Używanie lokalnej analizy wzorców...")
            
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
        """Kontekst dla diagramu aktywności - ulepszona wersja."""
        
        # Filtruj aktywności aby usunąć zbyt ogólne
        filtered_activities = []
        for activity in context.activities:
            if len(activity) > 8 and not any(skip in activity.lower() for skip in ['system', 'może być', 'można']):
                filtered_activities.append(activity)
        
        return f"""**KONTEKST PROCESU Z PDF: {pdf_doc.title}**

**NAZWA PROCESU:** {context.process_name}

**ROLE I AKTORZY:**
{chr(10).join(f"- {actor}" for actor in context.actors[:10]) if context.actors else "- (nie zidentyfikowano)"}

**SEKWENCJA DZIAŁAŃ:**
{chr(10).join(f"{i+1}. {activity}" for i, activity in enumerate(filtered_activities[:25])) if filtered_activities else "- (nie zidentyfikowano działań)"}

**DECYZJE I WARUNKI:**
{chr(10).join(f"- {decision}" for decision in context.decisions[:15]) if context.decisions else "- (nie zidentyfikowano)"}

**REGUŁY BIZNESOWE:**
{chr(10).join(f"- {rule}" for rule in context.business_rules[:10]) if context.business_rules else "- (nie zidentyfikowano)"}

**SYSTEMY ZAANGAŻOWANE:**
{chr(10).join(f"- {system}" for system in context.systems[:10]) if context.systems else "- (nie zidentyfikowano)"}

**OBIEKTY BIZNESOWE:**
{chr(10).join(f"- {obj}" for obj in context.data_flows[:10]) if context.data_flows else "- (nie zidentyfikowano)"}

**INSTRUKCJA:** Wykorzystaj powyższy kontekst do stworzenia diagramu aktywności pokazującego przepływ procesu z uwzględnieniem wszystkich ról, decyzji i działań."""
    
    def _get_class_context(self, context: ProcessContext, pdf_doc: PDFDocument) -> str:
        """Kontekst dla diagramu klas - znacznie ulepszona wersja."""
        
        # Filtruj i pogrupuj operacje biznesowe
        business_operations = []
        for activity in context.activities:
            # Wyłącz zbyt ogólne lub niepotrzebne frazy
            if any(skip in activity.lower() for skip in ['może', 'można', 'należy', 'powinien', 'system', 'proces']):
                continue
            if len(activity) > 10:  # Tylko znaczące operacje
                business_operations.append(activity)
        
        # Filtruj systemy/encje
        entities = []
        for system in context.systems:
            if len(system) > 2 and system.lower() not in ['system', 'serwis', 'service']:
                entities.append(system)
        
        # Dodaj obiekty biznesowe jako encje
        for obj in context.data_flows:
            if len(obj) > 2:
                entities.append(obj)
        
        # Filtruj aktorów
        filtered_actors = [actor for actor in context.actors if len(actor) > 3]
        
        return f"""**ANALIZA DOMENY Z PDF: {pdf_doc.title}**

**PROCES BIZNESOWY:** {context.process_name}

**GŁÓWNE BYTY/ENCJE:**
{chr(10).join(f"- {entity}" for entity in entities[:15]) if entities else "- (nie zidentyfikowano)"}

**ROLE W SYSTEMIE:**
{chr(10).join(f"- {actor}" for actor in filtered_actors[:10]) if filtered_actors else "- (nie zidentyfikowano)"}

**OPERACJE BIZNESOWE:**
{chr(10).join(f"- {operation}" for operation in business_operations[:20]) if business_operations else "- (nie zidentyfikowano operacji)"}

**REGUŁY BIZNESOWE:**
{chr(10).join(f"- {rule}" for rule in context.business_rules[:10]) if context.business_rules else "- (nie zidentyfikowano)"}

**PUNKTY DECYZYJNE:**
{chr(10).join(f"- {decision}" for decision in context.decisions[:8]) if context.decisions else "- (nie zidentyfikowano)"}

**INSTRUKCJA:** Wykorzystaj powyższy kontekst z dokumentów PDF do wzbogacenia diagramu o dodatkowe szczegóły, aktorów, systemy i procesy, które mogą być istotne dla kompletnego przedstawienia."""
    
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
def enhance_prompt_with_pdf_context(original_prompt: str, pdf_files: List[str], diagram_type: str, progress_callback=None) -> str:
    """Wzbogaca prompt o kontekst z plików PDF - z obsługą AI analysis i progress tracking."""
    
    if not pdf_files:
        return original_prompt
    
    processor = PDFProcessor()
    pdf_contexts = []
    
    # Sprawdzenie czy AI mode jest włączony
    analysis_mode = processor.analysis_mode
    
    if progress_callback:
        progress_callback(f"🔍 Analiza {len(pdf_files)} plików PDF w trybie: {analysis_mode.upper()}")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            if progress_callback:
                progress_callback(f"📄 Przetwarzanie pliku {i}/{len(pdf_files)}: {Path(pdf_file).name}")
                
            pdf_doc = processor.process_pdf(pdf_file)
            
            # Używaj AI analyzer jeśli dostępny, w przeciwnym razie lokalny
            context = processor.get_context_for_diagram_type(pdf_doc, diagram_type, progress_callback)
            
            # Dodaj informację o trybie analizy
            mode_info = f"\n[Metoda analizy: {analysis_mode.upper()}]"
            context_with_mode = context + mode_info
            pdf_contexts.append(context_with_mode)
            
        except Exception as e:
            error_msg = f"Błąd przetwarzania {pdf_file}: {e}"
            if progress_callback:
                progress_callback(f"❌ {error_msg}")
            print(error_msg)
    
    if pdf_contexts:
        if progress_callback:
            progress_callback("✅ Finalizowanie wzbogaconego promptu...")
            
        # Dostosuj instrukcję w zależności od trybu analizy
        if analysis_mode == "ai":
            instruction = "**INSTRUKCJA:** Powyższy kontekst został wygenerowany przez AI na podstawie analizy dokumentów PDF. Wykorzystaj te szczegółowe informacje do stworzenia kompletnego i precyzyjnego diagramu uwzględniającego wszystkie istotne elementy procesów biznesowych."
        else:
            instruction = "**INSTRUKCJA:** Wykorzystaj powyższy kontekst z dokumentów PDF do wzbogacenia diagramu o dodatkowe szczegóły, aktorów, systemy i procesy, które mogą być istotne dla kompletnego przedstawienia."
        
        enhanced_prompt = f"""
{original_prompt}

**DODATKOWY KONTEKST Z DOKUMENTÓW PDF:**

{chr(10).join(pdf_contexts)}

{instruction}
"""
        if progress_callback:
            progress_callback("🎯 Prompt wzbogacony o kontekst PDF")
            
        return enhanced_prompt
    
    return original_prompt