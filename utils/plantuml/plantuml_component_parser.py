import re
import pprint
import uuid
from datetime import datetime
import os
from utils.logger_utils import log_debug, log_info, log_error, log_exception, log_warning, setup_logger

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
        self.components = {}
        self.interfaces = {}
        self.packages = {}
        self.relationships = []
        self.notes = []
        self.flow = []
        self.current_package = None
        self.boundaries = {}
        self.is_c4_diagram = False
        self.c4_element_ids = {}
        self.diagram_mode = "auto"
        self.strategy = None

        self.debug_options = debug_options or {
            'parsing': False,
            'relationships': True,
            'structure': False,
            'packages': True,
            'c4': False,
        }

    def _generate_id(self):
        """Generuje unikalny identyfikator dla elementu."""
        return f"id_{uuid.uuid4().hex[:8]}"

    def parse(self):
        """Analizuje kod PlantUML linia po linii i zwraca strukturyzowane dane."""
        if self.debug_options.get('parsing'):
            log_debug("Rozpoczynam parsowanie kodu diagramu komponentów PlantUML")
            print("Rozpoczynam parsowanie kodu diagramu komponentów PlantUML")

        lines = self.code.strip().split('\n')

        self.diagram_mode = self._detect_diagram_mode(lines)
        self.is_c4_diagram = self.diagram_mode == 'c4'

        if self.debug_options.get('parsing'):
            log_debug(f"Wybrana strategia parsowania: {self.diagram_mode}")
            print(f"Wybrana strategia parsowania: {self.diagram_mode}")

        self.strategy = self._get_strategy()
        self.strategy.initialize_state(self)
        self.strategy.process(lines)
        self.strategy.finalize()

        self._convert_gateway_components_to_interfaces()
        self._add_components_to_packages()
        self.post_process()
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

    def _detect_diagram_mode(self, lines):
        """Określa typ diagramu na podstawie kodu PlantUML."""
        for raw in lines:
            line = raw.strip()
            if line.startswith('!') and 'C4' in line:
                return 'c4'

        c4_patterns = (
            r'^Rel',
            r'^(Person(?:_Ext)?|System(?:_Ext)?|Container(?:Db)?|Component(?:Db|Queue)?|Boundary|Enterprise)',
            r'^System_Boundary',
            r'^Container_Boundary',
            r'^Enterprise_Boundary'
        )
        for raw in lines:
            line = raw.strip()
            for pattern in c4_patterns:
                if re.match(pattern, line):
                    return 'c4'
        return 'classic'

    def _convert_gateway_components_to_interfaces(self):
        """Konwertuje komponenty o stereotypie gateway na interfejsy."""
        gateway_ids = [
            comp_id for comp_id, comp in list(self.components.items())
            if (comp.get('stereotype') or '').lower() == 'gateway'
        ]

        if not gateway_ids:
            return

        for comp_id in gateway_ids:
            component = self.components.pop(comp_id)
            interface_entry = {
                'type': 'interface',
                'name': component.get('name'),
                'alias': component.get('alias'),
                'id': comp_id,
                'package': component.get('package'),
                'stereotype': component.get('stereotype')
            }

            self.interfaces[comp_id] = interface_entry

            package_id = component.get('package')
            if package_id and package_id in self.packages:
                pkg = self.packages[package_id]
                components_list = pkg.get('components', [])
                if comp_id in components_list:
                    components_list.remove(comp_id)
                pkg.setdefault('interfaces', [])
                if comp_id not in pkg['interfaces']:
                    pkg['interfaces'].append(comp_id)

            for element in self.flow:
                if element.get('id') == comp_id:
                    element['type'] = 'interface'
                    element['stereotype'] = component.get('stereotype')
                    break

            if self.debug_options.get('structure'):
                log_debug(f"Przekonwertowano komponent '{component.get('name')}' na interfejs gateway")

    def _get_strategy(self):
        """Zwraca instancję strategii odpowiadającej wykrytemu trybowi diagramu."""
        if self.diagram_mode == 'c4':
            return C4ComponentParserStrategy()
        return ClassicComponentParserStrategy()
    
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


