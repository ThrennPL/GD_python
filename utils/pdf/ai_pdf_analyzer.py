"""
Agentowy system analizy PDF wykorzystujący modele AI.
Pozwala na głęboką analizę dokumentów PDF z wykorzystaniem sztucznej inteligencji.
"""

import os
import requests
import json
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING, Any
from dataclasses import dataclass
from datetime import datetime
import re
from pathlib import Path
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z .env
load_dotenv()

from utils.logger_utils import log_info, log_error, log_debug


@dataclass
class ProcessContext:
    """Kontekst procesu biznesowego - lokalna definicja dla AI analyzera."""
    process_name: str = ""
    actors: List[str] = None
    activities: List[str] = None
    decisions: List[str] = None
    data_flows: List[str] = None
    business_rules: List[str] = None
    systems: List[str] = None
    
    def __post_init__(self):
        if self.actors is None:
            self.actors = []
        if self.activities is None:
            self.activities = []
        if self.decisions is None:
            self.decisions = []
        if self.data_flows is None:
            self.data_flows = []
        if self.business_rules is None:
            self.business_rules = []
        if self.systems is None:
            self.systems = []


@dataclass 
class PDFDocument:
    """Reprezentacja dokumentu PDF - lokalna definicja."""
    file_path: str = ""
    title: str = ""
    total_pages: int = 0
    text_content: str = ""
    structured_content: Dict = None
    metadata: Dict = None
    hash: str = ""
    processed_date: str = ""
    
    def __post_init__(self):
        if self.structured_content is None:
            self.structured_content = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AIAnalysisResult:
    """Wynik analizy AI dokumentu PDF."""
    original_context: ProcessContext
    ai_enhanced_context: ProcessContext
    analysis_summary: str
    confidence_score: float
    processing_time: float
    model_used: str
    tokens_used: int


