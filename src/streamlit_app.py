import streamlit as st
import requests
import re
from datetime import datetime
import traceback
import base64
from io import BytesIO
import os
import sys

# Add parent directory to path to access utils and other modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from language.translations_pl import TRANSLATIONS as PL
from language.translations_en import TRANSLATIONS as EN

# Import PDF functionality
try:
    from utils.pdf.streamlit_pdf_integration import PDFUploadManager
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    PDFUploadManager = None

# Load environment variables
load_dotenv()

# Initialize session state for language if not exists
if 'current_language' not in st.session_state:
    st.session_state.current_language = "pl"

LANG = st.session_state.current_language

def tr(key):
    return EN[key] if LANG == "en" else PL[key]

def update_language():
    """Update language and reinitialize prompt templates"""
    global LANG, prompt_templates, get_diagram_specific_requirements
    LANG = st.session_state.current_language
    if LANG == "en":
        from prompts.prompt_templates_en import prompt_templates, get_diagram_specific_requirements
    else:
        from prompts.prompt_templates_pl import prompt_templates, get_diagram_specific_requirements
    st.rerun()

# Try to import custom modules with error handling
try:
    from utils.extract_code_from_response import extract_xml, extract_plantuml, extract_plantuml_blocks, is_valid_xml
    from input_validator import validate_input_text
    from utils.plantuml.plantuml_utils import plantuml_encode, identify_plantuml_diagram_type, fetch_plantuml_svg_local, fetch_plantuml_svg_www
    if LANG == "en":
        from prompts.prompt_templates_en import prompt_templates, get_diagram_specific_requirements
    else:
        from prompts.prompt_templates_pl import prompt_templates, get_diagram_specific_requirements
    from utils.logger_utils import setup_logger, log_info, log_error, log_exception, log_debug
    #from plantuml_to_ea import plantuml_to_xmi
    from utils.plantuml.plantuml_sequance_parser import PlantUMLSequenceParser
    from utils.xmi.xmi_sequance_generator import XMISequenceGenerator
    
    # Try to import BPMN integration
    try:
        from bpmn_integration import create_bpmn_integration, display_bpmn_result, display_bpmn_validation
        BPMN_AVAILABLE = True
    except ImportError as e:
        BPMN_AVAILABLE = False
        print(f"BPMN integration not available: {e}")
    from utils.plantuml.plantuml_class_parser import PlantUMLClassParser
    from utils.xmi.xmi_class_generator import XMIClassGenerator
    from utils.plantuml.plantuml_activity_parser import PlantUMLActivityParser
    from utils.xmi.xmi_activity_generator import XMIActivityGenerator 
    from utils.plantuml.plantuml_component_parser import PlantUMLComponentParser
    from utils.xmi.xmi_component_generator import XMIComponentGenerator
    MODULES_LOADED = True
except ImportError as e:
    MODULES_LOADED = False
    st.error(tr("modules_import_error").format(error=str(e)))
    st.stop()

# Configuration - Load from environment variables
try:
    setup_logger("streamlit_app.log")
except Exception as e:
    st.warning(tr("logger_setup_error").format(error=str(e)))

# Load configuration from .env file
plantuml_jar_path = os.getenv("PLANTUML_JAR_PATH", "plantuml.jar")
plantuml_generator_type = os.getenv("PLANTUML_GENERATOR_TYPE", "local")
API_URL = os.getenv("API_URL", "http://localhost:1234/v1/models")
CHAT_URL = os.getenv("CHAT_URL", "http://localhost:1234/v1/chat/completions")
API_KEY = os.getenv("API_KEY", "")
API_DEFAULT_MODEL = os.getenv("API_DEFAULT_MODEL", "")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "local")  # lub "gemini"

# Initialize BPMN Integration if available
bpmn_integration = None
if BPMN_AVAILABLE and API_KEY and MODEL_PROVIDER:
    try:
        bpmn_integration = create_bpmn_integration(
            api_key=API_KEY,
            model_provider=MODEL_PROVIDER,
            chat_url=CHAT_URL,
            default_model=API_DEFAULT_MODEL
        )
        if bpmn_integration:
            log_info("BPMN Integration initialized successfully")
        else:
            log_info("BPMN Integration not available (configuration issue)")
    except Exception as e:
        log_error(f"Failed to initialize BPMN Integration: {e}")
        bpmn_integration = None