class ComponentParserStrategy:
    """Wspólna baza dla strategii parsowania diagramów komponentów."""

    RELATION_TOKENS = (
        ('..|>', 'realization', 'forward'),
        ('--|>', 'inheritance', 'forward'),
        ('<|--', 'inheritance', 'backward'),
        ('<|..', 'realization', 'backward'),
        ('<--', 'association', 'backward'),
        ('<-', 'association', 'backward'),
        ('..>', 'dependency', 'forward'),
        ('<..', 'dependency', 'backward'),
        ('-->', 'association', 'forward'),
        ('->', 'association', 'forward'),
        ('--', 'association', 'undirected'),
        ('..', 'dependency', 'undirected')
    )

    PACKAGE_KEYWORDS = ('package', 'frame', 'node', 'folder', 'cloud')
    ACTOR_KEYWORDS = ('actor', 'cloud', 'database', 'queue', 'entity', 'control', 'boundary')

    def initialize_state(self, parser):
        self.parser = parser
        self.structure_stack = []
        self.last_element = None
        parser.current_package = None

    def process(self, lines):
        raise NotImplementedError

    def finalize(self):
        return None

    def _should_skip_line(self, line):
        return (
            not line or
            line.startswith("'") or
            line in ["@startuml", "@enduml"] or
            line.startswith('!')
        )

    def _log_parsing(self, index, line):
        if self.parser.debug_options.get('parsing'):
            log_debug(f"Przetwarzanie linii {index + 1}: {line}")
            print(f"Przetwarzanie linii {index + 1}: {line}")

    def _handle_common_line(self, lines, index):
        handlers = (
            self._handle_title,
            self._handle_actor,
            self._handle_package_start,
            self._handle_package_end,
            self._handle_component,
            self._handle_interface,
            self._handle_inline_component,
            self._handle_relationship,
            self._handle_note,
        )

        for handler in handlers:
            handled, new_index = handler(lines, index)
            if handled:
                return True, new_index
        return False, index

    def _handle_title(self, lines, index):
        line = lines[index].strip()
        if not line.startswith('title'):
            return False, index

        match = re.match(r'^title\s+(.*)$', line)
        if match:
            self.parser.title = match.group(1).strip()
            if self.parser.debug_options.get('parsing'):
                log_debug(f"Znaleziono tytuł: {self.parser.title}")
                print(f"Znaleziono tytuł: {self.parser.title}")
        return True, index + 1

    def _handle_actor(self, lines, index):
        line = lines[index].strip()
        parts = line.split()
        if not parts or parts[0] not in self.ACTOR_KEYWORDS:
            return False, index

        actor_match = re.match(r'^(\w+)\s+"?([^"]+)"?(?:\s+as\s+([\w\.]+))?', line)
        if not actor_match:
            return False, index

        element_type = actor_match.group(1)
        actor_name = actor_match.group(2).strip().strip('"')
        actor_alias = actor_match.group(3).strip() if actor_match.group(3) else None

        actor_id = self.parser._generate_id()
        actor_stereotype = None
        if element_type == 'database':
            actor_stereotype = 'database'

        actor = {
            'type': element_type,
            'name': actor_name,
            'alias': actor_alias,
            'stereotype': actor_stereotype,
            'id': actor_id,
            'package': self.parser.current_package
        }

        self.parser.components[actor_id] = actor
        self.parser.flow.append(actor)

        if self.parser.current_package:
            pkg = self.parser.packages.get(self.parser.current_package)
            if pkg is not None:
                pkg.setdefault('components', []).append(actor_id)

        if self.parser.debug_options.get('structure'):
            details = f" (alias: {actor_alias})" if actor_alias else ""
            log_debug(f"Dodano element {element_type}: {actor_name}{details}")
            print(f"Dodano element {element_type}: {actor_name}{details}")

        return True, index + 1

    def _handle_package_start(self, lines, index):
        line = lines[index].strip()
        if not any(line.startswith(keyword) for keyword in self.PACKAGE_KEYWORDS):
            return False, index

        package_match = re.match(r'^(package|frame|node|folder|cloud)\s+"([^"]+)"\s*(?:as\s+(\w+))?\s*\{?$', line)
        if not package_match:
            return False, index

        package_type = package_match.group(1)
        package_name = package_match.group(2)
        package_alias = package_match.group(3) if package_match.group(3) else None

        package_id = self.parser._generate_id()
        package = {
            'type': 'package',
            'package_kind': package_type,
            'name': package_name,
            'alias': package_alias,
            'id': package_id,
            'components': [],
            'interfaces': [],
            'parent_package': self.parser.current_package
        }

        self.parser.packages[package_id] = package
        self.parser.flow.append(package)

        self._push_scope(package_id)

        if self.parser.debug_options.get('packages'):
            alias_info = f" (alias: {package_alias})" if package_alias else ""
            log_debug(f"Rozpoczęto {package_type}: {package_name}{alias_info}")
            print(f"Rozpoczęto {package_type}: {package_name}{alias_info}")

        # Jeśli bieżąca linia nie kończy się nawiasem otwierającym, poszukaj go w kolejnych liniach
        next_index = index + 1
        if not line.rstrip().endswith('{'):
            j = next_index
            while j < len(lines) and (not lines[j].strip() or lines[j].strip().startswith("'")):
                j += 1
            if j < len(lines) and lines[j].strip() == '{':
                next_index = j + 1
            else:
                next_index = index + 1

        return True, next_index

    def _handle_package_end(self, lines, index):
        line = lines[index].strip()
        if line != '}' or (self.parser.current_package is None and not self.structure_stack):
            return False, index

        current_id = self.parser.current_package
        if self.parser.debug_options.get('packages') or self.parser.debug_options.get('c4'):
            if current_id and current_id in self.parser.packages:
                current_pkg = self.parser.packages[current_id]
                pkg_type = current_pkg.get('type', 'unknown')
                pkg_name = current_pkg.get('name', 'unknown')
            else:
                pkg_type = 'unknown'
                pkg_name = 'unknown'
            log_debug(f"Zakończono {pkg_type}: {pkg_name}")
            print(f"Zakończono {pkg_type}: {pkg_name}")

        self._pop_scope()
        return True, index + 1

    def _handle_component(self, lines, index):
        line = lines[index].strip()
        if any(token in line for token in ['--', '->', '..', '<-', '<|']):
            return False, index

        component_match = re.match(
            r'^(?:component\s+)?(?:"([^"]+)"|\[([^\[\]]+)\]|([\w\.]+))(?:\s+<<(.*?)>>)?(?:\s+as\s+([\w\.]+))?$',
            line
        )
        if not component_match:
            return False, index

        if component_match.group(1):
            component_name = component_match.group(1).strip()
        elif component_match.group(2):
            component_name = component_match.group(2).strip()
        else:
            component_name = component_match.group(3).strip()

        component_stereotype = component_match.group(4)
        component_alias = component_match.group(5)

        if component_stereotype and component_stereotype.startswith('<<') and component_stereotype.endswith('>>'):
            component_stereotype = component_stereotype[2:-2]

        component_name = component_name.strip('"')
        if component_name.startswith('[') and component_name.endswith(']'):
            component_name = component_name[1:-1]

        component_id = self.parser._generate_id()
        component = {
            'type': 'component',
            'name': component_name,
            'alias': component_alias,
            'stereotype': component_stereotype,
            'id': component_id,
            'package': self.parser.current_package
        }

        self.parser.components[component_id] = component
        self.parser.flow.append(component)

        if self.parser.current_package:
            self.parser.packages[self.parser.current_package]['components'].append(component_id)

        if self.parser.debug_options.get('structure'):
            alias_info = f" (alias: {component_alias})" if component_alias else ""
            stereo_info = f" <<{component_stereotype}>>" if component_stereotype else ""
            log_debug(f"Dodano komponent: {component_name}{stereo_info}{alias_info}")
            print(f"Dodano komponent: {component_name}{stereo_info}{alias_info}")

        self.last_element = component
        return True, index + 1

    def _handle_interface(self, lines, index):
        line = lines[index].strip()
        interface_match = re.match(r'^(?:interface\s+|^\(\()([^()]+)(?:\)\))?(?:\s+as\s+(\w+))?', line)
        if not interface_match:
            return False, index

        interface_name = interface_match.group(1).strip()
        if interface_name.startswith('I[') and interface_name.endswith(']'):
            interface_name = interface_name[2:-1].strip()
        interface_name = interface_name.strip('"')

        if ' as ' in interface_name and not interface_match.group(2):
            name_part, alias_part = interface_name.split(' as ', 1)
            interface_name = name_part.strip()
            interface_alias = alias_part.strip()
        else:
            interface_alias = interface_match.group(2).strip() if interface_match.group(2) else None

        interface_name = interface_name.strip('"')

        interface_id = self.parser._generate_id()
        interface = {
            'type': 'interface',
            'name': interface_name,
            'alias': interface_alias,
            'id': interface_id,
            'package': self.parser.current_package
        }

        self.parser.interfaces[interface_id] = interface
        self.parser.flow.append(interface)

        if self.parser.current_package:
            self.parser.packages[self.parser.current_package]['interfaces'].append(interface_id)

        if self.parser.debug_options.get('structure'):
            alias_info = f" (alias: {interface_alias})" if interface_alias else ""
            log_debug(f"Dodano interfejs: {interface_name}{alias_info}")
            print(f"Dodano interfejs: {interface_name}{alias_info}")

        self.last_element = interface
        return True, index + 1

    def _handle_inline_component(self, lines, index):
        line = lines[index].strip()
        if self.parser.current_package is None:
            return False, index

        inline_match = re.match(r'^\[([^\]]+)\](?:\s+<<(.*?)>>)?(?:\s+as\s+([\w\.]+))?', line)
        if not inline_match:
            return False, index

        comp_name = inline_match.group(1).strip()
        comp_stereotype = inline_match.group(2) if inline_match.group(2) else None
        comp_alias = inline_match.group(3) if inline_match.group(3) else None

        if comp_stereotype:
            comp_stereotype = comp_stereotype.strip()
            if comp_stereotype.startswith('<<') and comp_stereotype.endswith('>>'):
                comp_stereotype = comp_stereotype[2:-2]
        if comp_alias:
            comp_alias = comp_alias.strip()

        if comp_name.startswith('[') and comp_name.endswith(']'):
            comp_name = comp_name[1:-1].strip()
        comp_name = comp_name.strip('"')

        comp_id = self.parser._generate_id()
        component = {
            'type': 'component',
            'name': comp_name,
            'alias': comp_alias,
            'stereotype': comp_stereotype,
            'id': comp_id,
            'package': self.parser.current_package
        }

        self.parser.components[comp_id] = component
        self.parser.flow.append(component)
        self.parser.packages[self.parser.current_package]['components'].append(comp_id)

        if self.parser.debug_options.get('structure'):
            alias_info = f" (alias: {comp_alias})" if comp_alias else ""
            stereo_info = f" <<{comp_stereotype}>>" if comp_stereotype else ""
            log_debug(f"Dodano komponent w pakiecie: {comp_name}{stereo_info}{alias_info}")
            print(f"Dodano komponent w pakiecie: {comp_name}{stereo_info}{alias_info}")

        return True, index + 1

    def _handle_relationship(self, lines, index):
        line = lines[index].strip()
        label = None

        if ':' in line:
            relation_part, label_part = line.split(':', 1)
            label = label_part.strip()
        else:
            relation_part = line

        for token, rel_type, direction in self.RELATION_TOKENS:
            if token in relation_part:
                source_part, target_part = relation_part.split(token, 1)
                source = self._normalize_reference(source_part)
                target = self._normalize_reference(target_part)
                if direction == 'backward':
                    source, target = target, source

                if not source or not target:
                    continue

                relation = {
                    'type': 'relationship',
                    'source': source,
                    'target': target,
                    'relation_type': rel_type,
                    'raw_arrow': token,
                    'direction': direction,
                    'label': label or '',
                    'id': self.parser._generate_id()
                }

                self.parser.relationships.append(relation)
                self.parser.flow.append(relation)

                if self.parser.debug_options.get('relationships'):
                    label_info = f" : {relation['label']}" if relation['label'] else ''
                    log_debug(f"Dodano relację: {relation['source']} {token} {relation['target']}{label_info}")
                    print(f"Dodano relację: {relation['source']} {token} {relation['target']}{label_info}")

                return True, index + 1

        return False, index

    def _handle_note(self, lines, index):
        line = lines[index].strip()
        note_match = re.match(r'^note\s+(left|right|top|bottom)\s+of\s+([^:]+)\s*:\s*(.*)$', line)
        if not note_match:
            return False, index

        position = note_match.group(1).strip()
        target = note_match.group(2).strip()
        content = note_match.group(3).strip()

        note_lines = [content]
        j = index + 1
        if not content.endswith('end note'):
            while j < len(lines) and 'end note' not in lines[j]:
                note_lines.append(lines[j].strip())
                j += 1
            if j < len(lines):
                end_line = lines[j].strip()
                if end_line != 'end note':
                    note_lines.append(end_line.replace('end note', '').strip())
                j += 1
        else:
            note_lines[-1] = content.replace('end note', '').strip()

        note = {
            'type': 'note',
            'position': position,
            'target': target,
            'content': '\n'.join([line for line in note_lines if line]),
            'id': self.parser._generate_id(),
            'package': self.parser.current_package
        }

        self.parser.notes.append(note)
        self.parser.flow.append(note)

        if self.parser.debug_options.get('parsing'):
            log_debug(f"Dodano notatkę {position} of {target}: {note['content'][:30]}...")
            print(f"Dodano notatkę {position} of {target}: {note['content'][:30]}...")

        return True, j if j > index + 1 else index + 1

    def _normalize_reference(self, reference):
        ref = reference.strip()
        if ref.startswith('[') and ref.endswith(']'):
            ref = ref[1:-1]
        ref = ref.strip('"')
        return ref.strip()

    def _push_scope(self, package_id):
        if self.parser.current_package:
            self.structure_stack.append(self.parser.current_package)
        self.parser.current_package = package_id

    def _pop_scope(self):
        if self.structure_stack:
            self.parser.current_package = self.structure_stack.pop()
        else:
            self.parser.current_package = None


