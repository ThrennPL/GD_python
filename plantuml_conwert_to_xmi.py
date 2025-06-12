import re
from dataclasses import dataclass
from typing import List, Dict, Optional
import uuid
import xml.etree.ElementTree as ET
import xml.dom.minidom

@dataclass
class UMLClass:
    name: str
    attributes: List[str]
    methods: List[str]
    stereotype: Optional[str] = None
    
@dataclass
class UMLRelation:
    source: str
    target: str
    relation_type: str
    label: Optional[str] = None
    source_multiplicity: Optional[str] = None
    target_multiplicity: Optional[str] = None

@dataclass
class UMLEnum:
    name: str
    values: list

@dataclass
class UMLNote:
    target: str  # nazwa klasy/interfejsu/enumu
    text: str

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
        """Parsuje definicję klasy"""
        match = re.match(r'class\s+(\w+)(?:\s*<<(\w+)>>)?', line)
        if match:
            name = match.group(1)
            stereotype = match.group(2)
            uml_class = UMLClass(name, [], [], stereotype)
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
        """Parsuje atrybuty i metody klasy"""
        line = line.strip()
        
        # Metody (zawierają nawiasy)
        if '(' in line and ')' in line:
            current_class.methods.append(line)
        # Atrybuty
        elif line and not line in ['{', '}']:
            current_class.attributes.append(line)
    
    def _parse_relation(self, line: str):
        """Parsuje relacje między klasami"""
        # Proste mapowanie symboli PlantUML na typy relacji
        relation_patterns = {
            r'([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)\s*("[^"]*")?\s*<\|\-\-\s*("[^"]*")?\s*([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)': ('inheritance', True),
            r'([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)\s*("[^"]*")?\s*\-\-\>\|\s*("[^"]*")?\s*([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)': ('inheritance', False),
            r'([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)\s*("[^"]*")?\s*\-\-\s*("[^"]*")?\s*([A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)': ('association', False),
            r'(\w+)\s*<\|\-\-\s*(\w+)': ('inheritance', True),  # inheritance (odwrócone)
            r'(\w+)\s*\-\-\>\|\s*(\w+)': ('inheritance', False),  # inheritance
            r'(\w+)\s*\*\-\-\s*(\w+)': ('composition', False),
            r'(\w+)\s*\-\-\*\s*(\w+)': ('composition', True),
            r'(\w+)\s*o\-\-\s*(\w+)': ('aggregation', False),
            r'(\w+)\s*\-\-o\s*(\w+)': ('aggregation', True),
            r'(\w+)\s*\-\->\s*(\w+)': ('association', False),
            r'(\w+)\s*<\-\-\s*(\w+)': ('association', True),
            r'(\w+)\s*\-\-\s*(\w+)': ('association', False),
        }
        
        for pattern, (rel_type, reversed_) in relation_patterns.items():
            match = re.search(pattern, line)
            if match:
                # Sprawdź ile jest grup
                groups = match.groups()
                if len(groups) >= 4:
                    if reversed_:
                        source = match.group(4)
                        target = match.group(1)
                        source_mult = match.group(3)
                        target_mult = match.group(2)
                    else:
                        source = match.group(1)
                        target = match.group(4)
                        source_mult = match.group(2)
                        target_mult = match.group(3)
                elif len(groups) == 2:
                    if reversed_:
                        source = match.group(2)
                        target = match.group(1)
                    else:
                        source = match.group(1)
                        target = match.group(2)
                    source_mult = None
                    target_mult = None
                else:
                    continue  # pomiń jeśli nie pasuje

                # Wyciągnij etykietę (np. : posiada)
                label_match = re.search(r':\s*([^\n]+)', line)
                label = label_match.group(1).strip() if label_match else None

                # Usuń cudzysłowy z liczności
                source_mult = source_mult.strip('"') if source_mult else None
                target_mult = target_mult.strip('"') if target_mult else None

                relation = UMLRelation(source, target, rel_type, label)
                relation.source_multiplicity = source_mult
                relation.target_multiplicity = target_mult
                self.relations.append(relation)
                break