# Page configuration
st.set_page_config(
    page_title=tr("setWindowTitle"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'latest_response' not in st.session_state:
    st.session_state.latest_response = ""
if 'latest_xml' not in st.session_state:
    st.session_state.latest_xml = ""
if 'latest_plantuml' not in st.session_state:
    st.session_state.latest_plantuml = ""
if 'plantuml_diagrams' not in st.session_state:
    st.session_state.plantuml_diagrams = []
if 'verification_attempts' not in st.session_state:
    st.session_state.verification_attempts = 0
if 'last_prompt_type' not in st.session_state:
    st.session_state.last_prompt_type = None
if 'models' not in st.session_state:
    st.session_state.models = []
if 'show_plantuml_code' not in st.session_state:
    st.session_state.show_plantuml_code = False
if 'selected_diagram_index' not in st.session_state:
    st.session_state.selected_diagram_index = 0

# Initialize PDF manager if available
if PDF_SUPPORT:
    if 'pdf_manager' not in st.session_state:
        st.session_state.pdf_manager = PDFUploadManager()

# Helper functions for safe logging
def safe_log_info(message):
    try:
        log_info(message)
    except:
        pass

def safe_log_error(message): 
    try:
        log_error(message)
    except:
        pass

def safe_log_exception(message):
    try:
        log_exception(message)
    except:
        pass

# Helper functions
@st.cache_data
def get_loaded_models(_model_provider=None, _api_key=None):
    """Pobiera listę załadowanych modeli z API lub Gemini."""
    provider = _model_provider or MODEL_PROVIDER
    api_key = _api_key or API_KEY
    
    if provider == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            models = genai.list_models()
            # Filtrowanie tylko modeli obsługujących generateContent
            models_data = [
                {"id": m.name, "description": getattr(m, "description", ""), "supported": m.supported_generation_methods}
                for m in models if "generateContent" in getattr(m, "supported_generation_methods", [])
            ]
            safe_log_info(f"Loaded Gemini models: {len(models_data)} models found.")
            return models_data
        except Exception as e:
            safe_log_exception(f"Gemini error: {e}")
            return None
    elif provider == "mock":
        # Mock models for testing
        return [
            {"id": "mock-model-1", "description": "Mock model for testing"},
            {"id": "mock-model-2", "description": "Another mock model"}
        ]
    else:
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {API_KEY}"
        }
        try:
            response = requests.get(API_URL, headers=headers)
            safe_log_info(f"Request to {API_URL} returned status code {response.status_code}")
            if response.status_code == 200:
                safe_log_info(f"Response from {API_URL}: {response.text[:500]}...")
                models_data = response.json().get("data", [])
                return models_data
            else:
                error_msg = tr("error_fetch_models").format(status_code=response.status_code, text=response.text)
                safe_log_error(error_msg)
                return None
        except Exception as e:
            #error_msg = f"Wystąpił błąd podczas pobierania listy modeli: {e}"
            error_msg = tr("error_fetch_models_exception").format(error=str(e))
            safe_log_exception(error_msg)
            return None

def call_api(prompt, model_name):
    """Wywołuje API z podanym promptem i modelem."""
    if MODEL_PROVIDER == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            # Odpowiedź Gemini może mieć różną strukturę, np. response.text lub response.candidates[0].content.parts[0].text
            if hasattr(response, "text"):
                content = response.text
            elif hasattr(response, "candidates"):
                content = response.candidates[0].content.parts[0].text
            else:
                content = str(response)
            if os.getenv("DB_HOST") is not None:
                if os.getenv("DB_PROVIDER") == "mysql":
                    from utils.db.mysql_connector import log_ai_interaction
                    log_ai_interaction(request=prompt, response=content, model_name=model_name, status_code=None)
                elif os.getenv("DB_PROVIDER") == "postgresql":
                    from utils.db.PostgreSQL_connector import log_ai_interaction
                    log_ai_interaction(request=prompt, response=content, model_name=model_name, status_code=None)
            return content
        except Exception as e:
            safe_log_exception(f"Gemini API error: {e}")
            return f"Error Gemini API: {e}"
    else:
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {API_KEY}"
        }
        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7
        }
        try:
            response = requests.post(CHAT_URL, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                log_ai_interaction(request=prompt, response=content, model_name=model_name, status_code=response.status_code)
                return content
            else:
                return f"Błąd API: {response.status_code} - {response.text}"
        except Exception as e:
            error_msg = tr("error_connection").format(error=str(e))
            safe_log_exception(error_msg) 
            return error_msg
    
    

    

def get_complexity_level(level):
    """Zwraca poziom złożoności."""
    complexity = {
        "simple": "Podstawowe elementy, linearny przepływ",
        "medium": "Bramki decyzyjne, podstawowa obsługa błędów",
        "complex": "Sub-procesy, pełna obsługa wyjątków",
        "enterprise": "Pełny governance, monitoring, integracje"
    }
    return complexity.get(level, complexity["medium"])

def get_validation_rule(rule):
    """Zwraca regułę walidacji."""
    validation = {
        "syntax": "Walidacja XML Schema",
        "semantic": "Logika biznesowa",
        "camunda": "Kompatybilność z Camunda",
        "best_practices": "Najlepsze praktyki BPMN"
    }
    return validation.get(rule, validation["syntax"])

def get_output_format(format_type):
    """Zwraca format wyjściowy."""
    output_format = {
        "clean": "Tylko XML bez komentarzy",
        "documented": "XML z komentarzami wyjaśniającymi",
        "structured": "XML z dodatkowymi metadanymi"
    }
    return output_format.get(format_type, output_format["clean"])

def get_domain(domain):
    """Zwraca tłumaczoną nazwę domeny na podstawie klucza."""
    # domyślnie 'banking' jeśli nie znaleziono
    domain_key = domain if domain in [
        "NONE", "banking", "insurance", "logistics", "healthcare", "e-commerce"
    ] else "banking"
    return tr(f"domain_{domain_key}")

def save_file(content, filename):
    """Zapisuje zawartość do pliku i zwraca link do pobrania."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{filename}_{timestamp}"
    
    # Create download link
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{full_filename}">Pobierz {full_filename}</a>'
    return href

def display_plantuml_diagram(plantuml_code):
    """Wyświetla diagram PlantUML."""
    try:
        if plantuml_generator_type == "www":
            if plantuml_code is not None:
                safe_log_info(tr("plantuml_code_display").format(code=plantuml_code))
                svg_data, err_msg = fetch_plantuml_svg_www(plantuml_code, LANG=LANG)
                
                # Sprawdź czy wystąpił błąd PlantUML
                if err_msg:
                    safe_log_error(f"PlantUML błąd (www): {err_msg}")
                    st.error(f"Błąd PlantUML: {err_msg}")
                    return False
                
            else:
                error_msg = tr("msg_error_fetching_plantuml")
                st.error(error_msg)
                safe_log_error(error_msg + f": {plantuml_code}")
                return False
            
            if isinstance(svg_data, bytes):
                svg_str = svg_data.decode('utf-8')
                
                # Sprawdź czy SVG zawiera komunikat błędu
                if _is_error_svg(svg_str):
                    safe_log_error("SVG zawiera komunikat błędu PlantUML")
                    st.error("Diagram zawiera błędy składniowe PlantUML")
                    return False
                
                #resize SVG to fit the container
                #svg_str = svg_str.replace('width="100%"', 'width="50%" height="600"')
                #st.components.v1.html(svg_str, height=1000)
                st.image(
                    svg_str,
                    width=None,
                    use_container_width=True
                )
                return True
                
        elif plantuml_generator_type == "local":
            svg_path, err_msg = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path, LANG=LANG)
            
            # Sprawdź czy wystąpił błąd PlantUML  
            if err_msg:
                safe_log_error(f"PlantUML błąd (local): {err_msg}")
                st.error(f"Błąd PlantUML: {err_msg}")
                return False
                
            # Sprawdź czy plik SVG istnieje
            if not os.path.exists(svg_path):
                safe_log_error(f"Plik SVG nie został utworzony: {svg_path}")
                st.error("Nie udało się wygenerować diagramu SVG")
                return False
                
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_str = f.read()  
                
                # Sprawdź czy SVG zawiera komunikat błędu
                if _is_error_svg(svg_str):
                    safe_log_error("SVG zawiera komunikat błędu PlantUML")
                    st.error("Diagram zawiera błędy składniowe PlantUML") 
                    return False
                    
                #resize SVG to fit the container
                #svg_str = svg_str.replace('width="100%"', 'width="500%" height="600"')
            #st.components.v1.html(svg_str, height=1000)
                st.image(
                    svg_str,
                    width=None,
                    use_container_width=True
                )
            return True
            
    except Exception as e:
        error_msg = tr("msg_error_displaying_plantuml_exception").format(error=str(e))
        safe_log_exception(error_msg)
        st.error(error_msg)
        return False
    
    # Jeśli doszliśmy tutaj, coś poszło nie tak
    return False

def _is_error_svg(svg_content: str) -> bool:
    """Sprawdza czy SVG zawiera komunikat błędu PlantUML."""
    error_indicators = [
        "Syntax Error?",
        "Unknown preprocessing", 
        "Error line",
        "Syntax error",
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?><svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" contentScriptType=\"application/ecmascript\" contentStyleType=\"text/css\" height=\"16px\" preserveAspectRatio=\"none\" style=\"width:323px;height:16px;\" version=\"1.1\" viewBox=\"0 0 323 16\" width=\"323px\" zoomAndPan=\"magnify\"><defs><filter height=\"300%\" id=\"f1nk1pfzhqwmoc\" width=\"300%\" x=\"-1\" y=\"-1\"><feGaussianBlur result=\"blurOut\" stdDeviation=\"2.0\"/><feColorMatrix in=\"blurOut\" result=\"blurOut2\" type=\"matrix\" values=\"0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .4 0\"/><feOffset dx=\"4.0\" dy=\"4.0\" in=\"blurOut2\" result=\"blurOut3\"/><feBlend in=\"SourceGraphic\" in2=\"blurOut3\" mode=\"normal\"/></filter></defs><g><text fill=\"#000000\" font-family=\"sans-serif\" font-size=\"14\" lengthAdjust=\"spacingAndGlyphs\" textLength=\"0\" x=\"148.5\" y=\"11.5016\"/></g></svg>"
    ]
    
    for indicator in error_indicators:
        if indicator in svg_content:
            return True
    
    # Sprawdź czy SVG jest bardzo mały (może być pustym błędem)
    if len(svg_content.strip()) < 200:
        return True
        
    return False

@st.dialog(tr("show_plantuml_dialog"), width="large")
def show_plantuml_modal():
    st.markdown("**"+tr("show_plantuml_dialog")+":**")
    st.code(plantuml_code, language="plantuml")
            
    col1, col2 = st.columns(2)
    with col1:
        if st.download_button(
            label=tr("download_plantuml_button"),
            data=plantuml_code,
            file_name=f"{diagram_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.puml",
            mime="text/plain"
        ):
            st.success(tr("download_plantuml_success"))
    
    with col2:
        if st.button(tr("close_plantuml_button"), type="primary"):
            #st.session_state.show_plantuml_code = False
            st.rerun()

# Load models
if not st.session_state.models:
    with st.spinner(tr("loading_models")):
        models = get_loaded_models(MODEL_PROVIDER, API_KEY)
        if models:
            st.session_state.models = models

# Main UI
st.title(tr("setWindowTitle"))
st.markdown((tr("app_description")))

# Sidebar configuration
with st.sidebar:
    st.header(tr("configuration_lable"))
    
    # Language selection - at the top
    lang_options = {"pl": tr("language_polish"), "en": tr("language_english")}
    selected_lang = st.selectbox(
        tr("language_selector"), 
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=0 if st.session_state.current_language == "pl" else 1,
        key="language_selectbox"
    )
    
    if selected_lang != st.session_state.current_language:
        st.session_state.current_language = selected_lang
        update_language()
    
    st.divider()
    
    # Model selection
    if st.session_state.models:
        model_names = [model.get("id", "unknown") for model in st.session_state.models]
        selected_model = st.selectbox(tr("select_model_label"), model_names, 
                                      index = 0 if API_DEFAULT_MODEL not in model_names else model_names.index(API_DEFAULT_MODEL))
    else:
        st.error(tr("model_loaded_error"))
        selected_model = None
    
    st.divider()
    
    # Template configuration
    st.subheader(tr("template_lable"))
    template_type = st.radio(tr("template_type_label"), ["PlantUML", "BPMN"])
    
    # Filter templates by type
    if template_type == "BPMN":
        # Use XML templates for BPMN (they are compatible)
        filtered_templates = [
            name for name, data in prompt_templates.items()
            if data.get("type") == "XML"
        ]
    else:
        filtered_templates = [
            name for name, data in prompt_templates.items()
            if data.get("type") == template_type
        ]
    
    selected_template = st.selectbox(tr("template_selector"), filtered_templates)
    
    use_template = st.checkbox(tr("use_template_checkboxuse_template_checkbox"), value=True)
    
    st.divider()
    
    # Diagram type selection
    if selected_template and selected_template in prompt_templates:
        template_data = prompt_templates[selected_template]
        allowed_types = template_data["allowed_diagram_types"]
        all_types = [
            "sequence", "activity", "use case", "class", "state",
            "communication", "component", "deployment", "timing", "collaboration"
        ]
        
        if allowed_types == "all":
            diagram_types = all_types
        else:
            diagram_types = allowed_types
        
        diagram_type = st.selectbox(tr("template_layout.select_label"), diagram_types)
    else:
        diagram_type = st.selectbox(tr("template_layout.select_label"), [
            "sequence", "activity", "usecase", "class", "state", "flowchart",
            "communication", "component", "deployment", "timing", "collaboration"
        ])
    
    # BPMN specific options
    if template_type == "BPMN":
        st.subheader(tr("bpmn_generation_header"))
        
        # Show BPMN availability status
        if bpmn_integration and bpmn_integration.is_available():
            st.success(f"✅ BPMN dostępny ({MODEL_PROVIDER})")
        else:
            st.error("❌ BPMN niedostępny - sprawdź konfigurację AI")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bpmn_quality = st.slider(
                tr("bpmn_quality_label"), 
                min_value=0.5, max_value=1.0, value=0.8, step=0.1,
                help="Minimalna jakość procesu (wyższe wartości = więcej iteracji)"
            )
        
        with col2:
            bpmn_iterations = st.number_input(
                tr("bpmn_iterations_label"),
                min_value=1, max_value=10, value=10,
                help="Maksymalna liczba iteracji poprawek"
            )
            
        with col3:
            bpmn_process_type = st.selectbox(
                tr("bpmn_process_type_label"),
                ["business", "technical", "administrative", "support"],
                help="Typ procesu wpływa na styl generowania"
            )
    
    elif diagram_type.lower() in ["bpmn", "bpmn_flow", "bpmn_component"]:
        st.subheader("Opcje BPMN")
        complexity_level = st.selectbox("Poziom złożoności:", 
                                      ["simple", "medium", "complex", "enterprise"])
        validation_rule = st.selectbox("Reguła walidacji:", 
                                     ["syntax", "semantic", "camunda", "best_practices"])
        output_format = st.selectbox("Format wyjściowy:", 
                                   ["clean", "documented", "structured"])
        domain = st.selectbox("Domena:", 
                              ["NONE", "banking", "insurance", "logistics", "healthcare", "e-commerce"])

# PDF Upload Section (if supported)
if PDF_SUPPORT and 'pdf_manager' in st.session_state:
    st.session_state.pdf_manager.render_pdf_upload_section()

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header(tr("input_box"))
    process_description = st.text_area(
        "Opis procesu",
        height=150,
        placeholder=tr("input_box.setToolTip"),
    )
    
    # Validation button
    if st.button(tr("validate_input_button")):
        info_msg = tr("msg_info_sending_code_for_verification_log").format(process_description=process_description[:1000])
        safe_log_info(info_msg) 
        if process_description:
            
            # Simulate validation (you can implement actual validation logic)
            #info_msg = ("**Przekazano opis procesu do weryfikacji**\n")
            info_msg = tr("msg_info_sending_code_for_verification")
            st.spinner({"role": "System", "content": info_msg})
            safe_log_info(info_msg) 
            # Pobierz tekst z input_box
            if not process_description:
                st.session_state.conversation_history.append({"role": "System", "content": tr("msg_error_no_text_for_validation")})
                    
            # Pobierz szablon walidacji (np. "Weryfikacja opisu procesu")
            template_data = prompt_templates.get(tr("proces_description_validation"))
            if not template_data:
                st.session_state.conversation_history.append({"role": "System", "content": tr("msg_error_no_template_for_validation")})
            prompt = template_data["template"].format(
                process_description=process_description,
                diagram_type=diagram_type,
                diagram_specific_requirements=get_diagram_specific_requirements(diagram_type))
            last_prompt_type = "InputValidation"
            #send_to_api_custom_prompt(prompt)

            st.session_state.conversation_history.append({"role": "user", "content": prompt})
            safe_log_info(f"Prompt sent for validation: {prompt[:5000]}...")
            
            # Increment verification attempts
            if 'verification_attempts' not in st.session_state:
                st.session_state.verification_attempts = 0
            st.session_state.verification_attempts += 1

            with st.spinner(tr("msg_info_sending_description_for_verification")):
                response = call_api(prompt, selected_model)
                safe_log_info(f"Response from API: {response[:5000]}...")
                # Store response
                st.session_state.latest_response = response
                #st.session_state.conversation_history.append({"role": "user", "content": prompt})
                st.session_state.conversation_history.append({"role": "assistant", "content": response})
                    
                # Check for XML content
                xml_content = extract_xml(response)
                if xml_content and is_valid_xml(xml_content):
                    st.session_state.latest_xml = xml_content
                    
                # Check for PlantUML content
                plantuml_blocks = extract_plantuml_blocks(response)
                if plantuml_blocks:
                    st.session_state.latest_plantuml = plantuml_blocks[-1]
                    st.session_state.plantuml_diagrams = plantuml_blocks
                    
                st.rerun()
                st.success(tr("msg_info_validation_success"))
        else:
            st.warning(tr("msg_warning_no_text_for_validation"))
    
    # Send query button
    if st.button(tr("send_button"), type="primary"):
        if not process_description:
            st.error(tr("error_sending_request_empty"))
        elif not selected_model:
            st.error(tr("error_sending_request_no_model"))
        else:
            with st.spinner(tr("msg_info_generating_response")):
                # Prepare prompt
                if use_template and selected_template in prompt_templates:
                    template_data = prompt_templates[selected_template]
                    
                    # Use old BPMN logic only if template_type is not "BPMN" (for backward compatibility)
                    if diagram_type.lower() in ["bpmn", "bpmn_flow", "bpmn_component"] and template_type != "BPMN":
                        if selected_template == tr("bpmn_template_basic"):
                            prompt = template_data["template"].format(
                                diagram_type=diagram_type,
                                process_description=process_description,
                                diagram_specific_requirements=get_diagram_specific_requirements(diagram_type)
                            )
                        elif selected_template == tr("bpmn_template_advanced"):
                            prompt = template_data["template"].format(
                                diagram_type=diagram_type,
                                process_description=process_description,
                                diagram_specific_requirements=get_diagram_specific_requirements(diagram_type)
                            )
                        elif selected_template == tr("bpmn_template_bank"):
                            complexity = get_complexity_level(complexity_level)
                            validation = get_validation_rule(validation_rule)
                            output_fmt = get_output_format(output_format)
                            domain_desc = get_domain(domain)
                            
                            prompt = template_data["template"].format(
                                process_description = process_description + tr("bpmn_bank_details").format(
                                    complexity=complexity,
                                    validation=validation,
                                    output_format=output_format
                                ),
                                domain=domain_desc,
                            )
                        else:
                            prompt = process_description
                    else:
                        prompt = template_data["template"].format(
                            diagram_type=diagram_type,
                            process_description=process_description,
                            diagram_specific_requirements=get_diagram_specific_requirements(diagram_type)
                        )
                else:
                    prompt = process_description
                
                # Enhance prompt with PDF context if available
                if PDF_SUPPORT and 'pdf_manager' in st.session_state:
                    prompt = st.session_state.pdf_manager.get_enhanced_prompt(prompt, diagram_type)
                
                # Handle BPMN generation using BPMN Integration
                safe_log_info(f"Template type: {template_type}, BPMN integration available: {bpmn_integration is not None and bpmn_integration.is_available() if bpmn_integration else False}")
                
                if template_type == "BPMN" and bpmn_integration and bpmn_integration.is_available():
                    safe_log_info("Starting BPMN generation...")
                    # DEBUG kommunikat usunięty dla czystości logów
                    # DEBUG komunik previewu usunięty dla czystości logów
                    success, bpmn_result, metadata = bpmn_integration.generate_bpmn_process(
                        user_input=process_description,  # Use raw process_description, not processed prompt!
                        process_type=bpmn_process_type,
                        quality_target=bpmn_quality,
                        max_iterations=bpmn_iterations
                    )
                    
                    safe_log_info(f"BPMN generation result: success={success}")
                    
                    if success:
                        st.session_state.latest_xml = bpmn_result
                        st.session_state.latest_response = f"Generated BPMN process:\n\n{bpmn_result}"
                        st.session_state.conversation_history.append({"role": "user", "content": prompt})
                        st.session_state.conversation_history.append({"role": "assistant", "content": f"BPMN process generated successfully"})
                        display_bpmn_result(success, bpmn_result, metadata)
                        # Don't call st.rerun() here - let Streamlit handle the refresh naturally
                    else:
                        st.error(f"BPMN generation failed: {bpmn_result}")
                        # Add failed attempt to conversation history for transparency
                        st.session_state.conversation_history.append({"role": "user", "content": prompt})
                        st.session_state.conversation_history.append({"role": "assistant", "content": f"❌ BPMN generation failed: {bpmn_result}"})
                
                # Regular API call for PlantUML and other types
                else:
                    # Call API
                    response = call_api(prompt, selected_model)
                    safe_log_info(f"Response from model: {response[:5000]}...")
                    
                    # Store response
                    st.session_state.latest_response = response
                    st.session_state.conversation_history.append({"role": "user", "content": prompt})
                    st.session_state.conversation_history.append({"role": "assistant", "content": response})
                    
                    # Check for XML content
                    xml_content = extract_xml(response)
                    if xml_content and is_valid_xml(xml_content):
                        st.session_state.latest_xml = xml_content
                    
                    # Check for PlantUML content
                    plantuml_blocks = extract_plantuml_blocks(response)
                    if plantuml_blocks:
                        st.session_state.latest_plantuml = plantuml_blocks[-1]
                        st.session_state.plantuml_diagrams = plantuml_blocks
                    
                    st.rerun()

with col2:
    st.header(tr("conversation_lable"))
    with st.container(height=600):
        if st.session_state.conversation_history:
            # Display conversation history
            for i, message in enumerate(st.session_state.conversation_history):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])

# Display diagrams and download options
if st.session_state.plantuml_diagrams:
    st.header(tr("generated_diagrams"))
    
    # Create tabs for each diagram
    if len(st.session_state.plantuml_diagrams) > 1:
#        tabs = st.tabs([f"{identify_plantuml_diagram_type(st.session_state.plantuml_diagrams[i+1])}" for i in range(len(st.session_state.plantuml_diagrams))])
        tabs = st.tabs([f"{identify_plantuml_diagram_type(p, LANG=LANG)}" for p in st.session_state.plantuml_diagrams])        
        for i, (tab, plantuml_code) in enumerate(zip(tabs, st.session_state.plantuml_diagrams)):
            with tab:

                st.subheader(f"Diagram {i+1}")
                diagram_type_identified = identify_plantuml_diagram_type(plantuml_code, LANG=LANG)
                st.subheader(tr("diagram_subheader_name") + f": {diagram_type_identified}")
                diagrams = st.session_state.plantuml_diagrams
                with st.expander(f"Diagram {i+1}"):
                    if plantuml_code is not None:
                        if not display_plantuml_diagram(plantuml_code):
                            # Weryfikacja kodu w przypadku błędów
                            diagram_type = identify_plantuml_diagram_type(plantuml_code, LANG=LANG)
                            safe_log_info(tr("msg_info_validation_error").format(plantuml_code=plantuml_code)) 
                            verification_template = prompt_templates[tr("verification_template")]["template"]
                            prompt = verification_template.format(plantuml_code=plantuml_code, diagram_type=diagram_type)
                            safe_log_info(f"Prompt for verification: {prompt}") 
                            st.info(tr("msg_sending_code_for_verification"))
                            response = call_api(prompt, selected_model)
                            safe_log_info(f"Response from API (Verification): {response[:5000]}...")  # Loguj pierwsze 5000 znaków odpowiedzi
                            # wyciągniecie kodu PlantUML z odpowiedzi modelu
                            plantuml_code = extract_plantuml(response)
                            plantuml_code = plantuml_code.replace("!theme ocean", "")
                            plantuml_code = plantuml_code.replace("!theme grameful", "")
                            plantuml_code = plantuml_code.replace("!theme plain", "")
                            if not display_plantuml_diagram(plantuml_code):
                                st.error(tr("msg_error_fetching_plantuml_log"))
                                st.stop()
                            else:   
                                #st.session_state.plantuml_diagrams[i] = plantuml_code
                                if plantuml_code is not None:
                                    display_plantuml_diagram(plantuml_code)
                                else:
                                    st.error(tr("msg_error_displaying_plantuml"))
                # Download buttons
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                with col1:
                    if st.button(tr("show_plantuml_dialog"), key=f"show_code_{i}"):
                        st.session_state.show_plantuml_code = True
                        st.session_state.selected_diagram_index = i
                    
                with col2:
                    if st.download_button(
                        label=tr("download_plantuml_button"),
                        data=plantuml_code,
                        file_name=f"diagram_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.puml",
                        mime="text/plain"
                    ):
                        st.success(tr("msg_success_ready_for_downloading_plantuml"))
                
                with col3:
                    try:
                        if plantuml_generator_type == "www":
                            svg_data, err_msg  = fetch_plantuml_svg_www(plantuml_code, LANG=LANG)
                             
                        else:
                            svg_path, err_msg  = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path, LANG=LANG)
                            with open(svg_path, "rb") as f:
                                svg_data = f.read()

                        if st.download_button(
                            label=tr("download_svg_button"),
                            data=svg_data,
                            file_name=f"diagram_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                            mime="image/svg+xml"
                        ):
                            st.success(tr("msg_success_ready_for_downloading_SVG"))
                    except Exception as e:
                        error_msg = tr("msg_error_preparing_svg").format(error=str(e))
                        log_error(error_msg)
                        st.error(error_msg)
                
                with col4:
                    
                    if ("klas" in diagram_type_identified.lower()) or ("class" in diagram_type_identified.lower()):
                        try:
                            parser = PlantUMLClassParser()
                            parser.parse(plantuml_code)
                            diagram_title = parser.title if hasattr(parser, 'title') and parser.title else diagram_type 
                            xmi_content = XMIClassGenerator(autor = "195841").save_xmi(parser.classes, parser.relations, parser.enums, 
                                                            parser.notes, parser.primitive_types, diagram_name = diagram_title)
                            if st.download_button(
                                label=tr("download_xmi_button"),
                                data=xmi_content,
                                file_name=f"diagram_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                                mime="application/xml"
                            ):
                                st.success(tr("msg_success_ready_for_downloading_XMI"))
                        except Exception as e:
                            error_msg = tr("msg_error_generating_xmi").format(error=str(e))
                            safe_log_error(error_msg)   
                            st.error(error_msg)

                    elif ("sekwencji" in diagram_type_identified.lower()) or ("sequence" in diagram_type_identified.lower()):
                        
                        try:
                            parser = PlantUMLSequenceParser(plantuml_code)
                            parsed_data = parser.parse()
                            diagram_title = parsed_data.get('title', diagram_type)
                            xmi_content = XMISequenceGenerator(autor = "195841").generuj_diagram(
                                nazwa_diagramu=diagram_title,
                                dane=parsed_data
                            )
                            #xmi_content = plantuml_to_xmi(plantuml_code)
                            if st.download_button(
                                label=tr("download_xmi_button"),
                                data=xmi_content,
                                file_name=f"{diagram_type}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                                mime="application/xml"
                            ):
                                st.success(tr("msg_success_ready_for_downloading_XMI"))
                        except Exception as e:
                            error_msg = tr("msg_error_generating_xmi").format(error=str(e))
                            safe_log_error(error_msg)   
                            st.error(error_msg)
                    elif ("aktywności" in diagram_type_identified.lower()) or ("activity" in diagram_type_identified.lower()):

                        try:
                            parser = PlantUMLActivityParser(plantuml_code)
                            parsed_data = parser.parse()
                            diagram_title = parsed_data.get('title', diagram_type)
                            xmi_content = XMIActivityGenerator(author = "195841").generate_activity_diagram(
                                nazwa_diagramu=diagram_title,
                                dane=parsed_data
                            )
                            #xmi_content = plantuml_to_xmi(plantuml_code)
                            if st.download_button(
                                label=tr("download_xmi_button"),
                                data=xmi_content,
                                file_name=f"{diagram_type}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                                mime="application/xml"
                            ):
                                st.success(tr("msg_success_ready_for_downloading_XMI"))
                        except Exception as e:
                            error_msg = tr("msg_error_generating_xmi").format(error=str(e))
                            safe_log_error(error_msg)   
                            st.error(error_msg)
                    elif ("komponentów" in diagram_type_identified.lower()) or ("component" in diagram_type_identified.lower()):
                        
                        try:
                            parser = PlantUMLComponentParser(plantuml_code)
                            parsed_data = parser.parse()
                            diagram_title = parsed_data.get('title', diagram_type)
                            xmi_content = XMIComponentGenerator(author = "195841").generate_component_diagram(
                                nazwa_diagramu=diagram_title,
                                dane=parsed_data
                            )
                            #xmi_content = plantuml_to_xmi(plantuml_code)
                            if st.download_button(
                                label=tr("download_xmi_button"),
                                data=xmi_content,
                                file_name=f"{diagram_type}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                                mime="application/xml"
                            ):
                                st.success(tr("msg_success_ready_for_downloading_XMI"))
                        except Exception as e:
                            error_msg = tr("msg_error_generating_xmi").format(error=str(e))
                            safe_log_error(error_msg)   
                            st.error(error_msg)
                    

                    #else:
                        #st.button(f"Pobierz XMI {i+1}", disabled=True, help="XMI dostępne tylko dla diagramów klas", key=f"xmi_button_{i}")
    else:
        # Single diagram
        plantuml_code = st.session_state.plantuml_diagrams[0]
        diagram_type_identified = identify_plantuml_diagram_type(plantuml_code, LANG=LANG)
        st.subheader(tr("diagram_subheader_name") + f": {diagram_type_identified}")
        if not display_plantuml_diagram(plantuml_code):
            # Weryfikacja kodu w przypadku błędów
            safe_log_info(tr("msg_info_verifying_plantuml_code").format(plantuml_code=plantuml_code))
            diagram_type = identify_plantuml_diagram_type(plantuml_code, LANG=LANG)
            verification_template = prompt_templates[tr("verification_template")]["template"]
            prompt = verification_template.format(plantuml_code=plantuml_code, diagram_type=diagram_type)
            info_msg = tr("msg_info_sending_code_for_verification_singele").format(plantuml_code=plantuml_code)
            safe_log_info(info_msg) 
            st.info(tr("msg_sending_code_for_verification"))
            response = call_api(prompt, selected_model)
            safe_log_info(tr("msg_info_response_from_api").format(response=response[:5000])) 
            # wyciągniecie kodu PlantUML z odpowiedzi modelu
            plantuml_code = extract_plantuml(response)
            plantuml_code = plantuml_code.replace("!theme ocean", "")
            plantuml_code = plantuml_code.replace("!theme grameful", "")
            if not display_plantuml_diagram(plantuml_code):
                st.error(tr("msg_error_fetching_plantuml_log"))
                st.stop()
            else:   
                # st.session_state.plantuml_diagrams[i] = plantuml_code
                if plantuml_code is not None:
                    display_plantuml_diagram(plantuml_code)
                else:
                    st.error(tr("msg_error_displaying_plantuml"))  
                
        #display_plantuml_diagram(plantuml_code)
        # Download buttons
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            if st.button(tr("show_plantuml_dialog")):
                st.session_state.show_plantuml_code = True
                st.session_state.selected_diagram_index = 0  # Single diagram, index 0
            
        with col2:
            if st.download_button(
                label=tr("download_plantuml_button"),
                data=plantuml_code,
                file_name=f"diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.puml",
                mime="text/plain"
            ):
                st.success(tr("msg_success_ready_for_downloading_plantuml"))
        
        with col3:
            try:
                if plantuml_generator_type == "www":
                    svg_data, err_msg  = fetch_plantuml_svg_www(plantuml_code, LANG=LANG)
                else:
                    svg_path, err_msg  = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path, LANG=LANG)
                    with open(svg_path, "rb") as f:
                        svg_data = f.read()
                
                if st.download_button(
                    label=tr("download_svg_button"),
                    data=svg_data,
                    file_name=f"diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                    mime="image/svg+xml"
                ):
                    st.success(tr("msg_success_ready_for_downloading_SVG"))
            except Exception as e:
                st.error(tr("msg_error_preparing_svg").format(error=str(e)))
        
        with col4:
            if ("klas" in diagram_type_identified.lower()) or ("class" in diagram_type_identified.lower()):
                try:
                    parser = PlantUMLClassParser()
                    parser.parse(plantuml_code)
                    diagram_title = parser.title if hasattr(parser, 'title') and parser.title else diagram_type_identified
                    xmi_content = XMIClassGenerator(autor = "195841").save_xmi(parser.classes, parser.relations, parser.enums, 
                                                    parser.notes, parser.primitive_types, diagram_name = diagram_title)
                    if st.download_button(
                        label=tr("download_xmi_button"),
                        data=xmi_content,
                        file_name=f"diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                        mime="application/xml"
                    ):
                        st.success(tr("msg_success_ready_for_downloading_XMI"))
                except Exception as e:
                    st.error(tr("msg_error_generating_xmi").format(error=str(e)))
            elif ("sekwencji" in diagram_type_identified.lower()) or ("sequence" in diagram_type_identified.lower()):
                try:
                    parser = PlantUMLSequenceParser(plantuml_code)
                    parsed_data = parser.parse()
                    diagram_title = parsed_data.get('title', diagram_type_identified)
                    xmi_content = XMISequenceGenerator(autor = "195841").generuj_diagram(
                        nazwa_diagramu=diagram_title,
                        dane=parsed_data
                    )
                    #xmi_content = plantuml_to_xmi(plantuml_code)
                    if st.download_button(
                        label=tr("download_xmi_button"),
                        data=xmi_content,
                        file_name=f"{diagram_type}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                        mime="application/xml"
                    ):
                        st.success(tr("msg_success_ready_for_downloading_XMI"))
                except Exception as e:
                    error_msg = tr("msg_error_generating_xmi").format(error=str(e))
                    safe_log_error(error_msg)   
                    st.error(error_msg)

            elif ("aktywności" in diagram_type_identified.lower()) or ("activity" in diagram_type_identified.lower()):

                try:
                    parser = PlantUMLActivityParser(plantuml_code)
                    parsed_data = parser.parse()
                    diagram_title = parsed_data.get('title', diagram_type)
                    xmi_content = XMIActivityGenerator(author = "195841").generate_activity_diagram(
                        diagram_name=diagram_title,
                        parsed_data=parsed_data
                        )
                        #xmi_content = plantuml_to_xmi(plantuml_code)
                    if st.download_button(
                        label=tr("download_xmi_button"),
                        data=xmi_content,
                        file_name=f"{diagram_type}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                        mime="application/xml"
                    ):
                        st.success(tr("msg_success_ready_for_downloading_XMI"))
                except Exception as e:
                    error_msg = tr("msg_error_generating_xmi").format(error=str(e))
                    safe_log_error(error_msg)   
                    st.error(error_msg)

            elif ("komponentów" in diagram_type_identified.lower()) or ("component" in diagram_type_identified.lower()):
                        
                try:
                    parser = PlantUMLComponentParser(plantuml_code)
                    parsed_data = parser.parse()
                    diagram_title = parsed_data.get('title', diagram_type)
                    xmi_content = XMIComponentGenerator(author = "195841").generate_component_diagram(
                        diagram_name=diagram_title,
                        parsed_data1=parsed_data
                    )
                    #xmi_content = plantuml_to_xmi(plantuml_code)
                    if st.download_button(
                        label=tr("download_xmi_button"),
                        data=xmi_content,
                        file_name=f"{diagram_type}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                        mime="application/xml"
                    ):
                        st.success(tr("msg_success_ready_for_downloading_XMI"))
                except Exception as e:
                    error_msg = tr("msg_error_generating_xmi").format(error=str(e))
                    safe_log_error(error_msg)   
                    st.error(error_msg)
            #else:
            #    st.button(tr("download_xmi_button"), disabled=True, help=tr("download_xmi_button_help"))
            

# XML/BPMN download option
if st.session_state.latest_xml:
    # Check if this is BPMN or regular XML
    is_bpmn = "bpmn" in st.session_state.latest_xml.lower() or "process" in st.session_state.latest_xml.lower()
    
    if is_bpmn:
        st.header("🔄 " + tr("download_xml_header") + " (BPMN)")
        
        # Quality indicator (automatic, no manual buttons)
        if bpmn_integration and bpmn_integration.is_available():
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.info("ℹ️ Walidacja i ulepszenia BPMN są wykonywane automatycznie podczas generowania")
            
            with col2:
                # Quality indicator
                with st.spinner("Sprawdzanie jakości..."):
                    try:
                        is_valid, quality_score, _ = bpmn_integration.validate_bpmn(st.session_state.latest_xml)
                        if quality_score > 0:
                            st.metric("Jakość BPMN", f"{quality_score:.2f}", delta=None)
                    except:
                        st.metric("Jakość BPMN", "N/A")
    else:
        st.header(tr("download_xml_header"))
    
    with st.expander(tr("show_xml_button")):
        st.code(st.session_state.latest_xml, language="xml")
    
    if st.download_button(
        label=tr("download_xml_button") + (" (BPMN)" if is_bpmn else ""),
        data=st.session_state.latest_xml,
        file_name=f"{'bpmn_process' if is_bpmn else 'output'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
        mime="application/xml"
    ):
        st.success(tr("msg_success_ready_for_downloading_XML"))

# Modal window for PlantUML code
if st.session_state.show_plantuml_code and st.session_state.plantuml_diagrams:
    # Get the selected diagram index (default to 0 if not set)
    selected_index = st.session_state.get('selected_diagram_index', 0)
    if selected_index < len(st.session_state.plantuml_diagrams):
        plantuml_code = st.session_state.plantuml_diagrams[selected_index]
        diagram_type = identify_plantuml_diagram_type(plantuml_code, LANG=LANG)
    else:
        plantuml_code = st.session_state.plantuml_diagrams[0]
        diagram_type = identify_plantuml_diagram_type(plantuml_code, LANG=LANG)
    
    @st.dialog(tr("show_plantuml_dialog") + f" - {diagram_type}", width="large")
    def show_plantuml_modal():
        st.write(tr("edit_plantuml_code"))
        
        # Edytowalne pole tekstowe dla kodu PlantUML
        edited_code = st.text_area(
            label="",
            value=plantuml_code,
            height=500,
            key=f"plantuml_edit_{selected_index}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(tr("update_diagram_button"), type="secondary"):
                if edited_code.strip():
                    # Aktualizuj kod w session_state
                    st.session_state.plantuml_diagrams[selected_index] = edited_code
                    st.success(tr("msg_diagram_updated"))
                    st.rerun()
                    
        with col2:
            if st.button(tr("close_plantuml_button"), type="primary"):
                st.session_state.show_plantuml_code = False
                st.rerun()
    
   # Show modal and handle closing
    result = show_plantuml_modal()
    
    # If dialog was closed by X button, reset the state
    if result is None:
        st.session_state.show_plantuml_code = False


