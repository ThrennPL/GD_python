import xml.etree.ElementTree as ET
import uuid
from datetime import datetime
from plantuml_class_parser import PlantUMLParser
from plantuml_model import UMLClass, UMLRelation, UMLEnum, UMLNote

class XMLFormatter:
    """Klasa pomocnicza do formatowania XML podczas generowania."""
    
    def __init__(self):
        self.indent_level = 0
        self.indent_char = '  '  # Dwa spacje na poziom wcięcia
    
    def indent(self):
        """Zwiększa poziom wcięcia."""
        self.indent_level += 1
    
    def dedent(self):
        """Zmniejsza poziom wcięcia."""
        if self.indent_level > 0:
            self.indent_level -= 1
    
    def get_indent(self):
        """Zwraca aktualny string wcięcia."""
        return self.indent_char * self.indent_level

class XMLBuilder:
    """Klasa do budowania XML z właściwym formatowaniem."""
    
    def __init__(self):
        self.formatter = XMLFormatter()
        self.lines = []
    
    def add_line(self, line):
        """Dodaje linię z odpowiednim wcięciem."""
        self.lines.append(f"{self.formatter.get_indent()}{line}")
    
    def start_element(self, tag, attributes=None):
        """Rozpoczyna element XML."""
        attrs = ""
        if attributes:
            attrs = " " + " ".join([f'{k}="{v}"' for k, v in attributes.items()])
        
        self.add_line(f"<{tag}{attrs}>")
        self.formatter.indent()
    
    def end_element(self, tag):
        """Kończy element XML."""
        self.formatter.dedent()
        self.add_line(f"</{tag}>")
    
    def add_element(self, tag, attributes=None, text=None):
        """Dodaje kompletny element XML."""
        attrs = ""
        if attributes:
            attrs = " " + " ".join([f'{k}="{v}"' for k, v in attributes.items()])
        
        if text is not None:
            self.add_line(f"<{tag}{attrs}>{text}</{tag}>")
        else:
            self.add_line(f"<{tag}{attrs} />")
    
    def to_string(self):
        """Konwertuje do formatowanego stringa XML."""
        return '\n'.join(self.lines)

