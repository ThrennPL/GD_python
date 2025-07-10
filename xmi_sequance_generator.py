import xml.etree.ElementTree as ET

def stworz_pusty_diagram_sekwencji(nazwa_pliku_wyjsciowego: str):
    """
    Generuje plik XMI dla programu Enterprise Architect,
    który zawiera pusty diagram sekwencji.

    Args:
        nazwa_pliku_wyjsciowego: Nazwa pliku XML do zapisu.
    """
    # Definicja i rejestracja przestrzeni nazw (namespaces)
    # Jest to kluczowe dla poprawnego formatowania prefixów (xmi:, uml:)
    ns = {
        'uml': 'http://schema.omg.org/spec/UML/2.1',
        'xmi': 'http://schema.omg.org/spec/XMI/2.1'
    }
    ET.register_namespace('xmi', ns['xmi'])
    ET.register_namespace('uml', ns['uml'])

    # --- Główny element - korzeń dokumentu ---
    # <xmi:XMI xmi:version="2.1" ...>
    root = ET.Element(ET.QName(ns['xmi'], 'XMI'), {'xmi:version': '2.1'})

    # --- Dokumentacja eksportera ---
    # <xmi:Documentation exporter="Enterprise Architect" ... />
    ET.SubElement(root, ET.QName(ns['xmi'], 'Documentation'), {
        'exporter': 'Enterprise Architect',
        'exporterVersion': '6.5',
        'exporterID': '1560'
    })

    # --- Główny model UML ---
    # <uml:Model xmi:type="uml:Model" name="EA_Model" ...>
    model = ET.SubElement(root, ET.QName(ns['uml'], 'Model'), {
        'xmi:type': 'uml:Model',
        'name': 'EA_Model',
        'visibility': 'public'
    })

    # --- Pakiet dla diagramu sekwencji ---
    # <packagedElement xmi:type="uml:Package" ...>
    package_element = ET.SubElement(model, 'packagedElement', {
        'xmi:type': 'uml:Package',
        'xmi:id': 'EAPK_D2B9D371_ED6F_4ff3_942C_D810982DBDA1',
        'name': 'Diagram sekwencji',
        'visibility': 'public'
    })

    # --- Kolaboracja wewnątrz pakietu ---
    # <packagedElement xmi:type="uml:Collaboration" ...>
    collaboration = ET.SubElement(package_element, 'packagedElement', {
        'xmi:type': 'uml:Collaboration',
        'xmi:id': 'EAID_CB000000_371_ED6F_4ff3_942C_D810982DBDA',
        'name': 'EA_Collaboration1',
        'visibility': 'public'
    })

    # --- Interakcja wewnątrz kolaboracji ---
    # <ownedBehavior xmi:type="uml:Interaction" ...>
    ET.SubElement(collaboration, 'ownedBehavior', {
        'xmi:type': 'uml:Interaction',
        'xmi:id': 'EAID_IN000000_371_ED6F_4ff3_942C_D810982DBDA',
        'name': 'EA_Interaction1',
        'visibility': 'public'
    })

    # --- Rozszerzenia specyficzne dla Enterprise Architect ---
    # <xmi:Extension extender="Enterprise Architect" ...>
    extension = ET.SubElement(root, ET.QName(ns['xmi'], 'Extension'), {
        'extender': 'Enterprise Architect',
        'extenderID': '6.5'
    })

    # Sekcja <elements> wewnątrz <xmi:Extension>
    elements = ET.SubElement(extension, 'elements')
    element = ET.SubElement(elements, 'element', {
        'xmi:idref': 'EAPK_D2B9D371_ED6F_4ff3_942C_D810982DBDA1',
        'xmi:type': 'uml:Package',
        'name': 'Diagram sekwencji',
        'scope': 'public'
    })
    ET.SubElement(element, 'model', {
        'package2': 'EAID_D2B9D371_ED6F_4ff3_942C_D810982DBDA1',
        'package': 'EAPK_25CB1803_12A5_47b7_BF59_0C80F57AA528',
        'tpos': '0',
        'ea_localid': '1030',
        'ea_eleType': 'package'
    })
    ET.SubElement(element, 'properties', {
        'isSpecification': 'false', 'sType': 'Package', 'nType': '0', 'scope': 'public'
    })
    # UWAGA: Poniższe wartości (np. autor, daty) są statyczne, aby wiernie
    # odwzorować plik. W docelowym programie można je generować dynamicznie.
    ET.SubElement(element, 'project', {
        'author': '195841', 'version': '1.0', 'phase': '1.0',
        'created': '2025-07-10 19:07:57', 'modified': '2025-07-10 19:07:57',
        'complexity': '1', 'status': 'Proposed'
    })
    ET.SubElement(element, 'code', {'gentype': 'Java'})
    ET.SubElement(element, 'style', {'appearance': 'BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;VSwimLanes=1;HSwimLanes=1;BorderStyle=0;'})
    ET.SubElement(element, 'tags')
    ET.SubElement(element, 'xrefs')
    ET.SubElement(element, 'extendedProperties', {'tagged': '0', 'package_name': 'Example Model'})
    ET.SubElement(element, 'packageproperties', {'version': '1.0'})
    ET.SubElement(element, 'paths')
    ET.SubElement(element, 'times', {'created': '2025-07-10 19:07:57', 'modified': '2025-07-10 19:07:57'})
    ET.SubElement(element, 'flags', {'iscontrolled': 'FALSE', 'isprotected': 'FALSE', 'usedtd': 'FALSE', 'logxml': 'FALSE', 'packageFlags': 'isModel=1;VICON=3;'})

    # Puste sekcje w <xmi:Extension>
    ET.SubElement(extension, 'connectors')
    primitivetypes = ET.SubElement(extension, 'primitivetypes')
    ET.SubElement(primitivetypes, 'packagedElement', {
        'xmi:type': 'uml:Package',
        'xmi:id': 'EAPrimitiveTypesPackage',
        'name': 'EA_PrimitiveTypes_Package',
        'visibility': 'public'
    })
    ET.SubElement(extension, 'profiles')

    # Sekcja <diagrams> wewnątrz <xmi:Extension>
    diagrams = ET.SubElement(extension, 'diagrams')
    diagram = ET.SubElement(diagrams, 'diagram', {'xmi:id': 'EAID_9BA79071_5A6C_4907_A147_1FF0D5634A31'})
    ET.SubElement(diagram, 'model', {
        'package': 'EAPK_D2B9D371_ED6F_4ff3_942C_D810982DBDA1',
        'localID': '1142',
        'owner': 'EAPK_D2B9D371_ED6F_4ff3_942C_D810982DBDA1'
    })
    ET.SubElement(diagram, 'properties', {'name': 'Diagram sekwencji', 'type': 'Sequence'})
    ET.SubElement(diagram, 'project', {
        'author': '195841', 'version': '1.0',
        'created': '2025-07-10 19:08:31', 'modified': '2025-07-10 19:08:31'
    })
    # Długie ciągi stylów - skopiowane 1:1 z oryginału
    ET.SubElement(diagram, 'style1', {'value': 'ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=795;DocSize.cy=1134;ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;ShowShape=1;AllDockable=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;ShowNotes=0;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;'})
    ET.SubElement(diagram, 'style2')
    ET.SubElement(diagram, 'swimlanes', {'value': 'locked=false;orientation=0;width=0;inbar=false;names=false;color=-1;bold=false;fcol=0;tcol=-1;ofCol=-1;ufCol=-1;hl=1;ufh=0;hh=0;cls=0;bw=0;hli=0;bro=0;SwimlaneFont=lfh:-10,lfw:0,lfi:0,lfu:0,lfs:0,lfface:Calibri,lfe:0,lfo:0,lfchar:1,lfop:0,lfcp:0,lfq:0,lfpf=0,lfWidth=0;'})
    ET.SubElement(diagram, 'matrixitems', {'value': 'locked=false;matrixactive=false;swimlanesactive=true;kanbanactive=false;width=1;clrLine=0;'})
    ET.SubElement(diagram, 'extendedProperties')

    ET.indent(root, space="  ")
    # --- Zapis do pliku ---
    tree = ET.ElementTree(root)
    # Używamy kodowania 'windows-1252' i deklaracji XML, aby plik był identyczny z oryginałem
    tree.write(nazwa_pliku_wyjsciowego, encoding='windows-1252', xml_declaration=True)
    print(f"Plik '{nazwa_pliku_wyjsciowego}' został pomyślnie wygenerowany.")

# --- Użycie funkcji ---
if __name__ == '__main__':
    stworz_pusty_diagram_sekwencji("wygenerowany_diagram.xml")
    print("Pusty diagram sekwencji został wygenerowany.")