# API Reference - System GD

## 📖 Przegląd API

System GD oferuje kompletny zestaw API do generowania diagramów UML, BPMN, analizy dokumentów PDF oraz zarządzania konfiguracją. API jest zorganizowane w moduły funkcjonalne z jasno zdefiniowanymi interfejsami.

## 🏗️ Architektura API

### Główne moduły
- **AI Configuration API** - Konfiguracja providerów AI
- **BPMN Generation API** - Generowanie diagramów BPMN v2
- **PlantUML API** - Generowanie diagramów UML
- **PDF Analysis API** - Analiza dokumentów PDF
- **Desktop Application API** - Interfejsy aplikacji PyQt5
- **Web Application API** - Interfejsy aplikacji Streamlit

---

## 🔧 AI Configuration API

### Moduł: `bpmn_v2.ai_config`

#### `create_bpmn_config(selected_model: str = None)`
**Opis**: Tworzy konfigurację AI providera dla BPMN v2.

```python
def create_bpmn_config(selected_model: str = None) -> AIConfig:
    """
    Tworzy konfigurację AI providera na podstawie zmiennych środowiskowych.
    
    Args:
        selected_model: Opcjonalny model override z GUI
        
    Returns:
        AIConfig: Skonfigurowany obiekt AI providera
        
    Raises:
        ConfigurationError: Gdy wymagane zmienne środowiskowe są niedostępne
        ValueError: Gdy wartości konfiguracyjne są nieprawidłowe
        
    Environment Variables:
        - MODEL_PROVIDER: openai|gemini|claude|ollama|local
        - GOOGLE_API_KEY / API_KEY: Klucz Gemini API
        - OPENAI_API_KEY: Klucz OpenAI API  
        - CLAUDE_API_KEY: Klucz Anthropic Claude API
        - OLLAMA_BASE_URL: URL serwera Ollama
        - API_DEFAULT_MODEL: Domyślny model
        - CHAT_URL: URL endpoint czatu
    """

# Przykład użycia
from bpmn_v2.ai_config import create_bpmn_config

config = create_bpmn_config()
print(f"Provider: {config.provider}")
print(f"Model: {config.model}")
print(f"API URL: {config.chat_url}")
```

#### `get_default_config()`
**Opis**: Pobiera domyślną konfigurację AI.

```python
def get_default_config() -> AIConfig:
    """
    Tworzy domyślną konfigurację AI na podstawie zmiennych środowiskowych.
    
    Returns:
        AIConfig: Domyślna konfiguracja z ustawieniami produkcyjnymi
    """
```

### Klasa: `AIProvider`
**Enum providerów AI obsługiwanych przez system.**

```python
from enum import Enum

class AIProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini" 
    CLAUDE = "claude"
    OLLAMA = "ollama"
    MOCK = "mock"  # Do testowania
```

### Klasa: `AIConfig`
**Konfiguracja providera AI.**

```python
@dataclass
class AIConfig:
    provider: AIProvider
    model: str
    api_key: str
    chat_url: str
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    timeout: int = 60
    max_retries: int = 3
```

---

## 🎯 BPMN Generation API

### Moduł: `src.bpmn_integration`

#### Klasa: `BPMNIntegration`
**Główny interfejs do generowania diagramów BPMN.**

```python
class BPMNIntegration:
    def generate_bpmn_process(
        self,
        user_input: str,
        process_type: str = "business",
        quality_target: float = 0.8,
        max_iterations: int = 10
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generuje proces BPMN z automatyczną optymalizacją jakości.
        
        Args:
            user_input: Opis procesu biznesowego
            process_type: Typ procesu (business|technical|workflow)
            quality_target: Docelowa jakość (0.0-1.0)
            max_iterations: Maksymalna liczba iteracji
            
        Returns:
            Tuple[bool, str, Dict]: (success, bpmn_xml, metadata)
            
        Metadata zawiera:
            - iterations: Liczba wykonanych iteracji
            - final_score: Osiągnięty wynik jakości
            - processing_time: Czas przetwarzania
            - improvement_history: Historia optymalizacji
        """
```

#### `create_bpmn_integration()`
**Funkcja factory do tworzenia instancji BPMNIntegration.**

