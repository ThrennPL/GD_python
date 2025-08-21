import re
import sys

try:
    from utils.plantuml.plantuml_model import UMLClass, UMLRelation, UMLEnum, UMLNote
    from utils.logger_utils import setup_logger, log_info, log_error, log_debug, log_exception
except ImportError as e:
    print(f"❌ Krytyczny błąd importu podstawowych modułów: {e}")
    sys.exit(1)


setup_logger('plantuml_class_parser.log')

class PlantUMLClassParser:
    """Parser dla kodu PlantUML - poprawiona wersja z eliminacją duplikatów"""
    
    def __init__(self, debug_options=None):
        self.classes = {}
        self.relations = []
        self.enums = {}  
        self.notes = []
        self.primitive_types = set() 
        self.current_class = None
        self.current_enum = None
        self.note_mode = False
        self.note_target = None
        self.note_lines = []
        self.current_package = None
        self.class_aliases = {} 
        self.debug_options = debug_options or {
            'parsing': False,
            'structure': False,
            'relations': False,
            'notes': False,
        }
    
    def parse(self, plantuml_code: str):
        """Główna metoda parsowania"""
        lines = plantuml_code.strip().split('\n')
        
        # Wyczyść dane przed parsowaniem
        self.classes.clear()
        self.relations.clear()
        self.enums.clear()
        self.notes.clear()
        self.primitive_types.clear() 
        
        for line in lines:
            line = line.strip()
            if self.debug_options.get('parsing'):
                log_debug(f"Przetwarzanie linii: {line}")
                print(f"Przetwarzanie linii: {line}")
            # Pomiń puste linie, komentarze i znaczniki
            if not line or line.startswith("'") or line.startswith("@"):
                continue
            
            # Obsługa pakietów
            if self._parse_package(line):
                continue
                
            # Obsługa tytułów
            if self._parse_title(line):
                continue
            
            # Obsługa notatek wielolinijkowych w toku
            if self.note_mode:
                if self._parse_note_end(line):
                    continue
                else:
                    self.note_lines.append(line)
                    continue
            
            # Próbuj sparsować różne elementy w logicznej kolejności
            if self._parse_note_single_line(line):
                continue
            if self._parse_note_start(line):
                continue
            if self._parse_class_alias(line): 
                continue
            if self._parse_class_definition(line):
                continue
            if self._parse_interface_definition(line):
                continue
            if self._parse_enum_definition(line):
                continue
            if self._parse_class_content(line):
                continue
            if self._parse_relation(line):
                continue
            
            # Jeśli nic nie dopasowano, może to być błąd lub nieobsługiwany element
            print(f"DEBUG: Unrecognized line: {line}")
            log_debug(f"Unrecognized line: {line}")
        
        # Po zakończeniu parsowania wypisz statystyki relacji
        self._print_relation_stats()

        # Dodane debugowanie typów pierwotnych
        log_debug(f"Wykryte typy pierwotne: {', '.join(sorted(self.primitive_types))}")
        print(f"Wykryte typy pierwotne: {', '.join(sorted(self.primitive_types))}")

    def _add_relation_if_not_exists(self, new_relation: UMLRelation) -> bool:
        """
        Dodaje relację tylko jeśli nie istnieje już taka sama.
        Zwraca True jeśli relacja została dodana, False jeśli już istniała.
        """
        for rel in self.relations:
            # Sprawdź czy relacja tego samego typu łącząca te same klasy już istnieje
            if (rel.source == new_relation.source and 
                rel.target == new_relation.target and 
                rel.relation_type == new_relation.relation_type):
                
                # Dla dziedziczenia i realizacji nie potrzebujemy duplikatów
                if rel.relation_type in ['inheritance', 'realization']:
                    return False
                
                # Dla innych typów relacji sprawdź etykietę
                if rel.label == new_relation.label:
                    return False
        
        # Jeśli nie znaleziono duplikatu, dodaj relację
        self.relations.append(new_relation)
        return True

    def _parse_package(self, line: str) -> bool:
        """Parsuje pakiety"""
        if line.startswith('package '):
            # Wyciągnij nazwę pakietu
            match = re.match(r'package\s+"([^"]+)"\s*\{', line)
            if match:
                self.current_package = match.group(1)
                return True
        elif line == '}' and self.current_package:
            self.current_package = None
            return True
        return False

    def _parse_title(self, line: str) -> bool:
        """Parsuje tytuł diagramu"""
        if line.startswith('title '):
            return True
        return False

    def _parse_note_single_line(self, line: str) -> bool:
        """Parsuje notatki jednolinijkowe"""
        match = re.match(r'note\s+\w+\s+of\s+([A-Za-z0-9_ąćęłńóśźźĄĆĘŁŃÓŚŹŻ]+)\s*:\s*(.+)', line)
        if match:
            note_target = match.group(1)
            note_text = match.group(2)
            self.notes.append(UMLNote(note_target, note_text))
            return True
        return False
    
    def _parse_note_start(self, line: str) -> bool:
        """Parsuje początek notatki wielolinijkowej"""
        if line.startswith('note '):
            match = re.match(r'note\s+\w+\s+of\s+([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)', line)
            if match:
                self.note_target = match.group(1)
                self.note_mode = True
                self.note_lines = []
                return True
        return False
    
    def _parse_note_end(self, line: str) -> bool:
        """Parsuje koniec notatki wielolinijkowej"""
        if line == 'end note':
            self.notes.append(UMLNote(self.note_target, '\n'.join(self.note_lines)))
            self.note_mode = False
            self.note_target = None
            self.note_lines = []
            return True
        return False
    
    def _parse_class_alias(self, line: str) -> bool:
        """Parsuje definicję aliasu klasy."""
        alias_pattern = r'([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)\s+as\s+([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)'
        match = re.match(alias_pattern, line)
        
        if match:
            real_name = match.group(1)
            alias = match.group(2)
            self.class_aliases[alias] = real_name
            print(f"DEBUG: Zdefiniowano alias: {alias} -> {real_name}")
            log_info(f"Zdefiniowano alias: {alias} -> {real_name}")
            return True
        return False
    
    def _resolve_class_name(self, name: str) -> str:
        """Rozwiązuje rzeczywistą nazwę klasy z aliasu."""
        return self.class_aliases.get(name, name)

    def _parse_class_definition(self, line: str) -> bool:
        """Parsuje definicję klasy z obsługą extends i implements oraz stereotypów"""
        if not line.startswith('class ') and not line.startswith('abstract class '):
            return False
            
        # Rozszerzony wzorzec dla klasy z extends/implements i stereotypami w różnych formatach
        pattern = r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+(\w+(?:\s*,\s*\w+)*))?(?:\s*<<([^>]+)>>)?(?:\s*\{?)'
        match = re.match(pattern, line)
        
        if match:
            name = match.group(1)
            extends_class = match.group(2)
            implements_interfaces = match.group(3)
            stereotype = match.group(4)
            is_abstract = 'abstract' in line
            
            # Obsługa wielu stereotypów (np. <<entity,table>>)
            if stereotype and ',' in stereotype:
                stereotypes = [s.strip() for s in stereotype.split(',')]
                stereotype = stereotypes[0]  # Używamy pierwszego jako główny
                log_debug(f"Znaleziono wiele stereotypów dla klasy {name}: {stereotypes}")
            
            # Dodatkowe traktowanie dla często używanych stereotypów
            if stereotype:
                log_info(f"Znaleziono stereotyp <<{stereotype}>> dla klasy {name}")
                
                # Sprawdzenie konkretnych stereotypów
                if stereotype.lower() in ['entity', 'table', 'persistent']:
                    log_info(f"Klasa {name} jest encją persystentną")
                elif stereotype.lower() in ['boundary', 'ui', 'view']:
                    log_info(f"Klasa {name} jest elementem interfejsu użytkownika")
                elif stereotype.lower() in ['control', 'service']:
                    log_info(f"Klasa {name} jest serwisem/kontrolerem")
            
            # Utwórz klasę
            uml_class = UMLClass(name, [], [], stereotype, is_abstract)
            self.classes[name] = uml_class
            self.current_class = uml_class
            
            # Dodaj relację dziedziczenia
            if extends_class:
                new_relation = UMLRelation(
                    source=name, 
                    target=extends_class, 
                    relation_type='inheritance', 
                    label=None, 
                    source_multiplicity=None, 
                    target_multiplicity=None
                )
                if self._add_relation_if_not_exists(new_relation):
                    log_debug(f"DEBUG: Found inheritance: {name} extends {extends_class}")
            
            # Dodaj relacje implementacji
            if implements_interfaces:
                interfaces = [iface.strip() for iface in implements_interfaces.split(',')]
                for interface in interfaces:
                    new_relation = UMLRelation(
                        source=name, 
                        target=interface, 
                        relation_type='realization', 
                        label=None, 
                        source_multiplicity=None, 
                        target_multiplicity=None
                    )
                    if self._add_relation_if_not_exists(new_relation):
                        log_debug(f"DEBUG: Found implementation: {name} implements {interface}")
            
            return True
        
        # Fallback - stary wzorzec bez extends/implements
        match = re.match(r'(?:abstract\s+)?class\s+(\w+)(?:\s*<<([^>]+)>>)?(?:\s*\{?)', line)
        if match:
            name = match.group(1)
            stereotype = match.group(2)
            is_abstract = 'abstract' in line
            
            # Obsługa wielu stereotypów w fallback pattern
            if stereotype and ',' in stereotype:
                stereotypes = [s.strip() for s in stereotype.split(',')]
                stereotype = stereotypes[0]  # Używamy pierwszego jako główny
                log_debug(f"Znaleziono wiele stereotypów dla klasy {name}: {stereotypes}")
            
            # Dodatkowa obsługa stereotypów w fallback
            if stereotype:
                log_info(f"Znaleziono stereotyp <<{stereotype}>> dla klasy {name} (fallback)")
            
            uml_class = UMLClass(name, [], [], stereotype, is_abstract)
            self.classes[name] = uml_class
            self.current_class = uml_class
            return True
        
        return False
    
    def _parse_interface_definition(self, line: str) -> bool:
        """Parsuje definicję interfejsu z obsługą extends"""
        if not line.startswith('interface '):
            return False
            
        pattern = r'interface\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s*\{?)'
        match = re.match(pattern, line)
        
        if match:
            name = match.group(1)
            extends_interface = match.group(2)
            
            # Utwórz interfejs
            uml_class = UMLClass(name, [], [], "interface")
            self.classes[name] = uml_class
            self.current_class = uml_class
            
            # Dodaj relację dziedziczenia interfejsu
            if extends_interface:
                new_relation = UMLRelation(
                    source=name, 
                    target=extends_interface, 
                    relation_type='inheritance', 
                    label=None, 
                    source_multiplicity=None, 
                    target_multiplicity=None
                )
                if self._add_relation_if_not_exists(new_relation):
                    log_debug(f"DEBUG: Found interface inheritance: {name} extends {extends_interface}")
            
            return True
        
        return False
    
    def _parse_enum_definition(self, line: str) -> bool:
        """Parsuje definicję enum"""
        if not line.startswith('enum '):
            return False
            
        match = re.match(r'enum\s+(\w+)(?:\s*\{?)', line)
        if match:
            name = match.group(1)
            self.current_enum = UMLEnum(name, [])
            self.enums[name] = self.current_enum
            return True
        
        return False
    
    def _parse_class_content(self, line: str) -> bool:
        """Parsuje zawartość klasy lub enum"""
        # Obsługa nawiasów klamrowych
        if line in ['{', '}']:
            if line == '}':
                self.current_class = None
                self.current_enum = None
            return True
        
        # Obsługa separatorów w klasie (np. --)
        if line == '--' and (self.current_class or self.current_enum):
            return True
        
        # Obsługa zawartości enum
        if self.current_enum:
            if line and line != '--':
                self.current_enum.values.append(line)
            return True
        
        # Obsługa zawartości klasy
        if self.current_class:
            if line != '--':  # Ignoruj separatory
                self._parse_class_member(line)
            return True
        
        return False
    
    def _parse_class_member(self, line: str):
        """Parsuje składnik klasy (atrybut lub metodę)"""
        if not line or line in ['{', '}', '--']:
            return

        # Rozpoznaj modyfikatory {static}, {abstract} itp.
        modifiers = re.findall(r'\{(\w+)\}', line)
        clean_line = re.sub(r'\s*\{[^}]+\}', '', line)

        if '(' in clean_line and ')' in clean_line:
            # Metoda
            method_info = self._parse_method(clean_line, modifiers)
            self.current_class.methods.append(method_info)
        else:
            # Atrybut
            attr_info = self._parse_attribute(clean_line, modifiers)
            self.current_class.attributes.append(attr_info)
            
            # Wykryj i zapisz typ atrybutu do typów pierwotnych
            attr_type_match = re.search(r':\s*(\w+)', clean_line)
            if attr_type_match:
                attr_type = attr_type_match.group(1)
                
                # Sprawdź czy typ nie jest klasą ani enumem
                if attr_type not in self.classes and attr_type not in self.enums:
                    # Dodaj do zbioru typów pierwotnych
                    self.primitive_types.add(attr_type)
                    log_debug(f"Znaleziono typ pierwotny: {attr_type}")

    def _parse_method(self, line: str, modifiers: list) -> dict:
        """Parsuje metodę"""
        return {"signature": line, "modifiers": modifiers}

    def _parse_attribute(self, line: str, modifiers: list) -> dict:
        """Parsuje atrybut"""
        return {"declaration": line, "modifiers": modifiers}
    
    def _ensure_class_exists(self, class_name: str) -> UMLClass:
        """
        Upewnia się, że klasa istnieje w modelu.
        Jeśli nie, tworzy ją jako pustą klasę.
        """
        if class_name not in self.classes and class_name not in self.enums:
            log_info(f"Tworzenie klasy z relacji: {class_name}")
            self.classes[class_name] = UMLClass(name=class_name, attributes=[], methods=[], stereotype=None)
        
        if class_name in self.classes:
            return self.classes[class_name]
        return None  # Jeśli to enum
    
    def _parse_relation(self, line: str) -> bool:
        """Parsuje relacje między klasami z odpowiednią obsługą multiplikatorów"""
        log_debug(f"DEBUG: Parsowanie linii relacji: {line}")

        # Rozpoznaj dziedziczenie (<|-- lub --|>)
        inheritance_pattern = r'(\w+)\s*<\|--\s*(\w+)|(\w+)\s*--\|>\s*(\w+)'
        inheritance_match = re.search(inheritance_pattern, line)

        if inheritance_match:
            if inheritance_match.group(1) and inheritance_match.group(2):
                # A <|-- B (B dziedziczy po A)
                parent, child = inheritance_match.group(1), inheritance_match.group(2)
            else:
                # A --|> B (A dziedziczy po B)
                child, parent = inheritance_match.group(3), inheritance_match.group(4)
                    
            # Rozwiąż aliasy i zapewnij istnienie klas
            child = self._resolve_class_name(child)
            parent = self._resolve_class_name(parent)
            self._ensure_class_exists(child)
            self._ensure_class_exists(parent)
            
            # Wyciągnij etykietę, jeśli istnieje
            multiplicities, label = self._extract_multiplicity_and_label(line)
            
            # UMLRelation(source, target, relation_type, label, source_multiplicity, target_multiplicity)
            new_relation = UMLRelation(
                source=child,
                target=parent,
                relation_type='inheritance',
                label=label,
                source_multiplicity=None,
                target_multiplicity=None
            )
            
            # Dodaj tylko jeśli nie istnieje już taka relacja
            if self._add_relation_if_not_exists(new_relation):
                log_info(f"Znaleziono dziedziczenie: {child} dziedziczy po {parent}")
            return True

        # Sprawdź czy linia zawiera symbol relacji
        relation_symbols = ['-->', '<--', '--|>', '<|--', '--|>', '..|>', '<|..', '*--', 'o--', '--']
        if not any(rel_sym in line for rel_sym in relation_symbols):
            return False
        
        # Wyciągnij surowe stringi liczności i etykietę
        raw_multiplicities, label = self._extract_multiplicity_and_label(line)
                
        # Usuń etykietę i liczności z linii
        line_clean = re.sub(r':\s*.*$', '', line.strip())
        line_clean = re.sub(r'"[0-9*\.]+"\s*', '', line_clean)
        
        patterns = [
            # Specyficzne wzorce dla złożonych relacji
            (r'(\w+)\s*\*\-\-o\s*(\w+)', 'composition_aggregation_left', False), 
            (r'(\w+)\s*o\-\-\*\s*(\w+)', 'aggregation_composition_left', False), 
            
            # Dziedziczenie
            (r'(\w+)\s*<\|\-\-\s*(\w+)', 'inheritance', True),
            (r'(\w+)\s*\-\-\|\>\s*(\w+)', 'inheritance', False),
            (r'(\w+)\s*\|\>\s*(\w+)', 'inheritance', False),
            (r'(\w+)\s*<\|\s*(\w+)', 'inheritance', True),
            
            # Realizacja/Implementacja
            (r'(\w+)\s*<\|\.\.\s*(\w+)', 'realization', True),
            (r'(\w+)\s*\.\.\|\>\s*(\w+)', 'realization', False),
            
            # Kompozycja
            (r'(\w+)\s*\*\-\-\s*(\w+)', 'composition', False),
            (r'(\w+)\s*\-\-\*\s*(\w+)', 'composition', True),
            
            # Agregacja
            (r'(\w+)\s*o\-\-\s*(\w+)', 'aggregation', False),
            (r'(\w+)\s*\-\-o\s*(\w+)', 'aggregation', True),
            
            # Asocjacja
            (r'(\w+)\s*\-\->\s*(\w+)', 'association', False),
            (r'(\w+)\s*<\-\-\s*(\w+)', 'association', True),
            (r'(\w+)\s*\-\-\s*(\w+)', 'association', False),
        ]
        
        for pattern, rel_type, reversed_ in patterns:
            match = re.match(pattern, line_clean)
            if match:
                if reversed_:
                    source, target = match.group(2), match.group(1)
                else:
                    source, target = match.group(1), match.group(2)
                
                source = self._resolve_class_name(source)
                target = self._resolve_class_name(target)
                self._ensure_class_exists(source)
                self._ensure_class_exists(target)
                
                # Ustawienie domyślnych wartości krotności zależnie od typu relacji
                source_mult = None
                target_mult = None
                
                # Domyślne wartości dla kompozycji
                if rel_type == 'composition':
                    source_mult = "1"
                    target_mult = "0..*"
                # Domyślne wartości dla agregacji
                elif rel_type == 'aggregation':
                    source_mult = "0..*"
                    target_mult = "1"
                # Domyślne wartości dla asocjacji
                elif rel_type == 'association':
                    source_mult = "0..1"
                    target_mult = "0..*"
                    
                # Nadpisz domyślne wartości, jeśli podano explicite
                if len(raw_multiplicities) > 0:
                    # Konwersja do formatu Enterprise Architect (z "*" na "-1")
                    s_mult_lower, s_mult_upper = self.parse_multiplicity(raw_multiplicities[0])
                    source_mult = f"{s_mult_lower}..{s_mult_upper}" if s_mult_lower != s_mult_upper else s_mult_lower
                    
                if len(raw_multiplicities) > 1:
                    t_mult_lower, t_mult_upper = self.parse_multiplicity(raw_multiplicities[1])
                    target_mult = f"{t_mult_lower}..{t_mult_upper}" if t_mult_lower != t_mult_upper else t_mult_lower
                
                # Obsługa złożonych typów relacji
                if rel_type == 'composition_aggregation_left':
                    new_relation = UMLRelation(
                        source=source, 
                        target=target, 
                        relation_type='composition', 
                        label=label, 
                        source_multiplicity=source_mult or "1", 
                        target_multiplicity=target_mult or "0..*"
                    )
                    
                    if self._add_relation_if_not_exists(new_relation):
                        log_debug(f"DEBUG: Found complex relation: {source} --composition--> {target} (label: {label}) (source_mult: {source_mult}, target_mult: {target_mult})")
                    return True

                elif rel_type == 'aggregation_composition_left':
                    new_relation = UMLRelation(
                        source=source, 
                        target=target, 
                        relation_type='aggregation', 
                        label=label, 
                        source_multiplicity=source_mult or "0..*", 
                        target_multiplicity=target_mult or "1"
                    )
                    
                    if self._add_relation_if_not_exists(new_relation):
                        log_debug(f"DEBUG: Found complex relation: {source} --aggregation--> {target} (label: {label}) (source_mult: {source_mult}, target_mult: {target_mult})")
                    return True

                # Standardowa obsługa
                new_relation = UMLRelation(
                    source=source, 
                    target=target, 
                    relation_type=rel_type, 
                    label=label, 
                    source_multiplicity=source_mult, 
                    target_multiplicity=target_mult
                )
                
                if self._add_relation_if_not_exists(new_relation):
                    log_debug(f"DEBUG: Found relation: {source} --{rel_type}--> {target} (label: {label}) (source_mult: {source_mult}, target_mult: {target_mult})")
                return True
        
        log_debug(f"DEBUG: Relation not found: {line_clean!r}")
        return False

    def _print_relation_stats(self):
        """Wypisuje statystyki zidentyfikowanych relacji oraz multiplikatory"""
        type_counts = {}
        inheritance_relations = []
        
        for rel in self.relations:
            rel_type = rel.relation_type
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
            
            if rel_type == 'inheritance':
                inheritance_relations.append(f"{rel.source} -> {rel.target}")
        
        log_debug("\n STATYSTYKI RELACJI:")
        print("\nSTATYSTYKI RELACJI:")
        log_debug(f"DEBUG: Całkowita liczba relacji: {len(self.relations)}")
        print(f"Całkowita liczba unikalnych relacji: {len(self.relations)}")

        for rel_type, count in type_counts.items():
            print(f"- {rel_type}: {count}")
            log_debug(f"- {rel_type}: {count}")
        
        # Dodaj sekcję wyświetlającą wszystkie multiplikatory
        log_debug("\nMULTIPLIKATORY W RELACJACH:")
        print("\nMULTIPLIKATORY W RELACJACH:")
        
        # Grupuj relacje z multiplikatorami według typu relacji
        rel_with_multiplicity = {}
        for rel in self.relations:
            if rel.source_multiplicity or rel.target_multiplicity:
                rel_type = rel.relation_type
                if rel_type not in rel_with_multiplicity:
                    rel_with_multiplicity[rel_type] = []
                rel_with_multiplicity[rel_type].append(rel)
        
        # Wyświetl multiplikatory pogrupowane według typu relacji
        for rel_type, rels in rel_with_multiplicity.items():
            print(f"\nTyp relacji: {rel_type}")
            log_debug(f"\nTyp relacji: {rel_type}")
            
            for rel in rels:
                source_mult = rel.source_multiplicity if rel.source_multiplicity else "-"
                target_mult = rel.target_multiplicity if rel.target_multiplicity else "-"
                label = f" '{rel.label}'" if rel.label else ""
                
                # Parsuj multiplikatory dla lepszego wyświetlania
                if source_mult != "-":
                    source_lower, source_upper = self.parse_multiplicity(source_mult)
                    source_upper_disp = "*" if source_upper == "-1" else source_upper
                    source_display = f"{source_lower}..{source_upper_disp}" if source_lower != source_upper else source_lower
                else:
                    source_display = "-"
                    
                if target_mult != "-":
                    target_lower, target_upper = self.parse_multiplicity(target_mult)
                    target_upper_disp = "*" if target_upper == "-1" else target_upper
                    target_display = f"{target_lower}..{target_upper_disp}" if target_lower != target_upper else target_lower
                else:
                    target_display = "-"
                    
                print(f"  {rel.source} [{source_display}] --{label}--> [{target_display}] {rel.target}")
                log_debug(f"  {rel.source} [{source_display}] --{label}--> [{target_display}] {rel.target}")
                
                # Pokaż jak będzie wyglądać w EA (z -1 zamiast *)
                log_debug(f"  EA format: [{source_lower}..{source_upper}] -> [{target_lower}..{target_upper}]")
        
        log_debug("\nRELACJE DZIEDZICZENIA:")
        print("\nRELACJE DZIEDZICZENIA:")
        for rel in inheritance_relations:
            print(f"- {rel}")
            log_debug(f"- {rel}")

    @staticmethod
    def parse_multiplicity(mult_str):
        """
        Parsuje string krotności do wartości dolnej i górnej.
        Kompatybilna z formatem XMI oczekiwanym przez Enterprise Architect.
        
        Args:
            mult_str: String reprezentujący krotność (np. "0..1", "*", "1..*")
            
        Returns:
            tuple: (dolna granica, górna granica) gdzie "*" jest zamienione na "-1" dla EA
        """
        if not mult_str:
            return "1", "1"
                
        if mult_str == "*":
            return "0", "-1"  # Zauważ -1 zamiast "*" dla EA
            
        if ".." in mult_str:
            parts = mult_str.split("..")
            lower = parts[0].strip()
            upper = parts[1].strip()
            # Zamień "*" na "-1" dla górnej granicy
            if upper == "*":
                upper = "-1"
            return lower, upper
            
        # Pojedyncza wartość
        return mult_str, mult_str

    def _extract_multiplicity_and_label(self, line: str) -> tuple[list[str], str]:
        """Wyciąga surowe stringi liczności i etykietę z linii relacji PlantUML."""
        # Wzorzec na liczności w cudzysłowach
        mult_pattern = r'"([0-9*\.]+)"'
        multiplicities = re.findall(mult_pattern, line)

        # Usunięcie liczności z linii
        line_without_mult = re.sub(mult_pattern, '', line)

        label_match = re.search(r':\s*(?:(?:")([^"]+)(?:")|([^\s:]+))', line_without_mult)
        
        label = None
        if label_match:
            if label_match.group(1):
                label = label_match.group(1).strip()
            elif label_match.group(2):
                label = label_match.group(2).strip()

        return multiplicities, label

    def get_parsed_data(self):
        """Zwraca sparsowane dane w formacie słownika"""
        return {
            'classes': {name: {
                'attributes': cls.attributes,
                'methods': cls.methods,
                'stereotype': cls.stereotype,
                'is_abstract': cls.is_abstract
            } for name, cls in self.classes.items()},
            'enums': {name: {
                'values': enum.values
            } for name, enum in self.enums.items()},
            'relations': [{
                'source': rel.source,
                'target': rel.target,
                'relation_type': rel.relation_type,
                'label': rel.label,
                'source_multiplicity': rel.source_multiplicity,
                'target_multiplicity': rel.target_multiplicity
            } for rel in self.relations],
            'notes': [{
                'target': note.target,
                'text': note.text
            } for note in self.notes]
        }
        
    
# --- Przykład użycia ---
if __name__ == '__main__':
    import argparse
    import pprint
    from datetime import datetime

    parser = argparse.ArgumentParser(description='Parser diagramów klas PlantUML')
    parser.add_argument('input_file', nargs='?', default='diagram_klas_PlantUML.puml',
                        help='Plik wejściowy z kodem PlantUML')
    parser.add_argument('--output', '-o', help='Plik wyjściowy JSON (domyślnie: generowana nazwa)')
    parser.add_argument('--debug', '-d', action='store_true', help='Włącz tryb debugowania')
    parser.add_argument('--parsing', '-p', action='store_true', help='Debugowanie procesu parsowania')
    parser.add_argument('--structure', '-s', action='store_true', help='Debugowanie struktury')
    parser.add_argument('--relations', '-r', action='store_true', help='Debugowanie relacji')
    parser.add_argument('--notes', '-n', action='store_true', help='Debugowanie notatek')
    args = parser.parse_args()

    debug_options = {
        'parsing': args.parsing or args.debug,
        'structure': args.structure or args.debug,
        'relations': args.relations or args.debug,
        'notes': args.notes or args.debug,
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  
    input_file = args.input_file
    output_file = args.output or f'test_class_{timestamp}.json'

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        parser = PlantUMLClassParser(debug_options=debug_options)
        parser.parse(plantuml_code)
        
        # Przygotuj dane do wyświetlenia
        parsed_data = parser.get_parsed_data()

        print("--- Wynik Parsowania ---")
        log_info("Wynik parsowania:")
        pprint.pprint(parsed_data)
        
        # Opcjonalnie zapisz do pliku JSON
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        print(f"\nWynik zapisany do: {output_file}")
        log_info(f"Wynik zapisany do: {output_file}")
        
    except FileNotFoundError:
        print(f"Nie znaleziono pliku: {input_file}")
        log_error(f"Nie znaleziono pliku: {input_file}")
        print("Utwórz przykładowy plik PlantUML lub zmień nazwę pliku w kodzie.")
        log_info("Utwórz przykładowy plik PlantUML lub zmień nazwę pliku w kodzie.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        log_exception(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()