class EAXMIGenerator:
    """Generator plików XMI dla Enterprise Architect"""
    
    def __init__(self):
        self.ea_localid_counter = 1
        self.namespace = {
            'xmi': 'http://www.omg.org/XMI',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'uml': 'http://www.eclipse.org/uml2/3.0.0/UML'
        }
    
    def generate_xmi(self, classes: Dict[str, UMLClass], relations: List[UMLRelation], 
                     enums: Dict[str, UMLEnum], notes: List[UMLNote]) -> str:
        """Poprawiona metoda generująca XMI zgodny z EA"""
    
        # Główny element XMI - POPRAWNE przestrzenie nazw dla EA
        xmi_root = ET.Element('xmi:XMI')
        xmi_root.set('xmi:version', '2.0')
        xmi_root.set('xmlns:uml', 'http://www.eclipse.org/uml2/5.0.0/UML')
        xmi_root.set('xmlns:xmi', 'http://www.omg.org/XMI')
        xmi_root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        xmi_root.set('xmlns:eaProfile', 'http://www.sparxsystems.com/profiles/eaProfile/1.0')
    
        # Documentation - EA to lubi
        documentation = ET.SubElement(xmi_root, 'xmi:Documentation')
        documentation.set('exporter', 'Enterprise Architect')
        documentation.set('exporterVersion', '15.2')
    
        # Model UML
        model = ET.SubElement(xmi_root, 'uml:Model')
        model_id = f'EAID_{uuid.uuid4()}'
        model.set('xmi:id', model_id)
        model.set('name', 'PlantUMLImport')
    
        # Package dla klas - z poprawnymi właściwościami EA
        package = ET.SubElement(model, 'packagedElement')
        package.set('xmi:type', 'uml:Package')
        package_id = f'EAPK_{uuid.uuid4()}'
        package.set('xmi:id', package_id)
        package.set('name', 'Classes')
    
        # Generuj klasy z pełnymi metadanymi
        class_ids = {}
        for class_name, uml_class in classes.items():
            class_id = f'EAID_{uuid.uuid4()}'
            class_ids[class_name] = class_id
        
            class_elem = ET.SubElement(package, 'packagedElement')
        
            # Obsługa interfejsów vs klas
            if uml_class.stereotype == 'interface':
                class_elem.set('xmi:type', 'uml:Interface')
            else:
                class_elem.set('xmi:type', 'uml:Class')
            
            class_elem.set('xmi:id', class_id)
            class_elem.set('name', class_name)
            class_elem.set('visibility', 'public')
        
            # Dodaj atrybuty z pełnymi typami
            for attr in uml_class.attributes:
                attr_name, attr_type = self._split_attribute(attr)
                attr_elem = ET.SubElement(class_elem, 'ownedAttribute')
                attr_elem.set('xmi:id', f'EAID_{uuid.uuid4()}')
                attr_elem.set('name', attr_name)
                attr_elem.set('visibility', self._get_visibility(attr))
            
                # Typ atrybutu - EA wymaga referencji
                if attr_type:
                    type_elem = ET.SubElement(attr_elem, 'type')
                    type_elem.set('xmi:type', 'uml:PrimitiveType')
                    type_elem.set('href', f'pathmap://UML_LIBRARIES/EcorePrimitiveTypes.library.uml#{attr_type}')
        
            # Dodaj metody
            for method in uml_class.methods:
                method_elem = ET.SubElement(class_elem, 'ownedOperation')
                method_elem.set('xmi:id', f'EAID_{uuid.uuid4()}')
                method_elem.set('name', self._clean_method_name(method))
                method_elem.set('visibility', self._get_visibility(method))
    
        # Generuj enumy
        enum_ids = {}
        for enum_name, uml_enum in enums.items():
            enum_id = f'EAID_{uuid.uuid4()}'
            enum_ids[enum_name] = enum_id

            enum_elem = ET.SubElement(package, 'packagedElement')
            enum_elem.set('xmi:type', 'uml:Enumeration')
            enum_elem.set('xmi:id', enum_id)
            enum_elem.set('name', enum_name)
            enum_elem.set('visibility', 'public')
        
            for value in uml_enum.values:
                literal_elem = ET.SubElement(enum_elem, 'ownedLiteral')
                literal_elem.set('xmi:id', f'EAID_{uuid.uuid4()}')
                literal_elem.set('name', value)
    
        # Generuj relacje - TO JEST KLUCZOWE
        for relation in relations:
            if relation.source in class_ids and relation.target in class_ids:
            
                if relation.relation_type == 'inheritance':
                    # Generalizacja - specjalny przypadek
                    generalization = ET.SubElement(
                        package.find(f".//packagedElement[@xmi:id='{class_ids[relation.source]}']"),
                        'generalization'
                    )
                    generalization.set('xmi:id', f'EAID_{uuid.uuid4()}')
                    generalization.set('general', class_ids[relation.target])
                
                else:
                    # Inne relacje jako asocjacje
                    assoc_elem = ET.SubElement(package, 'packagedElement')
                    assoc_elem.set('xmi:type', 'uml:Association')
                    assoc_id = f'EAID_{uuid.uuid4()}'
                    assoc_elem.set('xmi:id', assoc_id)
                
                    if relation.label:
                        assoc_elem.set('name', relation.label)
                
                    # Końce asocjacji z pełnymi właściwościami
                    end1 = ET.SubElement(assoc_elem, 'ownedEnd')
                    end1.set('xmi:id', f'EAID_{uuid.uuid4()}')
                    end1.set('type', class_ids[relation.source])
                    if relation.source_multiplicity:
                        end1.set('multiplicity', relation.source_multiplicity)
                    
                    end2 = ET.SubElement(assoc_elem, 'ownedEnd')  
                    end2.set('xmi:id', f'EAID_{uuid.uuid4()}')
                    end2.set('type', class_ids[relation.target])
                    if relation.target_multiplicity:
                        end2.set('multiplicity', relation.target_multiplicity)
    
        # KLUCZOWE: EA Extension z wszystkimi metadanymi
        self.generate_ea_extension_improved(xmi_root, class_ids, relations, enum_ids, package_id)
    
        # Generuj diagram
        self.generate_diagram_with_layout(
            xmi_root.find('xmi:Extension'), 
            class_ids, 
            relations, 
            package_id
        )
    
        # Konwertuj do ładnego XML
        rough_string = ET.tostring(xmi_root, encoding='utf-8')
        parsed = xml.dom.minidom.parseString(rough_string)
    
        # Dodaj deklarację XML z encoding
        pretty_xml = parsed.toprettyxml(indent="  ", encoding="utf-8")
    
        # Popraw header XML
        xml_string = pretty_xml.decode('utf-8')
        xml_string = xml_string.replace('<?xml version="1.0" encoding="utf-8"?>', 
                                  '<?xml version="1.0" encoding="UTF-8"?>')
    
        return xml_string



    def generate_ea_profile(self, xmi_root):
        """Generuje profil EA wymagany do importu"""
        # EA Profile - kluczowy element!
        ea_profile = ET.SubElement(xmi_root, 'eaProfile')
        ea_profile.set('xmi:type', 'eaProfile:EAProfile')
        ea_profile.set('xmi:id', f'EA_Profile_{uuid.uuid4()}')
    
        # Stereotype definitions
        stereotype_elem = ET.SubElement(ea_profile, 'stereotype')
        stereotype_elem.set('name', 'class')
        stereotype_elem.set('baseClass', 'Class')
    
        return ea_profile

    def generate_ea_extension_improved(self, xmi_root, classes, relations, enums, package_id):
        """Ulepszona generacja EA Extension"""
        extension = ET.SubElement(xmi_root, 'xmi:Extension')
        extension.set('extender', 'Enterprise Architect')
        extension.set('extenderID', '6.5')
    
        # PROFILES - bardzo ważne!
        profiles = ET.SubElement(extension, 'profiles')
    
        # UML Profile
        uml_profile = ET.SubElement(profiles, 'umlprofile')
        uml_profile.set('profiletype', 'uml2')
    
        # PRIMITIVETYPES - EA wymaga definicji typów podstawowych
        primitive_types = ET.SubElement(extension, 'primitivetypes')
    
        basic_types = ['int', 'String', 'double', 'boolean', 'float', 'long', 'char', 'byte']
        for type_name in basic_types:
            ptype = ET.SubElement(primitive_types, 'primitivetype')
            ptype.set('xmi:id', f'eaxmiid{uuid.uuid4()}')
            ptype.set('name', type_name)
    
        # ELEMENTS z poprawnymi EA właściwościami
        elements = ET.SubElement(extension, 'elements')
    
        for class_name, class_id in classes.items():
            element = ET.SubElement(elements, 'element')
            element.set('xmi:idref', class_id)
            element.set('xmi:type', 'uml:Class')
            element.set('name', class_name)
            element.set('scope', 'public')
        
            # Properties - kluczowe dla EA
            properties = ET.SubElement(element, 'properties')
            properties.set('isSpecification', 'false')
            properties.set('sType', 'Class')
            properties.set('nType', '0')
            properties.set('scope', 'public')
            properties.set('isRoot', 'false')
            properties.set('isLeaf', 'false')
            properties.set('isAbstract', 'false')
            properties.set('isActive', 'false')
            properties.set('package', package_id)
            properties.set('date_created', '2024-01-01 00:00:00')
            properties.set('date_modified', '2024-01-01 00:00:00')
            properties.set('gentype', 'Java')
            properties.set('tagged', '0')
            properties.set('package_name', 'Classes')
            properties.set('version', '1.0')
            properties.set('isprotected', 'FALSE')
            properties.set('usedtd', 'FALSE')
            properties.set('logicalPackage', '1')
            properties.set('ea_localid', str(self.ea_localid_counter))
            properties.set('ea_guid', f'{{{uuid.uuid4()}}}')
        
            self.ea_localid_counter += 1
        
            # Style
            style = ET.SubElement(element, 'style')
            style.set('value', 'BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;VSwimLanes=1;HSwimLanes=1;BorderStyle=0;')
        
            # Tags - EA używa tagged values
            tags = ET.SubElement(element, 'tags')
        
            # Stereotypes
            stereotypes = ET.SubElement(element, 'stereotypes')
        
            # XRef - cross references
            xrefs = ET.SubElement(element, 'xrefs')
            xrefs.set('value', 'CreateSmartLinksOnLoad=1;')
    
        # CONNECTORS z poprawnymi właściwościami EA
        connectors = ET.SubElement(extension, 'connectors')
    
        connector_id_counter = 1
        for relation in relations:
            if relation.source in classes and relation.target in classes:
                connector = ET.SubElement(connectors, 'connector')
                connector.set('xmi:id', f'EAID_{uuid.uuid4()}')
            
                # EA wymaga tego formatu
                source_elem = ET.SubElement(connector, 'source')
                source_elem.set('xmi:idref', classes[relation.source])
            
                target_elem = ET.SubElement(connector, 'target')
                target_elem.set('xmi:idref', classes[relation.target])
            
                # Properties dla connectora
                properties = ET.SubElement(connector, 'properties')
                properties.set('ea_type', self._map_relation_type_to_ea(relation.relation_type))
                properties.set('direction', 'Source -> Destination')
                properties.set('linemode', '3')
                properties.set('linecolor', '-1')
                properties.set('linewidth', '0')
                properties.set('seonlycolor', '-1')
                properties.set('senumbercolor', '-1')
                properties.set('sefontcolor', '-1')
                properties.set('selinestyle', '0')
                properties.set('sefontsize', '0')
                properties.set('sefontweight', '0')
                properties.set('sefontitalic', '0')
                properties.set('sefontunderline', '0')
                properties.set('sefontfamily', 'Arial')
                properties.set('eventflags', '0')
                properties.set('stylesheet', '')
                properties.set('ea_localid', str(self.ea_localid_counter))
                properties.set('ea_guid', f'{{{uuid.uuid4()}}}')
            
                self.ea_localid_counter += 1
            
                # Source i Target details
                source_details = ET.SubElement(connector, 'source')
                source_details.set('aggregation', '0')
                source_details.set('multiplicity', relation.source_multiplicity or '1')
                source_details.set('role', '')
                source_details.set('roleType', 'false')
                source_details.set('containment', 'Unspecified')
                source_details.set('isNavigableEx', 'false')
                source_details.set('isNavigable', 'false')
                source_details.set('isOrdered', 'false')
                source_details.set('isChangeable', 'true')
            
                target_details = ET.SubElement(connector, 'target')
                target_details.set('aggregation', '0')
                target_details.set('multiplicity', relation.target_multiplicity or '1')
                target_details.set('role', '')
                target_details.set('roleType', 'false')
                target_details.set('containment', 'Unspecified')
                target_details.set('isNavigableEx', 'false')
                target_details.set('isNavigable', 'true')
                target_details.set('isOrdered', 'false')
                target_details.set('isChangeable', 'true')
            
                connector_id_counter += 1
    
        return extension

    def _map_relation_type_to_ea(self, relation_type: str) -> str:
        """Mapuje typy relacji PlantUML na typy EA"""
        mapping = {
            'inheritance': 'Generalization',
            'composition': 'Aggregation',
            'aggregation': 'Aggregation', 
            'association': 'Association',
            'dependency': 'Dependency',
            'realization': 'Realization'
        }
        return mapping.get(relation_type, 'Association')

    # BARDZO WAŻNE: Dodaj generację diagramu z elementami
    def generate_diagram_with_layout(self, extension, classes, relations, package_id):
        """Generuje diagram z podstawowym layoutem"""
        diagrams = ET.SubElement(extension, 'diagrams')
    
        diagram = ET.SubElement(diagrams, 'diagram')
        diagram_id = f'EAID_{uuid.uuid4()}'
        diagram.set('xmi:id', diagram_id)
    
        # EA wymaga tych właściwości
        properties = ET.SubElement(diagram, 'properties')
        properties.set('name', 'Class Diagram')
        properties.set('type', 'Logical')
        properties.set('documentation', '')
        properties.set('tooltype', 'UML')
        properties.set('version', '1.0')
        properties.set('author', 'PlantUML Converter')
        properties.set('created_date', '2024-01-01 00:00:00')
        properties.set('modified_date', '2024-01-01 00:00:00')
        properties.set('htmlpath', '')
        properties.set('show_details', '0')
        properties.set('orientation', 'P')
        properties.set('papersize', 'A4')
        properties.set('scale', '100')
        properties.set('showpagebreaks', 'false')
        properties.set('showpackagecontents', 'true')
        properties.set('showpubliconly', 'false')
        properties.set('showattributes', 'true')
        properties.set('showoperations', 'true')
        properties.set('showstereotype', 'true')
        properties.set('showparents', 'false')
        properties.set('showlagunagecollection', 'false')
        properties.set('swimlanes', 'locked=false;orientation=0;width=0;inbar=false;names=false;color=-1;bold=false;fcol=0;tcol=-1;ofCol=-1;ufCol=-1;hl=0;ufh=0;hh=0;cls=0;')
        properties.set('matrixitems', 'locked=false;matrixactive=false;swimlanesactive=true;kanbanactive=false;width=1;clrLine=0;')
        properties.set('ea_localid', str(self.ea_localid_counter))
        properties.set('ea_guid', f'{{{uuid.uuid4()}}}')
    
        self.ea_localid_counter += 1
    
        # Style
        style = ET.SubElement(diagram, 'style')
        style.set('value', 'MDGDgm=Extended::Class Diagram;STBLDgm=;ShowNotes=1;VisibleAttributeDetail=0;VisibleOperationDetail=0;VisibleTypeDetail=1;VisibleStereotype=1;VisibleTaggedValues=0;VisibleConstraints=0;VisibleCompartmentItems=1;')
    
        # Elements na diagramie z pozycjonowaniem
        elements = ET.SubElement(diagram, 'elements')
    
        x, y = 100, 100
        for i, (class_name, class_id) in enumerate(classes.items()):
            element = ET.SubElement(elements, 'element')
            element.set('geometry', f'Left={x};Top={y};Right={x+120};Bottom={y+80};')
            element.set('subject', class_id)
            element.set('seqno', str(i + 1))
            element.set('style', 'DUID=...;NSL=0;BCol=-1;BFol=-1;LCol=-1;LWth=-1;fontsz=0;bold=0;italic=0;ul=0;charset=0;pitch=0;')
        
            # Przesunięcie dla następnego elementu
            x += 150
            if x > 600:  # Nowy rząd
                x = 100
                y += 120
    
        return diagram


    def _clean_attribute_name(self, attr: str) -> str:
        """Wyczyść nazwę atrybutu z symboli PlantUML"""
        # Usuń prefiksy widoczności (+, -, #, ~)
        cleaned = re.sub(r'^[+\-#~]\s*', '', attr)
        # Weź tylko nazwę przed dwukropkiem (typ)
        return cleaned.split(':')[0].strip()
    
    def _clean_method_name(self, method: str) -> str:
        """Wyczyść nazwę metody"""
        cleaned = re.sub(r'^[+\-#~]\s*', '', method)
        # Weź część przed nawiasami
        return cleaned.split('(')[0].strip()
    
    def _get_visibility(self, member: str) -> str:
        """Określ widoczność na podstawie prefiksu PlantUML"""
        if member.startswith('+'):
            return 'public'
        elif member.startswith('-'):
            return 'private'
        elif member.startswith('#'):
            return 'protected'
        elif member.startswith('~'):
            return 'package'
        return 'public'  # domyślnie
    

    def _split_attribute(self, attr: str):
        # Rozdziela nazwę i typ atrybutu
        cleaned = re.sub(r'^[+\-#~]\s*', '', attr)
        parts = cleaned.split(':')
        name = parts[0].strip()
        attr_type = parts[1].strip() if len(parts) > 1 else None
        return name, attr_type

