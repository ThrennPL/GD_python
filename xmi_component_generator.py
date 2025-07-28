import xml.etree.ElementTree as ET
import xml.dom.minidom
import uuid
from datetime import datetime
import re
import os
from typing import Dict, List, Optional, Tuple
from logger_utils import log_debug, log_info, log_error, log_exception, log_warning, setup_logger
from plantuml_component_parser import PlantUMLComponentParser

setup_logger('xmi_component_generator.log')

class LayoutManager:
    """Klasa zarządzająca layoutem elementów diagramu komponentów."""
    
    def __init__(self, debug_positioning=False):
        self.debug_positioning = debug_positioning
        self.positions = {}  # Pozycje elementów
        self.element_sizes = {}  # Rozmiary elementów
        self.package_stack = []  # Stos pakietów
        self.package_positions = {}  # Pozycje pakietów
        self.current_x = 100  # Początkowa pozycja X
        self.current_y = 100  # Początkowa pozycja Y
        self.max_elements_in_row = 3  # Maksymalna liczba elementów w rzędzie
        self.elements_in_current_row = 0  # Licznik elementów w bieżącym rzędzie
        self.row_height = 0  # Wysokość bieżącego rzędu
        self.package_padding = 40  # Zwiększone wypełnienie pakietu
        self.horizontal_spacing = 30  # Zwiększony odstęp między elementami w poziomie
        self.vertical_spacing = 30  # Zwiększony odstęp między elementami w pionie
        self.elements_per_row = {}  # Słownik przechowujący optyma
        self.package_padding = 40  # Zwiększone wypełnienie pakietu
        self.horizontal_spacing = 30  # Zwiększony odstęp między elementami w poziomie
        self.vertical_spacing = 30  # Zwiększony odstęp między elementami w pionie
        self.elements_per_row = {}  # Słownik przechowujący optymalną liczbę elementów w wierszu dla pakietu
    
    def start_package(self, package_id, package_type, package_name):
        """Rozpoczyna układ pakietu, zapisując jego pozycję początkową."""
        # Zapisz aktualną pozycję dla pakietu
        width, height = self.register_element_size(package_id, package_type, package_name)
        
        # Jeśli jesteśmy wewnątrz innego pakietu, przesuń się trochę
        padding_x = 20 * len(self.package_stack)
        padding_y = 20 * len(self.package_stack)
        
        package_x = self.current_x + padding_x
        package_y = self.current_y + padding_y
        
        # Zapisz pozycję pakietu
        self.package_positions[package_id] = {
            'x': package_x,
            'y': package_y,
            'width': width,
            'height': height,
            'elements': [],
            'inner_packages': [],
            'row_count': 0,  # Licznik wierszy w pakiecie
            'current_row': []  # Elementy w bieżącym wierszu
        }
        
        # Oblicz optymalną liczbę elementów w wierszu
        self.elements_per_row[package_id] = self._calculate_optimal_elements_per_row(width)
        
        # Dodaj pakiet na stos
        self.package_stack.append(package_id)
        
        # Zaktualizuj bieżącą pozycję dla elementów w pakiecie
        self.current_x = package_x + self.package_padding  # Większe wypełnienie wewnętrzne
        self.current_y = package_y + 50  # Zwiększony nagłówek pakietu
        self.elements_in_current_row = 0
        self.row_height = 0
        
        if self.debug_positioning:
            print(f"📦 Rozpoczęto pakiet {package_type} '{package_name}' na pozycji ({package_x}, {package_y})")
            log_debug(f"📦 Rozpoczęto pakiet {package_type} '{package_name}' na pozycji ({package_x}, {package_y})")
        
        return package_x, package_y, width, height
    
    def _calculate_optimal_elements_per_row(self, container_width):
        """Oblicza optymalną liczbę elementów w wierszu na podstawie szerokości kontenera."""
        avg_element_width = 150  # Średnia szerokość elementu
        available_width = container_width - (2 * self.package_padding)
        elements_count = max(1, int(available_width / (avg_element_width + self.horizontal_spacing)))
        return elements_count
    
    def get_position_for_element(self, element_id, element_type, element_name):
        """Zwraca pozycję dla danego elementu, umieszczając go w kolejnym dostępnym miejscu."""
        # Sprawdź, czy już mamy zapisaną pozycję
        if element_id in self.positions:
            return self.positions[element_id]
        
        # Pobierz lub oblicz rozmiary elementu
        if element_id in self.element_sizes:
            width, height = self.element_sizes[element_id]
        else:
            width, height = self.register_element_size(element_id, element_type, element_name)
        
        # Jeśli jesteśmy w pakiecie, użyj jego konfiguracji do układania elementów
        if self.package_stack:
            package_id = self.package_stack[-1]
            package_data = self.package_positions[package_id]
            max_elements = self.elements_per_row.get(package_id, self.max_elements_in_row)
            
            # Sprawdź czy element zmieści się w bieżącym wierszu
            if self.elements_in_current_row >= max_elements:
                # Przejdź do nowego rzędu
                self.current_x = package_data['x'] + self.package_padding
                self.current_y += self.row_height + self.vertical_spacing
                self.elements_in_current_row = 0
                self.row_height = 0
                package_data['row_count'] += 1
                package_data['current_row'] = []
        else:
            # Sprawdź czy element zmieści się w bieżącym rzędzie
            if self.elements_in_current_row >= self.max_elements_in_row:
                # Przejdź do nowego rzędu
                self.current_x = 100  # Lewy margines
                self.current_y += self.row_height + self.vertical_spacing
                self.elements_in_current_row = 0
                self.row_height = 0
        
        # Ustaw pozycję elementu
        left = self.current_x
        top = self.current_y
        right = left + width
        bottom = top + height
        
        # Aktualizuj pozycję dla następnego elementu
        self.current_x += width + self.horizontal_spacing
        self.elements_in_current_row += 1
        self.row_height = max(self.row_height, height)
        
        # Zapisz element w bieżącym pakiecie, jeśli istnieje
        if self.package_stack:
            package_id = self.package_stack[-1]
            self.package_positions[package_id]['elements'].append(element_id)
            self.package_positions[package_id]['current_row'].append(element_id)
        
        # Stwórz i zapisz pozycję
        position = f"Left={left};Top={top};Right={right};Bottom={bottom};"
        self.positions[element_id] = position
        
        if self.debug_positioning:
            pkg_info = f" w pakiecie {self.package_stack[-1][-6:]}" if self.package_stack else ""
            print(f"📍 Umieszczono {element_type} '{element_name}' na pozycji ({left}, {top}){pkg_info}")
            log_debug(f"📍 Umieszczono {element_type} '{element_name}' na pozycji ({left}, {top}){pkg_info}")
        
        return position
    
    def end_package(self):
        """Kończy układ pakietu, dostosowując jego rozmiar do zawartości."""
        if not self.package_stack:
            log_warning("Próba zakończenia pakietu, ale stos pakietów jest pusty")
            return
        
        package_id = self.package_stack.pop()
        package_data = self.package_positions[package_id]
        
        # Oblicz granice pakietu na podstawie położenia jego elementów
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        # Sprawdź wszystkie elementy wewnątrz pakietu
        for element_id in package_data['elements']:
            if element_id in self.positions:
                position = self.positions[element_id]
                match = re.search(r'Left=(\d+\.?\d*);Top=(\d+\.?\d*);Right=(\d+\.?\d*);Bottom=(\d+\.?\d*)', position)
                if match:
                    left = float(match.group(1))
                    top = float(match.group(2))
                    right = float(match.group(3))
                    bottom = float(match.group(4))
                    
                    min_x = min(min_x, left)
                    min_y = min(min_y, top)
                    max_x = max(max_x, right)
                    max_y = max(max_y, bottom)
        
        # Uwzględnij wewnętrzne pakiety
        for inner_pkg_id in package_data['inner_packages']:
            if inner_pkg_id in self.package_positions:
                inner_pkg = self.package_positions[inner_pkg_id]
                min_x = min(min_x, inner_pkg['x'])
                min_y = min(min_y, inner_pkg['y'])
                max_x = max(max_x, inner_pkg['x'] + inner_pkg['width'])
                max_y = max(max_y, inner_pkg['y'] + inner_pkg['height'])
        
        # Jeśli nie ma elementów, użyj minimalnych rozmiarów
        if min_x == float('inf'):
            min_x = package_data['x']
            min_y = package_data['y']
            max_x = package_data['x'] + package_data['width']
            max_y = package_data['y'] + package_data['height']
        
        # Dodaj margines wokół wszystkich elementów
        left = package_data['x']  # Zachowaj oryginalną pozycję X pakietu
        top = package_data['y']   # Zachowaj oryginalną pozycję Y pakietu
        right = max(left + package_data['width'], max_x + self.package_padding)
        bottom = max(top + package_data['height'], max_y + self.package_padding)
        
        # Zaktualizuj rozmiary pakietu
        package_data['width'] = right - left
        package_data['height'] = bottom - top
        
        # Ustaw pozycję pakietu
        self.positions[package_id] = f"Left={left};Top={top};Right={right};Bottom={bottom};"
        
        # Przywróć pozycję do wartości przed wejściem do pakietu
        if self.package_stack:
            parent_id = self.package_stack[-1]
            parent_data = self.package_positions[parent_id]
            self.current_x = parent_data['x'] + self.package_padding
            self.current_y = bottom + self.vertical_spacing  # Umieść następny element pod zakończonym pakietem
            self.elements_in_current_row = 0
            self.row_height = 0
            
            # Dodaj ten pakiet do listy wewnętrznych pakietów rodzica
            parent_data['inner_packages'].append(package_id)
        else:
            # Jeśli wyszliśmy z najwyższego poziomu pakietu, ustaw bieżącą pozycję pod nim
            self.current_x = 100
            self.current_y = bottom + 40
            self.elements_in_current_row = 0
            self.row_height = 0
        
        if self.debug_positioning:
            print(f"📦 Zakończono pakiet {package_id[-6:]} o rozmiarze {package_data['width']}x{package_data['height']}")
            log_debug(f"📦 Zakończono pakiet {package_id[-6:]} o rozmiarze {package_data['width']}x{package_data['height']}")
        
        return left, top, package_data['width'], package_data['height']
    
    def register_element_size(self, element_id, element_type, element_name):
        """Oblicza i rejestruje rozmiary elementu na podstawie jego typu i nazwy."""
        # Standardowe rozmiary dla różnych typów elementów
        default_sizes = {
            'Component': (150, 70),
            'Interface': (130, 60),
            'Package': (450, 320),  # Większe bazowe rozmiary pakietów
            'Boundary': (500, 370),  # Większe bazowe rozmiary granic
            'Note': (200, 100),
            'Actor': (100, 120)
        }
        
        # Oblicz rozmiar na podstawie długości nazwy
        name_length = len(element_name)
        
        # Bazowy rozmiar w zależności od typu elementu
        base_width, base_height = default_sizes.get(element_type, (150, 70))
        
        # Dostosuj szerokość w zależności od długości nazwy
        width = max(base_width, min(base_width + name_length * 8, base_width * 2))
        
        # Dla pakietów - większa szerokość
        if element_type in ['Package', 'Boundary']:
            width = max(450, width)  # Zwiększona minimalna szerokość pakietu
            
            # Dostosuj wysokość pakietu w zależności od typu pakietu
            # (zamiast sprawdzania konkretnych nazw warstw)
            if "layer" in element_name.lower() or "warstwa" in element_name.lower():
                # To jest pakiet warstwy - użyj domyślnej wysokości bazowej
                pass  # Używamy base_height z default_sizes
            elif "module" in element_name.lower() or "moduł" in element_name.lower():
                # Dla modułów - średnia wysokość
                base_height = 250
            elif "domain" in element_name.lower() or "domena" in element_name.lower():
                # Dla domen - większa wysokość
                base_height = 380
            else:
                # Dla pozostałych typów pakietów
                # Dostosuj wysokość na podstawie długości nazwy
                base_height = max(270, min(320, 200 + name_length * 5))
        
        # Zapisz rozmiar elementu
        self.element_sizes[element_id] = (width, base_height)
        
        if self.debug_positioning:
            print(f"📏 Zarejestrowano rozmiar dla {element_type} '{element_name}': {width}x{base_height}")
            log_debug(f"📏 Zarejestrowano rozmiar dla {element_type} '{element_name}': {width}x{base_height}")
        
        return width, base_height

