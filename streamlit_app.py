import streamlit as st
import requests
import re
from datetime import datetime
import traceback
import base64
from io import BytesIO
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import custom modules with error handling
try:
    from extract_code_from_response import extract_xml, extract_plantuml, extract_plantuml_blocks, is_valid_xml
    from input_validator import validate_input_text
    from plantuml_utils import plantuml_encode, identify_plantuml_diagram_type, fetch_plantuml_svg_local, fetch_plantuml_svg_www
    from prompt_templates import prompt_templates, get_diagram_specific_requirements
    from logger_utils import setup_logger, log_info, log_error, log_exception
    from plantuml_to_ea import plantuml_to_xmi
    MODULES_LOADED = True
except ImportError as e:
    MODULES_LOADED = False
    st.error(f"Błąd importu modułów: {e}")
    st.stop()

# Configuration - Load from environment variables
try:
    setup_logger()
except Exception as e:
    st.warning(f"Logger setup failed: {e}")

# Load configuration from .env file
plantuml_jar_path = os.getenv("PLANTUML_JAR_PATH", "plantuml.jar")
plantuml_generator_type = os.getenv("PLANTUML_GENERATOR_TYPE", "local")
API_URL = os.getenv("API_URL", "http://localhost:1234/v1/models")
CHAT_URL = os.getenv("CHAT_URL", "http://localhost:1234/v1/chat/completions")
API_KEY = os.getenv("API_KEY", "")
API_DEFAULT_MODEL = os.getenv("API_DEFAULT_MODEL", "")

# Page configuration
st.set_page_config(
    page_title="Generator diagramów AI",
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
    """Pobiera listę załadowanych modeli z API."""
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
            error_msg = f"Błąd podczas pobierania modeli: {response.status_code}, {response.text}"
            safe_log_error(error_msg)
            return None
    except Exception as e:
        error_msg = f"Wystąpił błąd podczas pobierania listy modeli: {e}"
        safe_log_exception(error_msg)
        return None

def call_api(prompt, model_name):
    """Wywołuje API z podanym promptem i modelem."""
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
        safe_log_exception(f"Connection error: {e}")    
        return f"Błąd połączenia: {str(e)}"

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
    """Zwraca domenę."""
    domains = {
        "NONE": "Brak domeny",
        "bankowość": "Domena bankowa",
        "ubezpieczenia": "Domena ubezpieczeń",
        "logistyka": "Domena logistyki",
        "zdrowie": "Domena ochrony zdrowia",
        "e-commerce": "Domena e-commerce"
    }
    return domains.get(domain, domains["bankowość"])

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
                safe_log_info(f"Kod Plant UML z promptu (display): {plantuml_code}")
                svg_data = fetch_plantuml_svg_www(plantuml_code)
                
            else:
                st.error("Nie ma kodu do wyświetlenia")
                safe_log_error("Nie ma kodu do wyświetlenia: {plantuml_code}")
            
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
            svg_path = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path)
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
        st.error(f"Nie udało się wyświetlić diagramu: {e}")
        safe_log_exception(f"Nie udało się wyświetlić diagramu: {e}")
        return False

@st.dialog(f"Kod PlantUML", width="large")
def show_plantuml_modal():
    st.markdown("**Kod PlantUML:**")
    st.code(plantuml_code, language="plantuml")
            
    col1, col2 = st.columns(2)
    with col1:
        if st.download_button(
            label="Pobierz plik",
            data=plantuml_code,
            file_name=f"{diagram_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.puml",
            mime="text/plain"
        ):
            st.success("Plik został pobrany!")
    
    with col2:
        if st.button("Zamknij", type="primary"):
            #st.session_state.show_plantuml_code = False
            st.rerun()

# Load models
if not st.session_state.models:
    with st.spinner("Ładowanie modeli..."):
        models = get_loaded_models()
        if models:
            st.session_state.models = models

# Main UI
st.title("Generator diagramów AI")
st.markdown("Aplikacja do generowania diagramów PlantUML i XML przy użyciu modeli AI")

