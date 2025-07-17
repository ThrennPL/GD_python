
import subprocess
import sys
import re
import requests
import traceback
import os
from PyQt5.QtGui import QTextCharFormat, QColor, QFont
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSplitter, QTextEdit, QPushButton, QWidget, QDialog, QLabel, QTabWidget, QComboBox, QCheckBox, QLabel, QGroupBox, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup, QMessageBox, QFileDialog, QMenu
from PyQt5.QtSvg import QSvgWidget
from xml.etree.ElementTree import fromstring, ParseError
from datetime import datetime
from zlib import compress

from dotenv import load_dotenv

load_dotenv()

try:
    #from plantuml_to_ea import plantuml_to_xmi
    from extract_code_from_response import extract_xml, extract_plantuml, extract_plantuml_blocks, is_valid_xml
    from xml_highlighter import XMLHighlighter
    from input_validator import validate_input_text
    from api_thread import APICallThread
    from plantuml_utils import plantuml_encode, identify_plantuml_diagram_type, fetch_plantuml_svg_local, fetch_plantuml_svg_www
    from logger_utils import setup_logger, log_info, log_error, log_exception
    from translations_pl import TRANSLATIONS as PL
    from translations_en import TRANSLATIONS as EN
    from plantuml_sequance_parser import PlantUMLSequenceParser
    from xmi_sequance_generator import XMISequenceGenerator
    from plantuml_class_parser import PlantUMLClassParser
    from xmi_class_generator import XMIClassGenerator
except ImportError as e:
    MODULES_LOADED = False
    print(f"Error importing modules: {e}")
    sys.exit(1)

setup_logger("main_app.log")
# Load environment variables

plantuml_jar_path = os.getenv("PLANTUML_JAR_PATH", "plantuml.jar")
plantuml_generator_type = os.getenv("PLANTUML_GENERATOR_TYPE", "local")
DB_PROVIDER = os.getenv("DB_PROVIDER", "")
CHAT_URL = os.getenv("CHAT_URL", "http://localhost:1234//v1/chat/completions")
API_KEY = os.getenv("API_KEY", "")
API_DEFAULT_MODEL = os.getenv("API_DEFAULT_MODEL", "models/gemini-2.0-flash")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "gemini")  # lub "gemini"

LANG = "pl"  # Domyślny język, można zmienić na "pl" dla polskiego

def tr(key):
    return EN[key] if LANG == "en" else PL[key]

if LANG == "en":
    from prompt_templates_en import prompt_templates, get_diagram_specific_requirements
else:
    from prompt_templates_pl import prompt_templates, get_diagram_specific_requirements

