import streamlit as st
import requests
import re
from datetime import datetime
import traceback
import base64
from io import BytesIO
import os
from dotenv import load_dotenv
from translations_pl import TRANSLATIONS as PL
from translations_en import TRANSLATIONS as EN


# Load environment variables
load_dotenv()

LANG = "en"  # Domyślny język, można zmienić na "pl" dla polskiego

def tr(key):
    return EN[key] if LANG == "en" else PL[key]

# Try to import custom modules with error handling
try:
    from extract_code_from_response import extract_xml, extract_plantuml, extract_plantuml_blocks, is_valid_xml
    from input_validator import validate_input_text
    from plantuml_utils import plantuml_encode, identify_plantuml_diagram_type, fetch_plantuml_svg_local, fetch_plantuml_svg_www
    if LANG == "en":
        from prompt_templates_en import prompt_templates, get_diagram_specific_requirements
    else:
        from prompt_templates_pl import prompt_templates, get_diagram_specific_requirements
    from logger_utils import setup_logger, log_info, log_error, log_exception
    from plantuml_to_ea import plantuml_to_xmi
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
def get_loaded_models():
    """Pobiera listę załadowanych modeli z API lub Gemini."""
    if MODEL_PROVIDER == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=API_KEY)
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
                safe_log_error(tr("plantuml_code_display").format(code=plantuml_code))
                svg_data = fetch_plantuml_svg_www(plantuml_code, LANG=LANG)
                
            else:
                error_msg = tr("msg_error_fetching_plantuml")
                st.error(error_msg)
                safe_log_error(error_msg + f": {plantuml_code}")
            
            if isinstance(svg_data, bytes):
                svg_str = svg_data.decode('utf-8')
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
            svg_path = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path, LANG=LANG)
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_str = f.read()  
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
        models = get_loaded_models()
        if models:
            st.session_state.models = models

# Main UI
st.title(tr("setWindowTitle"))
st.markdown((tr("app_description")))

# Sidebar configuration
with st.sidebar:
    st.header(tr("configuration_lable"))
    
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
    template_type = st.radio(tr("template_type_label"), ["PlantUML", "XML"])
    
    # Filter templates by type
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
    if diagram_type.lower() in ["bpmn", "bpmn_flow", "bpmn_component"]:
        st.subheader("Opcje BPMN")
        complexity_level = st.selectbox("Poziom złożoności:", 
                                      ["simple", "medium", "complex", "enterprise"])
        validation_rule = st.selectbox("Reguła walidacji:", 
                                     ["syntax", "semantic", "camunda", "best_practices"])
        output_format = st.selectbox("Format wyjściowy:", 
                                   ["clean", "documented", "structured"])
        domain = st.selectbox("Domena:", 
                              ["NONE", "banking", "insurance", "logistics", "healthcare", "e-commerce"])

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header(tr("input_box"))
    process_description = st.text_area(
        "Wprowadź opis procesu:",
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
                    
                    if diagram_type.lower() in ["bpmn", "bpmn_flow", "bpmn_component"]:
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
                            svg_data = fetch_plantuml_svg_www(plantuml_code, LANG=LANG)
                             
                        else:
                            svg_path = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path, LANG=LANG)
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
                    if "klas" in diagram_type_identified.lower():
                        try:
                            xmi_content = plantuml_to_xmi(plantuml_code)
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
                    svg_data = fetch_plantuml_svg_www(plantuml_code, LANG=LANG)
                else:
                    svg_path = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path, LANG=LANG)
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
            if "klas" in diagram_type_identified.lower():
                try:
                    xmi_content = plantuml_to_xmi(plantuml_code)
                    if st.download_button(
                        label=tr("download_xmi_button"),
                        data=xmi_content,
                        file_name=f"diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                        mime="application/xml"
                    ):
                        st.success(tr("msg_success_ready_for_downloading_XMI"))
                except Exception as e:
                    st.error(tr("msg_error_generating_xmi").format(error=str(e)))
            else:
                st.button(tr("download_xmi_button"), disabled=True, help=tr("download_xmi_button_help"))

# XML download option
if st.session_state.latest_xml:
    st.header(tr("download_xml_header"))
    with st.expander(tr("show_xml_button")):
        st.code(st.session_state.latest_xml, language="xml")
    
    if st.download_button(
        label=tr("download_xml_button"),
        data=st.session_state.latest_xml,
        file_name=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
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
        st.code(plantuml_code, language="plantuml",height=500)
                
        if st.button(tr("close_plantuml_button"), type="primary"):
            st.session_state.show_plantuml_code = False
            st.rerun()
    
   # Show modal and handle closing
    result = show_plantuml_modal()
    
    # If dialog was closed by X button, reset the state
    if result is None:
        st.session_state.show_plantuml_code = False


