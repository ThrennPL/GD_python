import sys
import re
import requests
import xml.dom.minidom
from PyQt5.QtGui import QTextCharFormat, QSyntaxHighlighter, QColor, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSplitter, QTextEdit, QPushButton, QWidget, QDialog, QLabel, QTabWidget
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QThread, pyqtSignal
from xml.etree.ElementTree import fromstring, ParseError
from PyQt5.QtWidgets import QMessageBox
#import plantuml_encoder
import base64
import string
import zlib
from zlib import compress

plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet   = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = bytes.maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))

def plantuml_encode(plantuml_text):
    """Kompresuje i koduje tekst PlantUML do formatu URL zgodnego z plantuml.com."""
    zlibbed_str = compress(plantuml_text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(b64_to_plantuml).decode('utf-8')


class XMLHighlighter(QSyntaxHighlighter):
    """Klasa definiująca reguły kolorowania składni XML."""
    def __init__(self, document):
        super(XMLHighlighter, self).__init__(document)
        self.highlighting_rules = []

        # Definicje reguł kolorowania
        self.add_highlighting_rule(r"<\?xml.*?\?>", QColor("gray"))  # Deklaracja XML
        self.add_highlighting_rule(r"</?\w+.*?>", QColor("blue"))    # Tag otwierający/zamykający
        self.add_highlighting_rule(r"\".*?\"", QColor("red"))        # Wartości atrybutów
        self.add_highlighting_rule(r"=\s*\".*?\"", QColor("green"))  # Atrybuty

    def add_highlighting_rule(self, pattern, color):
        """Dodaje regułę kolorowania."""
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        text_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((re.compile(pattern), text_format))

    def highlightBlock(self, text):
        """Koloruje blok tekstu."""
        for pattern, text_format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, length = match.span()
                self.setFormat(start, length, text_format)

class APICallThread(QThread):
    response_received = pyqtSignal(str, str)  # Sygnalizuje odebranie odpowiedzi (model, treść)
    error_occurred = pyqtSignal(str)         # Sygnalizuje błąd

    def __init__(self, url, headers, payload, model_name):
        super().__init__()
        self.url = url
        self.headers = headers
        self.payload = payload
        self.model_name = model_name

    def run(self):
        """Wysyła żądanie API i emituje odpowiedź."""
        try:
            response = requests.post(self.url, headers=self.headers, json=self.payload)
            if response.status_code == 200:
                response_content = response.json().get("choices")[0].get("message").get("content", "No response")
                self.response_received.emit(self.model_name, response_content)
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                self.error_occurred.emit(error_msg)
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {e}")

class AIApp(QMainWindow):
    API_URL = "http://192.168.0.115:1234/v1/models"
    XML_BLOCK_PATTERN = r"```xml\n(.*?)\n```"
    

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Client with Conversation Context")
        self.setGeometry(100, 100, 800, 600)

        # indeks zakładki -> kod PlantUML
        self.plantuml_codes = {}  

        # Inicjalizacja listy modeli
        self.models = []

        # Layout główny
        main_layout = QVBoxLayout()

        # Widżety
        self.input_box = QTextEdit(self)
        self.output_box = QTextEdit(self)
        self.output_box.setReadOnly(True)
        self.output_box.setAcceptRichText(True)  # Umożliwia kolorowanie tekstu
        self.output_box.setStyleSheet("background-color: #f0f0f0;")  # Ustawienie koloru tła

        # Splitter do zarządzania proporcjami
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.output_box)
        splitter.addWidget(self.input_box)
        self.input_box.setFixedHeight(100)

        # Dodanie kolorowania składni
        self.highlighter = XMLHighlighter(self.output_box.document())

        # Przycisk "Wyślij zapytanie"
        self.send_button = QPushButton("Wyślij zapytanie")

        # Przycisk "Zapisz XML"
        self.save_xml_button = QPushButton("Zapisz XML")
        self.save_xml_button.setEnabled(False)  # Domyślnie nieaktywny

        # Przycisk "Zapisz PlantUML"
        self.save_PlantUML_button = QPushButton("Zapisz PlantUML")
        self.save_PlantUML_button.setEnabled(False)  # Domyślnie nieaktywny

        # ComboBox do wyboru modelu
        self.model_selector = QComboBox(self)
        self.model_selector.addItem("Loading models...")  # Placeholder na czas ładowania
        self.load_models()  # Załaduj modele przy starcie

        # Dodanie widżetów do layoutu
        main_layout.addWidget(self.model_selector)  # Dodanie ComboBox na górze
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.send_button)
        main_layout.addWidget(self.save_xml_button)  # Dodaj przycisk
        main_layout.addWidget(self.save_PlantUML_button)  # Dodaj przycisk PlantUML

        # Eventy dla przycisków
        self.send_button.clicked.connect(self.send_to_api)
        self.save_xml_button.clicked.connect(self.save_xml)
        self.save_PlantUML_button.clicked.connect(self.save_plantuml)

        # self.fetch_models_button = QPushButton("Fetch Models")
        # self.fetch_models_button.clicked.connect(self.display_models)

        # Central Widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Historia rozmowy
        self.conversation_history = []

        # Dodaj QTabWidget na diagramy PlantUML
        self.diagram_tabs = QTabWidget(self)
        main_layout.addWidget(self.diagram_tabs)
        self.diagram_tabs.setTabsClosable(True)
        self.diagram_tabs.tabCloseRequested.connect(self.close_plantuml_tab)

        def close_plantuml_tab(self, idx):
            self.diagram_tabs.removeTab(idx)
            if idx in self.plantuml_codes:
                del self.plantuml_codes[idx]


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
            if response.status_code == 200:
                models_data = response.json().get("data", [])
                self.models = models_data  # Przypisz listę modeli do self.models
                return models_data
            else:
                print(f"Błąd API: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            print(f"Wystąpił błąd podczas pobierania listy modeli: {e}")
            return None


    def send_to_api(self):
        """Wysyła zapytanie do API bez blokowania GUI."""
        self.send_button.setEnabled(False)  # Dezaktywuj przycisk podczas wysyłania zapytania
        input_text = self.input_box.toPlainText().strip()
        if not input_text:
            self.output_box.setText("Nie wysyłaj pustego zapytania.")
            self.send_button.setEnabled(True)  # Ponownie aktywuj przycisk w przypadku pustego zapytania
            return

        # Dodaj wiadomość użytkownika do historii rozmowy
        self.conversation_history.append({"role": "user", "content": input_text})
        self.append_to_chat("User", input_text)

        # Wyczyszczenie okna zapytania
        self.input_box.clear()

        # Budowanie listy messages
        messages = [{"role": "user", "content": input_text}] if not self.conversation_history[:-1] else self.conversation_history

        selected_model = self.model_selector.currentText()
        url = "http://192.168.0.115:1234/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": 0.7
        }

        # Utwórz i uruchom wątek
        self.api_thread = APICallThread(url, headers, payload, selected_model)
        self.api_thread.response_received.connect(self.handle_api_response)
        self.api_thread.error_occurred.connect(self.handle_api_error)
        self.api_thread.start()

    def handle_api_response(self, model_name, response_content):
        """Obsługuje odpowiedź z API."""
        self.send_button.setEnabled(True)  # Ponownie aktywuj przycisk
        self.conversation_history.append({"role": "assistant", "content": response_content})
        self.append_to_chat(model_name, response_content)

        # Sprawdzenie, czy odpowiedź zawiera poprawny XML
        xml_content = self.extract_xml(response_content)
        if xml_content and self.is_valid_xml(xml_content):
            self.save_xml_button.setEnabled(True)  # Aktywuj przycisk
            self.latest_xml = xml_content  # Zapisz ostatni poprawny XML
        else:
            self.save_xml_button.setEnabled(False)  # Dezaktywuj przycisk

    # Sprawdzenie, czy odpowiedź zawiera jeden lub więcej bloków PlantUML
        plantuml_blocks = re.findall(r"``plantuml\n(.*?)\n``", response_content, re.DOTALL)
        if plantuml_blocks:
            self.save_PlantUML_button.setEnabled(True)
            self.latest_plantuml = plantuml_blocks[-1]  # zapisz ostatni do ewentualnego zapisu
            for block in plantuml_blocks:
                self.show_plantuml_diagram(block)
        else:
            self.save_PlantUML_button.setEnabled(False)
            self.latest_plantuml = None


    def handle_api_error(self, error_msg):
        """Obsługuje błędy z API."""
        self.send_button.setEnabled(True)  # Ponownie aktywuj przycisk
        self.append_to_chat("System", error_msg)

    def extract_xml(self, text):
        """Wyodrębnia treść XML z odpowiedzi."""
        match = re.search(self.XML_BLOCK_PATTERN, text, re.DOTALL)
        return match.group(1) if match else None

    def is_valid_xml(self, text):
        """Sprawdza, czy podany tekst jest poprawnym i kompletnym plikiem XML."""
        try:
            fromstring(text)
            return True
        except ParseError:
            return False

    def save_xml(self):
        """Zapisuje ostatni poprawny XML do pliku."""
        if hasattr(self, "latest_xml") and self.latest_xml:
            try:
                with open("output.xml", "w", encoding="utf-8") as file:
                    file.write(self.latest_xml)
                self.output_box.append("Plik XML został zapisany jako 'output.xml'.\n")
            except Exception as e:
                self.output_box.append(f"Błąd zapisu pliku XML: {e}\n")
        else:
            self.output_box.append("Brak poprawnego pliku XML do zapisania.\n")

    def save_plantuml(self):
        """Zapisuje kod PlantUML z aktywnej zakładki do pliku."""
        idx = self.diagram_tabs.currentIndex()
        if idx in self.plantuml_codes:
            try:
                code = self.plantuml_codes[idx]
                diagram_type = self.identify_plantuml_diagram_type(code)
                with open("output.puml", "w", encoding="utf-8") as file:
                    file.write(code)
                self.output_box.append(f"Plik PlantUML ({diagram_type}) został zapisany jako 'output.puml'.\n")
            except Exception as e:
                self.output_box.append(f"Błąd zapisu pliku PlantUML: {e}\n")
        else:
            self.output_box.append("Brak kodu PlantUML do zapisania dla tej zakładki.\n")

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
            self.output_box.setPlainText(f"Błąd podczas wczytywania pliku XML: {e}")

    def close_plantuml_tab(self, idx):
        self.diagram_tabs.removeTab(idx)
        if idx in self.plantuml_codes:
            del self.plantuml_codes[idx]

    def show_plantuml_diagram(self, plantuml_code):
        encoded = plantuml_encode(plantuml_code)
        url = f"https://www.plantuml.com/plantuml/svg/{encoded}"
        try:
            import requests
            response = requests.get(url)
            if response.status_code == 200:
                svg_data = response.content
                # Tworzymy widget do wyświetlania SVG
                svg_widget = QSvgWidget()
                svg_widget.load(svg_data)
                # Tworzymy kontener na SVG (np. QWidget z layoutem)
                tab = QWidget()
                layout = QVBoxLayout(tab)
                layout.addWidget(svg_widget)
                tab.setLayout(layout)
                # Nazwa zakładki na podstawie typu diagramu
                diagram_type = self.identify_plantuml_diagram_type(plantuml_code)
                idx = self.diagram_tabs.addTab(tab, diagram_type)
                self.diagram_tabs.setCurrentWidget(tab)
                # Zapisz kod PlantUML dla tej zakładki
                self.plantuml_codes[idx] = plantuml_code
            else:
                QMessageBox.warning(self, "Błąd", "Nie udało się pobrać diagramu PlantUML.")
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się pobrać diagramu PlantUML: {e}")

    def identify_plantuml_diagram_type(self, plantuml_code: str) -> str:
        code = plantuml_code.lower()
        if 'state' in code or '-->' in code and 'state' in code:
            return "Diagram stanów"
        if 'actor' in code and '->' in code:
            return "Diagram sekwencji"
        if 'class' in code or 'interface' in code or '--|' in code or '<|--' in code:
            return "Diagram klas"
        if 'usecase' in code:
            return "Diagram przypadków użycia"
        if 'component' in code or 'node' in code:
            return "Diagram komponentów"
        return "Diagram ogólny (typ nieokreślony)"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIApp()
    window.show()
    sys.exit(app.exec_())