class XMIComponentGenerator:
    """
    Generator XMI dla diagramów komponentów UML/C4.
    Generuje w pełni funkcjonalny diagram komponentów w formacie XMI (dla Enterprise Architect)
    na podstawie danych z parsera PlantUML.
    """
    
    def __init__(self, author: str = "XMI Generator", debug_options: dict = None):
        self.author = author
        # Ustaw domyślne opcje debugowania
        self.debug_options = {
            'positioning': False,     # Debugowanie pozycji elementów
            'elements': False,        # Lista elementów diagramu
            'processing': False,      # Śledzenie przetwarzania elementów
            'relationships': False,   # Szczegóły tworzenia relacji
            'xml': False              # Debugowanie struktury XML
        }
        # Nadpisz domyślne opcje tymi przekazanymi w parametrze
        if debug_options:
            self.debug_options.update(debug_options)
        
        self._reset_state()
        self.ns = {
            'uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi': 'http://schema.omg.org/spec/XMI/2.1'
        }
        self._register_namespaces()
        
    def _reset_state(self):
        """Resetuje stan generatora przed każdym nowym diagramem."""
        self.id_map = {}  # Mapa ID elementów XML
        self.parser_id_to_xmi_id = {}  # Mapa ID parsera do ID XMI
        self.relationships = []  # Lista relacji
        self.diagram_objects = []  # Lista obiektów diagramu
        self.package_id = None  # ID głównego pakietu
        self.diagram_id = None  # ID diagramu
        self.root_package_id = None  # ID pakietu głównego
        self.added_to_diagram = set()
    
    def _register_namespaces(self):
        """Rejestruje przestrzenie nazw XML."""
        ET.register_namespace('xmi', self.ns['xmi'])
        ET.register_namespace('uml', self.ns['uml'])
    
    def _generate_ea_id(self, prefix: str = "EAID") -> str:
        """Generuje unikalny identyfikator w stylu EA."""
        return f"{prefix}_{str(uuid.uuid4()).upper().replace('-', '_')}"
    
    def generate_component_diagram(self, diagram_name: str, parsed_data: dict) -> str:
        """
        Główna metoda generująca całą strukturę XMI dla diagramu komponentów.
        
        Args:
            diagram_name: Nazwa diagramu
            parsed_data: Dane wygenerowane przez parser PlantUML
            
        Returns:
            str: Dokument XMI jako string
        """
        self._reset_state()
        self.parsed_data = parsed_data
        
        # Generowanie unikalnych identyfikatorów dla głównych elementów
        self.diagram_id = self._generate_ea_id("EAID")
        self.package_id = self._generate_ea_id("EAPK")
        
        # Utworzenie podstawowej struktury dokumentu
        root = self._create_document_root()
        model = self._create_uml_model(root)
        package = self._create_diagram_package(model, diagram_name)
        
        # Przetwarzanie elementów diagramu
        self._process_components(package, parsed_data['components'])
        self._process_interfaces(package, parsed_data['interfaces'])
        self._process_packages(package, parsed_data['packages'])
        
        # Przetwarzanie relacji
        self._process_relationships(package, parsed_data['relationships'])
        
        # Przetwarzanie notatek
        self._process_notes(package, parsed_data['notes'])
        
        # Weryfikacja spójności diagramu
        self._verify_diagram_consistency()
        
        # Dodanie rozszerzeń specyficznych dla EA
        self._create_ea_extensions(root, diagram_name)

        # Dodaj odniesienia do stereotypów po utworzeniu wszystkich elementów
        self._add_stereotype_references(root)
        
        # Zwróć sformatowany XML
        return self._format_xml(root)
    
    def _add_stereotype_references(self, root: ET.Element):
        """Dodaje odniesienia stereotypów do komponentów."""
        if not hasattr(self, 'component_stereotypes') or not self.component_stereotypes:
            return
        
        # Utwórz sekcję dla odniesień do stereotypów
        stereotype_refs = ET.SubElement(root, 'stereotypeApplications')
        
        for component_id, stereotype in self.component_stereotypes.items():
            if stereotype == 'service':
                ET.SubElement(stereotype_refs, 'serviceApplication', {
                    'xmi:id': self._generate_ea_id("EAID"),
                    'xmi:type': 'StandardProfileL2:Service',
                    'base_Component': component_id
                })
            elif stereotype == 'repository':
                ET.SubElement(stereotype_refs, 'repositoryApplication', {
                    'xmi:id': self._generate_ea_id("EAID"),
                    'xmi:type': 'SOMF:repository',
                    'base_Class': component_id
                })
            elif stereotype in ['controller', 'gateway', 'utility', 'facade']:
                ET.SubElement(stereotype_refs, f'{stereotype}Application', {
                    'xmi:id': self._generate_ea_id("EAID"),
                    'xmi:type': f'thecustomprofile:{stereotype}',
                    'base_Component': component_id
                })

    def _create_document_root(self) -> ET.Element:
        """Tworzy główny element dokumentu XMI."""
        root = ET.Element(f'{{{self.ns["xmi"]}}}XMI', {'xmi:version': '2.1'})
        
        # Dodaj dokumentację o eksporterze
        ET.SubElement(root, f'{{{self.ns["xmi"]}}}Documentation', {
            'exporter': 'Enterprise Architect',
            'exporterVersion': '6.5', 
            'exporterID': '1560'
        })
        
        return root
    
    def _create_uml_model(self, root: ET.Element) -> ET.Element:
        """Tworzy element modelu UML."""
        return ET.SubElement(root, ET.QName(self.ns['uml'], 'Model'), {
            'xmi:type': 'uml:Model', 'name': 'EA_Model', 'visibility': 'public'
        })
    
    def _create_diagram_package(self, model: ET.Element, diagram_name: str) -> ET.Element:
        """Tworzy główny pakiet diagramu."""
        root_package_id = self._generate_ea_id("EAPK")
        root_package = ET.SubElement(model, 'packagedElement', {
            'xmi:type': 'uml:Package', 
            'xmi:id': root_package_id, 
            'name': diagram_name, 
            'visibility': 'public'
        })
        
        # Dodaj atrybut "ea_localid" kluczowy dla EA
        root_package.set('ea_localid', self._get_local_id(root_package_id))
        
        self.root_package_id = root_package_id
        self.package_id = root_package_id
        
        return root_package
    
    def _process_components(self, parent_element, components):
        """Przetwarza komponenty z parsera PlantUML."""
        # Najpierw grupujemy komponenty według ich pakietów
        components_by_package = {}
        for component_id, component_data in components.items():
            package_id = component_data.get('package')
            if package_id:
                if package_id not in components_by_package:
                    components_by_package[package_id] = []
                components_by_package[package_id].append((component_id, component_data))
        
        # Przetwarzamy komponenty, które nie są przypisane do żadnego pakietu
        for component_id, component_data in components.items():
            component_package = component_data.get('package')
            
            # Tylko przetwarzaj komponenty bez pakietu w tym momencie
            if component_package:
                continue
                
            component_type = component_data.get('type', 'component')
            component_name = component_data.get('name', 'Unnamed')
            c4_type = component_data.get('c4_type', '')
            parser_id = component_data.get('id')
            
            # Utwórz element komponentu
            if component_type == 'c4_element':
                # Specjalna obsługa elementów C4
                xmi_id = self._add_c4_element(parent_element, component_data)
            else:
                # Standardowy komponent UML
                xmi_id = self._add_component(parent_element, component_data)
            
            # Zapisz mapowanie ID
            if parser_id:
                self.parser_id_to_xmi_id[parser_id] = xmi_id
            
            # Dodaj do listy obiektów diagramu
            self.diagram_objects.append({
                'id': xmi_id,
                'type': 'Component',
                'name': component_name,
                'c4_type': c4_type
            })
            
            if self.debug_options.get('processing', False):
                print(f"🔄 Przetworzono komponent '{component_name}' ({component_type})")
                log_debug(f"🔄 Przetworzono komponent '{component_name}' ({component_type})")
        
        # Komponenty w pakietach będą dodawane później w _process_package


    def _add_component(self, parent_element, component_data):
        """Dodaje standardowy komponent UML do modelu."""
        component_id = self._generate_ea_id("EAID")
        component_name = component_data.get('name', 'Unnamed')
        component_alias = component_data.get('alias')
        component_stereotype = component_data.get('stereotype', '')
        
        # Utwórz element komponentu jako bezpośrednie dziecko podanego elementu nadrzędnego
        component = ET.SubElement(parent_element, 'packagedElement', {
            'xmi:type': 'uml:Component',
            'xmi:id': component_id,
            'name': component_name,
            'visibility': 'public'
        })
        
        # Dodaj alias jeśli istnieje
        if component_alias:
            component.set('alias', component_alias)
        
        # Zapisz referencję do ID
        self.id_map[component_id] = component
        
        # Zapisz stereotyp do późniejszego wykorzystania przy tworzeniu profili
        if component_stereotype:
            if not hasattr(self, 'component_stereotypes'):
                self.component_stereotypes = {}
            self.component_stereotypes[component_id] = component_stereotype
        
        return component_id
    
    def _add_c4_element(self, parent_element, component_data):
        """Dodaje element C4 (Person, System, Container, Component) do modelu."""
        c4_id = self._generate_ea_id("EAID")
        c4_name = component_data.get('name', 'Unnamed')
        c4_type = component_data.get('c4_type', '')
        c4_technology = component_data.get('technology', '')
        c4_description = component_data.get('description', '')
        c4_package = component_data.get('package')
        
        # Określ element nadrzędny
        parent = parent_element
        if c4_package and c4_package in self.id_map:
            parent = self.id_map[c4_package]
        
        # Mapuj typ C4 na odpowiedni typ UML
        uml_type = 'uml:Component'  # domyślnie
        if 'person' in c4_type:
            uml_type = 'uml:Actor'
        elif 'system' in c4_type:
            uml_type = 'uml:Component'
        
        # Utwórz element C4
        c4_element = ET.SubElement(parent, 'packagedElement', {
            'xmi:type': uml_type,
            'xmi:id': c4_id,
            'name': c4_name,
            'visibility': 'public'
        })
        
        # Dodaj stereotyp odpowiadający typowi C4
        stereotype = c4_type.replace('_', ' ').title()
        ET.SubElement(c4_element, 'stereotype', {'name': stereotype})
        
        # Dodaj technologię jako taggedValue
        if c4_technology:
            tech_tag = ET.SubElement(c4_element, 'taggedValue', {'name': 'technology'})
            tech_tag.text = c4_technology
        
        # Dodaj opis jako taggedValue
        if c4_description:
            desc_tag = ET.SubElement(c4_element, 'taggedValue', {'name': 'description'})
            desc_tag.text = c4_description
        
        # Zapisz referencję do ID
        self.id_map[c4_id] = c4_element
        
        return c4_id
    
    def _process_interfaces(self, parent_element, interfaces):
        """Przetwarza interfejsy z parsera PlantUML."""
        for interface_id, interface_data in interfaces.items():
            interface_name = interface_data.get('name', 'Unnamed')
            interface_alias = interface_data.get('alias')
            interface_package = interface_data.get('package')
            parser_id = interface_data.get('id')
            
            # Określ element nadrzędny
            parent = parent_element
            if interface_package and interface_package in self.id_map:
                parent = self.id_map[interface_package]
            
            # Utwórz element interfejsu
            xmi_id = self._generate_ea_id("EAID")
            interface = ET.SubElement(parent, 'packagedElement', {
                'xmi:type': 'uml:Interface',
                'xmi:id': xmi_id,
                'name': interface_name,
                'visibility': 'public'
            })
            
            # Dodaj alias jeśli istnieje
            if interface_alias:
                interface.set('alias', interface_alias)
            
            # Zapisz referencję do ID
            self.id_map[xmi_id] = interface
            
            # Zapisz mapowanie ID
            if parser_id:
                self.parser_id_to_xmi_id[parser_id] = xmi_id
            
            # Dodaj do listy obiektów diagramu
            self.diagram_objects.append({
                'id': xmi_id,
                'type': 'Interface',
                'name': interface_name
            })
            
            if self.debug_options.get('processing', False):
                print(f"🔄 Przetworzono interfejs '{interface_name}'")
                log_debug(f"🔄 Przetworzono interfejs '{interface_name}'")
    
    def _process_packages(self, parent_element, packages):
        """Przetwarza pakiety z parsera PlantUML."""
        # Najpierw przetwarzaj pakiety najwyższego poziomu
        top_level_packages = [pkg_id for pkg_id, pkg_data in packages.items() 
                            if not pkg_data.get('parent_package')]
        
        # Przetwórz pakiety najwyższego poziomu
        for pkg_id in top_level_packages:
            self._process_package(parent_element, pkg_id, packages)
            
        # Po przetworzeniu pakietów, dodaj komponenty do ich pakietów
        self._add_components_to_packages()
    
    def _add_components_to_packages(self):
        """Dodaje komponenty do ich odpowiednich pakietów."""
        for component_id, component_data in self.parsed_data['components'].items():
            package_id = component_data.get('package')
            
            # Pomijamy komponenty bez pakietu (zostały już przetworzone wcześniej)
            if not package_id:
                continue
                
            # Pobierz XMI ID pakietu
            package_xmi_id = self.parser_id_to_xmi_id.get(package_id)
            if not package_xmi_id or package_xmi_id not in self.id_map:
                continue
                
            # Pobierz element pakietu
            package_element = self.id_map[package_xmi_id]
            
            component_type = component_data.get('type', 'component')
            component_name = component_data.get('name', 'Unnamed')
            c4_type = component_data.get('c4_type', '')
            parser_id = component_data.get('id')
            
            # Utwórz element komponentu wewnątrz pakietu
            if component_type == 'c4_element':
                xmi_id = self._add_c4_element(package_element, component_data)
            else:
                xmi_id = self._add_component(package_element, component_data)
            
            # Zapisz mapowanie ID
            if parser_id:
                self.parser_id_to_xmi_id[parser_id] = xmi_id
            
            # Dodaj do listy obiektów diagramu
            self.diagram_objects.append({
                'id': xmi_id,
                'type': 'Component',
                'name': component_name,
                'c4_type': c4_type
            })
            
            if self.debug_options.get('processing', False):
                print(f"🔄 Przetworzono komponent '{component_name}' ({component_type}) w pakiecie '{package_element.get('name')}'")
                log_debug(f"🔄 Przetworzono komponent '{component_name}' ({component_type}) w pakiecie '{package_element.get('name')}'")


    def _process_package(self, parent_element, package_id, all_packages):
        """Rekurencyjnie przetwarza pakiet i jego zawartość."""
        package_data = all_packages[package_id]
        package_name = package_data.get('name', 'Unnamed')
        package_alias = package_data.get('alias')
        package_type = package_data.get('type', 'package')
        parser_id = package_data.get('id')
        
        # Utwórz element pakietu
        xmi_id = self._generate_ea_id("EAID")
        
        # Wybierz odpowiedni typ UML w zależności od typu pakietu
        uml_type = 'uml:Package'
        if package_type == 'c4_boundary':
            # C4 Boundary to też pakiet, ale ze stereotypem
            uml_type = 'uml:Package'
            
        package = ET.SubElement(parent_element, 'packagedElement', {
            'xmi:type': uml_type,
            'xmi:id': xmi_id,
            'name': package_name,
            'visibility': 'public'
        })
        
        # Dodaj stereotyp dla granicy C4
        if package_type == 'c4_boundary':
            c4_type = package_data.get('c4_type', 'boundary')
            stereotype = c4_type.replace('_', ' ').title()
            ET.SubElement(package, 'stereotype', {'name': stereotype})
        
        # Dodaj alias jeśli istnieje
        if package_alias:
            package.set('alias', package_alias)
        
        # Zapisz referencję do ID
        self.id_map[xmi_id] = package
        
        # Zapisz mapowanie ID
        if parser_id:
            self.parser_id_to_xmi_id[parser_id] = xmi_id
        
        # Dodaj do listy obiektów diagramu
        self.diagram_objects.append({
            'id': xmi_id,
            'type': 'Package' if package_type == 'package' else 'Boundary',
            'name': package_name,
            'c4_type': package_data.get('c4_type', '')
        })
        
        if self.debug_options.get('processing', False):
            print(f"📦 Przetworzono pakiet '{package_name}' ({package_type})")
            log_debug(f"📦 Przetworzono pakiet '{package_name}' ({package_type})")
        
        # Rekurencyjnie przetwarzaj pakiety-dzieci
        children_packages = [
            child_id for child_id, child_data in all_packages.items()
            if child_data.get('parent_package') == package_id
        ]
        
        for child_id in children_packages:
            self._process_package(package, child_id, all_packages)
    
    def _process_relationships(self, parent_element, relationships):
        """Przetwarza relacje między elementami."""
        # Dodaj pełne debugowanie
        log_debug(f"Rozpoczynam przetwarzanie {len(relationships)} relacji")
        
        # Utwórz mapowania dla aliasów
        alias_to_id = {}
        name_to_id = {}
        
        # Mapowanie dla komponentów
        for comp_id, comp_data in self.parsed_data['components'].items():
            if 'alias' in comp_data and comp_data['alias']:
                alias_to_id[comp_data['alias']] = comp_id
            if 'name' in comp_data and comp_data['name']:
                name_to_id[comp_data['name']] = comp_id
                # Dodaj warianty nazw bez cudzysłowów
                clean_name = comp_data['name'].strip('"[]')
                if clean_name != comp_data['name']:
                    name_to_id[clean_name] = comp_id
        
        # KRYTYCZNA ZMIANA: Dodaj debugowanie mapowań
        log_debug(f"Mapowanie nazw elementów: {name_to_id}")
        log_debug(f"Mapowanie aliasów elementów: {alias_to_id}")
        
        # Przetwarzanie relacji
        for relation in relationships:
            relation_id = relation.get('id')
            relation_type = relation.get('type', 'relationship')
            source_id = None
            target_id = None
            source_xmi_id = None
            target_xmi_id = None
            
            # Pobierz identyfikatory źródła i celu relacji
            source_ref = relation.get('source')
            target_ref = relation.get('target')
            
            # KRYTYCZNA ZMIANA: Dodaj więcej szczegółów do logowania
            log_debug(f"Przetwarzanie relacji: {source_ref} -> {target_ref} (ID: {relation_id})")
            log_debug(f"  Relacja typu: {relation_type}")
            
            # 1. Sprawdź bezpośrednie ID z relacji (POPRAWKA: wyraźnie przypisz source_id/target_id)
            if 'source_id' in relation and relation['source_id']:
                source_id = relation['source_id']
                source_xmi_id = self.parser_id_to_xmi_id.get(source_id)
                log_debug(f"  Bezpośrednie source_id: {source_id} -> xmi_id: {source_xmi_id}")
            
            if 'target_id' in relation and relation['target_id']:
                target_id = relation['target_id']
                target_xmi_id = self.parser_id_to_xmi_id.get(target_id)
                log_debug(f"  Bezpośrednie target_id: {target_id} -> xmi_id: {target_xmi_id}")
            
            # NOWA POPRAWKA: Szukaj dokładnych nazw w surowej postaci
            if not source_id and source_ref in self.parsed_data['components']:
                source_id = source_ref
                source_xmi_id = self.parser_id_to_xmi_id.get(source_id)
                log_debug(f"  Znaleziono source jako bezpośredni ID komponentu: {source_id} -> {source_xmi_id}")
                
            if not target_id and target_ref in self.parsed_data['components']:
                target_id = target_ref
                target_xmi_id = self.parser_id_to_xmi_id.get(target_id)
                log_debug(f"  Znaleziono target jako bezpośredni ID komponentu: {target_id} -> {target_xmi_id}")
            
            # 2. Szukaj przez alias (POPRAWKA: dodaj debugowanie)
            if not source_id and source_ref in alias_to_id:
                source_id = alias_to_id[source_ref]
                source_xmi_id = self.parser_id_to_xmi_id.get(source_id)
                log_debug(f"  Znaleziono source przez alias: {source_ref} -> {source_id} -> xmi_id: {source_xmi_id}")
                
            if not target_id and target_ref in alias_to_id:
                target_id = alias_to_id[target_ref]
                target_xmi_id = self.parser_id_to_xmi_id.get(target_id)
                log_debug(f"  Znaleziono target przez alias: {target_ref} -> {target_id} -> xmi_id: {target_xmi_id}")
            
            # 3. Szukaj przez nazwę (POPRAWKA: dodaj debugowanie)
            if not source_id and source_ref in name_to_id:
                source_id = name_to_id[source_ref]
                source_xmi_id = self.parser_id_to_xmi_id.get(source_id)
                log_debug(f"  Znaleziono source przez nazwę: {source_ref} -> {source_id} -> xmi_id: {source_xmi_id}")
                
            if not target_id and target_ref in name_to_id:
                target_id = name_to_id[target_ref]
                target_xmi_id = self.parser_id_to_xmi_id.get(target_id)
                log_debug(f"  Znaleziono target przez nazwę: {target_ref} -> {target_id} -> xmi_id: {target_xmi_id}")
            
            # Jeśli nadal nie znaleziono obu końców relacji, pomijamy ją
            if not source_xmi_id or not target_xmi_id:
                log_warning(f"Nie udało się znaleźć elementów relacji: {source_ref} -> {target_ref}")
                if not source_xmi_id:
                    log_warning(f"  Nie znaleziono elementu źródłowego: {source_ref}")
                if not target_xmi_id:
                    log_warning(f"  Nie znaleziono elementu docelowego: {target_ref}")
                continue
            
            # Utwórz relację (pozostała część funkcji bez zmian)
            label = relation.get('label', '')
            relation_style = relation.get('relation_type', '-->')
            
            if relation_type == 'c4_relationship':
                xmi_id = self._add_c4_relationship(parent_element, source_xmi_id, target_xmi_id, relation)
            else:
                xmi_id = self._add_relationship(parent_element, source_xmi_id, target_xmi_id, label, relation_style)
            
            # Zapisz mapowanie ID
            if relation_id:
                self.parser_id_to_xmi_id[relation_id] = xmi_id
            
            # Dodaj do listy relacji
            self.relationships.append({
                'id': xmi_id,
                'source_id': source_xmi_id,
                'target_id': target_xmi_id,
                'label': label,
                'type': relation_type
            })
            
            log_debug(f"  ✅ Dodano relację: {source_ref} ({source_xmi_id}) -> {target_ref} ({target_xmi_id})")
    
    def _add_relationship(self, parent_element, source_id, target_id, label, style):
        """Dodaje standardową relację UML do modelu."""
        relationship_id = self._generate_ea_id("EAID")
        
        # Określ typ relacji na podstawie stylu
        if style == '-->' or style == '->':
            # Standardowa zależność
            dependency = ET.SubElement(parent_element, 'packagedElement', {
                'xmi:type': 'uml:Dependency',
                'xmi:id': relationship_id,
                'supplier': target_id,
                'client': source_id,
                'visibility': 'public'
            })
            
            if label:
                dependency.set('name', label)
            
            self.id_map[relationship_id] = dependency
        elif style == '--|>' or style == '-|>':
            # Generalizacja
            generalization = ET.SubElement(parent_element, 'packagedElement', {
                'xmi:type': 'uml:Generalization',
                'xmi:id': relationship_id,
                'general': target_id,
                'specific': source_id,
                'visibility': 'public'
            })
            
            if label:
                generalization.set('name', label)
            
            self.id_map[relationship_id] = generalization
        else:
            # Inne typy relacji jako zależności ze stereotypem
            dependency = ET.SubElement(parent_element, 'packagedElement', {
                'xmi:type': 'uml:Dependency',
                'xmi:id': relationship_id,
                'supplier': target_id,
                'client': source_id,
                'visibility': 'public'
            })
            
            if label:
                dependency.set('name', label)
            
            # Dodaj stereotyp na podstawie stylu
            if style == '<-->' or style == '<->':
                ET.SubElement(dependency, 'stereotype', {'name': 'bidirectional'})
            elif style == '..>' or style == '.>':
                ET.SubElement(dependency, 'stereotype', {'name': 'use'})
            elif style == '*--' or style == '*-':
                ET.SubElement(dependency, 'stereotype', {'name': 'composition'})
            elif style == 'o--' or style == 'o-':
                ET.SubElement(dependency, 'stereotype', {'name': 'aggregation'})
            
            self.id_map[relationship_id] = dependency
        
        return relationship_id
    
    def _add_c4_relationship(self, parent_element, source_id, target_id, relation_data):
        """Dodaje relację C4 do modelu."""
        relationship_id = self._generate_ea_id("EAID")
        
        # C4 relacje są implementowane jako zależności ze stereotypem
        dependency = ET.SubElement(parent_element, 'packagedElement', {
            'xmi:type': 'uml:Dependency',
            'xmi:id': relationship_id,
            'supplier': target_id,
            'client': source_id,
            'visibility': 'public'
        })
        
        # Dodaj etykietę
        label = relation_data.get('label', '')
        if label:
            dependency.set('name', label)
        
        # Dodaj stereotyp "C4"
        ET.SubElement(dependency, 'stereotype', {'name': 'C4'})
        
        # Dodaj technologię jako taggedValue
        technology = relation_data.get('technology', '')
        if technology:
            tech_tag = ET.SubElement(dependency, 'taggedValue', {'name': 'technology'})
            tech_tag.text = technology
        
        # Dodaj kierunek jako taggedValue
        direction = relation_data.get('direction', '')
        if direction:
            dir_tag = ET.SubElement(dependency, 'taggedValue', {'name': 'direction'})
            dir_tag.text = direction
        
        self.id_map[relationship_id] = dependency
        
        return relationship_id
    
    def _process_notes(self, parent_element, notes):
        """Przetwarza notatki z parsera PlantUML."""
        for note in notes:
            note_content = note.get('content', '')
            note_position = note.get('position', 'right')
            note_target_id = note.get('target_id')
            parser_id = note.get('id')
            
            # Sprawdź, czy mamy mapowanie ID z parsera na XMI
            target_xmi_id = None
            if note_target_id:
                target_xmi_id = self.parser_id_to_xmi_id.get(note_target_id)
            
            # Utwórz element komentarza
            xmi_id = self._generate_ea_id("EAID")
            comment = ET.SubElement(parent_element, 'ownedComment', {
                'xmi:type': 'uml:Comment',
                'xmi:id': xmi_id,
                'visibility': 'public'
            })
            
            # Dodaj treść komentarza
            body = ET.SubElement(comment, 'body')
            body.text = note_content
            
            # Powiąż komentarz z elementem docelowym
            if target_xmi_id:
                ET.SubElement(comment, 'annotatedElement', {'xmi:idref': target_xmi_id})
            
            # Zapisz referencję do ID
            self.id_map[xmi_id] = comment
            
            # Zapisz mapowanie ID
            if parser_id:
                self.parser_id_to_xmi_id[parser_id] = xmi_id
            
            # Dodaj do listy obiektów diagramu
            self.diagram_objects.append({
                'id': xmi_id,
                'type': 'Note',
                'name': note_content[:30] + ('...' if len(note_content) > 30 else ''),
                'position': note_position,
                'target_id': target_xmi_id
            })
            
            if self.debug_options.get('processing', False):
                print(f"📝 Przetworzono notatkę: {note_content[:30]}...")
                log_debug(f"📝 Przetworzono notatkę: {note_content[:30]}...")
    
    def _verify_diagram_consistency(self):
        """Weryfikuje spójność wygenerowanego diagramu."""
        # Sprawdź relacje bez elementów źródłowych lub docelowych
        for relation in self.relationships:
            source_id = relation['source_id']
            target_id = relation['target_id']
            
            if source_id not in self.id_map:
                log_warning(f"Relacja {relation['id']} ma nieistniejący element źródłowy: {source_id}")
            
            if target_id not in self.id_map:
                log_warning(f"Relacja {relation['id']} ma nieistniejący element docelowy: {target_id}")
    
    def _create_ea_extensions(self, root: ET.Element, diagram_name: str):
        """Dodaje rozszerzenia specyficzne dla Enterprise Architect."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 1. Dodaj sekcję profili (NOWA)
        self._create_profiles_section(root)
        
        # 2. Dodaj pozostałe sekcje
        extension = ET.SubElement(root, ET.QName(self.ns['xmi'], 'Extension'), {
            'extender': 'Enterprise Architect', 'extenderID': '6.5'
        })
        
        # POPRAWIONA KOLEJNOŚĆ:
        self._create_elements_section(extension, diagram_name, current_time)
        self._create_diagrams_section(extension, diagram_name, current_time)  
        self._create_connectors_section(extension) 
        
        # Debug - pokaż listę obiektów diagramu
        self._debug_diagram_objects()
    
    def _create_profiles_section(self, root: ET.Element):
        """Tworzy sekcję z profilami UML dla stereotypów."""
        # Twórz sekcję profili
        profiles = ET.SubElement(root, 'profiles')
        
        # 1. Standardowy profil L2 (dla stereotypu service)
        std_profile = ET.SubElement(profiles, 'uml:Profile', {
            'xmi:version': '2.1',
            'xmlns:uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi:id': 'EAPK_D8F4E180_BED4_4e61_B22D_45F371A2009C',
            'profiletype': 'uml2',
            'name': 'StandardProfileL2',
            'metamodelReference': 'uml2metamodel'
        })
    
        # Dodaj element Service
        service_element = ET.SubElement(std_profile, 'packagedElement', {
            'xmi:type': 'uml:Stereotype',
            'xmi:id': 'EAID_E8EB7F24_9586_429a_A543_5B9AA9CB786B',
            'name': 'Service',
            'visibility': 'public'
        })
        
        # 2. Profil niestandardowy (dla pozostałych stereotypów)
        custom_profile = ET.SubElement(profiles, 'uml:Profile', {
            'xmi:version': '2.1',
            'xmlns:uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi:id': 'EAPK_EC27B841_1486_494e_B760_1860478BF8F5',
            'profiletype': 'ea_uml2',
            'name': 'thecustomprofile',
            'metamodelReference': 'uml2metamodel'
        })
        
        # Dodaj definicje stereotypów
        stereotype_definitions = {
            'controller': 'EAID_3F786850_E47F_11D2_ABF0_00A0C90FFFC3',
            'gateway': 'EAID_C4F252E8_E947_11D2_ABF1_00A0C90FFFC8',
            'utility': 'EAID_D8C0A0A0_E947_11D2_ABF2_00A0C90FFFC9',
            'facade': 'EAID_F0C034E0_E947_11D2_ABF3_00A0C90FFFCA',
            'repository': 'EAID_08C0A0A0_E947_11D2_ABF4_00A0C90FFFCB'
        }
        
        for stereotype_name, stereotype_id in stereotype_definitions.items():
            stereotype_element = ET.SubElement(custom_profile, 'packagedElement', {
                'xmi:type': 'uml:Stereotype',
                'xmi:id': stereotype_id,
                'name': stereotype_name,
                'visibility': 'public'
            })
        
        # 3. Profil SOMF (dla stereotypu repository)
        somf_profile = ET.SubElement(profiles, 'uml:Profile', {
            'xmi:version': '2.1',
            'xmlns:uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi:id': 'EAPK_A3DDA574_A47C_4d73_9C42_F7EA2C5ACD8D',
            'profiletype': 'uml2',
            'name': 'SOMF',
            'metamodelReference': 'uml2metamodel'
        })
        
        repository_element = ET.SubElement(somf_profile, 'packagedElement', {
            'xmi:type': 'uml:Stereotype',
            'xmi:id': 'EAID_F1C0F34E_F947_11D2_ABF4_00A0C90FFFCC',
            'name': 'repository',
            'visibility': 'public'
        })

    def _create_elements_section(self, extension: ET.Element, diagram_name: str, current_time: str):
        """Tworzy sekcję elements z definicjami elementów dla EA."""
        elements = ET.SubElement(extension, 'elements')
        
        # Dodaj główny pakiet
        package_element = ET.SubElement(elements, 'element', {
            'xmi:idref': self.package_id,
            'xmi:type': 'uml:Package',
            'name': diagram_name,
            'scope': 'public'
        })
        
        # Dodaj model dla pakietu
        ET.SubElement(package_element, 'model', {
            'package2': f"EAID_{self.package_id.split('_')[1]}", 
            'package': "EAPK_25CB1803_12A5_47b7_BF59_0C80F57AA528",  # Stała wartość
            'tpos': '0',
            'ea_localid': self._get_local_id(self.package_id),
            'ea_eleType': 'package'
        })
        
        # Dodaj properties dla pakietu
        ET.SubElement(package_element, 'properties', {
            'isSpecification': 'false',
            'sType': 'Package',
            'nType': '7',
            'scope': 'public'
        })
        
        # Dodaj project info
        ET.SubElement(package_element, 'project', {
            'author': self.author,
            'version': '1.0',
            'phase': '1.0',
            'created': current_time,
            'modified': current_time
        })
        
        # Zbuduj mapowanie pakiet -> komponenty dla sekcji element
        package_to_components = {}
        
        # Dodaj elementy diagramu
        for obj in self.diagram_objects:
            if isinstance(obj, dict):
                obj_id = obj.get('id')
                obj_type = obj.get('type', 'Component')
                obj_name = obj.get('name', '')
                
                if obj_id in self.id_map:
                    # Znajdź element pakietu, w którym znajduje się ten komponent
                    parent_pkg = None
                    
                    # Sprawdź, czy to komponent przypisany do pakietu
                    for component_id, component_data in self.parsed_data['components'].items():
                        if self.parser_id_to_xmi_id.get(component_id) == obj_id:
                            package_id = component_data.get('package')
                            if package_id:
                                parent_pkg = self.parser_id_to_xmi_id.get(package_id)
                                # Dodaj do mapowania
                                if parent_pkg not in package_to_components:
                                    package_to_components[parent_pkg] = []
                                package_to_components[parent_pkg].append(obj_id)
                                break
                    
                    element = ET.SubElement(elements, 'element', {
                        'xmi:idref': obj_id,
                        'xmi:type': f"uml:{obj_type}",
                        'name': obj_name,
                        'scope': 'public'
                    })
                    
                    # Dodaj model dla elementu - wskazując na pakiet, jeśli istnieje
                    model_attrs = {
                        'tpos': '0',
                        'ea_localid': self._get_local_id(obj_id),
                        'ea_eleType': 'element'
                    }
                    
                    # Ustaw pakiet nadrzędny dla komponentu (w sekcji elements)
                    if parent_pkg:
                        model_attrs['package'] = parent_pkg
                    else:
                        model_attrs['package'] = self.package_id
                    
                    ET.SubElement(element, 'model', model_attrs)
                    
                    # Dodaj properties dla elementu
                    ET.SubElement(element, 'properties', {
                        'isSpecification': 'false',
                        'sType': obj_type,
                        'nType': self._get_ntype_for_element_type(obj_type),
                        'scope': 'public'
                    })
                    
                    # Dodaj informację o pakiecie w extendedProperties
                    if parent_pkg:
                        # Znajdź nazwę pakietu
                        pkg_name = ""
                        for pkg_id, pkg_data in self.parsed_data['packages'].items():
                            if self.parser_id_to_xmi_id.get(pkg_id) == parent_pkg:
                                pkg_name = pkg_data.get('name', '')
                                break
                        
                        if pkg_name:
                            extended = ET.SubElement(element, 'extendedProperties')
                            extended.set('package_name', pkg_name)
    
    def _get_ntype_for_element_type(self, element_type):
        """Zwraca odpowiedni nType dla danego typu elementu w EA."""
        ntype_map = {
            'Component': '4',
            'Interface': '5',
            'Package': '7',
            'Boundary': '10',
            'Note': '19',
            'Actor': '1'
        }
        return ntype_map.get(element_type, '4')  # Domyślnie Component
    
    def _create_connectors_section(self, extension: ET.Element):
        """Tworzy sekcję connectors z definicjami relacji dla EA."""
        connectors = ET.SubElement(extension, 'connectors')
        
        if self.debug_options.get('relationships', False):
            print(f"Tworzenie sekcji connectors dla {len(self.relationships)} relacji")
            log_debug(f"Tworzenie sekcji connectors dla {len(self.relationships)} relacji")
        
        added_connectors = 0
        
        for i, relation in enumerate(self.relationships):
            relation_id = relation['id']
            source_id = relation['source_id']
            target_id = relation['target_id']
            label = relation['label']
            relation_type = relation['type']
            
            # Upewnij się, że elementy źródłowe i docelowe istnieją
            if source_id not in self.id_map or target_id not in self.id_map:
                if self.debug_options.get('relationships', False):
                    log_warning(f"Pomijam relację {relation_id}: brak elementów w id_map")
                continue
            
            connector = ET.SubElement(connectors, 'connector', {
                'xmi:idref': relation_id
            })
            
            # SOURCE (element źródłowy)
            source = ET.SubElement(connector, 'source', {
                'xmi:idref': source_id
            })
            
            # Dodaj model dla źródła
            source_element = self.id_map[source_id]
            source_name = source_element.get('name', '')
            source_type = self._get_element_type(source_element)
            
            ET.SubElement(source, 'model', {
                'ea_localid': self._get_local_id(source_id),
                'type': source_type,
                'name': source_name
            })
            
            # Dodaj role i pozostałe atrybuty
            ET.SubElement(source, 'role', {'visibility': 'Public'})
            ET.SubElement(source, 'type', {'aggregation': 'none'})
            ET.SubElement(source, 'constraints')
            ET.SubElement(source, 'modifiers', {'isNavigable': 'false'})
            
            # TARGET (element docelowy)
            target = ET.SubElement(connector, 'target', {
                'xmi:idref': target_id
            })
            
            # Dodaj model dla celu
            target_element = self.id_map[target_id]
            target_name = target_element.get('name', '')
            target_type = self._get_element_type(target_element)
            
            ET.SubElement(target, 'model', {
                'ea_localid': self._get_local_id(target_id),
                'type': target_type,
                'name': target_name
            })
            
            # Dodaj role i pozostałe atrybuty
            ET.SubElement(target, 'role', {'visibility': 'Public'})
            ET.SubElement(target, 'type', {'aggregation': 'none'})
            ET.SubElement(target, 'constraints')
            ET.SubElement(target, 'modifiers', {'isNavigable': 'true'})
            
            # PROPERTIES (właściwości relacji)
            ea_type = self._get_connector_type(relation_type)
            properties_attrs = {
                'ea_type': ea_type,
                'direction': 'Source -> Destination'
            }
            
            if label:
                properties_attrs['name'] = label
            
            ET.SubElement(connector, 'properties', properties_attrs)
            
            # Dodaj dokumentację
            ET.SubElement(connector, 'documentation')
            
            # Dodaj appearance - wygląd relacji
            ET.SubElement(connector, 'appearance', {
                'linemode': '1',
                'linecolor': '-1',
                'linewidth': '1',
                'seqno': str(i),
                'headStyle': '0',
                'lineStyle': '0'
            })

            added_connectors += 1

        if self.debug_options.get('relationships', False):
            print(f"Dodano {added_connectors} connectors z {len(self.relationships)} relacji")
            log_debug(f"Dodano {added_connectors} connectors z {len(self.relationships)} relacji")

    
    def _get_connector_type(self, relation_type):
        """Zwraca typ konektora EA na podstawie typu relacji."""
        connector_types = {
            'c4_relationship': 'Dependency',
            'relationship': 'Dependency',
            'dependency': 'Dependency',
            'generalization': 'Generalization',
            'realization': 'Realisation',
            'composition': 'Composition',
            'aggregation': 'Aggregation'
        }
        return connector_types.get(relation_type, 'Dependency')
    
    def _get_element_type(self, element):
        """Zwraca typ elementu EA na podstawie elementu XML."""
        element_type = element.get('xmi:type', '')
        
        if element_type == 'uml:Component':
            return 'Component'
        elif element_type == 'uml:Interface':
            return 'Interface'
        elif element_type == 'uml:Package':
            return 'Package'
        elif element_type == 'uml:Actor':
            return 'Actor'
        elif element_type == 'uml:Comment':
            return 'Note'
        else:
            return 'Class'  # Domyślny typ
    
    def _create_diagrams_section(self, extension: ET.Element, diagram_name: str, current_time: str):
        """Tworzy sekcję diagrams z definicją diagramu dla EA."""
        component_seq = 100
        diagrams = ET.SubElement(extension, 'diagrams')
        diagram = ET.SubElement(diagrams, 'diagram', {
            'xmi:id': self.diagram_id,
            'name': diagram_name,
            'type': 'Component',
            'diagramType': 'ComponentDiagram'
        })
        
        # Model diagramu
        ET.SubElement(diagram, 'model', {
            'package': self.package_id,
            'localID': self._get_local_id(self.diagram_id),
            'owner': self.package_id
        })
        
        # Properties diagramu
        ET.SubElement(diagram, 'properties', {
            'name': diagram_name,
            'type': 'Component'
        })
        
        # Project info
        ET.SubElement(diagram, 'project', {
            'author': self.author,
            'version': '1.0',
            'created': current_time,
            'modified': current_time
        })
        
        # Style diagramu
        ET.SubElement(diagram, 'style1', {'value': (
            'ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;'
            'Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;'
            'ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=795;DocSize.cy=1134;'
            'ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;'
            'VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;'
            'HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;'
            'HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;'
            'ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;'
            'ShowShape=1;'
        )})
        
        # Dodaj flagę diagnostyczną
        enable_position_diagnostics = True
        position_log = []
        
        def log_position_info(message):
            """Funkcja pomocnicza do logowania informacji o pozycjach elementów"""
            if enable_position_diagnostics:
                position_log.append(message)
                if self.debug_options.get('positioning', False):
                    print(f"📊 {message}")
                    log_debug(f"📊 {message}")
        
        log_position_info(f"Rozpoczęto rozmieszczanie elementów dla diagramu '{diagram_name}'")
        layer_packages = {}
        # Najpierw przetwarzaj pakiety najwyższego poziomu
        for pkg_id, pkg_data in self.parsed_data['packages'].items():
            # Tylko pakiety najwyższego poziomu (bez parent_package)
            if not pkg_data.get('parent_package'):
                package_name = pkg_data.get('name', 'Unnamed Package')
                package_xmi_id = self.parser_id_to_xmi_id.get(pkg_id)
                
                if package_xmi_id:
                    layer_packages[package_name] = {
                        'id': pkg_id,
                        'xmi_id': package_xmi_id,
                        'name': package_name
                    }
                    log_position_info(f"Znaleziono warstwę: {package_name} (ID: {package_xmi_id})")
        # Dodaj rozszerzoną diagnostykę mapowania
        log_position_info(f"Sprawdzam mapowanie pakietów do komponentów")

        # Przeanalizuj wszystkie komponenty i ich pakiety
        for comp_id, comp_data in self.parsed_data['components'].items():
            package_id = comp_data.get('package')
            comp_name = comp_data.get('name', 'Bez nazwy')
            comp_xmi_id = self.parser_id_to_xmi_id.get(comp_id)
            
            log_position_info(f"Komponent: {comp_name} (ID: {comp_id})")
            log_position_info(f"  XMI ID komponentu: {comp_xmi_id}")
            
            if package_id:
                # Sprawdź, czy XMI ID pakietu istnieje w mapowaniu
                package_xmi_id = self.parser_id_to_xmi_id.get(package_id)
                log_position_info(f"  Przypisany do pakietu (ID: {package_id})")
                log_position_info(f"  XMI ID pakietu: {package_xmi_id}")
                
                # Sprawdź, czy istnieje warstwa odpowiadająca pakietowi
                found_layer = False
                for layer_name, pkg_info in layer_packages.items():
                    if pkg_info['id'] == package_id:
                        found_layer = True
                        log_position_info(f"  Należy do warstwy: {layer_name}")
                        break
                
                if not found_layer:
                    log_position_info(f"  UWAGA: Nie znaleziono warstwy dla pakietu {package_id}")
            else:
                log_position_info(f"  Nie przypisany do żadnego pakietu")

        # Diagnostyka samych warstw
        log_position_info(f"Sprawdzam mapowanie identyfikatorów warstw")
        for layer_name, pkg_info in layer_packages.items():
            log_position_info(f"Warstwa: {layer_name}")
            log_position_info(f"  Parser ID: {pkg_info['id']}")
            log_position_info(f"  XMI ID: {pkg_info['xmi_id']}")
            log_position_info(f"  Weryfikacja w parser_id_to_xmi_id: {self.parser_id_to_xmi_id.get(pkg_info['id'])}")

        # Diagnostyka parser_id_to_xmi_id
        log_position_info(f"Zawartość mapowania parser_id_to_xmi_id:")
        for parser_id, xmi_id in self.parser_id_to_xmi_id.items():
            # Znajdź nazwę elementu na podstawie ID
            element_name = "Nieznany"
            element_type = "Nieznany"
            
            # Sprawdź w komponentach
            for id, data in self.parsed_data['components'].items():
                if id == parser_id:
                    element_name = data.get('name', 'Bez nazwy')
                    element_type = "Komponent"
                    break
            
            # Sprawdź w pakietach
            for id, data in self.parsed_data['packages'].items():
                if id == parser_id:
                    element_name = data.get('name', 'Bez nazwy')
                    element_type = "Pakiet"
                    break
            
            # Sprawdź w interfejsach
            for id, data in self.parsed_data['interfaces'].items():
                if id == parser_id:
                    element_name = data.get('name', 'Bez nazwy')
                    element_type = "Interfejs"
                    break
                    
            log_position_info(f"  {parser_id} -> {xmi_id} ({element_type}: {element_name})")

        # Elements diagramu
        elements = ET.SubElement(diagram, 'elements')
    
        # Dodaj tytuł diagramu
        title_id = self._generate_ea_id("EAID")
        title_x = 100
        title_y = 20
        title_width = 800
        title_height = 50
        title_position = f"Left={title_x};Top={title_y};Right={title_x + title_width};Bottom={title_y + title_height};"

        ET.SubElement(elements, 'element', {
            'subject': title_id,
            'seqno': "1",
            'geometry': title_position,
            'style': "DUID=unique_id;BorderColor=-1;BorderWidth=0;BackColor=-1;",
            'elementclass': 'Text'
        })
        
        # Tablica z komponentami, które już zostały dodane do diagramu
        self.added_to_diagram = set()
        
        # Mapowanie pakietów do ich komponentów
        component_to_package = {}
        for comp_id, comp_data in self.parsed_data['components'].items():
            package_id = comp_data.get('package')
            if package_id:
                # Sprawdź czy otrzymamy XMI ID pakietu
                package_xmi_id = self.parser_id_to_xmi_id.get(package_id)
                
                # Tylko jeśli mamy prawidłowe XMI ID pakietu
                if package_xmi_id:
                    if package_xmi_id not in component_to_package:
                        component_to_package[package_xmi_id] = []
                    
                    component_xmi_id = self.parser_id_to_xmi_id.get(comp_id)
                    if component_xmi_id:
                        component_to_package[package_xmi_id].append({
                            'id': comp_id,
                            'name': comp_data.get('name', 'Unnamed'),
                            'type': comp_data.get('type', 'Component'),
                            'stereotype': comp_data.get('stereotype', ''),
                            'xmi_id': component_xmi_id
                        })
                        log_position_info(f"  Dodano komponent '{comp_data.get('name')}' do pakietu {package_xmi_id}")
                    else:
                        log_position_info(f"  UWAGA: Nie znaleziono XMI ID dla komponentu '{comp_data.get('name')}' (ID: {comp_id})")
                else:
                    log_position_info(f"  UWAGA: Nie znaleziono XMI ID dla pakietu {package_id} komponentu '{comp_data.get('name')}'")
        
        # Znajdź pakiety reprezentujące warstwy
        layer_packages = {}
        for pkg_id, pkg_data in self.parsed_data['packages'].items():
            # Tylko pakiety najwyższego poziomu (bez parent_package)
            if not pkg_data.get('parent_package'):
                layer_name = pkg_data.get('name', 'Unnamed Layer')
                layer_packages[layer_name] = {
                    'id': pkg_id,
                    'xmi_id': self.parser_id_to_xmi_id.get(pkg_id),
                    'name': layer_name
                }
                log_position_info(f"Znaleziono warstwę: {layer_name} (ID: {layer_packages[layer_name]['xmi_id']})")
        
        # Obliczamy wymiary pakietów na podstawie zawartości
        package_dimensions = {}
        
        for layer_name, pkg_info in layer_packages.items():
            pkg_xmi_id = pkg_info['xmi_id']
            components = component_to_package.get(pkg_xmi_id, [])
            
            log_position_info(f"Analiza pakietu '{layer_name}' (ID: {pkg_xmi_id}), liczba komponentów: {len(components)}")
            
            # Analizuj komponenty wewnątrz pakietu
            if components:
                # Parametry układu wewnątrz pakietu
                margin_x = 40
                margin_y = 60
                comp_spacing_x = 30
                comp_spacing_y = 30
                
                # Standardowe wymiary komponentu
                base_comp_width = 160
                comp_height = 70
                
                # Oblicz szerokości komponentów
                component_widths = []
                for comp in components:
                    comp_name = comp.get('name', '')
                    name_length = len(comp_name)
                    adjusted_width = min(max(base_comp_width, name_length * 8), base_comp_width * 2)
                    component_widths.append(adjusted_width)
                    log_position_info(f"  - Komponent '{comp_name}' (ID: {comp.get('xmi_id', 'N/A')}), szerokość: {adjusted_width}px")
                
                # Określ optymalną liczbę komponentów w wierszu
                if len(components) <= 3:
                    components_per_row = len(components)
                else:
                    components_per_row = max(2, min(3, len(components) // 2 + (1 if len(components) % 2 else 0)))
                
                # Oblicz liczbę wierszy
                num_rows = (len(components) + components_per_row - 1) // components_per_row
                
                log_position_info(f"  * Układ: {components_per_row} komponentów w wierszu, {num_rows} wierszy")
                
                # Oblicz szerokość pakietu
                if components_per_row == 1:
                    package_width = 2 * margin_x + max(component_widths)
                else:
                    package_width = 2 * margin_x + components_per_row * max(component_widths) + (components_per_row - 1) * comp_spacing_x
                
                # Minimalny rozmiar pakietu
                package_width = max(package_width, 450)
                
                # Oblicz wysokość pakietu
                package_height = 2 * margin_y + num_rows * comp_height + (num_rows - 1) * comp_spacing_y
                package_height = max(package_height, 270)  # Minimalny rozmiar
                
                log_position_info(f"  * Obliczone wymiary pakietu: {package_width}x{package_height}px")
                
                # Zapisz wymiary pakietu
                package_dimensions[pkg_xmi_id] = {
                    'width': package_width,
                    'height': package_height,
                    'components_per_row': components_per_row,
                    'num_rows': num_rows,
                    'component_widths': component_widths
                }
            else:
                # Domyślne wymiary dla pustego pakietu
                package_dimensions[pkg_xmi_id] = {
                    'width': 450,
                    'height': 270,
                    'components_per_row': 1,
                    'num_rows': 0,
                    'component_widths': []
                }
                log_position_info(f"  * Pusty pakiet, używam domyślnych wymiarów: 450x270px")
        
        # Rozmieszczamy pakiety warstw z odpowiednimi odstępami
        package_positions = {}
        vertical_spacing = 50  # Odstęp pionowy między pakietami
        horizontal_spacing = 200  # Odstęp poziomy między kolumnami pakietów
        max_layers_in_column = 5  # Maksymalna liczba warstw w jednej kolumnie
        start_x = 100
        start_y = 100
        current_x = start_x
        current_y = start_y
        layer_count = 0
        current_column = 0
        
        log_position_info(f"Rozpoczynam rozmieszczanie pakietów warstw (pionowo)")

        # Najpierw umieść pakiety warstw
        for i, (layer_name, pkg_info) in enumerate(layer_packages.items()):
            pkg_xmi_id = pkg_info['xmi_id']
            
            # Pobierz obliczone wymiary pakietu
            pkg_width = package_dimensions.get(pkg_xmi_id, {}).get('width', 450)  # domyślna szerokość
            pkg_height = package_dimensions.get(pkg_xmi_id, {}).get('height', 270)  # domyślna wysokość
            
            # Sprawdź czy rozpocząć nową kolumnę
            if layer_count >= max_layers_in_column:
                current_column += 1
                current_y = start_y
                current_x += max([pos['width'] for pos in package_positions.values()]) + horizontal_spacing
                layer_count = 0
                log_position_info(f"Rozpoczynam nową kolumnę pakietów (kolumna {current_column+1})")
            
            # Zapisz pozycję pakietu
            left = current_x
            top = current_y
            right = left + pkg_width
            bottom = top + pkg_height
            
            package_positions[pkg_xmi_id] = {
                'left': left, 'top': top, 'right': right, 'bottom': bottom,
                'width': pkg_width, 'height': pkg_height
            }
            
            log_position_info(f"Pakiet '{layer_name}' (ID: {pkg_xmi_id}): Left={left}, Top={top}, Right={right}, Bottom={bottom}, Kolumna={current_column+1}")
            
            # Rysuj pakiet z odpowiednim kolorem tła
            position = f"Left={left};Top={top};Right={right};Bottom={bottom};"
            ET.SubElement(elements, 'element', {
                'subject': pkg_xmi_id,
                'seqno': str(i + 10),  # Seqno dla pakietów
                'geometry': position,
                'style': f"DUID=unique_id;BorderColor=-1;BorderWidth=1;{self._get_layer_style(layer_name)}",
                'elementclass': 'Package'
            })
            
            self.added_to_diagram.add(pkg_xmi_id)
            
            # Przesuń pozycję dla następnego pakietu (w dół)
            current_y += pkg_height + vertical_spacing
            layer_count += 1
        
        # Znajdź maksymalny punkt X i Y używanych przez pakiety
        max_right = max([pos['right'] for pos in package_positions.values()], default=start_x)
        max_bottom = max([pos['bottom'] for pos in package_positions.values()], default=start_y)

        # Oblicz środek wysokości wszystkich warstw
        min_top = min([pos['top'] for pos in package_positions.values()], default=start_y)
        avg_y = min_top + (max_bottom - min_top) / 2

        # Znajdź środek poziomy wszystkich warstw
        center_x = start_x + (max_right - start_x) / 2

        # Ustaw pozycję X dla elementów zewnętrznych - po prawej stronie warstw
        actors_x = max_right + horizontal_spacing  # Po prawej stronie warstw
        actors_y = min_top + (max_bottom - min_top) / 2 - 150  # Na wysokości środka warstw

        # Dla elementów spoza warstw - rozmieszczenie w poziomie od prawej strony warstw
        current_x = actors_x
        max_elements_in_row = 5  # Maksymalna liczba elementów w rzędzie
        elements_in_row = 0

        log_position_info(f"Rozpoczynam rozmieszczanie elementów zewnętrznych (obok warstw)")
        log_position_info(f"Elementy zewnętrzne: X={actors_x}, Y={actors_y}")

        # Lista elementów zewnętrznych do rozmieszczenia
        external_elements = []

        # Najpierw zbierz wszystkie elementy zewnętrzne
        for obj in self.diagram_objects:
            obj_id = obj.get('id')
            obj_type = obj.get('type', '')
            
            # Sprawdź, czy element należy do jakiegoś pakietu
            element_in_package = False
            for comp_id, comp_data in self.parsed_data['components'].items():
                if self.parser_id_to_xmi_id.get(comp_id) == obj_id and comp_data.get('package'):
                    element_in_package = True
                    break
            
            # Jeśli element jest już w pakiecie, pomiń go
            if element_in_package:
                continue
            
            # Elementy zewnętrzne (aktorzy, systemy, itp.)
            if obj_type in ['Actor', 'Component', 'Interface']:
                external_elements.append(obj)

        # Jeśli mamy zbyt dużo elementów zewnętrznych, dostosuj układ
        element_seq = 100
        if external_elements:
            # Oblicz potrzebną przestrzeń dla wszystkich elementów zewnętrznych
            estimated_width_per_element = 150  # Szacowana szerokość elementu
            total_width_needed = len(external_elements) * estimated_width_per_element
            
            # Dostosuj liczbę elementów w rzędzie na podstawie dostępnej przestrzeni
            if len(external_elements) <= max_elements_in_row:
                elements_per_row = len(external_elements)
            else:
                elements_per_row = max_elements_in_row
            
            # Oblicz liczbę rzędów
            num_rows = (len(external_elements) + elements_per_row - 1) // elements_per_row
            
            # Rozmieść elementy zewnętrzne w siatce
            for i, obj in enumerate(external_elements):
                obj_id = obj.get('id')
                obj_type = obj.get('type', '')
                obj_name = obj.get('name', '')
                
                # Oblicz pozycję w siatce
                row = i // elements_per_row
                col = i % elements_per_row
                
                # Dostosuj szerokość i wysokość w zależności od typu elementu
                if obj_type == 'Component':
                    obj_width = min(max(150, len(obj_name) * 7), 250)
                    obj_height = 70
                elif obj_type == 'Interface':
                    obj_width = min(max(130, len(obj_name) * 6), 200)
                    obj_height = 60
                else:  # Actor
                    obj_width = 100
                    obj_height = 120
                

                # Oblicz pozycję elementu - zawsze w jednej kolumnie
                elem_x = actors_x
                elem_y = actors_y + i * (obj_height + 40)  # Jeden pod drugim
                
                # Pozycja elementu
                obj_position = f"Left={elem_x};Top={elem_y};Right={elem_x + obj_width};Bottom={elem_y + obj_height};"
                
                log_position_info(f"Element zewnętrzny '{obj_name}' (ID: {obj_id}): Left={elem_x}, Top={elem_y}, Wiersz={row}, Kolumna={col}")
                
                ET.SubElement(elements, 'element', {
                    'subject': obj_id,
                    'seqno': str(element_seq),
                    'geometry': obj_position,
                    'style': "DUID=unique_id;",
                    'elementclass': obj_type
                })
                
                self.added_to_diagram.add(obj_id)
                element_seq += 1
        
        log_position_info(f"Rozpoczynam rozmieszczanie komponentów wewnątrz pakietów")
        
        # Dla każdego pakietu rozmieszczamy jego komponenty
        for pkg_xmi_id, position in package_positions.items():
            components = component_to_package.get(pkg_xmi_id, [])
            if not components:
                continue
            
            # Znajdź nazwę pakietu
            pkg_name = ""
            for layer_name, pkg_info in layer_packages.items():
                if pkg_info['xmi_id'] == pkg_xmi_id:
                    pkg_name = layer_name
                    break
            
            log_position_info(f"Rozmieszczam komponenty w pakiecie '{pkg_name}' (ID: {pkg_xmi_id})")
                
            # Parametry układu wewnątrz pakietu
            margin_x = 40  # Margines poziomy od granicy pakietu
            margin_y = 60  # Margines pionowy od góry pakietu
            comp_spacing_x = 30  # Odstęp poziomy między komponentami
            comp_spacing_y = 30  # Odstęp pionowy między komponentami
            
            # Standardowa wysokość komponentu
            comp_height = 70
            
            # Pobierz obliczone parametry układu
            components_per_row = package_dimensions[pkg_xmi_id]['components_per_row']
            component_widths = package_dimensions[pkg_xmi_id]['component_widths']
            
            # Jeśli mamy mniej niż 4 komponenty, układaj je w jednym rzędzie
            if len(components) < 4:
                components_per_row = len(components)
            
            log_position_info(f"  * Układ: {components_per_row} komponenty w wierszu")
            
            # Rozmieszczamy komponenty w siatce wewnątrz pakietu
            for i, comp in enumerate(components):
                row = i // components_per_row
                col = i % components_per_row
                
                # Szerokość komponentu zależna od nazwy
                if i < len(component_widths):
                    comp_width = component_widths[i]
                else:
                    comp_name = comp.get('name', '')
                    name_length = len(comp_name)
                    comp_width = min(max(160, name_length * 8), 300)
                
                # Oblicz dostępną szerokość wiersza
                available_row_width = position['width'] - (2 * margin_x)
                
                # Oblicz szerokość pojedynczego komponentu w wierszu
                single_comp_width = (available_row_width - ((components_per_row - 1) * comp_spacing_x)) / components_per_row
                
                # Dostosuj szerokość do dostępnej przestrzeni, ale zachowaj minimum
                comp_width = min(comp_width, single_comp_width)
                comp_width = max(comp_width, 150)  # Minimum 150 px szerokości
                
                # Oblicz pozycję komponentu wewnątrz pakietu
                # Dla pojedynczego komponentu w wierszu - wyśrodkuj
                if components_per_row == 1:
                    comp_left = position['left'] + (position['width'] - comp_width) / 2
                else:
                    # Dla wielu komponentów - rozmieść równomiernie
                    total_comps_width = components_per_row * comp_width
                    total_spacing = (components_per_row - 1) * comp_spacing_x
                    start_x = position['left'] + (position['width'] - (total_comps_width + total_spacing)) / 2
                    comp_left = start_x + (col * (comp_width + comp_spacing_x))
                
                # Pozycja Y - od góry pakietu plus margines, zwiększany dla każdego kolejnego rzędu
                comp_top = position['top'] + margin_y + (row * (comp_height + comp_spacing_y))
                comp_right = comp_left + comp_width
                comp_bottom = comp_top + comp_height
                
                comp_name = comp.get('name', '')
                comp_xmi_id = comp.get('xmi_id')
                
                log_position_info(f"  - Komponent '{comp_name}' (ID: {comp_xmi_id}): Left={comp_left}, Top={comp_top}, Right={comp_right}, Bottom={comp_bottom}, Wiersz={row}, Kolumna={col}")
                
                comp_position = f"Left={comp_left};Top={comp_top};Right={comp_right};Bottom={comp_bottom};"
                
                if comp_xmi_id and comp_xmi_id not in self.added_to_diagram:
                    # Określ styl komponentu w zależności od stereotypu
                    component_style = "DUID=unique_id;"
                    stereotype = comp.get('stereotype', '')
                    
                    if stereotype:
                        log_position_info(f"    Stereotyp: {stereotype}")
                        # Jawne dodanie stereotypu do stylu elementu
                        component_style += f"stereotype={stereotype};"
                    
                    if stereotype == 'controller':
                        component_style += "BackColor=-1249301;"
                    elif stereotype == 'service':
                        component_style += "BackColor=-3342357;"
                    elif stereotype == 'repository':
                        component_style += "BackColor=-1120106;"
                    elif stereotype == 'facade':
                        component_style += "BackColor=-6357;"
                    elif stereotype == 'utility':
                        component_style += "BackColor=-8355732;"
                    elif stereotype == 'gateway':
                        component_style += "BackColor=-16711681;"
                    
                    # Dodaj komponent do diagramu
                    ET.SubElement(elements, 'element', {
                        'subject': comp_xmi_id,
                        'seqno': str(component_seq),
                        'geometry': comp_position,
                        'style': component_style,  # Bez "stereotype=" w tym atrybucie
                        'elementclass': comp.get('type', 'Component')
                    })
                    
                    self.added_to_diagram.add(comp_xmi_id)
                    component_seq += 1
        
        log_position_info("\nPODSUMOWANIE DIAGNOSTYKI")
        log_position_info(f"Liczba pakietów warstw: {len(layer_packages)}")

        for layer_name, pkg_info in layer_packages.items():
            pkg_xmi_id = pkg_info['xmi_id']
            components = component_to_package.get(pkg_xmi_id, [])
            log_position_info(f"Warstwa {layer_name}: {len(components)} komponentów")
            
            for comp in components:
                log_position_info(f"  - {comp.get('name')} (ID: {comp.get('xmi_id')})")

        log_position_info(f"Elementy dodane do diagramu: {len(self.added_to_diagram)}")
        log_position_info(f"Łącznie elementów diagramu: {len(self.diagram_objects)}")

        # Zapisz diagnostykę pozycji do pliku
        if enable_position_diagnostics:
            try:
                log_file_name = f"position_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                with open(log_file_name, 'w', encoding='utf-8') as f:
                    f.write(f"Diagnostyka pozycji elementów dla diagramu '{diagram_name}'\n")
                    f.write(f"Data wygenerowania: {current_time}\n\n")
                    for log_entry in position_log:
                        f.write(f"{log_entry}\n")
                print(f"\nZapisano diagnostykę pozycji do pliku: {log_file_name}")
                log_info(f"Zapisano diagnostykę pozycji do pliku: {log_file_name}")
            except Exception as e:
                print(f"Błąd podczas zapisywania pliku diagnostycznego: {e}")
                log_error(f"Błąd podczas zapisywania pliku diagnostycznego: {e}")
        
        # Dodaj pozostałe elementy (aktorzy, systemy zewnętrzne itp.) poniżej pakietów
        actors_y = max([pos['bottom'] for pos in package_positions.values()], default=start_y) + 100
        current_x = start_x
        
        for obj in self.diagram_objects:
            obj_id = obj.get('id')
            obj_type = obj.get('type', '')
            
            # Pomiń elementy, które są już dodane do diagramu
            if obj_id in self.added_to_diagram:
                continue
            
            # Elementy zewnętrzne (aktorzy, systemy, itp.)
            if obj_type in ['Actor', 'Component', 'Interface']:
                obj_name = obj.get('name', '')
                name_length = len(obj_name)
                
                # Dostosuj szerokość w zależności od typu i długości nazwy
                if obj_type == 'Component':
                    obj_width = min(max(150, name_length * 7), 250)
                    obj_height = 70
                elif obj_type == 'Interface':
                    obj_width = min(max(130, name_length * 6), 200)
                    obj_height = 60
                else:  # Actor
                    obj_width = 100
                    obj_height = 120
                
                # Sprawdź czy element zmieści się w bieżącym wierszu
                if current_x + obj_width > 1000:  # Maksymalna szerokość diagramu
                    current_x = start_x
                    actors_y += obj_height + 40
                
                obj_position = f"Left={current_x};Top={actors_y};Right={current_x + obj_width};Bottom={actors_y + obj_height};"
                
                ET.SubElement(elements, 'element', {
                    'subject': obj_id,
                    'seqno': str(component_seq),
                    'geometry': obj_position,
                    'style': "DUID=unique_id;",
                    'elementclass': obj_type
                })
                
                self.added_to_diagram.add(obj_id)
                current_x += obj_width + 50
                component_seq += 1
        
        # Dodaj diagramlinks dla relacji
        diagramlinks = ET.SubElement(diagram, 'diagramlinks')
        
        log_position_info(f"Przetwarzanie {len(self.relationships)} relacji dla diagramlinks")
        added_links = 0

        for relation in self.relationships:
            relation_id = relation['id']
            source_id = relation['source_id']
            target_id = relation['target_id']
            
            # Pomiń relacje bez prawidłowych ID źródła lub celu
            if source_id not in self.id_map or target_id not in self.id_map:
                log_position_info(f"  Pomijam relację {relation_id}: brak elementów w id_map")
                continue
            
            # KRYTYCZNA POPRAWKA: Sprawdź czy oba końce relacji są na diagramie
            if source_id not in self.added_to_diagram or target_id not in self.added_to_diagram:
                log_position_info(f"  Pomijam relację {relation_id}: elementy nie są na diagramie")
                continue
            
            # Generuj unikalny linkID dla diagramlink
            link_uuid = f"DCLINK_{uuid.uuid4().hex[:8].upper()}"
            
            diagramlink = ET.SubElement(diagramlinks, 'diagramlink', {
                'connectorID': relation_id,
                'start': source_id,
                'end': target_id,
                'linkID': link_uuid,
                'hidden': '0',
                'geometry': 'EDGE=1;$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path=;'
            })
            
            added_links += 1
            log_position_info(f"  ✅ Dodano diagramlink: {source_id} -> {target_id}")

        log_position_info(f"Dodano {added_links} relacji do diagramu z {len(self.relationships)} istniejących")
        log_debug(f"self.added_to_diagram zawiera {len(self.added_to_diagram)} elementów")
        for elem_id in self.added_to_diagram:
            log_debug(f"  - {elem_id}")
    
    def _get_stereotype_style(self, stereotype):
        """Zwraca styl dla danego stereotypu."""
        if not stereotype:
            return ""
        
        # Stereotyp musi być jawnie podany w stylu
        style = f"stereotype={stereotype};"
        
        # Dodaj również kolor na podstawie stereotypu
        if stereotype == 'controller':
            style += "BackColor=-1249301;"
        elif stereotype == 'service':
            style += "BackColor=-3342357;"
        elif stereotype == 'repository':
            style += "BackColor=-1120106;"
        elif stereotype == 'facade':
            style += "BackColor=-6357;"
        elif stereotype == 'utility':
            style += "BackColor=-8355732;"
        elif stereotype == 'gateway':
            style += "BackColor=-16711681;"
        
        return style

    def _get_layer_style(self, layer_name):
        """Zwraca styl dla pakietu warstwy z odpowiednim kolorem tła."""
        # Zamiast sztywno przypisanych kolorów, generuj kolor na podstawie nazwy
        name_hash = hash(layer_name) % 6  # Używamy tylko 6 podstawowych kolorów
        
        layer_colors = [
            "BackColor=-1249281;",  # Jasnoniebieski
            "BackColor=-3342337;",  # Jasnozielony
            "BackColor=-1120086;",  # Jasnopomarańczowy
            "BackColor=-6337;",     # Jasnofioletowy
            "BackColor=-5111808;",  # Czerwonawy
            "BackColor=-8355712;"   # Szary
        ]
        
        base_style = "DUID=unique_id;BorderColor=-1;BorderWidth=1;"
        return base_style + layer_colors[name_hash]

    def _get_local_id(self, obj_id):
        """Generuje lokalny identyfikator dla Enterprise Architect na podstawie ID elementu."""
        if not hasattr(self, '_local_id_counter'):
            self._local_id_counter = 1
        
        if not hasattr(self, '_local_id_map'):
            self._local_id_map = {}
        
        if obj_id not in self._local_id_map:
            self._local_id_map[obj_id] = str(self._local_id_counter)
            self._local_id_counter += 1
        
        return self._local_id_map[obj_id]
    
    def _debug_diagram_objects(self):
        """Wyświetla informacje o elementach dodanych do diagramu."""
        if not self.debug_options.get('elements', False):
            return
            
        print(f"\n--- Elementy diagramu ({len(self.diagram_objects)}) ---")
        log_debug(f"\n--- Elementy diagramu ({len(self.diagram_objects)}) ---")
        
        for obj in self.diagram_objects:
            if isinstance(obj, dict):
                obj_id = obj.get('id', 'brak ID')
                obj_type = obj.get('type', 'nieznany typ')
                obj_name = obj.get('name', '')
                print(f" - {obj_type}: {obj_name} ({obj_id[-6:]})")
                log_debug(f" - {obj_type}: {obj_name} ({obj_id[-6:]})")
            else:
                print(f" - {obj}")
                log_debug(f" - {obj}")
    
    def _format_xml(self, root: ET.Element) -> str:
        """Poprawia nagłówek i formatuje XML do czytelnej postaci."""
        # Zastosuj sanityzację do całego drzewa XML rekurencyjnie
        self._sanitize_tree(root)
        
        xml_string = ET.tostring(root, encoding='unicode', method='xml', xml_declaration=True)
        xml_string_fixed = xml_string.replace("<?xml version='1.0' encoding='unicode'?>", '<?xml version="1.0" encoding="UTF-8"?>')
        dom = xml.dom.minidom.parseString(xml_string_fixed)
        return dom.toprettyxml(indent="  ")
    
    def _sanitize_tree(self, element):
        """Sanityzuje wszystkie atrybuty w całym drzewie XML rekurencyjnie."""
        # Sanityzuj atrybuty bieżącego elementu
        for key, value in list(element.attrib.items()):
            if value is None:
                element.attrib[key] = ""
            elif isinstance(value, bool):
                element.attrib[key] = 'true' if value else 'false'
        
        # Sanityzuj wszystkie elementy potomne
        for child in element:
            self._sanitize_tree(child)

# --- Przykład użycia ---
if __name__ == '__main__':
    import argparse
    import os
    from plantuml_component_parser import PlantUMLComponentParser
    from datetime import datetime
    
    setup_logger('xmi_component_generator.log')
    
    # Utworzenie parsera argumentów z bezpośrednią obsługą plików PlantUML
    parser = argparse.ArgumentParser(description='Generator XMI dla diagramów komponentów')
    parser.add_argument('input_file', nargs='?', default='Diagram komponentów_20250726_085243.puml',
                        help='Plik wejściowy z kodem PlantUML')
    parser.add_argument('--output', '-o', 
                        help='Plik wyjściowy XMI (domyślnie: diagram_komponentow_[timestamp].xmi)')
    
    # Opcje parsowania PlantUML
    parser.add_argument('--parse-debug', '-pd', action='store_true', 
                        help='Włącz debugowanie parsowania')
    parser.add_argument('--parse-relationships', '-pr', action='store_true', 
                        help='Włącz debugowanie relacji w parserze')
    parser.add_argument('--parse-structure', '-ps', action='store_true', 
                        help='Włącz debugowanie struktury w parserze')
    parser.add_argument('--parse-packages', '-pp', action='store_true', 
                        help='Włącz debugowanie pakietów w parserze')
    parser.add_argument('--parse-c4', '-pc4', action='store_true',
                        help='Włącz debugowanie elementów C4 w parserze')
    
    # Opcje generowania XMI
    parser.add_argument('--debug-positioning', '-dp', action='store_true', 
                        help='Włącz debugowanie pozycjonowania elementów')
    parser.add_argument('--debug-elements', '-de', action='store_true', 
                        help='Pokaż listę elementów diagramu')
    parser.add_argument('--debug-processing', '-dpr', action='store_true', 
                        help='Włącz szczegółowe śledzenie przetwarzania elementów')
    parser.add_argument('--debug-relationships', '-dr', action='store_true', 
                        help='Pokaż szczegóły tworzenia relacji')
    parser.add_argument('--debug-xml', '-dx', action='store_true', 
                        help='Włącz debugowanie struktury XML')
    parser.add_argument('--author', '-a', default='XMI Generator', 
                        help='Autor diagramu')
    
    # Parsowanie argumentów
    args = parser.parse_args()
    
    # Konfiguracja opcji debugowania parsera PlantUML
    parse_debug_options = {
        'parsing': args.parse_debug,
        'relationships': args.parse_relationships,
        'structure': args.parse_structure,
        'packages': args.parse_packages,
        'c4': args.parse_c4
    }
    
    # Konfiguracja opcji debugowania generatora XMI
    xmi_debug_options = {
        'positioning': args.debug_positioning,
        'elements': args.debug_elements,
        'processing': args.debug_processing,
        'relationships': args.debug_relationships,
        'xml': args.debug_xml
    }
    
    # Ustawienie nazwy pliku wyjściowego
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        output_file = args.output
    else:
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        output_file = f'{base_name}_{timestamp}.xmi'
    
    try:
        print(f"Wczytywanie pliku PlantUML: {args.input_file}")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
            
        # Parsowanie diagramu PlantUML
        print("Parsowanie diagramu komponentów PlantUML...")
        parser = PlantUMLComponentParser(plantuml_code, parse_debug_options)
        parsed_data = parser.parse()
        
        # Generowanie XMI
        print("Generowanie XMI...")
        generator = XMIComponentGenerator(author=args.author, debug_options=xmi_debug_options)
        
        # Użyj tytułu diagramu jako nazwy, jeśli istnieje
        diagram_name = parsed_data.get('title', '') or os.path.splitext(os.path.basename(args.input_file))[0]
        xmi_content = generator.generate_component_diagram(diagram_name, parsed_data)
        
        # Zapisz XMI do pliku
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xmi_content)
        
        # Wyświetl statystyki
        components_count = len(parsed_data['components'])
        interfaces_count = len(parsed_data['interfaces'])
        packages_count = len(parsed_data['packages'])
        relationships_count = len(parsed_data['relationships'])
        
        print("\n=== Podsumowanie ===")
        log_info("=== Podsumowanie ===")
        print(f"Diagram komponentów: {diagram_name}")
        log_info(f"Diagram komponentów: {diagram_name}")
        print(f"Komponenty: {components_count}")
        log_info(f"Komponenty: {components_count}")
        print(f"Interfejsy: {interfaces_count}")
        log_info(f"Interfejsy: {interfaces_count}")
        print(f"Pakiety: {packages_count}")
        log_info(f"Pakiety: {packages_count}")
        print(f"Relacje: {relationships_count}")
        log_info(f"Relacje: {relationships_count}")
        
        if parsed_data.get('is_c4_diagram'):
            print("Wykryto elementy notacji C4")
            log_info("Wykryto elementy notacji C4")
        
        print(f"\nWygenerowano plik XMI: {output_file}")
        log_info(f"Wygenerowano plik XMI: {output_file}")
        
    except FileNotFoundError:
        print(f"Nie znaleziono pliku: {args.input_file}")
        log_error(f"Nie znaleziono pliku: {args.input_file}")
        print("Podaj poprawną ścieżkę do pliku PlantUML.")
        log_info("Podaj poprawną ścieżkę do pliku PlantUML.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        log_exception(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()
