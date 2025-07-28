import re
import pprint
import uuid
from datetime import datetime
import os
from logger_utils import log_debug, log_info, log_error, log_exception, log_warning, setup_logger

setup_logger("plantuml_component_parser.log")

class PlantUMLComponentParser:
    """
    Parsuje tekstowy opis diagramu komponentów PlantUML
    i przekształca go w strukturyzowane dane.
    Obsługuje zarówno standardowe diagramy komponentów UML jak i notację C4.
    """

    def __init__(self, plantuml_code: str, debug_options=None):
        """
        Inicjalizuje parser.

        Args:
            plantuml_code: Ciąg znaków zawierający kod diagramu PlantUML.
            debug_options: Słownik z opcjami debugowania.
        """
        self.code = plantuml_code
        self.title = ""
        self.components = {}      # Słownik komponentów {id: component_data}
        self.interfaces = {}      # Słownik interfejsów {id: interface_data}
        self.packages = {}        # Słownik pakietów {id: package_data}
        self.relationships = []   # Lista relacji między elementami
        self.notes = []           # Lista notatek
        self.flow = []            # Lista wszystkich elementów w kolejności występowania
        self.current_package = None  # Aktualnie przetwarzany pakiet
        self.boundaries = {}      # Słownik granic C4 (boundary)
        self.is_c4_diagram = False # Czy wykryto elementy C4
        self.c4_element_ids = {}  # Mapa ID C4 na ID wewnętrzne
        
        # Opcje debugowania
        self.debug_options = debug_options or {
            'parsing': False,       # Debugowanie procesu parsowania
            'relationships': True,  # Szczegółowe informacje o relacjach
            'structure': False,     # Informacje o strukturze komponentów
            'packages': True,       # Informacje o pakietach
            'c4': False,           # Debugowanie elementów C4
        }

    def _generate_id(self):
        """Generuje unikalny identyfikator dla elementu."""
        return f"id_{uuid.uuid4().hex[:8]}"

    def parse(self):
        """
        Główna metoda parsująca, która analizuje kod linia po linii.
        """
        if self.debug_options.get('parsing'):
            log_debug("Rozpoczynam parsowanie kodu diagramu komponentów PlantUML")
            print("Rozpoczynam parsowanie kodu diagramu komponentów PlantUML")
        
        lines = self.code.strip().split('\n')
        
        # Sprawdź, czy diagram używa biblioteki C4
        for line in lines:
            if "!include" in line and "C4" in line:
                self.is_c4_diagram = True
                if self.debug_options.get('c4'):
                    log_debug("Wykryto diagram C4 na podstawie include C4")
                    print("Wykryto diagram C4 na podstawie include C4")
                break
        
        # Stos do śledzenia zagnieżdżonych struktur (pakiety, granice)
        structure_stack = []
        
        # Rejestr połączeń - do debugowania i weryfikacji poprawności
        connections = []
        
        # Ostatnio przetworzony element - do śledzenia relacji
        last_element = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Pomiń puste linie, komentarze i znaczniki start/end
            if not line or line.startswith("'") or line in ["@startuml", "@enduml"] or line.startswith("!"):
                i += 1
                continue
            
            if self.debug_options.get('parsing'):
                log_debug(f"Przetwarzanie linii {i+1}: {line}")
                print(f"Przetwarzanie linii {i+1}: {line}")

            # Parsowanie tytułu
            if line.startswith('title'):
                match = re.match(r'^title\s+(.*)$', line)
                if match:
                    self.title = match.group(1).strip()
                    if self.debug_options.get('parsing'):
                        log_debug(f"Znaleziono tytuł: {self.title}")
                        print(f"Znaleziono tytuł: {self.title}")
                    i += 1
                    continue

            # Parsowanie elementów C4
            c4_element_match = re.match(r'^(Person|System|Container|Component|Boundary|Enterprise|System_Boundary|Container_Boundary|Enterprise_Boundary|Person_Ext|System_Ext)\(([^,]+),\s*"([^"]*)"(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?\)', line)
            if c4_element_match:
                element_type = c4_element_match.group(1).lower()
                element_id = c4_element_match.group(2).strip()
                element_name = c4_element_match.group(3).strip() if c4_element_match.group(3) else element_id
                element_tech = c4_element_match.group(4).strip() if c4_element_match.group(4) else ""
                element_desc = c4_element_match.group(5).strip() if c4_element_match.group(5) else ""
                element_sprite = c4_element_match.group(6).strip() if c4_element_match.group(6) and c4_element_match.group(6) else ""
                
                self.is_c4_diagram = True
                
                c4_element_id = self._generate_id()
                
                # Zapisz mapowanie ID C4 na wewnętrzne ID
                self.c4_element_ids[element_id] = c4_element_id
                
                # Sprawdź, czy jest to granica (boundary)
                if 'boundary' in element_type:
                    # Obsługa granic C4 (podobne do pakietów)
                    boundary = {
                        'type': 'c4_boundary',
                        'c4_type': element_type,
                        'name': element_name,
                        'c4_id': element_id,
                        'id': c4_element_id,
                        'technology': element_tech,
                        'description': element_desc,
                        'components': [],
                        'interfaces': [],
                        'parent_package': self.current_package
                    }
                    
                    self.packages[c4_element_id] = boundary
                    self.flow.append(boundary)
                    
                    # Zapisz poprzedni pakiet/granicę na stosie i ustaw nowy jako aktualny
                    if self.current_package:
                        structure_stack.append(self.current_package)
                    self.current_package = c4_element_id
                    
                    if self.debug_options.get('c4'):
                        log_debug(f"Dodano granicę C4 {element_type}: {element_name}")
                        print(f"Dodano granicę C4 {element_type}: {element_name}")
                    
                    # Sprawdź czy następna linia to "{"
                    j = i + 1
                    while j < len(lines) and (not lines[j].strip() or lines[j].strip().startswith("'")):
                        j += 1
                    
                    if j < len(lines) and lines[j].strip() == '{':
                        i = j + 1  # Przejdź za "{"
                    else:
                        i += 1  # Przejdź do następnej linii
                    continue
                    
                else:
                    # Zwykły element C4 (Person, System, Container, Component)
                    c4_element = {
                        'type': 'c4_element',
                        'c4_type': element_type,
                        'c4_id': element_id,
                        'name': element_name,
                        'technology': element_tech,
                        'description': element_desc,
                        'sprite': element_sprite,
                        'id': c4_element_id,
                        'package': self.current_package
                    }
                    
                    self.components[c4_element_id] = c4_element
                    self.flow.append(c4_element)
                    
                    # Dodaj element C4 do aktualnego pakietu/granicy, jeśli istnieje
                    if self.current_package:
                        self.packages[self.current_package]['components'].append(c4_element_id)
                    
                    if self.debug_options.get('c4'):
                        log_debug(f"Dodano element C4 {element_type}: {element_name}")
                        print(f"Dodano element C4 {element_type}: {element_name}")
                    
                    i += 1
                    continue

            # Parsowanie relacji C4
            c4_rel_match = re.match(r'^Rel(?:\w*)\(([^,]+),\s*([^,]+),\s*"([^"]*)"(?:,\s*"([^"]*)")?(?:,\s*[^,]*)?(?:,\s*"([^"]*)")?\)', line)
            if c4_rel_match:
                source_id = c4_rel_match.group(1).strip()
                target_id = c4_rel_match.group(2).strip()
                label = c4_rel_match.group(3).strip() if c4_rel_match.group(3) else ""
                technology = c4_rel_match.group(4).strip() if c4_rel_match.group(4) else ""
                direction = c4_rel_match.group(5).strip() if c4_rel_match.group(5) else ""
                
                self.is_c4_diagram = True
                
                relation = {
                    'type': 'c4_relationship',
                    'source': source_id,
                    'target': target_id,
                    'label': label,
                    'technology': technology,
                    'direction': direction,
                    'id': self._generate_id()
                }
                
                self.relationships.append(relation)
                self.flow.append(relation)
                
                if self.debug_options.get('c4'):
                    log_debug(f"Dodano relację C4: {source_id} -> {target_id} : {label}")
                    print(f"Dodano relację C4: {source_id} -> {target_id} : {label}")
                
                i += 1
                continue

                # Parsowanie aktorów i elementów zewnętrznych (cloud, database, etc.)
            actor_match = re.match(r'^(?:actor|cloud|database|queue)\s+\"?([^"]+)\"?\s*(?:as\s+(\w+))?', line)
            if actor_match:
                actor_name = actor_match.group(1).strip()
                actor_name = actor_name.strip('"') # Usuń cudzysłowy, jeśli występują
                actor_alias = actor_match.group(2).strip() if actor_match.group(2) else None
                
                element_type = line.split(' ')[0]  # Typ elementu (actor, cloud, database, queue)
                actor_id = self._generate_id()
                
                actor = {
                    'type': element_type,
                    'name': actor_name,
                    'alias': actor_alias,
                    'id': actor_id,
                    'package': self.current_package
                }
                    
                # Dodaj do komponentów, żeby można było je łączyć relacjami
                self.components[actor_id] = actor
                self.flow.append(actor)
                    
                if self.debug_options.get('structure'):
                    log_debug(f"Dodano element {element_type}: {actor_name}" + 
                            (f" (alias: {actor_alias})" if actor_alias else ""))
                    print(f"Dodano element {element_type}: {actor_name}" + 
                        (f" (alias: {actor_alias})" if actor_alias else ""))
                
                i += 1
                continue


            # Parsowanie pakietów (rozpoczęcie)
            package_start = re.match(r'^package\s+"([^"]+)"\s*(?:\{|as\s+(\w+)\s*\{)?$', line)
            if package_start:
                package_name = package_start.group(1)
                package_alias = package_start.group(2) if package_start.group(2) else None
                package_id = self._generate_id()
                
                package = {
                    'type': 'package',
                    'name': package_name,
                    'alias': package_alias,
                    'id': package_id,
                    'components': [],
                    'interfaces': [],
                    'parent_package': self.current_package
                }
                
                self.packages[package_id] = package
                self.flow.append(package)
                
                # Zapisz poprzedni pakiet na stosie i ustaw nowy jako aktualny
                if self.current_package:
                    structure_stack.append(self.current_package)
                self.current_package = package_id
                
                if self.debug_options.get('packages'):
                    log_debug(f"Rozpoczęto pakiet: {package_name}" + 
                              (f" (alias: {package_alias})" if package_alias else ""))
                    print(f"Rozpoczęto pakiet: {package_name}" + 
                          (f" (alias: {package_alias})" if package_alias else ""))
                
                i += 1
                continue

            # Parsowanie pakietów (zakończenie)
            if line == '}' and (self.current_package or structure_stack):
                if self.debug_options.get('packages') or self.debug_options.get('c4'):
                    current_type = self.packages[self.current_package]['type'] if self.current_package else "unknown"
                    current_name = self.packages[self.current_package]['name'] if self.current_package else "unknown"
                    log_debug(f"Zakończono {current_type}: {current_name}")
                    print(f"Zakończono {current_type}: {current_name}")
                
                # Przywróć poprzedni pakiet/granicę ze stosu, jeśli istnieje
                if structure_stack:
                    self.current_package = structure_stack.pop()
                else:
                    self.current_package = None
                
                i += 1
                continue

            # Parsowanie komponentów
            component_match = re.match(r'^(?:component\s+)?(?:"([^"]+)"|(?:\[([^\[\]]+)\]))(?:\s+<<([^>]+)>>)?(?:\s+as\s+(\w+))?', line)
            if component_match:
                if component_match.group(1):  # Format z cudzysłowami: component "Nazwa" as alias
                    component_name = component_match.group(1).strip()
                    component_stereotype = component_match.group(3) if component_match.group(3) else None
                    component_alias = component_match.group(4) if component_match.group(4) else None
                else:  # Format z nawiasami: component [Nazwa] as alias
                    component_name = component_match.group(2).strip()
                    component_stereotype = component_match.group(3) if component_match.group(3) else None
                    component_alias = component_match.group(4) if component_match.group(4) else None
                
                # DODANE: Wykrywanie stereotypów w formacie skrótowym <<stereotyp>>
                if component_stereotype and component_stereotype.startswith("<<") and component_stereotype.endswith(">>"):
                    component_stereotype = component_stereotype[2:-2]  # Usuń << i >>

                # Usuń nawiasy kwadratowe z nazwy, jeśli są
                if component_name.startswith('[') and component_name.endswith(']'):
                    component_name = component_name[1:-1]
                
                component_name = component_name.strip('"')  # Usuń cudzysłowy, jeśli występują
                
                # DODANE: Logowanie oryginalnych danych z kodu PlantUML
                if self.debug_options.get('structure'):
                    log_debug(f"Wykryto komponent w PlantUML: '{component_name}'" + 
                            (f" <<{component_stereotype}>>" if component_stereotype else "") + 
                            (f" (alias: {component_alias})" if component_alias else ""))
                
                component_id = self._generate_id()
                component = {
                    'type': 'component',
                    'name': component_name,
                    'alias': component_alias,
                    'stereotype': component_stereotype,
                    'id': component_id,
                    'package': self.current_package
                }
                
                self.components[component_id] = component
                self.flow.append(component)
                
                # Dodaj komponent do aktualnego pakietu, jeśli istnieje
                if self.current_package:
                    self.packages[self.current_package]['components'].append(component_id)
                
                if self.debug_options.get('structure'):
                    log_debug(f"Dodano komponent: {component_name}" + 
                            (f" <<{component_stereotype}>>" if component_stereotype else "") +
                            (f" (alias: {component_alias})" if component_alias else ""))
                
                # Zapamiętaj ostatni element
                last_element = component
                
                i += 1
                continue

            # Parsowanie interfejsów
            interface_match = re.match(r'^(?:interface\s+|^\(\()([^()]+)(?:\)\))?(?:\s+as\s+(\w+))?', line)
            if interface_match:
                interface_name = interface_match.group(1).strip()
                
                # Sprawdź czy interfejs jest w formacie I[Nazwa]
                if interface_name.startswith('I[') and interface_name.endswith(']'):
                    interface_name = interface_name[2:-1].strip()  # Usuń I[ i ]
                
                # Napraw nazwy interfejsów - usuń znaki cudzysłowów
                interface_name = interface_name.strip('"')
                
                # Usuń "as iservice" z nazwy, jeśli zostało dołączone
                if " as " in interface_name:
                    parts = interface_name.split(" as ")
                    interface_name = parts[0].strip()
                    # Jeśli nie ma aliasu z grupy 2, użyj tego z nazwy
                    if not interface_match.group(2):
                        interface_alias = parts[1].strip()
                    else:
                        interface_alias = interface_match.group(2).strip()
                else:
                    interface_alias = interface_match.group(2).strip() if interface_match.group(2) else None                
                interface_id = self._generate_id()
                interface = {
                    'type': 'interface',
                    'name': interface_name,
                    'alias': interface_alias,
                    'id': interface_id,
                    'package': self.current_package
                }
                
                self.interfaces[interface_id] = interface
                self.flow.append(interface)
                
                # Dodaj interfejs do aktualnego pakietu, jeśli istnieje
                if self.current_package:
                    self.packages[self.current_package]['interfaces'].append(interface_id)
                
                if self.debug_options.get('structure'):
                    log_debug(f"Dodano interfejs: {interface_name}" + 
                              (f" (alias: {interface_alias})" if interface_alias else ""))
                    print(f"Dodano interfejs: {interface_name}" + 
                          (f" (alias: {interface_alias})" if interface_alias else ""))
                
                # Zapamiętaj ostatni element
                last_element = interface
                
                i += 1
                continue

            # Parsowanie komponentów wewnątrz pakietu
            if self.current_package and re.match(r'^\[([^\]]+)\](?:\s+<<([^>]+)>>)?(?:\s+as\s+(\w+))?', line.strip()):
                comp_match = re.match(r'^\[([^\]]+)\](?:\s+<<([^>]+)>>)?(?:\s+as\s+(\w+))?', line.strip())
                if comp_match:
                    comp_name = comp_match.group(1).strip()
                    comp_stereotype = comp_match.group(2) if len(comp_match.groups()) > 1 and comp_match.group(2) else None
                    comp_alias = comp_match.group(3) if len(comp_match.groups()) > 2 and comp_match.group(3) else None
                    
                    # Usuń nawiasy kwadratowe, jeśli są częścią nazwy
                    if comp_name.startswith('[') and comp_name.endswith(']'):
                        comp_name = comp_name[1:-1].strip()
                    
                    comp_name = comp_name.strip('"')  # Usuń cudzysłowy, jeśli występują
                    comp_id = self._generate_id()
                    
                    component = {
                        'type': 'component',
                        'name': comp_name,
                        'alias': comp_alias,
                        'stereotype': comp_stereotype,
                        'id': comp_id,
                        'package': self.current_package
                    }
                    
                    self.components[comp_id] = component
                    self.flow.append(component)
                    
                    # Dodaj komponent do aktualnego pakietu
                    self.packages[self.current_package]['components'].append(comp_id)
                    
                    if self.debug_options.get('structure'):
                        log_debug(f"Dodano komponent w pakiecie: {comp_name}" + 
                                (f" <<{comp_stereotype}>>" if comp_stereotype else "") + 
                                (f" (alias: {comp_alias})" if comp_alias else ""))
                        print(f"Dodano komponent w pakiecie: {comp_name}" + 
                            (f" <<{comp_stereotype}>>" if comp_stereotype else "") + 
                            (f" (alias: {comp_alias})" if comp_alias else ""))
                    
                    i += 1
                    continue

            # Parsowanie relacji
            relation_match = re.match(r'^([^\s<>-]+)\s*([-\.]+)(?:>|\)|\(|\|)(?:>|\)|\(|\|)?\s*([^\s<>-]+)(?:\s*:\s*(.+))?$', line)
            if relation_match:
                source_name = relation_match.group(1).strip()
                relation_type = relation_match.group(2).strip()
                target_name = relation_match.group(3).strip()
                label = relation_match.group(4).strip() if relation_match.group(4) else ""
                
                # Usuń nawiasy kwadratowe i cudzysłowy z nazw elementów
                if source_name.startswith('[') and source_name.endswith(']'):
                    source_name = source_name[1:-1]
                if target_name.startswith('[') and target_name.endswith(']'):
                    target_name = target_name[1:-1]
                
                source_name = source_name.strip('"')
                target_name = target_name.strip('"')
                
                relation = {
                    'type': 'relationship',
                    'source': source_name,
                    'target': target_name,
                    'relation_type': relation_type,
                    'label': label,
                    'id': self._generate_id()
                }
                
                self.relationships.append(relation)
                self.flow.append(relation)
                
                if self.debug_options.get('relationships'):
                    log_debug(f"Dodano relację: {source_name} {relation_type}> {target_name}" + 
                            (f" : {label}" if label else ""))
                    print(f"Dodano relację: {source_name} {relation_type}> {target_name}" + 
                        (f" : {label}" if label else ""))
                
                i += 1
                continue

            # Parsowanie notatek
            note_match = re.match(r'^note\s+(left|right|top|bottom)\s+of\s+([^:]+)\s*:\s*(.*)$', line)
            if note_match:
                position = note_match.group(1).strip()
                target = note_match.group(2).strip()
                content = note_match.group(3).strip()
                
                # Sprawdź, czy nota jest wieloliniowa
                if not content.endswith('end note'):
                    # Zbierz wszystkie linie notatki
                    note_content = [content]
                    j = i + 1
                    while j < len(lines) and 'end note' not in lines[j]:
                        note_content.append(lines[j].strip())
                        j += 1
                    
                    if j < len(lines) and 'end note' in lines[j]:
                        # Usuń 'end note' z ostatniej linii, jeśli jest częścią linii
                        last_line = lines[j].strip()
                        if last_line != 'end note':
                            note_content.append(last_line.replace('end note', '').strip())
                        i = j  # Przesuwamy indeks za 'end note'
                    
                    content = '\n'.join(note_content)
                
                note = {
                    'type': 'note',
                    'position': position,
                    'target': target,
                    'content': content,
                    'id': self._generate_id(),
                    'package': self.current_package
                }
                
                self.notes.append(note)
                self.flow.append(note)
                
                if self.debug_options.get('parsing'):
                    log_debug(f"Dodano notatkę {position} of {target}: {content[:30]}...")
                    print(f"Dodano notatkę {position} of {target}: {content[:30]}...")
                
                i += 1
                continue
            
            # Jeśli żaden wzorzec nie pasował, po prostu przejdź do następnej linii
            i += 1
        
        self._add_components_to_packages()
        # Wykonaj post-processing
        self.post_process()

        # Po zakończeniu parsowania, sprawdź i zaloguj statystyki i problemy
        self._debug_parser_results()

        return {
            'title': self.title,
            'is_c4_diagram': self.is_c4_diagram,
            'components': self.components,
            'interfaces': self.interfaces,
            'packages': self.packages,
            'relationships': self.relationships,
            'notes': self.notes,
            'flow': self.flow,
            'c4_element_ids': self.c4_element_ids
        }
    
    def _add_component(self, name, stereotype, alias, package_id):
        """
        Dodaje komponent do diagramu i przypisuje go do pakietu.
        
        Args:
            name: Nazwa komponentu
            stereotype: Stereotyp komponentu (np. 'controller', 'service' itp.)
            alias: Alias dla komponentu używany w relacjach
            package_id: ID pakietu, do którego należy przypisać komponent
        
        Returns:
            str: ID utworzonego komponentu
        """
        component_id = self._generate_id()
        
        self.components[component_id] = {
            'type': 'component',
            'name': name,
            'alias': alias,
            'stereotype': stereotype,
            'id': component_id,
            'package': package_id
        }
        
        # Dodaj komponent do listy komponentów pakietu
        if package_id in self.packages:
            if 'components' not in self.packages[package_id]:
                self.packages[package_id]['components'] = []
            self.packages[package_id]['components'].append(component_id)
            
            if self.debug_options.get('structure'):
                log_debug(f"Dodano komponent do pakietu: {name} <<{stereotype}>> (alias: {alias})")
        
        return component_id

    def _add_components_to_packages(self):
        """Dodaje komponenty do pakietów tylko jeśli pakiety są puste."""
        
        # Sprawdź, czy diagram ma już zdefiniowane pakiety
        if not self.packages:
            # Jeśli nie ma żadnych pakietów, utwórz domyślny pakiet "Main"
            default_pkg_id = self._generate_id()
            self.packages[default_pkg_id] = {
                'type': 'package',
                'name': 'Main',
                'alias': 'main',
                'id': default_pkg_id,
                'components': [],
                'interfaces': [],
                'parent_package': None
            }
            
            # Przypisz wszystkie komponenty bez pakietu do domyślnego pakietu
            for comp_id, comp in self.components.items():
                if not comp.get('package'):
                    comp['package'] = default_pkg_id
                    self.packages[default_pkg_id]['components'].append(comp_id)
        
        # Słownik standardowych stereotypów dla różnych rodzajów komponentów
        default_stereotypes = {
            'api': 'gateway',
            'web': 'controller', 
            'app': 'controller',
            'mobile': 'controller',
            'ui': 'controller',
            'service': 'service',
            'repository': 'repository',
            'dao': 'repository',
            'cache': 'utility',
            'adapter': 'facade',
            'integration': 'facade'
        }
        
        # Sprawdź komponenty bez stereotypów i przypisz im stereotypy na podstawie nazwy
        for comp_id, comp in self.components.items():
            if not comp.get('stereotype'):
                comp_name_lower = comp['name'].lower()
                # Sprawdź czy nazwa komponentu zawiera jedno ze słów kluczowych
                for keyword, stereotype in default_stereotypes.items():
                    if keyword in comp_name_lower:
                        comp['stereotype'] = stereotype
                        if self.debug_options.get('structure'):
                            log_debug(f"Przypisano automatycznie stereotyp {stereotype} do komponentu {comp['name']}")
                        break
        
        # ZMIANA: USUNIĘCIE automatycznego dodawania domyślnych komponentów do pustych pakietów
        # Zachowanie oryginalnych komponentów z kodu PlantUML jest kluczowe dla działania relacji
        empty_packages = []
        for pkg_id, pkg in self.packages.items():
            if not pkg.get('components'):
                log_debug(f"Pakiet '{pkg['name']}' jest pusty - nie dodawaj domyślnych komponentów")
                empty_packages.append(pkg_id)
        
        # Jeżeli zachodzi potrzeba oznaczenia pustych pakietów, można to zrobić bez nadpisywania
        for pkg_id in empty_packages:
            self.packages[pkg_id]['is_empty'] = True

    def _resolve_element_reference(self, reference):
        """Rozwiązuje referencję elementu (nazwa, alias lub C4 ID) do jego ID."""
        # Usuń cudzysłowy i nawiasy kwadratowe, jeśli występują
        reference = reference.strip('"')
        if reference.startswith('[') and reference.endswith(']'):
            reference = reference[1:-1].strip()
        
        # NOWE: Dodaj diagnostykę dla śledzenia problemu
        if self.debug_options.get('relationships'):
            log_debug(f"Rozwiązywanie referencji dla elementu: '{reference}'")
        
        # Szukaj najpierw po aliasach (najczęściej używane w relacjach)
        for comp_id, comp in self.components.items():
            if comp.get('alias') == reference:
                if self.debug_options.get('relationships'):
                    log_debug(f"  Znaleziono komponent po aliasie: {comp['name']}")
                return comp_id
        
        # Szukaj w interfejsach po aliasach
        for intf_id, intf in self.interfaces.items():
            if intf.get('alias') == reference:
                if self.debug_options.get('relationships'):
                    log_debug(f"  Znaleziono interfejs po aliasie: {intf['name']}")
                return intf_id
        
        # NOWE: Szukaj w pakietach po aliasach
        for pkg_id, pkg in self.packages.items():
            if pkg.get('alias') == reference:
                if self.debug_options.get('relationships'):
                    log_debug(f"  Znaleziono pakiet po aliasie: {pkg['name']}")
                return pkg_id
        
        # Szukaj po nazwach
        for comp_id, comp in self.components.items():
            if comp['name'] == reference:
                if self.debug_options.get('relationships'):
                    log_debug(f"  Znaleziono komponent po nazwie: {comp['name']}")
                return comp_id
        
        # Szukaj w interfejsach
        for intf_id, intf in self.interfaces.items():
            if intf['name'] == reference:
                if self.debug_options.get('relationships'):
                    log_debug(f"  Znaleziono interfejs po nazwie: {intf['name']}")
                return intf_id
        
        # Szukaj w pakietach po nazwie
        for pkg_id, pkg in self.packages.items():
            if pkg['name'] == reference:
                if self.debug_options.get('relationships'):
                    log_debug(f"  Znaleziono pakiet po nazwie: {pkg['name']}")
                return pkg_id
        
        # Sprawdź czy to ID elementu C4 
        if reference in self.c4_element_ids:
            if self.debug_options.get('relationships'):
                log_debug(f"  Znaleziono element C4 po ID: {reference}")
            return self.c4_element_ids[reference]
        
        # Ostatnia próba - szukaj z nawiasami kwadratowymi
        reference_with_brackets = f"[{reference}]"
        for comp_id, comp in self.components.items():
            if comp['name'] == reference_with_brackets:
                if self.debug_options.get('relationships'):
                    log_debug(f"  Znaleziono komponent po nazwie z nawiasami: {comp['name']}")
                return comp_id
        
        # NOWE: Jeśli nie znaleziono, wyświetl diagnostykę
        if self.debug_options.get('relationships'):
            log_debug(f"  Nie znaleziono elementu dla referencji: '{reference}'")
            log_debug("  Dostępne aliasy komponentów: " + str([comp.get('alias') for comp in self.components.values() if comp.get('alias')]))
            log_debug("  Dostępne aliasy interfejsów: " + str([intf.get('alias') for intf in self.interfaces.values() if intf.get('alias')]))
            log_debug("  Dostępne aliasy pakietów: " + str([pkg.get('alias') for pkg in self.packages.values() if pkg.get('alias')]))
        
        return None
    
    def post_process(self):
        """
        Funkcja wykonywana po parsowaniu w celu rozwiązania referencji i weryfikacji poprawności.
        """
        # Rozwiązanie referencji w relacjach
        for relation in self.relationships:
            source_id = self._resolve_element_reference(relation['source'])
            target_id = self._resolve_element_reference(relation['target'])
            
            if source_id:
                relation['source_id'] = source_id
                source_type = next((e['type'] for e in self.flow if e.get('id') == source_id), None)
                relation['source_type'] = source_type
            else:
                log_warning(f"Nie znaleziono elementu źródłowego: {relation['source']}")
            
            if target_id:
                relation['target_id'] = target_id
                target_type = next((e['type'] for e in self.flow if e.get('id') == target_id), None)
                relation['target_type'] = target_type
            else:
                log_warning(f"Nie znaleziono elementu docelowego: {relation['target']}")
        
        # Rozwiązanie referencji w notatkach
        for note in self.notes:
            target_id = self._resolve_element_reference(note['target'])
            if target_id:
                note['target_id'] = target_id
                target_type = next((e['type'] for e in self.flow if e.get('id') == target_id), None)
                note['target_type'] = target_type
            else:
                log_warning(f"Nie znaleziono elementu docelowego notatki: {note['target']}")
        
        # Weryfikacja zagnieżdżenia pakietów
        self._verify_package_nesting()
        
        return self.flow
    
    def _verify_package_nesting(self):
        """Weryfikuje poprawność zagnieżdżenia pakietów."""
        for pkg_id, pkg in self.packages.items():
            parent_id = pkg.get('parent_package')
            if parent_id and parent_id not in self.packages:
                log_warning(f"Pakiet {pkg['name']} ma nieprawidłowe odwołanie do pakietu nadrzędnego")
                pkg['parent_package'] = None
    
    def _debug_parser_results(self):
        """Analizuje i loguje wyniki parsowania oraz potencjalne problemy."""
        if not self.debug_options.get('parsing'):
            return
            
        # Statystyki
        stats = self.get_statistics()
        log_debug("\n=== STATYSTYKI PARSOWANIA ===")
        print("\n=== STATYSTYKI PARSOWANIA ===")
        
        for key, value in stats.items():
            if isinstance(value, dict):
                log_debug(f"  {key}:")
                print(f"  {key}:")
                for subkey, subvalue in value.items():
                    log_debug(f"    {subkey}: {subvalue}")
                    print(f"    {subkey}: {subvalue}")
            else:
                log_debug(f"  {key}: {value}")
                print(f"  {key}: {value}")
        
        # Wykrywanie potencjalnych problemów
        log_debug("\n=== POTENCJALNE PROBLEMY ===")
        print("\n=== POTENCJALNE PROBLEMY ===")
        
        # 1. Sprawdź nierozwiązane referencje w relacjach
        unresolved_relations = [r for r in self.relationships 
                               if not r.get('source_id') or not r.get('target_id')]
        
        if unresolved_relations:
            msg = f"Znaleziono {len(unresolved_relations)} relacji z nierozwiązanymi referencjami"
            log_warning(msg)
            print(f"⚠️ {msg}")
            
            for relation in unresolved_relations:
                missing = []
                if not relation.get('source_id'):
                    missing.append(f"source: {relation['source']}")
                if not relation.get('target_id'):
                    missing.append(f"target: {relation['target']}")
                
                log_warning(f"Nierozwiązane referencje w relacji: {', '.join(missing)}")
                print(f"   - {', '.join(missing)}")
        
        # 2. Sprawdź nierozwiązane referencje w notatkach
        unresolved_notes = [n for n in self.notes if not n.get('target_id')]
        
        if unresolved_notes:
            msg = f"Znaleziono {len(unresolved_notes)} notatek z nierozwiązanymi referencjami"
            log_warning(msg)
            print(f"⚠️ {msg}")
            
            for note in unresolved_notes:
                log_warning(f"Nierozwiązana referencja w notatce: target: {note['target']}")
                print(f"   - target: {note['target']}")
        
        # 3. Sprawdź izolowane komponenty (bez relacji)
        all_related_components = set()
        for relation in self.relationships:
            if relation.get('source_id'):
                all_related_components.add(relation['source_id'])
            if relation.get('target_id'):
                all_related_components.add(relation['target_id'])
        
        isolated_components = [comp_id for comp_id in self.components 
                              if comp_id not in all_related_components]
        
        if isolated_components:
            msg = f"Znaleziono {len(isolated_components)} izolowanych komponentów (bez relacji)"
            log_debug(msg)
            print(f"ℹ️ {msg}")
            
            for comp_id in isolated_components:
                comp_name = self.components[comp_id]['name']
                log_debug(f"Izolowany komponent: {comp_name}")
                print(f"   - {comp_name}")

    def get_statistics(self):
        """Zwraca statystyki diagramu."""
        # Komponenty według pakietów
        components_by_package = {}
        for pkg_id, pkg in self.packages.items():
            components_by_package[pkg['name']] = len(pkg.get('components', []))
        
        # Typy relacji
        relation_types = {}
        for rel in self.relationships:
            if rel['type'] == 'c4_relationship':
                rel_type = 'c4_relation'
            else:
                rel_type = rel.get('relation_type', 'unknown')
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
        
        # Liczba elementów C4 według typów
        c4_element_types = {}
        for comp_id, comp in self.components.items():
            if comp.get('c4_type'):
                c4_type = comp['c4_type']
                c4_element_types[c4_type] = c4_element_types.get(c4_type, 0) + 1
        
        stats = {
            'total_components': len(self.components),
            'total_interfaces': len(self.interfaces),
            'total_packages': len(self.packages),
            'total_relationships': len(self.relationships),
            'total_notes': len(self.notes),
            'components_by_package': components_by_package,
            'relationship_types': relation_types,
            'is_c4_diagram': self.is_c4_diagram
        }
        
        if self.is_c4_diagram:
            stats['c4_element_types'] = c4_element_types
        
        return stats

