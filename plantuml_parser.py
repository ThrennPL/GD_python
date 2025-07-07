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
            m = re.match(r'note\s+\w+\s+of\s+([A-Za-z0-9_ąćęłńóśźźĄĆĘŁŃÓŚŹŻ]+)\s*:\s*(.+)', line)
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
            # Upewnij się, że PlantUML-owy symbol relacji jest w linii
            if any(rel_sym in line for rel_sym in ['-->', '<--', '--', '||--', '|>', '<|','<|--', '--|>', '..|>', '<|..', '*--', 'o--']):
                self._parse_relation(line)

    def _parse_enum_definition(self, line: str) -> UMLEnum:
        match = re.match(r'enum\s+(\w+)', line)
        if match:
            name = match.group(1)
            return UMLEnum(name, [])
        return None
    
    def _parse_class_definition(self, line: str) -> UMLClass:
        """Parsuje definicję klasy z obsługą extends i implements"""
        # Wzorzec dla klasy z extends/implements
        # Przykłady:
        # class Przelew extends Konto
        # class Przelew extends Konto implements Validatable
        # abstract class Przelew extends Konto
        # class Przelew extends Konto {
        
        pattern = r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+(\w+(?:\s*,\s*\w+)*))?(?:\s*<<(\w+)>>)?(?:\s*\{?)'
        match = re.match(pattern, line)
        
        if match:
            name = match.group(1)
            extends_class = match.group(2)  # Klasa nadrzędna
            implements_interfaces = match.group(3)  # Interfejsy (może być lista)
            stereotype = match.group(4)
            is_abstract = 'abstract' in line
            
            # Utworz klasę
            uml_class = UMLClass(name, [], [], stereotype, is_abstract)
            self.classes[name] = uml_class
            
            # Jeśli klasa dziedziczy po innej klasie, dodaj relację dziedziczenia
            if extends_class:
                self.relations.append(UMLRelation(
                    name, extends_class, 'inheritance', None, None, None
                ))
                print(f"DEBUG: Found inheritance: {name} extends {extends_class}")
            
            # Jeśli klasa implementuje interfejsy, dodaj relacje implementacji
            if implements_interfaces:
                # Podziel interfejsy (mogą być oddzielone przecinkami)
                interfaces = [iface.strip() for iface in implements_interfaces.split(',')]
                for interface in interfaces:
                    self.relations.append(UMLRelation(
                        name, interface, 'realization', None, None, None
                    ))
                    print(f"DEBUG: Found implementation: {name} implements {interface}")
            
            return uml_class
        
        # Fallback - stary wzorzec bez extends/implements
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
        """Parsuje definicję interfejsu z obsługą extends"""
        # Wzorzec dla interfejsu z extends
        # Przykłady:
        # interface Validatable
        # interface Validatable extends BaseInterface
        
        pattern = r'interface\s+(\w+)(?:\s+extends\s+(\w+))?'
        match = re.match(pattern, line)
        
        if match:
            name = match.group(1)
            extends_interface = match.group(2)  # Interfejs nadrzędny
            
            # Utworz interfejs
            uml_class = UMLClass(name, [], [], "interface")
            self.classes[name] = uml_class
            
            # Jeśli interfejs dziedziczy po innym interfejsie, dodaj relację dziedziczenia
            if extends_interface:
                self.relations.append(UMLRelation(
                    name, extends_interface, 'inheritance', None, None, None
                ))
                print(f"DEBUG: Found interface inheritance: {name} extends {extends_interface}")
            
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
        """Parsuje relacje między klasami - poprawione wzorce i obsługa liczności"""
        # Najpierw wyciągnij surowe stringi liczności i etykietę
        raw_multiplicities, label = self._extract_multiplicity_and_label(line)
                
        # Usuń etykietę i liczności z linii, aby dopasować czysty wzorzec relacji
        line_clean = re.sub(r':\s*.*$', '', line.strip())
        line_clean = re.sub(r'"[0-9*\.]+"\s*', '', line_clean)
        
        patterns = [
            # Specyficzne wzorce dla złożonych relacji na początku
            # Kompozycja po lewej, Agregacja po prawej (Zamówienie *--o Koszyk)
            (r'(\w+)\s*\*\-\-o\s*(\w+)', 'composition_aggregation_left', False), 
            # Agregacja po lewej, Kompozycja po prawej (Koszyk o--* Zamówienie)
            (r'(\w+)\s*o\-\-\*\s*(\w+)', 'aggregation_composition_left', False), 
            
            # Dziedziczenie
            (r'(\w+)\s*<\|\-\-\s*(\w+)', 'inheritance', True),
            (r'(\w+)\s*\-\-\|\>\s*(\w+)', 'inheritance', False),
            (r'(\w+)\s*\|\>\s*(\w+)', 'inheritance', False),
            (r'(\w+)\s*<\|\s*(\w+)', 'inheritance', True),
            
            # Realizacja/Implementacja
            (r'(\w+)\s*<\|\.\.\s*(\w+)', 'realization', True),
            (r'(\w+)\s*\.\.\|\>\s*(\w+)', 'realization', False),
            
            # Kompozycja (ogólna)
            (r'(\w+)\s*\*\-\-\s*(\w+)', 'composition', False),
            (r'(\w+)\s*\-\-\*\s*(\w+)', 'composition', True),
            
            # Agregacja (ogólna)
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
                
                # Zastosuj parse_multiplicity do wyodrębnionych surowych stringów
                # Defaultowe wartości dla source_mult i target_mult, jeśli nie podano
                s_mult_lower, s_mult_upper = ("0", "*") # Domyślna dla asocjacji/ogólna
                t_mult_lower, t_mult_upper = ("0", "*")

                if len(raw_multiplicities) > 0:
                    s_mult_lower, s_mult_upper = self.parse_multiplicity(raw_multiplicities[0])
                if len(raw_multiplicities) > 1:
                    t_mult_lower, t_mult_upper = self.parse_multiplicity(raw_multiplicities[1])

                source_mult = f"{s_mult_lower}..{s_mult_upper}" if s_mult_lower != s_mult_upper else s_mult_lower
                target_mult = f"{t_mult_lower}..{t_mult_upper}" if t_mult_lower != t_mult_upper else t_mult_lower
                
                # Specjalna obsługa dla nowych, złożonych typów relacji
                if rel_type == 'composition_aggregation_left':
                    actual_rel_type = 'composition'
                    # Te domyślne liczności powinny być używane TYLKO jeśli nie podano ich jawnie w PlantUML
                    if not raw_multiplicities or len(raw_multiplicities) < 1: 
                         source_mult = "1" # Domyślna dla strony kompozycji
                    if not raw_multiplicities or len(raw_multiplicities) < 2:
                         target_mult = "0..*" # Domyślna dla strony agregacji
                    
                    print(f"DEBUG: Found complex relation: {source} --{actual_rel_type}--> {target} (label: {label}) (source_mult: {source_mult}, target_mult: {target_mult})")

                    self.relations.append(UMLRelation(
                        source, target, actual_rel_type, label, source_mult, target_mult
                    ))
                    return

                elif rel_type == 'aggregation_composition_left':
                    actual_rel_type = 'aggregation' 
                    if not raw_multiplicities or len(raw_multiplicities) < 1:
                         source_mult = "0..*"
                    if not raw_multiplicities or len(raw_multiplicities) < 2:
                         target_mult = "1"
                    
                    print(f"DEBUG: Found complex relation: {source} --{actual_rel_type}--> {target} (label: {label}) (source_mult: {source_mult}, target_mult: {target_mult})")

                    self.relations.append(UMLRelation(
                        source, target, actual_rel_type, label, source_mult, target_mult
                    ))
                    return

                # Standardowa obsługa dla pozostałych relacji
                print(f"DEBUG: Found relation: {source} --{rel_type}--> {target} (label: {label}) (source_mult: {source_mult}, target_mult: {target_mult})")
                
                self.relations.append(UMLRelation(
                    source, target, rel_type, label, source_mult, target_mult
                ))
                return
        
        print(f"DEBUG: Relation not found: {line_clean!r}")

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
        return multiplicity, multiplicity # W przypadku "1", "2" itp.

    def _extract_multiplicity_and_label(self, line: str) -> tuple[list[str], str]:
        """Wyciąga surowe stringi liczności i etykietę z linii relacji PlantUML."""
        # Wzorzec na liczności w cudzysłowach
        mult_pattern = r'"([0-9*\.]+)"'
        multiplicities = re.findall(mult_pattern, line)

        # Usunięcie liczności z linii, żeby łatwiej wyciągnąć etykietę
        line_without_mult = re.sub(mult_pattern, '', line)

        label_match = re.search(r':\s*(?:(?:")([^"]+)(?:")|([^\s:]+))', line_without_mult)
        # Zmodyfikowany regex do wyciągania etykiety:
        # - ': ' po którym następuje cudzysłów i tekst w cudzysłowie (grupa 1)
        # - LUB ': ' po którym następuje dowolny tekst nie będący spacją/dwukropkiem (grupa 2)
        
        label = None
        if label_match:
            if label_match.group(1): # Etykieta w cudzysłowie
                label = label_match.group(1).strip()
            elif label_match.group(2): # Etykieta bez cudzysłowu
                label = label_match.group(2).strip()

        return multiplicities, label