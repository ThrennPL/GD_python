import xml.etree.ElementTree as ET
import uuid
from datetime import datetime
import xml.dom.minidom

class XMIActivityGenerator:
    """
    Generuje szkielet diagramu aktywności w formacie XMI,
    zgodny ze standardem Enterprise Architect.
    
    Klasa ta odwzorowuje strukturę pliku Czysty_diagram_aktywności.xml
    i służy jako podstawa do dalszego dynamicznego dodawania elementów.
    """

    def __init__(self, author: str = "Default_Author"):
        """
        Inicjalizuje generator XMI dla diagramu aktywności.

        Args:
            author (str): Autor diagramu.
        """
        self.author = author
        self.id_map = {}  # Słownik do przechowywania wygenerowanych ID
        self.ns = {
            'uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi': 'http://schema.omg.org/spec/XMI/2.1'
        }
        self._register_namespaces()

    def _register_namespaces(self):
        """Rejestruje przestrzenie nazw XML dla ElementTree."""
        ET.register_namespace('xmi', self.ns['xmi'])
        ET.register_namespace('uml', self.ns['uml'])

    def _generate_ea_id(self, prefix: str = "EAID") -> str:
        """Generuje unikalny identyfikator w formacie używanym przez EA."""
        return f"{prefix}_{str(uuid.uuid4()).upper().replace('-', '_')}"

    def _create_document_root(self) -> ET.Element:
        """
        Tworzy główny element dokumentu XMI (<xmi:XMI>).

        Returns:
            ET.Element: Główny element XMI.
        """
        root = ET.Element(ET.QName(self.ns['xmi'], 'XMI'), {
            'xmi:version': '2.1'
            # Usunięto redundantne atrybuty przestrzeni nazw:
            # 'xmlns:uml': self.ns['uml'],
            # 'xmlns:xmi': self.ns['xmi']
        })

        # Dodanie dokumentacji z informacjami o eksporterze
        ET.SubElement(root, ET.QName(self.ns['xmi'], 'Documentation'), {
            'exporter': 'Enterprise Architect',
            'exporterVersion': '6.5',
            'exporterID': '1560'
        })
        return root

    def _create_uml_model(self, root: ET.Element) -> ET.Element:
        """
        Tworzy główny element modelu UML (<uml:Model>).

        Args:
            root (ET.Element): Główny element dokumentu XMI.

        Returns:
            ET.Element: Element modelu UML.
        """
        return ET.SubElement(root, ET.QName(self.ns['uml'], 'Model'), {
            'xmi:type': 'uml:Model',
            'name': 'EA_Model',
            'visibility': 'public'
        })

    def _create_diagram_package(self, model: ET.Element, diagram_name: str) -> ET.Element:
        """
        Tworzy pakiet dla diagramu aktywności (<packagedElement>).

        Args:
            model (ET.Element): Element modelu UML.
            diagram_name (str): Nazwa diagramu, która będzie nazwą pakietu.

        Returns:
            ET.Element: Element pakietu.
        """
        self.id_map['package_element'] = self._generate_ea_id("EAPK")
        package_element = ET.SubElement(model, 'packagedElement', {
            'xmi:type': 'uml:Package',
            'xmi:id': self.id_map['package_element'],
            'name': diagram_name,
            'visibility': 'public'
        })
        return package_element

    def _create_ea_extensions(self, root: ET.Element, diagram_name: str):
        """
        Tworzy główny kontener z rozszerzeniami dla Enterprise Architect (<xmi:Extension>).

        Args:
            root (ET.Element): Główny element dokumentu XMI.
            diagram_name (str): Nazwa diagramu.
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        extension = ET.SubElement(root, ET.QName(self.ns['xmi'], 'Extension'), {
            'extender': 'Enterprise Architect',
            'extenderID': '6.5'
        })

        # Tworzenie poszczególnych sekcji wewnątrz rozszerzeń
        self._create_elements_section(extension, diagram_name, current_time)
        self._create_connectors_section(extension)
        self._create_primitivetypes_section(extension)
        ET.SubElement(extension, 'profiles') # Pusta sekcja profili
        self._create_diagrams_section(extension, diagram_name, current_time)
        
    def _create_elements_section(self, extension: ET.Element, diagram_name: str, current_time: str):
        """Tworzy sekcję <elements> w rozszerzeniach EA."""
        elements = ET.SubElement(extension, 'elements')
        element = ET.SubElement(elements, 'element', {
            'xmi:idref': self.id_map['package_element'],
            'xmi:type': 'uml:Package',
            'name': diagram_name,
            'scope': 'public'
        })

        # Zagnieżdżone tagi definiujące właściwości pakietu
        self.id_map['model_id'] = self._generate_ea_id("EAPK")
        ET.SubElement(element, 'model', {
            'package2': self.id_map['package_element'],
            'package': self.id_map['model_id'],
            'tpos': '0',
            'ea_localid': '1096', # Wartość z pliku wzorcowego
            'ea_eleType': 'package'
        })
        ET.SubElement(element, 'properties', {
            'isSpecification': 'false', 'sType': 'Package', 'nType': '0', 'scope': 'public'
        })
        ET.SubElement(element, 'project', {
            'author': self.author, 'version': '1.0', 'phase': '1.0',
            'created': current_time, 'modified': current_time,
            'complexity': '1', 'status': 'Proposed'
        })
        ET.SubElement(element, 'code', {'gentype': 'Java'})
        ET.SubElement(element, 'style', {
            'appearance': 'BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;VSwimLanes=1;HSwimLanes=1;BorderStyle=0;'
        })
        ET.SubElement(element, 'tags')
        ET.SubElement(element, 'xrefs')
        ET.SubElement(element, 'extendedProperties', {'tagged': '0', 'package_name': 'Example Model'})
        ET.SubElement(element, 'packageproperties', {'version': '1.0'})
        ET.SubElement(element, 'paths')
        ET.SubElement(element, 'times', {'created': current_time, 'modified': current_time})
        ET.SubElement(element, 'flags', {
            'iscontrolled': 'FALSE', 'isprotected': 'FALSE', 'usedtd': 'FALSE',
            'logxml': 'FALSE', 'packageFlags': 'isModel=1;VICON=3;'
        })

    def _create_connectors_section(self, extension: ET.Element):
        """Tworzy pustą sekcję <connectors>."""
        ET.SubElement(extension, 'connectors')

    def _create_primitivetypes_section(self, extension: ET.Element):
        """Tworzy sekcję <primitivetypes>."""
        primitivetypes = ET.SubElement(extension, 'primitivetypes')
        ET.SubElement(primitivetypes, 'packagedElement', {
            'xmi:type': 'uml:Package',
            'xmi:id': 'EAPrimitiveTypesPackage',
            'name': 'EA_PrimitiveTypes_Package',
            'visibility': 'public'
        })

    def _create_diagrams_section(self, extension: ET.Element, diagram_name: str, current_time: str):
        """Tworzy sekcję <diagrams> zawierającą definicję diagramu aktywności."""
        self.id_map['diagram'] = self._generate_ea_id("EAID")
        diagrams = ET.SubElement(extension, 'diagrams')
        diagram = ET.SubElement(diagrams, 'diagram', {'xmi:id': self.id_map['diagram']})

        ET.SubElement(diagram, 'model', {
            'package': self.id_map['package_element'],
            'localID': '1204', # Wartość z pliku wzorcowego
            'owner': self.id_map['package_element']
        })
        ET.SubElement(diagram, 'properties', {'name': diagram_name, 'type': 'Activity'})
        ET.SubElement(diagram, 'project', {
            'author': self.author, 'version': '1.0',
            'created': current_time, 'modified': current_time
        })
        ET.SubElement(diagram, 'style1', {
            'value': 'ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=795;DocSize.cy=1134;ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;ShowShape=1;AllDockable=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;ShowNotes=0;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;'
        })
        ET.SubElement(diagram, 'style2') # Pusty tag
        ET.SubElement(diagram, 'swimlanes', {
            'value': 'locked=false;orientation=0;width=0;inbar=false;names=false;color=-1;bold=false;fcol=0;tcol=-1;ofCol=-1;ufCol=-1;hl=1;ufh=0;hh=0;cls=0;bw=0;hli=0;bro=0;SwimlaneFont=lfh:-10,lfw:0,lfi:0,lfu:0,lfs:0,lfface:Calibri,lfe:0,lfo:0,lfchar:1,lfop:0,lfcp:0,lfq:0,lfpf=0,lfWidth=0;'
        })
        ET.SubElement(diagram, 'matrixitems', {
            'value': 'locked=false;matrixactive=false;swimlanesactive=true;kanbanactive=false;width=1;clrLine=0;'
        })
        ET.SubElement(diagram, 'extendedProperties') # Pusty tag

    def generate_xml_structure(self, diagram_name: str) -> str:
        """
        Główna metoda generująca całą strukturę XMI dla pustego diagramu aktywności.

        Args:
            diagram_name (str): Nazwa, która zostanie nadana diagramowi.

        Returns:
            str: Kompletny dokument XMI jako ciąg znaków.
        """
        # Reset mapy ID dla każdego nowego diagramu
        self.id_map = {}

        # Krok po kroku budujemy strukturę XML
        root = self._create_document_root()
        model = self._create_uml_model(root)
        self._create_diagram_package(model, diagram_name)
        self._create_ea_extensions(root, diagram_name)

        # Zwracamy wygenerowany XML jako string
        # 'xml_declaration=True' dodaje `<?xml ... ?>`
        # 'encoding="unicode"' zwraca string, a nie bajty
        return ET.tostring(root, encoding='unicode', method='xml', xml_declaration=True)

    def set_author(self, author: str):
        """Ustawia nowego autora diagramu."""
        self.author = author

# --- Przykład użycia ---
if __name__ == '__main__':
    # 1. Inicjalizacja generatora z domyślnym autorem
    generator = XMIActivityGenerator(author="195841")

    # 2. Ustawienie parametrów
    diagram_name = "Diagram aktywności"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"wygenerowany_diagram_aktywnosci_{timestamp}.xml"

    # 3. Wygenerowanie struktury XMI
    xml_content = generator.generate_xml_structure(diagram_name)
    
    # 4. Poprawienie nagłówka XML
    xml_content_fixed = xml_content.replace(
        '<?xml version=\'1.0\' encoding=\'unicode\'?>',
        '<?xml version="1.0" encoding="UTF-8"?>'
    )
    
    # 5. Formatowanie XML z wcięciami
    dom = xml.dom.minidom.parseString(xml_content_fixed)
    xml_content_formatted = dom.toprettyxml(indent="  ", encoding="utf-8").decode('utf-8')
    
    # 6. Zapisanie pliku z kodowaniem UTF-8
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(xml_content_formatted)
        print(f"✔ Plik '{output_filename}' został pomyślnie wygenerowany.")
        print(f"  - Autor: {generator.author}")
        print(f"  - Nazwa diagramu: {diagram_name}")
    except Exception as e:
        print(f"❌ Wystąpił błąd podczas zapisu pliku: {e}")