class XMIClassGenerator:
    def __init__(self, autor: str = "195841"):
        """
        Inicjalizuje generator XMI.
        
        Args:
            autor: Autor diagramu (domyślnie "195841")
        """
        self.autor = autor
        self.id_map = {}
        self.ns = {
            'uml': 'http://www.omg.org/spec/UML/20110701',
            'xmi': 'http://www.omg.org/spec/XMI/20110701'
        }
        self._zarejestruj_przestrzenie_nazw()
        self.ea_localid_counter = 1

    def _zarejestruj_przestrzenie_nazw(self):
        """Rejestruje przestrzenie nazw XML."""
        ET.register_namespace('xmi', self.ns['xmi'])
        ET.register_namespace('uml', self.ns['uml'])
    
    def _generuj_ea_id(self, prefix: str = "EAID") -> str:
        """Generuje unikalny identyfikator EA."""
        return f"{prefix}_{str(uuid.uuid4()).upper()}"
    
    def _stworz_korzen_dokumentu(self) -> ET.Element:
        """Tworzy główny element XMI."""
        # Tworzenie głównego elementu z prostszymi atrybutami
        root = ET.Element('XMI')
        root.set('version', '2.1')
        root.set('xmlns:uml', 'http://schema.omg.org/spec/UML/2.1')
        root.set('xmlns:xmi', 'http://schema.omg.org/spec/XMI/2.1')
        
        # Dodanie dokumentacji
        documentation = ET.SubElement(root, 'Documentation')
        documentation.set('exporter', 'Enterprise Architect')
        documentation.set('exporterVersion', '6.5')
    
        return root

    def _stworz_model_uml(self, root: ET.Element) -> ET.Element:
        """Tworzy główny model UML."""
        model = ET.SubElement(root, 'Model')
        model.set('type', 'uml:Model')
        model.set('name', 'EA_Model')
        model.set('visibility', 'public')
        return model

    def _stworz_pakiet_diagramu(self, model: ET.Element, nazwa_diagramu: str) -> ET.Element:
        """Tworzy pakiet dla diagramu klas."""
        self.id_map['package_element'] = self._generuj_ea_id("EAPK")
        package_element = ET.SubElement(model, 'packagedElement', {
            'xmi:type': 'uml:Package',
            'xmi:id': self.id_map['package_element'],
            'name': nazwa_diagramu,
            'visibility': 'public'
        })
        
        return package_element
    
    def dodaj_klase(self, package_element: ET.Element, klasa: UMLClass):
        """Dodaje klasę do pakietu."""
        class_id = self._generuj_ea_id("EAID")
        self.id_map[f"class_{klasa.name}"] = class_id
        
        class_element = ET.SubElement(package_element, 'packagedElement', {
            'xmi:type': 'uml:Class' if not klasa.stereotype == 'interface' else 'uml:Interface',
            'xmi:id': class_id,
            'name': klasa.name,
            'visibility': 'public',
            'isAbstract': 'true' if klasa.is_abstract else 'false'
        })
        
        # Dodaj atrybuty
        for attr in klasa.attributes:
            self.dodaj_atrybut(class_element, attr)
            
        # Dodaj metody
        for method in klasa.methods:
            self.dodaj_metode(class_element, method)
        
        return class_id

    def dodaj_atrybut(self, class_element: ET.Element, attr_data: dict):
        """Dodaje atrybut do klasy."""
        attr_id = self._generuj_ea_id("EAID")
        visibility = self._get_visibility(attr_data['declaration'])
        
        attr_element = ET.SubElement(class_element, 'ownedAttribute', {
            'xmi:type': 'uml:Property',
            'xmi:id': attr_id,
            'name': self._clean_attribute_name(attr_data['declaration']),
            'visibility': visibility
        })
        
        if 'static' in attr_data.get('modifiers', []):
            attr_element.set('isStatic', 'true')

    def dodaj_metode(self, class_element: ET.Element, method_data: dict):
        """Dodaje metodę do klasy."""
        method_id = self._generuj_ea_id("EAID")
        visibility = self._get_visibility(method_data['signature'])
        
        method_element = ET.SubElement(class_element, 'ownedOperation', {
            'xmi:type': 'uml:Operation',
            'xmi:id': method_id,
            'name': self._clean_method_name(method_data['signature']),
            'visibility': visibility
        })
        
        if 'static' in method_data.get('modifiers', []):
            method_element.set('isStatic', 'true')
        if 'abstract' in method_data.get('modifiers', []):
            method_element.set('isAbstract', 'true')

    def _format_xml(self, xml_string: str) -> str:
        """Formatuje XML dla lepszej czytelności."""
        try:
            import xml.dom.minidom
            dom = xml.dom.minidom.parseString(xml_string)
            # Usuwamy przestrzenie nazw z tagów, aby uniknąć duplikacji
            xml_pretty = dom.toprettyxml(indent='  ')
            
            # Usuń puste linie (które minidom czasem dodaje)
            lines = [line for line in xml_pretty.split('\n') if line.strip()]
            return '\n'.join(lines)
        except Exception as e:
            print(f"Uwaga: Nie udało się sformatować XML: {e}")
            return xml_string
    
    def generuj_diagram(self, nazwa_diagramu: str, dane: dict) -> str:
        """
        Generuje diagram w formacie XMI z odpowiednim formatowaniem.
        
        Args:
            nazwa_diagramu: Nazwa diagramu
            dane: Sparsowane dane z parsera PlantUML
        
        Returns:
            str: Sformatowany kod XMI
        """
        # Reset id_map dla każdego nowego diagramu
        self.id_map = {}
        
        # Inicjalizacja buildera XML
        builder = XMLBuilder()
        
        # Dodaj deklarację XML
        builder.add_line('<?xml version="1.0" encoding="windows-1252"?>')
        
        # Rozpocznij element XMI
        builder.start_element('xmi:XMI', {
            'version': '2.1',
            'xmlns:uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmlns:xmi': 'http://schema.omg.org/spec/XMI/2.1'
        })
        
        # Dodaj dokumentację
        builder.add_element('xmi:Documentation', {
            'exporter': 'Enterprise Architect',
            'exporterVersion': '6.5',
            'exporterID': '1560',
        })
        
        # Rozpocznij model
        builder.start_element('uml:Model', {
            'type': 'uml:Model',
            'name': 'EA_Model',
            'visibility': 'public'
        })
        
        # Utwórz pakiet
        self.id_map['package_element'] = self._generuj_ea_id("EAPK")
        builder.start_element('packagedElement', {
            'xmi:type': 'uml:Package',
            'xmi:id': self.id_map['package_element'],
            'name': nazwa_diagramu,
            'visibility': 'public'
        })
        
        # Debug info
        print("\n=== Przetwarzanie danych ===")
        if dane:
            print(f"Klasy: {len(dane.classes)}")
            print(f"Enumy: {len(dane.enums)}")
            print(f"Relacje: {len(dane.relations)}")
        
        # Dodaj klasy
        for class_name, class_obj in dane.classes.items():
            print(f"Przetwarzanie klasy: {class_name}")
            self._dodaj_klase_formatowana(builder, class_obj)
        
        # Dodaj enumy
        for enum_name, enum_obj in dane.enums.items():
            print(f"Przetwarzanie enuma: {enum_name}")
            self._dodaj_enum_formatowany(builder, enum_obj)
        
        # Dodaj relacje
        for relation in dane.relations:
            print(f"Przetwarzanie relacji: {relation.source} -> {relation.target}")
            self._dodaj_relacje_formatowane(builder, relation)
        
        # Zamknij pakiet
        builder.end_element('packagedElement')
        
        # Zamknij model
        builder.end_element('uml:Model')
        
        # Dodaj rozszerzenia EA
        self._dodaj_rozszerzenia_ea_formatowane(builder)
        
        # Zamknij XMI
        builder.end_element('xmi:XMI')
        
        # Zwróć sformatowany XML
        return builder.to_string()

    def _dodaj_klase_formatowana(self, builder: XMLBuilder, klasa: UMLClass):
        """Dodaje klasę z odpowiednim formatowaniem."""
        class_id = self._generuj_ea_id("EAID")
        self.id_map[f"class_{klasa.name}"] = class_id
        
        builder.start_element('packagedElement', {
            'xmi:type': 'uml:Class' if not klasa.stereotype == 'interface' else 'uml:Interface',
            'xmi:id': class_id,
            'name': klasa.name,
            'visibility': 'public',
            'isAbstract': 'true' if klasa.is_abstract else 'false'
        })
        
        # Dodaj atrybuty
        for attr in klasa.attributes:
            self._dodaj_atrybut_formatowany(builder, attr)
        
        # Dodaj metody
        for method in klasa.methods:
            self._dodaj_metode_formatowana(builder, method)
        
        builder.end_element('packagedElement')
        return class_id

    def _dodaj_atrybut_formatowany(self, builder: XMLBuilder, attr_data: dict):
        """Dodaje atrybut z odpowiednim formatowaniem."""
        attr_id = self._generuj_ea_id("EAID")
        visibility = self._get_visibility(attr_data['declaration'])
        
        attrs = {
            'xmi:type': 'uml:Property',
            'xmi:id': attr_id,
            'name': self._clean_attribute_name(attr_data['declaration']),
            'visibility': visibility
        }
        
        if 'static' in attr_data.get('modifiers', []):
            attrs['isStatic'] = 'true'
        
        builder.add_element('ownedAttribute', attrs)

    def _dodaj_enum_formatowany(self, builder: XMLBuilder, enum: UMLEnum):
        """Dodaje typ wyliczeniowy do pakietu w sformatowanym XML."""
        enum_id = self._generuj_ea_id("EAID")
        self.id_map[f"enum_{enum.name}"] = enum_id
        
        # Rozpocznij element enum
        builder.start_element('packagedElement', {
            'xmi:type': 'uml:Enumeration',
            'xmi:id': enum_id,
            'name': enum.name,
            'visibility': 'public'
        })
        
        # Dodaj wartości enuma
        for value in enum.values:
            literal_id = self._generuj_ea_id("EAID")
            builder.add_element('ownedLiteral', {
                'xmi:type': 'uml:EnumerationLiteral',
                'xmi:id': literal_id,
                'name': value,
                'visibility': 'public'
            })
        
        # Zakończ element enum
        builder.end_element('packagedElement')
        
        return enum_id
    
    def _dodaj_relacje_formatowane(self, builder: XMLBuilder, relation: UMLRelation):
        """Dodaje relację między klasami w sformatowanym XML."""
        relation_id = self._generuj_ea_id("EAID")
        
        # Mapowanie typów relacji na typy UML
        type_mapping = {
            'extends': ('uml:Generalization', 'generalization'),
            'implements': ('uml:Realization', 'interfaceRealization'),
            'aggregation': ('uml:Association', 'aggregation'),
            'composition': ('uml:Association', 'composition'),
            'association': ('uml:Association', 'none')
        }
        
        xmi_type, aggregation_type = type_mapping.get(relation.relation_type, ('uml:Association', 'none'))
        
        # Pobierz identyfikatory źródła i celu
        source_id = self.id_map.get(f"class_{relation.source}")
        target_id = self.id_map.get(f"class_{relation.target}")
        
        if not (source_id and target_id):
            return
        
        # Rozpocznij element relacji
        attrs = {
            'xmi:type': xmi_type,
            'xmi:id': relation_id,
            'visibility': 'public'
        }
        
        if relation.label:
            attrs['name'] = relation.label
            
        builder.start_element('packagedElement', attrs)
        
        if xmi_type == 'uml:Generalization':
            builder.add_element('generalization', {
                'general': target_id,
                'specific': source_id
            })
        else:
            # Dodaj końce asocjacji
            self._dodaj_koniec_asocjacji_formatowany(builder, source_id, 
                                    relation.source_multiplicity, 'source', aggregation_type)
            self._dodaj_koniec_asocjacji_formatowany(builder, target_id, 
                                    relation.target_multiplicity, 'target', 'none')
        
        # Zamknij element relacji
        builder.end_element('packagedElement')
        
        return relation_id

    def _dodaj_koniec_asocjacji_formatowany(self, builder: XMLBuilder, class_id: str, 
                            multiplicity: str, end_type: str, aggregation_type: str):
        """Dodaje końcówkę asocjacji w sformatowanym XML."""
        end_id = self._generuj_ea_id("EAID")
        
        attrs = {
            'xmi:type': 'uml:Property',
            'xmi:id': end_id,
            'visibility': 'public',
            'type': class_id
        }
        
        if aggregation_type != 'none':
            attrs['aggregation'] = aggregation_type
            
        builder.start_element('ownedEnd', attrs)
        
        if multiplicity:
            lower, upper = self._parse_multiplicity(multiplicity)
            if lower is not None:
                builder.add_element('lowerValue', {
                    'xmi:type': 'uml:LiteralInteger',
                    'value': str(lower)
                })
            if upper is not None:
                builder.add_element('upperValue', {
                    'xmi:type': 'uml:LiteralUnlimitedNatural',
                    'value': str(upper)
                })
        
        builder.end_element('ownedEnd')

    def _dodaj_rozszerzenia_ea_formatowane(self, builder: XMLBuilder):
        """Tworzy rozszerzenia specyficzne dla Enterprise Architect w sformatowanym XML."""
        builder.start_element('xmi:Extension', {
            'extender': 'Enterprise Architect',
            'extenderID': '6.5'
        })
        
        # Sekcja elements
        builder.start_element('elements')
        for key, element_id in self.id_map.items():
            if key.startswith(('class_', 'enum_')):
                name = key.split('_')[1]
                builder.start_element('element', {
                    'xmi:idref': element_id,
                    'xmi:type': 'uml:Class',
                    'name': name,
                    'scope': 'public'
                })
                
                builder.add_element('model', {
                    'package': self.id_map['package_element'],
                    'tpos': '0',
                    'ea_localid': str(self.ea_localid_counter),
                    'ea_eleType': 'element'
                })
                self.ea_localid_counter += 1
                
                builder.add_element('properties', {
                    'documentation': '',
                    'isSpecification': 'false',
                    'sType': 'Class',
                    'nType': '0',
                    'scope': 'public',
                    'isRoot': 'false',
                    'isLeaf': 'false',
                    'isAbstract': 'false',
                    'isActive': 'false'
                })
                
                builder.end_element('element')
        builder.end_element('elements')
        
        # Sekcja connectors - rozbudowana według wzoru
        builder.start_element('connectors')
        
        # Przetwarzamy relacje
        for key, relation_id in self.id_map.items():
            if key.startswith('rel_'):
                # Wyodrębnianie źródła i celu z klucza
                parts = key.split('_')
                if len(parts) >= 3:
                    source = parts[1]
                    target = parts[2]
                    
                    source_id = self.id_map.get(f"class_{source}")
                    target_id = self.id_map.get(f"class_{target}")
                    
                    if source_id and target_id:
                        builder.start_element('connector', {
                            'xmi:idref': relation_id
                        })
                        
                        # Source
                        builder.start_element('source', {
                            'xmi:idref': source_id
                        })
                        builder.add_element('model', {
                            'ea_localid': str(self.ea_localid_counter),
                            'type': 'Class',
                            'name': source
                        })
                        self.ea_localid_counter += 1
                        builder.add_element('role', {
                            'visibility': 'Public',
                            'targetScope': 'instance'
                        })
                        builder.add_element('type', {
                            'aggregation': 'none',
                            'containment': 'Unspecified'
                        })
                        builder.add_element('constraints')
                        builder.add_element('modifiers', {
                            'isOrdered': 'false',
                            'changeable': 'none',
                            'isNavigable': 'false'
                        })
                        builder.add_element('style', {
                            'value': 'Union=0;Derived=0;AllowDuplicates=0;Owned=0;Navigable=Non-Navigable;'
                        })
                        builder.add_element('documentation')
                        builder.add_element('xrefs')
                        builder.add_element('tags')
                        builder.end_element('source')
                        
                        # Target
                        builder.start_element('target', {
                            'xmi:idref': target_id
                        })
                        builder.add_element('model', {
                            'ea_localid': str(self.ea_localid_counter),
                            'type': 'Class',
                            'name': target
                        })
                        self.ea_localid_counter += 1
                        builder.add_element('role', {
                            'visibility': 'Public',
                            'targetScope': 'instance'
                        })
                        builder.add_element('type', {
                            'aggregation': 'none',
                            'containment': 'Unspecified'
                        })
                        builder.add_element('constraints')
                        builder.add_element('modifiers', {
                            'isOrdered': 'false',
                            'changeable': 'none',
                            'isNavigable': 'true'
                        })
                        builder.add_element('style', {
                            'value': 'Union=0;Derived=0;AllowDuplicates=0;Owned=0;Navigable=Navigable;'
                        })
                        builder.add_element('documentation')
                        builder.add_element('xrefs')
                        builder.add_element('tags')
                        builder.end_element('target')
                        
                        # Model, properties i inne
                        builder.add_element('model', {
                            'ea_localid': str(self.ea_localid_counter)
                        })
                        self.ea_localid_counter += 1
                        builder.add_element('properties', {
                            'ea_type': 'Association',
                            'direction': 'Source -> Destination'
                        })
                        builder.add_element('modifiers', {
                            'isRoot': 'false',
                            'isLeaf': 'false'
                        })
                        builder.add_element('documentation')
                        builder.add_element('appearance', {
                            'linemode': '3',
                            'linecolor': '-1',
                            'linewidth': '0',
                            'seqno': '0',
                            'headStyle': '0',
                            'lineStyle': '0'
                        })
                        builder.add_element('labels', {
                            'mb': '«association»'
                        })
                        builder.add_element('extendedProperties', {
                            'virtualInheritance': '0'
                        })
                        builder.add_element('style')
                        builder.add_element('xrefs')
                        builder.add_element('tags')
                        
                        builder.end_element('connector')
        
        builder.end_element('connectors')
        
        # Sekcja primitivetypes
        builder.start_element('primitivetypes')
        builder.add_element('packagedElement', {
            'xmi:type': 'uml:Package',
            'xmi:id': 'EAPrimitiveTypesPackage',
            'name': 'EA_PrimitiveTypes_Package',
            'visibility': 'public'
        })
        builder.end_element('primitivetypes')
        
        # Sekcja profiles
        builder.add_element('profiles')
        
        # Dodanie sekcji diagrams
        builder.start_element('diagrams')
        diagram_id = self._generuj_ea_id("EAID")
        builder.start_element('diagram', {
            'xmi:id': diagram_id
        })
        builder.add_element('model', {
            'package': self.id_map['package_element'],
            'localID': '1140',
            'owner': self.id_map['package_element']
        })
        builder.add_element('properties', {
            'name': 'Diagram_klas',
            'type': 'Logical'
        })
        builder.end_element('diagram')
        builder.end_element('diagrams')
        
        builder.end_element('xmi:Extension')

    def _dodaj_relacje_formatowane(self, builder: XMLBuilder, relation: UMLRelation):
        """Dodaje relację między klasami w sformatowanym XML."""
        relation_id = self._generuj_ea_id("EAID")
        
        # Zapisz ID relacji z informacją o źródle i celu
        rel_key = f"rel_{relation.source}_{relation.target}"
        self.id_map[rel_key] = relation_id
        
        # Mapowanie typów relacji na typy UML
        # ...reszta kodu pozostaje bez zmian...

    def _dodaj_metode_formatowana(self, builder: XMLBuilder, method_data: dict):
        """Dodaje metodę z odpowiednim formatowaniem."""
        method_id = self._generuj_ea_id("EAID")
        visibility = self._get_visibility(method_data['signature'])
        
        attrs = {
            'xmi:type': 'uml:Operation',
            'xmi:id': method_id,
            'name': self._clean_method_name(method_data['signature']),
            'visibility': visibility
        }
        
        if 'static' in method_data.get('modifiers', []):
            attrs['isStatic'] = 'true'
        if 'abstract' in method_data.get('modifiers', []):
            attrs['isAbstract'] = 'true'
        
        builder.add_element('ownedOperation', attrs)

        
    def _get_visibility(self, declaration: str) -> str:
        """Określa widoczność elementu na podstawie deklaracji."""
        if declaration.startswith('+'):
            return 'public'
        elif declaration.startswith('-'):
            return 'private'
        elif declaration.startswith('#'):
            return 'protected'
        elif declaration.startswith('~'):
            return 'package'
        return 'public'

    def _clean_attribute_name(self, declaration: str) -> str:
        """Czyści nazwę atrybutu z modyfikatorów i typu."""
        # Usuń widoczność i spacje
        name = declaration.lstrip('+-#~ ')
        # Weź tylko część przed typem (jeśli jest)
        return name.split(':')[0].strip()

    def _clean_method_name(self, signature: str) -> str:
        """Czyści nazwę metody z modyfikatorów i parametrów."""
        # Usuń widoczność i spacje
        name = signature.lstrip('+-#~ ')
        # Weź tylko część przed nawiasami
        return name.split('(')[0].strip()

    def dodaj_enum(self, package_element: ET.Element, enum: UMLEnum):
        """Dodaje typ wyliczeniowy do pakietu."""
        enum_id = self._generuj_ea_id("EAID")
        self.id_map[f"enum_{enum.name}"] = enum_id
        
        enum_element = ET.SubElement(package_element, 'packagedElement', {
            'xmi:type': 'uml:Enumeration',
            'xmi:id': enum_id,
            'name': enum.name,
            'visibility': 'public'
        })
        
        # Dodaj wartości enuma
        for value in enum.values:
            literal_id = self._generuj_ea_id("EAID")
            ET.SubElement(enum_element, 'ownedLiteral', {
                'xmi:type': 'uml:EnumerationLiteral',
                'xmi:id': literal_id,
                'name': value,
                'visibility': 'public'
            })
        
        return enum_id

    def dodaj_relacje(self, package_element: ET.Element, relation: UMLRelation):
        """Dodaje relację między klasami."""
        relation_id = self._generuj_ea_id("EAID")
        
        # Mapowanie typów relacji na typy UML
        type_mapping = {
            'extends': ('uml:Generalization', 'generalization'),
            'implements': ('uml:Realization', 'interfaceRealization'),
            'aggregation': ('uml:Association', 'aggregation'),
            'composition': ('uml:Association', 'composition'),
            'association': ('uml:Association', 'none')
        }
        
        xmi_type, aggregation_type = type_mapping.get(relation.relation_type, ('uml:Association', 'none'))
        
        # Pobierz identyfikatory źródła i celu
        source_id = self.id_map.get(f"class_{relation.source}")
        target_id = self.id_map.get(f"class_{relation.target}")
        
        if not (source_id and target_id):
            return
        
        relation_element = ET.SubElement(package_element, 'packagedElement', {
            'xmi:type': xmi_type,
            'xmi:id': relation_id,
            'visibility': 'public'
        })
        
        if xmi_type == 'uml:Generalization':
            relation_element.set('general', target_id)
            relation_element.set('specific', source_id)
        else:
            # Dodaj końce asocjacji
            self._dodaj_koniec_asocjacji(relation_element, source_id, 
                                    relation.source_multiplicity, 'source', aggregation_type)
            self._dodaj_koniec_asocjacji(relation_element, target_id, 
                                    relation.target_multiplicity, 'target', 'none')
        
        if relation.label:
            relation_element.set('name', relation.label)
        
        return relation_id

    def _dodaj_koniec_asocjacji(self, relation_element: ET.Element, class_id: str, 
                            multiplicity: str, end_type: str, aggregation_type: str):
        """Dodaje końcówkę asocjacji."""
        end_id = self._generuj_ea_id("EAID")
        
        end = ET.SubElement(relation_element, 'ownedEnd', {
            'xmi:type': 'uml:Property',
            'xmi:id': end_id,
            'visibility': 'public',
            'type': class_id
        })
        
        if multiplicity:
            lower, upper = self._parse_multiplicity(multiplicity)
            if lower is not None:
                ET.SubElement(end, 'lowerValue', {
                    'xmi:type': 'uml:LiteralInteger',
                    'value': str(lower)
                })
            if upper is not None:
                ET.SubElement(end, 'upperValue', {
                    'xmi:type': 'uml:LiteralUnlimitedNatural',
                    'value': str(upper)
                })
        
        if aggregation_type != 'none':
            end.set('aggregation', aggregation_type)

    def _parse_multiplicity(self, multiplicity: str) -> tuple:
        """Parsuje zapis mnogości relacji."""
        if not multiplicity:
            return None, None
        
        if multiplicity == '*':
            return 0, -1
        
        if '..' in multiplicity:
            lower, upper = multiplicity.split('..')
            return int(lower), -1 if upper == '*' else int(upper)
        
        try:
            value = int(multiplicity)
            return value, value
        except ValueError:
            return None, None
        
    def _stworz_rozszerzenia_ea(self, root: ET.Element, nazwa_diagramu: str) -> None:
        """Tworzy rozszerzenia specyficzne dla Enterprise Architect."""
        teraz = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        extension = ET.SubElement(root, ET.QName(self.ns['xmi'], 'Extension'), {
            'extender': 'Enterprise Architect',
            'extenderID': '6.5'
        })
        
        self._stworz_sekcje_elements(extension, nazwa_diagramu, teraz)
        self._stworz_sekcje_connectors(extension)
        self._stworz_primitivetypes(extension)
        ET.SubElement(extension, 'profiles')

    def _stworz_sekcje_elements(self, extension: ET.Element, nazwa_diagramu: str, teraz: str) -> None:
        """Tworzy sekcję elements w rozszerzeniach EA."""
        elements = ET.SubElement(extension, 'elements')
        
        # Dodaj element dla każdej klasy i enuma
        for key, element_id in self.id_map.items():
            if key.startswith(('class_', 'enum_')):
                element = ET.SubElement(elements, 'element', {
                    'xmi:idref': element_id,
                    'xmi:type': 'uml:Class',
                    'name': key.split('_')[1],
                    'scope': 'public'
                })
                
                ET.SubElement(element, 'model', {
                    'package': self.id_map['package_element'],
                    'tpos': '0',
                    'ea_localid': str(self.ea_localid_counter),
                    'ea_eleType': 'element'
                })
                self.ea_localid_counter += 1
                
                ET.SubElement(element, 'properties', {
                    'documentation': '',
                    'isSpecification': 'false',
                    'sType': 'Class',
                    'nType': '0',
                    'scope': 'public',
                    'isRoot': 'false',
                    'isLeaf': 'false',
                    'isAbstract': 'false',
                    'isActive': 'false'
                })

    def _stworz_sekcje_connectors(self, extension: ET.Element) -> None:
        """Tworzy sekcję connectors w rozszerzeniach EA."""
        connectors = ET.SubElement(extension, 'connectors')
        
        for relation in self.id_map.keys():
            if not relation.startswith('rel_'):
                continue
                
            relation_id = self.id_map[relation]
            connector = ET.SubElement(connectors, 'connector', {
                'xmi:idref': relation_id
            })
            
            # Dodaj source i target
            source = ET.SubElement(connector, 'source', {
                'xmi:idref': self.id_map.get(f"class_{relation['source']}")
            })
            ET.SubElement(source, 'model', {
                'ea_localid': str(self.ea_localid_counter)
            })
            self.ea_localid_counter += 1
            
            target = ET.SubElement(connector, 'target', {
                'xmi:idref': self.id_map.get(f"class_{relation['target']}")
            })
            ET.SubElement(target, 'model', {
                'ea_localid': str(self.ea_localid_counter)
            })
            self.ea_localid_counter += 1
            
            # Dodaj properties
            properties = {
                'ea_type': 'Association',
                'direction': 'Source -> Destination',
                'sourcecard': relation.get('source_multiplicity', ''),
                'targetcard': relation.get('target_multiplicity', ''),
                'sourcestyle': 'Union=0;Derived=0;AllowDuplicates=0;',
                'targetStyle': 'Union=0;Derived=0;AllowDuplicates=0;',
            }
            
            ET.SubElement(connector, 'properties', properties)
            ET.SubElement(connector, 'documentation')
            ET.SubElement(connector, 'labels', {
                'mt': relation.get('label', '')
            })

    def _stworz_primitivetypes(self, extension: ET.Element) -> None:
        """Tworzy sekcję primitivetypes."""
        primitivetypes = ET.SubElement(extension, 'primitivetypes')
        ET.SubElement(primitivetypes, 'packagedElement', {
            'xmi:type': 'uml:Package',
            'xmi:id': 'EAPrimitiveTypesPackage',
            'name': 'EA_PrimitiveTypes_Package',
            'visibility': 'public'
        })

