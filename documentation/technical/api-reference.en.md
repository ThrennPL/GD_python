# API Reference - GD System

## 📖 API Overview

The GD system provides a comprehensive set of APIs for generating UML diagrams, BPMN, PDF document analysis, and configuration management. The APIs are organized into functional modules with clearly defined interfaces.

## 🏗️ API Architecture

### Main Modules

- **AI Configuration API** - AI provider configuration
- **BPMN Generation API** - BPMN v2 diagram generation
- **PlantUML API** - UML diagram generation
- **PDF Analysis API** - PDF document analysis
- **Desktop Application API** - PyQt5 application interfaces
- **Web Application API** - Streamlit application interfaces

---

## 🔧 AI Configuration API

### Module: `bpmn_v2.ai_config`

#### `create_bpmn_config(selected_model: str = None)`

**Description**: Creates AI provider configuration for BPMN v2.

```python
def create_bpmn_config(selected_model: str = None) -> AIConfig:
    """
    Creates AI provider configuration based on environment variables.
    
    Args:
        selected_model: Optional model override from GUI
        
    Returns:
        AIConfig: Configured AI provider object
        
    Raises:
        ConfigurationError: When required environment variables are unavailable
        ValueError: When configuration values are invalid
        
    Environment Variables:
        - MODEL_PROVIDER: openai|gemini|claude|ollama|local
        - GOOGLE_API_KEY / API_KEY: Gemini API key
        - OPENAI_API_KEY: OpenAI API key  
        - CLAUDE_API_KEY: Anthropic Claude API key
        - OLLAMA_BASE_URL: Ollama server URL
        - API_DEFAULT_MODEL: Default model
        - CHAT_URL: Chat endpoint URL
    """

# Usage Example
from bpmn_v2.ai_config import create_bpmn_config

config = create_bpmn_config()
print(f"Provider: {config.provider}")
print(f"Model: {config.model}")
print(f"API URL: {config.chat_url}")
```

#### `get_default_config()`

**Description**: Retrieves default AI configuration.

```python
def get_default_config() -> AIConfig:
    """
    Creates default AI configuration based on environment variables.
    
    Returns:
        AIConfig: Default configuration with production settings
    """
```

### Class: `AIProvider`

**Enum of AI providers supported by the system.**

```python
from enum import Enum

class AIProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini" 
    CLAUDE = "claude"
    OLLAMA = "ollama"
    MOCK = "mock"  # For testing
```

### Class: `AIConfig`

**AI provider configuration.**

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

### Module: `src.bpmn_integration`

#### Class: `BPMNIntegration`

**Main interface for BPMN diagram generation.**

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
        Generates BPMN process with automatic quality optimization.
        
        Args:
            user_input: Business process description
            process_type: Process type (business|technical|workflow)
            quality_target: Target quality (0.0-1.0)
            max_iterations: Maximum number of iterations
            
        Returns:
            Tuple[bool, str, Dict]: (success, bpmn_xml, metadata)
            
        Metadata contains:
            - iterations: Number of iterations performed
            - final_score: Achieved quality score
            - processing_time: Processing time
            - improvement_history: Optimization history
        """
```

#### `create_bpmn_integration()`

**Factory function for creating BPMNIntegration instances.**

```python
def create_bpmn_integration(
    api_key: str,
    model_provider: str,
    chat_url: str,
    default_model: str
) -> Optional[BPMNIntegration]:
    """
    Creates BPMNIntegration instance with provided configuration.
    
    Args:
        api_key: Provider API key
        model_provider: Provider name (openai|gemini|claude|ollama)
        chat_url: Chat endpoint URL
        default_model: Default model
        
    Returns:
        BPMNIntegration or None on configuration error
    """
```

### Module: `bpmn_v2.complete_pipeline`

#### Class: `BPMNv2Pipeline`

**BPMN v2 pipeline with full component integration.**

```python
class BPMNv2Pipeline:
    def __init__(self, ai_config: Optional[AIConfig] = None):
        """
        Initializes BPMN v2 pipeline.
        
        Args:
            ai_config: Optional AI configuration
        """
        
    def generate_complete_bpmn(
        self, 
        polish_description: str,
        context_type: ContextType = ContextType.GENERAL
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Polish text → AI → JSON → BPMN XML.
        
        Args:
            polish_description: Process description in Polish
            context_type: Context type (GENERAL|BANKING|INSURANCE|HEALTHCARE)
            
        Returns:
            Dict with pipeline results:
                - success: bool
                - bpmn_xml: str
                - quality_score: float
                - processing_metadata: dict
        """