```python
def create_bpmn_integration(
    api_key: str,
    model_provider: str,
    chat_url: str,
    default_model: str
) -> Optional[BPMNIntegration]:
    """
    Tworzy instancję BPMNIntegration z podaną konfiguracją.
    
    Args:
        api_key: Klucz API providera
        model_provider: Nazwa providera (openai|gemini|claude|ollama)
        chat_url: URL endpointa czatu
        default_model: Domyślny model
        
    Returns:
        BPMNIntegration lub None przy błędzie konfiguracji
    """
```

### Moduł: `bpmn_v2.complete_pipeline`

#### Klasa: `BPMNv2Pipeline`
**Pipeline BPMN v2 z pełną integracją komponentów.**

```python
class BPMNv2Pipeline:
    def __init__(self, ai_config: Optional[AIConfig] = None):
        """
        Inicjalizuje pipeline BPMN v2.
        
        Args:
            ai_config: Opcjonalna konfiguracja AI
        """
        
    def generate_complete_bpmn(
        self, 
        polish_description: str,
        context_type: ContextType = ContextType.GENERAL
    ) -> Dict[str, Any]:
        """
        Kompletny pipeline: Polski tekst → AI → JSON → BPMN XML.
        
        Args:
            polish_description: Opis procesu po polsku
            context_type: Typ kontekstu (GENERAL|BANKING|INSURANCE|HEALTHCARE)
            
        Returns:
            Dict z wynikami pipeline:
                - success: bool
                - bpmn_xml: str
                - quality_score: float
                - processing_metadata: dict
        """
```

---

## 📊 PlantUML API

### Moduł: `src.main` / `utils.plantuml`

#### Funkcje generowania PlantUML

```python
def generate_plantuml(
    prompt: str,
    diagram_type: str,
    template: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Generuje kod PlantUML dla różnych typów diagramów.
    
    Args:
        prompt: Opis diagramu
        diagram_type: sequence|activity|class|component|usecase|state
        template: Opcjonalny szablon promptu
        
    Returns:
        Tuple[bool, str]: (success, plantuml_code)
    """

def validate_plantuml(plantuml_code: str) -> Tuple[bool, str]:
    """
    Waliduje kod PlantUML poprzez próbę generowania SVG.
    
    Args:
        plantuml_code: Kod PlantUML do walidacji
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message_or_svg)
    """

def render_plantuml_svg(plantuml_code: str) -> Optional[str]:
    """
    Renderuje kod PlantUML do formatu SVG.
    
    Args:
        plantuml_code: Kod PlantUML
        
    Returns:
        str: SVG content lub None przy błędzie
    """
```

---

## 📄 PDF Analysis API

### Moduł: `utils.pdf.ai_pdf_analyzer`

#### Klasa: `AIPDFAnalyzer`
**Analiza dokumentów PDF z wykorzystaniem AI.**

```python
class AIPDFAnalyzer:
    def __init__(self):
        """
        Inicjalizuje analyzer PDF z konfiguracją z .env.
        
        Environment Variables:
            - PDF_ANALYSIS_MODE: ai|local
            - PDF_ANALYSIS_MODEL: Model do analizy PDF
            - PDF_ANALYSIS_PROMPT_LANG: pl|en
        """
        
    def analyze_pdf(
        self, 
        pdf_path: str, 
        diagram_type: str,
        max_pages: int = 50
    ) -> Dict[str, Any]:
        """
        Analizuje dokument PDF i wyciąga kontekst biznesowy.
        
        Args:
            pdf_path: Ścieżka do pliku PDF
            diagram_type: Typ diagramu (activity|sequence|class|component)
            max_pages: Maksymalna liczba stron do przetworzenia
            
        Returns:
            Dict z wynikami analizy:
                - success: bool
                - business_context: str
                - key_entities: List[str]
                - process_steps: List[str]
                - error: Optional[str]
        """
```

### Moduł: `utils.pdf.pdf_extractor`

#### Funkcje ekstrakcji tekstu

```python
def extract_text_from_pdf(
    pdf_path: str, 
    max_pages: int = None
) -> Tuple[bool, str]:
    """
    Wyciąga tekst z dokumentu PDF.
    
    Args:
        pdf_path: Ścieżka do pliku PDF
        max_pages: Maksymalna liczba stron
        
    Returns:
        Tuple[bool, str]: (success, extracted_text)
    """

def chunk_text(text: str, chunk_size: int = 4000) -> List[str]:
    """
    Dzieli tekst na mniejsze fragmenty.
    
    Args:
        text: Tekst do podziału
        chunk_size: Rozmiar fragmentu
        
    Returns:
        List[str]: Lista fragmentów tekstu
    """
```