if __name__ == '__main__':
    try:
        # Wczytaj i sparsuj plik PlantUML
        input_file = 'diagram_klas_PlantUML.puml'
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        # Parsowanie
        parser = PlantUMLParser()
        parser.parse(plantuml_code)
        parsed_data = parser  # Parser sam w sobie zawiera sparsowane dane
        
        # Debug info
        print("\n=== Sparsowane dane ===")
        print(f"Liczba klas: {len(parser.classes)}")
        print(f"Liczba enumów: {len(parser.enums)}")
        print(f"Liczba relacji: {len(parser.relations)}")
        
        # Generowanie XMI
        generator = XMIClassGenerator(autor="195841")
        xmi_code = generator.generuj_diagram(
            nazwa_diagramu="Diagram klas - System Bankowy",
            dane=parsed_data
        )
        
        # Zapis do pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"diagram_klas_{timestamp}.xmi"
        
        # Dodaj deklarację XML tylko jeśli nie ma jej w sformatowanym kodzie
        with open(output_file, "w", encoding="utf-8") as f:
            if not xmi_code.startswith('<?xml'):
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(xmi_code)
        
        print(f"\nWygenerowano plik XMI: {output_file}")
        
    except Exception as e:
        print(f"Błąd: {e}")
        import traceback
        traceback.print_exc()
