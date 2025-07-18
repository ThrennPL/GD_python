import xml.etree.ElementTree as ET
import uuid
from datetime import datetime
import xml.dom.minidom
from plantuml_activity_parser import PlantUMLActivityParser

class XMIActivityGenerator:
    """
    Generuje w pełni funkcjonalny diagram aktywności w formacie XMI (dla Enterprise Architect)
    na podstawie danych z parsera PlantUML, obsługując wszystkie kluczowe elementy.
    """

    def __init__(self, author: str = "Default_Author"):
        self.author = author
        self._reset_state()
        self.ns = {
            'uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi': 'http://schema.omg.org/spec/XMI/2.1'
        }
        self._register_namespaces()

    def _reset_state(self):
        """Resetuje stan generatora przed każdym nowym diagramem."""
        self.id_map = {}
        self.transitions = []
        self.diagram_objects = []
        self.swimlane_ids = {}
        self.main_activity_id = None
        self.package_id = None
        self.diagram_id = None

    def _register_namespaces(self):
        ET.register_namespace('xmi', self.ns['xmi'])
        ET.register_namespace('uml', self.ns['uml'])

    def _generate_ea_id(self, prefix: str = "EAID") -> str:
        return f"{prefix}_{str(uuid.uuid4()).upper().replace('-', '_')}"

    # --- METODY GŁÓWNEJ LOGIKI ---

    def generate_activity_diagram(self, diagram_name: str, parsed_data: dict) -> str:
        """
        Główna metoda generująca całą strukturę XMI dla diagramu aktywności.
        """
        self._reset_state()

        root = self._create_document_root()
        model = self._create_uml_model(root)
        package = self._create_diagram_package(model, diagram_name)
        main_activity = self._create_main_activity(package, diagram_name)

        # Krok 1: Utwórz wszystkie tory (swimlanes) jako partycje
        self._create_partitions_from_swimlanes(main_activity, parsed_data['swimlanes'])

        # Krok 2: Przetwarzaj przepływ, tworząc węzły i krawędzie
        self._process_flow(main_activity, parsed_data['flow'])
        
        # Krok 3: Stwórz rozszerzenia specyficzne dla Enterprise Architect
        self._create_ea_extensions(root, diagram_name)
        
        # Krok 4: Zwróć sformatowany XML
        return self._format_xml(root)

    def _process_flow(self, main_activity: ET.Element, flow: list):
        """Przetwarza listę elementów z parsera, tworząc logikę diagramu."""
        previous_node_id = None
        structure_stack = []  # Stos do obsługi zagnieżdżonych struktur (if, fork)

        for item in flow:
            item_type = item.get('type')
            current_node_id = None
            transition_needed = True
            
            # Pobierz ID partycji dla bieżącego elementu
            partition_id = self.swimlane_ids.get(item.get('swimlane'))

            # Mapowanie typów na metody obsługujące
            handlers = {
                'control': self._handle_control,
                'activity': self._handle_activity,
                'decision_start': self._handle_decision_start,
                'decision_else': self._handle_decision_else,
                'decision_end': self._handle_decision_end,
                'fork_start': self._handle_fork_start,
                'fork_end': self._handle_fork_end,
                'fork_again': self._handle_fork_again,
                'note': self._handle_note,
            }

            handler = handlers.get(item_type)
            if handler:
                result = handler(item, main_activity, structure_stack, previous_node_id, partition_id)
                current_node_id = result.get('id')
                previous_node_id = result.get('prev_id', previous_node_id)
                transition_needed = result.get('transition', True)
            
            elif item_type != 'swimlane':
                print(f"ℹ️ Pominięto nieznany element: {item_type}")

            # Tworzenie przejścia, jeśli jest to wymagane
            if transition_needed and previous_node_id and current_node_id:
                guard = self._get_guard_for_transition(structure_stack, item)
                self._add_transition(main_activity, previous_node_id, current_node_id, name=guard)
            
            if current_node_id:
                previous_node_id = current_node_id

    # --- METODY OBSŁUGUJĄCE ELEMENTY PRZEPŁYWU ---

    def _handle_control(self, item, parent, stack, prev_id, partition):
        action = item['action']
        node_type_map = {'start': 'uml:InitialNode', 'stop': 'uml:ActivityFinalNode', 'end': 'uml:ActivityFinalNode'}
        name_map = {'start': 'Initial', 'stop': 'Final', 'end': 'Final'}
        node_id = self._add_node(parent, node_type_map[action], name_map[action], partition)
        return {'id': node_id}

    def _handle_activity(self, item, parent, stack, prev_id, partition):
        node_id = self._add_node(parent, 'uml:OpaqueAction', item['text'], partition)
        return {'id': node_id}

    def _handle_decision_start(self, item, parent, stack, prev_id, partition):
        node_id = self._add_node(parent, 'uml:DecisionNode', item.get('condition', 'Decision'), partition)
        stack.append({'type': 'decision', 'id': node_id, 'branch_ends': []})
        return {'id': node_id}

    def _handle_decision_else(self, item, parent, stack, prev_id, partition):
        if stack and stack[-1]['type'] == 'decision':
            stack[-1]['branch_ends'].append(prev_id)
            return {'id': None, 'prev_id': stack[-1]['id'], 'transition': False}
        return {'id': None, 'transition': False}

    def _handle_decision_end(self, item, parent, stack, prev_id, partition):
        if stack and stack[-1]['type'] == 'decision':
            decision_data = stack.pop()
            merge_node_id = self._add_node(parent, 'uml:MergeNode', 'Merge', partition)
            
            # Połącz ostatnią gałąź (else)
            self._add_transition(parent, prev_id, merge_node_id)
            # Połącz wcześniejsze gałęzie (then)
            for branch_end_id in decision_data['branch_ends']:
                self._add_transition(parent, branch_end_id, merge_node_id)
            
            return {'id': merge_node_id, 'transition': False}
        return {'id': None, 'transition': False}

    def _handle_fork_start(self, item, parent, stack, prev_id, partition):
        node_id = self._add_node(parent, 'uml:ForkNode', 'Fork', partition)
        stack.append({'type': 'fork', 'id': node_id, 'branch_ends': []})
        return {'id': node_id}

    def _handle_fork_again(self, item, parent, stack, prev_id, partition):
        if stack and stack[-1]['type'] == 'fork':
            stack[-1]['branch_ends'].append(prev_id)
            return {'id': None, 'prev_id': stack[-1]['id'], 'transition': False}
        return {'id': None, 'transition': False}

    def _handle_fork_end(self, item, parent, stack, prev_id, partition):
        if stack and stack[-1]['type'] == 'fork':
            fork_data = stack.pop()
            join_node_id = self._add_node(parent, 'uml:JoinNode', 'Join', partition)

            self._add_transition(parent, prev_id, join_node_id)
            for branch_end_id in fork_data['branch_ends']:
                self._add_transition(parent, branch_end_id, join_node_id)

            return {'id': join_node_id, 'transition': False}
        return {'id': None, 'transition': False}

    def _handle_note(self, item, parent, stack, prev_id, partition):
        note_id = self._add_node(parent, 'uml:Comment', item['text'], None)
        if prev_id:
            # Połącz notatkę z ostatnim elementem
            ET.SubElement(self.id_map[note_id], 'annotatedElement', {'xmi:idref': prev_id})
        return {'id': None, 'transition': False} # Notatka nie wpływa na przepływ

    # --- METODY POMOCNICZE TWORZENIA ELEMENTÓW ---

    def _add_node(self, parent_activity: ET.Element, node_type: str, name: str, partition_id: str) -> str:
        """Dodaje węzeł (aktywność, decyzję, etc.) do modelu i przygotowuje jego reprezentację."""
        node_id = self._generate_ea_id("EAID")
        attrs = {'xmi:type': node_type, 'xmi:id': node_id, 'name': name}
        if partition_id:
            attrs['inPartition'] = partition_id
        
        node = ET.SubElement(parent_activity, 'node', attrs)
        self.id_map[node_id] = node  # Przechowaj referencję do elementu
        self.diagram_objects.append({'id': node_id})
        print(f"✔ Dodano węzeł: {name} (Typ: {node_type})")
        return node_id
    
    def _add_transition(self, parent_activity: ET.Element, source_id: str, target_id: str, name: str = ""):
        """Dodaje przejście (ControlFlow) między dwoma węzłami."""
        if not source_id or not target_id: return

        transition_id = self._generate_ea_id("EAID")
        attrs = {'xmi:type': 'uml:ControlFlow', 'xmi:id': transition_id, 'source': source_id, 'target': target_id}
        if name:
            attrs['name'] = name
            # Dodaj warunek 'guard' do przejścia
            guard = ET.SubElement(parent_activity, 'ownedRule', {'xmi:id': self._generate_ea_id("EAID")})
            ET.SubElement(guard, 'specification', {'xmi:type': 'uml:LiteralString', 'value': name, 'xmi:id': self._generate_ea_id("EAID")})
            attrs['guard'] = guard.attrib['xmi:id']

        ET.SubElement(parent_activity, 'edge', attrs)
        self.transitions.append({'id': transition_id, 'source_id': source_id, 'target_id': target_id, 'name': name})
        print(f"  ↳ Dodano przejście: z {source_id[-4:]} do {target_id[-4:]} [etykieta: '{name}']")

    def _get_guard_for_transition(self, stack, item) -> str:
        """Pobiera etykietę (guard) dla przejścia z węzła decyzyjnego."""
        if stack and stack[-1]['type'] == 'decision':
            # Sprawdź, czy jesteśmy w gałęzi 'else'
            if len(stack[-1]['branch_ends']) > 0:
                return item.get('else_label', 'no')
            else: # Jesteśmy w gałęzi 'then'
                return item.get('then_label', 'yes')
        return ""

    def _create_partitions_from_swimlanes(self, parent_activity: ET.Element, swimlanes: dict):
        """Tworzy elementy uml:ActivityPartition na podstawie torów."""
        for name in swimlanes.keys():
            partition_id = self._generate_ea_id("EAID")
            self.swimlane_ids[name] = partition_id
            ET.SubElement(parent_activity, 'group', {
                'xmi:type': 'uml:ActivityPartition', 'xmi:id': partition_id, 'name': name
            })
            self.diagram_objects.append({'id': partition_id}) # Dodaj do wizualizacji
            print(f"🏊 Utworzono tor (partition): {name}")

    # --- METODY BUDOWANIA SZKIELETU XMI (w większości bez zmian) ---

    def _create_document_root(self) -> ET.Element:
        root = ET.Element(ET.QName(self.ns['xmi'], 'XMI'), {'xmi:version': '2.1'})
        ET.SubElement(root, ET.QName(self.ns['xmi'], 'Documentation'), {
            'exporter': 'Enterprise Architect', 'exporterVersion': '6.5', 'exporterID': '1560'
        })
        return root

    def _create_uml_model(self, root: ET.Element) -> ET.Element:
        return ET.SubElement(root, ET.QName(self.ns['uml'], 'Model'), {
            'xmi:type': 'uml:Model', 'name': 'EA_Model', 'visibility': 'public'
        })

    def _create_diagram_package(self, model: ET.Element, diagram_name: str) -> ET.Element:
        self.package_id = self._generate_ea_id("EAPK")
        return ET.SubElement(model, 'packagedElement', {
            'xmi:type': 'uml:Package', 'xmi:id': self.package_id, 'name': diagram_name, 'visibility': 'public'
        })

    def _create_main_activity(self, package: ET.Element, diagram_name: str) -> ET.Element:
        self.main_activity_id = self._generate_ea_id("EAID")
        return ET.SubElement(package, 'packagedElement', {
            'xmi:type': 'uml:Activity', 'xmi:id': self.main_activity_id, 'name': diagram_name
        })

    def _create_ea_extensions(self, root: ET.Element, diagram_name: str):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        extension = ET.SubElement(root, ET.QName(self.ns['xmi'], 'Extension'), {
            'extender': 'Enterprise Architect', 'extenderID': '6.5'
        })

        # Dodaj element dla pakietu (zabezpieczenie)
        packages = ET.SubElement(extension, 'packages')
        package = ET.SubElement(packages, 'package', {'xmi:idref': self.package_id})
        ET.SubElement(package, 'visibility', {'value': 'public'})
        
        self._create_elements_section(extension, diagram_name, current_time)
        self._create_connectors_section(extension)
        self._create_diagrams_section(extension, diagram_name, current_time)

    def _create_elements_section(self, extension: ET.Element, diagram_name: str, current_time: str):
        elements = ET.SubElement(extension, 'elements')
        # Dodaj wszystkie utworzone elementy (węzły, partycje)
        element = ET.SubElement(elements, 'element', {
            'xmi:idref': self.package_id,
            'xmi:type': 'uml:Package',
            'name': diagram_name,
            'scope': 'public'
        })
        for obj_id in self.diagram_objects:
            ET.SubElement(elements, 'element', {'xmi:idref': obj_id['id']})

    def _create_connectors_section(self, extension: ET.Element):
        connectors = ET.SubElement(extension, 'connectors')
        for i, tran in enumerate(self.transitions):
            connector = ET.SubElement(connectors, 'connector', {'xmi:idref': tran['id']})
            ET.SubElement(connector, 'source', {'xmi:idref': tran['source_id']})
            ET.SubElement(connector, 'target', {'xmi:idref': tran['target_id']})
            ET.SubElement(connector, 'labels', {'pt': f"llabel={tran['name']};"})
            ET.SubElement(connector, 'properties', {'ea_type': 'ControlFlow', 'direction': 'Source -> Destination'})
            ET.SubElement(connector, 'appearance', {'seqno': str(i)})

    def _create_diagrams_section(self, extension: ET.Element, diagram_name: str, current_time: str):
        self.diagram_id = self._generate_ea_id("EAID")
        diagrams = ET.SubElement(extension, 'diagrams')
        diagram = ET.SubElement(diagrams, 'diagram', {'xmi:id': self.diagram_id})
        
        # Poprawne powiązanie diagramu z pakietem i activity
        ET.SubElement(diagram, 'model', {
            'package': self.package_id, 
            'localID': '1',  # Dodany atrybut localID
            'owner': self.package_id,
            'tpos': '0'      # Dodany atrybut tpos
        })
        
        # Dodatkowo możesz potrzebować element 'style'
        ET.SubElement(diagram, 'style', {
            'value': 'ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;'
        })
        
        ET.SubElement(diagram, 'properties', {
            'name': diagram_name, 
            'type': 'Activity',
            'documentation': ''  # Dodaj pusty atrybut documentation
        })
        
        ET.SubElement(diagram, 'project', {
            'author': self.author, 
            'version': '1.0',    # Dodaj wersję
            'created': current_time, 
            'modified': current_time
        })
        
        elements = ET.SubElement(diagram, 'elements')
        # Prosty algorytm pozycjonowania
        x, y, seqno = 100, 100, 0
        for obj in self.diagram_objects:
            is_partition = obj['id'] in self.swimlane_ids.values()
            width = 500 if is_partition else 120
            height = 800 if is_partition else 50
            
            ET.SubElement(elements, 'element', {
                'subject': obj['id'], 'seqno': str(seqno),
                'geometry': f"Left={x};Top={y};Right={x+width};Bottom={y+height};"
            })
            if is_partition: x += width + 20 # Nowa kolumna dla nowego toru
            else: y += 100 # Przesuń w dół dla następnego elementu w tym samym torze
            seqno += 1

    def _format_xml(self, root: ET.Element) -> str:
        """Poprawia nagłówek i formatuje XML do czytelnej postaci."""
        xml_string = ET.tostring(root, encoding='unicode', method='xml', xml_declaration=True)
        xml_string_fixed = xml_string.replace("<?xml version='1.0' encoding='unicode'?>", '<?xml version="1.0" encoding="UTF-8"?>')
        dom = xml.dom.minidom.parseString(xml_string_fixed)
        return dom.toprettyxml(indent="  ")