---

## 🖥️ Desktop Application API

### Moduł: `src.main`

#### Klasa: `AIApp` (QMainWindow)
**Główna aplikacja desktopowa PyQt5.**

```python
class AIApp(QMainWindow):
    def __init__(self):
        """
        Inicjalizuje główne okno aplikacji desktop.
        """
        
    def send_to_api(self) -> None:
        """
        Wysyła zapytanie do API bez blokowania GUI.
        Obsługuje PlantUML i BPMN generation.
        """
        
    def handle_bpmn_generation(self, process_description: str) -> None:
        """
        Obsługuje generowanie BPMN v2 z GUI.
        
        Args:
            process_description: Opis procesu z GUI
        """
        
    def enhance_prompt_with_pdf_context(
        self, 
        prompt: str, 
        diagram_type: str
    ) -> str:
        """
        Wzbogaca prompt o kontekst z analizy PDF.
        
        Args:
            prompt: Oryginalny prompt
            diagram_type: Typ diagramu
            
        Returns:
            str: Wzbogacony prompt
        """
```

---

## 🌐 Web Application API

### Moduł: `src.streamlit_app`

#### Główne funkcje Streamlit

```python
def render_bpmn_interface() -> None:
    """
    Renderuje interfejs BPMN v2 w aplikacji Streamlit.
    Obsługuje parametry jakości, progress tracking, wyniki.
    """

def handle_plantuml_generation(
    prompt: str, 
    diagram_type: str,
    template: str
) -> Tuple[bool, str]:
    """
    Obsługuje generowanie PlantUML w interfejsie web.
    
    Args:
        prompt: Opis diagramu
        diagram_type: Typ diagramu 
        template: Szablon promptu
        
    Returns:
        Tuple[bool, str]: (success, result)
    """
    
def display_svg_diagram(svg_content: str) -> None:
    """
    Wyświetla diagram SVG w interfejsie Streamlit.
    
    Args:
        svg_content: Zawartość SVG do wyświetlenia
    """
```

---

## 🔍 Validation & Quality APIs

### Moduł: `bpmn_v2.bpmn_compliance_validator`

#### Klasa: `BPMNComplianceValidator`
**Walidacja zgodności BPMN z standardami.**

```python
class BPMNComplianceValidator:
    def validate_bpmn_xml(self, bpmn_xml: str) -> ValidationResult:
        """
        Waliduje XML BPMN pod kątem zgodności ze standardem.
        
        Args:
            bpmn_xml: Kod XML BPMN
            
        Returns:
            ValidationResult: Wyniki walidacji
        """
        
    def calculate_quality_score(self, bpmn_xml: str) -> float:
        """
        Oblicza wynik jakości diagramu BPMN.
        
        Args:
            bpmn_xml: Kod XML BPMN
            
        Returns:
            float: Wynik jakości (0.0-1.0)
        """
```

---

## ⚡ Utilities APIs

### Moduł: `utils.logger_utils`

```python
def log_info(message: str, component: str = "System") -> None:
def log_error(message: str, error: Exception = None) -> None:
def log_warning(message: str) -> None:
```

### Moduł: `utils.extract_code_from_response`

```python
def extract_plantuml_code(response: str) -> Optional[str]:
def extract_bpmn_xml(response: str) -> Optional[str]:
```

---

## 🎭 Mock APIs (Testing)

### Moduł: `bpmn_v2.ai_integration`

#### Klasa: `MockAIClient`
**Mock client do testowania bez prawdziwych API calls.**

```python
class MockAIClient:
    def send_request(self, prompt: str) -> AIResponse:
        """
        Symuluje odpowiedź AI dla celów testowych.
        
        Args:
            prompt: Prompt testowy
            
        Returns:
            AIResponse: Symulowana odpowiedź
        """
```

---

## 📋 Error Handling

### Hierarchia wyjątków

