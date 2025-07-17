import unittest
import sys
import os
import tempfile
import re
from unittest.mock import patch, MagicMock

# Dodaj katalog główny projektu do ścieżki, aby można było importować moduły
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plantuml_utils import (
    tr, 
    plantuml_encode, 
    identify_plantuml_diagram_type,
    fetch_plantuml_svg_www,
    fetch_plantuml_svg_local
)

class TestPlantUMLUtils(unittest.TestCase):
    
    def setUp(self):
        # Przygotowanie przykładowych kodów PlantUML do testów
        self.class_diagram = """
        @startuml
        class User {
            -id: int
            -name: string
            +login(): void
        }
        class Account {
            -balance: decimal
        }
        User -- Account
        @enduml
        """
        
        self.sequence_diagram = """
        @startuml
        actor User
        participant System
        User -> System: login(username, password)
        System --> User: loginResponse
        @enduml
        """
        
        self.activity_diagram = """
        @startuml
        @startactivity
        start
        :Process A;
        if (condition) then
            :Process B;
        else
            :Process C;
        endif
        stop
        @endactivity
        @enduml
        """
        
        self.state_diagram = """
        @startuml
        @startstate
        [*] --> State1
        State1 --> State2
        State2 --> [*]
        @endstate
        @enduml
        """
        
        self.c4_diagram = """
        @startuml
        !include <C4/C4_Container>
        Person(user, "User")
        System(system, "System")
        Rel(user, system, "Uses")
        @enduml
        """

    def test_tr_pl(self):
        """Test funkcji tr dla języka polskiego"""
        # Założenie: klucz 'diagram_type_class_diagram' powinien zwracać 'Diagram klas' w języku polskim
        self.assertEqual(tr('diagram_type_class_diagram', LANG='pl'), 'Diagram klas')
    
    def test_tr_en(self):
        """Test funkcji tr dla języka angielskiego"""
        # Założenie: klucz 'diagram_type_class_diagram' powinien zwracać 'Class diagram' w języku angielskim
        self.assertEqual(tr('diagram_type_class_diagram', LANG='en'), 'Class diagram')
    
    def test_identify_class_diagram(self):
        """Test identyfikacji diagramu klas"""
        diagram_type = identify_plantuml_diagram_type(self.class_diagram, LANG='pl')
        self.assertEqual(diagram_type, 'Diagram klas')
        
        # Test w języku angielskim
        diagram_type_en = identify_plantuml_diagram_type(self.class_diagram, LANG='en')
        self.assertEqual(diagram_type_en, 'Class diagram')
    
    def test_identify_sequence_diagram(self):
        """Test identyfikacji diagramu sekwencji"""
        diagram_type = identify_plantuml_diagram_type(self.sequence_diagram, LANG='pl')
        self.assertEqual(diagram_type, 'Diagram sekwencji')
    
    def test_identify_activity_diagram(self):
        """Test identyfikacji diagramu aktywności"""
        diagram_type = identify_plantuml_diagram_type(self.activity_diagram, LANG='pl')
        self.assertEqual(diagram_type, 'Diagram aktywności')
    
    def test_identify_state_diagram(self):
        """Test identyfikacji diagramu stanów"""
        diagram_type = identify_plantuml_diagram_type(self.state_diagram, LANG='pl')
        self.assertEqual(diagram_type, 'Diagram stanów')
    
    def test_identify_c4_diagram(self):
        """Test identyfikacji diagramu C4"""
        diagram_type = identify_plantuml_diagram_type(self.c4_diagram, LANG='pl')
        self.assertEqual(diagram_type, 'Diagram komponentów')
    
    def test_identify_empty_diagram(self):
        """Test identyfikacji pustego diagramu"""
        diagram_type = identify_plantuml_diagram_type("", LANG='pl')
        self.assertEqual(diagram_type, 'Diagram ogólny (typ nieokreślony)')

    def test_plantuml_encode(self):
        """Test kodowania tekstu PlantUML do formatu URL"""
        # Prosty test kodowania
        simple_diagram = "@startuml\nA->B\n@enduml"
        encoded = plantuml_encode(simple_diagram)
        
        # Sprawdź, czy wynik nie jest pusty
        self.assertTrue(encoded)
        self.assertTrue(len(encoded) > 0)
        
        # Dodatkowa diagnostyka - wypisz pierwsze kilka znaków
        print(f"Pierwsze znaki zakodowanego diagramu: {encoded[:20]}")
    
    @patch('requests.get')
    def test_fetch_plantuml_svg_www_success(self, mock_get):
        """Test pobierania SVG z serwisu plantuml.com - przypadek sukcesu"""
        # Przygotuj mocka dla odpowiedzi HTTP
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<svg>Test SVG Content</svg>'
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        # Wywołaj funkcję
        svg_content, error_msg = fetch_plantuml_svg_www('@startuml\nA->B\n@enduml')
        
        # Sprawdź wyniki
        self.assertEqual(svg_content, b'<svg>Test SVG Content</svg>')
        self.assertEqual(error_msg, '')
    
    @patch('requests.get')
    def test_fetch_plantuml_svg_www_error(self, mock_get):
        """Test pobierania SVG z serwisu plantuml.com - przypadek błędu"""
        # Przygotuj mocka dla odpowiedzi HTTP z błędem
        mock_response = MagicMock()
        mock_response.status_code = 200  # Status 200, ale z błędem w nagłówkach
        mock_response.content = b'Error content'
        mock_response.headers = {
            'X-PlantUML-Diagram-Error-Line': '2',
            'X-PlantUML-Diagram-Error': 'Syntax Error',
            'X-PlantUML-Diagram-Description': 'Invalid syntax'
        }
        mock_get.return_value = mock_response
        
        # Wywołaj funkcję
        svg_content, error_msg = fetch_plantuml_svg_www('@startuml\nA->B\n@enduml')
        
        # Sprawdź, czy error_msg zawiera informacje o błędzie
        self.assertIn('3: Syntax Error : Invalid syntax', error_msg)  # Line 2 + 1
    
    @patch('subprocess.run')
    def test_fetch_plantuml_svg_local_success(self, mock_run):
        """Test generowania SVG lokalnie - przypadek sukcesu"""
        # Przygotuj mocka dla wyniku subprocess.run
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = b''
        mock_process.stderr = b''
        mock_run.return_value = mock_process
        
        # Wywołaj funkcję
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path, error_msg = fetch_plantuml_svg_local(
                '@startuml\nA->B\n@enduml',
                'plantuml.jar'
            )
            
            # Sprawdź wyniki
            self.assertTrue(os.path.exists(os.path.dirname(svg_path)))
            self.assertEqual(error_msg, '')
    
    @patch('subprocess.run')
    def test_fetch_plantuml_svg_local_error(self, mock_run):
        """Test generowania SVG lokalnie - przypadek błędu"""
        # Przygotuj mocka dla wyniku subprocess.run z błędem
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = b'Stdout error message'
        mock_process.stderr = b'Error: Invalid syntax'
        mock_run.return_value = mock_process
        
        # Wywołaj funkcję
        svg_path, error_msg = fetch_plantuml_svg_local(
            '@startuml\nA->B\n@enduml',
            'plantuml.jar'
        )
        
        # Sprawdź, czy error_msg zawiera informacje o błędzie
        self.assertEqual(error_msg, 'Error: Invalid syntax')

if __name__ == '__main__':
    unittest.main()