import re
import xml.etree.ElementTree as ET
import xml.dom.minidom
import uuid
from datetime import datetime
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
        self.ns = {
            'xmi': 'http://www.omg.org/XMI',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'uml': 'http://www.eclipse.org/uml2/5.0.0/UML',
            'eaProfile': 'http://www.sparxsystems.com/profiles/eaProfile/1.0'
        }
    
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
        Tworzy główny element XMI z deklaracjami przestrzeni nazw.
        """
        self._zarejestruj_przestrzenie_nazw()
        xmi_root = ET.Element(
            'xmi:XMI',
            {
                'xmi:version': '2.1',
                'xmlns:xmi': 'http://www.omg.org/XMI',
                'xmlns:uml': 'http://www.eclipse.org/uml2/5.0.0/UML',
                'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xmlns:eaProfile': 'http://www.sparxsystems.com/profiles/eaProfile/1.0'
            }
        )
        doc = ET.SubElement(xmi_root, 'xmi:Documentation')
        doc.set('exporter', 'Enterprise Architect')
        doc.set('exporterVersion', '15.2')
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
        
        # Dodaj referencję diagramu do pakietu - NOWA SEKCJA
        diagram_id = self._generuj_ea_id("EADIAG")
        self.id_map['diagram'] = diagram_id
        
        # Dodaj element diagramu bezpośrednio do pakietu
        diagram_ref = ET.SubElement(package_element, 'packagedElement')
        diagram_ref.set('xmi:type', 'uml:Diagram')
        diagram_ref.set('xmi:id', diagram_id)
        diagram_ref.set('name', 'Class Diagram')
        
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
    
    def _dodaj_dziedziczenie(self, package: ET.Element, relation: UMLRelation, 
                        source_id: str, target_id: str) -> str:
        """
        Dodaje relację dziedziczenia.
        Args:
            package: Element pakietu
            relation: Relacja UML (dziedziczenie)
            source_id: ID klasy dziedziczącej (podklasa)
            target_id: ID klasy bazowej (nadklasa)
        Returns:
            ID utworzonej relacji dziedziczenia
        """
        generalization_id = self._generuj_ea_id()
        
        # Znajdź element klasy źródłowej (podklasy)
        source_elem = None
        for elem in package.findall('.//packagedElement'):
            if elem.get('xmi:id') == source_id:
                source_elem = elem
                break
        
        if source_elem is not None:
            # Dodaj element generalization bezpośrednio do podklasy
            gen_elem = ET.SubElement(source_elem, 'generalization')
            gen_elem.set('xmi:id', generalization_id)
            gen_elem.set('xmi:type', 'uml:Generalization')
            gen_elem.set('general', target_id)
        
        return generalization_id
    
    def _dodaj_asocjacje(self, package: ET.Element, relation: UMLRelation, 
                        source_id: str, target_id: str) -> str:
        """
        Dodaje relację asocjacji, agregacji, kompozycji lub zależności.
        Args:
            package: Element pakietu
            relation: Relacja UML
            source_id: ID klasy źródłowej
            target_id: ID klasy docelowej
        Returns:
            ID utworzonej relacji
        """
        association_id = self._generuj_ea_id()
        
        # Określ typ relacji w standardzie UML
        if relation.relation_type == 'composition':
            aggregation_type = 'composite'
        elif relation.relation_type == 'aggregation':
            aggregation_type = 'shared'
        else:
            aggregation_type = 'none'
        
        # Utwórz relację
        assoc_elem = ET.SubElement(package, 'packagedElement')
        assoc_elem.set('xmi:type', 'uml:Association')
        assoc_elem.set('xmi:id', association_id)
        if relation.label:
            assoc_elem.set('name', relation.label)
        
        # Generuj ID dla końców asocjacji
        source_end_id = self._generuj_ea_id()
        target_end_id = self._generuj_ea_id()
        
        # Dodaj memberEnds (referencje)
        assoc_elem.set('memberEnd', f"{source_end_id} {target_end_id}")
        
        # Multiplicity
        src_lower, src_upper = PlantUMLParser.parse_multiplicity(relation.source_multiplicity)
        tgt_lower, tgt_upper = PlantUMLParser.parse_multiplicity(relation.target_multiplicity)
        
        # Source end
        owned_end_source = ET.SubElement(assoc_elem, 'ownedEnd')
        owned_end_source.set('xmi:id', source_end_id)
        owned_end_source.set('visibility', 'public')
        owned_end_source.set('type', source_id)
        owned_end_source.set('association', association_id)
        
        ET.SubElement(owned_end_source, 'lowerValue', {
            'xmi:type': 'uml:LiteralInteger', 
            'xmi:id': self._generuj_ea_id(), 
            'value': src_lower
        })
        
        ET.SubElement(owned_end_source, 'upperValue', {
            'xmi:type': 'uml:LiteralUnlimitedNatural', 
            'xmi:id': self._generuj_ea_id(), 
            'value': src_upper
        })
        
        # Target end
        owned_end_target = ET.SubElement(assoc_elem, 'ownedEnd')
        owned_end_target.set('xmi:id', target_end_id)
        owned_end_target.set('visibility', 'public')
        owned_end_target.set('type', target_id)
        owned_end_target.set('association', association_id)
        
        # Ustaw aggregation na końcu docelowym dla kompozycji i agregacji
        if aggregation_type != 'none':
            owned_end_target.set('aggregation', aggregation_type)
        
        ET.SubElement(owned_end_target, 'lowerValue', {
            'xmi:type': 'uml:LiteralInteger', 
            'xmi:id': self._generuj_ea_id(), 
            'value': tgt_lower
        })
        
        ET.SubElement(owned_end_target, 'upperValue', {
            'xmi:type': 'uml:LiteralUnlimitedNatural', 
            'xmi:id': self._generuj_ea_id(), 
            'value': tgt_upper
        })
        
        return association_id
    
    def _dodaj_relacje(self, package: ET.Element, relations: List[UMLRelation], 
                 class_ids: Dict[str, str], enum_ids: Dict[str, str]) -> Dict[Tuple, str]:
        """
        Dodaje relacje do pakietu.
        Args:
            package: Element pakietu
            relations: Lista relacji UML
            class_ids: Słownik mapujący nazwy klas na ich ID
            enum_ids: Słownik mapujący nazwy enumeratorów na ich ID
        Returns:
            Słownik mapujący klucze relacji na ich ID
        """
        connector_ids_map = {}
        
        for relation in relations:
            print(f"DEBUG: Przetwarzam relację: {relation.source} -> {relation.target} typu {relation.relation_type}, label: {relation.label}")
            
            # Pobierz ID źródła i celu
            source_id = self.id_map.get(f"class_{relation.source}") or self.id_map.get(f"enum_{relation.source}")
            target_id = self.id_map.get(f"class_{relation.target}") or self.id_map.get(f"enum_{relation.target}")
            
            if not source_id or not target_id:
                print(f"WARN: Nie znaleziono ID dla {relation.source} lub {relation.target}, pomijam relację")
                continue
            
            # Relacja dziedziczenia wymaga specjalnej obsługi
            if relation.relation_type == 'inheritance':
                generalization_id = self._dodaj_dziedziczenie(package, relation, source_id, target_id)
                connector_ids_map[(relation.source, relation.target, relation.label)] = generalization_id
                print(f"SUCCESS: Dodano dziedziczenie: {relation.source} -> {relation.target}, ID: {generalization_id}")
            else:
                # Dodaj standardową relację (asocjacja, agregacja, kompozycja, zależność)
                association_id = self._dodaj_asocjacje(package, relation, source_id, target_id)
                connector_ids_map[(relation.source, relation.target, relation.label)] = association_id
        
        return connector_ids_map
    
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
        # Używamy już wygenerowanego ID diagramu
        diagram_id = self.id_map['diagram']
        
        # Teraz dodaj diagram w sekcji rozszerzeń EA
        diagrams = ET.SubElement(extension, 'diagrams')
        
        diagram = ET.SubElement(diagrams, 'diagram')
        diagram.set('xmi:id', diagram_id)
        diagram.set('name', 'Class Diagram')
        diagram.set('diagramType', 'ClassDiagram')
        
        # <model> z przypisaniem pakietu
        ET.SubElement(diagram, 'model', {
            'package': self.id_map['package_element'],
            'localID': str(self.ea_localid_counter),
            'owner': self.id_map['package_element'],
            'type': 'Logical' 
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
        
        # Dodaj styl diagramu
        ET.SubElement(diagram, 'diagramstyle', {
            'version': '1.0',
            'description': 'Diagram wygenerowany automatycznie',
            'properties': 'wireframe=false;'
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
        
        # Dodajemy obiekty diagramu - kluczowa część dla EA
        diagobjects = ET.SubElement(diagram, 'diagobjects')
        x, y = 100, 100
        
        # Dodaj każdą klasę jako obiekt diagramu
        for i, uml_class in enumerate(classes):
            class_name = uml_class.name
            class_id = self.id_map.get(f"class_{class_name}")
            if not class_id:
                continue
                
            # Unikalny identyfikator obiektu na diagramie
            diag_obj_id = f"DCOBJ_{uuid.uuid4().hex[:8].upper()}"
            
            # Dodaj obiekt diagramu
            diagobj = ET.SubElement(diagobjects, 'diagobj')
            diagobj.set('objectID', class_id)  # ID klasy z głównej części XMI
            diagobj.set('rectID', diag_obj_id)  # Unikalny ID dla pozycjonowania
            
            # Dodaj pozycję i wymiary
            ET.SubElement(diagobj, 'bounds', {
                'x': str(x),
                'y': str(y),
                'width': '150',
                'height': '100'
            })
            
            # Przesuń dla następnego elementu
            x += 200
            if x > 700:
                x = 100
                y += 180
        
        # Dodaj sekcję diagramlinks dla połączeń
        diagramlinks = ET.SubElement(diagram, 'diagramlinks')
        
        # Dodaj każdą relację jako link diagramu
        for relation in relations:
            rel_key = (relation.source, relation.target, relation.label)
            conn_id = connector_ids_map.get(rel_key)
            if not conn_id:
                continue
                
            diag_link_id = f"DCLINK_{uuid.uuid4().hex[:8].upper()}"
            
            # Dodaj link diagramu
            diaglink = ET.SubElement(diagramlinks, 'diagramlink')
            diaglink.set('connectorID', conn_id)  # ID konektora z głównej części XMI
            diaglink.set('linkID', diag_link_id)  # Unikalny ID dla linii
        
        # Dodaj elementy diagramu (pozycje klas)
        elements_node = ET.SubElement(diagram, 'elements')
        x, y = 100, 100
        
        # Dodaj elementy klas na diagramie
        for i, uml_class in enumerate(classes):
            class_id = self.id_map.get(f"class_{uml_class.name}")
            if not class_id:
                continue
                
            duid = uuid.uuid4().hex[:8].upper()
            
            element = ET.SubElement(elements_node, 'element')
            element.set('geometry', f'Left={x};Top={y};Right={x+150};Bottom={y+120};')
            element.set('subject', class_id)
            element.set('seqno', str(i + 1))
            element.set('style', f'DUID={duid};NSL=0;BCol=-1;BFol=-1;LCol=-1;LWth=-1;'
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
                
            eoid = uuid.uuid4().hex[:8].upper()
            soid = uuid.uuid4().hex[:8].upper()
            
            element = ET.SubElement(elements_node, 'element')
            element.set('geometry', 'SX=0;SY=0;EX=0;EY=0;EDGE=3;')
            element.set('subject', conn_id)
            element.set('style', f'Mode=3;EOID={eoid};SOID={soid};Color=-1;LWidth=0;Hidden=0;')

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
    
    def _analizuj_wynikowe_xmi(self, xmi_content: str):
        """Analizuje wygenerowany XMI pod kątem liczby elementów"""
        root = ET.fromstring(xmi_content)
        
        # Liczniki
        classes = len(root.findall('.//packagedElement[@xmi:type="uml:Class"]', self.ns))
        interfaces = len(root.findall('.//packagedElement[@xmi:type="uml:Interface"]', self.ns))
        generalizations = len(root.findall('.//generalization', self.ns))
        associations = len(root.findall('.//packagedElement[@xmi:type="uml:Association"]', self.ns))
        dependencies = len(root.findall('.//packagedElement[@xmi:type="uml:Dependency"]', self.ns))
        
        print(f"\nANALIZA WYGENEROWANEGO XMI:")
        print(f"- Klasy: {classes}")
        print(f"- Interfejsy: {interfaces}")
        print(f"- Generalizacje (dziedziczenie): {generalizations}")
        print(f"- Asocjacje: {associations}")
        print(f"- Zależności: {dependencies}")
    
    def _debug_xml(self, element: ET.Element, prefix: str = ""):
        """Debuguje strukturę XML, wypisując wszystkie tagi i atrybuty"""
        print(f"{prefix}<{element.tag} {' '.join([f'{k}=\"{v}\"' for k, v in element.attrib.items()])}>")
        for child in element:
            self._debug_xml(child, prefix + "  ")
        print(f"{prefix}</{element.tag}>")
            

    def _format_xml(self, xml_string: str) -> str:
        """
        Formatuje dokument XML dodając wcięcia i nowe linie.
        """
        try:
            import xml.dom.minidom as minidom
            dom = minidom.parseString(xml_string)
            pretty_xml = dom.toprettyxml(indent="  ", encoding="UTF-8")
            # Usuwa puste linie
            lines = [line for line in pretty_xml.decode('utf-8').split('\n') if line.strip()]
            return '\n'.join(lines)
        except Exception as e:
            print(f"Nie udało się sformatować XML: {e}")
            return xml_string
        
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
        # Najpierw rejestrujemy przestrzenie nazw
        ET.register_namespace('xmi', 'http://www.omg.org/XMI')
        ET.register_namespace('uml', 'http://www.eclipse.org/uml2/5.0.0/UML')
        ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        ET.register_namespace('eaProfile', 'http://www.sparxsystems.com/profiles/eaProfile/1.0')
        
        # Reszta kodu pozostaje bez zmian...
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
        
        '''try:
            # 6. Wygeneruj dokument XML
            rough_string = ET.tostring(root, encoding='utf-8')
            parsed = xml.dom.minidom.parseString(rough_string)
            pretty_xml = parsed.toprettyxml(indent="  ", encoding="utf-8")
            
            # Popraw header XML
            xml_string = pretty_xml.decode('utf-8')
            xml_string = xml_string.replace('<?xml version="1.0" encoding="utf-8"?>', 
                                      '<?xml version="1.0" encoding="UTF-8"?>')
            
            self._analizuj_wynikowe_xmi(xml_string)
            return xml_string
            
        except Exception as e:
            print(f"Błąd podczas generowania XML: {e}")
            
            # Spróbuj dokładniej zdiagnozować problem
            print("\nDiagnostyka problemu:")
            try:
                print(f"Root tag: {root.tag}")
                print("Pierwsze poziomy drzewa XML:")
                for child in root:
                    print(f"  - {child.tag} (atrybuty: {child.attrib})")
                    for grandchild in child:
                        print(f"    - {grandchild.tag}")
            except Exception as inner_e:
                print(f"Błąd podczas diagnostyki: {inner_e}")
            
            raise e'''
        
        try:
            # Generowanie XML bez formatowania
            xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            xml_string = xml_bytes.decode('utf-8')

            # Dodaj ładne formatowanie
            formatted_xml = self._format_xml(xml_string)
            self._analizuj_wynikowe_xmi(formatted_xml)
            return formatted_xml
        except Exception as e:
            print(f"Błąd podczas generowania XML: {e}")
            try:
                return ET.tostring(root, encoding="utf-8").decode('utf-8')
            except Exception as e2:
                print(f"Drugi błąd: {e2}")
                raise e


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