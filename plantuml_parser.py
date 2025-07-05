from plantuml_model import UMLClass, UMLRelation, UMLEnum, UMLNote
import re

class PlantUMLParser:
    """Parser dla kodu PlantUML"""
    
    def __init__(self):
        self.classes = {}
        self.relations = []
        self.enums = {}  
        self.notes = []
    
    def parse(self, plantuml_code: str):
        """Główna metoda parsowania"""
        lines = plantuml_code.strip().split('\n')
        current_class = None
        current_enum = None
        note_mode = False
        note_target = None
        note_lines = []

        for line in lines:
            line = line.strip()

            # Obsługa notatek jednolinijkowych
            m = re.match(r'note\s+\w+\s+of\s+([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)\s*:\s*(.+)', line)
            if m:
                note_target = m.group(1)
                note_text = m.group(2)
                self.notes.append(UMLNote(note_target, note_text))
                continue

            # Obsługa notatek wielolinijkowych
            if line.startswith('note '):
                # np. note left of Konto
                m = re.match(r'note\s+\w+\s+of\s+([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)', line)
                if m:
                    note_target = m.group(1)
                    note_mode = True
                    note_lines = []
                continue
            if note_mode:
                if line == 'end note':
                    self.notes.append(UMLNote(note_target, '\n'.join(note_lines)))
                    note_mode = False
                    note_target = None
                    note_lines = []
                else:
                    note_lines.append(line)
                continue
            
            if not line or line.startswith("'") or line.startswith("@"):
                continue

            # Parsowanie klas
            if line.startswith('class '):
                current_class = self._parse_class_definition(line)

            elif line.startswith('interface '):
                current_class = self._parse_interface_definition(line)

            elif line.startswith('enum '):
                current_enum = self._parse_enum_definition(line)
                if current_enum:
                    self.enums[current_enum.name] = current_enum
                continue

            elif current_enum and line == '{':
                continue
            elif current_enum and line == '}':
                current_enum = None
                continue
            elif current_enum:
                # Dodaj wartość do enum
                if line:
                    current_enum.values.append(line)
                continue

            # Parsowanie zawartości klasy
            elif current_class and line in ['{', '}']:
                if line == '}':
                    current_class = None
                continue

            elif current_class:
                self._parse_class_member(line, current_class)

            # Parsowanie relacji
            elif any(rel in line for rel in ['-->', '<--', '--', '||--', '|>', '<|']):
                self._parse_relation(line)

    def _parse_enum_definition(self, line: str) -> UMLEnum:
        match = re.match(r'enum\s+(\w+)', line)
        if match:
            name = match.group(1)
            return UMLEnum(name, [])
        return None
    
    def _parse_class_definition(self, line: str) -> UMLClass:
        match = re.match(r'(?:abstract\s+)?class\s+(\w+)(?:\s*<<(\w+)>>)?', line)
        if match:
            name = match.group(1)
            stereotype = match.group(2)
            is_abstract = 'abstract' in line
            uml_class = UMLClass(name, [], [], stereotype, is_abstract)
            self.classes[name] = uml_class
            return uml_class
        return None
    
    def _parse_interface_definition(self, line: str) -> UMLClass:
        """Parsuje definicję interfejsu"""
        match = re.match(r'interface\s+(\w+)', line)
        if match:
            name = match.group(1)
            uml_class = UMLClass(name, [], [], "interface")
            self.classes[name] = uml_class
            return uml_class
        return None
    
    def _parse_class_member(self, line: str, current_class: UMLClass):
        line = line.strip()
        if not line or line in ['{', '}']:
            return

        # Rozpoznaj {static}, {abstract} itp.
        modifiers = re.findall(r'\{(\w+)\}', line)
        clean_line = re.sub(r'\s*\{[^}]+\}', '', line)

        if '(' in clean_line and ')' in clean_line:
            # Metoda
            method_info = self._parse_method(clean_line, modifiers)
            current_class.methods.append(method_info)
        else:
            # Atrybut
            attr_info = self._parse_attribute(clean_line, modifiers)
            current_class.attributes.append(attr_info)

    def _parse_method(self, line: str, modifiers: list):
        return {"signature": line, "modifiers": modifiers}

    def _parse_attribute(self, line: str, modifiers: list):
        return {"declaration": line, "modifiers": modifiers}
    
    def _parse_relation(self, line: str):
        """Parsuje relacje między klasami - poprawione wzorce"""
        # Najpierw wyciągnij liczności i etykietę
        multiplicities, label = self._extract_multiplicity_and_label(line)
        #print(f"DEBUG: line={line!r} multiplicities={multiplicities} label={label!r}")
        
        # Usuń etykietę i liczności z linii
        line_clean = re.sub(r':\s*.*$', '', line.strip())
        line_clean = re.sub(r'"[0-9*\.]+"\s*', '', line_clean)
        
        #print(f"DEBUG: line_clean={line_clean!r}")  # Dodatkowy debug
        
        patterns = [
            # Dziedziczenie - POPRAWIONE WZORCE
            (r'(\w+)\s*<\|\-\-\s*(\w+)', 'inheritance', True),   # A <|-- B (A dziedziczy z B)
            (r'(\w+)\s*\-\-\|\>\s*(\w+)', 'inheritance', False),  # A --|> B (A dziedziczy z B)
            (r'(\w+)\s*\|\>\s*(\w+)', 'inheritance', False),      # A |> B (skrócona forma)
            (r'(\w+)\s*<\|\s*(\w+)', 'inheritance', True),        # A <| B (skrócona forma)
            
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
                
                source_mult = multiplicities[0] if len(multiplicities) > 0 else None
                target_mult = multiplicities[1] if len(multiplicities) > 1 else None
                
                #print(f"DEBUG: Found relation: {source} --{rel_type}--> {target} (label: {label})")
                
                self.relations.append(UMLRelation(
                    source, target, rel_type, label, source_mult, target_mult
                ))
                return  # Ważne: przerwij po znalezieniu pierwszego dopasowania
        
        #print(f"DEBUG: No pattern matched for line: {line_clean!r}")

    @staticmethod
    def parse_multiplicity(multiplicity):
        """Zwraca (lower, upper) jako stringi na podstawie notacji UML/PlantUML."""
        if not multiplicity:
            return "0", "*"
        if ".." in multiplicity:
            lower, upper = multiplicity.split("..")
            return lower.strip(), upper.strip().replace("n", "*").replace("#", "*")
        if multiplicity == "*":
            return "0", "*"
        return multiplicity, multiplicity

    def _extract_multiplicity_and_label(self, line: str):
        """Wyciąga liczność i etykietę z linii relacji PlantUML."""
        mult_pattern = r'"([0-9*\.]+)"'
        multiplicities = re.findall(mult_pattern, line)
        label_match = re.search(r':\s*"([^"]+)"', line)
        label = label_match.group(1).strip() if label_match else None
        return multiplicities, label
    