class AIPDFAnalyzer:
    """Agentowy analyzer PDF wykorzystujący modele AI."""
    
    def __init__(self):
        # Konfiguracja z .env
        self.analysis_mode = os.getenv("PDF_ANALYSIS_MODE", "local").lower()
        self.model = os.getenv("PDF_ANALYSIS_MODEL", os.getenv("API_DEFAULT_MODEL", "gemini"))
        self.prompt_language = os.getenv("PDF_ANALYSIS_PROMPT_LANG", "pl").lower()
        
        # Połączenie z modelem (ta sama konfiguracja co diagramy)
        self.chat_url = os.getenv("CHAT_URL", "")
        self.api_key = os.getenv("API_KEY", "")
        self.model_provider = os.getenv("MODEL_PROVIDER", "local").lower()
        
        # Podstawowy procesor PDF (tylko jeśli potrzebny)
        self.pdf_processor = None
        
        # Cache wyników AI
        self.ai_cache = {}
        
        log_info(f"AIPDFAnalyzer initialized: mode={self.analysis_mode}, model={self.model}, provider={self.model_provider}")
        
        # Sprawdź możliwości modelu
        self.pdf_supported = self._check_pdf_support()
        log_info(f"PDF support: {self.pdf_supported}")
    
    def _check_pdf_support(self) -> bool:
        """Sprawdza czy model obsługuje bezpośrednie przetwarzanie PDF."""
        # Lista modeli obsługujących PDF
        pdf_capable_models = [
            "models/gemini-2.0-flash",
            "models/gemini-1.5-pro", 
            "models/gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]
        
        # Sprawdź czy provider obsługuje PDF
        if self.model_provider != "gemini":
            log_info(f"Provider {self.model_provider} nie obsługuje bezpośredniego PDF")
            return False
            
        # Sprawdź czy model jest w liście obsługujących
        model_supports = any(model in self.model.lower() for model in [m.lower() for m in pdf_capable_models])
        
        if not model_supports:
            log_info(f"Model {self.model} nie obsługuje bezpośredniego PDF")
            return False
            
        # Sprawdź dostępność Google File API
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            log_info("Google File API dostępne")
            return True
        except Exception as e:
            log_error(f"Brak dostępu do Google File API: {e}")
            return False
    
    def get_analysis_prompt(self, content: str, diagram_type: str) -> str:
        """Generuje prompt analizy dla danego typu diagramu."""
        prompts = {
            "activity": """
Przeanalizuj ten dokument PDF i zidentyfikuj elementy procesu biznesowego:

1. ROLE I AKTORZY - Kto jest zaangażowany w proces?
2. SEKWENCJA DZIAŁAŃ - Jakie są główne kroki procesu? 
3. PUNKTY DECYZYJNE - Gdzie występują rozgałęzienia?
4. WARUNKI I ZASADY - Jakie warunki muszą być spełnione?
5. REZULTATY I KOŃCE - Jak kończy się proces?

Skoncentruj się na praktycznych aspektach implementacji procesu.
Uwzględnij wszystkie wymienione role, zadania i przepływy.
            """,
            
            "sequence": """
Przeanalizuj ten dokument PDF pod kątem sekwencji interakcji:

1. UCZESTNICY - Kto komunikuje się w systemie?
2. KOMUNIKACJA - Jakie wiadomości są wymieniane?
3. CHRONOLOGIA - W jakiej kolejności następuje komunikacja?
4. OBIEKTY - Jakie obiekty/komponenty są używane?
5. LIFECYCLE - Jak długo trwają interakcje?

Zwróć szczególną uwagę na przepływ danych i komunikację.
            """,
            
            "class": """
Przeanalizuj ten dokument PDF pod kątem struktury obiektowej:

1. KLASY - Jakie główne klasy/obiekty są opisane?
2. ATRYBUTY - Jakie właściwości mają te obiekty?
3. METODY - Jakie operacje mogą wykonywać?
4. RELACJE - Jak obiekty są ze sobą połączone?
5. HIERARCHIE - Czy istnieją relacje dziedziczenia?

Skup się na strukture danych i relacjach między obiektami.
            """,
            
            "component": """
Przeanalizuj ten dokument PDF pod kątem architektury systemu:

1. KOMPONENTY - Jakie główne elementy systemu są opisane?
2. INTERFEJSY - Jak komponenty się komunikują?
3. ZALEŻNOŚCI - Które komponenty od siebie zależą?
4. WDROŻENIA - Jak komponenty są implementowane?
5. KONFIGURACJA - Jak system jest skonfigurowany?

Uwzględnij wszystkie aspekty techniczne i organizacyjne.
            """
        }
        
        base_prompt = prompts.get(diagram_type, prompts["activity"])
        
        if content:
            return f"{base_prompt}\n\nTekst do analizy:\n{content}"
        else:
            return base_prompt
    
    def analyze_pdf_direct(self, pdf_path: str, diagram_type: str = "general", progress_callback=None) -> Tuple[str, Dict]:
        """Bezpośrednia analiza PDF przez model AI z informacjami o postępie."""
        
        if not self.pdf_supported:
            raise ValueError("Model nie obsługuje bezpośredniej analizy PDF")
            
        try:
            import google.generativeai as genai
            
            if progress_callback:
                progress_callback("Konfiguracja modelu AI...")
                
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            if progress_callback:
                progress_callback(f"Przesyłanie pliku PDF: {Path(pdf_path).name}...")
                
            start_time = datetime.now()
            
            # Upload PDF
            uploaded_file = genai.upload_file(
                path=pdf_path,
                display_name=f"PDF Analysis - {Path(pdf_path).name}"
            )
            
            upload_time = (datetime.now() - start_time).total_seconds()
            
            if progress_callback:
                progress_callback(f"Analiza dokumentu przez AI ({self.model})...")
                
            # Przygotuj prompt
            prompt = self.get_analysis_prompt("", diagram_type)
            prompt += "\n\nPrzeanalizuj załączony dokument PDF zgodnie z powyższymi wytycznymi."
            
            # Analiza przez AI
            analysis_start = datetime.now()
            response = model.generate_content([
                prompt,
                uploaded_file
            ])
            
            analysis_time = (datetime.now() - analysis_start).total_seconds()
            total_time = upload_time + analysis_time
            
            if progress_callback:
                progress_callback("Czyszczenie plików tymczasowych...")
                
            # Cleanup
            genai.delete_file(uploaded_file.name)
            
            if progress_callback:
                progress_callback(f"Analiza zakończona ({total_time:.1f}s)")
                
            metadata = {
                "processing_time": total_time,
                "upload_time": upload_time,
                "analysis_time": analysis_time,
                "method": "direct_pdf",
                "model_used": self.model,
                "success": True,
                "file_size": Path(pdf_path).stat().st_size,
                "tokens_used": len(response.text.split()) if hasattr(response, 'text') else 0
            }
            
            return response.text, metadata
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Błąd analizy PDF: {str(e)}")
                
            log_error(f"Direct PDF analysis failed: {e}")
            metadata = {
                "processing_time": 0,
                "method": "direct_pdf", 
                "model_used": self.model,
                "success": False,
                "error": str(e)
            }
            return "", metadata
        """Generuje prompt dla AI do analizy PDF."""
        
        if self.prompt_language == "en":
            base_prompt = f"""
You are an expert business process analyst. Analyze the following PDF document content and extract comprehensive business context.

DOCUMENT CONTENT:
{pdf_text[:4000]}...

ANALYSIS TASKS:
1. BUSINESS PROCESS IDENTIFICATION:
   - Main business process name and description
   - Process scope and objectives
   - Process triggers and end conditions

2. STAKEHOLDER ANALYSIS:
   - Primary actors/roles involved in the process
   - Secondary stakeholders and their involvement
   - External parties and their interactions

3. BUSINESS OPERATIONS EXTRACTION:
   - Detailed list of business operations/activities
   - Operation sequences and dependencies
   - Critical business rules and constraints

4. SYSTEM COMPONENTS:
   - IT systems, applications, and platforms involved
   - Data objects, documents, and information flows
   - Integration points and interfaces

5. DECISION POINTS:
   - Business decisions and approval gates
   - Conditional logic and branching scenarios
   - Exception handling and alternative flows

6. DOMAIN MODEL:
   - Key business entities and their relationships
   - Data attributes and business objects
   - Business rules and validation criteria

TARGET DIAGRAM TYPE: {diagram_type}

Provide your analysis in structured format with specific, actionable details suitable for {diagram_type} diagram generation.
Focus on extracting concrete, implementable elements rather than abstract descriptions.
"""
        else:  # Polish
            base_prompt = f"""
Jesteś ekspertem analizy procesów biznesowych. Przeanalizuj zawartość dokumentu PDF i wyciągnij komprehensywny kontekst biznesowy.

ZAWARTOŚĆ DOKUMENTU:
{pdf_text[:4000]}...

ZADANIA ANALIZY:
1. IDENTYFIKACJA PROCESU BIZNESOWEGO:
   - Nazwa i opis głównego procesu biznesowego
   - Zakres i cele procesu
   - Wyzwalacze i warunki zakończenia procesu

2. ANALIZA INTERESARIUSZY:
   - Główni aktorzy/role zaangażowani w proces
   - Drugorzędni interesariusze i ich udział
   - Strony zewnętrzne i ich interakcje

3. EKSTRAKCJA OPERACJI BIZNESOWYCH:
   - Szczegółowa lista operacji/działań biznesowych
   - Sekwencje operacji i zależności
   - Kluczowe reguły biznesowe i ograniczenia

4. KOMPONENTY SYSTEMOWE:
   - Systemy IT, aplikacje i platformy zaangażowane
   - Obiekty danych, dokumenty i przepływy informacji
   - Punkty integracji i interfejsy

5. PUNKTY DECYZYJNE:
   - Decyzje biznesowe i bramy zatwierdzenia
   - Logika warunkowa i scenariusze rozgałęzień
   - Obsługa wyjątków i przepływy alternatywne

6. MODEL DOMENY:
   - Kluczowe encje biznesowe i ich relacje
   - Atrybuty danych i obiekty biznesowe
   - Reguły biznesowe i kryteria walidacji

DOCELOWY TYP DIAGRAMU: {diagram_type}

Przedstaw analizę w strukturalnym formacie ze szczegółowymi, wykonalnymi detalami odpowiednimi do generowania diagramu {diagram_type}.
Skup się na wyciągnięciu konkretnych, implementowalnych elementów zamiast abstrakcyjnych opisów.
"""
        
        return base_prompt
    
    def call_ai_model(self, prompt: str) -> Tuple[str, Dict]:
        """Wywołuje model AI do analizy - używa tego samego mechanizmu co główna aplikacja."""
        start_time = datetime.now()
        
        # Dla Gemini używamy SDK (tak jak główna aplikacja)
        if self.model_provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model)
                
                # Konfiguracja generacji
                generation_config = genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                    top_k=40,
                    top_p=0.95
                )
                
                response = model.generate_content(prompt, generation_config=generation_config)
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Pobierz odpowiedź (tak jak w głównej aplikacji)
                if hasattr(response, "text"):
                    ai_response = response.text
                elif hasattr(response, "candidates"):
                    ai_response = response.candidates[0].content.parts[0].text
                else:
                    ai_response = str(response)
                
                # Aproksymacja tokenów (Gemini SDK nie zawsze zwraca usage)
                tokens_used = len(prompt.split()) + len(ai_response.split())
                
                metadata = {
                    "processing_time": processing_time,
                    "tokens_used": tokens_used,
                    "model_used": self.model,
                    "success": True,
                    "method": "google_sdk"
                }
                
                log_info(f"Gemini SDK AI PDF analysis completed: {processing_time:.2f}s, ~{tokens_used} tokens")
                return ai_response, metadata
                
            except Exception as e:
                log_error(f"Gemini SDK call failed: {str(e)}")
                metadata = {
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "tokens_used": 0,
                    "model_used": self.model,
                    "success": False,
                    "error": str(e),
                    "method": "google_sdk"
                }
                return "", metadata
        
        # Dla OpenAI i local - używamy REST API
        headers = {
            "Content-Type": "application/json"
        }
        
        # Konfiguracja dla różnych providerów
        if self.model_provider == "openai":
            headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2048
            }
        else:  # local
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2048
            }
        
        try:
            response = requests.post(self.chat_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result_data = response.json()
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Wyciągnij odpowiedź
            ai_response = result_data["choices"][0]["message"]["content"]
            tokens_used = result_data.get("usage", {}).get("total_tokens", 0)
            
            metadata = {
                "processing_time": processing_time,
                "tokens_used": tokens_used,
                "model_used": self.model,
                "success": True,
                "method": "rest_api"
            }
            
            log_info(f"REST API AI PDF analysis completed: {processing_time:.2f}s, {tokens_used} tokens")
            return ai_response, metadata
            
        except Exception as e:
            log_error(f"REST API call failed: {str(e)}")
            metadata = {
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "tokens_used": 0,
                "model_used": self.model,
                "success": False,
                "error": str(e),
                "method": "rest_api"
            }
            return "", metadata
    
    def format_context_for_diagram(self, ai_response: Dict, diagram_type: str) -> str:
        """Formatuje odpowiedź AI do kontekstu dla określonego typu diagramu."""
        
        # Tymczasowa metoda do testów - używa prostego formatowania
        if not ai_response:
            return "Brak danych do formatowania."
        
        # Podstawowe formatowanie
        result = f"**KONTEKST AI ({diagram_type.upper()}):**\n\n"
        
        if 'actors' in ai_response:
            result += f"**AKTORZY:** {', '.join(ai_response['actors'])}\n"
        
        if 'activities' in ai_response:
            result += f"**AKTYWNOŚCI:** {', '.join(ai_response['activities'][:5])}\n"
        
        if 'systems' in ai_response:
            result += f"**SYSTEMY:** {', '.join(ai_response['systems'])}\n"
        
        if 'confidence' in ai_response:
            result += f"**PEWNOŚĆ:** {ai_response['confidence']*100:.1f}%\n"
        
        return result
    
    def parse_ai_response(self, ai_response: str) -> ProcessContext:
        """Parsuje odpowiedź AI do struktury ProcessContext."""
        
        enhanced_context = ProcessContext(
            process_name="",
            actors=[],
            activities=[],
            decisions=[],
            data_flows=[],
            business_rules=[],
            systems=[]
        )
        
        # Wyciągnij informacje z odpowiedzi AI using patterns
        lines = ai_response.split('\n')
        
        current_section = ""
        for line in lines:
            line = line.strip()
            
            # Identyfikuj sekcje
            if "proces" in line.lower() and ("nazwa" in line.lower() or "name" in line.lower()):
                current_section = "process"
            elif "aktor" in line.lower() or "role" in line.lower() or "stakeholder" in line.lower():
                current_section = "actors"
            elif "operacj" in line.lower() or "operation" in line.lower() or "działan" in line.lower():
                current_section = "activities"
            elif "system" in line.lower() or "komponent" in line.lower():
                current_section = "systems"
            elif "decyzj" in line.lower() or "decision" in line.lower():
                current_section = "decisions"
            elif "reguł" in line.lower() or "rule" in line.lower():
                current_section = "business_rules"
            elif "dane" in line.lower() or "data" in line.lower() or "dokument" in line.lower():
                current_section = "data_flows"
            
            # Wyciągnij zawartość dla każdej sekcji
            if line.startswith(('-', '*', '•')) and current_section:
                content = re.sub(r'^[-*•]\s*', '', line).strip()
                
                if content and len(content) > 3:
                    if current_section == "process" and not enhanced_context.process_name:
                        enhanced_context.process_name = content
                    elif current_section == "actors":
                        enhanced_context.actors.append(content)
                    elif current_section == "activities":
                        enhanced_context.activities.append(content)
                    elif current_section == "systems":
                        enhanced_context.systems.append(content)
                    elif current_section == "decisions":
                        enhanced_context.decisions.append(content)
                    elif current_section == "business_rules":
                        enhanced_context.business_rules.append(content)
                    elif current_section == "data_flows":
                        enhanced_context.data_flows.append(content)
        
        # Deduplikuj i ogranicz
        enhanced_context.actors = list(set(enhanced_context.actors))[:15]
        enhanced_context.activities = list(set(enhanced_context.activities))[:25]
        enhanced_context.systems = list(set(enhanced_context.systems))[:15]
        enhanced_context.decisions = list(set(enhanced_context.decisions))[:15]
        enhanced_context.business_rules = list(set(enhanced_context.business_rules))[:15]
        enhanced_context.data_flows = list(set(enhanced_context.data_flows))[:15]
        
        return enhanced_context
    
    def analyze_pdf_document(self, pdf_doc: PDFDocument, diagram_type: str = "general") -> AIAnalysisResult:
        """Główna metoda analizy dokumentu PDF."""
        
        # Sprawdź tryb analizy
        if self.analysis_mode == "local":
            log_info("Using local PDF analysis mode")
            return self._local_analysis(pdf_doc, diagram_type)
        
        # Analiza AI
        log_info(f"Using AI PDF analysis mode: {self.model_provider}")
        
        # Cache check
        cache_key = f"{pdf_doc.hash}_{diagram_type}_{self.model}"
        if cache_key in self.ai_cache:
            log_debug(f"Using cached AI analysis for {pdf_doc.title}")
            return self.ai_cache[cache_key]
        
        # Podstawowa analiza
        original_context = self.pdf_processor.analyze_process_context(pdf_doc.text_content)
        
        # Generuj prompt dla AI
        prompt = self.get_analysis_prompt(pdf_doc.text_content, diagram_type)
        
        # Wywołaj AI
        ai_response, metadata = self.call_ai_model(prompt)
        
        if not metadata.get("success", False):
            log_error("AI analysis failed, falling back to local analysis")
            return self._local_analysis(pdf_doc, diagram_type)
        
        # Parsuj odpowiedź AI
        ai_enhanced_context = self.parse_ai_response(ai_response)
        
        # Połącz z podstawową analizą
        merged_context = self._merge_contexts(original_context, ai_enhanced_context)
        
        # Stwórz wynik
        result = AIAnalysisResult(
            original_context=original_context,
            ai_enhanced_context=merged_context,
            analysis_summary=ai_response[:500] + "..." if len(ai_response) > 500 else ai_response,
            confidence_score=0.8 if len(merged_context.activities) > 5 else 0.6,
            processing_time=metadata["processing_time"],
            model_used=metadata["model_used"],
            tokens_used=metadata["tokens_used"]
        )
        
        # Cache result
        self.ai_cache[cache_key] = result
        
        log_info(f"AI PDF analysis completed: {len(merged_context.activities)} activities, confidence: {result.confidence_score}")
        return result
    
    def _local_analysis(self, pdf_doc: PDFDocument, diagram_type: str) -> AIAnalysisResult:
        """Fallback do lokalnej analizy."""
        context = self.pdf_processor.analyze_process_context(pdf_doc.text_content)
        
        return AIAnalysisResult(
            original_context=context,
            ai_enhanced_context=context,
            analysis_summary="Local pattern-based analysis",
            confidence_score=0.5,
            processing_time=0.1,
            model_used="local_patterns",
            tokens_used=0
        )
    
    def _merge_contexts(self, original: ProcessContext, ai_enhanced: ProcessContext) -> ProcessContext:
        """Łączy kontekst lokalny z wynikami AI."""
        merged = ProcessContext(
            process_name=ai_enhanced.process_name or original.process_name,
            actors=list(set(original.actors + ai_enhanced.actors))[:15],
            activities=list(set(original.activities + ai_enhanced.activities))[:30],
            decisions=list(set(original.decisions + ai_enhanced.decisions))[:15],
            data_flows=list(set(original.data_flows + ai_enhanced.data_flows))[:15],
            business_rules=list(set(original.business_rules + ai_enhanced.business_rules))[:15],
            systems=list(set(original.systems + ai_enhanced.systems))[:15]
        )
        
        return merged
    
    def get_enhanced_context_for_diagram(self, pdf_doc: PDFDocument, diagram_type: str, progress_callback=None) -> str:
        """Zwraca wzbogacony kontekst dla konkretnego typu diagramu - z inteligentnym wyborem metody."""
        
        # Smart method selection z informacjami o postępie
        if progress_callback:
            progress_callback("Sprawdzanie możliwości modelu...")
            
        if self.pdf_supported and hasattr(pdf_doc, 'file_path') and Path(pdf_doc.file_path).exists():
            # Sprawdź rozmiar pliku
            file_size = Path(pdf_doc.file_path).stat().st_size
            max_size = 10 * 1024 * 1024  # 10MB limit dla direct PDF
            
            if file_size <= max_size:
                if progress_callback:
                    progress_callback("🚀 Wybrano metodę: Bezpośrednia analiza PDF")
                    
                try:
                    return self._analyze_with_direct_pdf(pdf_doc, diagram_type, progress_callback)
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"⚠️ Błąd bezpośredniej analizy: {e}. Przełączanie na text extraction...")
                    log_error(f"Direct PDF failed, falling back to text: {e}")
            else:
                if progress_callback:
                    progress_callback(f"📄 Plik za duży ({file_size/1024/1024:.1f}MB). Używanie text extraction...")
        
        # Fallback: Text extraction method
        if progress_callback:
            progress_callback("📝 Używanie metody: Text Extraction + AI")
            
        return self._analyze_with_text_extraction(pdf_doc, diagram_type, progress_callback)
    
    def _analyze_with_direct_pdf(self, pdf_doc: PDFDocument, diagram_type: str, progress_callback=None) -> str:
        """Analiza przez bezpośrednie przesłanie PDF."""
        
        try:
            import google.generativeai as genai
            
            if progress_callback:
                progress_callback("Konfiguracja modelu AI...")
                
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            if progress_callback:
                progress_callback(f"Przesyłanie pliku PDF: {Path(pdf_doc.file_path).name}...")
                
            start_time = datetime.now()
            
            # Upload PDF
            uploaded_file = genai.upload_file(
                path=pdf_doc.file_path,
                display_name=f"PDF Analysis - {Path(pdf_doc.file_path).name}"
            )
            
            upload_time = (datetime.now() - start_time).total_seconds()
            
            if progress_callback:
                progress_callback(f"Analiza dokumentu przez AI ({self.model})...")
                
            # Przygotuj prompt
            prompt = self.get_analysis_prompt("", diagram_type)
            prompt += "\n\nPrzeanalizuj załączony dokument PDF zgodnie z powyższymi wytycznymi."
            
            # Analiza przez AI
            analysis_start = datetime.now()
            response = model.generate_content([
                prompt,
                uploaded_file
            ])
            
            analysis_time = (datetime.now() - analysis_start).total_seconds()
            total_time = upload_time + analysis_time
            
            if progress_callback:
                progress_callback("Czyszczenie plików tymczasowych...")
                
            # Cleanup
            genai.delete_file(uploaded_file.name)
            
            if progress_callback:
                progress_callback(f"✅ Analiza zakończona ({total_time:.1f}s)")
                
            # Parse i format response
            enhanced_context = self.parse_ai_response(response.text)
            result = AIAnalysisResult(
                original_context=ProcessContext(),
                ai_enhanced_context=enhanced_context,
                analysis_summary=f"Bezpośrednia analiza PDF w {total_time:.1f}s",
                confidence_score=0.9,
                processing_time=total_time,
                model_used=self.model,
                tokens_used=len(response.text.split()) if hasattr(response, 'text') else 0
            )
            
            return self._format_context_by_type(enhanced_context, pdf_doc, result, diagram_type)
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Błąd analizy PDF: {str(e)}")
            raise e
    
    def _analyze_with_text_extraction(self, pdf_doc: PDFDocument, diagram_type: str, progress_callback=None) -> str:
        """Analiza przez text extraction."""
        
        if progress_callback:
            progress_callback("Przygotowywanie promptu z tekstu...")
            
        # Przygotuj prompt z ekstraktowanym tekstem
        prompt = self.get_analysis_prompt(pdf_doc.text_content[:5000], diagram_type)
        
        if progress_callback:
            progress_callback(f"Analiza przez AI ({self.model})...")
            
        # Wywołaj AI
        ai_response, metadata = self.call_ai_model(prompt)
        
        if metadata["success"]:
            if progress_callback:
                progress_callback(f"✅ Analiza zakończona ({metadata['processing_time']:.1f}s)")
                
            # Parse i format
            enhanced_context = self.parse_ai_response(ai_response)
            result = AIAnalysisResult(
                original_context=ProcessContext(),
                ai_enhanced_context=enhanced_context,
                analysis_summary=f"Text extraction + AI w {metadata['processing_time']:.1f}s",
                confidence_score=0.8,
                processing_time=metadata['processing_time'],
                model_used=metadata['model_used'],
                tokens_used=metadata['tokens_used']
            )
            
            return self._format_context_by_type(enhanced_context, pdf_doc, result, diagram_type)
        else:
            if progress_callback:
                progress_callback(f"❌ Błąd analizy AI: {metadata.get('error', 'Unknown')}")
            raise Exception(f"AI analysis failed: {metadata.get('error', 'Unknown')}")
    
    def _format_context_by_type(self, context: ProcessContext, pdf_doc: PDFDocument, result: AIAnalysisResult, diagram_type: str) -> str:
        """Formatuje kontekst dla określonego typu diagramu."""
        
        if diagram_type.lower() in ['class', 'klas']:
            return self._format_class_context(context, pdf_doc, result)
        elif diagram_type.lower() in ['activity', 'aktywności']:
            return self._format_activity_context(context, pdf_doc, result)
        elif diagram_type.lower() in ['sequence', 'sekwencji']:
            return self._format_sequence_context(context, pdf_doc, result)
        else:
            return self._format_general_context(context, pdf_doc, result)
    
    def _format_class_context(self, context: ProcessContext, pdf_doc: PDFDocument, result: AIAnalysisResult) -> str:
        """Formatuje kontekst dla diagramu klas."""
        analysis_info = f"AI Analysis: {result.model_used}, Confidence: {result.confidence_score:.1f}, {result.processing_time:.1f}s"
        
        return f"""**🤖 AI-ENHANCED ANALIZA DOMENY Z PDF: {pdf_doc.title}**

**PROCES BIZNESOWY:** {context.process_name}

**GŁÓWNE BYTY/ENCJE ({len(context.systems + context.data_flows)}):**
{chr(10).join(f"- {entity}" for entity in (context.systems + context.data_flows)[:15]) if (context.systems + context.data_flows) else "- (nie zidentyfikowano)"}

**ROLE W SYSTEMIE ({len(context.actors)}):**
{chr(10).join(f"- {actor}" for actor in context.actors[:15]) if context.actors else "- (nie zidentyfikowano)"}

**OPERACJE BIZNESOWE ({len(context.activities)}):**
{chr(10).join(f"- {operation}" for operation in context.activities[:25]) if context.activities else "- (nie zidentyfikowano operacji)"}

**REGUŁY BIZNESOWE ({len(context.business_rules)}):**
{chr(10).join(f"- {rule}" for rule in context.business_rules[:15]) if context.business_rules else "- (nie zidentyfikowano)"}

**PUNKTY DECYZYJNE ({len(context.decisions)}):**
{chr(10).join(f"- {decision}" for decision in context.decisions[:10]) if context.decisions else "- (nie zidentyfikowano)"}

**ANALIZA:** {analysis_info}

**INSTRUKCJA:** Wykorzystaj powyższy kontekst wzbogacony analizą AI do stworzenia komprehensywnego diagramu klas odzwierciedlającego rzeczywistą architekturę i logikę biznesową."""
    
    def _format_activity_context(self, context: ProcessContext, pdf_doc: PDFDocument, result: AIAnalysisResult) -> str:
        """Formatuje kontekst dla diagramu aktywności."""
        analysis_info = f"AI Analysis: {result.model_used}, Confidence: {result.confidence_score:.1f}, {result.processing_time:.1f}s"
        
        return f"""**🤖 AI-ENHANCED KONTEKST PROCESU Z PDF: {pdf_doc.title}**

**NAZWA PROCESU:** {context.process_name}

**ROLE I AKTORZY ({len(context.actors)}):**
{chr(10).join(f"- {actor}" for actor in context.actors[:15]) if context.actors else "- (nie zidentyfikowano)"}

**SEKWENCJA DZIAŁAŃ ({len(context.activities)}):**
{chr(10).join(f"{i+1}. {activity}" for i, activity in enumerate(context.activities[:30])) if context.activities else "- (nie zidentyfikowano działań)"}

**DECYZJE I WARUNKI ({len(context.decisions)}):**
{chr(10).join(f"- {decision}" for decision in context.decisions[:15]) if context.decisions else "- (nie zidentyfikowano)"}

**REGUŁY BIZNESOWE ({len(context.business_rules)}):**
{chr(10).join(f"- {rule}" for rule in context.business_rules[:15]) if context.business_rules else "- (nie zidentyfikowano)"}

**SYSTEMY ZAANGAŻOWANE ({len(context.systems)}):**
{chr(10).join(f"- {system}" for system in context.systems[:15]) if context.systems else "- (nie zidentyfikowano)"}

**ANALIZA:** {analysis_info}

**INSTRUKCJA:** Wykorzystaj wzbogacony kontekst AI do stworzenia szczegółowego diagramu aktywności pokazującego rzeczywisty przepływ procesu z wszystkimi rolami, decyzjami i działaniami."""

    def _format_sequence_context(self, context: ProcessContext, pdf_doc: PDFDocument, result: AIAnalysisResult) -> str:
        """Formatuje kontekst dla diagramu sekwencji."""
        analysis_info = f"AI Analysis: {result.model_used}, Confidence: {result.confidence_score:.1f}, {result.processing_time:.1f}s"
        
        return f"""**🤖 AI-ENHANCED KONTEKST SEKWENCJI Z PDF: {pdf_doc.title}**

**PROCES:** {context.process_name}

**UCZESTNICY PROCESU ({len(context.actors)}):**
{chr(10).join(f"- {actor}" for actor in context.actors[:15])}

**INTERAKCJE I KOMUNIKACJA ({len(context.activities)}):**
{chr(10).join(f"- {activity}" for activity in context.activities[:20])}

**SYSTEMY I KOMPONENTY ({len(context.systems)}):**
{chr(10).join(f"- {system}" for system in context.systems[:15])}

**ANALIZA:** {analysis_info}

**INSTRUKCJA:** Wykorzystaj kontekst AI do wygenerowania diagramu sekwencji pokazującego chronologiczną wymianę wiadomości między uczestnikami."""

    def _format_general_context(self, context: ProcessContext, pdf_doc: PDFDocument, result: AIAnalysisResult) -> str:
        """Formatuje ogólny kontekst."""
        analysis_info = f"AI Analysis: {result.model_used}, Confidence: {result.confidence_score:.1f}, {result.processing_time:.1f}s"
        
        return f"""**🤖 AI-ENHANCED KONTEKST Z PDF: {pdf_doc.title}**

**PROCES:** {context.process_name}
**ANALIZA:** {analysis_info}

{result.analysis_summary}

**AKTORZY:** {', '.join(context.actors[:10])}
**SYSTEMY:** {', '.join(context.systems[:10])}
**DZIAŁANIA:** {len(context.activities)} zidentyfikowanych operacji

**INSTRUKCJA:** Wykorzystaj powyższy kontekst wzbogacony AI do wygenerowania precyzyjnego diagramu."""