# Główna klasa konwertera
class PlantUMLToEAConverter:
    """Główny konwerter PlantUML do Enterprise Architect"""
    
    def __init__(self):
        self.parser = PlantUMLParser()
        self.xmi_generator = EAXMIGenerator()
    
    def convert(self, plantuml_code: str) -> str:
        """Konwertuje kod PlantUML na XMI dla EA"""
        # Parsuj PlantUML
        self.parser.parse(plantuml_code)
        
        # Generuj XMI
        xmi_content = self.xmi_generator.generate_xmi(
            self.parser.classes, 
            self.parser.relations,
            self.parser.enums,
            self.parser.notes 
        )
        
        return xmi_content
    
    def convert_file(self, input_file: str, output_file: str):
        """Konwertuje plik PlantUML na plik XMI"""
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        xmi_content = self.convert(plantuml_code)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xmi_content)
        
        print(f"Konwersja zakończona: {input_file} -> {output_file}")

# Przykład użycia
if __name__ == "__main__":
    # Przykładowy kod PlantUML
    sample_plantuml = """
    @startuml
    class Person {
        -name: String
        -age: int
        +getName(): String
        +setName(name: String): void
    }
    
    class Employee {
        -employeeId: String
        -salary: double
        +getEmployeeId(): String
    }
    
    Person <|-- Employee
    @enduml
    """
    
    # Konwertuj
    
    converter = PlantUMLToEAConverter()
    xmi_result = converter.convert(sample_plantuml)
    
    print("Wygenerowany XMI:")
    print(xmi_result[:500] + "...")  # Pokaż pierwsze 500 znaków

def plantuml_to_xmi(plantuml_code: str) -> str:
    """
    Funkcja pomocnicza do użycia w GUI – konwertuje kod PlantUML na XMI.
    """
    converter = PlantUMLToEAConverter()
    return converter.convert(plantuml_code)