```python
class GDPythonError(Exception):
    """Bazowy wyjątek systemu GD."""

class AIConfigurationError(GDPythonError):
    """Błąd konfiguracji AI providera."""

class BPMNGenerationError(GDPythonError):
    """Błąd generowania BPMN."""

class QualityThresholdError(GDPythonError):
    """Nie udało się osiągnąć wymaganej jakości."""

class PDFAnalysisError(GDPythonError):
    """Błąd analizy PDF."""
```

---

## 📊 Response Formats

### BPMN Generation Response

```json
{
    "success": true,
    "bpmn_xml": "<definitions>...</definitions>",
    "metadata": {
        "iterations": 5,
        "final_score": 0.85,
        "processing_time": 45.2,
        "improvement_history": [
            {"iteration": 1, "score": 0.65},
            {"iteration": 2, "score": 0.72},
            {"iteration": 3, "score": 0.78},
            {"iteration": 4, "score": 0.82},
            {"iteration": 5, "score": 0.85}
        ],
        "quality_details": {
            "structure_score": 0.9,
            "naming_score": 0.8,
            "flow_score": 0.85,
            "completeness_score": 0.8
        }
    }
}
```

### PDF Analysis Response

```json
{
    "success": true,
    "business_context": "Proces obsługi kredytu hipotecznego...",
    "key_entities": ["Klient", "Bank", "Kredyt", "Nieruchomość"],
    "process_steps": [
        "Złożenie wniosku",
        "Weryfikacja dokumentów", 
        "Ocena zdolności kredytowej",
        "Decyzja kredytowa"
    ],
    "metadata": {
        "pages_processed": 25,
        "analysis_time": 12.3,
        "confidence_score": 0.92
    }
}
```

---

## 🔗 Integration Examples

### Kompletny przykład BPMN Generation

```python
from src.bpmn_integration import create_bpmn_integration
from bpmn_v2.ai_config import create_bpmn_config

# Konfiguracja
integration = create_bpmn_integration(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model_provider="gemini",
    chat_url="https://generativelanguage.googleapis.com/v1beta/models",
    default_model="gemini-2.0-flash"
)

# Generowanie BPMN
success, bpmn_xml, metadata = integration.generate_bpmn_process(
    user_input="Proces obsługi reklamacji w e-commerce",
    quality_target=0.8,
    max_iterations=10
)

if success:
    print(f"BPMN wygenerowany, jakość: {metadata['final_score']}")
    print(f"Iteracji: {metadata['iterations']}")
    
    # Zapis do pliku
    with open("process.bpmn", "w", encoding="utf-8") as f:
        f.write(bpmn_xml)
else:
    print(f"Błąd: {bpmn_xml}")
```

### Kompletny przykład z analizą PDF

