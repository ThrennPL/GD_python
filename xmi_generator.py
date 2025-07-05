import re
import xml.etree.ElementTree as ET
import xml.dom.minidom
import uuid
from typing import Dict, List, Optional
from plantuml_model import UMLClass, UMLRelation, UMLEnum, UMLNote
from logger_utils import setup_logger, log_info, log_error, log_exception

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
        model.set('visibility', 'public') 
    
        # Package dla klas - z poprawnymi właściwościami EA
        package = ET.SubElement(model, 'packagedElement')
        package.set('xmi:type', 'uml:Package')
        package_id = f'EAPK_{uuid.uuid4()}'
        package.set('xmi:id', package_id)
        package.set('name', 'Classes')
        package.set('visibility', 'public') 
    
        # Generuj klasy z pełnymi metadanymi
        classes_data = {}
        for class_name, uml_class in classes.items():
            class_id = f'EAID_{uuid.uuid4()}'
            uml_class.xmi_id = class_id # Zapisz ID w obiekcie dla łatwego dostępu
            class_data_entry = {'obj': uml_class, 'attrs': {}, 'ops': {}}
            classes_data[class_name] = class_data_entry
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
                attr_id = f'EAID_{uuid.uuid4()}'
                attr_decl = attr["declaration"] 
                attr_name, attr_type = self._split_attribute(attr_decl) 
                modifiers = attr.get("modifiers", [])
                class_data_entry['attrs'][attr_name] = attr_id
                # Ustaw ID w elemencie
                attr_elem = ET.SubElement(class_elem, 'ownedAttribute')
                attr_elem.set('xmi:id', attr_id)
                attr_elem.set('xmi:type', 'uml:Property')
                attr_elem.set('name', attr_name)
                attr_elem.set('visibility', self._get_visibility(attr_decl))
                attr_elem.set('isStatic', 'false')
                attr_elem.set('isReadOnly', 'false')
                attr_elem.set('isDerived', 'false')
                attr_elem.set('isOrdered', 'false')
                attr_elem.set('isUnique', 'true')
                attr_elem.set('isDerivedUnion', 'false')

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
                
                ET.SubElement(attr_elem, 'lowerValue', {
                    'xmi:type': 'uml:LiteralInteger',
                    'xmi:id': f'EAID_LI{str(uuid.uuid4()).replace("-", "")[:6]}_{attr_id[-12:]}',
                    'value': '1'
                })
                ET.SubElement(attr_elem, 'upperValue', {
                    'xmi:type': 'uml:LiteralInteger',
                    'xmi:id': f'EAID_LI{str(uuid.uuid4()).replace("-", "")[:6]}_{attr_id[-12:]}',
                    'value': '1'
                })

            # Dodaj metody
            for method in uml_class.methods:
                op_id = f'EAID_{uuid.uuid4()}'
                method_name = self._clean_method_name(method["signature"])
                class_data_entry['ops'][method_name] = op_id
                # Ustaw ID w elemencie
                op_elem = ET.SubElement(class_elem, 'ownedOperation')
                op_elem.set('xmi:id', op_id)
                method_sig = method["signature"]
                modifiers = method.get("modifiers", [])
                op_elem.set('name', self._clean_method_name(method_sig))
                op_elem.set('visibility', self._get_visibility(method_sig))

                # Obsługa static/abstract
                if "static" in modifiers:
                    op_elem.set('isStatic', 'true')
                if "abstract" in modifiers:
                    op_elem.set('isAbstract', 'true')
                # (opcjonalnie) inne modyfikatory jako taggedValue
                if modifiers:
                    tagged = ET.SubElement(op_elem, 'taggedValue')
                    tagged.set('name', 'modifiers')
                    tagged.set('value', ','.join(modifiers))
            
            #classes_data[class_id] = class_data_entry
    
        class_ids = {class_name: data['obj'].xmi_id for class_name, data in classes_data.items()}

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

        connector_ids_map = {}

        # Generuj relacje - TO JEST KLUCZOWE
        for relation in relations:
            if relation.source in class_ids and relation.target in class_ids:
                rel_key = (relation.source, relation.target, relation.label)
                if relation.relation_type == 'inheritance':
                    # Generalizacja - specjalny przypadek, zostaje bez zmian
                    parent_elem = package.find(f".//packagedElement[@xmi:id='{class_ids[relation.source]}']", self.namespace)
                    if parent_elem is not None:
                        generalization = ET.SubElement(parent_elem, 'generalization')
                        gen_id = f'EAID_{uuid.uuid4()}'
                        generalization.set('xmi:id', gen_id)
                        generalization.set('general', class_ids[relation.target])
                        connector_ids_map[rel_key] = gen_id  # lub gen_id dla generalizacji
                    else:
                        log_error(f"Nie znaleziono klasy o xmi:id={class_ids[relation.source]} dla generalizacji!")

                elif relation.relation_type == 'association':
                    # Asocjacja - pełna definicja z końcówkami
                    assoc_id = f'EAID_{uuid.uuid4()}'
                    assoc_elem = ET.SubElement(package, 'packagedElement')
                    assoc_elem.set('xmi:type', 'uml:Association')
                    assoc_elem.set('xmi:id', assoc_id)
                    assoc_elem.set('name', relation.label or '')
                    assoc_elem.set('visibility', 'public')

                    # Definiujemy końcówki asocjacji (memberEnd i ownedEnd)
                    source_end_id = f'EAID_src_{uuid.uuid4()}'
                    target_end_id = f'EAID_tgt_{uuid.uuid4()}'
                    assoc_elem.set('memberEnd', f"{source_end_id} {target_end_id}")

                    # Właściwa definicja końcówek
                    owned_end_source = ET.SubElement(assoc_elem, 'ownedEnd')
                    owned_end_source.set('xmi:id', source_end_id)
                    owned_end_source.set('visibility', 'public')
                    owned_end_source.set('type', class_ids[relation.source])
                    owned_end_source.set('association', assoc_id)

                    owned_end_target = ET.SubElement(assoc_elem, 'ownedEnd')
                    owned_end_target.set('xmi:id', target_end_id)
                    owned_end_target.set('visibility', 'public')
                    owned_end_target.set('type', class_ids[relation.target])
                    owned_end_target.set('association', assoc_id)

                    # Definicja nawigowalności - źródło jest nawigowalne, cel nie
                    ET.SubElement(owned_end_source, 'lowerValue', {'xmi:type': 'uml:LiteralInteger', 'value': '0'})
                    ET.SubElement(owned_end_source, 'upperValue', {'xmi:type': 'uml:LiteralUnlimitedNatural', 'value': '*'})
                    
                    ET.SubElement(owned_end_target, 'lowerValue', {'xmi:type': 'uml:LiteralInteger', 'value': '0'})
                    ET.SubElement(owned_end_target, 'upperValue', {'xmi:type': 'uml:LiteralUnlimitedNatural', 'value': '*'})
                    
                    connector_ids_map[rel_key] = assoc_id
                elif relation.relation_type == 'usage':
                    usage_id = f'EAID_{uuid.uuid4()}'
                    usage_elem = ET.SubElement(package, 'packagedElement')
                    usage_elem.set('xmi:type', 'uml:Usage')
                    usage_elem.set('xmi:id', usage_id)
                    usage_elem.set('visibility', 'public')
                    usage_elem.set('supplier', class_ids[relation.target])
                    usage_elem.set('client', class_ids[relation.source])
                    connector_ids_map[rel_key] = usage_id
                elif relation.relation_type == 'dependency':
                    dep_id = f'EAID_{uuid.uuid4()}'
                    dep_elem = ET.SubElement(package, 'packagedElement')
                    dep_elem.set('xmi:type', 'uml:Dependency')
                    dep_elem.set('xmi:id', dep_id)
                    dep_elem.set('visibility', 'public')
                    dep_elem.set('supplier', class_ids[relation.target])
                    dep_elem.set('client', class_ids[relation.source])
                    connector_ids_map[rel_key] = dep_id
                elif relation.relation_type == 'aggregation':
                    # Asocjacja agregacji - podobna do zwykłej asocjacji, ale z innym typem
                    assoc_id = f'EAID_{uuid.uuid4()}'
                    assoc_elem = ET.SubElement(package, 'packagedElement')
                    assoc_elem.set('xmi:type', 'uml:Association')
                    assoc_elem.set('xmi:id', assoc_id)
                    assoc_elem.set('name', relation.label or '')
                    assoc_elem.set('visibility', 'public')

                    # Definiujemy końcówki asocjacji (memberEnd i ownedEnd)
                    source_end_id = f'EAID_src_{uuid.uuid4()}'
                    target_end_id = f'EAID_tgt_{uuid.uuid4()}'
                    assoc_elem.set('memberEnd', f"{source_end_id} {target_end_id}")

                    # Właściwa definicja końcówek
                    owned_end_source = ET.SubElement(assoc_elem, 'ownedEnd')
                    owned_end_source.set('xmi:id', source_end_id)
                    owned_end_source.set('visibility', 'public')
                    owned_end_source.set('type', class_ids[relation.source])
                    owned_end_source.set('association', assoc_id)

                    owned_end_target = ET.SubElement(assoc_elem, 'ownedEnd')
                    owned_end_target.set('xmi:id', target_end_id)
                    owned_end_target.set('visibility', 'public')
                    owned_end_target.set('type', class_ids[relation.target])
                    owned_end_target.set('association', assoc_id)

                    # Definicja nawigowalności - źródło jest nawigowalne, cel nie
                    ET.SubElement(owned_end_source, 'lowerValue', {'xmi:type': 'uml:LiteralInteger', 'value': '0'})
                    ET.SubElement(owned_end_source, 'upperValue', {'xmi:type': 'uml:LiteralUnlimitedNatural', 'value': '*'})
                    
                    ET.SubElement(owned_end_target, 'lowerValue', {'xmi:type': 'uml:LiteralInteger', 'value': '0'})
                    ET.SubElement(owned_end_target, 'upperValue', {'xmi:type': 'uml:LiteralUnlimitedNatural', 'value': '*'})
                
                else:
                    # --- NOWY KOD: Tworzymy pełny element uml:Association ---
                    assoc_id = f'EAID_{uuid.uuid4()}'
                    connector_ids_map[rel_key] = assoc_id

                    assoc_elem = ET.SubElement(package, 'packagedElement')
                    assoc_elem.set('xmi:type', 'uml:Association')
                    assoc_elem.set('xmi:id', assoc_id)
                    assoc_elem.set('name', relation.label or '')
                    assoc_elem.set('visibility', 'public')

                    # Definiujemy końcówki asocjacji (memberEnd i ownedEnd)
                    # To jest potrzebne dla pełnej definicji w UML
                    source_end_id = f'EAID_src_{uuid.uuid4()}'
                    target_end_id = f'EAID_tgt_{uuid.uuid4()}'
                    assoc_elem.set('memberEnd', f"{source_end_id} {target_end_id}")

                    # Właściwa definicja końcówek
                    owned_end_target = ET.SubElement(assoc_elem, 'ownedEnd')
                    owned_end_target.set('xmi:id', target_end_id)
                    owned_end_target.set('visibility', 'public')
                    owned_end_target.set('type', class_ids[relation.target])
                    owned_end_target.set('association', assoc_id)
                    
                    # Definicja nawigowalności - cel jest nawigowalny
                    ET.SubElement(owned_end_target, 'lowerValue', {'xmi:type': 'uml:LiteralInteger', 'value': '0'})
                    ET.SubElement(owned_end_target, 'upperValue', {'xmi:type': 'uml:LiteralUnlimitedNatural', 'value': '*'})
                    
                    # Druga końcówka (źródłowa) jest własnością asocjacji, ale nie jest nawigowalna
                    # Zgodnie z formatem EA, często jest definiowana wewnątrz typu, a nie jako ownedEnd
                    # Dla uproszczenia, na razie zostawiamy tak. Kluczowe jest, że cel jest ownedEnd.
            rel_key = (relation.source, relation.target, relation.label)
            # wygeneruj ID dla konektora (assoc_id lub gen_id)
            #connector_ids_map[rel_key] = new_connector_id
    

        connector_ids = list(connector_ids_map.values())
        # KLUCZOWE: EA Extension z wszystkimi metadanymi
        extension = self.generate_ea_extension_improved(
            xmi_root, classes_data, relations, enum_ids, package_id, connector_ids_map
        )

        
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

    def generate_ea_extension_improved(self, xmi_root, classes_data, relations, enums, package_id, connector_ids_map):
        """
        Ulepszona generacja EA Extension z pełną i szczegółową strukturą
        dla elementów, atrybutów, operacji i konektorów.
        
        Args:
            classes_data (dict): Słownik mapujący ID klasy na słownik z jej danymi:
                                {'obj': UMLClass, 'attrs': {name: id}, 'ops': {name: id}}
            connector_ids_map (dict): Słownik mapujący krotkę (source, target, label) na ID konektora.
        """
        extension = ET.SubElement(xmi_root, 'xmi:Extension')
        extension.set('extender', 'Enterprise Architect')
        extension.set('extenderID', '6.5')

        # ... (sekcje profiles, primitivetypes - bez zmian) ...
        profiles = ET.SubElement(extension, 'profiles')
        uml_profile = ET.SubElement(profiles, 'umlprofile')
        uml_profile.set('profiletype', 'uml2')
        primitive_types = ET.SubElement(extension, 'primitivetypes')
        basic_types = ['int', 'String', 'double', 'boolean', 'float', 'long', 'char', 'byte']
        for type_name in basic_types:
            ptype = ET.SubElement(primitive_types, 'primitivetype')
            ptype.set('xmi:id', f'eaxmiid_{uuid.uuid4()}')
            ptype.set('name', type_name)

        # --- NOWA, BARDZIEJ SZCZEGÓŁOWA SEKcja ELEMENTS ---
        elements = ET.SubElement(extension, 'elements')
        class_id_to_local_id = {}

        for class_id, data in classes_data.items():
            uml_class = data['obj']
            class_id = uml_class.xmi_id
            element = ET.SubElement(elements, 'element')
            element.set('xmi:idref', class_id)
            element.set('xmi:type', 'uml:Interface' if uml_class.stereotype == 'interface' else 'uml:Class')
            element.set('name', uml_class.name)
            element.set('scope', 'public')

            # <model> - zawiera ID lokalne i GUID
            local_id = str(self.ea_localid_counter)
            class_id_to_local_id[class_id] = local_id
            ET.SubElement(element, 'model', {
                'package': package_id,
                'tpos': '0',
                'ea_localid': local_id,
                'ea_eleType': 'element',
                'ea_guid': f'{{{uuid.uuid4()}}}'
            })
            self.ea_localid_counter += 1

            # <properties> - zawiera właściwości UML
            ET.SubElement(element, 'properties', {
                'isSpecification': 'false',
                'sType': 'Interface' if uml_class.stereotype == 'interface' else 'Class',
                'nType': '0',
                'scope': 'public',
                'isRoot': 'false',
                'isLeaf': 'false',
                'isAbstract': 'true' if any(m.get('modifiers') and 'abstract' in m.get('modifiers') for m in uml_class.methods) else 'false',
                'isActive': 'false'
            })

            # <project> - metadane projektu (mogą być statyczne)
            ET.SubElement(element, 'project', {
                'author': 'Converter', 'version': '1.0', 'phase': '1.0',
                'created': '2025-07-04 23:00:00', 'modified': '2025-07-04 23:00:00',
                'complexity': '1', 'status': 'Proposed'
            })

            ET.SubElement(element, 'code', {'gentype': 'Java'})
            ET.SubElement(element, 'style', {'appearance': 'BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;VSwimLanes=1;HSwimLanes=1;BorderStyle=0;'})
            ET.SubElement(element, 'tags')
            ET.SubElement(element, 'xrefs') # Pusty, EA go wypełni
            ET.SubElement(element, 'extendedProperties', {'tagged': '0', 'package_name': 'Classes'})

            # --- SEKCJA ATTRIBUTES ---
            if uml_class.attributes:
                attributes_section = ET.SubElement(element, 'attributes')
                for i, attr_data in enumerate(uml_class.attributes):
                    attr_name, attr_type = self._split_attribute(attr_data["declaration"])
                    attr_id = data['attrs'].get(attr_name)
                    if not attr_id: continue

                    attribute = ET.SubElement(attributes_section, 'attribute')
                    attribute.set('xmi:idref', attr_id)
                    attribute.set('name', attr_name)
                    attribute.set('scope', self._get_visibility(attr_data["declaration"]))

                    ET.SubElement(attribute, 'initial')
                    ET.SubElement(attribute, 'documentation')
                    ET.SubElement(attribute, 'model', {'ea_localid': str(self.ea_localid_counter), 'ea_guid': f'{{{uuid.uuid4()}}}'})
                    self.ea_localid_counter += 1
                    ET.SubElement(attribute, 'properties', {'derived': '0', 'collection': 'false', 'static': '1' if 'static' in attr_data.get('modifiers', []) else '0', 'duplicates': '0', 'changeability': 'changeable'})
                    ET.SubElement(attribute, 'coords', {'ordered': '0'})
                    ET.SubElement(attribute, 'containment', {'position': str(i)})
                    ET.SubElement(attribute, 'stereotype')
                    ET.SubElement(attribute, 'bounds', {'lower': '1', 'upper': '1'})
                    ET.SubElement(attribute, 'options')
                    ET.SubElement(attribute, 'style')
                    ET.SubElement(attribute, 'styleex', {'value': 'IsLiteral=0;'})
                    ET.SubElement(attribute, 'tags')
                    ET.SubElement(attribute, 'xrefs')

            # --- SEKCJA OPERATIONS ---
            if uml_class.methods:
                operations_section = ET.SubElement(element, 'operations')
                for i, method_data in enumerate(uml_class.methods):
                    method_name = self._clean_method_name(method_data["signature"])
                    method_id = data['ops'].get(method_name)
                    if not method_id: continue

                    operation = ET.SubElement(operations_section, 'operation')
                    operation.set('xmi:idref', method_id)
                    operation.set('name', method_name)
                    operation.set('scope', self._get_visibility(method_data["signature"]))

                    ET.SubElement(operation, 'properties', {'position': str(i)})
                    ET.SubElement(operation, 'stereotype')
                    ET.SubElement(operation, 'model', {'ea_guid': f'{{{uuid.uuid4()}}}', 'ea_localid': str(self.ea_localid_counter)})
                    self.ea_localid_counter += 1
                    ET.SubElement(operation, 'type', {'const': 'false', 'static': '1' if 'static' in method_data.get('modifiers', []) else '0', 'isAbstract': '1' if 'abstract' in method_data.get('modifiers', []) else '0', 'synchronised': '0', 'pure': '0', 'isQuery': 'false'})
                    ET.SubElement(operation, 'behaviour')
                    ET.SubElement(operation, 'code')
                    ET.SubElement(operation, 'style')
                    ET.SubElement(operation, 'styleex')
                    ET.SubElement(operation, 'documentation')
                    ET.SubElement(operation, 'tags')
                    ET.SubElement(operation, 'xrefs')

            # --- SEKCJA LINKS ---
            outgoing_relations = [rel for rel in relations if rel.source == uml_class.name]
            if outgoing_relations:
                links_section = ET.SubElement(element, 'links')
                for rel in outgoing_relations:
                    rel_key = (rel.source, rel.target, rel.label)
                    conn_id = connector_ids_map.get(rel_key)
                    if conn_id:
                        rel_type_name = self._map_relation_type_to_ea(rel.relation_type)
                        link = ET.SubElement(links_section, rel_type_name)
                        link.set('xmi:id', conn_id) # Tutaj używamy xmi:id, bo to jest definicja linku
                        link.set('start', class_id)
                        link.set('end', classes_data[rel.target]['obj'].xmi_id) # Potrzebujemy ID celu

        # Sekcja CONNECTORS (pozostaje taka sama jak w poprzedniej poprawce)
        # ... wklej tutaj kompletną sekcję generowania konektorów z poprzedniej odpowiedzi ...
        # Poniżej skrócona wersja dla kontekstu
        connectors = ET.SubElement(extension, 'connectors')
        for relation in relations:
            rel_key = (relation.source, relation.target, relation.label)
            conn_id = connector_ids_map.get(rel_key)
            if not conn_id:
                continue

            connector = ET.SubElement(connectors, 'connector')
            connector.set('xmi:idref', conn_id)

            # Źródło
            source_id = classes_data[relation.source]['obj'].xmi_id
            source_elem = ET.SubElement(connector, 'source', {'xmi:idref': source_id})
            ET.SubElement(source_elem, 'model', {
                'ea_localid': str(self.ea_localid_counter),
                'type': 'Class',
                'name': relation.source
            })
            self.ea_localid_counter += 1
            ET.SubElement(source_elem, 'role', {'visibility': 'Public', 'targetScope': 'instance'})
            ET.SubElement(source_elem, 'type', {'aggregation': 'none', 'containment': 'Unspecified'})
            ET.SubElement(source_elem, 'constraints')
            ET.SubElement(source_elem, 'modifiers', {'isOrdered': 'false', 'changeable': 'none', 'isNavigable': 'false'})
            ET.SubElement(source_elem, 'style', {'value': 'Union=0;Derived=0;AllowDuplicates=0;Owned=0;Navigable=Non-Navigable;'})
            ET.SubElement(source_elem, 'documentation')
            ET.SubElement(source_elem, 'xrefs')
            ET.SubElement(source_elem, 'tags')

            # Cel
            target_id = classes_data[relation.target]['obj'].xmi_id
            target_elem = ET.SubElement(connector, 'target', {'xmi:idref': target_id})
            ET.SubElement(target_elem, 'model', {
                'ea_localid': str(self.ea_localid_counter),
                'type': 'Class',
                'name': relation.target
            })
            self.ea_localid_counter += 1
            ET.SubElement(target_elem, 'role', {'visibility': 'Public', 'targetScope': 'instance'})
            ET.SubElement(target_elem, 'type', {'aggregation': 'none', 'containment': 'Unspecified'})
            ET.SubElement(target_elem, 'constraints')
            ET.SubElement(target_elem, 'modifiers', {'isOrdered': 'false', 'changeable': 'none', 'isNavigable': 'true'})
            ET.SubElement(target_elem, 'style', {'value': 'Union=0;Derived=0;AllowDuplicates=0;Owned=0;Navigable=Navigable;'})
            ET.SubElement(target_elem, 'documentation')
            ET.SubElement(target_elem, 'xrefs')
            ET.SubElement(target_elem, 'tags')

            # Pozostałe sekcje konektora
            ET.SubElement(connector, 'model', {'ea_localid': str(self.ea_localid_counter)})
            self.ea_localid_counter += 1
            ET.SubElement(connector, 'properties', {'ea_type': self._map_relation_type_to_ea(relation.relation_type), 'direction': 'Source -> Destination'})
            ET.SubElement(connector, 'modifiers', {'isRoot': 'false', 'isLeaf': 'false'})
            ET.SubElement(connector, 'documentation')
            ET.SubElement(connector, 'appearance', {'linemode': '3', 'linecolor': '-1', 'linewidth': '0', 'seqno': '0', 'headStyle': '0', 'lineStyle': '0'})
            ET.SubElement(connector, 'labels', {'mb': f'«{relation.relation_type}»'})
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