class AIApp(QMainWindow):
    API_URL = os.getenv("API_URL", "http://localhost:1234//v1/models")
    XML_BLOCK_PATTERN = r"```xml\n(.*?)\n```"
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("setWindowTitle"))
        self.setGeometry(100, 100, 1200, 1000)
        self.verification_attempts = 0
        self.last_prompt_type = None 
        self.prompt_templates = prompt_templates  # Załaduj szablony z pliku

        # Grupa dla szablonu
        template_group = QGroupBox(tr("template_group"))
        template_layout = QHBoxLayout()

        # ComboBox do wyboru modelu
        self.model_selector = QComboBox(self)
        self.model_selector.setToolTip(tr("model_selector.setToolTip"))
        self.model_selector.addItem("Loading models...")  # Placeholder na czas ładowania
        self.load_models()  # Załaduj modele przy starcie

        # indeks zakładki -> kod PlantUML
        self.plantuml_codes = {}  

        # Inicjalizacja listy modeli
        self.models = []

        # Layout główny
        main_layout = QVBoxLayout()

        # Widżety
        self.input_box = QTextEdit(self)
        self.input_box.setToolTip(tr("input_box.setToolTip"))
        self.output_box = QTextEdit(self)
        self.output_box.setToolTip(tr("output_box.setToolTip"))
        self.output_box.setReadOnly(True)
        self.output_box.setAcceptRichText(True)  # Umożliwia kolorowanie tekstu
        self.output_box.setStyleSheet("background-color: #f0f0f0;")  # Ustawienie koloru tła
        self.output_box.setMinimumHeight(200)

        # Radiobuttony do wyboru typu szablonu
        self.radio_plantuml = QRadioButton("PlantUML")
        self.radio_xml = QRadioButton("XML")
        self.radio_plantuml.setChecked(True)  # domyślnie PlantUML

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_plantuml)
        radio_layout.addWidget(self.radio_xml)
        template_layout.addLayout(radio_layout)

        self.template_type_group = QButtonGroup(self)
        self.template_type_group.addButton(self.radio_plantuml)
        self.template_type_group.addButton(self.radio_xml)

        self.radio_plantuml.toggled.connect(self.update_template_selector)
        self.radio_xml.toggled.connect(self.update_template_selector)

        self.template_selector = QComboBox(self)
        self.template_selector.setToolTip(tr("template_selector.setToolTip"))
        self.template_selector.addItems(list(self.prompt_templates.keys()))

        template_layout.addWidget(QLabel(tr("template_selector")))
        template_layout.addWidget(self.template_selector)
        template_group.setStyleSheet("background-color: #f0ffff;")

        # Dodanie ComboBox do wyboru typu diagramu
        self.diagram_type_selector = QComboBox(self)
        self.diagram_type_selector.setToolTip(tr("diagram_type_selector.setToolTip"))
        self.diagram_type_selector.addItems([
            "sequence", "activity", "usecase", "class", "state", "flowchart",
            "communication", "component", "deployment", "timing", "collaboration"
        ])
        
        template_layout.addWidget(QLabel(tr("template_layout.select_label")))
        template_layout.addWidget(self.diagram_type_selector)

        self.template_selector.currentIndexChanged.connect(self.on_template_changed)
        self.on_template_changed(self.template_selector.currentIndex())  # Ustaw początkowo

        self.update_template_selector()

        self.use_template_checkbox = QCheckBox(tr("use_template_checkboxuse_template_checkbox"), self)
        self.use_template_checkbox.setChecked(True)  # domyślnie zaznaczony
        self.use_template_checkbox.stateChanged.connect(self.on_use_template_checkbox_changed)
        # Ustaw stan początkowy
        self.on_use_template_checkbox_changed(self.use_template_checkbox.checkState())

        template_layout.addWidget(self.use_template_checkbox)
        
        template_group.setLayout(template_layout)

        # Layout główny
        left_layout = QVBoxLayout()

        # 1. Etykieta i wybór modelu (dodaj na górze)
        left_layout.addWidget(QLabel(tr("model_selector")))
        left_layout.addWidget(self.model_selector)

        # 2. Grupa dla szablonu (jak dotychczas)
        left_layout.addWidget(template_group)

        # Przycisk "Wyślij zapytanie"
        self.send_button = QPushButton(tr("send_button"))

        # Przycisk "Zapisz XML"
        self.save_xml_button = QPushButton(tr("save_xml_button"))
        self.save_xml_button.setEnabled(False)  # Domyślnie nieaktywny

        # Przycisk "Edytuj PlantUML"
        self.edit_plantuml_button = QPushButton(tr("edit_plantuml_button"))
        self.edit_plantuml_button.setEnabled(False)  
        # Przycisk "Zapisz PlantUML"
        self.save_PlantUML_button = QPushButton(tr("save_plantuml_button"))
        self.save_PlantUML_button.setEnabled(False)  

        self.save_xmi_button = QPushButton(tr("save_xmi_button"))
        self.save_xmi_button.setEnabled(False)

        # Przycisk "Zapisz diagram" - w formie graficznej
        self.save_diagram_button = QPushButton(tr("save_diagram_button"))
        self.save_diagram_button.setEnabled(False)

        self.validate_input_button = QPushButton(tr("validate_input_button"), self)

        # 3. Output box (okno konwersacji)
        left_layout.addWidget(QLabel(tr("output_box")))
        left_layout.addWidget(self.output_box)

        # 4. Input box (opis procesu)
        left_layout.addWidget(QLabel(tr("input_box")))
        left_layout.addWidget(self.input_box)
        self.input_box.setFixedHeight(100)

        # 5. Przyciski pod input_box
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.validate_input_button)
        buttons_layout.addWidget(self.send_button)
        buttons_layout.addWidget(self.save_xml_button)
        buttons_layout.addWidget(self.edit_plantuml_button)
        buttons_layout.addWidget(self.save_PlantUML_button)
        buttons_layout.addWidget(self.save_xmi_button)
        buttons_layout.addWidget(self.save_diagram_button)
        left_layout.addLayout(buttons_layout)

        # --- PRAWA KOLUMNA: zakładki z diagramami ---
        self.diagram_tabs = QTabWidget(self)
        self.diagram_tabs.setTabsClosable(True)
        self.diagram_tabs.tabCloseRequested.connect(self.close_plantuml_tab)
        self.diagram_tabs.currentChanged.connect(self.on_tab_changed)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(950)

        main_layout = QHBoxLayout()
        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.diagram_tabs, stretch=2)

        # Central Widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.validate_input_button.clicked.connect(self.validate_input_button_pressed)
        self.save_xmi_button.clicked.connect(self.save_xmi)
        self.save_diagram_button.clicked.connect(self.save_active_diagram)

        # Eventy dla przycisków
        self.send_button.clicked.connect(self.send_to_api)
        self.save_xml_button.clicked.connect(self.save_xml)
        self.save_PlantUML_button.clicked.connect(self.save_plantuml)
        self.edit_plantuml_button.clicked.connect(self.edit_plantuml)

        # Historia rozmowy
        self.conversation_history = []

        # Połącz sygnał zmiany zakładki z tą metodą
        self.diagram_tabs.currentChanged.connect(self.on_tab_changed)


    def close_plantuml_tab(self, idx):
        self.diagram_tabs.removeTab(idx)
        if idx in self.plantuml_codes:
            del self.plantuml_codes[idx]

    def validate_input_button_pressed(self):
        """Sprawdza poprawność tekstu z input_box."""
        validate_input_text(self, self.diagram_type_selector.currentText(), LANG=LANG)

    def update_template_selector(self):
        selected_type = "PlantUML" if self.radio_plantuml.isChecked() else "XML"
        self.template_selector.blockSignals(True)
        self.template_selector.clear()
        filtered = [
            name for name, data in self.prompt_templates.items()
            if data.get("type") == selected_type
        ]
        self.template_selector.addItems(filtered)
        self.template_selector.blockSignals(False)
        self.on_template_changed(self.template_selector.currentIndex())

    
    def on_tab_changed(self, index):
        # Pobierz typ diagramu z aktualnej zakładki (np. z atrybutu lub tekstu)
        current_diagram_type = self.get_current_diagram_type(index)
        if ("klas" or "sekwencji") in current_diagram_type.lower():
            self.save_xmi_button.setEnabled(True)
        else:
            self.save_xmi_button.setEnabled(False)

    def get_current_diagram_type(self, index):
        # Pobierz tytuł zakładki
        tab_text = self.diagram_tabs.tabText(index)
        # Możesz tu dodać własną logikę, np. analizę tekstu lub atrybutów
        return tab_text

    def on_template_changed(self, index):
        selected_template = self.template_selector.currentText()
        allowed_types = self.prompt_templates[selected_template]["allowed_diagram_types"]
        all_types = [
            "sequence", "activity", "use case", "class", "state",
            "communication", "component", "deployment", "timing", "collaboration"
        ]
        self.diagram_type_selector.blockSignals(True)
        self.diagram_type_selector.clear()
        if allowed_types == "all":
            self.diagram_type_selector.addItems(all_types)
        else:
            self.diagram_type_selector.addItems(allowed_types)
        self.diagram_type_selector.blockSignals(False)

    def get_templates_for_diagram_type(diagram_type):
        return [
            name for name, data in prompt_templates.items()
            if data["allowed_diagram_types"] == "all" or diagram_type in data["allowed_diagram_types"]
        ]

    def show_raw_response(self, text):
        """Wyświetla czystą odpowiedź w oknie dialogowym."""
        msg = QMessageBox(self)
        msg.setWindowTitle(tr("msg_setWindowTitle"))
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg.setText(text)
        msg.exec_()

    def load_models(self):
        """Ładuje listę modeli z API do ComboBox."""
        models = self.get_loaded_models()
        self.model_selector.clear()  # Wyczyść ComboBox
        if models:
            for model in models:
                model_id = model.get("id", "unknown")
                self.model_selector.addItem(model_id)
        else:
            self.model_selector.addItem("No models available")
        self.model_selector.setCurrentText(API_DEFAULT_MODEL)  # Ustaw domyślny model
    
    def get_loaded_models(self):
        """Pobiera listę modeli z API, obsługuje OpenAI i Gemini."""
        #MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "gemini")
        log_info(tr("msf_info_model_provider").format(MODEL_PROVIDER=MODEL_PROVIDER))
        try:
            if MODEL_PROVIDER == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=API_KEY)
                models = genai.list_models()
                # Filtrowanie tylko modeli obsługujących generateContent
                models_data = [
                    {"id": m.name, "description": getattr(m, "description", ""), "supported": m.supported_generation_methods}
                    for m in models if "generateContent" in getattr(m, "supported_generation_methods", [])
                ]
                self.models = models_data
                log_info(f"Loaded Gemini models: {len(models_data)} models found.")
                return models_data
            else:
                response = requests.get(self.API_URL, headers={"Authorization": f"Bearer {API_KEY}"} if API_KEY else {"Content-Type": "application/json"})
                log_info(f"Request to {self.API_URL} returned status code {response.status_code}")
                if response.status_code == 200:
                    log_info(f"Response from {self.API_URL}: {response.text[:5000]}...")
                    models_data = response.json().get("data", [])
                    self.models = models_data
                    log_info(f"Loaded models: {len(models_data)} models found.")
                    return models_data
                else:
                    error_msg = tr("error_fetch_models").format(status_code=response.status_code, text=response.text)
                    log_error(error_msg)
                    return None
        except Exception as e:
            error_msg = tr("error_fetch_models_exception").format(error=e)
            log_exception(error_msg)
            return None

    def start_api_thread(self, prompt, model_name=None):
        self.prompt_text = prompt

        if model_name is None:
            model_name = self.model_selector.currentText()
        try:
            url = CHAT_URL
            headers = {"Content-Type": "application/json","Authorization": f"Bearer {API_KEY}"} if API_KEY else {"Content-Type": "application/json"}
            messages = [{"role": "user", "content": prompt}]
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.7
            }
            self.api_thread = APICallThread(url, headers, payload, model_name, MODEL_PROVIDER)
            self.api_thread.response_received.connect(self.handle_api_response)
            self.api_thread.error_occurred.connect(self.handle_api_error)
            self.api_thread.start()
            log_info(f"Starting API thread for model {model_name} with prompt: {prompt[:100]}...")
        except Exception as e:
            error_msg = tr("error_sending_request").format(model_name=model_name, error=e)
            log_exception(error_msg)
            self.output_box.setText(error_msg)
            self.send_button.setEnabled(True)
            return
            
    def generate_bpmn_prompt(self, process_description, complexity, validation, output_format, domain):
            selected_template = self.template_selector.currentText()
            template_data = self.prompt_templates[selected_template]
            if selected_template == tr("bpmn_template_bank"):
                process_description=process_description
                template = template_data[tr("bpmn_template_bank")]
                return 
            
            elif selected_template == tr("bpmn_template_advanced"):
                process_description=process_description
                template = template_data[tr("bpmn_template_advanced")]
            else:
                template = template_data[tr("bpmn_template_basic")]

            return template.format(
                process_description=process_description,
                complexity=complexity,
                validation=validation,
                output_format=output_format
            )

    def send_to_api(self):
        """Wysyła zapytanie do API bez blokowania GUI."""
        diagram_type = self.diagram_type_selector.currentText()
        process_description = self.input_box.toPlainText().strip()
        use_template = self.use_template_checkbox.isChecked()

        self.output_box.append(tr("msg_info_waiting_for_model_response"))
        self.waiting_timer = QTimer()
        self.waiting_dots = 0

        def update_waiting_animation():
            self.waiting_dots = (self.waiting_dots % 4) + 1
            cursor = self.output_box.textCursor()
            cursor.movePosition(cursor.End)
            cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor)
            cursor.removeSelectedText()
            cursor.setCharFormat(QTextCharFormat())
            format = QTextCharFormat()
            format.setForeground(QColor("blue"))
            format.setFontWeight(QFont.Bold)
            cursor.setCharFormat(format)
            cursor.insertText(f"{tr("msg_info_waiting_for_model_response")}{'.' * self.waiting_dots}")
        self.waiting_timer.timeout.connect(update_waiting_animation)
        self.waiting_timer.start(500)  # Aktualizuj co 500 ms
        
        selected_template = self.template_selector.currentText()
        template_data = self.prompt_templates[selected_template]
        if diagram_type.lower() in ["bpmn", "bpmn_flow", "bpmn_component"]:
            # Pobierz dodatkowe parametry z GUI lub ustaw domyślne
            complexity = self.get_complexity_level()      # np. "medium"
            validation = self.get_validation_rule()       # np. "syntax"
            output_format = self.get_output_format()      # np. "clean"
            domain = self.get_domain()                    # np. None lub "bankowość"
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
                prompt = template_data["template"].format(
                process_description = process_description + tr("bpmn_bank_details").format(
                    complexity=complexity,
                    validation=validation,
                    output_format=output_format
                ),
                domain=domain,
                )
            else:
                prompt = process_description


        elif use_template:
            prompt = template_data["template"].format(
                diagram_type=diagram_type,
                process_description=process_description,
                diagram_specific_requirements=get_diagram_specific_requirements(diagram_type)
            )
        else:
            prompt = process_description

        self.send_button.setEnabled(False)
        if not process_description:
            self.output_box.setText(tr("error_sending_request_empty"))
            self.send_button.setEnabled(True)
            return

        # Dodaj wiadomość użytkownika do historii rozmowy
        self.conversation_history.append({"role": "user", "content": prompt})
        self.append_to_chat("User", prompt)
        self.input_box.clear()

        # Uruchom wątek API z gotowym promptem i wybranym modelem
        selected_model = self.model_selector.currentText()
        self.start_api_thread(prompt, selected_model)

    def get_complexity_level(self):
        """Zwraca poziom złożoności wybrany przez użytkownika."""
        complexity = {
            "simple": "Podstawowe elementy, linearny przepływ",
            "medium": "Bramki decyzyjne, podstawowa obsługa błędów",
            "complex": "Sub-procesy, pełna obsługa wyjątków",
            "enterprise": "Pełny governance, monitoring, integracje"
        }
        selected_level = "medium"  # Domyślnie "medium"

        # Możesz dodać ComboBox lub RadioButton do GUI, aby użytkownik mógł wybrać poziom złożoności
        return complexity[selected_level]
    
    def get_validation_rule(self):
        """Zwraca regułę walidacji wybraną przez użytkownika."""

        validation = {
            "syntax": "Walidacja XML Schema",
            "semantic": "Logika biznesowa",
            "camunda": "Kompatybilność z Camunda",
            "best_practices": "Najlepsze praktyki BPMN"
        }
        selected_rule = "syntax"  # Domyślnie "syntax"

        # Możesz dodać ComboBox lub RadioButton do GUI, aby użytkownik mógł wybrać poziom złożoności
        return validation[selected_rule]
    
    def get_output_format(self):
        """Zwraca format wyjściowy wybrany przez użytkownika. """

        output_format = {
            "clean": "Tylko XML bez komentarzy",
            "documented": "XML z komentarzami wyjaśniającymi",
            "structured": "XML z dodatkowymi metadanymi"
        }
        selected_forma = "clean"  # Domyślnie "clean"

        # Możesz dodać ComboBox lub RadioButton do GUI, aby użytkownik mógł wybrać poziom złożoności
        return output_format[selected_forma]

    def get_domain(self):
        """Zwraca domenę wybraną przez użytkownika. """
        domain_keys = [
            "NONE",
            "banking",
            "insurance",
            "logistics",
            "healthcare",
            "e-commerce"
        ]
        # Możesz dodać ComboBox lub RadioButton do GUI, aby użytkownik mógł wybrać domenę
        selected_domain = "banking"
        return tr(f"domain_{selected_domain}")
    
    def handle_api_response(self, model_name, response_content):
        """Obsługuje odpowiedź z API."""
        if hasattr(self, "verification_timer") and self.verification_timer.isActive():
            self.verification_timer.stop()
        if hasattr(self, "waiting_timer") and self.waiting_timer.isActive():
            self.waiting_timer.stop()
        
        
        try:
            if DB_PROVIDER == "mysql":
                from mysql_connector import log_ai_interaction
                subprocess.Popen([ sys.executable, 'mysql_connector.py', self.prompt_text, response_content, model_name])    
            elif DB_PROVIDER == "postgres":
                from PostgreSQL_connector import log_ai_interaction
                subprocess.Popen([ sys.executable, 'postgres_connector.py', self.prompt_text, response_content, model_name])

            #log_info(f"AI interaction logged in database successfully for model {model_name}")
        except Exception as e:
            tb = traceback.format_exc()
            log_error(f"Error logging AI interaction: {e}\n{tb}\n")

        self.send_button.setEnabled(True)  # Ponownie aktywuj przycisk
        self.conversation_history.append({"role": "assistant", "content": response_content})
        self.append_to_chat(model_name, response_content)
        self.latest_response = response_content

        # Sprawdzenie, czy odpowiedź zawiera poprawny XML
        xml_content = extract_xml(response_content)
        if xml_content and is_valid_xml(xml_content):
            self.save_xml_button.setEnabled(True)  # Aktywuj przycisk
            self.latest_xml = xml_content  # Zapisz ostatni poprawny XML
        else:
            self.save_xml_button.setEnabled(False)  # Dezaktywuj przycisk

        # Sprawdzenie, czy odpowiedź zawiera blok PlantUML
        plantuml_blocks = extract_plantuml_blocks(response_content)
        if plantuml_blocks:
            self.save_PlantUML_button.setEnabled(True)
            self.edit_plantuml_button.setEnabled(True)
            # Sprawdź typ diagramu
            diagram_type = identify_plantuml_diagram_type(plantuml_blocks[-1], LANG)
            # print(f"Identified diagram type: {diagram_type}")
            if ("klas" or "sekwencji") in diagram_type.strip().lower():
                self.save_xmi_button.setEnabled(True)
            else:
                self.save_xmi_button.setEnabled(False)
            self.latest_plantuml = plantuml_blocks[-1]
            for block in plantuml_blocks:
                self.show_plantuml_diagram(block)
            return

        # Jeśli to była odpowiedź na weryfikację, sprawdź czy model uznał kod za poprawny
        if self.last_prompt_type == "Verification":
            if tr("msg_validation_success") in response_content.lower():
                self.output_box.append(tr("msg_validation_success_message"))
                # zapisz do logu komunikat o poprawności
                log_info(tr("msg_validation_success_message"))
                self.verification_attempts = 0
                return
            # Jeśli nie, spróbuj jeszcze raz (ale show_plantuml_diagram już to obsłuży)
            plantuml_blocks = re.findall(r"```plantuml\n(.*?)\n```", response_content, re.DOTALL)
            if plantuml_blocks:
                self.show_plantuml_diagram(plantuml_blocks[-1])
                # Zapisz do logu komunikat o niepoprawności  
                log_info(tr("msg_validation_failure_continue"))
                
            else:
                error_msg = (tr("msg_validation_failure"))
                self.append_to_chat("System", error_msg)
                log_error(error_msg)

            return

        self.save_PlantUML_button.setEnabled(False)
        self.edit_plantuml_button.setEnabled(False)
        self.latest_plantuml = None


    def handle_api_error(self, error_msg):
        """Obsługuje błędy z API."""
        self.send_button.setEnabled(True)  # Ponownie aktywuj przycisk
        self.append_to_chat("System", error_msg)

    def save_xml(self):
        """Zapisuje ostatni poprawny XML do pliku."""
        xml_content = extract_xml(self.latest_response)
        if xml_content and is_valid_xml(xml_content):
            to_save = xml_content
        else:
            plantuml_code = extract_plantuml(self.latest_response)
            if plantuml_code:
                to_save = bpmn_to_xml(plantuml_code)
            else:
                error_msg = (tr("msg_no_valid_xml"))
                self.append_to_chat("System", error_msg)
                return
        if hasattr(self, "latest_xml") and self.latest_xml:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"output_{timestamp}.xml"
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(self.latest_xml)
                ok_msg = (tr("msg_xml_saved").format(filename=filename))
                self.append_to_chat("System", ok_msg)
                log_info(ok_msg)
            except Exception as e:
                error_msg = (tr("msg_error_saving_xml").format(error=e))
                self.append_to_chat("System", error_msg)
                log_exception(error_msg)
        else:
            error_msg = (tr("msg_no_valid_xml_to_save"))
            self.append_to_chat("System", error_msg)
            log_exception(error_msg)

    def preview_plantuml_diagram(self, plantuml_code):
        """
        Generuje podgląd diagramu PlantUML w nowym oknie na podstawie podanego kodu.
        
        Args:
            plantuml_code (str): Kod PlantUML do wygenerowania podglądu
        """
        try:
            # Usunięcie motywów, które mogą powodować problemy
            plantuml_code = plantuml_code.replace("!theme ocean", "")
            plantuml_code = plantuml_code.replace("!theme grameful", "")
            plantuml_code = plantuml_code.replace("!theme plain", "")
            
            # Generowanie SVG zgodnie z ustawionym typem generatora
            if plantuml_generator_type == "local":
                svg_data, err_msg = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path, LANG)
            elif plantuml_generator_type == "www":
                svg_data, err_msg = fetch_plantuml_svg_www(plantuml_code, LANG)
            
            # Jeśli wystąpił błąd podczas generowania
            if err_msg:
                QMessageBox.warning(self, tr("preview_diagram_error_title"), 
                                tr("msg_error_generating_diagram").format(error=err_msg))
                return
                
            # Tworzenie okna dialogowego do podglądu
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle(tr("preview_diagram_title"))
            preview_dialog.resize(800, 600)
            
            # Dodanie widżetu SVG
            svg_widget = QSvgWidget()
            svg_widget.load(svg_data)
            
            # Layout dla dialogu
            layout = QVBoxLayout(preview_dialog)
            layout.addWidget(svg_widget)
            
            # Przycisk zamknięcia
            close_button = QPushButton(tr("dialog_close_button"), preview_dialog)
            close_button.clicked.connect(preview_dialog.accept)
            
            # Dodanie przycisku do layoutu
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(close_button)
            layout.addLayout(button_layout)
            
            # Wyświetlenie okna dialogowego
            preview_dialog.exec_()
            
        except Exception as e:
            error_msg = tr("msg_error_previewing_diagram").format(error=str(e))
            log_exception(error_msg)
            QMessageBox.warning(self, tr("preview_diagram_error_title"), error_msg)

    def save_edited_plantuml(self, idx, new_code, dialog):
        """
        Zapisuje zmodyfikowany kod PlantUML i aktualizuje diagram w zakładce.
        
        Args:
            idx (int): Indeks zakładki do aktualizacji
            new_code (str): Nowy kod PlantUML
            dialog (QDialog): Okno dialogowe edycji
        """
        try:
            # Usunięcie motywów, które mogą powodować problemy
            new_code = new_code.replace("!theme ocean", "")
            new_code = new_code.replace("!theme grameful", "")
            new_code = new_code.replace("!theme plain", "")
            
            # Sprawdzanie poprawności kodu przez generowanie SVG
            if plantuml_generator_type == "local":
                svg_data, err_msg = fetch_plantuml_svg_local(new_code, plantuml_jar_path, LANG)
            elif plantuml_generator_type == "www":
                svg_data, err_msg = fetch_plantuml_svg_www(new_code, LANG)
            
            # Jeśli wystąpił błąd podczas generowania diagramu
            if err_msg:
                QMessageBox.warning(dialog, tr("edit_plantuml_error_title"), 
                                tr("msg_error_validating_plantuml").format(error=err_msg))
                return  # Nie zamykamy dialogu, aby użytkownik mógł poprawić kod
            
            # Aktualizacja kodu w słowniku
            if idx in self.plantuml_codes:
                self.plantuml_codes[idx] = new_code
                
                # Pobranie aktualnego widgetu
                current_tab = self.diagram_tabs.widget(idx)
                
                # Aktualizacja diagramu
                svg_widget = QSvgWidget()
                svg_widget.load(svg_data)
                
                # Aktualizacja zawartości zakładki
                layout = current_tab.layout()
                
                # Usunięcie starego widgetu SVG
                for i in reversed(range(layout.count())):
                    layout.itemAt(i).widget().setParent(None)
                
                # Dodanie nowego widgetu SVG
                layout.addWidget(svg_widget)
                
                # Aktualizacja tytułu zakładki
                diagram_type = identify_plantuml_diagram_type(new_code, LANG)
                self.diagram_tabs.setTabText(idx, diagram_type)
                
                # Zamknięcie dialogu edycji
                dialog.accept()
                
                # Wyświetlenie komunikatu o sukcesie
                ok_msg = tr("msg_info_edited_plantuml_saved").format(diagram_type=diagram_type)
                self.append_to_chat("System", ok_msg)
                log_info(ok_msg)
                
                # Aktualizacja przycisków
                self.save_diagram_button.setEnabled(True)
                if ("klas" in diagram_type.lower()) or ("sekwencji" in diagram_type.lower()):
                    self.save_xmi_button.setEnabled(True)
                else:
                    self.save_xmi_button.setEnabled(False)
            else:
                error_msg = tr("msg_no_valid_edited_plantuml_to_save")
                self.append_to_chat("System", error_msg)
                log_exception(error_msg)
                dialog.reject()
        except Exception as e:
            error_msg = tr("msg_error_updating_plantuml").format(error=str(e))
            log_exception(error_msg)
            QMessageBox.warning(dialog, tr("edit_plantuml_error_title"), error_msg)

    def edit_plantuml(self):
        """Otwiera okno dialogowe do edycji kodu PlantUML."""
        idx = self.diagram_tabs.currentIndex()
        if idx in self.plantuml_codes:
            plantuml_code = self.plantuml_codes[idx]
            dialog = QDialog(self)
            dialog.setWindowTitle(tr("dialog_edit_plantuml_title"))
            layout = QVBoxLayout(dialog)

            # Ustawienie minimalnego rozmiaru dla edytora tekstu
            text_edit = QTextEdit(dialog)
            text_edit.setPlainText(plantuml_code)
            text_edit.setMinimumSize(500, 400)  # Minimum 500x400
            layout.addWidget(text_edit)
            
            save_button = QPushButton(tr("dialog_save_button"), dialog)
            preview_button = QPushButton(tr("dialog_preview_button"), dialog)
            cancel_button = QPushButton(tr("dialog_cancel_button"), dialog)
            
            if text_edit.textChanged:
                save_button.setEnabled(True)
                preview_button.setEnabled(True)
            else:
                save_button.setEnabled(False)
                preview_button.setEnabled(False)
                
            cancel_button.clicked.connect(dialog.reject)
            preview_button.clicked.connect(lambda: self.preview_plantuml_diagram(text_edit.toPlainText()))
            save_button.clicked.connect(lambda: self.save_edited_plantuml(idx, text_edit.toPlainText(), dialog))
            
            # Poziomy layout dla przycisków w jednej linii
            button_layout = QHBoxLayout()
            button_layout.addStretch()  # Elastyczna przestrzeń po lewej
            button_layout.addWidget(preview_button)
            button_layout.addWidget(save_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)  # Dodaj layout przycisków do głównego layoutu

            # Ustawienie minimalnego rozmiaru dla całego dialogu
            dialog.setMinimumSize(550, 500)
            
            dialog.exec_()
        else:
            error_msg = tr("msg_no_valid_plantuml_to_edit")
            self.append_to_chat("System", error_msg)
            log_exception(error_msg)

    def save_plantuml(self):
        """Zapisuje kod PlantUML z aktywnej zakładki do pliku."""
        idx = self.diagram_tabs.currentIndex()
        if idx in self.plantuml_codes:
            try:
                code = self.plantuml_codes[idx]
                diagram_type = identify_plantuml_diagram_type(code, LANG)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = f"{diagram_type.replace(' ', '_')}_{timestamp}.puml"
                
                # Otwórz okno dialogowe do wyboru pliku
                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    tr("dialog_save_plantuml_title"),  # Tytuł okna
                    default_filename,  # Domyślna nazwa pliku
                    "PlantUML Files (*.puml);;All Files (*)"  # Filtr plików
                )
                
                # Jeśli użytkownik anulował dialog, filename będzie pusty
                if not filename:
                    return
                
                # Zapisz plik
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(code)
                
                ok_msg = tr("msg_plantuml_saved").format(diagram_type=diagram_type, filename=filename)
                self.append_to_chat("System", ok_msg)
                log_info(ok_msg)
                
            except Exception as e:
                error_msg = tr("msg_error_saving_plantuml").format(error=e)
                self.append_to_chat("System", error_msg)
                log_exception(error_msg)
        else:
            error_msg = tr("msg_no_valid_plantuml_to_save")
            self.append_to_chat("System", error_msg)
            log_exception(error_msg)

    def save_xmi(self):
        """Zapisuje kod XMI z aktywnej zakładki do pliku."""
        idx = self.diagram_tabs.currentIndex()
        if idx in self.plantuml_codes:
            plantuml_code = self.plantuml_codes[idx]
            diagram_type = identify_plantuml_diagram_type(plantuml_code, LANG)
            try:
                if diagram_type == ('Diagram klas' or 'Class diagram'):
                    #xmi_code = plantuml_to_xmi(plantuml_code)
                    parser = PlantUMLClassParser()
                    parser.parse(plantuml_code)
                    xmi_code = XMIClassGenerator(autor = "195841").save_xmi(parser.classes, parser.relations, parser.enums, 
                                    parser.notes, parser.primitive_types, diagram_name = diagram_type)
                elif diagram_type == ('Diagram sekwencji' or 'Sequence diagram'):
                    parser = PlantUMLSequenceParser(plantuml_code)
                    parsed_data = parser.parse()
                    xmi_code =XMISequenceGenerator(autor = "195841").generuj_diagram(
                        nazwa_diagramu=diagram_type,
                        dane=parsed_data  
                    )
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = f"{diagram_type.replace(' ', '_')}_{timestamp}.xmi"
                
                # Otwórz okno dialogowe do wyboru pliku
                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    tr("dialog_save_xmi_title"),  # Tytuł okna
                    default_filename,  # Domyślna nazwa pliku
                    "XMI Files (*.xmi);;All Files (*)"  # Filtr plików
                )
                
                # Jeśli użytkownik anulował dialog, filename będzie pusty
                if not filename:
                    return
                
                # Zapisz plik
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(xmi_code)
                
                ok_msg = tr("msg_xmi_saved").format(filename=filename)
                self.append_to_chat("System", ok_msg)
                log_info(f"XMI saved: {filename}")
                
            except Exception as e:
                tb = traceback.format_exc()
                error_msg = tr("msg_error_saving_xmi").format(error=e, traceback=tb)                
                self.append_to_chat("System", error_msg)
                log_exception(error_msg)
        else:
            error_msg = tr("msg_no_valid_plantuml_to_convert")
            self.append_to_chat("System", error_msg)
            log_exception(error_msg)

    def save_active_diagram(self):
        idx = self.diagram_tabs.currentIndex()
        if idx in self.plantuml_codes:
            plantuml_code = self.plantuml_codes[idx]
            diagram_type = identify_plantuml_diagram_type(plantuml_code, LANG)
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = f"{diagram_type.replace(' ', '_')}_{timestamp}.svg"
                 
                # Otwórz okno dialogowe do wyboru pliku
                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    tr("dialog_save_diagram_title"),  # Tytuł okna
                    default_filename,  # Domyślna nazwa pliku
                    "SVG Files (*.svg);;All Files (*)"  # Filtr plików
                )
                
                # Jeśli użytkownik anulował dialog, filename będzie pusty
                if not filename:
                    return
            
                if plantuml_generator_type == "local":
                    svg_path, error_msg = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path, LANG)
                    with open(svg_path, "r", encoding="utf-8") as f:
                        svg_data = f.read()
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(svg_data)
                elif plantuml_generator_type == "www":
                    svg_data, error_msg = fetch_plantuml_svg_www(plantuml_code, LANG)
                    with open(filename, "wb") as f:
                        f.write(svg_data)
                ok_msg = tr("msg_diagram_saved").format(filename=filename)
                self.append_to_chat("System", ok_msg)
                log_info(ok_msg)
            except Exception as e:
                error_msg = tr("msg_error_saving_diagram").format(error=e)
                self.append_to_chat("System", error_msg)
                log_exception(error_msg)
        else:
            error_msg = tr("msg_no_valid_diagram_to_save")
            self.append_to_chat("System", error_msg)
            log_exception(error_msg)

    def append_to_chat(self, sender: str, message: str):
        """
        Dodaje wiadomość do historii rozmowy z kolorowaniem nazw, pogrubieniem tekstu między **...**,
        zachowaniem nowych linii oraz zamianą * na początku linii na punktator.
        Fragmenty XML (```xml ... ```) są wyświetlane jako tekst (z kolorowaniem składni).
        """
        xml_blocks = re.findall(self.XML_BLOCK_PATTERN, message, re.DOTALL)
        message_for_format = re.sub(self.XML_BLOCK_PATTERN, "___XML_BLOCK___", message, flags=re.DOTALL)
        message_html = self.format_message_html(message_for_format)

        cursor = self.output_box.textCursor()
        cursor.movePosition(cursor.End)

        sender_format = QTextCharFormat()
        sender_format.setForeground(self.get_sender_color(sender))
        sender_format.setFontWeight(QFont.Bold)
        cursor.insertText(f"{sender}: ", sender_format)

        self.output_box.setTextCursor(cursor)

        parts = message_html.split("___XML_BLOCK___")
        for i, part in enumerate(parts):
            if part:
                self.output_box.insertHtml(part)
            if i < len(xml_blocks):
                self.output_box.insertPlainText('\n' + xml_blocks[i] + '\n')

        self.output_box.insertHtml("<br>")
        self.output_box.setTextCursor(self.output_box.textCursor())
        self.output_box.ensureCursorVisible()


    def get_sender_color(self, sender: str) -> QColor:
        if sender == "User":
            return QColor("green")
        elif any(model['id'] == sender for model in self.models):
            return QColor("blue")
        return QColor("gray")

    def format_message_html(self, message: str) -> str:
        # Zamień < i > na encje HTML, żeby nie znikały znaczniki XML
        message = message.replace('<', '&lt;').replace('>', '&gt;')
        def bold_replacer(match):
            return f"<b>{match.group(1)}</b>"
        html = re.sub(r"\*\*(.*?)\*\*", bold_replacer, message)
        html = re.sub(r"(^|\n)\*(\s*)", r"\1•\2", html)
        # Zamiana pojedynczych backticków na <code>
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
        # Zamiana pojedynczych cudzysłowów na <code>
        html = re.sub(r"'([^']+)'", r"<code>\1</code>", html)
        html = html.replace('\n', '<br>')
        return html
    
    def display_models(self):
        """Wyświetla listę załadowanych modeli w oknie output_box."""
        models = self.get_loaded_models()
        if models:
            self.output_box.append("Loaded models:\n")
            for model in models:
                model_id = model.get("id", "unknown")
                model_owner = model.get("owned_by", "unknown")
                self.output_box.append(f"- {model_id} (Owned by: {model_owner})\n")

        else:
            self.output_box.append("Failed to fetch models.")

    def show_xml_file(self, filepath):
        """Wczytuje i prezentuje plik XML z kolorowaniem składni."""
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                xml_content = file.read()
            # Ładujemy jako zwykły tekst, highlighter zadziała automatycznie
            self.output_box.setPlainText(xml_content)
        except Exception as e:
            error_msg = tr("msg_error_loading_xml").format(error=e)
            self.append_to_chat("System", error_msg)
            

    def close_plantuml_tab(self, idx):
        self.diagram_tabs.removeTab(idx)
        if idx in self.plantuml_codes:
            del self.plantuml_codes[idx]

    def show_plantuml_diagram(self, plantuml_code):
        err_msg = ""
        try:
            plantuml_code = plantuml_code.replace("!theme ocean", "")
            plantuml_code = plantuml_code.replace("!theme grameful", "")
            plantuml_code = plantuml_code.replace("!theme plain", "")
            if plantuml_generator_type == "local":
                svg_data, err_msg = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path, LANG)
                print(f"svg_data: {svg_data}" if svg_data else f"svg_data: {err_msg}" if err_msg else f"svg_data: {svg_data}")
            elif plantuml_generator_type == "www":
                svg_data, err_msg = fetch_plantuml_svg_www(plantuml_code, LANG)
                print(f"svg_data: {svg_data}" if svg_data else f"svg_data: {err_msg}" if err_msg else f"svg_data: {svg_data}")
            svg_widget = QSvgWidget()
            svg_widget.load(svg_data)
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(svg_widget)
            tab.setLayout(layout)
            # Nazwa zakładki na podstawie typu diagramu
            diagram_type = identify_plantuml_diagram_type(plantuml_code, LANG)
            idx = self.diagram_tabs.addTab(tab, diagram_type)
            self.diagram_tabs.setCurrentWidget(tab)
            # Zapisz kod PlantUML dla tej zakładki
            self.plantuml_codes[idx] = plantuml_code
            self.save_diagram_button.setEnabled(True)
            if err_msg is None:
                self.verification_attempts = 0  # Reset liczby prób po sukcesie

            tab.setContextMenuPolicy(Qt.CustomContextMenu)
            def show_context_menu(point):
                menu = QMenu(self)
                action_edit=menu.addAction(tr("edit_plantuml_button"))
                action_plum=menu.addAction(tr("save_plantuml_button"))
                action_svg=menu.addAction(tr("save_diagram_button"))
                #action_test=menu.addAction("test")
                current_diagram_type = self.get_current_diagram_type(idx)
                if ("klas" in current_diagram_type.lower()) or ("sekwencji" in current_diagram_type.lower()):
                    action_xmi=menu.addAction(tr("save_xmi_button"))
                action=menu.exec_(svg_widget.mapToGlobal(point))
                
                if action==action_plum:
                    self.save_plantuml()
                elif action==action_svg:
                    self.save_active_diagram()
                elif (("klas" in current_diagram_type.lower()) or ("sekwencji" in current_diagram_type.lower())) and (action==action_xmi):
                    self.save_xmi()
                elif action==action_edit:
                    self.edit_plantuml()

            tab.customContextMenuRequested.connect(show_context_menu)
        except Exception as e:
            error_msg = tr("msg_error_fetching_plantuml").format(error=e)
            log_exception(error_msg)
            self.append_to_chat("System", error_msg)
        if err_msg != "":
            print(f"Error message: {err_msg}, self.verification_attempts: {self.verification_attempts}, self.last_prompt_type: {self.last_prompt_type}")  
            try:
                line_parts = err_msg.split(':', 1)
                log_info(f"Extracted line parts from error message: {line_parts}")
                if len(line_parts) > 0:
                    line_num_str = line_parts[0].strip()
                    log_info(f"Extracted line number string: {line_num_str}")
                    if line_num_str.isdigit():
                        line_num = int(line_num_str)
                        log_info(f"Parsed line number: {line_num}")
                        pluntuml_lines = plantuml_code.splitlines()
                        log_info(f"Number of lines in PlantUML code: {pluntuml_lines}")
                        if 0 < line_num <= len(pluntuml_lines):
                            problematic_line = pluntuml_lines[line_num - 1].strip()
                        log_info(f"Problematic line extracted: {problematic_line}")
                        err_msg = f"{err_msg}: '{problematic_line}'"
            except Exception as e:
                log_error(f"Error while parsing error message: {e}")

            if self.diagram_type_selector.isEnabled():
                diagram_type = self.diagram_type_selector.currentText()
            else:
                diagram_type = identify_plantuml_diagram_type(plantuml_code)
            # Automatycznie wyślij prompt do weryfikacji kodu
            if self.last_prompt_type == "Verification" and self.verification_attempts >= 2:
                error_msg = tr("msg_verification_attempts_exceeded")
                log_error(error_msg)
                self.append_to_chat("System", error_msg)
                QMessageBox.warning(
                    self, tr("verification_template"),
                    tr("msg_verification_attempts_exceeded")
                    ),
                self.verification_attempts = 0
                return
            self.verification_attempts += 1
            verification_template = self.prompt_templates[tr("verification_template")]["template"]
            prompt = tr("msg_info_verifying_plantuml_code_error_line").format(err_msg=err_msg)  + verification_template.format(plantuml_code=plantuml_code, diagram_type=diagram_type)
            self.output_box.append(tr("msg_info_waiting_for_verification"))
            self.verification_timer = QTimer()
            self.verification_dots = 0
            def update_verification_animation():
                self.verification_dots = (self.verification_dots %4) + 1
                cursor = self.output_box.textCursor()
                cursor.movePosition(cursor.End)
                cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor)
                cursor.removeSelectedText()
                format = QTextCharFormat()
                format.setForeground(QColor("red"))
                format.setFontWeight(QFont.Bold)
                cursor.setCharFormat(format)
                cursor.insertText(tr("msg_info_waiting_for_verification") + "." * self.verification_dots)
            self.verification_timer.timeout.connect(update_verification_animation)
            self.verification_timer.start(500)
                
            self.last_prompt_type = "Verification"

            print(f"Weryfikacja PlantUML: {self.verification_attempts}, {self.last_prompt_type}, {err_msg}")
            error_msg = tr("msg_sending_code_for_verification")
            self.append_to_chat("System", error_msg)
            self.send_to_api_custom_prompt(prompt)

    def send_to_api_custom_prompt(self, prompt):
        self.send_button.setEnabled(False)
        self.start_api_thread(prompt)

    def on_use_template_checkbox_changed(self, state):
        use_template = self.use_template_checkbox.isChecked()
        self.template_selector.setEnabled(use_template)
        self.diagram_type_selector.setEnabled(use_template)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIApp()
    window.show()
    sys.exit(app.exec_())