```python
from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer

# Analiza PDF
analyzer = AIPDFAnalyzer()
result = analyzer.analyze_pdf(
    pdf_path="documents/process_spec.pdf",
    diagram_type="activity"
)

if result["success"]:
    # Użycie kontekstu w generowaniu
    enhanced_prompt = f"""
    {original_prompt}
    
    Kontekst biznesowy z dokumentacji:
    {result["business_context"]}
    
    Kluczowe elementy: {', '.join(result["key_entities"])}
    """
    
    # Generowanie z wzbogaconym promptem
    success, bpmn_xml, metadata = integration.generate_bpmn_process(
        user_input=enhanced_prompt
    )
```
            ConfigurationError: Nieprawidłowa konfiguracja AI
            
        Example:
            integration = BPMNIntegration()
            result = integration.generate_bpmn(
                prompt="Proces obsługi zamówienia klienta",
                quality_threshold=0.85,
                max_iterations=15,
                process_type="business"
            )
            
            if result['quality_score'] >= 0.85:
                print("BPMN wygenerowany pomyślnie!")
                print(f"Jakość: {result['quality_score']:.2f}")
        """
```

#### `BMPNIntegration.validate_bpmn()`
**Opis**: Waliduje istniejący diagram BPMN.
**Moduł**: `src.bpmn_integration`

```python
def validate_bpmn(self, bpmn_xml: str) -> Dict[str, Any]:
    """
    Waliduje diagram BPMN pod kątem poprawności syntaktycznej i semantycznej.
    
    Args:
        bpmn_xml: Kod BPMN XML do walidacji
        
    Returns:
        Dict zawierający:
            - is_valid: Boolean - czy diagram jest poprawny
            - quality_score: Wynik jakości (0.0-1.0)
            - errors: Lista błędów krytycznych
            - warnings: Lista ostrzeżeń
            - suggestions: Lista sugestii poprawy
            - validation_details: Szczegóły walidacji
            
    Example:
        validation = integration.validate_bpmn(bpmn_xml)
        if validation['is_valid']:
            print(f"BPMN jest poprawny. Jakość: {validation['quality_score']}")
        else:
            print("Błędy:", validation['errors'])
    """
```

#### `BMPNIntegration.improve_bpmn()`
**Opis**: Poprawia istniejący diagram BPMN.
**Moduł**: `src.bpmn_integration`

```python
def improve_bpmn(
    self,
    bpmn_xml: str,
    target_quality: float = 0.8,
    focus_areas: List[str] = None
) -> Dict[str, Any]:
    """
    Poprawia istniejący diagram BPMN.
    
    Args:
        bpmn_xml: Obecny kod BPMN XML
        target_quality: Docelowa jakość (0.0-1.0)
        focus_areas: Obszary do poprawy ['structure', 'naming', 'flow', 'compliance']
        
    Returns:
        Dict zawierający poprawiony BPMN i metryki poprawy
        
    Example:
        improved = integration.improve_bpmn(
            bpmn_xml=current_bpmn,
            target_quality=0.9,
            focus_areas=['naming', 'structure']
        )
    """
```

### PlantUML Generation API

#### `PlantUMLGenerator.generate_diagram()`
**Opis**: Generuje diagramy PlantUML z różnych typów.
**Moduł**: `utils.plantuml`

```python
class PlantUMLGenerator:
    def generate_diagram(
        self,
        description: str,
        diagram_type: str,
        template_name: str = None,
        output_format: str = "puml"
    ) -> Dict[str, Any]:
        """
        Generuje diagram PlantUML na podstawie opisu.
        
        Args:
            description: Opis procesu/systemu
            diagram_type: Typ diagramu (activity, sequence, class, component)
            template_name: Nazwa szablonu do użycia
            output_format: Format wyjściowy (puml, svg, png)
            
        Returns:
            Dict z wygenerowanym diagramem i metadanymi
            
        Supported Diagram Types:
            - activity: Diagramy aktywności/procesów
            - sequence: Diagramy sekwencji
            - class: Diagramy klas
            - component: Diagramy komponentów
            - use_case: Diagramy przypadków użycia
            - state: Diagramy stanów
            - deployment: Diagramy wdrożeń
            
        Example:
            generator = PlantUMLGenerator()
            result = generator.generate_diagram(
                description="System logowania użytkownika",
                diagram_type="sequence",
                output_format="svg"
            )
        """
```

### PDF Processing API

#### `PDFProcessor.extract_text()`
**Opis**: Ekstraktuje tekst z plików PDF.
**Moduł**: `utils.pdf_processor`

```python
class PDFProcessor:
    def extract_text(
        self,
        file_path: str,
        max_pages: int = 50,
        extract_tables: bool = False
    ) -> Dict[str, Any]:
        """
        Ekstraktuje tekst z pliku PDF.
        
        Args:
            file_path: Ścieżka do pliku PDF
            max_pages: Maksymalna liczba stron do przetworzenia
            extract_tables: Czy ekstraktować tabele
            
        Returns:
            Dict zawierający:
                - text: Wyekstraktowany tekst
                - pages_processed: Liczba przetworzonych stron
                - tables: Lista tabel (jeśli extract_tables=True)
                - metadata: Metadane pliku
                - processing_time: Czas przetwarzania
                
        Raises:
            PDFProcessingError: Błąd podczas przetwarzania PDF
            FileNotFoundError: Plik nie istnieje
            PermissionError: Brak uprawnień do pliku
            
        Example:
            processor = PDFProcessor()
            result = processor.extract_text(
                file_path="document.pdf",
                max_pages=20,
                extract_tables=True
            )
            
            print(f"Extracted {len(result['text'])} characters")
            if result['tables']:
                print(f"Found {len(result['tables'])} tables")
        """
```

#### `PDFProcessor.analyze_content()`
**Opis**: Analizuje zawartość PDF za pomocą AI.
**Moduł**: `utils.pdf_processor`

```python
def analyze_content(
    self,
    pdf_text: str,
    analysis_type: str = "process",
    ai_config: AIConfig = None
) -> Dict[str, Any]:
    """
    Analizuje zawartość PDF za pomocą AI.
    
    Args:
        pdf_text: Tekst wyekstraktowany z PDF
        analysis_type: Typ analizy (process, structure, requirements, data)
        ai_config: Konfiguracja AI providera
        
    Returns:
        Dict z wynikami analizy
        
    Analysis Types:
        - process: Identyfikuje procesy biznesowe
        - structure: Analizuje strukturę dokumentu
        - requirements: Wyodrębnia wymagania
        - data: Identyfikuje modele danych
        
    Example:
        analysis = processor.analyze_content(
            pdf_text=extracted_text,
            analysis_type="process"
        )
        
        processes = analysis['identified_processes']
        for process in processes:
            print(f"Found process: {process['name']}")
    """
```

### Template Management API

#### `TemplateManager.load_template()`
**Opis**: Ładuje szablon promptu.
**Moduł**: `prompts.template_manager`

```python
class TemplateManager:
    def load_template(
        self,
        template_name: str,
        language: str = "pl",
        diagram_type: str = None
    ) -> TemplateDefinition:
        """
        Ładuje szablon promptu.
        
        Args:
            template_name: Nazwa szablonu
            language: Język szablonu (pl, en)
            diagram_type: Typ diagramu (opcjonalne filtrowanie)
            
        Returns:
            TemplateDefinition: Załadowany szablon
            
        Raises:
            TemplateNotFoundError: Szablon nie istnieje
            LanguageNotSupportedError: Język nie jest obsługiwany
            
        Example:
            manager = TemplateManager()
            template = manager.load_template(
                template_name="business_process",
                language="pl"
            )
            
            formatted = template.format(
                process_name="Obsługa zamówienia",
                stakeholders="Klient, Sprzedawca, Magazyn"
            )
        """
```

#### `TemplateManager.list_templates()`
**Opis**: Listuje dostępne szablony.
**Moduł**: `prompts.template_manager`

```python
def list_templates(
    self,
    language: str = None,
    diagram_type: str = None,
    complexity: str = None
) -> List[TemplateDefinition]:
    """
    Listuje dostępne szablony z opcjonalnym filtrowaniem.
    
    Args:
        language: Filtruj po języku
        diagram_type: Filtruj po typie diagramu
        complexity: Filtruj po poziomie złożoności
        
    Returns:
        List[TemplateDefinition]: Lista pasujących szablonów
        
    Example:
        templates = manager.list_templates(
            language="pl",
            diagram_type="activity",
            complexity="basic"
        )
        
        for template in templates:
            print(f"{template.name}: {template.description}")
    """
```

### Metrics & Analytics API

#### `MetricsCollector.record_operation()`
**Opis**: Rejestruje metryki operacji.
**Moduł**: `utils.metrics`

```python
class MetricsCollector:
    def record_operation(
        self,
        operation_type: str,
        duration: float,
        success: bool,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Rejestruje metryki wykonanej operacji.
        
        Args:
            operation_type: Typ operacji (generate_bpmn, generate_plantuml, pdf_extract)
            duration: Czas trwania w sekundach
            success: Czy operacja zakończyła się sukcesem
            metadata: Dodatkowe metadane operacji
            
        Example:
            collector = MetricsCollector()
            collector.record_operation(
                operation_type="generate_bpmn",
                duration=15.7,
                success=True,
                metadata={
                    "quality_score": 0.87,
                    "iterations": 3,
                    "model": "gemini-pro"
                }
            )
        """