# Sidebar configuration
with st.sidebar:
    st.header("Konfiguracja")
    
    # Model selection
    if st.session_state.models:
        model_names = [model.get("id", "unknown") for model in st.session_state.models]
        selected_model = st.selectbox("Wybierz model AI:", model_names, 
                                      index = 0 if API_DEFAULT_MODEL not in model_names else model_names.index(API_DEFAULT_MODEL))
    else:
        st.error("Nie udało się załadować modeli")
        selected_model = None
    
    st.divider()
    
    # Template configuration
    st.subheader("Szablon zapytania")
    template_type = st.radio("Typ szablonu:", ["PlantUML", "XML"])
    
    # Filter templates by type
    filtered_templates = [
        name for name, data in prompt_templates.items()
        if data.get("type") == template_type
    ]
    
    selected_template = st.selectbox("Wybierz szablon:", filtered_templates)
    
    use_template = st.checkbox("Użyj szablonu do wiadomości", value=True)
    
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
        
        diagram_type = st.selectbox("Wybierz typ diagramu:", diagram_types)
    else:
        diagram_type = st.selectbox("Wybierz typ diagramu:", [
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
                            ["NONE", "bankowość", "ubezpieczenia", "logistyka", "zdrowie", "e-commerce"])

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Opis procesu")
    process_description = st.text_area(
        "Wprowadź opis procesu:",
        height=150,
        placeholder="Opisz proces, który chcesz przekształcić w diagram..."
    )
    
    # Validation button
    if st.button("Sprawdź poprawność opisu"):
        info_msg = f"Sprawdzanie poprawności opisu procesu: {process_description[:100]}..."
        safe_log_info(info_msg) 
        if process_description:
            
            # Simulate validation (you can implement actual validation logic)
            info_msg = ("**Przekazano opis procesu do weryfikacji**\n")
            st.spinner({"role": "System", "content": info_msg})
            safe_log_info("Przekazano opis procesu do weryfikacji") 
            # Pobierz tekst z input_box
            if not process_description:
                st.session_state.conversation_history.append({"role": "System", "content":"Brak tekstu do walidacji.\n\n"})
                    
            # Pobierz szablon walidacji (np. "Weryfikacja opisu procesu")
            template_data = prompt_templates.get("Weryfikacja opisu procesu")
            if not template_data:
                st.session_state.conversation_history.append({"role": "System", "content": "Brak szablonu do weryfikacji opisu procesu.\n\n"})
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

            with st.spinner("Sprawdzanie poprawności opisu procesu..."):
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
                st.success("Opis procesu wygląda poprawnie!")
        else:
            st.warning("Wprowadź opis procesu do walidacji")
    
    # Send query button
    if st.button("Wyślij zapytanie", type="primary"):
        if not process_description:
            st.error("Nie wysyłaj pustego zapytania.")
        elif not selected_model:
            st.error("Wybierz model AI.")
        else:
            with st.spinner("Generowanie odpowiedzi..."):
                # Prepare prompt
                if use_template and selected_template in prompt_templates:
                    template_data = prompt_templates[selected_template]
                    
                    if diagram_type.lower() in ["bpmn", "bpmn_flow", "bpmn_component"]:
                        if selected_template == "BPMN - podstawowy":
                            prompt = template_data["template"].format(
                                diagram_type=diagram_type,
                                process_description=process_description,
                                diagram_specific_requirements=get_diagram_specific_requirements(diagram_type)
                            )
                        elif selected_template == "BPMN - zaawansowany":
                            prompt = template_data["template"].format(
                                diagram_type=diagram_type,
                                process_description=process_description,
                                diagram_specific_requirements=get_diagram_specific_requirements(diagram_type)
                            )
                        elif selected_template == "BPMN - domena bankowa":
                            complexity = get_complexity_level(complexity_level)
                            validation = get_validation_rule(validation_rule)
                            output_fmt = get_output_format(output_format)
                            domain_desc = get_domain(domain)
                            
                            prompt = template_data["template"].format(
                                process_description=process_description + f"\n Zaawansowane elementy: {complexity}\n Walidacja: {validation}\n Format wyjściowy: {output_fmt}",
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
    st.header("Odpowiedź modelu")
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
    st.header("Wygenerowane diagramy")
    
    # Create tabs for each diagram
    if len(st.session_state.plantuml_diagrams) > 1:
#        tabs = st.tabs([f"{identify_plantuml_diagram_type(st.session_state.plantuml_diagrams[i+1])}" for i in range(len(st.session_state.plantuml_diagrams))])
        tabs = st.tabs([f"{identify_plantuml_diagram_type(p)}" for p in st.session_state.plantuml_diagrams])        
        for i, (tab, plantuml_code) in enumerate(zip(tabs, st.session_state.plantuml_diagrams)):
            with tab:

                st.subheader(f"Diagram {i+1}")
                diagram_type_identified = identify_plantuml_diagram_type(plantuml_code)
                st.subheader(f"Typ diagramu: {diagram_type_identified}")
                diagrams = st.session_state.plantuml_diagrams
                with st.expander(f"Diagram {i+1}"):
                    if plantuml_code is not None:
                        if not display_plantuml_diagram(plantuml_code):
                            # Weryfikacja kodu w przypadku błędów
                            diagram_type = identify_plantuml_diagram_type(plantuml_code)
                            safe_log_info(f"Kod Plant UML z promptu: {plantuml_code}")
                            verification_template = prompt_templates["Weryfikacja kodu PlantUML"]["template"]
                            prompt = verification_template.format(plantuml_code=plantuml_code, diagram_type=diagram_type)
                            safe_log_info(f"Prompt for verification: {prompt}") 
                            st.info("Wysyłam kod do weryfikacji: ")
                            response = call_api(prompt, selected_model)
                            safe_log_info(f"Response from API (Weryfikacje): {response[:5000]}...")  # Loguj pierwsze 5000 znaków odpowiedzi
                            # wyciągniecie kodu PlantUML z odpowiedzi modelu
                            plantuml_code = extract_plantuml(response)
                            plantuml_code = plantuml_code.replace("!theme ocean", "")
                            plantuml_code = plantuml_code.replace("!theme grameful", "")
                            safe_log_info(f"Kod Plant UML po wycięciu !theme ocean: {plantuml_code}")
                            if not display_plantuml_diagram(plantuml_code):
                                st.error("Nie udało się pobrać diagramu PlantUML.")
                                st.stop()
                            else:   
                                #st.session_state.plantuml_diagrams[i] = plantuml_code
                                if plantuml_code is not None:
                                    display_plantuml_diagram(plantuml_code)
                                else:
                                    st.error("Nie ma kodu do wyświetlenia")
                # Download buttons
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                with col1:
                    if st.button("Kod PlantUML", key=f"show_code_{i}"):
                        st.session_state.show_plantuml_code = True
                        st.session_state.selected_diagram_index = i
                    
                with col2:
                    if st.download_button(
                        label="Pobierz PlantUML",
                        data=plantuml_code,
                        file_name=f"diagram_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.puml",
                        mime="text/plain"
                    ):
                        st.success("Plik PlantUML został przygotowany do pobrania!")
                
                with col3:
                    try:
                        if plantuml_generator_type == "www":
                            svg_data = fetch_plantuml_svg_www(plantuml_code)
                             
                        else:
                            svg_path = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path)
                            with open(svg_path, "rb") as f:
                                svg_data = f.read()

                        if st.download_button(
                            label="Pobierz SVG",
                            data=svg_data,
                            file_name=f"diagram_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                            mime="image/svg+xml"
                        ):
                            st.success("Plik SVG został przygotowany do pobrania!")
                    except Exception as e:
                        log_error(f"Błąd podczas przygotowania SVG: {e}")
                        st.error(f"Błąd podczas przygotowania SVG: {e}")
                
                with col4:
                    if "klas" in diagram_type_identified.lower():
                        try:
                            xmi_content = plantuml_to_xmi(plantuml_code)
                            if st.download_button(
                                label="Pobierz XMI",
                                data=xmi_content,
                                file_name=f"diagram_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                                mime="application/xml"
                            ):
                                st.success("Plik XMI został przygotowany do pobrania!")
                        except Exception as e:
                            st.error(f"Błąd podczas generowania XMI: {e}"),
                            safe_log_error(f"Błąd podczas generowania XMI: {e}")
                    #else:
                        #st.button(f"Pobierz XMI {i+1}", disabled=True, help="XMI dostępne tylko dla diagramów klas", key=f"xmi_button_{i}")
    else:
        # Single diagram
        plantuml_code = st.session_state.plantuml_diagrams[0]
        diagram_type_identified = identify_plantuml_diagram_type(plantuml_code)
        st.subheader(f"Typ diagramu: {diagram_type_identified}")
        if not display_plantuml_diagram(plantuml_code):
            # Weryfikacja kodu w przypadku błędów
            safe_log_info(f"Kod Plant UML z promptu (Weryfikacje pojedyńcze): {plantuml_code}")
            diagram_type = identify_plantuml_diagram_type(plantuml_code)
            verification_template = prompt_templates["Weryfikacja kodu PlantUML"]["template"]
            prompt = verification_template.format(plantuml_code=plantuml_code, diagram_type=diagram_type)
            safe_log_info(f"Prompt for verification (Weryfikacje pojedyńcze): {prompt}") 
            st.info("Wysyłam kod do weryfikacji")
            response = call_api(prompt, selected_model)
            safe_log_info(f"Response from API (Weryfikacje pojedyńcze): {response[:5000]}...")  # Loguj pierwsze 5000 znaków odpowiedzi
            # wyciągniecie kodu PlantUML z odpowiedzi modelu
            plantuml_code = extract_plantuml(response)
            plantuml_code = plantuml_code.replace("!theme ocean", "")
            plantuml_code = plantuml_code.replace("!theme grameful", "")
            safe_log_info(f"Kod Plant UML po wycięciu !theme ocean: {plantuml_code}")
            if not display_plantuml_diagram(plantuml_code):
                st.error("Nie udało się pobrać diagramu PlantUML.")
                st.stop()
            else:   
                # st.session_state.plantuml_diagrams[i] = plantuml_code
                if plantuml_code is not None:
                    display_plantuml_diagram(plantuml_code)
                else:
                    st.error("Nie ma kodu do wyświetlenia")  
                
        #display_plantuml_diagram(plantuml_code)
        # Download buttons
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            if st.button("Kod PlantUML"):
                st.session_state.show_plantuml_code = True
                st.session_state.selected_diagram_index = 0  # Single diagram, index 0
            
        with col2:
            if st.download_button(
                label="Pobierz PlantUML",
                data=plantuml_code,
                file_name=f"diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.puml",
                mime="text/plain"
            ):
                st.success("Plik PlantUML został przygotowany do pobrania!")
        
        with col3:
            try:
                if plantuml_generator_type == "www":
                    svg_data = fetch_plantuml_svg_www(plantuml_code)
                else:
                    svg_path = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path)
                    with open(svg_path, "rb") as f:
                        svg_data = f.read()
                
                if st.download_button(
                    label="Pobierz SVG",
                    data=svg_data,
                    file_name=f"diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                    mime="image/svg+xml"
                ):
                    st.success("Plik SVG został przygotowany do pobrania!")
            except Exception as e:
                st.error(f"Błąd podczas przygotowania SVG: {e}")
        
        with col4:
            if "klas" in diagram_type_identified.lower():
                try:
                    xmi_content = plantuml_to_xmi(plantuml_code)
                    if st.download_button(
                        label="Pobierz XMI",
                        data=xmi_content,
                        file_name=f"diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmi",
                        mime="application/xml"
                    ):
                        st.success("Plik XMI został przygotowany do pobrania!")
                except Exception as e:
                    st.error(f"Błąd podczas generowania XMI: {e}")
            else:
                st.button("Pobierz XMI", disabled=True, help="XMI dostępne tylko dla diagramów klas")