# --- Przykład użycia ---
if __name__ == '__main__':
    generator = XMIActivityGenerator(author="195841_AI")
    
    input_puml_file = 'diagram_aktywnosci_PlantUML.puml'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"pelny_diagram_aktywnosci_{timestamp}.xmi"
    diagram_name = f"Pełny diagram aktywności {timestamp}"

    # Przykładowy, złożony kod PlantUML do testów
    plantuml_example_code = """
    @startuml
    title Proces weryfikacji tożsamości
    
    |Klient|
    start
    :Rozpocznij proces;
    
    |System|
    :Poproś o dane;
    
    |Klient|
    :Wprowadź dane logowania;
    note right: Użytkownik wpisuje login i hasło.
    
    |System|
    if (Dane poprawne?) then (tak)
      :Zaloguj użytkownika;
      if (Wymagana weryfikacja 2FA?) then (tak)
        :Wyślij kod 2FA;
        |Klient|
        :Wprowadź kod 2FA;
      endif
      |System|
      fork
        :Zapisz logowanie w historii;
      fork again
        :Przekieruj na stronę główną;
      end fork
    else (nie)
      :Wyświetl błąd logowania;
    endif
    
    |Klient|
    stop
    
    @enduml
    """
    
    try:
        with open(input_puml_file, 'w', encoding='utf-8') as f:
            f.write(plantuml_example_code)
        
        with open(input_puml_file, 'r', encoding='utf-8') as f:
            parser = PlantUMLActivityParser(f.read())
            parsed_data = parser.parse()

        print("--- Rozpoczęto generowanie XMI ---")
        xml_content = generator.generate_activity_diagram(diagram_name, parsed_data)

        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"\n--- Zakończono ---")
        print(f"🎉 Plik '{output_filename}' został pomyślnie wygenerowany.")

    except Exception as e:
        print(f"❌ Wystąpił krytyczny błąd: {e}")
        import traceback
        traceback.print_exc()