```

#### `MetricsCollector.get_performance_stats()`
**Opis**: Pobiera statystyki wydajności.
**Moduł**: `utils.metrics`

```python
def get_performance_stats(
    self,
    time_range: str = "24h",
    operation_type: str = None
) -> Dict[str, Any]:
    """
    Pobiera statystyki wydajności dla określonego okresu.
    
    Args:
        time_range: Zakres czasu (1h, 24h, 7d, 30d)
        operation_type: Filtruj po typie operacji
        
    Returns:
        Dict ze statystykami wydajności
        
    Example:
        stats = collector.get_performance_stats(
            time_range="24h",
            operation_type="generate_bpmn"
        )
        
        print(f"Average response time: {stats['avg_duration']}s")
        print(f"Success rate: {stats['success_rate']}%")
        print(f"Total operations: {stats['total_operations']}")
    """
```

## 🌐 Streamlit Web API

### Session Management

#### `get_session_state()`
**Opis**: Pobiera stan sesji Streamlit.
**Moduł**: `streamlit_app`

```python
def get_session_state() -> SessionState:
    """
    Pobiera lub tworzy stan sesji Streamlit.
    
    Returns:
        SessionState: Obiekt stanu sesji
        
    Properties:
        - session_id: Unikalny identyfikator sesji
        - user_input: Dane wejściowe użytkownika
        - processing_history: Historia przetwarzania
        - current_config: Aktualna konfiguracja
        
    Example:
        state = get_session_state()
        state.user_input = "Nowy proces biznesowy"
        state.selected_provider = "gemini"
    """