if __name__ == '__main__':
    print("Parser diagramów komponentów PlantUML")
    import argparse
    setup_logger('plantuml_component_parser.log')
    
    # Konfiguracja parsera argumentów
    parser = argparse.ArgumentParser(description='Parser diagramów komponentów PlantUML')
    parser.add_argument('input_file', nargs='?', default='Diagram komponentów_20250726_085243.puml',
                        help='Plik wejściowy z kodem PlantUML')
    parser.add_argument('--output', '-o', help='Plik wyjściowy JSON (domyślnie: generowana nazwa)')
    parser.add_argument('--debug', '-d', action='store_true', help='Włącz tryb debugowania')
    parser.add_argument('--all', '-a', action='store_true', help='Włącz wszystkie opcje debugowania')
    parser.add_argument('--parsing', '-p', action='store_true', help='Debugowanie procesu parsowania')
    parser.add_argument('--relationships', '-r', action='store_true', help='Debugowanie relacji')
    parser.add_argument('--structure', '-s', action='store_true', help='Debugowanie struktury komponentów')
    parser.add_argument('--packages', '-pkg', action='store_true', help='Debugowanie pakietów')
    parser.add_argument('--c4', '-c4', action='store_true', help='Debugowanie elementów C4')
    
    # Parsowanie argumentów
    args = parser.parse_args()
    
    # Konfiguracja opcji debugowania na podstawie argumentów
    debug_options = {
        'parsing': args.parsing or args.all or args.debug,
        'relationships': args.relationships or args.all or args.debug,
        'structure': args.structure or args.all or args.debug,
        'packages': args.packages or args.all or args.debug,
        'c4': args.c4 or args.all or args.debug,
    }
    
    # Ustawienie nazwy pliku wyjściowego
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        output_file = args.output
    else:
        output_file = f'component_diagram_{timestamp}.json'
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        # Inicjalizacja i uruchomienie parsera
        parser = PlantUMLComponentParser(plantuml_code, debug_options)
        parsed_data = parser.parse()

        print("--- Wynik Parsowania ---")
        log_info("Rozpoczęto parsowanie diagramu komponentów PlantUML.")
        log_info(f"Parsowanie zakończone. Tytuł: {parsed_data['title']}")
        
        if parsed_data['is_c4_diagram']:
            print("Wykryto diagram w notacji C4")
            log_info("Wykryto diagram w notacji C4")
        
        if args.debug or args.all:
            pprint.pprint(parsed_data)

        # Wyświetl statystyki
        stats = parser.get_statistics()
        print("\n--- Statystyki ---")
        log_info("Wyświetlanie statystyk diagramu komponentów.")
        log_info(f"Statystyki: {stats}")
        pprint.pprint(stats)

        # Zapisz do pliku JSON
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        print(f"\nWynik zapisany do: {output_file}")
        log_info(f"Wynik zapisany do: {output_file}")
        
    except FileNotFoundError:
        print(f"Nie znaleziono pliku: {args.input_file}")
        log_error(f"Nie znaleziono pliku: {args.input_file}")
        print("Utwórz przykładowy plik PlantUML lub podaj poprawną ścieżkę.")
        log_info("Utwórz przykładowy plik PlantUML lub podaj poprawną ścieżkę.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        log_exception(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()
