import re
import xml.etree.ElementTree as ET
import xml.dom.minidom
import uuid
from typing import Dict, List, Optional
from plantuml_model import UMLClass, UMLRelation, UMLEnum, UMLNote

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
                attr_decl = attr["declaration"]
                modifiers = attr.get("modifiers", [])
                attr_name, attr_type = self._split_attribute(attr_decl)
                attr_elem = ET.SubElement(class_elem, 'ownedAttribute')
                attr_elem.set('xmi:id', f'EAID_{uuid.uuid4()}')
                attr_elem.set('name', attr_name)
                attr_elem.set('visibility', self._get_visibility(attr_decl))

                # Obsługa static/readonly
                if "static" in modifiers:
                    attr_elem.set('isStatic', 'true')
                if "readonly" in modifiers:
                    attr_elem.set('isReadOnly', 'true')
                # (opcjonalnie) inne modyfikatory jako taggedValue
                if modifiers:
                    tagged = ET.SubElement(attr_elem, 'taggedValue')
                    tagged.set('name', 'modifiers')
                    tagged.set('value', ','.join(modifiers))

                # Typ atrybutu - EA wymaga referencji
                if attr_type:
                    type_elem = ET.SubElement(attr_elem, 'type')
                    type_elem.set('xmi:type', 'uml:PrimitiveType')
                    type_elem.set('href', f'pathmap://UML_LIBRARIES/EcorePrimitiveTypes.library.uml#{attr_type}')

            # Dodaj metody
            for method in uml_class.methods:
                method_elem = ET.SubElement(class_elem, 'ownedOperation')
                method_elem.set('xmi:id', f'EAID_{uuid.uuid4()}')
                method_sig = method["signature"]
                modifiers = method.get("modifiers", [])
                method_elem.set('name', self._clean_method_name(method_sig))
                method_elem.set('visibility', self._get_visibility(method_sig))

                # Obsługa static/abstract
                if "static" in modifiers:
                    method_elem.set('isStatic', 'true')
                if "abstract" in modifiers:
                    method_elem.set('isAbstract', 'true')
                # (opcjonalnie) inne modyfikatory jako taggedValue
                if modifiers:
                    tagged = ET.SubElement(method_elem, 'taggedValue')
                    tagged.set('name', 'modifiers')
                    tagged.set('value', ','.join(modifiers))
    
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

        connector_ids = []

        # Generuj relacje - TO JEST KLUCZOWE
        for relation in relations:
            if relation.source in class_ids and relation.target in class_ids:
            
                if relation.relation_type == 'inheritance':
                    # Generalizacja - specjalny przypadek, zostaje bez zmian
                    generalization = ET.SubElement(
                        package.find(f".//packagedElement[@xmi:id='{class_ids[relation.source]}']", self.namespace),
                        'generalization'
                    )
                    gen_id = f'EAID_{uuid.uuid4()}'
                    generalization.set('xmi:id', gen_id)
                    generalization.set('general', class_ids[relation.target])
                    connector_ids.append(gen_id)
                
                else:
                    # Dla innych relacji generujemy tylko ID dla konektora w sekcji Extension.
                    # NIE tworzymy już elementu <packagedElement> typu uml:Association.
                    # Dzięki temu EA nie stworzy dodatkowego elementu w drzewie projektu.
                    conn_id = f'EAID_{uuid.uuid4()}'
                    connector_ids.append(conn_id)
    
        # KLUCZOWE: EA Extension z wszystkimi metadanymi
        extension = self.generate_ea_extension_improved(xmi_root, class_ids, relations, enum_ids, package_id, connector_ids)

    
        # Generuj diagram
        self.generate_diagram_with_layout(
            extension, 
            class_ids, 
            relations, 
            package_id,
            connector_ids
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

    def generate_ea_extension_improved(self, xmi_root, classes, relations, enums, package_id, connector_ids):
        """Ulepszona generacja EA Extension z poprawną strukturą konektorów."""
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
    
        # Używamy słownika do mapowania nazw klas na ich obiekty UMLClass dla łatwiejszego dostępu
        # Zakładając, że `classes` przekazane do `generate_xmi` to słownik `Dict[str, UMLClass]`
        # Jeśli nie, trzeba będzie go przekazać dodatkowo do tej funkcji.
        # W tym kodzie zakładam, że `classes` to `class_ids` z oryginalnego kodu (Dict[str, str])
        # i potrzebujemy dostępu do nazwy klasy.
        
        rel_iterator = iter(relations)
        
        for conn_id in connector_ids:
            relation = next(rel_iterator)
            if relation.source not in classes or relation.target not in classes:
                continue

            connector = ET.SubElement(connectors, 'connector')
            
            # Dla dziedziczenia referencjujemy istniejący element generalizacji
            if relation.relation_type == 'inheritance':
                connector.set('xmi:idref', conn_id)
                
                # Właściwości dla generalizacji są prostsze
                properties = ET.SubElement(connector, 'properties')
                properties.set('ea_type', 'Generalization')
                properties.set('direction', 'Source -> Destination')
                properties.set('stereotype', 'Generalization')

                source = ET.SubElement(connector, 'source', {'xmi:idref': classes[relation.source]})
                target = ET.SubElement(connector, 'target', {'xmi:idref': classes[relation.target]})
                
            else:
                # Dla innych relacji tworzymy nowy konektor z pełną strukturą EA
                connector.set('xmi:id', conn_id)

                # --- ŹRÓDŁO RELACJI ---
                source = ET.SubElement(connector, 'source')
                source.set('xmi:idref', classes[relation.source])
                ET.SubElement(source, 'model', {'type': 'Class', 'name': relation.source})
                ET.SubElement(source, 'role', {
                    'visibility': 'Public', 
                    'targetScope': 'instance',
                    'multiplicity': relation.source_multiplicity or '1..1'
                })
                ET.SubElement(source, 'type', {
                    'aggregation': 'composite' if relation.relation_type == 'composition' else 'none',
                    'containment': 'Unspecified'
                })
                ET.SubElement(source, 'modifiers', {'isOrdered': 'false', 'changeable': 'none', 'isNavigable': 'false'})
                ET.SubElement(source, 'style', {'Navigable': 'Non-Navigable'})

                # --- CEL RELACJI ---
                target = ET.SubElement(connector, 'target')
                target.set('xmi:idref', classes[relation.target])
                ET.SubElement(target, 'model', {'type': 'Class', 'name': relation.target})
                ET.SubElement(target, 'role', {
                    'visibility': 'Public', 
                    'targetScope': 'instance',
                    'multiplicity': relation.target_multiplicity or '1..1'
                })
                ET.SubElement(target, 'type', {'aggregation': 'none', 'containment': 'Unspecified'})
                ET.SubElement(target, 'modifiers', {'isOrdered': 'false', 'changeable': 'none', 'isNavigable': 'true'})
                ET.SubElement(target, 'style', {'Navigable': 'Navigable'})
                
                # --- WŁAŚCIWOŚCI SAMEGO KONEKTORA ---
                ET.SubElement(connector, 'model', {'ea_localid': str(self.ea_localid_counter)})
                self.ea_localid_counter += 1

                properties = ET.SubElement(connector, 'properties', {
                    'ea_type': self._map_relation_type_to_ea(relation.relation_type),
                    'direction': 'Source -> Destination'
                })
                if relation.label:
                    properties.set('name', relation.label)

                ET.SubElement(connector, 'modifiers', {'isRoot': 'false', 'isLeaf': 'false'})
                ET.SubElement(connector, 'appearance', {
                    'linemode': '3', 'linecolor': '-1', 'linewidth': '0', 'seqno': '0', 'headStyle': '0', 'lineStyle': '0'
                })
                
                # Etykieta stereotypu (np. <<use>>)
                if relation.relation_type == 'dependency':
                     ET.SubElement(connector, 'labels', {'mb': '«use»'})
                else:
                     ET.SubElement(connector, 'labels')
                     
                ET.SubElement(connector, 'extendedProperties', {'virtualInheritance': '0'})
                ET.SubElement(connector, 'style')
                ET.SubElement(connector, 'xrefs')
                ET.SubElement(connector, 'tags')
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
    def generate_diagram_with_layout(self, extension, classes, relations, package_id, connector_ids):
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
    
        connectors = ET.SubElement(diagram, 'connectors')
        for conn_id in connector_ids:
            connector = ET.SubElement(connectors, 'connector')
            connector.set('connector_id', conn_id)

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
