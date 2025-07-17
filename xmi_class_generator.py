import xml.dom.minidom
import xml.etree.ElementTree as ET
from datetime import datetime
import uuid
import os
import re
from typing import Dict, List, Optional, Tuple
from plantuml_model import UMLClass, UMLRelation, UMLEnum, UMLNote
from plantuml_class_parser import PlantUMLClassParser
from logger_utils import log_info, log_error, log_exception, log_debug, setup_logger, log_warning
from translations_pl import TRANSLATIONS as PL
from translations_en import TRANSLATIONS as EN


setup_logger()

def tr(key):
    return EN[key] if LANG == "en" else PL[key]

class XMIClassGenerator:
    """Generator plików XMI dla diagramów klas Enterprise Architect"""
    
    def __init__(self, autor: str = "GD Generator"):
        """
        Inicjalizuje generator XMI.
        
        Args:
            autor: Autor diagramu
        """
        self.autor = autor
        self.id_map = {}
        self.namespaces = {
            'xmi': 'http://schema.omg.org/spec/XMI/2.1',
            'uml': 'http://schema.omg.org/spec/UML/2.1',
            'StandardProfileL2': 'http://www.omg.org/spec/UML/20110701/StandardProfileL2.xmi'
        }
        self.ea_package_id = "EAPK_CB7224AD_95A4_4e31_9549_415EAEE5D3E4"
        
    def _generate_uuid(self, prefix="EAID_"):
        """Generuje unikalny identyfikator w formacie EA."""
        return f"{prefix}{str(uuid.uuid4()).replace('-', '_')}"
    
    def _get_current_timestamp(self):
        """Zwraca aktualny timestamp w formacie używanym przez EA."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def generate_skeleton(self, diagram_name="Classes", package_name="DiagramKlas"):
        """
        Generuje podstawowy szkielet pliku XMI.
        
        Args:
            diagram_name: Nazwa diagramu
            package_name: Nazwa pakietu
            
        Returns:
            tuple: (dokument DOM, element główny, ID pakietu, ID diagramu)
        """
        # Tworzymy pusty dokument bez określania root element z prefixem
        doc = xml.dom.minidom.getDOMImplementation().createDocument(None, "XMI", None)
        root = doc.documentElement
        
        # Zmieniamy nazwę na xmi:XMI - najpierw usuwamy stary element root
        root_new = doc.createElement("XMI")
        # Dodajemy atrybuty i przestrzenie nazw
        root_new.setAttribute("xmi:version", "2.1")
        
        # Ustawiamy przestrzenie nazw
        for prefix, uri in self.namespaces.items():
            root_new.setAttribute(f"xmlns:{prefix}", uri)
            
        # Zamieniamy stary root na nowy
        doc.replaceChild(root_new, root)
        root = root_new
        
        # Dokumentacja XMI
        documentation = doc.createElement("Documentation")
        documentation.setAttribute("exporter", "Enterprise Architect")
        documentation.setAttribute("exporterVersion", "6.5")
        documentation.setAttribute("exporterID", "1560")
        root.appendChild(documentation)
        
        # Model UML
        model = doc.createElement("Model")
        model.setAttribute("xmi:type", "uml:Model")
        model.setAttribute("name", "EA_Model")
        model.setAttribute("visibility", "public")
        model.setAttribute("ea_package_id", self.ea_package_id)
        model.setAttribute("ea_version", "2.0")
        root.appendChild(model)
        
        # Pakiet główny
        package_id = self._generate_uuid()
        self.id_map['package'] = package_id
        
        package = doc.createElement("packagedElement")
        package.setAttribute("xmi:type", "uml:Package")
        package.setAttribute("xmi:id", package_id)
        package.setAttribute("name", package_name)
        package.setAttribute("visibility", "public")
        model.appendChild(package)
        
        # Rozszerzenie XMI (EA-specific)
        extension = doc.createElement("Extension")
        extension.setAttribute("extender", "Enterprise Architect")
        extension.setAttribute("extenderID", "6.5")
        root.appendChild(extension)
        
        # Sekcje rozszerzenia
        elements = doc.createElement("elements")
        extension.appendChild(elements)
        
        # Element pakietu
        pkg_element = doc.createElement("element")
        pkg_element.setAttribute("xmi:idref", package_id)
        pkg_element.setAttribute("xmi:type", "uml:Package")
        pkg_element.setAttribute("name", package_name)
        pkg_element.setAttribute("scope", "public")
        elements.appendChild(pkg_element)
        
        # Właściwości pakietu
        model_elem = doc.createElement("model")
        model_elem.setAttribute("package2", package_id)
        model_elem.setAttribute("package", self.ea_package_id)
        model_elem.setAttribute("tpos", "0")
        model_elem.setAttribute("ea_localid", "976")
        model_elem.setAttribute("ea_eleType", "package")
        pkg_element.appendChild(model_elem)
        
        properties = doc.createElement("properties")
        properties.setAttribute("isSpecification", "false")
        properties.setAttribute("sType", "Package")
        properties.setAttribute("nType", "0")
        properties.setAttribute("scope", "public")
        pkg_element.appendChild(properties)
        
        project = doc.createElement("project")
        project.setAttribute("author", self.autor)
        project.setAttribute("version", "1.0")
        project.setAttribute("phase", "1.0")
        project.setAttribute("created", self._get_current_timestamp())
        project.setAttribute("modified", self._get_current_timestamp())
        project.setAttribute("complexity", "1")
        project.setAttribute("status", "Proposed")
        pkg_element.appendChild(project)
        
        code = doc.createElement("code")
        code.setAttribute("gentype", "Java")
        pkg_element.appendChild(code)
        
        style = doc.createElement("style")
        style.setAttribute("appearance", "BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;VSwimLanes=1;HSwimLanes=1;BorderStyle=0;")
        pkg_element.appendChild(style)
        
        tags = doc.createElement("tags")
        pkg_element.appendChild(tags)
        
        xrefs = doc.createElement("xrefs")
        pkg_element.appendChild(xrefs)
        
        extendedProperties = doc.createElement("extendedProperties")
        extendedProperties.setAttribute("tagged", "0")
        extendedProperties.setAttribute("package_name", package_name)
        pkg_element.appendChild(extendedProperties)
        
        packageproperties = doc.createElement("packageproperties")
        packageproperties.setAttribute("version", "1.0")
        pkg_element.appendChild(packageproperties)
        
        paths = doc.createElement("paths")
        pkg_element.appendChild(paths)
        
        times = doc.createElement("times")
        times.setAttribute("created", self._get_current_timestamp().split(" ")[0] + " 00:00:00")
        times.setAttribute("modified", self._get_current_timestamp())
        pkg_element.appendChild(times)
        
        flags = doc.createElement("flags")
        flags.setAttribute("iscontrolled", "FALSE")
        flags.setAttribute("isprotected", "FALSE")
        flags.setAttribute("usedtd", "FALSE")
        flags.setAttribute("logxml", "FALSE")
        pkg_element.appendChild(flags)
        
        # Sekcja connectors
        connectors = doc.createElement("connectors")
        extension.appendChild(connectors)
        
        # Sekcja diagrams
        diagrams = doc.createElement("diagrams")
        extension.appendChild(diagrams)
        
        # Diagram
        diagram_id = self._generate_uuid()
        self.id_map['diagram'] = diagram_id
        
        diagram = doc.createElement("diagram")
        diagram.setAttribute("xmi:id", diagram_id)
        diagrams.appendChild(diagram)
        
        model_diag = doc.createElement("model")
        model_diag.setAttribute("package", package_id)
        model_diag.setAttribute("localID", "1102")
        model_diag.setAttribute("owner", package_id)
        diagram.appendChild(model_diag)
        
        properties_diag = doc.createElement("properties")
        properties_diag.setAttribute("name", diagram_name)
        properties_diag.setAttribute("type", "Logical")
        diagram.appendChild(properties_diag)
        
        project_diag = doc.createElement("project")
        project_diag.setAttribute("author", self.autor)
        project_diag.setAttribute("version", "1.0")
        project_diag.setAttribute("created", self._get_current_timestamp())
        project_diag.setAttribute("modified", self._get_current_timestamp())
        diagram.appendChild(project_diag)
        
        style_diag = doc.createElement("style1")
        style_diag.setAttribute("value", "ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=795;DocSize.cy=1134;ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;ShowShape=1;AllDockable=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;ShowNotes=0;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;")
        diagram.appendChild(style_diag)
        
        style_diag2 = doc.createElement("style2")
        style_diag2.setAttribute("value", "ExcludeRTF=0;DocAll=0;HideQuals=0;AttPkg=1;ShowTests=0;ShowMaint=0;SuppressFOC=1;MatrixActive=0;SwimlanesActive=1;KanbanActive=0;MatrixLineWidth=1;MatrixLineClr=0;MatrixLocked=0;TConnectorNotation=UML 2.1;TExplicitNavigability=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;MDGDgm=;STBLDgm=;ShowNotes=0;VisibleAttributeDetail=0;ShowOpRetType=1;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;SuppressedCompartments=;Theme=:119;SaveTag=4C19637D;")
        diagram.appendChild(style_diag2)
        
        swimlanes = doc.createElement("swimlanes")
        swimlanes.setAttribute("value", "locked=false;orientation=0;width=0;inbar=false;names=false;color=-1;bold=false;fcol=0;tcol=-1;ofCol=-1;ufCol=-1;hl=1;ufh=0;hh=0;cls=0;bw=0;hli=0;bro=0;")
        diagram.appendChild(swimlanes)
        
        # Elements w diagramie
        elements_diag = doc.createElement("elements")
        diagram.appendChild(elements_diag)
        
        # Sekcja primitivetypes
        primitivetypes = doc.createElement("primitivetypes")
        extension.appendChild(primitivetypes)

        # Sekcja profiles
        profiles = doc.createElement("profiles")
        extension.appendChild(profiles)

        return doc, root, package, extension

    def _map_type_to_id(self, type_name):
        """
        Mapuje nazwę typu na ID typu.
        
        Args:
            type_name: Nazwa typu
            
        Returns:
            str: ID typu lub None jeśli nie znaleziono
        """
        # Normalizacja nazwy typu (małe litery dla lepszego dopasowania)
        normalized_name = type_name.lower()
        
        # Obsługa aliasów dla typów podstawowych
        if normalized_name in ["string", "str", "text"]:
            return self.id_map.get('type_string')
        elif normalized_name in ["int", "integer", "number"]:
            return self.id_map.get('type_int')
        elif normalized_name in ["double", "float", "decimal", "real"]:
            return self.id_map.get('type_double')
        elif normalized_name in ["bool", "boolean"]:
            return self.id_map.get('type_boolean')

        # Sprawdź, czy to typ pierwotny
        type_id = self.id_map.get(f'type_{type_name}')
        if type_id:
            return type_id
        
        # Sprawdź, czy to klasa
        class_id = self.id_map.get(f'class_{type_name}')
        if class_id:
            return class_id
        
        # Sprawdź, czy to enum
        enum_id = self.id_map.get(f'enum_{type_name}')
        if enum_id:
            return enum_id
        
        # Nie znaleziono typu - użyj string jako domyślny
        return self.id_map.get('type_string')

    def add_class(self, doc, package_element, uml_class: UMLClass):
        """
        Dodaje klasę do dokumentu XMI.
        
        Args:
            doc: Dokument XML DOM
            package_element: Element pakietu, do którego dodajemy klasę
            uml_class: Obiekt klasy UML
        
        Returns:
            tuple: (Element klasy, ID klasy)
        """
        class_id = self._generate_uuid()
        self.id_map[f"class_{uml_class.name}"] = class_id
        
        # Tworzymy element klasy w modelu UML
        class_element = doc.createElement("packagedElement")
        
        # Obsługa interfejsów vs klas
        if uml_class.stereotype == 'interface':
            class_element.setAttribute("xmi:type", "uml:Interface")
        else:
            class_element.setAttribute("xmi:type", "uml:Class")
            
        class_element.setAttribute("xmi:id", class_id)
        class_element.setAttribute("name", uml_class.name)
        class_element.setAttribute("visibility", "public")
        
        if uml_class.is_abstract:
            class_element.setAttribute("isAbstract", "true")
        
        package_element.appendChild(class_element)
        
        # Dodawanie atrybutów
        for attr in uml_class.attributes:
            attr_id = self._generate_uuid()
            attr_decl = attr["declaration"]
            attr_name, attr_type = self._split_attribute(attr_decl)
            modifiers = attr.get("modifiers", [])
            
            attr_elem = doc.createElement("ownedAttribute")
            attr_elem.setAttribute("xmi:id", attr_id)
            attr_elem.setAttribute("name", attr_name)
            attr_elem.setAttribute("visibility", self._get_visibility(attr_decl))
            
            # Powiąż z typem - użyj ID typu zamiast nazwy
            if attr_type:
                type_id = self._map_type_to_id(attr_type)
                if type_id:
                    if attr_type:
                        type_id = self._map_type_to_id(attr_type)
                        if type_id:
                            type_elem = doc.createElement("type")
                            type_elem.setAttribute("xmi:idref", type_id)
                            attr_elem.appendChild(type_elem)
                    
                    # Dodaj jawną krotność - zapobiega oznaczaniu {bag}
                    lower_value = doc.createElement("lowerValue")
                    lower_value.setAttribute("xmi:type", "uml:LiteralInteger")
                    lower_value.setAttribute("xmi:id", self._generate_uuid())
                    lower_value.setAttribute("value", "1")
                    attr_elem.appendChild(lower_value)
                    
                    upper_value = doc.createElement("upperValue")
                    upper_value.setAttribute("xmi:type", "uml:LiteralInteger")
                    upper_value.setAttribute("xmi:id", self._generate_uuid())
                    upper_value.setAttribute("value", "1")
                    attr_elem.appendChild(upper_value)
            
            if "static" in modifiers:
                attr_elem.setAttribute("isStatic", "true")
                
            class_element.appendChild(attr_elem)
            self.id_map[f"attr_{uml_class.name}_{attr_name}"] = attr_id
        
        # Dodawanie metod
        for method in uml_class.methods:
            method_id = self._generate_uuid()
            method_sig = method["signature"]
            method_name = self._clean_method_name(method_sig)
            modifiers = method.get("modifiers", [])
            
            op_elem = doc.createElement("ownedOperation")
            op_elem.setAttribute("xmi:id", method_id)
            op_elem.setAttribute("name", method_name)
            op_elem.setAttribute("visibility", self._get_visibility(method_sig))
            
            if "static" in modifiers:
                op_elem.setAttribute("isStatic", "true")
            if "abstract" in modifiers:
                op_elem.setAttribute("isAbstract", "true")
                
            class_element.appendChild(op_elem)
            self.id_map[f"method_{uml_class.name}_{method_name}"] = method_id
        
        # Dodanie stereotypu (zgodne z formatem EA)
        if uml_class.stereotype and uml_class.stereotype != 'interface':
            self._dodaj_stereotyp_do_elementu_EA(doc, class_id, uml_class.stereotype)
        
        return class_element, class_id
    
    def _dodaj_stereotyp_do_elementu_EA(self, doc, element_id, stereotype):
        """
        Dodaje stereotyp do elementu w rozszerzeniu EA.
        
        Args:
            doc: Dokument XML DOM
            element_id: ID elementu
            stereotype: Nazwa stereotypu
        """
        # Znajdź element w rozszerzeniu EA
        elements = doc.getElementsByTagName("element")
        for elem in elements:
            if elem.getAttribute("xmi:idref") == element_id:
                # Sprawdź czy element ma już sekcję stereotypes
                stereotypes_elem = None
                for node in elem.childNodes:
                    if node.nodeType == node.ELEMENT_NODE and node.nodeName == "stereotypes":
                        stereotypes_elem = node
                        break
                
                # Jeśli nie ma, utwórz
                if not stereotypes_elem:
                    stereotypes_elem = doc.createElement("stereotypes")
                    elem.appendChild(stereotypes_elem)
                
                # Dodaj stereotyp
                stereotype_elem = doc.createElement("stereotype")
                stereotype_elem.setAttribute("stereotype", stereotype)
                stereotype_elem.setAttribute("ea_type", "element")
                stereotypes_elem.appendChild(stereotype_elem)
                
                # Dodaj odpowiednie style dla stereotypu
                style_elem = None
                for node in elem.childNodes:
                    if node.nodeType == node.ELEMENT_NODE and node.nodeName == "style":
                        style_elem = node
                        break
                        
                if style_elem:
                    curr_style = style_elem.getAttribute("appearance") or ""
                    # Dodaj informacje o stereotypie do stylu
                    if "StereotypeFont=" not in curr_style:
                        curr_style += f";StereotypeFont=-1;StereotypeVisible=1;"
                    style_elem.setAttribute("appearance", curr_style)
                    
                break

    def add_enum(self, doc, package_element, uml_enum: UMLEnum):
        """
        Dodaje enumerator do dokumentu XMI.
        
        Args:
            doc: Dokument XML DOM
            package_element: Element pakietu
            uml_enum: Obiekt enumeratora UML
        
        Returns:
            tuple: (Element enumeratora, ID enumeratora)
        """
        enum_id = self._generate_uuid()
        self.id_map[f"enum_{uml_enum.name}"] = enum_id
        
        enum_element = doc.createElement("packagedElement")
        enum_element.setAttribute("xmi:type", "uml:Enumeration")
        enum_element.setAttribute("xmi:id", enum_id)
        enum_element.setAttribute("name", uml_enum.name)
        enum_element.setAttribute("visibility", "public")
        
        package_element.appendChild(enum_element)
        
        # Dodaj wartości enumeratora
        for value in uml_enum.values:
            literal_id = self._generate_uuid()
            
            literal_elem = doc.createElement("ownedLiteral")
            literal_elem.setAttribute("xmi:id", literal_id)
            literal_elem.setAttribute("name", value)
            
            enum_element.appendChild(literal_elem)
            self.id_map[f"literal_{uml_enum.name}_{value}"] = literal_id
        
        return enum_element, enum_id

    def dodaj_wszystkie_relacje(self, doc, package_element, relations, extension_element):
        """
        Centralna metoda do dodawania wszystkich relacji do modelu i konektorów do rozszerzenia EA.
        
        Args:
            doc: Dokument XML DOM
            package_element: Element pakietu
            relations: Lista relacji UML
            extension_element: Element rozszerzenia EA
        
        Returns:
            dict: Mapa ID relacji
        """
        # Mapa ID relacji
        relation_ids = {}
        
        # Dodaj relacje do modelu UML
        for relation in relations:
            source_id = self.id_map.get(f"class_{relation.source}") or self.id_map.get(f"enum_{relation.source}")
            target_id = self.id_map.get(f"class_{relation.target}") or self.id_map.get(f"enum_{relation.target}")
            
            if not source_id or not target_id:
                log_warning(f"WARN: Nie znaleziono ID dla {relation.source} lub {relation.target}, pomijam relację")
                continue
                
            # Obsługa różnych typów relacji
            rel_elem, rel_id = None, None
            if relation.relation_type == 'inheritance':
                rel_elem, rel_id = self._add_inheritance(doc, package_element, relation, source_id, target_id)
            elif relation.relation_type == 'realization':
                rel_elem, rel_id = self._add_realization(doc, package_element, relation, source_id, target_id)
            else:
                rel_elem, rel_id = self._add_association(doc, package_element, relation, source_id, target_id)
                
            if rel_elem and rel_id:
                # Zapisz ID relacji w mapie
                key = f"{relation.relation_type}_{relation.source}_{relation.target}"
                if relation.label:
                    key += f"_{relation.label}"
                relation_ids[key] = rel_id
        
        # Dodaj konektory do rozszerzenia EA
        self.add_diagram_connectors(doc, extension_element, relations)
        
        # Dodaj relacje do diagramu
        self._dodaj_relacje_do_diagramu(doc, extension_element, relations)
        
        return relation_ids
    
    def _dodaj_relacje_do_diagramu(self, doc, extension_element, relations):
        """
        Dodaje relacje do diagramu w rozszerzeniu EA.
        
        Args:
            doc: Dokument XML DOM
            extension_element: Element rozszerzenia EA
            relations: Lista relacji UML
        """
        # Znajdź diagram
        diagram_id = self.id_map.get('diagram')
        if not diagram_id:
            log_warning("WARN: Nie znaleziono ID diagramu")
            return
            
        diagrams = doc.getElementsByTagName("diagram")
        diagram = None
        for diag in diagrams:
            if diag.getAttribute("xmi:id") == diagram_id:
                diagram = diag
                break
        
        if not diagram:
            log_warning("WARN: Nie znaleziono elementu diagramu")
            return
        
        # Znajdź lub utwórz sekcję diagramlinks
        diagramlinks = None
        for node in diagram.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.nodeName == "diagramlinks":
                diagramlinks = node
                break
        
        if not diagramlinks:
            diagramlinks = doc.createElement("diagramlinks")
            diagram.appendChild(diagramlinks)
        
        # Stwórz słownik do śledzenia już dodanych linków
        added_links = {}
        # Dodaj linki dla wszystkich relacji
        for relation in relations:
            # Pobierz ID źródła i celu
            source_id = self.id_map.get(f"class_{relation.source}") or self.id_map.get(f"enum_{relation.source}")
            target_id = self.id_map.get(f"class_{relation.target}") or self.id_map.get(f"enum_{relation.target}")
            
            if not source_id or not target_id:
                continue
                
            # Znajdź ID konektora
            connector_id = None
            if relation.relation_type == 'inheritance':
                connector_id = self.id_map.get(f'inheritance_{relation.source}_{relation.target}')
            elif relation.relation_type == 'realization':
                connector_id = self.id_map.get(f'realization_{relation.source}_{relation.target}')
            else:
                assoc_key = f'association_{relation.source}_{relation.target}'
                if relation.label:
                    assoc_key += f'_{relation.label}'
                connector_id = self.id_map.get(assoc_key)
            
            if connector_id:
                link_key = f"{source_id}_{target_id}_{connector_id}"
        
                # Sprawdź czy link już istnieje
                if link_key in added_links:
                    continue
                # Dodaj link diagramu
                diagramlink = doc.createElement("diagramlink")
                diagramlink.setAttribute("connectorID", connector_id)
                diagramlink.setAttribute("start", source_id)
                diagramlink.setAttribute("end", target_id)
                diagramlink.setAttribute("linkID", f"DCLINK_{uuid.uuid4().hex[:8].upper()}")
                diagramlink.setAttribute("hidden", "0")
                diagramlink.setAttribute("geometry", "EDGE=1;$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path=;")
                if relation.source_multiplicity or relation.target_multiplicity or relation.label:
                    lb_value = relation.source_multiplicity if relation.source_multiplicity else ""
                    mt_value = relation.label if relation.label else ""
                    rb_value = relation.target_multiplicity if relation.target_multiplicity else ""
                    
                    diagramlink.setAttribute("labels", f"lb={lb_value};mt={mt_value};rb={rb_value};")

                diagramlinks.appendChild(diagramlink)

                added_links[link_key] = True

    def add_relation(self, doc, package_element, relation: UMLRelation):
        """
        Dodaje relację między klasami.
        
        Args:
            doc: Dokument XML DOM
            package_element: Element pakietu
            relation: Obiekt relacji UML
        
        Returns:
            tuple: (Element relacji, ID relacji)
        """
        source_id = self.id_map.get(f"class_{relation.source}") or self.id_map.get(f"enum_{relation.source}")
        target_id = self.id_map.get(f"class_{relation.target}") or self.id_map.get(f"enum_{relation.target}")
        
        if not source_id or not target_id:
            log_warning(f"WARN: Nie znaleziono ID dla {relation.source} lub {relation.target}, pomijam relację")
            return None, None
        
        # Obsługa dziedziczenia jako specjalny przypadek
        if relation.relation_type == 'inheritance':
            return self._add_inheritance(doc, package_element, relation, source_id, target_id)
        elif relation.relation_type == 'realization':
            return self._add_realization(doc, package_element, relation, source_id, target_id)
        else:
            # Standardowa asocjacja, agregacja, kompozycja
            return self._add_association(doc, package_element, relation, source_id, target_id)

    def _add_inheritance(self, doc, package_element, relation: UMLRelation, source_id: str, target_id: str):
        """
        Dodaje relację dziedziczenia do dokumentu XMI zgodnie ze standardem EA.
        
        Args:
            doc: Dokument XML
            package_element: Element pakietu, w którym dodać relację
            relation: Obiekt relacji UML
            source_id: ID źródłowego elementu (dziecko)
            target_id: ID docelowego elementu (rodzic)
            
        Returns:
            tuple: (element relacji, ID relacji)
        """
        # Generuj ID dla generalizacji
        generalization_id = self._generate_uuid()
        
        # Utwórz element generalizacji
        gen_elem = doc.createElement("packagedElement")
        gen_elem.setAttribute("xmi:type", "uml:Generalization")
        gen_elem.setAttribute("xmi:id", generalization_id)
        gen_elem.setAttribute("general", target_id)
        
        # Dodaj atrybut client/subtype (źródło - klasa dziedzicząca)
        client_elem = doc.createElement("client")
        client_elem.setAttribute("xmi:idref", source_id)
        gen_elem.appendChild(client_elem)
        
        # Dodaj atrybut supplier/supertype (cel - klasa bazowa)
        supplier_elem = doc.createElement("supplier")
        supplier_elem.setAttribute("xmi:idref", target_id)
        gen_elem.appendChild(supplier_elem)
        
        # Zapisz ID do mapy identyfikatorów
        self.id_map[f'inheritance_{relation.source}_{relation.target}'] = generalization_id
        
        # Dodaj generalizację do pakietu
        package_element.appendChild(gen_elem)
        
        self.id_map[f'inheritance_{relation.source}_{relation.target}'] = generalization_id
    
        return gen_elem, generalization_id

    def _add_realization(self, doc, package_element, relation: UMLRelation, source_id: str, target_id: str):
        """
        Dodaje relację realizacji interfejsu.
        
        Args:
            doc: Dokument XML DOM
            package_element: Element pakietu
            relation: Obiekt relacji UML
            source_id: ID klasy implementującej
            target_id: ID interfejsu
        
        Returns:
            tuple: (Element relacji, ID relacji)
        """
        realization_id = self._generate_uuid()
        
        # Znajdź element klasy implementującej
        source_elem = None
        for node in package_element.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.getAttribute("xmi:id") == source_id:
                source_elem = node
                break
        
        if source_elem:
            # Dodaj interfaceRealization do klasy implementującej
            real_elem = doc.createElement("interfaceRealization")
            real_elem.setAttribute("xmi:id", realization_id)
            real_elem.setAttribute("client", source_id)
            real_elem.setAttribute("supplier", target_id)
            real_elem.setAttribute("contract", target_id)
            
            source_elem.appendChild(real_elem)
            
            return real_elem, realization_id
        else:
            log_warning(f"WARN: Nie znaleziono elementu klasy {relation.source} dla relacji realizacji")
            return None, None



    def _add_multiplicity(self, doc, end_element, lower: str, upper: str):
        """
        Dodaje informacje o liczności do końca asocjacji.
        
        Args:
            doc: Dokument XML DOM
            end_element: Element końca asocjacji
            lower: Dolna granica liczności
            upper: Górna granica liczności
        """
        # Dolna granica
        lower_value = doc.createElement("lowerValue")
        lower_value.setAttribute("xmi:type", "uml:LiteralInteger")
        lower_value.setAttribute("xmi:id", self._generate_uuid())
        lower_value.setAttribute("value", lower)
        end_element.appendChild(lower_value)
        
        # Górna granica
        upper_value = doc.createElement("upperValue")
        if upper == "*":
            upper_value.setAttribute("xmi:type", "uml:LiteralUnlimitedNatural")
            upper_value.setAttribute("value", "-1")  # '*' jest reprezentowane jako '-1' w EA
        else:
            upper_value.setAttribute("xmi:type", "uml:LiteralInteger")
            upper_value.setAttribute("value", upper)
        upper_value.setAttribute("xmi:id", self._generate_uuid())
        end_element.appendChild(upper_value)

    def add_diagram_elements(self, doc, extension_element, classes, enums, relations):
        """
        Dodaje elementy diagramu do rozszerzenia EA.
        
        Args:
            doc: Dokument XML DOM
            extension_element: Element rozszerzenia EA
            classes: Klasy UML
            enums: Enumy UML
            relations: Relacje UML
        """
        # Znajdź element diagramu
        diagram_id = self.id_map['diagram']
        package_id = self.id_map['package']
        
        # Znajdź element diagrams
        diagrams_elem = None
        for node in extension_element.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.nodeName == "diagrams":
                diagrams_elem = node
                break
        
        if not diagrams_elem:
            log_warning("WARN: Nie znaleziono sekcji diagrams w rozszerzeniu")
            return
        
        # Znajdź element diagram
        diagram_elem = None
        for node in diagrams_elem.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.nodeName == "diagram" and node.getAttribute("xmi:id") == diagram_id:
                diagram_elem = node
                break
        
        if not diagram_elem:
            log_warning("WARN: Nie znaleziono elementu diagram w sekcji diagrams")
            return
        
        # Znajdź lub utwórz elements w diagramie
        elements_diag = None
        for node in diagram_elem.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.nodeName == "elements":
                elements_diag = node
                break
        
        if not elements_diag:
            elements_diag = doc.createElement("elements")
            diagram_elem.appendChild(elements_diag)
        
        # Dodaj elementy klas do diagramu
        x, y = 100, 100
        i = 0
        
        # Dodawanie klas
        for class_name, uml_class in classes.items():
            class_id = self.id_map.get(f"class_{class_name}")
            if not class_id:
                continue
                
            # Dodaj element diagramu dla klasy
            element = doc.createElement("element")
            element.setAttribute("geometry", f"Left={x};Top={y};Right={x+150};Bottom={y+120};")
            element.setAttribute("subject", class_id)
            element.setAttribute("seqno", str(i))
            element.setAttribute("style", "DUID=unique_id;")
            
            elements_diag.appendChild(element)
            i += 1
            
            # Przesuń pozycję dla następnego elementu
            x += 200
            if x > 700:  # Jeśli przekroczy szerokość diagramu, przejdź do nowej linii
                x = 100
                y += 150
        
        # Dodawanie enumów
        for enum_name, uml_enum in enums.items():
            enum_id = self.id_map.get(f"enum_{enum_name}")
            if not enum_id:
                continue
                
            # Dodaj element diagramu dla enuma
            element = doc.createElement("element")
            element.setAttribute("geometry", f"Left={x};Top={y};Right={x+150};Bottom={y+100};")
            element.setAttribute("subject", enum_id)
            element.setAttribute("seqno", str(i))
            element.setAttribute("style", "DUID=unique_id;")
            
            elements_diag.appendChild(element)
            i += 1
            
            # Przesuń pozycję dla następnego elementu
            x += 200
            if x > 700:
                x = 100
                y += 150
        
        # Znajdź lub utwórz diagramlinks w diagramie
        diagramlinks = None
        for node in diagram_elem.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.nodeName == "diagramlinks":
                diagramlinks = node
                break
        
        if not diagramlinks:
            diagramlinks = doc.createElement("diagramlinks")
            diagram_elem.appendChild(diagramlinks)
            
        # Dodanie relacji do diagramu (pomijamy na razie dla uproszczenia)
        # TODO: Dodać kod dla rysowania relacji na diagramie

    def _split_attribute(self, attr: str) -> Tuple[str, Optional[str]]:
        """
        Rozdziela nazwę i typ atrybutu.
        
        Args:
            attr: Deklaracja atrybutu
        
        Returns:
            tuple: (nazwa, typ) - nazwa i typ atrybutu
        """
        cleaned = re.sub(r'^[+\-#~]\s*', '', attr)  # Usuń modyfikator dostępu
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
            str: Czysta nazwa metody
        """
        cleaned = re.sub(r'^[+\-#~]\s*', '', method)  # Usuń modyfikator dostępu
        return cleaned.split('(')[0].strip()

    def _get_visibility(self, member: str) -> str:
        """
        Określ widoczność na podstawie prefiksu PlantUML.
        
        Args:
            member: Deklaracja składnika
        
        Returns:
            str: Nazwa widoczności (public, private, protected, package)
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

    def _analizuj_wynikowe_xmi(self, doc):
        """
        Analizuje wygenerowany XMI pod kątem liczby elementów.
        
        Args:
            doc: Dokument XML DOM
        """
        # Liczniki
        classes = len(doc.getElementsByTagName("packagedElement")) # To uproszczenie - trzeba by filtrować po @xmi:type
        interfaces = 0  # Trzeba by przeszukać po atrybutach xmi:type="uml:Interface"
        generalizations = len(doc.getElementsByTagName("generalization"))
        associations = 0  # Trzeba by przeszukać po atrybutach xmi:type="uml:Association"
        dependencies = 0  # Trzeba by przeszukać po atrybutach xmi:type="uml:Dependency"
        
        # Dokładniejsze liczenie klas i interfejsów
        for elem in doc.getElementsByTagName("packagedElement"):
            if elem.getAttribute("xmi:type") == "uml:Class":
                classes += 1
            elif elem.getAttribute("xmi:type") == "uml:Interface":
                interfaces += 1
            elif elem.getAttribute("xmi:type") == "uml:Association":
                associations += 1
            elif elem.getAttribute("xmi:type") == "uml:Dependency":
                dependencies += 1
        
        log_info(f"\nANALIZA WYGENEROWANEGO XMI:")
        log_info(f"- Klasy: {classes}")
        log_info(f"- Interfejsy: {interfaces}")
        log_info(f"- Generalizacje (dziedziczenie): {generalizations}")
        log_info(f"- Asocjacje: {associations}")
        log_info(f"- Zależności: {dependencies}")

    
    def _map_relation_to_connector_id(self, relation):
        """
        Mapuje relację na identyfikator konektora w XMI.
        
        Args:
            relation: Obiekt relacji UML
            
        Returns:
            str: Identyfikator konektora w XMI
        """
        # Dla relacji dziedziczenia, identyfikator to ID generalizacji
        if relation.relation_type == 'inheritance':
            # Tu trzeba przeszukać wszystkie generalizacje w modelu
            return self.id_map.get(f'inheritance_{relation.source}_{relation.target}')
        
        # Dla innych relacji, identyfikator to ID asocjacji
        return self.id_map.get(f'association_{relation.source}_{relation.target}_{relation.label}')


    def _fix_xml_prefixes(self, xml_str):
        """
        Poprawia prefixy XML w wyjściowym dokumencie.
        
        Args:
            xml_str: String XML do poprawienia
            
        Returns:
            str: Poprawiony XML
        """
        # Poprawne prefixy dla głównych elementów
        xml_str = re.sub(r'<XMI ', r'<xmi:XMI ', xml_str)
        xml_str = re.sub(r'</XMI>', r'</xmi:XMI>', xml_str)
        xml_str = re.sub(r'<Documentation ', r'<xmi:Documentation ', xml_str)
        xml_str = re.sub(r'</Documentation>', r'</xmi:Documentation>', xml_str)
        xml_str = re.sub(r'<Model ', r'<uml:Model ', xml_str)
        xml_str = re.sub(r'</Model>', r'</uml:Model>', xml_str)
        xml_str = re.sub(r'<Extension ', r'<xmi:Extension ', xml_str)
        xml_str = re.sub(r'</Extension>', r'</xmi:Extension>', xml_str)
    
        return xml_str
    
    def _add_association(self, doc, package_element, relation: UMLRelation, source_id: str, target_id: str):
        """
        Dodaje relację asocjacji, agregacji lub kompozycji.
        
        Args:
            doc: Dokument XML DOM
            package_element: Element pakietu
            relation: Obiekt relacji UML
            source_id: ID klasy źródłowej
            target_id: ID klasy docelowej
        
        Returns:
            tuple: (Element relacji, ID relacji)
        """
        # Generowanie ID asocjacji
        association_id = self._generate_uuid('EAID_')
        source_end_id = self._generate_uuid('EAID_src')  # Prefiks dla źródła
        target_end_id = self._generate_uuid('EAID_dst') 
        
        # Tworzenie elementu asocjacji
        assoc_elem = doc.createElement("packagedElement")
        assoc_elem.setAttribute("xmi:type", "uml:Association")
        assoc_elem.setAttribute("xmi:id", association_id)
        if relation.label:
            assoc_elem.setAttribute("name", relation.label)
        
        package_element.appendChild(assoc_elem)
        
        # Utworzenie końców asocjacji
        source_end_id = self._generate_uuid()
        target_end_id = self._generate_uuid()
        
        # Koniec źródłowy
        source_end = doc.createElement("ownedEnd")
        source_end.setAttribute("xmi:id", source_end_id)
        type_elem = doc.createElement("type")
        type_elem.setAttribute("xmi:idref", source_id)
        source_end.appendChild(type_elem)
        source_end.setAttribute("association", association_id)
        
        # Dodaj krotność dla źródła
        source_lower, source_upper = "1", "1"  # domyślnie 1
        if relation.source_multiplicity:
            source_lower, source_upper = PlantUMLClassParser.parse_multiplicity(relation.source_multiplicity)
        self._add_multiplicity(doc, source_end, source_lower, source_upper)
        
        assoc_elem.appendChild(source_end)
        
        # Koniec docelowy
        target_end = doc.createElement("ownedEnd")
        target_end.setAttribute("xmi:id", target_end_id)
        # Zamiast type="ID" używamy elementu <type>
        type_elem = doc.createElement("type")
        type_elem.setAttribute("xmi:idref", target_id)
        target_end.appendChild(type_elem)
        target_end.setAttribute("association", association_id)

        
        # Określ typ agregacji dla odpowiednich relacji
        if relation.relation_type == 'composition':
            target_end.setAttribute("aggregation", "composite")
        elif relation.relation_type == 'aggregation':
            target_end.setAttribute("aggregation", "shared")
            
        # Dodaj krotność dla celu
        target_lower, target_upper = "1", "1"  # domyślnie 1
        if relation.target_multiplicity:
            target_lower, target_upper = PlantUMLClassParser.parse_multiplicity(relation.target_multiplicity)
        self._add_multiplicity(doc, target_end, target_lower, target_upper)
            
        assoc_elem.appendChild(target_end)
        
        # Dodaj oba końce do memberEnd
        assoc_elem.setAttribute("memberEnd", f"{source_end_id} {target_end_id}")
        
        # Zapisz ID asocjacji w mapie ID - kluczowe dla konektorów w diagramie!
        key = f'association_{relation.source}_{relation.target}'
        if relation.label:
            key += f'_{relation.label}'
        self.id_map[key] = association_id
        
        return assoc_elem, association_id

    def add_diagram_connectors(self, doc, extension_element, relations):
        """
        Dodaje konektory do diagramu w rozszerzeniu EA.
        
        Args:
            doc: Dokument XML DOM
            extension_element: Element rozszerzenia EA
            relations: Lista relacji UML
        """
        # Znajdź sekcję connectors w rozszerzeniu
        connectors_elem = None
        for node in extension_element.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.nodeName == "connectors":
                connectors_elem = node
                break
        
        if not connectors_elem:
            log_warning("WARN: Nie znaleziono sekcji connectors w rozszerzeniu")
            connectors_elem = doc.createElement("connectors")
            extension_element.appendChild(connectors_elem)
        
        # Dodaj konektory dla każdej relacji
        for relation in relations:
            # Unikalne ID dla każdej relacji
            relation_key = f'{relation.source}_{relation.target}_{relation.relation_type}'
            if relation.label:
                relation_key += f'_{relation.label}'
            
            # Pobierz ID źródła i celu
            source_id = self.id_map.get(f"class_{relation.source}") or self.id_map.get(f"enum_{relation.source}")
            target_id = self.id_map.get(f"class_{relation.target}") or self.id_map.get(f"enum_{relation.target}")
            
            if not source_id or not target_id:
                log_warning(f"WARN: Nie znaleziono ID dla {relation.source} lub {relation.target}, pomijam relację")
                continue
                
            # Znajdź ID konektora w zależności od typu relacji
            connector_id = None
            if relation.relation_type == 'inheritance':
                # Dla dziedziczenia znajdź ID generalizacji
                connector_id = self.id_map.get(f'inheritance_{relation.source}_{relation.target}')
            else:
                # Dla innych relacji znajdź ID asocjacji
                assoc_key = f'association_{relation.source}_{relation.target}'
                if relation.label:
                    assoc_key += f'_{relation.label}'
                connector_id = self.id_map.get(assoc_key)
                
            if not connector_id:
                # Jeśli nie znaleziono ID, wygeneruj nowy
                connector_id = self._generate_uuid()
                log_debug(f"DEBUG: Wygenerowano nowe ID konektora: {connector_id}")
                
            # Utwórz element konektora
            connector = doc.createElement("connector")
            connector.setAttribute("xmi:idref", connector_id)
            connectors_elem.appendChild(connector)
                
            # Źródło konektora
            source = doc.createElement("source")
            source.setAttribute("xmi:idref", source_id)
            connector.appendChild(source)
            
            # Model źródła
            source_model = doc.createElement("model")
            source_model.setAttribute("ea_localid", str(hash(relation.source) % 10000))
            source_model.setAttribute("type", "Class")
            source_model.setAttribute("name", relation.source)
            source.appendChild(source_model)
            
            # Rola źródła
            source_role = doc.createElement("role")
            source_role.setAttribute("visibility", "Public")
            source_role.setAttribute("targetScope", "instance")
            source.appendChild(source_role)
            
            # Typ źródła
            source_type = doc.createElement("type")
            if relation.source_multiplicity:
                source_type.setAttribute("multiplicity", relation.source_multiplicity)
            source_type.setAttribute("aggregation", "none")
            source_type.setAttribute("containment", "Unspecified")
            source.appendChild(source_type)
            
            # Cel konektora
            target = doc.createElement("target")
            target.setAttribute("xmi:idref", target_id)
            connector.appendChild(target)
            
            # Model celu
            target_model = doc.createElement("model")
            target_model.setAttribute("ea_localid", str(hash(relation.target) % 10000))
            target_model.setAttribute("type", "Class") 
            target_model.setAttribute("name", relation.target)
            target.appendChild(target_model)
            
            # Rola celu
            target_role = doc.createElement("role")
            target_role.setAttribute("visibility", "Public")
            target_role.setAttribute("targetScope", "instance")
            target.appendChild(target_role)
            
            # Typ celu
            target_type = doc.createElement("type")
            if relation.target_multiplicity:
                target_type.setAttribute("multiplicity", relation.target_multiplicity)
            target_type.setAttribute("aggregation", "none") 
            target_type.setAttribute("containment", "Unspecified")
            target.appendChild(target_type)
            
            # Model konektora
            model = doc.createElement("model")
            model.setAttribute("ea_localid", str(abs(hash(relation.source + relation.target)) % 10000))
            connector.appendChild(model)
            
            # Właściwości konektora
            properties = doc.createElement("properties")
            properties.setAttribute("ea_type", self._get_connector_type(relation.relation_type))
            if relation.label:
                properties.setAttribute("name", relation.label)
            # Krotnośći jako atrybuty
            if relation.source_multiplicity:
                properties.setAttribute("sourcecard", relation.source_multiplicity)
            if relation.target_multiplicity:
                properties.setAttribute("targetcard", relation.target_multiplicity)
            properties.setAttribute("direction", "Source -> Destination")
            connector.appendChild(properties)
            
            # Modyfikatory
            modifiers = doc.createElement("modifiers")
            modifiers.setAttribute("isRoot", "false")
            modifiers.setAttribute("isLeaf", "false")
            connector.appendChild(modifiers)
            
            # Dokumentacja
            documentation = doc.createElement("documentation")
            connector.appendChild(documentation)
            
            # Wygląd
            appearance = doc.createElement("appearance")
            appearance.setAttribute("linemode", "3")
            appearance.setAttribute("linecolor", "-1")
            appearance.setAttribute("linewidth", "0")
            appearance.setAttribute("seqno", "0")
            appearance.setAttribute("headStyle", "0")
            appearance.setAttribute("lineStyle", "0")
            connector.appendChild(appearance)
            
            # Style konektora
            style = doc.createElement("style")
            if relation.relation_type == "inheritance":
                style.setAttribute("value", "Mode=3;EOID=5123C2D9;SOID=DCE:FB48;Color=-1;LWidth=0;TREE=OS;") 
            elif relation.relation_type == "aggregation":
                style.setAttribute("value", "Mode=3;EOID=5123C2D9;SOID=DCE:FB48;Color=-1;LWidth=0;TREE=OA;")
            elif relation.relation_type == "composition":
                style.setAttribute("value", "Mode=3;EOID=5123C2D9;SOID=DCE:FB48;Color=-1;LWidth=0;TREE=OC;")
            else:
                style.setAttribute("value", "Mode=3;EOID=5123C2D9;SOID=DCE:FB48;Color=-1;LWidth=0;")
            connector.appendChild(style)
            
            # Etykiety - kluczowe dla krotnośći!
            labels = doc.createElement("labels")
            
            # Nazwa relacji (środek)
            if relation.label:
                mt = doc.createElement("mt")
                mt.setAttribute("value", relation.label)
                labels.appendChild(mt)
            
            # Krotność źródła (początek)
            if relation.source_multiplicity:
                lb = doc.createElement("lb")
                lb.setAttribute("value", relation.source_multiplicity)
                labels.appendChild(lb)
            
            # Krotność celu (koniec)
            if relation.target_multiplicity:
                rb = doc.createElement("rb")
                rb.setAttribute("value", relation.target_multiplicity)
                labels.appendChild(rb)
                
            connector.appendChild(labels)
            
            # Dodaj konektory do diagramu
            self._add_connector_to_diagram(doc, connector_id, relation, source_id, target_id)

    def _add_connector_to_diagram(self, doc, connector_id, relation, source_id, target_id):
        """
        Dodaje konektor do diagramu.
        
        Args:
            doc: Dokument XML DOM
            connector_id: ID konektora
            relation: Relacja UML
            source_id: ID elementu źródłowego 
            target_id: ID elementu docelowego
        """
        # Znajdź diagram
        diagram_id = self.id_map.get('diagram')
        if not diagram_id:
            log_warning("WARN: Nie znaleziono ID diagramu")
            return
            
        diagrams = doc.getElementsByTagName("diagram")
        diagram = None
        for diag in diagrams:
            if diag.getAttribute("xmi:id") == diagram_id:
                diagram = diag
                break
        
        if not diagram:
            log_warning("WARN: Nie znaleziono elementu diagramu")
            return
        
        # Znajdź lub utwórz sekcję diagramlinks
        diagramlinks = None
        for node in diagram.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.nodeName == "diagramlinks":
                diagramlinks = node
                break
        
        if not diagramlinks:
            diagramlinks = doc.createElement("diagramlinks")
            diagram.appendChild(diagramlinks)
        
        # Dodaj link diagramu z pełnymi atrybutami jak w starym generatorze
        diagramlink = doc.createElement("diagramlink")
        diagramlink.setAttribute("connectorID", connector_id)
        
        # Kluczowe atrybuty - referencje do elementów źródłowych i docelowych
        diagramlink.setAttribute("start", source_id)
        diagramlink.setAttribute("end", target_id)
        
        # Identyfikator linku
        link_id = f"DCLINK_{uuid.uuid4().hex[:8].upper()}"
        diagramlink.setAttribute("linkID", link_id)
        
        # Dodatkowe atrybuty
        diagramlink.setAttribute("hidden", "0")
        diagramlink.setAttribute("geometry", "EDGE=1;$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path=;")
        
        diagramlinks.appendChild(diagramlink)

    def _get_connector_type(self, relation_type):
        """
        Konwertuje typ relacji UML do typu konektora EA.
        
        Args:
            relation_type: Typ relacji UML
        
        Returns:
            str: Typ konektora EA
        """
        type_map = {
            'inheritance': 'Generalization',
            'realization': 'Realisation',
            'association': 'Association',
            'aggregation': 'Aggregation',
            'composition': 'Composition',
            'dependency': 'Dependency'
        }
        return type_map.get(relation_type, 'Association')


    def generate_xmi(self, classes: Dict[str, UMLClass], relations: List[UMLRelation], 
                    enums: Dict[str, UMLEnum], notes: List[UMLNote], 
                    primitive_types: set = None, diagram_name: str = "DiagramKlas"):
        """
        Generuje pełny XMI na podstawie modelu UML z prawidłową obsługą typów.
        
        Args:
            classes: Słownik klas UML
            relations: Lista relacji UML
            enums: Słownik enumeratorów UML
            notes: Lista notatek UML
            primitive_types: Zbiór typów pierwotnych
            diagram_name: Nazwa diagramu
        
        Returns:
            str: Zawartość pliku XMI jako string
        """
        # Generuj szkielet XMI z typami pierwotnymi w odpowiedniej sekcji
        doc, root, package, extension = self.generate_skeleton(diagram_name, "DiagramKlas")
        
        self._dodaj_typy_pierwotne(doc, None, primitive_types)

        for enum_name, uml_enum in enums.items():
            self.add_enum(doc, package, uml_enum)
        
        # Dodaj klasy
        for class_name, uml_class in classes.items():
            self.add_class(doc, package, uml_class)
        
        # Dodaj wszystkie relacje - scentralizowana obsługa
        relation_ids = self.dodaj_wszystkie_relacje(doc, package, relations, extension)
        
        # Dodaj elementy diagramu
        self.add_diagram_elements(doc, extension, classes, enums, relations)
        
        # Analizuj wynikowe XMI
        self._analizuj_wynikowe_xmi(doc)
        
        # Używamy metody do poprawy prefixów XML
        xml_str = doc.toprettyxml(indent="  ", encoding="UTF-8").decode('utf-8')
        xml_str = self._fix_xml_prefixes(xml_str)
        
        return xml_str
    
    def _dodaj_typy_pierwotne(self, doc, model_element, primitive_types=None):
        """
        Dodaje definicje typów pierwotnych do sekcji primitivetypes w rozszerzeniu EA
        w strukturze zagnieżdżonych pakietów zgodnej z formatem EA.
        
        Args:
            doc: Dokument XML DOM
            model_element: Element modelu UML
            primitive_types: Lista typów pierwotnych do dodania (opcjonalnie)
        
        Returns:
            dict: Słownik z ID typów pierwotnych
        """
        # Jeśli nie podano listy typów, użyj domyślnych
        if not primitive_types:
            primitive_types = [
                'string', 'int', 'double', 'boolean', 'float', 'long', 
                'char', 'byte', 'Date', 'Time', 'DateTime'
            ]
        
        # Słownik typów pierwotnych z ich ID
        type_ids = {}
        for type_name in primitive_types:
            type_ids[type_name] = f"EAJava_{type_name}"
        
        # Zapisz ID typów w mapie
        for type_name, type_id in type_ids.items():
            self.id_map[f'type_{type_name}'] = type_id
        
        # Znajdź sekcję primitivetypes w rozszerzeniu
        extension = None
        for node in doc.getElementsByTagName("Extension"):
            extension = node
            break
        
        if not extension:
            log_warning("WARN: Nie znaleziono sekcji Extension")
            return type_ids
        
        # Znajdź lub utwórz sekcję primitivetypes
        primitivetypes_elem = None
        for node in extension.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.nodeName == "primitivetypes":
                primitivetypes_elem = node
                break
        
        if not primitivetypes_elem:
            primitivetypes_elem = doc.createElement("primitivetypes")
            extension.appendChild(primitivetypes_elem)
        
        # Utwórz główny pakiet typów pierwotnych
        prim_types_pkg = doc.createElement("packagedElement")
        prim_types_pkg.setAttribute("xmi:type", "uml:Package")
        prim_types_pkg.setAttribute("xmi:id", "EAPrimitiveTypesPackage")
        prim_types_pkg.setAttribute("name", "EA_PrimitiveTypes_Package")
        prim_types_pkg.setAttribute("visibility", "public")
        primitivetypes_elem.appendChild(prim_types_pkg)
        
        # Utwórz podpakiet typów Java
        java_types_pkg = doc.createElement("packagedElement")
        java_types_pkg.setAttribute("xmi:type", "uml:Package")
        java_types_pkg.setAttribute("xmi:id", "EAJavaTypesPackage")
        java_types_pkg.setAttribute("name", "EA_Java_Types_Package")
        java_types_pkg.setAttribute("visibility", "public")
        prim_types_pkg.appendChild(java_types_pkg)
        
        # Dodaj poszczególne typy pierwotne do podpakietu Java
        for type_name, type_id in type_ids.items():
            prim_type = doc.createElement("packagedElement")
            prim_type.setAttribute("xmi:type", "uml:PrimitiveType")
            prim_type.setAttribute("xmi:id", type_id)
            prim_type.setAttribute("name", type_name)
            prim_type.setAttribute("visibility", "public")
            
            # Dodanie generalizacji dla int
            if type_name == 'int':
                generalization = doc.createElement("generalization")
                generalization.setAttribute("xmi:type", "uml:Generalization")
                generalization.setAttribute("xmi:id", f"{type_id}_General")
                
                general = doc.createElement("general")
                general.setAttribute("href", "http://schema.omg.org/spec/UML/2.1/uml.xml#Integer")
                generalization.appendChild(general)
                prim_type.appendChild(generalization)
                
            java_types_pkg.appendChild(prim_type)
        
        return type_ids

    def save_xmi(self, classes, relations, enums, notes, primitive_types=None, diagram_name="Classes"):
        """
        Generuje i zapisuje plik XMI.
        
        Args:
            classes: Klasy UML
            relations: Relacje UML
            enums: Enumeratory UML
            notes: Notatki UML
            primitive_types: Zbiór typów pierwotnych
            diagram_name: Nazwa diagramu
        
        Returns:
            xmi_content: Zawartość pliku XMI jako string
        """
        xmi_content = self.generate_xmi(classes, relations, enums, notes, primitive_types, diagram_name)
    
        return xmi_content
        
if __name__ == "__main__":
    # Przykład użycia
    from plantuml_class_parser import PlantUMLClassParser
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_file = 'diagram_klas_PlantUML.puml'
    output_file = f"diagram_klas_{timestamp}.xmi"
    
    try:
        # Wczytaj plik PlantUML
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        # Parsuj kod PlantUML
        parser = PlantUMLClassParser()
        parser.parse(plantuml_code)
        
        # Generuj XMI z dynamicznie odczytanymi typami pierwotnymi
        generator = XMIClassGenerator()
        xmi_content=generator.save_xmi( parser.classes, parser.relations, parser.enums, 
                          parser.notes, parser.primitive_types, "DiagramKlas")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xmi_content)
            
        log_info(f"Wygenerowano plik XMI: {output_file}")
        
    except FileNotFoundError:
        log_error(f"Nie znaleziono pliku: {input_file}")
        log_error("Utwórz przykładowy plik PlantUML lub zmień nazwę pliku w kodzie.")
    except Exception as e:
        log_error(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()