class C4ComponentParserStrategy(ComponentParserStrategy):
    """Strategia parsowania diagramów C4."""

    def process(self, lines):
        parser = self.parser
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if self._should_skip_line(line):
                i += 1
                continue

            self._log_parsing(i, line)

            handled, next_index = self._handle_c4_element(lines, i)
            if handled:
                i = next_index
                continue

            handled, next_index = self._handle_c4_relation(lines, i)
            if handled:
                i = next_index
                continue

            handled, next_index = self._handle_common_line(lines, i)
            if handled:
                i = next_index
                continue

            i += 1

    def _handle_c4_element(self, lines, index):
        line = lines[index].strip()
        parser = self.parser
        element_match = re.match(
            r'^(Person(?:_Ext)?|System(?:_Ext)?|Container(?:Db)?|Component(?:Db|Queue)?|Boundary|Enterprise|System_Boundary|Container_Boundary|Enterprise_Boundary)\(([^,]+),\s*"([^"]*)"(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?\)',
            line
        )
        if not element_match:
            return False, index

        element_type = element_match.group(1).lower()
        element_id = element_match.group(2).strip()
        element_name = element_match.group(3).strip() if element_match.group(3) else element_id
        element_tech = element_match.group(4).strip() if element_match.group(4) else ""
        element_desc = element_match.group(5).strip() if element_match.group(5) else ""
        element_sprite = element_match.group(6).strip() if element_match.group(6) else ""

        parser.is_c4_diagram = True

        generated_id = parser._generate_id()
        parser.c4_element_ids[element_id] = generated_id

        if 'boundary' in element_type:
            boundary = {
                'type': 'c4_boundary',
                'c4_type': element_type,
                'name': element_name,
                'c4_id': element_id,
                'id': generated_id,
                'technology': element_tech,
                'description': element_desc,
                'components': [],
                'interfaces': [],
                'parent_package': parser.current_package
            }

            parser.packages[generated_id] = boundary
            parser.flow.append(boundary)
            self._push_scope(generated_id)

            if parser.debug_options.get('c4'):
                log_debug(f"Dodano granicę C4 {element_type}: {element_name}")
                print(f"Dodano granicę C4 {element_type}: {element_name}")

            next_index = index + 1
            j = next_index
            while j < len(lines) and (not lines[j].strip() or lines[j].strip().startswith("'")):
                j += 1
            if j < len(lines) and lines[j].strip() == '{':
                next_index = j + 1
            return True, next_index

        c4_element = {
            'type': 'c4_element',
            'c4_type': element_type,
            'c4_id': element_id,
            'name': element_name,
            'technology': element_tech,
            'description': element_desc,
            'sprite': element_sprite,
            'id': generated_id,
            'package': parser.current_package
        }

        parser.components[generated_id] = c4_element
        parser.flow.append(c4_element)

        if parser.current_package:
            parser.packages[parser.current_package]['components'].append(generated_id)

        if parser.debug_options.get('c4'):
            log_debug(f"Dodano element C4 {element_type}: {element_name}")
            print(f"Dodano element C4 {element_type}: {element_name}")

        return True, index + 1

    def _handle_c4_relation(self, lines, index):
        line = lines[index].strip()
        parser = self.parser
        relation_match = re.match(
            r'^Rel(?:\w*)\(([^,]+),\s*([^,]+),\s*"([^"]*)"(?:,\s*"([^"]*)")?(?:,\s*[^,]*)?(?:,\s*"([^"]*)")?\)',
            line
        )
        if not relation_match:
            return False, index

        source_id = relation_match.group(1).strip()
        target_id = relation_match.group(2).strip()
        label = relation_match.group(3).strip() if relation_match.group(3) else ""
        technology = relation_match.group(4).strip() if relation_match.group(4) else ""
        direction = relation_match.group(5).strip() if relation_match.group(5) else ""

        parser.is_c4_diagram = True

        relation = {
            'type': 'c4_relationship',
            'source': source_id,
            'target': target_id,
            'label': label,
            'technology': technology,
            'direction': direction,
            'id': parser._generate_id()
        }

        parser.relationships.append(relation)
        parser.flow.append(relation)

        if parser.debug_options.get('c4'):
            log_debug(f"Dodano relację C4: {source_id} -> {target_id} : {label}")
            print(f"Dodano relację C4: {source_id} -> {target_id} : {label}")

        return True, index + 1


class ClassicComponentParserStrategy(ComponentParserStrategy):
    """Strategia parsowania klasycznych diagramów komponentów."""

    def process(self, lines):
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if self._should_skip_line(line):
                i += 1
                continue

            self._log_parsing(i, line)

            handled, next_index = self._handle_common_line(lines, i)
            if handled:
                i = next_index
                continue

            i += 1

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
