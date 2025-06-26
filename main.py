from plantuml_to_ea import plantuml_to_xmi
from extract_code_from_response import extract_xml, extract_plantuml, extract_plantuml_blocks, is_valid_xml
from xml_highlighter import XMLHighlighter
from input_validator import validate_input_text
from api_thread import APICallThread
from plantuml_utils import plantuml_encode, identify_plantuml_diagram_type, fetch_plantuml_svg_local, fetch_plantuml_svg_www
from prompt_templates import prompt_templates, get_diagram_specific_requirements
from logger_utils import setup_logger, log_info, log_error, log_exception
import sys
import re
import requests
from PyQt5.QtGui import QTextCharFormat, QColor, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSplitter, QTextEdit, QPushButton, QWidget, QDialog, QLabel, QTabWidget, QComboBox, QCheckBox, QLabel, QGroupBox, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup, QMessageBox
from PyQt5.QtSvg import QSvgWidget
from xml.etree.ElementTree import fromstring, ParseError
#import plantuml_encoder
from datetime import datetime
from zlib import compress
import traceback

setup_logger()
plantuml_jar_path = "plantuml.jar"  # Ścieżka do pliku plantuml.jar
plantuml_generator_type = "www"  # Możliwe wartości: "local" lub "www"

class AIApp(QMainWindow):
    API_URL = "http://localhost:1234/v1/models"
    XML_BLOCK_PATTERN = r"```xml\n(.*?)\n```"
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generator diagramów AI")
        self.setGeometry(100, 100, 1200, 1000)
        self.verification_attempts = 0
        self.last_prompt_type = None 
        self.prompt_templates = prompt_templates  # Załaduj szablony z pliku

        # Grupa dla szablonu
        template_group = QGroupBox("Konfiguracja szablonu")
        template_layout = QHBoxLayout()

        # ComboBox do wyboru modelu
        self.model_selector = QComboBox(self)
        self.model_selector.setToolTip("Wybierz model AI do użycia.")
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
        self.input_box.setToolTip("Wprowadź opis procesu lub zapytanie do modelu.")
        self.output_box = QTextEdit(self)
        self.output_box.setToolTip("Odpowiedź modelu AI. Możesz tu zobaczyć wygenerowany kod PlantUML.")
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
        self.template_selector.setToolTip("Wybierz szablon zapytania do modelu AI.")
        self.template_selector.addItems(list(self.prompt_templates.keys()))

        template_layout.addWidget(QLabel("Wybierz szablon zapytania:"))
        template_layout.addWidget(self.template_selector)
        template_group.setStyleSheet("background-color: #f0ffff;")

        # Dodanie ComboBox do wyboru typu diagramu
        self.diagram_type_selector = QComboBox(self)
        self.diagram_type_selector.setToolTip("Wybierz typ diagramu do wygenerowania.")
        self.diagram_type_selector.addItems([
            "sequence", "activity", "usecase", "class", "state", "flowchart",
            "communication", "component", "deployment", "timing", "collaboration"
        ])
        
        template_layout.addWidget(QLabel("Wybierz typ diagramu:"))
        template_layout.addWidget(self.diagram_type_selector)

        self.template_selector.currentIndexChanged.connect(self.on_template_changed)
        self.on_template_changed(self.template_selector.currentIndex())  # Ustaw początkowo

        self.update_template_selector()

        self.use_template_checkbox = QCheckBox("Użyj szablonu do wiadomości", self)
        self.use_template_checkbox.setChecked(True)  # domyślnie zaznaczony
        self.use_template_checkbox.stateChanged.connect(self.on_use_template_checkbox_changed)
        # Ustaw stan początkowy
        self.on_use_template_checkbox_changed(self.use_template_checkbox.checkState())

        template_layout.addWidget(self.use_template_checkbox)
        
        template_group.setLayout(template_layout)

        # Layout główny
        left_layout = QVBoxLayout()

        # 1. Etykieta i wybór modelu (dodaj na górze)
        left_layout.addWidget(QLabel("Wybierz model AI:"))
        left_layout.addWidget(self.model_selector)

        # 2. Grupa dla szablonu (jak dotychczas)
        left_layout.addWidget(template_group)

        # Przycisk "Wyślij zapytanie"
        self.send_button = QPushButton("Wyślij zapytanie")

        # Przycisk "Zapisz XML"
        self.save_xml_button = QPushButton("Zapisz XML")
        self.save_xml_button.setEnabled(False)  # Domyślnie nieaktywny

        # Przycisk "Zapisz PlantUML"
        self.save_PlantUML_button = QPushButton("Zapisz PlantUML")
        self.save_PlantUML_button.setEnabled(False)  # Domyślnie nieaktywny

        self.save_xmi_button = QPushButton("Zapisz XMI")
        self.save_xmi_button.setEnabled(False)

        # Przycisk "Zapisz diagram" - w formie graficznej
        self.save_diagram_button = QPushButton("Zapisz diagram")
        self.save_diagram_button.setEnabled(False)

        self.validate_input_button = QPushButton("Sprawdź poprawność opisu procesu", self)

        # 3. Output box (okno konwersacji)
        left_layout.addWidget(QLabel("Okno konwersacji:"))
        left_layout.addWidget(self.output_box)

        # 4. Input box (opis procesu)
        left_layout.addWidget(QLabel("Wprowadź opis procesu:"))
        left_layout.addWidget(self.input_box)
        self.input_box.setFixedHeight(100)

        # 5. Przyciski pod input_box
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.validate_input_button)
        buttons_layout.addWidget(self.send_button)
        buttons_layout.addWidget(self.save_xml_button)
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
        validate_input_text(self, self.diagram_type_selector.currentText())

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
        if "klas" in current_diagram_type.lower():
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
        msg.setWindowTitle("Czysta odpowiedź modelu")
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
    
    def get_loaded_models(self):
        """Pobiera listę załadowanych modeli z API."""
        try:
            response = requests.get(self.API_URL)
            log_info(f"Request to {self.API_URL} returned status code {response.status_code}")

            if response.status_code == 200:
                log_info(f"Response from {self.API_URL}: {response.text[:500]}...")  # Loguj pierwsze 500 znaków odpowiedzi   
                models_data = response.json().get("data", [])
                self.models = models_data
                return models_data
            else:
                error_msg = f"Błąd podczas pobierania modeli: {response.status_code}, {response.text}"
                #print(error_msg)
                log_error(error_msg)
                return None
        except Exception as e:
            error_msg = f"Wystąpił błąd podczas pobierania listy modeli: {e}"
            #print(error_msg)
            log_exception(error_msg)
            return None

    def start_api_thread(self, prompt, model_name=None):
        """
        Uruchamia wątek API z podanym promptem i modelem.
        """
        if model_name is None:
            model_name = self.model_selector.currentText()
        url = "http://localhost:1234/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7
        }
        self.api_thread = APICallThread(url, headers, payload, model_name)
        self.api_thread.response_received.connect(self.handle_api_response)
        self.api_thread.error_occurred.connect(self.handle_api_error)
        self.api_thread.start()

    def generate_bpmn_prompt(self, process_description, complexity, validation, output_format, domain):
            selected_template = self.template_selector.currentText()
            template_data = self.prompt_templates[selected_template]
            if selected_template == "BPMN - domena bankowa":
                process_description=process_description
                return 
            
            elif selected_template == "BPMN - zaawansowany":
                process_description=process_description
                template = template_data["BPMN - zaawansowany"]
            else:
                template = template_data["BPMN - podstawowy"]

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

        selected_template = self.template_selector.currentText()
        template_data = self.prompt_templates[selected_template]
        if diagram_type.lower() in ["bpmn", "bpmn_flow", "bpmn_component"]:
            # Pobierz dodatkowe parametry z GUI lub ustaw domyślne
            complexity = self.get_complexity_level()      # np. "medium"
            validation = self.get_validation_rule()       # np. "syntax"
            output_format = self.get_output_format()      # np. "clean"
            domain = self.get_domain()                    # np. None lub "bankowość"
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
                prompt = template_data["template"].format(
                process_description=process_description + "\n Zaawansowane elementy: " + complexity + "\n Walidacja: " + validation + "\n Format wyjściowy: " + output_format,
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
            self.output_box.setText("Nie wysyłaj pustego zapytania.")
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
        domain = { 
            "NONE": "Brak domeny",
            "bankowość": "Domena bankowa",
            "ubezpieczenia": "Domena ubezpieczeń",
            "logistyka": "Domena logistyki",
            "zdrowie": "Domena ochrony zdrowia",
            "e-commerce": "Domena e-commerce" 
        }
        # Możesz dodać ComboBox lub RadioButton do GUI, aby użytkownik mógł wybrać domenę
        selected_domain = "bankowość"
        # Domyślnie "bankowość"
        return domain[selected_domain]
    
    def handle_api_response(self, model_name, response_content):
        """Obsługuje odpowiedź z API."""
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
            # Sprawdź typ diagramu
            diagram_type = identify_plantuml_diagram_type(plantuml_blocks[-1])
            # print(f"Identified diagram type: {diagram_type}")
            if "klas" in diagram_type.strip().lower():
                self.save_xmi_button.setEnabled(True)
            else:
                self.save_xmi_button.setEnabled(False)
            self.latest_plantuml = plantuml_blocks[-1]
            for block in plantuml_blocks:
                self.show_plantuml_diagram(block)
            return

        # Jeśli to była odpowiedź na weryfikację, sprawdź czy model uznał kod za poprawny
        if self.last_prompt_type == "Verification":
            if "kod jest poprawny" in response_content.lower():
                self.output_box.append("Model uznał kod PlantUML za poprawny. Przerywam dalsze próby.\n")
                # zapisz do logu komunikat o poprawności
                log_info("Model uznał kod PlantUML za poprawny. Przerywam dalsze próby.")
                self.verification_attempts = 0
                return
            # Jeśli nie, spróbuj jeszcze raz (ale show_plantuml_diagram już to obsłuży)
            plantuml_blocks = re.findall(r"```plantuml\n(.*?)\n```", response_content, re.DOTALL)
            if plantuml_blocks:
                self.show_plantuml_diagram(plantuml_blocks[-1])
                # Zapisz do logu komunikat o niepoprawności  
                log_info("Model uznał kod PlantUML za niepoprawny. Próbuję ponownie.")
                
            else:
                error_msg = ("Nie udało się uzyskać poprawionego kodu PlantUML.\n")
                self.append_to_chat("System", error_msg)
                log_error(error_msg)

            return

        self.save_PlantUML_button.setEnabled(False)
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
                error_msg = ("Brak poprawnego XML do zapisania.\n")
                self.append_to_chat("System", error_msg)
                return
        if hasattr(self, "latest_xml") and self.latest_xml:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"output_{timestamp}.xml"
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(self.latest_xml)
                ok_msg = (f"Plik XML został zapisany jako '{filename}'.\n")
                self.append_to_chat("System", ok_msg)
                log_info(f"Plik XML został zapisany jako '{filename}'")
            except Exception as e:
                error_msg = (f"Błąd zapisu pliku XML: {e}\n")
                self.append_to_chat("System", error_msg)
                log_exception(error_msg)
        else:
            error_msg = ("Brak poprawnego pliku XML do zapisania.\n")
            self.append_to_chat("System", error_msg)
            log_exception(error_msg)

    def save_plantuml(self):
        """Zapisuje kod PlantUML z aktywnej zakładki do pliku."""
        idx = self.diagram_tabs.currentIndex()
        if idx in self.plantuml_codes:
            try:
                code = self.plantuml_codes[idx]
                diagram_type = identify_plantuml_diagram_type(code)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"output_{timestamp}.puml"
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(code)
                ok_msg = (f"Plik PlantUML ({diagram_type}) został zapisany jako '{filename}'.\n")
                self.append_to_chat("System", ok_msg)
                log_info(f"Plik PlantUML ({diagram_type}) został zapisany jako '{filename}'.")
            except Exception as e:
                error_msg = (f"Błąd zapisu pliku PlantUML: {e}\n")
                self.append_to_chat("System", error_msg)
                log_exception(error_msg)
        else:
            error_msg = ("Brak kodu PlantUML do zapisania dla tej zakładki.\n")
            self.append_to_chat("System", error_msg)
            log_exception(error_msg)

    def save_xmi(self):
        idx = self.diagram_tabs.currentIndex()
        if idx in self.plantuml_codes:
            plantuml_code = self.plantuml_codes[idx]
            try:
                xmi_code = plantuml_to_xmi(plantuml_code)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"output_{timestamp}.xmi"
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(xmi_code)
                ok_msg = (f"Plik XMI został zapisany jako '{filename}'.\n")
                self.append_to_chat("System", ok_msg)
                log_info(f"XMI saved: {filename}")
            except Exception as e:
                tb = traceback.format_exc()
                error_msg = f"Błąd podczas konwersji lub zapisu XMI: {e}\n{tb}"
                self.append_to_chat("System", error_msg)
                log_exception(error_msg)
        else:
            error_msg = "Brak kodu PlantUML do konwersji na XMI.\n"
            self.append_to_chat("System", error_msg)
            log_exception(error_msg)

    def save_active_diagram(self):
        idx = self.diagram_tabs.currentIndex()
        if idx in self.plantuml_codes:
            plantuml_code = self.plantuml_codes[idx]
            diagram_type = identify_plantuml_diagram_type(plantuml_code)
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{diagram_type.replace(' ', '_')}_{timestamp}.svg"
                if plantuml_generator_type == "local":
                    svg_path = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path)
                    with open(svg_path, "r", encoding="utf-8") as f:
                        svg_data = f.read()
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(svg_data)
                elif plantuml_generator_type == "www":
                    svg_data = fetch_plantuml_svg_www(plantuml_code)
                    with open(filename, "wb") as f:
                        f.write(svg_data)
                ok_msg = (f"Diagram zapisany jako '{filename}'.\n")
                self.append_to_chat("System", ok_msg)
                log_info(f"Diagram zapisany jako: {filename}")
            except Exception as e:
                error_msg = (f"Błąd podczas zapisu diagramu: {e}\n")
                self.append_to_chat("System", error_msg)
                log_exception(error_msg)
        else:
            error_msg = ("Brak diagramu do zapisania.\n")
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
            error_msg = (f"Błąd podczas wczytywania pliku XML: {e}")
            self.append_to_chat("System", error_msg)
            

    def close_plantuml_tab(self, idx):
        self.diagram_tabs.removeTab(idx)
        if idx in self.plantuml_codes:
            del self.plantuml_codes[idx]

    def show_plantuml_diagram(self, plantuml_code):
        try:
            if plantuml_generator_type == "local":
                svg_data = fetch_plantuml_svg_local(plantuml_code, plantuml_jar_path)
            elif plantuml_generator_type == "www":
                svg_data = fetch_plantuml_svg_www(plantuml_code)
            # Tworzymy widget do wyświetlania SVG
            svg_widget = QSvgWidget()
            svg_widget.load(svg_data)
            # Tworzymy kontener na SVG (np. QWidget z layoutem)
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(svg_widget)
            tab.setLayout(layout)
            # Nazwa zakładki na podstawie typu diagramu
            diagram_type = identify_plantuml_diagram_type(plantuml_code)
            # print(f"Identified diagram type: {diagram_type}")
            idx = self.diagram_tabs.addTab(tab, diagram_type)
            self.diagram_tabs.setCurrentWidget(tab)
            # Zapisz kod PlantUML dla tej zakładki
            self.plantuml_codes[idx] = plantuml_code
            self.save_diagram_button.setEnabled(True)
            self.verification_attempts = 0  # Reset liczby prób po sukcesie
        except Exception as e:
            error_msg = (f"Nie udało się pobrać diagramu PlantUML: {e}\n")
            log_exception(error_msg)
            self.append_to_chat("System", error_msg)
            if self.diagram_type_selector.isEnabled():
                diagram_type = self.diagram_type_selector.currentText()
            else:
                diagram_type = identify_plantuml_diagram_type(plantuml_code)
            # Automatycznie wyślij prompt do weryfikacji kodu
            if self.last_prompt_type == "Verification" and self.verification_attempts >= 2:
                error_msg = ("Próbowano dwukrotnie zweryfikować kod PlantUML. Przerywam dalsze próby.\n")
                log_error(error_msg)
                self.append_to_chat("System", error_msg)
                QMessageBox.warning(
                    self, "Weryfikacja kodu PlantUML",
                    "Próbowano dwukrotnie zweryfikować kod PlantUML. Przerywam dalsze próby."
                )
                return
            self.verification_attempts += 1
            verification_template = self.prompt_templates["Weryfikacja kodu PlantUML"]["template"]
            prompt = verification_template.format(plantuml_code=plantuml_code, diagram_type=diagram_type)
            self.last_prompt_type = "Verification"
            error_msg = (f"Wysyłam kod do weryfikacji\n")
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