```

---

## 📊 PlantUML API

### Module: `src.main` / `utils.plantuml`

#### PlantUML Generation Functions

```python
def generate_plantuml(
    prompt: str,
    diagram_type: str,
    template: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Generates PlantUML code for various diagram types.
    
    Args:
        prompt: Diagram description
        diagram_type: sequence|activity|class|component|usecase|state
        template: Optional prompt template
        
    Returns:
        Tuple[bool, str]: (success, plantuml_code)
    """

def validate_plantuml(plantuml_code: str) -> Tuple[bool, str]:
    """
    Validates PlantUML code by attempting SVG generation.
    
    Args:
        plantuml_code: PlantUML code to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message_or_svg)
    """

def render_plantuml_svg(plantuml_code: str) -> Optional[str]:
    """
    Renders PlantUML code to SVG format.
    
    Args:
        plantuml_code: PlantUML code
        
    Returns:
        str: SVG content or None on error
    """
```

---

## 📄 PDF Analysis API

### Module: `utils.pdf.ai_pdf_analyzer`

#### Class: `AIPDFAnalyzer`

**PDF document analysis using AI.**

```python
class AIPDFAnalyzer:
    def __init__(self):
        """
        Initializes PDF analyzer with configuration from .env.
        
        Environment Variables:
            - PDF_ANALYSIS_MODE: ai|local
            - PDF_ANALYSIS_MODEL: Model for PDF analysis
            - PDF_ANALYSIS_PROMPT_LANG: pl|en
        """
        
    def analyze_pdf(
        self, 
        pdf_path: str, 
        diagram_type: str,
        max_pages: int = 50
    ) -> Dict[str, Any]:
        """
        Analyzes PDF document and extracts business context.
        
        Args:
            pdf_path: Path to PDF file
            diagram_type: Diagram type (activity|sequence|class|component)
            max_pages: Maximum number of pages to process
            
        Returns:
            Dict with analysis results:
                - success: bool
                - business_context: str
                - key_entities: List[str]
                - process_steps: List[str]
                - error: Optional[str]
        """
```

### Module: `utils.pdf.pdf_extractor`

#### Text Extraction Functions

```python
def extract_text_from_pdf(
    pdf_path: str, 
    max_pages: int = None
) -> Tuple[bool, str]:
    """
    Extracts text from PDF document.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages
        
    Returns:
        Tuple[bool, str]: (success, extracted_text)
    """

def chunk_text(text: str, chunk_size: int = 4000) -> List[str]:
    """
    Splits text into smaller chunks.
    
    Args:
        text: Text to split
        chunk_size: Chunk size
        
    Returns:
        List[str]: List of text chunks
    """
```

---

## 🖥️ Desktop Application API

### Module: `src.main`

#### Class: `AIApp` (QMainWindow)

**Main desktop application PyQt5.**

```python
class AIApp(QMainWindow):
    def __init__(self):
        """
        Initializes main desktop application window.
        """
        
    def send_to_api(self) -> None:
        """
        Sends request to API without blocking GUI.
        Handles PlantUML and BPMN generation.
        """
        
    def handle_bpmn_generation(self, process_description: str) -> None:
        """
        Handles BPMN v2 generation from GUI.
        
        Args:
            process_description: Process description from GUI
        """
        
    def enhance_prompt_with_pdf_context(
        self, 
        prompt: str, 
        diagram_type: str
    ) -> str:
        """
        Enhances prompt with PDF analysis context.
        
        Args:
            prompt: Original prompt
            diagram_type: Diagram type
            
        Returns:
            str: Enhanced prompt
        """
```

---

## 🌐 Web Application API

### Module: `src.streamlit_app`

#### Main Streamlit Functions

```python
def render_bpmn_interface() -> None:
    """
    Renders BPMN v2 interface in Streamlit application.
    Handles quality parameters, progress tracking, results.
    """

def handle_plantuml_generation(
    prompt: str, 
    diagram_type: str,
    template: str
) -> Tuple[bool, str]:
    """
    Handles PlantUML generation in web interface.
    
    Args:
        prompt: Diagram description
        diagram_type: Diagram type 
        template: Prompt template
        
    Returns:
        Tuple[bool, str]: (success, result)
    """
    
def display_svg_diagram(svg_content: str) -> None:
    """
    Displays SVG diagram in Streamlit interface.
    
    Args:
        svg_content: SVG content to display
    """
```

---

## 🔍 Validation & Quality APIs

### Module: `bpmn_v2.bpmn_compliance_validator`

#### Class: `BPMNComplianceValidator`

**BPMN compliance validation with standards.**

```python
class BPMNComplianceValidator:
    def validate_bpmn_xml(self, bpmn_xml: str) -> ValidationResult:
        """
        Validates BPMN XML for standard compliance.
        
        Args:
            bpmn_xml: BPMN XML code
            
        Returns:
            ValidationResult: Validation results
        """
        
    def calculate_quality_score(self, bpmn_xml: str) -> float:
        """
        Calculates quality score for BPMN diagram.
        
        Args:
            bpmn_xml: BPMN XML code
            
        Returns:
            float: Quality score (0.0-1.0)
        """
```

---

## ⚡ Utilities APIs

### Module: `utils.logger_utils`

```python
def log_info(message: str, component: str = "System") -> None:
def log_error(message: str, error: Exception = None) -> None:
def log_warning(message: str) -> None:
```

### Module: `utils.extract_code_from_response`

```python
def extract_plantuml_code(response: str) -> Optional[str]:
def extract_bpmn_xml(response: str) -> Optional[str]:
```

---

## 🎭 Mock APIs (Testing)

### Module: `bpmn_v2.ai_integration`

#### Class: `MockAIClient`

**Mock client for testing without real API calls.**

```python
class MockAIClient:
    def send_request(self, prompt: str) -> AIResponse:
        """
        Simulates AI response for testing purposes.
        
        Args:
            prompt: Test prompt
            
        Returns:
            AIResponse: Simulated response
        """
```

---

## 📋 Error Handling

### Exception Hierarchy

```python
class GDPythonError(Exception):
    """Base exception for GD system."""

class AIConfigurationError(GDPythonError):
    """AI provider configuration error."""

class BPMNGenerationError(GDPythonError):
    """BPMN generation error."""

class QualityThresholdError(GDPythonError):
    """Failed to achieve required quality."""

class PDFAnalysisError(GDPythonError):
    """PDF analysis error."""
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
    "business_context": "Mortgage loan processing...",
    "key_entities": ["Customer", "Bank", "Loan", "Property"],
    "process_steps": [
        "Application submission",
        "Document verification", 
        "Credit assessment",
        "Loan decision"
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

### Complete BPMN Generation Example

```python
from src.bpmn_integration import create_bpmn_integration
from bpmn_v2.ai_config import create_bpmn_config

# Configuration
integration = create_bpmn_integration(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model_provider="gemini",
    chat_url="https://generativelanguage.googleapis.com/v1beta/models",
    default_model="gemini-2.0-flash"
)

# BPMN Generation
success, bpmn_xml, metadata = integration.generate_bpmn_process(
    user_input="E-commerce complaint handling process",
    quality_target=0.8,
    max_iterations=10
)

if success:
    print(f"BPMN generated, quality: {metadata['final_score']}")
    print(f"Iterations: {metadata['iterations']}")
    
    # Save to file
    with open("process.bpmn", "w", encoding="utf-8") as f:
        f.write(bpmn_xml)
else:
    print(f"Error: {bpmn_xml}")
```

### Complete Example with PDF Analysis

```python
from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer

# PDF Analysis
analyzer = AIPDFAnalyzer()
result = analyzer.analyze_pdf(
    pdf_path="documents/process_spec.pdf",
    diagram_type="activity"
)

if result["success"]:
    # Use context in generation
    enhanced_prompt = f"""
    {original_prompt}
    
    Business context from documentation:
    {result["business_context"]}
    
    Key elements: {', '.join(result["key_entities"])}
    """
    
    # Generation with enhanced prompt
    success, bpmn_xml, metadata = integration.generate_bpmn_process(
        user_input=enhanced_prompt
    )
```