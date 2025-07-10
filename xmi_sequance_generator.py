import xml.etree.ElementTree as ET
import uuid
from datetime import datetime


class XMISequenceGenerator:
    """
    Klasa do generowania plików XMI dla programu Enterprise Architect,
    które zawierają puste diagramy sekwencji.
    """
    
    def __init__(self, autor: str = "195841"):
        """
        Inicjalizuje generator XMI.
        
        Args:
            autor: Autor diagramu (domyślnie "195841")
        """
        self.autor = autor
        self.id_map = {}
        self.ns = {
            'uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi': 'http://schema.omg.org/spec/XMI/2.1'
        }
        self._zarejestruj_przestrzenie_nazw()
    
    def _zarejestruj_przestrzenie_nazw(self):
        """Rejestruje przestrzenie nazw XML."""
        ET.register_namespace('xmi', self.ns['xmi'])
        ET.register_namespace('uml', self.ns['uml'])
    
    def _generuj_ea_id(self, prefix: str = "EAID") -> str:
        """
        Generuje ID w formacie EA.
        
        Args:
            prefix: Prefiks ID (domyślnie "EAID")
            
        Returns:
            Wygenerowane ID w formacie EA
        """
        return f"{prefix}_{str(uuid.uuid4()).upper()}"
    
    def _stworz_korzen_dokumentu(self) -> ET.Element:
        """
        Tworzy główny element XMI.
        
        Returns:
            Główny element XMI
        """
        root = ET.Element(ET.QName(self.ns['xmi'], 'XMI'), {'xmi:version': '2.1'})
        
        # Dokumentacja eksportera
        ET.SubElement(root, ET.QName(self.ns['xmi'], 'Documentation'), {
            'exporter': 'Enterprise Architect',
            'exporterVersion': '6.5',
            'exporterID': '1560'
        })
        
        return root
    
    def _stworz_model_uml(self, root: ET.Element) -> ET.Element:
        """
        Tworzy główny model UML.
        
        Args:
            root: Element główny dokumentu
            
        Returns:
            Element modelu UML
        """
        return ET.SubElement(root, ET.QName(self.ns['uml'], 'Model'), {
            'xmi:type': 'uml:Model',
            'name': 'EA_Model',
            'visibility': 'public'
        })
    
    def _stworz_pakiet_diagramu(self, model: ET.Element, nazwa_diagramu: str) -> ET.Element:
        """
        Tworzy pakiet dla diagramu sekwencji.
        
        Args:
            model: Element modelu UML
            nazwa_diagramu: Nazwa diagramu
            
        Returns:
            Element pakietu
        """
        self.id_map['package_element'] = self._generuj_ea_id("EAPK")
        package_element = ET.SubElement(model, 'packagedElement', {
            'xmi:type': 'uml:Package',
            'xmi:id': self.id_map['package_element'],
            'name': nazwa_diagramu,
            'visibility': 'public'
        })
        
        # Kolaboracja wewnątrz pakietu
        self.id_map['collaboration'] = self._generuj_ea_id("EAPK")
        collaboration = ET.SubElement(package_element, 'packagedElement', {
            'xmi:type': 'uml:Collaboration',
            'xmi:id': self.id_map['collaboration'],
            'name': 'EA_Collaboration1',
            'visibility': 'public'
        })
        
        # Interakcja wewnątrz kolaboracji
        self.id_map['interaction'] = self._generuj_ea_id("EAID")
        interaction = ET.SubElement(collaboration, 'ownedBehavior', {
            'xmi:type': 'uml:Interaction',
            'xmi:id': self.id_map['interaction'],
            'name': 'EA_Interaction1',
            'visibility': 'public'
        })
        
        return package_element, interaction
    
    def _stworz_rozszerzenia_ea(self, root: ET.Element, nazwa_diagramu: str) -> None:
        """
        Tworzy rozszerzenia specyficzne dla Enterprise Architect.
        
        Args:
            root: Element główny dokumentu
            nazwa_diagramu: Nazwa diagramu
        """
        teraz = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        extension = ET.SubElement(root, ET.QName(self.ns['xmi'], 'Extension'), {
            'extender': 'Enterprise Architect',
            'extenderID': '6.5'
        })
        

        self._stworz_sekcje_elements(extension, nazwa_diagramu, teraz)
        
        # Puste sekcje
        ET.SubElement(extension, 'connectors')
        self._stworz_primitivetypes(extension)
        ET.SubElement(extension, 'profiles')
        
        # Sekcja diagrams
        self._stworz_sekcje_diagrams(extension, nazwa_diagramu, teraz)
    
    def _stworz_sekcje_elements(self, extension: ET.Element, nazwa_diagramu: str, teraz: str) -> None:

        """
        Tworzy sekcję elements w rozszerzeniach EA.
        
        Args:
            extension: Element rozszerzenia
            nazwa_diagramu: Nazwa diagramu
            teraz: Aktualny czas
        """
        elements = ET.SubElement(extension, 'elements')
        element = ET.SubElement(elements, 'element', {
            'xmi:idref': self.id_map['package_element'],
            'xmi:type': 'uml:Package',
            'name': nazwa_diagramu,
            'scope': 'public'
        })
        
        self.id_map['model_id'] = self._generuj_ea_id("EAPK")
        ET.SubElement(element, 'model', {
            'package2': self.id_map['package_element'],
            'package': self.id_map['model_id'],
            'tpos': '0',
            'ea_localid': '1030',
            'ea_eleType': 'package'
        })
        
        ET.SubElement(element, 'properties', {
            'isSpecification': 'false', 'sType': 'Package', 'nType': '0', 'scope': 'public'
        })
        
        ET.SubElement(element, 'project', {
            'author': self.autor, 'version': '1.0', 'phase': '1.0',
            'created': teraz, 'modified': teraz,
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
        ET.SubElement(element, 'times', {'created': teraz, 'modified': teraz})
        ET.SubElement(element, 'flags', {
            'iscontrolled': 'FALSE', 'isprotected': 'FALSE', 'usedtd': 'FALSE', 
            'logxml': 'FALSE', 'packageFlags': 'isModel=1;VICON=3;'
        })
        
        # Sekcja elements
        for key, actor_id in self.id_map.items():
            if key.startswith("actor_"):
                ET.SubElement(elements, 'element', {
                    'xmi:idref': actor_id,
                    'xmi:type': 'uml:Actor',
                    'name': key.replace("actor_", ""),
                    'scope': 'public'
                })
        for key, lifeline_id in self.id_map.items():
            if key.startswith("lifeline_"):
                ET.SubElement(elements, 'element', {
                    'xmi:idref': lifeline_id,
                    'xmi:type': 'uml:Lifeline',
                    'name': key.replace("lifeline_", ""),
                    'scope': 'public'
                })
            
    def _stworz_primitivetypes(self, extension: ET.Element) -> None:
        """
        Tworzy sekcję primitivetypes.
        
        Args:
            extension: Element rozszerzenia
        """
        primitivetypes = ET.SubElement(extension, 'primitivetypes')
        ET.SubElement(primitivetypes, 'packagedElement', {
            'xmi:type': 'uml:Package',
            'xmi:id': 'EAPrimitiveTypesPackage',
            'name': 'EA_PrimitiveTypes_Package',
            'visibility': 'public'
        })
    
    def _stworz_sekcje_diagrams(self, extension: ET.Element, nazwa_diagramu: str, teraz: str) -> None:
        """
        Tworzy sekcję diagrams w rozszerzeniach EA.
        
        Args:
            extension: Element rozszerzenia
            nazwa_diagramu: Nazwa diagramu
            teraz: Aktualny czas
        """
        self.id_map['diagram'] = self._generuj_ea_id("EAID")
        diagrams = ET.SubElement(extension, 'diagrams')
        diagram = ET.SubElement(diagrams, 'diagram', {'xmi:id': self.id_map['diagram']})
        
        ET.SubElement(diagram, 'model', {
            'package': self.id_map['package_element'],
            'localID': '1142',
            'owner': self.id_map['package_element']
        })
        
        ET.SubElement(diagram, 'properties', {'name': nazwa_diagramu, 'type': 'Sequence'})
        ET.SubElement(diagram, 'project', {
            'author': self.autor, 'version': '1.0',
            'created': teraz, 'modified': teraz
        })
        
        # Długie ciągi stylów
        ET.SubElement(diagram, 'style1', {
            'value': 'ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=795;DocSize.cy=1134;ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;ShowShape=1;AllDockable=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;ShowNotes=0;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;'
        })
        
        ET.SubElement(diagram, 'style2')
        ET.SubElement(diagram, 'swimlanes', {
            'value': 'locked=false;orientation=0;width=0;inbar=false;names=false;color=-1;bold=false;fcol=0;tcol=-1;ofCol=-1;ufCol=-1;hl=1;ufh=0;hh=0;cls=0;bw=0;hli=0;bro=0;SwimlaneFont=lfh:-10,lfw:0,lfi:0,lfu:0,lfs:0,lfface:Calibri,lfe:0,lfo:0,lfchar:1,lfop:0,lfcp:0,lfq:0,lfpf=0,lfWidth=0;'
        })
        ET.SubElement(diagram, 'matrixitems', {
            'value': 'locked=false;matrixactive=false;swimlanesactive=true;kanbanactive=false;width=1;clrLine=0;'
        })
        ET.SubElement(diagram, 'extendedProperties')
        
        # Tworzenie obiektów w diagramie
        diagram_objects = ET.SubElement(diagram, 'diagramObjects')
        x = 100  # startowa pozycja

        for key, lifeline_id in self.id_map.items():
            if key.startswith("lifeline_"):
                obj = ET.SubElement(diagram_objects, 'diagramObject')
                ET.SubElement(obj, 'model', {
                    'package': self.id_map['package_element'],
                    'element': lifeline_id
                })
                ET.SubElement(obj, 'geometry', {
                    'top': str(100),
                    'left': str(x),
                    'bottom': str(200),
                    'right': str(x + 100)
                })
                x += 200

    
    def generuj_diagram(self, nazwa_diagramu: str, nazwa_pliku: str) -> None:
        """
        Generuje plik XMI dla programu Enterprise Architect,
        który zawiera pusty diagram sekwencji.
        
        Args:
            nazwa_diagramu: Nazwa diagramu
            nazwa_pliku: Nazwa pliku XML do zapisu
        """
        # Resetuj mapę ID dla każdego nowego diagramu
        self.id_map = {}
        
        # Tworzenie struktury XML
        root = self._stworz_korzen_dokumentu()
        model = self._stworz_model_uml(root)
        package_element, interaction = self._stworz_pakiet_diagramu(model, nazwa_diagramu)
        self.dodaj_aktora(package_element, interaction, "Użytkownik")
        self.dodaj_aktora(package_element, interaction, "System")
        self._stworz_rozszerzenia_ea(root, nazwa_diagramu)
        
        # Formatowanie i zapis
        ET.indent(root, space="  ")
        tree = ET.ElementTree(root)
        tree.write(nazwa_pliku, encoding='windows-1252', xml_declaration=True)
        print(f"Plik '{nazwa_pliku}' został pomyślnie wygenerowany.")
    
    def ustaw_autora(self, autor: str) -> None:
        """
        Ustawia autora diagramów.
        
        Args:
            autor: Nowy autor
        """
        self.autor = autor
    
    def pobierz_autora(self) -> str:
        """
        Pobiera aktualnego autora.
        
        Returns:
            Aktualny autor
        """
        return self.autor
    
    def dodaj_aktora(self, package_element: ET.Element, interaction: ET.Element, nazwa: str) -> str:

        """
        Dodaje aktora do pakietu UML i jako lifeline do interakcji.

        Args:
            package_element: Element pakietu UML (z _stworz_pakiet_diagramu)
            nazwa: Nazwa aktora

        Returns:
            ID lifeline'u
        """
        actor_id = self._generuj_ea_id("EAID")
        lifeline_id = self._generuj_ea_id("EAID")

        # Dodaj aktora do pakietu
        actor = ET.SubElement(package_element, 'packagedElement', {
            'xmi:type': 'uml:Actor',
            'xmi:id': actor_id,
            'name': nazwa,
            'visibility': 'public'
        })

        # Znajdź interakcję (zakładamy, że jest tylko jedna)
        ET.SubElement(interaction, 'lifeline', {
            'xmi:type': 'uml:Lifeline',
            'xmi:id': lifeline_id,
            'name': nazwa,
            'represents': actor_id
        })

        # Zapisz ID
        self.id_map[f"actor_{nazwa}"] = actor_id
        self.id_map[f"lifeline_{nazwa}"] = lifeline_id

        return lifeline_id




# --- Przykład użycia ---
if __name__ == '__main__':
    generator = XMISequenceGenerator(autor="195841")
    autor="195841"
    teraz = datetime.now().strftime("%Y%m%d_%H%M%S")
    nazwa_pliku = f"wygenerowany_diagram_{teraz}.xml"
    diagram_name = "Diagram sekwencji"
    
    
    
    # Można też zmienić autora i wygenerować kolejny diagram
    generator.ustaw_autora(autor)
    generator.generuj_diagram(diagram_name, nazwa_pliku)