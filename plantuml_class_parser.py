from plantuml_model import UMLClass, UMLRelation, UMLEnum, UMLNote
import re

class PlantUMLParser:
    """Parser dla kodu PlantUML - poprawiona wersja"""
    
    def __init__(self):
        self.classes = {}
        self.relations = []
        self.enums = {}  
        self.notes = []
        self.current_class = None
        self.current_enum = None
        self.note_mode = False
        self.note_target = None
        self.note_lines = []
        self.current_package = None
    
    def parse(self, plantuml_code: str):
        """Główna metoda parsowania"""
        lines = plantuml_code.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
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
    
    def _parse_class_definition(self, line: str) -> bool:
        """Parsuje definicję klasy z obsługą extends i implements"""
        if not line.startswith('class ') and not line.startswith('abstract class '):
            return False
            
        # Wzorzec dla klasy z extends/implements
        pattern = r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+(\w+(?:\s*,\s*\w+)*))?(?:\s*<<(\w+)>>)?(?:\s*\{?)'
        match = re.match(pattern, line)
        
        if match:
            name = match.group(1)
            extends_class = match.group(2)
            implements_interfaces = match.group(3)
            stereotype = match.group(4)
            is_abstract = 'abstract' in line
            
            # Utwórz klasę
            uml_class = UMLClass(name, [], [], stereotype, is_abstract)
            self.classes[name] = uml_class
            self.current_class = uml_class
            
            # Dodaj relację dziedziczenia
            if extends_class:
                self.relations.append(UMLRelation(
                    source=name, 
                    target=extends_class, 
                    relation_type='inheritance', 
                    label=None, 
                    source_multiplicity=None, 
                    target_multiplicity=None
                ))
                print(f"DEBUG: Found inheritance: {name} extends {extends_class}")
            
            # Dodaj relacje implementacji
            if implements_interfaces:
                interfaces = [iface.strip() for iface in implements_interfaces.split(',')]
                for interface in interfaces:
                    self.relations.append(UMLRelation(
                        source=name, 
                        target=interface, 
                        relation_type='realization', 
                        label=None, 
                        source_multiplicity=None, 
                        target_multiplicity=None
                    ))
                    print(f"DEBUG: Found implementation: {name} implements {interface}")
            
            return True
        
        # Fallback - stary wzorzec bez extends/implements
        match = re.match(r'(?:abstract\s+)?class\s+(\w+)(?:\s*<<(\w+)>>)?(?:\s*\{?)', line)
        if match:
            name = match.group(1)
            stereotype = match.group(2)
            is_abstract = 'abstract' in line
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
                self.relations.append(UMLRelation(
                    source=name, 
                    target=extends_interface, 
                    relation_type='inheritance', 
                    label=None, 
                    source_multiplicity=None, 
                    target_multiplicity=None
                ))
                print(f"DEBUG: Found interface inheritance: {name} extends {extends_interface}")
            
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

    def _parse_method(self, line: str, modifiers: list) -> dict:
        """Parsuje metodę"""
        return {"signature": line, "modifiers": modifiers}

    def _parse_attribute(self, line: str, modifiers: list) -> dict:
        """Parsuje atrybut"""
        return {"declaration": line, "modifiers": modifiers}
    
    def _parse_relation(self, line: str) -> bool:
        """Parsuje relacje między klasami"""
        print(f"DEBUG: Parsowanie linii relacji: {line}")

        # Rozpoznaj dziedziczenie (<|-- lub --|>)
        # Rozpoznaj dziedziczenie (<|-- lub --|>)
        inheritance_pattern = r'(\w+)\s*<\|--\s*(\w+)|(\w+)\s*--\|>\s*(\w+)'
        inheritance_match = re.search(inheritance_pattern, line)

        if inheritance_match:
            if inheritance_match.group(1) and inheritance_match.group(2):
                # A <|-- B (B dziedziczy po A)
                parent, child = inheritance_match.group(1), inheritance_match.group(2)
            else:
                # A --|> B (B dziedziczy po A)
                parent, child = inheritance_match.group(3), inheritance_match.group(4)
                    
            print(f"Znaleziono dziedziczenie: {child} dziedziczy po {parent}")
            
            # Wyciągnij etykietę, jeśli istnieje
            multiplicities, label = self._extract_multiplicity_and_label(line)
            
            # UMLRelation(source, target, relation_type, source_multiplicity, target_multiplicity, label)
            # W tym przypadku source=child, target=parent (dziecko dziedziczy po rodzicu)
            self.relations.append(
                UMLRelation(child, parent, 'inheritance', None, None, label)
            )
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
            (r'(\w+)\s*\-\-\|\>\s*(\w+)', 'inheritance', False),
            
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
                
                # Parsuj liczności
                s_mult_lower, s_mult_upper = ("0", "*")
                t_mult_lower, t_mult_upper = ("0", "*")

                if len(raw_multiplicities) > 0:
                    s_mult_lower, s_mult_upper = self.parse_multiplicity(raw_multiplicities[0])
                if len(raw_multiplicities) > 1:
                    t_mult_lower, t_mult_upper = self.parse_multiplicity(raw_multiplicities[1])

                source_mult = f"{s_mult_lower}..{s_mult_upper}" if s_mult_lower != s_mult_upper else s_mult_lower
                target_mult = f"{t_mult_lower}..{t_mult_upper}" if t_mult_lower != t_mult_upper else t_mult_lower
                
                # Obsługa złożonych typów relacji
                if rel_type == 'composition_aggregation_left':
                    actual_rel_type = 'composition'
                    if not raw_multiplicities or len(raw_multiplicities) < 1: 
                         source_mult = "1"
                    if not raw_multiplicities or len(raw_multiplicities) < 2:
                         target_mult = "0..*"
                    
                    print(f"DEBUG: Found complex relation: {source} --{actual_rel_type}--> {target} (label: {label}) (source_mult: {source_mult}, target_mult: {target_mult})")
                    self.relations.append(UMLRelation(
                        source=source, 
                        target=target, 
                        relation_type=actual_rel_type, 
                        label=label, 
                        source_multiplicity=source_mult, 
                        target_multiplicity=target_mult
                    ))
                    return True

                elif rel_type == 'aggregation_composition_left':
                    actual_rel_type = 'aggregation' 
                    if not raw_multiplicities or len(raw_multiplicities) < 1:
                         source_mult = "0..*"
                    if not raw_multiplicities or len(raw_multiplicities) < 2:
                         target_mult = "1"
                    
                    print(f"DEBUG: Found complex relation: {source} --{actual_rel_type}--> {target} (label: {label}) (source_mult: {source_mult}, target_mult: {target_mult})")
                    self.relations.append(UMLRelation(
                        source=source, 
                        target=target, 
                        relation_type=actual_rel_type, 
                        label=label, 
                        source_multiplicity=source_mult, 
                        target_multiplicity=target_mult
                    ))
                    return True

                # Standardowa obsługa
                print(f"DEBUG: Found relation: {source} --{rel_type}--> {target} (label: {label}) (source_mult: {source_mult}, target_mult: {target_mult})")
                self.relations.append(UMLRelation(
                    source=source, 
                    target=target, 
                    relation_type=rel_type, 
                    label=label, 
                    source_multiplicity=source_mult, 
                    target_multiplicity=target_mult
                ))
                return True
        
        print(f"DEBUG: Relation not found: {line_clean!r}")
        return False

    @staticmethod
    def parse_multiplicity(multiplicity: str) -> tuple[str, str]:
        """Zwraca (lower, upper) jako stringi na podstawie notacji UML/PlantUML."""
        if not multiplicity:
            return "0", "*"
        if ".." in multiplicity:
            lower, upper = multiplicity.split("..")
            return lower.strip(), upper.strip().replace("n", "*").replace("#", "*")
        if multiplicity == "*":
            return "0", "*"
        return multiplicity, multiplicity

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
    import pprint
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  
    input_file = 'diagram_klas_PlantUML.puml'
    output_file = f'test_class_{timestamp}.json'
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        parser = PlantUMLParser()
        parser.parse(plantuml_code)
        
        # Przygotuj dane do wyświetlenia
        parsed_data = parser.get_parsed_data()

        print("--- Wynik Parsowania ---")
        pprint.pprint(parsed_data)
        
        # Opcjonalnie zapisz do pliku JSON
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        print(f"\nWynik zapisany do: {output_file}")
        
    except FileNotFoundError:
        print(f"Nie znaleziono pliku: {input_file}")
        print("Utwórz przykładowy plik PlantUML lub zmień nazwę pliku w kodzie.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()