```

### UI Components API

#### `render_config_sidebar()`
**Opis**: Renderuje sidebar z konfiguracją.
**Moduł**: `streamlit_app`

```python
def render_config_sidebar() -> Dict[str, Any]:
    """
    Renderuje sidebar z opcjami konfiguracji.
    
    Returns:
        Dict z wybranymi opcjami konfiguracji
        
    Configuration Options:
        - ai_provider: Wybór providera AI
        - model_name: Wybór modelu
        - language: Język interfejsu
        - diagram_type: Typ diagramu
        - quality_settings: Ustawienia jakości
        
    Example:
        config = render_config_sidebar()
        if config['ai_provider'] != st.session_state.provider:
            st.rerun()
    """
```

#### `display_result()`
**Opis**: Wyświetla wyniki generowania.
**Moduł**: `streamlit_app`

```python
def display_result(
    result: Dict[str, Any],
    show_metrics: bool = True,
    allow_download: bool = True
) -> None:
    """
    Wyświetla wyniki generowania diagramu.
    
    Args:
        result: Wynik generowania
        show_metrics: Czy pokazać metryki
        allow_download: Czy umożliwić pobieranie
        
    Features:
        - Podgląd diagramu (SVG/PNG)
        - Wyświetlanie kodu źródłowego
        - Metryki jakości i wydajności
        - Opcje pobierania w różnych formatach
        - Historia iteracji (dla BPMN)
        
    Example:
        result = bpmn_integration.generate_bpmn(user_input)
        display_result(
            result=result,
            show_metrics=True,
            allow_download=True
        )
    """
```

## 🖥️ Desktop PyQt5 API

### Main Application

#### `MainApplication.handle_bpmn_generation()`
**Opis**: Obsługuje generowanie BPMN w aplikacji desktop.
**Moduł**: `main`

```python
class MainApplication(QMainWindow):
    def handle_bpmn_generation(self) -> None:
        """
        Obsługuje proces generowania diagramu BPMN w aplikacji desktop.
        
        Features:
            - Walidacja danych wejściowych
            - Wyświetlanie progress bara
            - Obsługa błędów z user-friendly komunikatami
            - Automatyczne zapisywanie wyników
            - Integracja z systemem powiadomień
            
        UI Elements:
            - Progress bar z informacją o kroku
            - Cancel button dla długotrwałych operacji
            - Status bar z informacjami o błędach
            - Results panel z podglądem
            
        Example Usage:
            app = MainApplication()
            app.input_text.setPlainText("Proces obsługi klienta")
            app.handle_bmpn_generation()  # Called by button click
        """
```

### File Operations

#### `export_diagram()`
**Opis**: Eksportuje diagram do pliku.
**Moduł**: `main`

```python
def export_diagram(
    self,
    content: str,
    content_type: str,
    filename: str = None
) -> str:
    """
    Eksportuje diagram do pliku z wyborem lokalizacji.
    
    Args:
        content: Zawartość do eksportu
        content_type: Typ zawartości (plantuml, bpmn, svg)
        filename: Sugerowana nazwa pliku
        
    Returns:
        str: Ścieżka do zapisanego pliku
        
    Supported Formats:
        - .puml: PlantUML source code
        - .bpmn: BPMN XML
        - .svg: Scalable Vector Graphics  
        - .png: Portable Network Graphics
        - .xmi: XML Metadata Interchange
        
    Example:
        file_path = app.export_diagram(
            content=bpmn_xml,
            content_type="bpmn",
            filename="process_diagram"
        )
        
        if file_path:
            print(f"Diagram saved to: {file_path}")
    """
