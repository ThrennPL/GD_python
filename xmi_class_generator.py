import re
import xml.etree.ElementTree as ET
import xml.dom.minidom
import uuid
from typing import Dict, List, Optional, Tuple
from plantuml_model import UMLClass, UMLRelation, UMLEnum, UMLNote
from plantuml_class_parser import PlantUMLParser
from logger_utils import setup_logger, log_info, log_error, log_exception

setup_logger("xmi_generator.log")

class XMIGenerator:
    """Generator plików XMI dla diagramów klas Enterprise Architect"""
    
    def __init__(self, autor: str = "195841"):
        """
        Inicjalizuje generator XMI.
        
        Args:
            autor: Autor diagramu (domyślnie "195841")
        """
        self.autor = autor
        self.id_map = {}
        self.ea_localid_counter = 1
        self.namespace = {
            'xmi': 'http://www.omg.org/XMI',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'uml': 'http://www.eclipse.org/uml2/3.0.0/UML'
        }
        self._zarejestruj_przestrzenie_nazw()
    
    def _zarejestruj_przestrzenie_nazw(self):
        """Rejestruje przestrzenie nazw XML."""
        ET.register_namespace('xmi', 'http://www.omg.org/XMI')
        ET.register_namespace('uml', 'http://www.eclipse.org/uml2/5.0.0/UML')
        ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        ET.register_namespace('eaProfile', 'http://www.sparxsystems.com/profiles/eaProfile/1.0')
    
    def _generuj_ea_id(self, prefix: str = "EAID") -> str:
        """Generuje unikalny identyfikator zgodny z EA"""
        return f"{prefix}_{uuid.uuid4()}"
    
    def _stworz_korzen_dokumentu(self) -> ET.Element:
        """
        Tworzy główny element XMI.
        Returns:
            Główny element XMI
        """
        # Główny element XMI z poprawnymi przestrzeniami nazw dla EA
        xmi_root = ET.Element('xmi:XMI')
        xmi_root.set('xmi:version', '2.0')
        xmi_root.set('xmlns:uml', 'http://www.eclipse.org/uml2/5.0.0/UML')
        xmi_root.set('xmlns:xmi', 'http://www.omg.org/XMI')
        xmi_root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        xmi_root.set('xmlns:eaProfile', 'http://www.sparxsystems.com/profiles/eaProfile/1.0')
        
        # Documentation - EA to lubi
        ET.SubElement(xmi_root, 'xmi:Documentation', {
            'exporter': 'Enterprise Architect',
            'exporterVersion': '15.2'
        })
        
        return xmi_root
    
    def _stworz_model_uml(self, root: ET.Element, nazwa_diagramu: str) -> ET.Element:
        """
        Tworzy główny model UML.
        Args:
            root: Element główny dokumentu
            nazwa_diagramu: Nazwa diagramu
        Returns:
            Element modelu UML
        """
        model_id = self._generuj_ea_id()
        self.id_map['model'] = model_id
        
        model = ET.SubElement(root, 'uml:Model')
        model.set('xmi:id', model_id)
        model.set('name', nazwa_diagramu)
        model.set('visibility', 'public')
        
        return model
    
    def _stworz_pakiet_diagramu(self, model: ET.Element, nazwa_pakietu: str) -> ET.Element:
        """
        Tworzy pakiet dla diagramu klas.
        Args:
            model: Element modelu UML
            nazwa_pakietu: Nazwa pakietu
        Returns:
            Element pakietu
        """
        package_id = self._generuj_ea_id("EAPK")
        self.id_map['package_element'] = package_id
        
        package_element = ET.SubElement(model, 'packagedElement')
        package_element.set('xmi:type', 'uml:Package')
        package_element.set('xmi:id', package_id)
        package_element.set('name', nazwa_pakietu)
        package_element.set('visibility', 'public')
        
        return package_element
    
    def _dodaj_klase(self, package: ET.Element, uml_class: UMLClass) -> str:
        """
        Dodaje klasę do pakietu.
        Args:
            package: Element pakietu
            uml_class: Obiekt klasy UML do dodania
        Returns:
            ID wygenerowanej klasy
        """
        class_id = self._generuj_ea_id()
        self.id_map[f"class_{uml_class.name}"] = class_id
        
        # Obsługa interfejsów vs klas
        if uml_class.stereotype == 'interface':
            class_elem = ET.SubElement(package, 'packagedElement')
            class_elem.set('xmi:type', 'uml:Interface')
        else:
            class_elem = ET.SubElement(package, 'packagedElement')
            class_elem.set('xmi:type', 'uml:Class')
        
        class_elem.set('xmi:id', class_id)
        class_elem.set('name', uml_class.name)
        class_elem.set('visibility', 'public')
        
        if uml_class.is_abstract:
            class_elem.set('isAbstract', 'true')
        
        # Dodaj atrybuty
        for attr in uml_class.attributes:
            attr_id = self._generuj_ea_id()
            attr_decl = attr["declaration"]
            attr_name, attr_type = self._split_attribute(attr_decl)
            modifiers = attr.get("modifiers", [])
            
            attr_elem = ET.SubElement(class_elem, 'ownedAttribute')
            attr_elem.set('xmi:id', attr_id)
            attr_elem.set('xmi:type', 'uml:Property')
            attr_elem.set('name', attr_name)
            attr_elem.set('visibility', self._get_visibility(attr_decl))
            attr_elem.set('isStatic', 'true' if "static" in modifiers else 'false')
            attr_elem.set('isReadOnly', 'true' if "readonly" in modifiers else 'false')
            attr_elem.set('isDerived', 'false')
            attr_elem.set('isOrdered', 'false')
            attr_elem.set('isUnique', 'true')
            attr_elem.set('isDerivedUnion', 'false')
            
            # Typ atrybutu - EA wymaga referencji
            if attr_type:
                type_elem = ET.SubElement(attr_elem, 'type')
                type_elem.set('xmi:type', 'uml:PrimitiveType')
                type_elem.set('href', f'pathmap://UML_LIBRARIES/EcorePrimitiveTypes.library.uml#{attr_type}')
            
            ET.SubElement(attr_elem, 'lowerValue', {
                'xmi:type': 'uml:LiteralInteger',
                'xmi:id': f'{self._generuj_ea_id("EAID_LI")}',
                'value': '1'
            })
            ET.SubElement(attr_elem, 'upperValue', {
                'xmi:type': 'uml:LiteralInteger',
                'xmi:id': f'{self._generuj_ea_id("EAID_LI")}',
                'value': '1'
            })
            
            # Zapisz ID atrybutu w mapie
            self.id_map[f"attr_{uml_class.name}_{attr_name}"] = attr_id
        
        # Dodaj metody
        for method in uml_class.methods:
            method_id = self._generuj_ea_id()
            method_sig = method["signature"]
            method_name = self._clean_method_name(method_sig)
            modifiers = method.get("modifiers", [])
            
            op_elem = ET.SubElement(class_elem, 'ownedOperation')
            op_elem.set('xmi:id', method_id)
            op_elem.set('name', method_name)
            op_elem.set('visibility', self._get_visibility(method_sig))
            
            # Obsługa static/abstract
            if "static" in modifiers:
                op_elem.set('isStatic', 'true')
            if "abstract" in modifiers:
                op_elem.set('isAbstract', 'true')
                
            # Zapisz ID metody w mapie
            self.id_map[f"method_{uml_class.name}_{method_name}"] = method_id
        
        return class_id
    
    def _dodaj_enum(self, package: ET.Element, uml_enum: UMLEnum) -> str:
        """
        Dodaje enumerator do pakietu.
        Args:
            package: Element pakietu
            uml_enum: Obiekt enumeratora UML do dodania
        Returns:
            ID wygenerowanego enumeratora
        """
        enum_id = self._generuj_ea_id()
        self.id_map[f"enum_{uml_enum.name}"] = enum_id
        
        enum_elem = ET.SubElement(package, 'packagedElement')
        enum_elem.set('xmi:type', 'uml:Enumeration')
        enum_elem.set('xmi:id', enum_id)
        enum_elem.set('name', uml_enum.name)
        enum_elem.set('visibility', 'public')
        
        # Dodaj wartości enumeratora
        for value in uml_enum.values:
            literal_id = self._generuj_ea_id()
            literal_elem = ET.SubElement(enum_elem, 'ownedLiteral')
            literal_elem.set('xmi:id', literal_id)
            literal_elem.set('name', value)
            
            self.id_map[f"literal_{uml_enum.name}_{value}"] = literal_id
        
        return enum_id
    
    def _dodaj_relacje(self, package: ET.Element, relations: List[UMLRelation], 
                       class_ids: Dict[str, str], enum_ids: Dict[str, str]) -> Dict:
        """
        Dodaje relacje między klasami/enumami.
        Args:
            package: Element pakietu
            relations: Lista relacji UML
            class_ids: Słownik mapujący nazwy klas na ich ID
            enum_ids: Słownik mapujący nazwy enumów na ich ID
        Returns:
            Słownik mapujący identyfikatory relacji
        """
        connector_ids_map = {}
        
        for relation in relations:
            # Sprawdź czy źródło i cel istnieją
            source_id = class_ids.get(relation.source) or enum_ids.get(relation.source)
            target_id = class_ids.get(relation.target) or enum_ids.get(relation.target)
            
            if not source_id or not target_id:
                log_error(f"Nie znaleziono klasy/enuma: {relation.source} lub {relation.target}")
                continue
                
            rel_key = (relation.source, relation.target, relation.label)
            
            # Obsługa różnych typów relacji
            if relation.relation_type == 'inheritance':
                # Generalizacja
                gen_id = self._generuj_ea_id()
                connector_ids_map[rel_key] = gen_id
                
                generalization = ET.SubElement(package, 'generalization')
                generalization.set('xmi:type', 'uml:Generalization')
                generalization.set('xmi:id', gen_id)
                generalization.set('general', target_id)
                generalization.set('specific', source_id)
                
                if relation.label:
                    generalization.set('name', relation.label)
                    
            elif relation.relation_type in ['association', 'aggregation', 'composition']:
                # Asocjacja, agregacja, kompozycja
                assoc_id = self._generuj_ea_id()
                connector_ids_map[rel_key] = assoc_id
                
                assoc_elem = ET.SubElement(package, 'packagedElement')
                assoc_elem.set('xmi:type', 'uml:Association')
                assoc_elem.set('xmi:id', assoc_id)
                
                if relation.label:
                    assoc_elem.set('name', relation.label)
                
                assoc_elem.set('visibility', 'public')
                
                # Definiujemy końcówki asocjacji
                source_end_id = self._generuj_ea_id("EAID_src")
                target_end_id = self._generuj_ea_id("EAID_tgt")
                
                # Dodaj memberEnd jako osobne elementy
                ET.SubElement(assoc_elem, 'memberEnd', {'xmi:idref': source_end_id})
                ET.SubElement(assoc_elem, 'memberEnd', {'xmi:idref': target_end_id})
                
                # Source end
                owned_end_source = ET.SubElement(assoc_elem, 'ownedEnd')
                owned_end_source.set('xmi:id', source_end_id)
                owned_end_source.set('visibility', 'public')
                owned_end_source.set('type', source_id)
                owned_end_source.set('association', assoc_id)
                
                # Target end
                owned_end_target = ET.SubElement(assoc_elem, 'ownedEnd')
                owned_end_target.set('xmi:id', target_end_id)
                owned_end_target.set('visibility', 'public')
                owned_end_target.set('type', target_id)
                owned_end_target.set('association', assoc_id)
                
                # Ustawienie typu agregacji
                if relation.relation_type == 'aggregation':
                    owned_end_target.set('aggregation', 'shared')
                elif relation.relation_type == 'composition':
                    owned_end_target.set('aggregation', 'composite')
                
                # Multiplicity
                src_lower, src_upper = PlantUMLParser.parse_multiplicity(relation.source_multiplicity)
                tgt_lower, tgt_upper = PlantUMLParser.parse_multiplicity(relation.target_multiplicity)
                
                ET.SubElement(owned_end_source, 'lowerValue', {'xmi:type': 'uml:LiteralInteger', 'value': src_lower})
                ET.SubElement(owned_end_source, 'upperValue', {'xmi:type': 'uml:LiteralUnlimitedNatural', 'value': src_upper})
                ET.SubElement(owned_end_target, 'lowerValue', {'xmi:type': 'uml:LiteralInteger', 'value': tgt_lower})
                ET.SubElement(owned_end_target, 'upperValue', {'xmi:type': 'uml:LiteralUnlimitedNatural', 'value': tgt_upper})
                
            elif relation.relation_type == 'dependency':
                # Zależność
                dep_id = self._generuj_ea_id()
                connector_ids_map[rel_key] = dep_id
                
                dep_elem = ET.SubElement(package, 'packagedElement')
                dep_elem.set('xmi:type', 'uml:Dependency')
                dep_elem.set('xmi:id', dep_id)
                dep_elem.set('visibility', 'public')
                dep_elem.set('client', source_id)
                dep_elem.set('supplier', target_id)
                
                if relation.label:
                    dep_elem.set('name', relation.label)
                
            elif relation.relation_type == 'usage':
                # Użycie
                usage_id = self._generuj_ea_id()
                connector_ids_map[rel_key] = usage_id
                
                usage_elem = ET.SubElement(package, 'packagedElement')
                usage_elem.set('xmi:type', 'uml:Usage')
                usage_elem.set('xmi:id', usage_id)
                usage_elem.set('visibility', 'public')
                usage_elem.set('client', source_id)
                usage_elem.set('supplier', target_id)
                
                if relation.label:
                    usage_elem.set('name', relation.label)
        
        return connector_ids_map
    
    def _stworz_rozszerzenia_ea(self, root: ET.Element, classes: Dict[str, UMLClass], 
                               relations: List[UMLRelation], connector_ids_map: Dict) -> None:
        """
        Tworzy rozszerzenia specyficzne dla Enterprise Architect.
        Args:
            root: Element główny dokumentu
            classes: Słownik klas UML
            relations: Lista relacji UML
            connector_ids_map: Mapa ID konektorów
        """
        extension = ET.SubElement(root, 'xmi:Extension')
        extension.set('extender', 'Enterprise Architect')
        extension.set('extenderID', '6.5')
        
        # Elements section
        elements_node = ET.SubElement(extension, 'elements')
        
        # Dodaj pakiet do elements
        package_element = ET.SubElement(elements_node, 'element')
        package_element.set('xmi:idref', self.id_map['package_element'])
        package_element.set('xmi:type', 'uml:Package')
        package_element.set('name', 'Classes')
        package_element.set('scope', 'public')
        
        # Dodaj model package2
        ET.SubElement(package_element, 'model', {
            'package2': self.id_map['package_element'],
            'package': self.id_map['model'],
            'tpos': '0',
            'ea_localid': str(self.ea_localid_counter),
            'ea_eleType': 'package'
        })
        self.ea_localid_counter += 1
        
        # Dodaj properties
        ET.SubElement(package_element, 'properties', {
            'isSpecification': 'false', 'sType': 'Package', 'nType': '0', 'scope': 'public'
        })
        
        # Dodaj project
        ET.SubElement(package_element, 'project', {
            'author': self.autor, 'version': '1.0', 'phase': '1.0',
            'created': self._get_current_time(), 'modified': self._get_current_time(),
            'complexity': '1', 'status': 'Proposed'
        })
        
        # Dodaj inne elementy pakietu
        ET.SubElement(package_element, 'code', {'gentype': 'Java'})
        ET.SubElement(package_element, 'style', {
            'appearance': 'BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;VSwimLanes=1;HSwimLanes=1;BorderStyle=0;'
        })
        ET.SubElement(package_element, 'tags')
        ET.SubElement(package_element, 'xrefs')
        ET.SubElement(package_element, 'extendedProperties', {'tagged': '0', 'package_name': 'Example Model'})
        ET.SubElement(package_element, 'packageproperties', {'version': '1.0'})
        ET.SubElement(package_element, 'paths')
        ET.SubElement(package_element, 'times', {'created': self._get_current_time(), 'modified': self._get_current_time()})
        ET.SubElement(package_element, 'flags', {
            'iscontrolled': 'FALSE', 'isprotected': 'FALSE', 'usedtd': 'FALSE', 
            'logxml': 'FALSE', 'packageFlags': 'isModel=1;VICON=3;'
        })
        
        # Dodaj elementy dla klas
        class_id_to_local_id = {}
        
        for class_name, uml_class in classes.items():
            class_id = self.id_map.get(f"class_{class_name}")
            if not class_id:
                continue
                
            element = ET.SubElement(elements_node, 'element')
            element.set('xmi:idref', class_id)
            element.set('xmi:type', 'uml:Interface' if uml_class.stereotype == 'interface' else 'uml:Class')
            element.set('name', class_name)
            element.set('scope', 'public')
            
            # <model> - zawiera ID lokalne i GUID
            local_id = str(self.ea_localid_counter)
            class_id_to_local_id[class_id] = local_id
            ET.SubElement(element, 'model', {
                'package': self.id_map['package_element'],
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
                'isAbstract': 'true' if uml_class.is_abstract else 'false',
                'isActive': 'false'
            })
            
            # <project> - metadane projektu
            ET.SubElement(element, 'project', {
                'author': self.autor, 'version': '1.0', 'phase': '1.0',
                'created': self._get_current_time(), 'modified': self._get_current_time(),
                'complexity': '1', 'status': 'Proposed'
            })
            
            ET.SubElement(element, 'code', {'gentype': 'Java'})
            ET.SubElement(element, 'style', {'appearance': 'BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;VSwimLanes=1;HSwimLanes=1;BorderStyle=0;'})
            ET.SubElement(element, 'tags')
            ET.SubElement(element, 'xrefs')
            ET.SubElement(element, 'extendedProperties', {'tagged': '0', 'package_name': 'Classes'})
            
            # Dodaj sekcję atrybutów
            if uml_class.attributes:
                attributes_section = ET.SubElement(element, 'attributes')
                for i, attr_data in enumerate(uml_class.attributes):
                    attr_name, _ = self._split_attribute(attr_data["declaration"])
                    attr_id = self.id_map.get(f"attr_{class_name}_{attr_name}")
                    if not attr_id:
                        continue
                        
                    attribute = ET.SubElement(attributes_section, 'attribute')
                    attribute.set('xmi:idref', attr_id)
                    attribute.set('name', attr_name)
                    attribute.set('scope', self._get_visibility(attr_data["declaration"]))
                    
                    ET.SubElement(attribute, 'initial')
                    ET.SubElement(attribute, 'documentation')
                    ET.SubElement(attribute, 'model', {'ea_localid': str(self.ea_localid_counter), 'ea_guid': f'{{{uuid.uuid4()}}}'})
                    self.ea_localid_counter += 1
                    
                    is_static = '1' if 'static' in attr_data.get('modifiers', []) else '0'
                    ET.SubElement(attribute, 'properties', {
                        'derived': '0', 'collection': 'false', 
                        'static': is_static, 'duplicates': '0', 
                        'changeability': 'changeable'
                    })
                    
                    ET.SubElement(attribute, 'coords', {'ordered': '0'})
                    ET.SubElement(attribute, 'containment', {'position': str(i)})
                    ET.SubElement(attribute, 'stereotype')
                    ET.SubElement(attribute, 'bounds', {'lower': '1', 'upper': '1'})
                    ET.SubElement(attribute, 'options')
                    ET.SubElement(attribute, 'style')
                    ET.SubElement(attribute, 'styleex', {'value': 'IsLiteral=0;'})
                    ET.SubElement(attribute, 'tags')
                    ET.SubElement(attribute, 'xrefs')
            
            # Dodaj sekcję metod
            if uml_class.methods:
                operations_section = ET.SubElement(element, 'operations')
                for i, method_data in enumerate(uml_class.methods):
                    method_name = self._clean_method_name(method_data["signature"])
                    method_id = self.id_map.get(f"method_{class_name}_{method_name}")
                    if not method_id:
                        continue
                        
                    operation = ET.SubElement(operations_section, 'operation')
                    operation.set('xmi:idref', method_id)
                    operation.set('name', method_name)
                    operation.set('scope', self._get_visibility(method_data["signature"]))
                    
                    ET.SubElement(operation, 'properties', {'position': str(i)})
                    ET.SubElement(operation, 'stereotype')
                    ET.SubElement(operation, 'model', {'ea_guid': f'{{{uuid.uuid4()}}}', 'ea_localid': str(self.ea_localid_counter)})
                    self.ea_localid_counter += 1
                    
                    is_static = '1' if 'static' in method_data.get('modifiers', []) else '0'
                    is_abstract = '1' if 'abstract' in method_data.get('modifiers', []) else '0'
                    ET.SubElement(operation, 'type', {
                        'const': 'false', 'static': is_static, 
                        'isAbstract': is_abstract, 'synchronised': '0', 
                        'pure': '0', 'isQuery': 'false'
                    })
                    
                    ET.SubElement(operation, 'behaviour')
                    ET.SubElement(operation, 'code')
                    ET.SubElement(operation, 'style')
                    ET.SubElement(operation, 'styleex')
                    ET.SubElement(operation, 'documentation')
                    ET.SubElement(operation, 'tags')
                    ET.SubElement(operation, 'xrefs')
        
        # Connectors section
        connectors = ET.SubElement(extension, 'connectors')
        
        for relation in relations:
            rel_key = (relation.source, relation.target, relation.label)
            conn_id = connector_ids_map.get(rel_key)
            if not conn_id:
                continue
                
            connector = ET.SubElement(connectors, 'connector')
            connector.set('xmi:idref', conn_id)
            
            # Source
            source_id = self.id_map.get(f"class_{relation.source}") or self.id_map.get(f"enum_{relation.source}")
            if not source_id:
                continue
                
            source_elem = ET.SubElement(connector, 'source')
            source_elem.set('xmi:idref', source_id)
            
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
            
            # Target
            target_id = self.id_map.get(f"class_{relation.target}") or self.id_map.get(f"enum_{relation.target}")
            if not target_id:
                continue
                
            target_elem = ET.SubElement(connector, 'target')
            target_elem.set('xmi:idref', target_id)
            
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
            
            ET.SubElement(connector, 'properties', {
                'ea_type': self._map_relation_type_to_ea(relation.relation_type), 
                'direction': 'Source -> Destination'
            })
            
            ET.SubElement(connector, 'modifiers', {'isRoot': 'false', 'isLeaf': 'false'})
            ET.SubElement(connector, 'documentation')
            ET.SubElement(connector, 'appearance', {
                'linemode': '3', 'linecolor': '-1', 'linewidth': '0', 
                'seqno': '0', 'headStyle': '0', 'lineStyle': '0'
            })
            
            ET.SubElement(connector, 'labels', {'mb': f'«{relation.relation_type}»'})
            ET.SubElement(connector, 'extendedProperties', {'virtualInheritance': '0'})
            ET.SubElement(connector, 'style')
            ET.SubElement(connector, 'xrefs')
            ET.SubElement(connector, 'tags')
        
        # Dodaj diagramy
        self._dodaj_diagram(extension, classes.values(), relations, connector_ids_map)
        
        # Primitive types section
        primitivetypes = ET.SubElement(extension, 'primitivetypes')
        basic_types = ['int', 'String', 'double', 'boolean', 'float', 'long', 'char', 'byte']
        
        for type_name in basic_types:
            ptype = ET.SubElement(primitivetypes, 'primitivetype')
            ptype.set('xmi:id', self._generuj_ea_id("eaxmiid"))
            ptype.set('name', type_name)
        
        # Profiles section
        profiles = ET.SubElement(extension, 'profiles')
        uml_profile = ET.SubElement(profiles, 'umlprofile')
        uml_profile.set('profiletype', 'uml2')
    
    def _dodaj_diagram(self, extension: ET.Element, classes: List[UMLClass], 
                      relations: List[UMLRelation], connector_ids_map: Dict) -> None:
        """
        Dodaje diagram do rozszerzeń EA.
        Args:
            extension: Element rozszerzenia
            classes: Lista klas UML
            relations: Lista relacji UML
            connector_ids_map: Mapa ID konektorów
        """
        diagrams = ET.SubElement(extension, 'diagrams')
        
        diagram_id = self._generuj_ea_id()
        self.id_map['diagram'] = diagram_id
        
        diagram = ET.SubElement(diagrams, 'diagram')
        diagram.set('xmi:id', diagram_id)
        
        # <model> z przypisaniem pakietu
        ET.SubElement(diagram, 'model', {
            'package': self.id_map['package_element'],
            'localID': str(self.ea_localid_counter),
            'owner': self.id_map['package_element']
        })
        self.ea_localid_counter += 1
        
        # <properties>
        ET.SubElement(diagram, 'properties', {'name': 'Classes', 'type': 'Logical'})
        
        # <project> - metadane
        ET.SubElement(diagram, 'project', {
            'author': self.autor,
            'version': '1.0',
            'created': self._get_current_time(),
            'modified': self._get_current_time()
        })
        
        # <style1> i <style2>
        ET.SubElement(diagram, 'style1', {
            'value': (
                'ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;Border=1;HighlightForeign=1;'
                'PackageContents=1;SequenceNotes=0;ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=795;DocSize.cy=1134;'
                'ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;VisibleAttributeDetail=0;ShowOpRetType=1;'
                'ShowIcons=1;CollabNums=0;HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;'
                'HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;ShowMaint=0;ConnectorNotation=UML 2.1;'
                'ExplicitNavigability=0;ShowShape=1;AllDockable=0;AdvancedElementProps=1;AdvancedFeatureProps=1;'
                'AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;ShowNotes=0;SuppressBrackets=0;SuppConnectorLabels=0;'
                'PrintPageHeadFoot=0;ShowAsList=0;'
            )
        })
        
        ET.SubElement(diagram, 'style2', {
            'value': (
                'ExcludeRTF=0;DocAll=0;HideQuals=0;AttPkg=1;ShowTests=0;ShowMaint=0;SuppressFOC=1;MatrixActive=0;'
                'SwimlanesActive=1;KanbanActive=0;MatrixLineWidth=1;MatrixLineClr=0;MatrixLocked=0;'
                'TConnectorNotation=UML 2.1;TExplicitNavigability=0;AdvancedElementProps=1;AdvancedFeatureProps=1;'
                'AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;MDGDgm=;STBLDgm=;ShowNotes=0;'
                'VisibleAttributeDetail=0;ShowOpRetType=1;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;'
                'ShowAsList=0;SuppressedCompartments=;Theme=:119;SaveTag=4C19637D;'
            )
        })
        
        ET.SubElement(diagram, 'swimlanes', {
            'value': (
                'locked=false;orientation=0;width=0;inbar=false;names=false;color=-1;bold=false;fcol=0;tcol=-1;ofCol=-1;'
                'ufCol=-1;hl=1;ufh=0;hh=0;cls=0;bw=0;hli=0;bro=0;'
                'SwimlaneFont=lfh:-10,lfw:0,lfi:0,lfu:0,lfs:0,lfface:Calibri,lfe:0,lfo:0,lfchar:1,lfop:0,lfcp:0,lfq:0,'
                'lfpf=0,lfWidth=0;'
            )
        })
        
        ET.SubElement(diagram, 'matrixitems', {
            'value': 'locked=false;matrixactive=false;swimlanesactive=true;kanbanactive=false;width=1;clrLine=0;'
        })
        
        ET.SubElement(diagram, 'extendedProperties')
        
        # Elementy diagramu (pozycje klas)
        elements_node = ET.SubElement(diagram, 'elements')
        x, y = 100, 100
        
        # Dodaj elementy klas na diagramie
        for i, uml_class in enumerate(classes):
            class_id = self.id_map.get(f"class_{uml_class.name}")
            if not class_id:
                continue
                
            element = ET.SubElement(elements_node, 'element')
            element.set('geometry', f'Left={x};Top={y};Right={x+150};Bottom={y+120};')
            element.set('subject', class_id)
            element.set('seqno', str(i + 1))
            element.set('style', f'DUID={uuid.uuid4().hex[:8].upper()};NSL=0;BCol=-1;BFol=-1;LCol=-1;LWth=-1;'
                              f'fontsz=0;bold=0;black=0;italic=0;ul=0;charset=0;pitch=0;')
            
            # Przesunięcie pozycji dla następnego elementu
            x += 200
            if x > 700:
                x = 100
                y += 180
        
        # Dodaj konektory (połączenia) na diagramie
        for relation in relations:
            rel_key = (relation.source, relation.target, relation.label)
            conn_id = connector_ids_map.get(rel_key)
            if not conn_id:
                continue
                
            element = ET.SubElement(elements_node, 'element')
            element.set('geometry', 'SX=0;SY=0;EX=0;EY=0;EDGE=3;')
            element.set('subject', conn_id)
            element.set('style', f'Mode=3;EOID={uuid.uuid4().hex[:8].upper()};SOID={uuid.uuid4().hex[:8].upper()};Color=-1;LWidth=0;Hidden=0;')
    
    def _map_relation_type_to_ea(self, relation_type: str) -> str:
        """
        Mapuje typy relacji PlantUML na typy EA.
        Args:
            relation_type: Typ relacji w PlantUML
        Returns:
            Odpowiadający typ relacji w EA
        """
        mapping = {
            'inheritance': 'Generalization',
            'composition': 'Aggregation',
            'aggregation': 'Aggregation', 
            'association': 'Association',
            'dependency': 'Dependency',
            'realization': 'Realization',
            'usage': 'Usage'
        }
        return mapping.get(relation_type, 'Association')
    
    def _split_attribute(self, attr: str) -> Tuple[str, Optional[str]]:
        """
        Rozdziela nazwę i typ atrybutu.
        Args:
            attr: Deklaracja atrybutu
        Returns:
            (nazwa, typ) - tupla z nazwą i typem atrybutu
        """
        cleaned = re.sub(r'^[+\-#~]\s*', '', attr)
        parts = cleaned.split(':')
        name = parts[0].strip()
        attr_type = parts[1].strip() if len(parts) > 1 else None
        return name, attr_type
    
    def _clean_method_name(self, method: str) -> str:
        """
        Wyczyść nazwę metody.
        Args:
            method: Sygnatura metody
        Returns:
            Czysta nazwa metody
        """
        cleaned = re.sub(r'^[+\-#~]\s*', '', method)
        return cleaned.split('(')[0].strip()
    
    def _get_visibility(self, member: str) -> str:
        """
        Określ widoczność na podstawie prefiksu PlantUML.
        Args:
            member: Deklaracja składnika
        Returns:
            Nazwa widoczności (public, private, protected, package)
        """
        if member.startswith('+'):
            return 'public'
        elif member.startswith('-'):
            return 'private'
        elif member.startswith('#'):
            return 'protected'
        elif member.startswith('~'):
            return 'package'
        return 'public'  # domyślnie
    
    def _get_current_time(self) -> str:
        """Zwraca aktualny czas w formacie EA."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def generuj_xmi(self, classes: Dict[str, UMLClass], relations: List[UMLRelation], 
                   enums: Dict[str, UMLEnum], notes: List[UMLNote], nazwa_diagramu: str = "DiagramKlas") -> str:
        """
        Generuje plik XMI dla EA na podstawie modelu PlantUML.
        
        Args:
            classes: Słownik z klasami UML
            relations: Lista relacji UML
            enums: Słownik z enumeratorami UML
            notes: Lista notatek UML
            nazwa_diagramu: Nazwa diagramu
            
        Returns:
            Zawartość pliku XMI jako string
        """
        # 1. Utwórz podstawową strukturę dokumentu
        root = self._stworz_korzen_dokumentu()
        model = self._stworz_model_uml(root, nazwa_diagramu)
        package = self._stworz_pakiet_diagramu(model, "Classes")
        
        # 2. Dodaj klasy
        class_ids = {}
        for class_name, uml_class in classes.items():
            class_id = self._dodaj_klase(package, uml_class)
            class_ids[class_name] = class_id
            log_info(f"Dodano klasę: {class_name} z ID: {class_id}")
        
        # 3. Dodaj enumeratory
        enum_ids = {}
        for enum_name, uml_enum in enums.items():
            enum_id = self._dodaj_enum(package, uml_enum)
            enum_ids[enum_name] = enum_id
            log_info(f"Dodano enum: {enum_name} z ID: {enum_id}")
        
        # 4. Dodaj relacje
        connector_ids = self._dodaj_relacje(package, relations, class_ids, enum_ids)
        log_info(f"Dodano {len(connector_ids)} relacji")
        
        # 5. Dodaj rozszerzenia EA
        self._stworz_rozszerzenia_ea(root, classes, relations, connector_ids)
        
        # 6. Wygeneruj dokument XML
        rough_string = ET.tostring(root, encoding='utf-8')
        parsed = xml.dom.minidom.parseString(rough_string)
        pretty_xml = parsed.toprettyxml(indent="  ", encoding="utf-8")
        
        # Popraw header XML
        xml_string = pretty_xml.decode('utf-8')
        xml_string = xml_string.replace('<?xml version="1.0" encoding="utf-8"?>', 
                                  '<?xml version="1.0" encoding="UTF-8"?>')
        
        return xml_string

# Przykład użycia
if __name__ == '__main__':
    import sys
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'diagram_klas_PlantUML.puml'
        
    output_file = f'diagram_klas_{timestamp}.xmi'
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        # Parsuj kod PlantUML
        parser = PlantUMLParser()
        parser.parse(plantuml_code)
        
        # Pobierz dane
        classes = {}
        for name, data in parser.classes.items():
            classes[name] = data
        
        # Generuj XMI
        generator = XMIGenerator()
        xmi_content = generator.generuj_xmi(
            classes=parser.classes, 
            relations=parser.relations, 
            enums=parser.enums, 
            notes=parser.notes
        )
        
        # Zapisz do pliku
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xmi_content)
        
        print(f"Wygenerowano plik: {output_file}")
        
    except FileNotFoundError:
        print(f"Nie znaleziono pliku: {input_file}")
    except Exception as e:
        log_exception(f"Błąd podczas generowania XMI: {e}")
        print(f"Błąd: {e}")