# XML download option
if st.session_state.latest_xml:
    st.header("Wygenerowany XML")
    with st.expander("Pokaż XML"):
        st.code(st.session_state.latest_xml, language="xml")
    
    if st.download_button(
        label="Pobierz XML",
        data=st.session_state.latest_xml,
        file_name=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
        mime="application/xml"
    ):
        st.success("Plik XML został przygotowany do pobrania!")

# Modal window for PlantUML code
if st.session_state.show_plantuml_code and st.session_state.plantuml_diagrams:
    # Get the selected diagram index (default to 0 if not set)
    selected_index = st.session_state.get('selected_diagram_index', 0)
    if selected_index < len(st.session_state.plantuml_diagrams):
        plantuml_code = st.session_state.plantuml_diagrams[selected_index]
        diagram_type = identify_plantuml_diagram_type(plantuml_code)
    else:
        plantuml_code = st.session_state.plantuml_diagrams[0]
        diagram_type = identify_plantuml_diagram_type(plantuml_code)
    
    @st.dialog(f"Kod PlantUML - {diagram_type}", width="large")
    def show_plantuml_modal():
        st.code(plantuml_code, language="plantuml",height=500)
                
        if st.button("Zamknij", type="primary"):
            st.session_state.show_plantuml_code = False
            st.rerun()
    
   # Show modal and handle closing
    result = show_plantuml_modal()
    
    # If dialog was closed by X button, reset the state
    if result is None:
        st.session_state.show_plantuml_code = False