```

## 🔌 Integration APIs

### External Tool Integration

#### `plantuml_render()`
**Opis**: Renderuje PlantUML do różnych formatów.
**Moduł**: `utils.plantuml_renderer`

```python
def plantuml_render(
    plantuml_code: str,
    output_format: str = "svg",
    renderer: str = "local"
) -> bytes:
    """
    Renderuje kod PlantUML do określonego formatu.
    
    Args:
        plantuml_code: Kod PlantUML do renderowania
        output_format: Format wyjściowy (svg, png, pdf)
        renderer: Renderer do użycia (local, www)
        
    Returns:
        bytes: Wyrenderowany diagram
        
    Renderers:
        - local: Używa lokalnego PlantUML JAR
        - www: Używa serwisu online PlantUML
        
    Raises:
        RenderingError: Błąd podczas renderowania
        PlantUMLSyntaxError: Błąd składni PlantUML
        
    Example:
        svg_data = plantuml_render(
            plantuml_code=puml_content,
            output_format="svg",
            renderer="local"
        )
        
        with open("diagram.svg", "wb") as f:
            f.write(svg_data)
    """
```

### Database Integration

#### `MetricsDatabase.store_metrics()`
**Opis**: Zapisuje metryki do bazy danych.
**Moduł**: `utils.db.metrics_db`

```python
class MetricsDatabase:
    def store_metrics(
        self,
        metrics: PerformanceMetric
    ) -> bool:
        """
        Zapisuje metryki wydajności do bazy danych.
        
        Args:
            metrics: Obiekt z metrykami do zapisania
            
        Returns:
            bool: True jeśli sukces, False w przeciwnym razie
            
        Example:
            db = MetricsDatabase()
            metric = PerformanceMetric(
                operation_type="generate_bpmn",
                total_time=12.5,
                success=True,
                quality_score=0.85
            )
            
            success = db.store_metrics(metric)
            if success:
                print("Metrics stored successfully")
        """
```

## 🔒 Authentication & Security

### API Key Management

#### `validate_api_key()`
**Opis**: Waliduje klucz API providera.
**Moduł**: `security.api_validation`

```python
def validate_api_key(
    provider: str,
    api_key: str
) -> Tuple[bool, str]:
    """
    Waliduje klucz API dla określonego providera.
    
    Args:
        provider: Nazwa providera (openai, gemini, claude)
        api_key: Klucz API do walidacji
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
        
    Example:
        is_valid, error = validate_api_key("openai", "sk-...")
        if not is_valid:
            print(f"Invalid API key: {error}")
    """
```

## 📊 Error Handling

### Custom Exceptions

```python
class GDPythonError(Exception):
    """Base exception dla systemu GD"""
    pass

class ConfigurationError(GDPythonError):
    """Błąd konfiguracji systemu"""
    pass

class BPMNGenerationError(GDPythonError):
    """Błąd podczas generowania BPMN"""
    pass

class QualityThresholdError(GDPythonError):
    """Nie udało się osiągnąć wymaganej jakości"""
    pass

class PDFProcessingError(GDPythonError):
    """Błąd podczas przetwarzania PDF"""
    pass

class TemplateNotFoundError(GDPythonError):
    """Szablon nie został znaleziony"""
    pass

class RenderingError(GDPythonError):
    """Błąd podczas renderowania diagramu"""
    pass
```

### Error Response Format

```python
# Standardowy format odpowiedzi z błędem
{
    "success": False,
    "error": {
        "type": "ConfigurationError",
        "message": "Missing required environment variable: GEMINI_API_KEY",
        "code": "MISSING_API_KEY",
        "details": {
            "missing_variable": "GEMINI_API_KEY",
            "provider": "gemini",
            "suggestion": "Set GEMINI_API_KEY in your .env file"
        }
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
}
```

---

*API Reference jest regularnie aktualizowana wraz z rozwojem systemu. Sprawdzaj najnowszą wersję dokumentacji.*