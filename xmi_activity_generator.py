import xml.etree.ElementTree as ET
import uuid
from datetime import datetime
import xml.dom.minidom
from plantuml_activity_parser import PlantUMLActivityParser
import re 

class LayoutManager:
    """Klasa zarządzająca layoutem elementów diagramu."""
    
    def __init__(self, swimlane_ids, transitions=None, id_map=None):
        self.positions = {}
        self.current_y = {}
        self.swimlanes_geometry = {}
        self.swimlane_ids = swimlane_ids
        self.id_map = id_map or {}
        self.transitions = transitions or []
        
        # Inicjalizuj wysokości dla każdego toru
        lane_x = 100  # Początkowa pozycja X pierwszego toru
        lane_width = 250  # Szerokość każdego toru
        
        # Dynamiczne rozłożenie torów w zależności od ich liczby
        total_lanes = len(swimlane_ids)
        for i, (name, swimlane_id) in enumerate(swimlane_ids.items()):
            # Inicjalizuj początkową wysokość dla toru
            self.current_y[swimlane_id] = 180
            
            # Utwórz podstawową geometrię dla toru
            self.swimlanes_geometry[swimlane_id] = {
                'x': lane_x,
                'y': 100,
                'width': lane_width,
                'height': 1050,  # Standardowa wysokość
                'center_x': lane_x + lane_width / 2,
                'index': i,      # Zapamiętaj indeks toru (kolejność)
                'name': name     # Zapamiętaj nazwę toru
            }
            
            # Przesuń pozycję X dla następnego toru
            lane_x += lane_width + 30  # 30px to margines między torami
            
            print(f"📊 Inicjalizacja toru {name}: x={self.swimlanes_geometry[swimlane_id]['x']}, center={self.swimlanes_geometry[swimlane_id]['center_x']}")
    
    def get_position_for_element(self, node):
        """Zwraca pozycję (geometrię) dla danego elementu z uwzględnieniem struktury diagramu."""
        node_id = node.attrib.get('xmi:id')
        
        # Sprawdź, czy już mamy zapisaną pozycję
        if node_id in self.positions:
            return self.positions[node_id]
        
        # Określ, do którego toru należy element
        partition_id = node.attrib.get('inPartition')
        
        # Pobierz rozmiary elementu
        width, height = self._get_element_size(node)
        
        # Sprawdź typ elementu dla specjalnego pozycjonowania
        node_type = node.attrib.get('xmi:type', '')
        node_name = node.attrib.get('name', '')
        is_decision = 'DecisionNode' in node_type
        is_control = 'InitialNode' in node_type or 'ActivityFinalNode' in node_type
        
        # Domyślne wartości pozycji
        left = 200 - (width / 2)  # Środek standardowego toru
        top = 180  # Domyślna wysokość startowa
        
        # Ustal pozycję bazującą na strukturze diagramu
        if partition_id in self.swimlanes_geometry:
            swimlane = self.swimlanes_geometry[partition_id]
            lane_center = swimlane['center_x']
            lane_left = swimlane['x']
            lane_width = swimlane['width']
            
            # Wyśrodkuj element w torze
            left = lane_center - (width / 2)
            
            branch_path = self._determine_branch_path(node_id)
            
            # Analiza informacji o gałęzi
            branch_info = {}
            if branch_path:
                parts = branch_path.split('_')
                if len(parts) >= 3:
                    decision_id = parts[1]
                    branch_type = parts[2]
                    branch_info = {
                        'branch_path': branch_path,
                        'branch_type': branch_type,
                        'parent_decision': decision_id,
                        'depth': self._get_decision_depth(node_id)
                    }
                    
                    # Sprawdź pozycję Y węzła decyzyjnego (rodzica)
                    parent_id = "branch_" + decision_id
                    if parent_id in self.id_map:
                        # Wyekstraktuj wartość Top z zapisanej pozycji
                        match = re.search(r'Top=(\d+\.?\d*);', self.positions.get(parent_id, ''))
                        if match:
                            branch_info['parent_y'] = float(match.group(1))
            
            # Ustal pozycję Y i przesunięcie X w zależności od rodzaju elementu
            if is_control:
                if 'InitialNode' in node_type:
                    # Węzeł początkowy zawsze na górze diagramu
                    top = swimlane['y'] + 80
                    self.current_y[partition_id] = top + height + 50
                elif 'ActivityFinalNode' in node_type:
                    # Znajdź wszystkie istniejące węzły końcowe
                    finals_count = sum(1 for n in self.positions 
                                    if n in self.id_map and 
                                    'ActivityFinalNode' in self.id_map[n].attrib.get('xmi:type', ''))
                    # Umieść każdy nowy węzeł końcowy poniżej poprzednich
                    top = swimlane['y'] + 180 + (finals_count * 60)
                    
            elif is_decision:
                # Węzły decyzyjne potrzebują więcej miejsca
                decision_depth = branch_info.get('depth', 0) or self._get_decision_depth(node_id)
                
                # Przesunięcie w poziomie zależne od głębokości decyzji
                horizontal_offset = min(50 * decision_depth, (lane_width - width) / 2 - 20)
                left += horizontal_offset
                
                # Określ pozycję pionową na podstawie poprzednich elementów w hierarchii
                if branch_info.get('parent_y') is not None:
                    # Umieść decyzję pod jej rodzicem (poprzednim elementem)
                    top = branch_info['parent_y'] + 120
                else:
                    top = self.current_y.get(partition_id, 180) + 60
                
                # Zapisz informacje o tej decyzji do wykorzystania przez jej gałęzie
                decision_key = f"decision_{node_id[-6:]}"
                self.current_y[decision_key] = top
                
                # Oddzielne wysokości dla gałęzi "tak" i "nie"
                self.current_y[f"{decision_key}_yes"] = top + height + 50
                self.current_y[f"{decision_key}_no"] = top + height + 50
                
                # Rozdziel przestrzeń dla gałęzi
                self._register_branch_space(node_id, left, top)
                
                # Aktualizuj ogólną wysokość toru tylko jeśli potrzeba
                self.current_y[partition_id] = max(self.current_y[partition_id], top + height + 150)
                
            else:
                # Dla standardowych elementów (actions)
                if branch_path:
                    # Element jest częścią gałęzi decyzyjnej
                    branch_type = branch_info.get('branch_type', 'default')
                    parent_decision = branch_info.get('parent_decision')
                    
                    if parent_decision:
                        # Pobierz bazową pozycję decyzji
                        decision_key = f"decision_{parent_decision}"
                        base_top = self.current_y.get(f"{decision_key}_{branch_type}", 
                                                    self.current_y.get(partition_id, 180))
                        
                        # Pozycja Y zależna od gałęzi
                        top = base_top + 70
                        
                        # Pozycja X zależna od typu gałęzi (tak/nie)
                        if branch_type == 'yes':
                            # Gałąź "tak" - przesuń w lewo
                            left -= 50
                        else:  # branch_type == 'no'
                            # Gałąź "nie" - przesuń w prawo
                            left += 50
                        
                        # Aktualizuj wysokość dla tej konkretnej gałęzi
                        self.current_y[f"{decision_key}_{branch_type}"] = top + height + 20
                    else:
                        # Standardowy element bez powiązania z decyzją
                        top = self.current_y.get(partition_id, 180) + 70
                        self.current_y[partition_id] = top + height + 20
                else:
                    # Element nie jest w żadnej gałęzi - standardowe pozycjonowanie
                    top = self.current_y.get(partition_id, 180) + 70
                    self.current_y[partition_id] = top + height + 20
            
            # Zapewnij, że element nie wychodzi poza granice toru
            if left < lane_left + 10:
                left = lane_left + 10
            if left + width > lane_left + lane_width - 10:
                left = lane_left + lane_width - width - 10
            
            # Znajdź nazwę toru dla komunikatu debugowania
            swimlane_name = "Nieznany"
            for name, pid in self.swimlane_ids.items():
                if pid == partition_id:
                    swimlane_name = name
                    break
                    
            # Logowanie informacji o aktualizacji wysokości
            print(f"   📏 Aktualizacja wysokości dla {swimlane_name}: {top} -> {self.current_y[partition_id]}")
        
        # Oblicz pozostałe współrzędne
        right = left + width
        bottom = top + height
        
        # Utwórz string z pozycją
        position = f"Left={left};Top={top};Right={right};Bottom={bottom};"
        
        # Zapisz pozycję do cache
        self.positions[node_id] = position
        
        # Debugowanie
        position_before = "Brak pozycji"
        self._debug_position_calculation(node_id, partition_id, position_before, position)
        
        return position


    def _register_branch_space(self, decision_id, x_pos, y_pos):
        """Rejestruje przestrzeń dla gałęzi decyzyjnych."""
        if not hasattr(self, 'branch_spaces'):
            self.branch_spaces = {}
        
        # Zapisz informacje o położeniu tej decyzji
        self.branch_spaces[decision_id] = {
            'x': x_pos,
            'y': y_pos,
            'yes_branch': {
                'x_offset': -50,  # Gałąź "tak" idzie w lewo
                'elements': []
            },
            'no_branch': {
                'x_offset': 50,   # Gałąź "nie" idzie w prawo
                'elements': []
            }
        }

    def _determine_branch_path(self, node_id):
        """Określa ścieżkę gałęzi dla elementu na podstawie połączeń z pełnym śledzeniem historii."""
        # Znajdź wszystkie połączenia wchodzące do tego węzła
        incoming = [t for t in self.transitions if t.get('target_id') == node_id]
        
        if not incoming:
            return None
        
        # Budujemy pełne drzewo ścieżek wstecz
        paths = []
        visited = set()
        
        def trace_back(curr_id, path=None):
            if path is None:
                path = []
            
            if curr_id in visited:
                return  # Unikaj cykli
            
            visited.add(curr_id)
            path = [curr_id] + path  # Dodaj bieżący węzeł do ścieżki
            
            # Jeśli to element początkowy, zapisz ścieżkę
            incoming = [t for t in self.transitions if t.get('target_id') == curr_id]
            if not incoming:
                paths.append(path)
                return
            
            # Kontynuuj śledzenie wstecz dla wszystkich połączeń przychodzących
            for transition in incoming:
                source_id = transition.get('source_id')
                if source_id:
                    # Dodaj etykietę przejścia do ścieżki
                    trace_back(source_id, path)
        
        # Rozpocznij śledzenie od bieżącego węzła
        trace_back(node_id)
        
        # Analizuj ścieżki do najbliższej decyzji
        for path in paths:
            for i, path_node_id in enumerate(path[1:], 1):  # Pomijamy pierwszy węzeł (to nasz bieżący)
                if path_node_id in self.id_map:
                    node = self.id_map[path_node_id]
                    if node is not None and 'xmi:type' in node.attrib and 'DecisionNode' in node.attrib.get('xmi:type', ''):
                        # Znajdujemy tę decyzję, która jest najbliżej bieżącego węzła
                        prev_id = path[i-1]  # Id węzła poprzedzającego decyzję
                        for trans in self.transitions:
                            if trans.get('source_id') == path_node_id and trans.get('target_id') == prev_id:
                                guard = trans.get('name', '').lower()
                                branch_type = 'yes' if guard == 'tak' else 'no'
                                return f"branch_{path_node_id[-6:]}_{branch_type}"
        
        return None

    def _get_decision_depth(self, node_id):
        """Oblicza głębokość zagnieżdżenia decyzji dla elementu z limitem przesunięcia."""
        depth = 0
        
        # Sprawdź stos decyzji dla bieżącego węzła
        parent_ids = set()
        current_ids = {node_id}
        
        # Iteracyjnie przeszukuj graf wstecz
        while current_ids:
            next_ids = set()
            for nid in current_ids:
                # Znajdź wszystkie węzły, które prowadzą do obecnego węzła
                for trans in self.transitions:
                    if trans.get('target_id') == nid and trans.get('source_id') not in parent_ids:
                        source_id = trans.get('source_id')
                        # Sprawdź, czy to węzeł decyzyjny
                        if source_id in self.id_map:
                            node_type = self.id_map[source_id].attrib.get('xmi:type', '')
                            if 'DecisionNode' in node_type:
                                depth += 1
                        next_ids.add(source_id)
                        parent_ids.add(source_id)
            
            current_ids = next_ids
        
        # Ogranicz maksymalną głębokość, aby uniknąć wyjścia poza tor
        # Zakładamy że 3 poziomy to maksimum w ramach jednego toru
        max_safe_depth = 3
        return min(depth, max_safe_depth)
    
    def _debug_position_calculation(self, node_id, partition_id, position_before, position_after):
        """Loguje informacje o procesie wyliczania pozycji elementu."""
        if not hasattr(self, 'id_map') or not self.id_map or node_id not in self.id_map:
            print(f"\n🔍 Debug pozycjonowania elementu: ID={node_id[-6:]} (brak informacji)")
            return
            
        node_type = self.id_map[node_id].attrib.get('xmi:type', 'unknown')
        node_name = self.id_map[node_id].attrib.get('name', 'unnamed')
        
        # Pobierz nazwę swimlane'a na podstawie partition_id
        swimlane_name = "Nieznany"
        for name, pid in self.swimlane_ids.items():
            if pid == partition_id:
                swimlane_name = name
                break
        
        print(f"\n🔍 Debug pozycjonowania elementu: {node_name} ({node_type})")
        print(f"   ID: {node_id[-6:]} | Partition: {swimlane_name} ({partition_id[-6:] if partition_id else 'None'})")
        print(f"   Przed: {position_before}")
        print(f"   Po:    {position_after}")
        print(f"   Wysokość toru {swimlane_name}: {self.current_y.get(partition_id, 'nie istnieje')}")
        
        # Sprawdź, czy element jest w swoim torze
        if partition_id:
            for name, pid in self.swimlane_ids.items():
                if pid == partition_id:
                    swimlane = self.swimlanes_geometry.get(pid, {})
                    left_edge = swimlane.get('x', 0)
                    right_edge = left_edge + swimlane.get('width', 0)
                    
                    # Sprawdź, czy element wykracza poza tor
                    match = re.search(r'Left=(\d+\.?\d*);Top=(\d+\.?\d*);Right=(\d+\.?\d*);Bottom=(\d+\.?\d*);', position_after)
                    if match:
                        element_left = float(match.group(1))
                        element_right = float(match.group(3))
                        
                        if element_left < left_edge or element_right > right_edge:
                            print(f"   ⚠️ Element wykracza poza swój tor! ({left_edge} - {right_edge})")
        
    def _get_element_size(self, node):
        """Określa rozmiar elementu na podstawie jego typu."""
        node_type = node.attrib.get('xmi:type', '')
        
        # Domyślny rozmiar dla standardowej akcji
        width, height = 120, 60
        
        # Dostosuj rozmiary w zależności od typu
        if 'InitialNode' in node_type or 'ActivityFinalNode' in node_type:
            # Węzły początkowe/końcowe - małe okrągłe symbole
            width, height = 30, 30
        elif 'DecisionNode' in node_type or 'MergeNode' in node_type:
            # Węzły decyzyjne - romby
            width, height = 40, 40
        elif 'ForkNode' in node_type or 'JoinNode' in node_type:
            # Węzły fork/join - małe prostokąty
            width, height = 80, 10
        elif 'Comment' in node_type:
            # Notatki - szerokie, aby zmieścić tekst
            width, height = 140, 60
        elif 'Action' in node_type:
            # Sprawdź, czy akcja ma długą nazwę
            if 'name' in node.attrib:
                name_len = len(node.attrib['name'])
                # Dostosuj szerokość na podstawie długości nazwy
                if name_len > 20:
                    width = min(220, 80 + name_len * 4)
        
        return width, height

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
        self.partitions = {} 
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

        self.diagram_id = self._generate_ea_id("EAID")

        root = self._create_document_root()
        model = self._create_uml_model(root)
        diagram_name = "Diagram aktywności"
        package = self._create_diagram_package(model, diagram_name)
        main_activity = self._create_main_activity(package, diagram_name)

        # Krok 1: Utwórz wszystkie tory (swimlanes) jako partycje
        self._create_partitions_from_swimlanes(main_activity, parsed_data['swimlanes'])

        # Krok 2: Przetwarzaj przepływ, tworząc węzły i krawędzie
        self._process_flow(main_activity, parsed_data['flow'])
        
        # Upewnij się, że typy są spójne w całym dokumencie
        self._ensure_element_type_consistency()

        # Zaktualizuj powiązania między partycjami a elementami
        self._update_partition_elements(main_activity)
        
        # Krok 3: Stwórz rozszerzenia specyficzne dla Enterprise Architect
        self._create_ea_extensions(root, diagram_name)
        
        # Krok 4: Zwróć sformatowany XML
        return self._format_xml(root)

    def _process_flow(self, main_activity: ET.Element, flow: list):
        """Przetwarza listę elementów z parsera, tworząc logikę diagramu."""
        previous_node_id = None
        previous_swimlane = None
        structure_stack = []
        fork_source_id = None

        for i, item in enumerate(flow):
            current_swimlane = item.get('swimlane')
            item_type = item.get('type')
            current_node_id = None
            transition_needed = True
            special_source_id = None  
            
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

            # Logowanie dla debugowania
            print(f"Przetwarzanie elementu {i+1}/{len(flow)}: typ={item_type}, tekst={item.get('text', '')}")

            handler = handlers.get(item_type)
            if handler:
                result = handler(item, main_activity, structure_stack, previous_node_id, partition_id)
                current_node_id = result.get('id')
                
                # Specjalna obsługa dla fork_again - pobierz ID forka jako źródło przejścia
                if item_type == 'fork_again' and 'prev_id' in result:
                    special_source_id = result.get('prev_id')
                    # Zapisz ID forka do użycia dla następnego elementu
                    fork_source_id = special_source_id
                    transition_needed = False  # Sam fork_again nie tworzy przejścia
                    
                # Obsługa elementu po fork_again (musi być połączony z forkiem)
                elif fork_source_id and current_node_id:
                    # Połącz bieżący węzeł z ostatnim forkiem
                    self._add_transition(main_activity, fork_source_id, current_node_id, 
                                        name=item.get('label', ''))
                    fork_source_id = None  # Zresetuj fork_source_id po użyciu
                    transition_needed = False  # Już utworzyliśmy przejście
                
                # Standardowa obsługa dla innych elementów
                else:
                    transition_needed = result.get('transition', True)
            
            elif item_type != 'swimlane':
                print(f"ℹ️ Pominięto nieznany element: {item_type}")

            # Tworzenie przejścia, jeśli jest to wymagane
            if transition_needed and previous_node_id and current_node_id:
                # Sprawdź, czy mamy specjalne źródło dla tego przejścia
                source_id = special_source_id if special_source_id else previous_node_id
                
                # Pobierz ewentualną etykietę przejścia (np. dla decision)
                guard = self._get_guard_for_transition(structure_stack, item)
                
                # Dodaj przejście od źródła do bieżącego węzła
                self._add_transition(main_activity, source_id, current_node_id, name=guard)
                
                # Specjalna obsługa przejść międzytorowych
                if previous_swimlane and current_swimlane and previous_swimlane != current_swimlane:
                    # Oznacz, że to przejście jest między torami (do późniejszego wykorzystania)
                    for trans in self.transitions:
                        if trans['source_id'] == source_id and trans['target_id'] == current_node_id:
                            trans['cross_swimlane'] = True
                            break
            
            # Aktualizuj ID poprzedniego węzła dla następnej iteracji
            if current_node_id:
                previous_node_id = current_node_id
                
            # Aktualizuj poprzedni swimlane
            if current_swimlane:
                previous_swimlane = current_swimlane
            
            # Logowanie dla debugowania stanu
            stack_info = [f"{s['type']}:{s['id'][-6:]}" for s in structure_stack]
            print(f"  - Stan: prev={previous_node_id[-6:] if previous_node_id else 'None'}, "
                f"curr={current_node_id[-6:] if current_node_id else 'None'}, "
                f"fork_src={fork_source_id[-6:] if fork_source_id else 'None'}, "
                f"stos={stack_info}")
                
            #  Po przetworzeniu wszystkich elementów, zrób dodatkowe przejście
            final_nodes = []
            last_node_id = None
                
                # Znajdź wszystkie węzły końcowe i ostatni przetworzony element
            for node_id, node in self.id_map.items():
                if node.attrib.get('xmi:type') == 'uml:ActivityFinalNode':
                    final_nodes.append(node_id)
                    
                    # Przyjmij, że ostatni przetworzony element to ten, z którego powinno
                    # być połączenie do węzła końcowego
                if current_node_id:
                    last_node_id = current_node_id
                
                # Jeśli mamy węzeł końcowy i ostatni element, połącz je
            if final_nodes and last_node_id:
                self._add_transition(main_activity, last_node_id, final_nodes[0])
                print(f"  ↳ Dodano połączenie do węzła końcowego: {last_node_id[-4:]} → {final_nodes[0][-4:]}")

                    # przez wszystkie elementy, aby poprawnie powiązać je z torami
            self._update_partition_elements(main_activity)

    def _debug_find_none_values(self, element, path=""):
        """Funkcja znajdująca wszystkie atrybuty None w drzewie XML."""
        current_path = f"{path}/{element.tag}" if path else element.tag
        
        for key, value in element.attrib.items():
            if value is None:
                print(f"⚠️ Znaleziono atrybut None: {current_path} -> {key}")
        
        for child in element:
            self._debug_find_none_values(child, current_path)

    def _handle_decision_end(self, item, parent, stack, prev_id, partition):
        """Obsługuje zakończenie bloku decyzyjnego."""
        if stack and stack[-1]['type'] == 'decision':
            decision_data = stack.pop()
            
            # Dodaj bieżący węzeł jako koniec gałęzi
            if prev_id:
                decision_data['branch_ends'].append(prev_id)
                
            # Utwórz węzeł merge, jeśli były co najmniej dwie gałęzie
            if len(decision_data['branch_ends']) > 1:
                merge_node_id = self._add_node(parent, 'uml:MergeNode', 'Merge', partition)
                
                # Połącz wszystkie końce gałęzi z węzłem merge
                for branch_end_id in decision_data['branch_ends']:
                    self._add_transition(parent, branch_end_id, merge_node_id)
                
                return {'id': merge_node_id, 'transition': False}
            
            # Jeśli była tylko jedna gałąź, po prostu kontynuuj
            return {'id': prev_id, 'transition': True}
        
        return {'id': prev_id, 'transition': True}

    def _handle_control(self, item, parent, stack, prev_id, partition):
        """Obsługuje węzły kontrolne (start/stop/end)."""
        action = item['action']
        node_type_map = {'start': 'uml:InitialNode', 'stop': 'uml:ActivityFinalNode', 'end': 'uml:ActivityFinalNode'}
        name_map = {'start': 'Initial', 'stop': 'Final', 'end': 'Final'}
        
        node_id = self._add_node(parent, node_type_map[action], name_map[action], partition)
        
        # Dodaj element do listy obiektów diagramu
        self.diagram_objects.append({
            'id': node_id,
            'type': node_type_map[action].replace('uml:', '')  # Usuń prefiks uml:
        })
        
        # Dla węzła końcowego nie tworzymy przejścia wychodzącego
        is_terminal = action in ('stop', 'end')
        
        return {'id': node_id, 'transition': not is_terminal}

    def _debug_diagram_objects(self):
        """Wyświetla informacje o elementach dodanych do diagramu."""
        print(f"\n--- Elementy diagramu ({len(self.diagram_objects)}) ---")
        for obj in self.diagram_objects:
            if isinstance(obj, dict):
                obj_id = obj.get('id', 'brak ID')
                obj_type = obj.get('type', 'nieznany typ')
                print(f" - {obj_type}: {obj_id[-6:]}")
            else:
                print(f" - {obj}")

    def _handle_activity(self, item, parent, stack, prev_id, partition):
        """Obsługuje element 'activity' - tworzy węzeł aktywności."""
        node_id = self._add_node(parent, 'uml:Action', item['text'], partition)
        
        # Dodaj do listy obiektów diagramu
        self.diagram_objects.append({
            'id': node_id,
            'type': 'UML_ActivityNode',
            'name': item['text']
        })
    
        return {'id': node_id}
    
    def _create_node(self, parent: ET.Element, node_type: str, node_name: str = None) -> ET.Element:
        """Tworzy węzeł z odpowiednim typem UML."""
        node_id = self._generate_ea_id("EAID")
        attrs = {'xmi:id': node_id, 'visibility': 'public'}
        
        # Mapowanie typów na prawidłowe typy UML
        type_map = {
            'action': 'uml:Action',
            'decision': 'uml:DecisionNode',
            'merge': 'uml:MergeNode',
            'initial': 'uml:InitialNode',
            'final': 'uml:ActivityFinalNode',
            'fork': 'uml:ForkNode',      # Zmiana z uml:Synchronization
            'join': 'uml:JoinNode'       # Zmiana z uml:Synchronization
        }
        
        if node_name:
            attrs['name'] = node_name
        
        node = ET.SubElement(parent, 'node', {
            'xmi:type': type_map.get(node_type, 'uml:Action'),
            **attrs
        })
        
        self.id_map[node_id] = node
        return node

    def _handle_decision_start(self, item, parent, stack, prev_id, partition):
        """Obsługuje początek bloku decyzyjnego."""
        condition = item.get('condition', 'Decision')
        node_id = self._add_node(parent, 'uml:DecisionNode', condition, partition)
        
        # Dodaj węzeł do stosu struktur z listą branch_ends do późniejszego połączenia w merge
        stack.append({
            'type': 'decision', 
            'id': node_id, 
            'branch_ends': []
        })
        
        # Dodaj element do listy obiektów diagramu - kluczowy krok!
        self.diagram_objects.append({
            'id': node_id,
            'type': 'DecisionNode'  # Usuń prefiks uml:
        })
    
        return {'id': node_id, 'transition': True}

    def _handle_decision_else(self, item, parent, stack, prev_id, partition):
        """Obsługuje gałąź 'else' w bloku decyzyjnym."""
        if stack and stack[-1]['type'] == 'decision':
            decision_data = stack[-1]
            # Zapisz poprzedni węzeł jako koniec poprzedniej gałęzi
            if prev_id:
                decision_data['branch_ends'].append(prev_id)
            
            # Pobierz ID węzła decyzyjnego, aby utworzyć przejście od niego
            decision_id = decision_data['id']
            # Utwórz powiązanie z decyzją - tu powinno być połączenie z gałęzią else
            return {'id': decision_id, 'transition': True, 'label': item.get('else_label', 'nie')}
        
        return {'id': prev_id, 'transition': True}

    def _handle_fork_end(self, item, parent, stack, prev_id, partition):
        """Obsługuje zakończenie bloku fork/join."""
        if stack and stack[-1]['type'] == 'fork':
            fork_data = stack.pop()
            join_node_id = self._add_node(parent, 'uml:JoinNode', 'Join', partition)
            
            # Dodaj do listy obiektów diagramu - ważne!
            self.diagram_objects.append({
                'id': join_node_id,
                'type': 'JoinNode'
            })

            # Dodaj przejście od bieżącego węzła do join
            if prev_id:
                self._add_transition(parent, prev_id, join_node_id)
                
            # Dodaj również wszystkie końce gałęzi do join
            for branch_end_id in fork_data['branch_ends']:
                self._add_transition(parent, branch_end_id, join_node_id)

            return {'id': join_node_id, 'transition': True}
        
        return {'id': prev_id, 'transition': True}

    def _handle_fork_start(self, item, parent, stack, prev_id, partition):
        """Obsługuje początek bloku fork/join."""
        node_id = self._add_node(parent, 'uml:ForkNode', 'Fork', partition)
        
        stack.append({
            'type': 'fork', 
            'id': node_id, 
            'branch_ends': []
        })
        
        # WAŻNE: Dodaj do listy obiektów diagramu
        self.diagram_objects.append({
            'id': node_id,
            'type': 'ForkNode'
        })
        
        if prev_id:
            self._add_transition(parent, prev_id, node_id)
        
        return {'id': node_id, 'transition': False} 

    def _handle_fork_again(self, item, parent, stack, prev_id, partition):
        """Obsługuje element 'fork again' - oznacza kolejną gałąź forka."""
        if stack and stack[-1]['type'] == 'fork':
            fork_id = stack[-1]['id']  # ID węzła fork
            
            # Zapamiętaj poprzedni węzeł jako zakończenie poprzedniej gałęzi
            if prev_id:
                stack[-1]['branch_ends'].append(prev_id)
            
            # Nie tworzymy tu nowego węzła - tylko zaznaczamy, że następny element
            # powinien mieć relację od węzła fork
            return {'id': None, 'prev_id': fork_id}
        
        return {'id': None, 'transition': False}

    def _handle_fork_end(self, item, parent, stack, prev_id, partition):
        if stack and stack[-1]['type'] == 'fork':
            fork_data = stack.pop()
            join_node_id = self._add_node(parent, 'uml:JoinNode', 'Join', partition)
            
            # Dodaj do listy obiektów diagramu - KLUCZOWY BRAKUJĄCY KOD
            self.diagram_objects.append({
                'id': join_node_id,
                'type': 'JoinNode'
            })

            self._add_transition(parent, prev_id, join_node_id)
            for branch_end_id in fork_data['branch_ends']:
                self._add_transition(parent, branch_end_id, join_node_id)

            return {'id': join_node_id, 'transition': False}
        return {'id': None, 'transition': False}

    def _handle_note(self, item, parent, stack, prev_id, partition):
        """Obsługuje notatki (komentarze)."""
        note_id = self._generate_ea_id("EAID")
        
        # Utwórz komentarz z poprawnie ustawioną treścią
        note = ET.SubElement(parent, 'ownedComment', self._sanitize_xml_attrs({
            'xmi:type': 'uml:Comment', 
            'xmi:id': note_id,
            'visibility': 'public',
            'name': item['text'][:30] + ('...' if len(item['text']) > 30 else '')
        }))
        
        # Dodaj ciało notatki jako osobny element
        body = ET.SubElement(note, 'body')
        body.text = item['text']  # Pełna treść notatki
        
        # Połącz notatkę z elementem docelowym
        if prev_id:
            ET.SubElement(note, 'annotatedElement', {'xmi:idref': prev_id})
        
        # Dodaj do listy obiektów diagramu z poprawnym typem
        self.diagram_objects.append({
            'id': note_id,
            'type': 'Comment',
            'name': item['text']
        })
        
        return {'id': None, 'transition': False}

    def _add_node(self, parent_activity: ET.Element, node_type: str, name: str, partition_id: str) -> str:
        """Dodaje węzeł (aktywność, decyzję, etc.) do modelu i przygotowuje jego reprezentację."""
        node_id = self._generate_ea_id("EAID")
        attrs = {'xmi:type': node_type, 'xmi:id': node_id, 'visibility': 'public'}
        
        if name:  # Sprawdź czy nazwa nie jest None
            attrs['name'] = name
        
        if partition_id:
            attrs['inPartition'] = partition_id
        
        # Sanityzuj atrybuty przed utworzeniem elementu
        attrs = self._sanitize_xml_attrs(attrs)
        node = ET.SubElement(parent_activity, 'node', attrs)
        self.id_map[node_id] = node
        
        return node_id
    
    def _add_transition(self, parent_activity: ET.Element, source_id: str, target_id: str, name: str = ""):
        """Dodaje przejście (ControlFlow) między dwoma węzłami."""
        if not source_id or not target_id: return

        transition_id = self._generate_ea_id("EAID")
        attrs = {
            'xmi:type': 'uml:ControlFlow', 
            'xmi:id': transition_id, 
            'source': source_id, 
            'target': target_id,
            'visibility': 'public'  # Dodany atrybut visibility
        }
        if name:
            attrs['name'] = name
            # Dodaj warunek 'guard' do przejścia
            guard = ET.SubElement(parent_activity, 'ownedRule', {'xmi:id': self._generate_ea_id("EAID")})
            ET.SubElement(guard, 'specification', {
                'xmi:type': 'uml:LiteralString', 
                'value': name, 
                'xmi:id': self._generate_ea_id("EAID")
            })
            attrs['guard'] = guard.attrib['xmi:id']

        edge = ET.SubElement(parent_activity, 'edge', self._sanitize_xml_attrs(attrs))
        
        # Dodaj referencje do source i target (wzorzec EA)
        source_node = self.id_map[source_id]
        target_node = self.id_map[target_id]
        
        # Dodaj odniesienie do wychodzących (outgoing) dla źródła
        ET.SubElement(source_node, 'outgoing', {'xmi:idref': transition_id})
        
        # Dodaj odniesienie do przychodzących (incoming) dla celu
        ET.SubElement(target_node, 'incoming', {'xmi:idref': transition_id})
        
        self.transitions.append({
            'id': transition_id, 
            'source_id': source_id, 
            'target_id': target_id, 
            'name': name
        })
        print(f"  ↳ Dodano przejście: z {source_id[-4:]} do {target_id[-4:]} [etykieta: '{name}']")

    def _get_guard_for_transition(self, structure_stack, item):
        """Zwraca wartość warunku (guard) dla przejścia na podstawie kontekstu."""
        item_type = item.get('type')
        
        if item_type == 'decision_start':
            return item.get('then_label', 'tak')
        
        if item_type == 'decision_else':
            return item.get('else_label', 'nie')
            
        # Dla innych typów nie ustawiamy etykiety warunku
        return ""

    def _create_partitions_from_swimlanes(self, parent_activity: ET.Element, swimlanes: dict):
        """Tworzy elementy uml:ActivityPartition na podstawie torów."""
        for name in swimlanes.keys():
            partition_id = self._generate_ea_id("EAID")
            self.swimlane_ids[name] = partition_id
            
            # Utwórz partycję jako group (nie packagedElement)
            partition = ET.SubElement(parent_activity, 'group', {
                'xmi:type': 'uml:ActivityPartition', 
                'xmi:id': partition_id, 
                'name': name,
                'visibility': 'public'
            })
            
            self.partitions[name] = partition
            self.diagram_objects.append({'id': partition_id, 'type': 'ActivityPartition'})
            print(f"🏊 Utworzono tor (partition): {name}")

    def _create_document_root(self) -> ET.Element:
        root = ET.Element(ET.QName(self.ns['xmi'], 'XMI'), self._sanitize_xml_attrs({'xmi:version': '2.1'}))
        ET.SubElement(root, ET.QName(self.ns['xmi'], 'Documentation'), self._sanitize_xml_attrs({
            'exporter': 'Enterprise Architect', 
            'exporterVersion': '6.5', 
            'exporterID': '1560'
        }))
        return root

    def _create_uml_model(self, root: ET.Element) -> ET.Element:
        return ET.SubElement(root, ET.QName(self.ns['uml'], 'Model'), {
            'xmi:type': 'uml:Model', 'name': 'EA_Model', 'visibility': 'public'
        })

    def _create_diagram_package(self, model: ET.Element, diagram_name: str) -> ET.Element:
        """Tworzy główny pakiet diagramu."""
        # Tworzenie głównego pakietu "Diagram aktywności"
        root_package_id = self._generate_ea_id("EAPK")
        root_package = ET.SubElement(model, 'packagedElement', {
            'xmi:type': 'uml:Package', 
            'xmi:id': root_package_id, 
            'name': 'Diagram aktywności', 
            'visibility': 'public'
        })
        
        # UWAGA: Dodaj atrybut "ea_localid", który jest kluczowy dla EA do poprawnego importu
        root_package.set('ea_localid', self._get_local_id(root_package_id))
        
        self.root_package_id = root_package_id
        self.package_id = root_package_id
        
        return root_package

    def _update_partition_elements(self, parent_activity):
        """Aktualizuje powiązania elementów z torami."""
        for node_id, node in self.id_map.items():
            partition_id = node.attrib.get('inPartition', None)
            # Ten kod tylko ustawia atrybut w modelu, nie w wizualizacji diagramu

    def _create_main_activity(self, package: ET.Element, diagram_name: str) -> ET.Element:
        """Tworzy główną aktywność w pakiecie."""
        self.main_activity_id = self._generate_ea_id("EAID")
        return ET.SubElement(package, 'packagedElement', {
            'xmi:type': 'uml:Activity', 
            'xmi:id': self.main_activity_id, 
            'name': 'EA_Activity1',  # Stała nazwa zgodna z wzorcem
            'visibility': 'public'
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
        self._debug_diagram_objects()
        self._create_diagrams_section(extension, diagram_name)  # Bez przekazywania current_time

    def _create_elements_section(self, extension: ET.Element, diagram_name: str, current_time: str):
        elements = ET.SubElement(extension, 'elements')
        
        # Dodaj główny pakiet
        package_element = ET.SubElement(elements, 'element', {
            'xmi:idref': self.package_id,
            'xmi:type': 'uml:Package',
            'name': 'Diagram aktywności',
            'scope': 'public'
        })
        
        # Dodaj model dla pakietu
        ET.SubElement(package_element, 'model', {
            'package2': f"EAID_{self.package_id.split('_')[1]}", 
            'package': "EAPK_25CB1803_12A5_47b7_BF59_0C80F57AA528",  # Stała wartość ze wzorca
            'tpos': '0',
            'ea_localid': self._get_local_id(self.package_id),
            'ea_eleType': 'package'
        })
        
        # Dodaj elementy torów (ActivityPartition)
        for name, partition_id in self.swimlane_ids.items():
            swimlane_element = ET.SubElement(elements, 'element', {
                'xmi:idref': partition_id,
                'xmi:type': 'uml:ActivityPartition',
                'name': name,
                'scope': 'public'
            })
            
            # Dodaj model dla toru
            ET.SubElement(swimlane_element, 'model', {
                'package': self.package_id,  # Pakiet zawierający ten tor
                'tpos': '0',
                'ea_localid': self._get_local_id(partition_id),
                'ea_eleType': 'element'
            })
            
            # Dodaj properties dla toru
            ET.SubElement(swimlane_element, 'properties', {
                'isSpecification': 'false',
                'sType': 'ActivityPartition',
                'nType': '0',
                'scope': 'public'
            })
        
        # Dodaj pozostałe elementy diagramu z odpowiednim przypisaniem do torów
        for node_id, node in self.id_map.items():
            if node_id not in self.swimlane_ids.values():  # Nie dodawaj torów ponownie
                node_element = ET.SubElement(elements, 'element', {'xmi:idref': node_id})
                
                # Określ typ i nazwę elementu
                node_type = node.attrib.get('xmi:type', '')
                if 'name' in node.attrib:
                    node_name = node.attrib['name']
                else:
                    node_name = ''
                
                # Znajdź tor, do którego należy ten element
                owner_id = None
                if 'inPartition' in node.attrib:
                    owner_id = node.attrib['inPartition']
                
                # Dodaj model dla elementu
                model_attrs = {
                    'package': self.package_id,
                    'tpos': '0',
                    'ea_localid': self._get_local_id(node_id),
                    'ea_eleType': 'element'
                }
                
                if owner_id:
                    model_attrs['owner'] = owner_id
                    
                ET.SubElement(node_element, 'model', model_attrs)
                
                # Dodaj properties dla elementu
                props = ET.SubElement(node_element, 'properties', {
                    'isSpecification': 'false',
                    'sType': self._get_element_type(node_id),
                    'nType': self._get_ntype_from_uml_type(node_type),
                    'scope': 'public'
                })
                
                if node_name:
                    props.set('name', node_name)

    def _get_ntype_from_uml_type(self, uml_type):
        ntype_map = {
            'uml:Action': '0',           # Action
            'uml:DecisionNode': '131',   # Decision
            'uml:MergeNode': '133',      # Merge
            'uml:InitialNode': '100',    # Initial (zmienione z 101 na 100)
            'uml:ActivityFinalNode': '101',  # Final (zmienione z 102 na 101)
            'uml:ForkNode': '0',        # Fork
            'uml:JoinNode': '0',        # Join
            'uml:ControlFlow': '97'      # ControlFlow
        }
        return ntype_map.get(uml_type, '0')
    
    def _get_local_id(self, obj_id):
        """Generuje lokalny identyfikator dla Enterprise Architect na podstawie ID elementu."""
        # W EA lokalny ID to zwykle liczbowy identyfikator
        # Możemy użyć prostego hashowania ID do liczby
        if not hasattr(self, '_local_id_counter'):
            self._local_id_counter = 1
        
        if not hasattr(self, '_local_id_map'):
            self._local_id_map = {}
        
        if obj_id not in self._local_id_map:
            self._local_id_map[obj_id] = str(self._local_id_counter)
            self._local_id_counter += 1
        
        return self._local_id_map[obj_id]

    def _get_element_type(self, obj_id):
        """Zwraca typ elementu EA na podstawie jego ID."""
        if obj_id in self.id_map and 'xmi:type' in self.id_map[obj_id].attrib:
            uml_type = self.id_map[obj_id].attrib['xmi:type']
            
            type_mapping = {
                'uml:Action': 'Action',
                'uml:DecisionNode': 'Decision',
                'uml:MergeNode': 'Merge',
                'uml:InitialNode': 'StateNode',
                'uml:ActivityFinalNode': 'StateNode',
                'uml:ForkNode': 'Synchronization',  # Prawidłowo mapuj na Synchronization
                'uml:JoinNode': 'Synchronization',  # Prawidłowo mapuj na Synchronization
                'uml:Comment': 'Note'
            }
            
            return type_mapping.get(uml_type, 'Action')
        return 'Action'

    def _get_element_name(self, obj_id):
        """Zwraca nazwę elementu na podstawie jego ID."""
        if obj_id in self.id_map and 'name' in self.id_map[obj_id].attrib:
            return self.id_map[obj_id].attrib['name']
        return ""  # Pusta nazwa dla elementów bez nazwy

    def _create_connectors_section(self, extension: ET.Element):
        """Tworzy sekcję connectors zawierającą wszystkie przejścia między elementami."""
        connectors = ET.SubElement(extension, 'connectors')
        
        for i, tran in enumerate(self.transitions):
            connector = ET.SubElement(connectors, 'connector', {'xmi:idref': tran['id']})
            
            # --- SOURCE (źródło przejścia) ---
            source_type = self._get_element_type(tran['source_id'])
            source_name = self._get_element_name(tran['source_id'])
            
            # SOURCE
            source = ET.SubElement(connector, 'source', {'xmi:idref': tran['source_id']})
            ET.SubElement(source, 'model', {
                'ea_localid': self._get_local_id(tran['source_id']), 
                'type': source_type,
                'name': source_name
            })
            
            # Rola źródła
            ET.SubElement(source, 'role', {'visibility': 'Public', 'targetScope': 'instance'})
            
            # Typ relacji dla źródła
            ET.SubElement(source, 'type', {'aggregation': 'none', 'containment': 'Unspecified'})
            
            # Ograniczenia dla źródła
            ET.SubElement(source, 'constraints')
            
            # Modyfikatory dla źródła
            ET.SubElement(source, 'modifiers', {
                'isOrdered': 'false',
                'changeable': 'none', 
                'isNavigable': 'false'
            })
            
            # Styl dla źródła
            ET.SubElement(source, 'style', {'value': 'Union=0;Derived=0;AllowDuplicates=0;'})
            
            # Dodaj informację o torze dla źródła
            source_node = self.id_map[tran['source_id']]
            source_swimlane = None
            if 'inPartition' in source_node.attrib:
                source_partition = source_node.attrib['inPartition']
                for name, pid in self.swimlane_ids.items():
                    if pid == source_partition:
                        source_swimlane = name
                        ET.SubElement(source, 'properties', {'swimlane': name})
                        break
            
            # --- TARGET (cel przejścia) ---
            target_type = self._get_element_type(tran['target_id'])
            target_name = self._get_element_name(tran['target_id'])
            
            # TARGET
            target = ET.SubElement(connector, 'target', {'xmi:idref': tran['target_id']})
            ET.SubElement(target, 'model', {
                'ea_localid': self._get_local_id(tran['target_id']), 
                'type': target_type,
                'name': target_name
            })
                
            # Rola celu
            ET.SubElement(target, 'role', {'visibility': 'Public', 'targetScope': 'instance'})
            
            # Typ relacji dla celu
            ET.SubElement(target, 'type', {'aggregation': 'none', 'containment': 'Unspecified'})
            
            # Ograniczenia dla celu
            ET.SubElement(target, 'constraints')
            
            # Modyfikatory dla celu
            ET.SubElement(target, 'modifiers', {
                'isOrdered': 'false',
                'changeable': 'none', 
                'isNavigable': 'true'
            })
            
            # Styl dla celu
            ET.SubElement(target, 'style', {'value': 'Union=0;Derived=0;AllowDuplicates=0;'})
            
            # Dodaj informację o torze dla celu
            target_node = self.id_map[tran['target_id']]
            target_swimlane = None
            if 'inPartition' in target_node.attrib:
                target_partition = target_node.attrib['inPartition']
                for name, pid in self.swimlane_ids.items():
                    if pid == target_partition:
                        target_swimlane = name
                        ET.SubElement(target, 'properties', {'swimlane': name})
                        break
            
            # --- PROPERTIES (właściwości połączenia) ---
            properties_attrs = {
                'ea_type': 'ControlFlow',
                'stereotype': '',
                'direction': 'Source -> Destination',
                'virtualInheritance': '0'
            }
            
            # Dodaj etykietę przejścia jeśli istnieje
            if tran['name']:
                properties_attrs['name'] = tran['name']
                properties_attrs['guard'] = tran['name']  # Ustaw guard dla warunku decyzji
            
            # Dodaj element properties z odpowiednimi atrybutami
            ET.SubElement(connector, 'properties', properties_attrs)
            
            # --- LABELS (etykiety przejścia) ---
            if tran['name']:
                label_attrs = {
                    'lb': tran['name'],       # Tekst etykiety
                    'mt': '0',                # Typ etykiety
                    'ea_localid': self._get_local_id(tran['id']) + '_lbl'  # Unikalny ID etykiety
                }
                
                # Różne położenie etykiety w zależności od typu przejścia
                if source_swimlane != target_swimlane and source_swimlane and target_swimlane:
                    # Dla przejść między torami - etykieta na środku
                    label_attrs['pt'] = 'Center'
                else:
                    # Dla przejść wewnątrz toru - etykieta z boku
                    label_attrs['pt'] = 'MiddleRight'
                
                ET.SubElement(connector, 'labels', label_attrs)
            
            # --- DOCUMENTATION (dokumentacja) ---
            ET.SubElement(connector, 'documentation', {
                'value': tran.get('name', '') or ''  # Zamień None na pusty string
            })
            
            # --- APPEARANCE (wygląd połączenia) ---
            appearance_attrs = {
                'linemode': '1',     # Domyślnie: prosta linia
                'linecolor': '-1',   # Domyślny kolor
                'linewidth': '1',    # Standardowa grubość
                'seqno': str(i),     # Numer sekwencyjny
                'headStyle': '0',    # Standardowa strzałka
                'lineStyle': '0'     # Ciągła linia
            }
            
            # Specjalna konfiguracja dla relacji międzytorowych
            if source_swimlane != target_swimlane and source_swimlane and target_swimlane:
                # Dla relacji między różnymi torami użyj innego stylu
                appearance_attrs['linemode'] = '3'      # Automatyczne routowanie
                appearance_attrs['routing'] = 'Orthogonal'  # Prostopadłe linie
                appearance_attrs['startPointX'] = '-1'  # Automatyczne punkty startowe
                appearance_attrs['startPointY'] = '-1'
                appearance_attrs['endPointX'] = '-1'    # Automatyczne punkty końcowe
                appearance_attrs['endPointY'] = '-1'
            else:
                # Dla relacji wewnątrz toru - prostsza konfiguracja
                appearance_attrs['linemode'] = '1'
            
            ET.SubElement(connector, 'appearance', appearance_attrs)
            
            # --- TAGS (tagi dla przejścia) ---
            if tran.get('name'):
                tags = ET.SubElement(connector, 'tags')
                ET.SubElement(tags, 'tag', {
                    'name': 'guard',
                    'value': tran['name'],
                    'modelElement': tran['id']
                })
                
            # --- XREFS (referencje krzyżowe) ---
            xrefs = ET.SubElement(connector, 'xrefs')
            
            # --- EXTENDEDPROPERTIES (rozszerzone właściwości) ---
            conditional = 'true' if tran.get('name', '') != '' else 'false'
            
            # Upewnij się, że diagram_id istnieje
            diagram_id = getattr(self, 'diagram_id', '')
            if not diagram_id:
                diagram_id = self._generate_ea_id("EAID")
                self.diagram_id = diagram_id
                
            ET.SubElement(connector, 'extendedProperties', 
                self._sanitize_xml_attrs({
                    'conditional': conditional,
                    'diagram': diagram_id
                })
            )
            
    def _sanitize_xml_attrs(self, attrs):
        """Sanityzuje atrybuty XML, konwertując None i bool na stringi."""
        if attrs is None:
            return {}
            
        result = {}
        for key, value in attrs.items():
            if value is None:
                result[key] = ''  # Konwertuj None na pusty string
            elif isinstance(value, bool):
                result[key] = 'true' if value else 'false'  # Konwertuj bool na string
            else:
                result[key] = str(value)  # Konwertuj wszystko inne na string
        return result
    
    def _ensure_element_type_consistency(self):
        """Zapewnia spójność typów elementów w całym dokumencie XMI."""
        for node_id, node in self.id_map.items():
            if 'xmi:type' in node.attrib:
                uml_type = node.attrib['xmi:type']
                
                # Upewnij się, że typ elementów fork/join jest poprawny
                if uml_type == 'uml:Synchronization' and 'name' in node.attrib:
                    if node.attrib['name'] == 'Fork':
                        node.attrib['xmi:type'] = 'uml:ForkNode'
                    elif node.attrib['name'] == 'Join':
                        node.attrib['xmi:type'] = 'uml:JoinNode'
                    

    def _calculate_diagram_layout(self):
        """Oblicza optymalne położenie wszystkich elementów na diagramie."""
        # 1. Przygotuj strukturę grafową
        graph = {}
        for obj_id in self.id_map.keys():
            graph[obj_id] = {'next': [], 'prev': [], 'level': -1, 'type': None}
            if obj_id in self.id_map and 'xmi:type' in self.id_map[obj_id].attrib:
                graph[obj_id]['type'] = self.id_map[obj_id].attrib['xmi:type']
        
        # 2. Zbuduj graf z przejść
        for trans in self.transitions:
            source_id, target_id = trans['source_id'], trans['target_id']
            if source_id in graph and target_id in graph:
                graph[source_id]['next'].append(target_id)
                graph[target_id]['prev'].append(source_id)
        
        # 3. Przypisz poziomy (warstwy) w grafie - algorytm topologiczny
        queue = [node_id for node_id, data in graph.items() if not data['prev']]  # węzły startowe
        current_level = 0
        
        while queue:
            next_queue = []
            for node_id in queue:
                graph[node_id]['level'] = current_level
                next_queue.extend([next_id for next_id in graph[node_id]['next'] 
                                if all(graph[p]['level'] >= 0 for p in graph[next_id]['prev'])])
            current_level += 1
            queue = next_queue
        
        # 4. Znajdź najwyższy poziom dla każdego toru
        swimlane_levels = {}
        node_counts = {}
        for name, partition_id in self.swimlane_ids.items():
            swimlane_levels[name] = -1
            node_counts[name] = 0
        
        # Zlicz elementy i znajdź najwyższy poziom w każdym torze
        for node_id, node_data in self.id_map.items():
            if 'inPartition' in node_data.attrib:
                partition_id = node_data.attrib['inPartition']
                for name, pid in self.swimlane_ids.items():
                    if pid == partition_id and node_id in graph:
                        swimlane_levels[name] = max(swimlane_levels[name], graph[node_id]['level'])
                        node_counts[name] += 1
        
        # 5. Oblicz współrzędne uwzględniając poziomy i tory
        node_positions = {}
        swimlane_positions = {}
        
        # Zmiana układu - używamy pionowych torów jeden obok drugiego
        x_offset = 100
        lane_width = 250  # Mniejsza szerokość torów
        margin = 30
        
        # Przygotuj mapy poziomów dla każdego toru
        lane_elements = {name: [] for name in self.swimlane_ids.keys()}
        
        # Przypisz elementy do odpowiednich torów
        for node_id, node in self.id_map.items():
            if 'inPartition' in node.attrib:
                swimlane = None
                for name, pid in self.swimlane_ids.items():
                    if pid == node.attrib['inPartition']:
                        swimlane = name
                        break
                
                if swimlane:
                    lane_elements[swimlane].append(node_id)
        
        # Oblicz wysokość każdego toru na podstawie liczby elementów
        for name, elements in lane_elements.items():
            element_count = len(elements)
            # Wysokość zależna od liczby elementów (przynajmniej 1 element + margines)
            height = max(800, 150 * (element_count + 2))
            
            swimlane_positions[name] = {
                'x': x_offset,
                'y': 100,
                'width': lane_width,
                'height': height
            }
            x_offset += lane_width + margin
        
        # 6. Przydzielanie poziomów dla elementów w torach
        # Inicjalizacja słownika przechowującego następny dostępny Y dla każdego toru
        swimlane_next_y = {name: swimlane_positions[name]['y'] + 80 for name in self.swimlane_ids.keys()}

        # Słownik do śledzenia ostatniego elementu w każdym torze
        previous_in_lane = {name: None for name in self.swimlane_ids.keys()}

        # Sortuj węzły według ich poziomów w grafie, żeby zachować logiczną kolejność
        sorted_nodes = []
        for level in range(current_level):
            for node_id, data in graph.items():
                if data['level'] == level:
                    sorted_nodes.append(node_id)

        # Najpierw przypisz pozycje dla węzłów o określonych poziomach
        for node_id in sorted_nodes:
            if node_id not in self.id_map:
                continue
                
            node = self.id_map[node_id]
            if 'xmi:type' not in node.attrib:
                continue
                
            # Dostosowanie rozmiaru węzłów w zależności od typu
            node_type = node.attrib['xmi:type']
            node_width = 120
            node_height = 60
            
            # Zmniejsz rozmiar węzłów kontrolnych i decyzyjnych
            if node_type in ('uml:InitialNode', 'uml:ActivityFinalNode'):
                node_width = 30  # Mniejszy rozmiar
                node_height = 30
            elif node_type == 'uml:DecisionNode':
                node_width = 40
                node_height = 40
            elif node_type in ('uml:MergeNode', 'uml:Synchronization'):
                node_width = 40
                node_height = 40
                
            swimlane = None
            if 'inPartition' in node.attrib:
                for name, pid in self.swimlane_ids.items():
                    if pid == node.attrib['inPartition']:
                        swimlane = name
                        break
            
            if swimlane:
                # Pobierz pozycję dla toru
                swimlane_pos = swimlane_positions[swimlane]
                
                # Lepsze wyśrodkowanie elementów w torach
                lane_center = swimlane_pos['x'] + (swimlane_pos['width'] / 2)
                x = lane_center - (node_width / 2)
                
                # Kontrola odległości pionowej między elementami
                vertical_spacing = 50  # Odstęp pionowy
                
                prev_node = previous_in_lane[swimlane]
                if prev_node and prev_node in node_positions:
                    # Minimalny odstęp od poprzedniego elementu
                    min_spacing = node_positions[prev_node]['height'] + vertical_spacing
                    y = max(swimlane_next_y[swimlane], 
                        node_positions[prev_node]['y'] + min_spacing)
                else:
                    y = swimlane_next_y[swimlane]
                
                # Ustaw pozycję elementu
                node_positions[node_id] = {
                    'x': x, 'y': y,
                    'width': node_width, 'height': node_height
                }
                
                # Zapisz bieżący węzeł jako poprzedni dla tego toru
                previous_in_lane[swimlane] = node_id
                
                # Aktualizuj następny dostępny Y dla tego toru
                swimlane_next_y[swimlane] = y + node_height + vertical_spacing
        
        # 7. Specjalne traktowanie dla węzłów decyzyjnych
        for node_id, data in graph.items():
            if data['type'] == 'uml:DecisionNode' and node_id in node_positions:
                branches = [t for t in self.transitions if t['source_id'] == node_id]
                
                if len(branches) > 1:
                    decision_pos = node_positions[node_id]
                    branch_offset = 80  # Odstęp między gałęziami w poziomie
                    
                    # Rozmieść gałęzie w poziomie
                    for i, branch in enumerate(branches):
                        target_id = branch['target_id']
                        if target_id in node_positions:
                            offset_x = (i - (len(branches) - 1) / 2) * branch_offset
                            
                            # Modyfikuj pozycję X, zachowaj Y
                            node_positions[target_id]['x'] = decision_pos['x'] + offset_x
                            # Przesunięcie w pionie dla lepszej widoczności
                            node_positions[target_id]['y'] = decision_pos['y'] + 80
        
        # 8. Specjalne traktowanie dla węzłów łączących (merge i join)
        for node_id, data in graph.items():
            if data['type'] in ('uml:MergeNode', 'uml:JoinNode') and node_id in node_positions:
                # Znajdź wszystkie źródła tego węzła łączącego
                sources = [t['source_id'] for t in self.transitions if t['target_id'] == node_id]
                
                if sources and all(s in node_positions for s in sources):
                    # Wyśrodkuj węzeł względem jego źródeł
                    avg_x = sum(node_positions[s]['x'] for s in sources) / len(sources)
                    max_y = max(node_positions[s]['y'] for s in sources) + 100
                    
                    node_positions[node_id]['x'] = avg_x
                    node_positions[node_id]['y'] = max_y
        
        # 9. Specjalne traktowanie notatek
        for node_id, node in self.id_map.items():
            if 'xmi:type' in node.attrib and node.attrib['xmi:type'] == 'uml:Comment':
                # Sprawdź, czy notatka ma powiązany element
                annotated_elements = node.findall('annotatedElement')
                
                if annotated_elements:
                    ref_id = annotated_elements[0].get('xmi:idref')
                    if ref_id in node_positions:
                        # Umieść notatkę z prawej strony powiązanego elementu
                        ref_pos = node_positions[ref_id]
                        node_positions[node_id] = {
                            'x': ref_pos['x'] + ref_pos['width'] + 30,
                            'y': ref_pos['y'],
                            'width': 150,  # Większa szerokość dla notatek
                            'height': 80
                        }
                else:
                    # Umieść niepowiązane notatki na górze diagramu
                    node_positions[node_id] = {
                        'x': 100,
                        'y': 50,
                        'width': 150,
                        'height': 80
                    }
        
        # 10. Sprawdź i rozszerz tory jeśli elementy wychodzą poza ich granice
        for node_id, pos in node_positions.items():
            node = self.id_map.get(node_id)
            if node is not None and 'inPartition' in node.attrib:
                partition_id = node.attrib['inPartition']
                for name, pid in self.swimlane_ids.items():
                    if pid == partition_id:
                        swimlane_pos = swimlane_positions[name]
                        
                        # Sprawdź czy element wychodzi poza tor w poziomie
                        if pos['x'] < swimlane_pos['x']:
                            pos['x'] = swimlane_pos['x'] + 20  # Margines
                        
                        right_edge = pos['x'] + pos['width']
                        lane_right_edge = swimlane_pos['x'] + swimlane_pos['width']
                        if right_edge > lane_right_edge:
                            # Rozszerz tor w poziomie (zamiast przesuwać element)
                            new_width = right_edge - swimlane_pos['x'] + 50  # Dodatkowy margines
                            swimlane_positions[name]['width'] = new_width
                        
                        # Sprawdź czy element wychodzi poza tor w pionie
                        bottom_edge = pos['y'] + pos['height']
                        lane_bottom_edge = swimlane_pos['y'] + swimlane_pos['height']
                        if bottom_edge > lane_bottom_edge:
                            # Rozszerz tor w dół
                            new_height = bottom_edge - swimlane_pos['y'] + 100  # Większy margines
                            swimlane_positions[name]['height'] = new_height
        
        return node_positions, swimlane_positions

    def _create_diagrams_section(self, extension: ET.Element, diagram_name: str):
        """Tworzy sekcję diagram zawierającą informacje o diagramie aktywności."""
        if not self.diagram_id:
            self.diagram_id = self._generate_ea_id("EAID")
            
        diagrams = ET.SubElement(extension, 'diagrams')
        diagram = ET.SubElement(diagrams, 'diagram', {
            'xmi:id': self.diagram_id,
            'name': diagram_name,
            'type': 'Activity',
            'diagramType': 'ActivityDiagram'
        })
            
        # Model diagramu
        ET.SubElement(diagram, 'model', self._sanitize_xml_attrs({
            'package': self.package_id,
            'localID': str(self._local_id_counter),
            'owner': self.package_id,
            'ea_localid': str(self._local_id_counter),
            'tpos': '0'
        }))
        self._local_id_counter += 1
        
        # Style diagramu
        ET.SubElement(diagram, 'style1', {'value': (
            'ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;'
            'Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;'
            'ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=795;DocSize.cy=1134;'
            'ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;'
            'VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;'
            'HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;'
            'HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;'
            'ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;'
            'AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;'
            'ShowShape=1;'
        )})
        
        # Konfiguracja swimlanes
        ET.SubElement(diagram, 'swimlanes', {'value': (
            'locked=false;orientation=1;width=0;inbar=false;names=true;color=-1;'
            'bold=false;fcol=0;tcol=-1;ofCol=-1;ufCol=-1;hl=0;ufh=0;cls=0;'
            'SwimlaneFont=lfh:-10,lfw:0,lfi:0,lfu:0,lfs:0,lfface:Calibri,lfe:0,'
            'lfo:0,lfchar:1,lfop:0,lfcp:0,lfq:0,lfpf=0,lfWidth=0;'
        )})
        
        # Właściwości diagramu
        ET.SubElement(diagram, 'properties', self._sanitize_xml_attrs({
            'name': diagram_name,
            'type': 'Activity',
            'documentation': ''
        }))
        
        # Informacje o projekcie
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ET.SubElement(diagram, 'project', {
            'author': 'XMI Generator',
            'version': '1.0',
            'created': current_time,
            'modified': current_time
        })
        
        # Elementy diagramu - tworzę tylko jedną sekcję elements
        elements = ET.SubElement(diagram, 'elements')
        
        # Tworzę manager layoutu
        layout_manager = self._create_layout_manager()
        
        # Najpierw dodaję tory (swimlanes) - ważne dla poprawnego układu
        for i, (name, partition_id) in enumerate(self.swimlane_ids.items()):
        # Pobierz geometrię toru z layoutManagera
            lane_geom = layout_manager.swimlanes_geometry.get(partition_id, {})
            left = lane_geom.get('x', 100 + i * 280)
            width = lane_geom.get('width', 250)
            right = left + width
            
            ET.SubElement(elements, 'element', self._sanitize_xml_attrs({
                'subject': partition_id,
                'seqno': str(i),
                'geometry': f"Left={left};Top=100;Right={right};Bottom=1150;",
                'style': "LineColor=15461355;FillColor=14993154;LineWidth=1;BorderStyle=0;VPartition=1;"
            }))
        
        # Sortowanie elementów dla lepszego układu
        sorted_objects = []
        
        # Dodaję najpierw węzły początkowe i końcowe
        for obj_id in self.diagram_objects:
            element_id = obj_id.get('id') if isinstance(obj_id, dict) else obj_id
            if element_id in self.id_map:
                node = self.id_map[element_id]
                if 'xmi:type' in node.attrib and ('InitialNode' in node.attrib['xmi:type'] or 'ActivityFinalNode' in node.attrib['xmi:type']):
                    sorted_objects.append(element_id)
        
        # Dodaję węzły decyzyjne, fork i join
        for obj_id in self.diagram_objects:
            element_id = obj_id.get('id') if isinstance(obj_id, dict) else obj_id
            if element_id in self.id_map and element_id not in sorted_objects:
                node = self.id_map[element_id]
                if 'xmi:type' in node.attrib and ('DecisionNode' in node.attrib['xmi:type'] or 'ForkNode' in node.attrib['xmi:type'] or 'JoinNode' in node.attrib['xmi:type'] or 'MergeNode' in node.attrib['xmi:type']):
                    sorted_objects.append(element_id)
        
        # Dodaję pozostałe elementy
        for obj_id in self.diagram_objects:
            element_id = obj_id.get('id') if isinstance(obj_id, dict) else obj_id
            if element_id and element_id not in sorted_objects and element_id in self.id_map:
                sorted_objects.append(element_id)
        
        # Teraz dodaję wszystkie elementy diagramu z ich geometrią
        seq_no = len(self.swimlane_ids)  # Zaczynam numerację od liczby torów
        for element_id in sorted_objects:
            if not element_id or element_id not in self.id_map:
                continue
            
            node = self.id_map[element_id]
            position = layout_manager.get_position_for_element(node)
            element_style = self._get_style_for_element(node)
            
            ET.SubElement(elements, 'element', self._sanitize_xml_attrs({
                'subject': element_id,
                'seqno': str(seq_no),
                'geometry': position,
                'style': element_style
            }))
            seq_no += 1
        
        return diagram

    def _get_style_for_element(self, node):
        """Zwraca styl CSS dla elementu diagramu z uwzględnieniem kolorów z PlantUML."""
        node_type = node.attrib.get('xmi:type', '')
        node_name = node.attrib.get('name', '').lower()
        
        # Domyślny styl dla elementu
        style = "BorderColor=-1;BorderWidth=-1;"
        
        if 'InitialNode' in node_type:
            style += "BColor=0;FontColor=-1;BorderWidth=0;Shape=Circle;"
        elif 'ActivityFinalNode' in node_type:
            style += "BColor=0;FontColor=-1;BorderWidth=1;Shape=Circle;"
        elif 'DecisionNode' in node_type or 'MergeNode' in node_type:
            style += "BColor=16777062;FontColor=-1;Shape=Diamond;"
        elif 'ForkNode' in node_type or 'JoinNode' in node_type:
            style += "BColor=0;FontColor=-1;LineWidth=3;Shape=Rectangle;"
        else:
            # Standardowe akcje - zaokrąglone prostokąty z kolorami zależnymi od nazwy
            if 'pozytywny' in node_name:
                # Zielony dla pozytywnych wyników
                style += "BColor=8454143;FontColor=-1;BorderRadius=10;"
            elif 'negatywny' in node_name or 'błąd' in node_name or 'blad' in node_name:
                # Czerwony dla negatywnych wyników
                style += "BColor=5263615;FontColor=-1;BorderRadius=10;"
            elif 'wizualn' in node_name:
                # Pomarańczowy dla błędów wizualnych
                style += "BColor=42495;FontColor=-1;BorderRadius=10;"
            else:
                # Standardowy kolor dla pozostałych akcji
                style += "BColor=13434828;FontColor=-1;BorderRadius=10;"
        
        return style

    def _create_layout_manager(self):
        """Tworzy i zwraca instancję managera layoutu."""
        # Przekaż ID wszystkich torów oraz mapę ID do LayoutManager
        layout_manager = LayoutManager(
            self.swimlane_ids, 
            transitions=self.transitions,
            id_map=self.id_map
        )
        return layout_manager

    def _sanitize_tree(self, element):
        """Sanityzuje wszystkie atrybuty w całym drzewie XML rekurencyjnie."""
        # Sanityzuj atrybuty bieżącego elementu
        for key, value in list(element.attrib.items()):
            if value is None:
                element.attrib[key] = ""
            elif isinstance(value, bool):
                element.attrib[key] = 'true' if value else 'false'
        
        # Sanityzuj wszystkie elementy potomne
        for child in element:
            self._sanitize_tree(child)

    def _format_xml(self, root: ET.Element) -> str:
        """Poprawia nagłówek i formatuje XML do czytelnej postaci."""
        # Debugowanie - znajdź wszystkie wartości None przed serializacją
        print("Sprawdzanie wartości None w drzewie XML...")
        self._debug_find_none_values(root)
        
        # Zastosuj sanityzację do całego drzewa XML rekurencyjnie
        self._sanitize_tree(root)
        
        xml_string = ET.tostring(root, encoding='unicode', method='xml', xml_declaration=True)
        xml_string_fixed = xml_string.replace("<?xml version='1.0' encoding='unicode'?>", '<?xml version="1.0" encoding="UTF-8"?>')
        dom = xml.dom.minidom.parseString(xml_string_fixed)
        return dom.toprettyxml(indent="  ")

# --- Przykład użycia ---
if __name__ == '__main__':
    generator = XMIActivityGenerator(author="195841_AI")
    
    input_puml_file = 'Diagram_aktywnosci_test2.puml'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"pelny_diagram_aktywnosci_{timestamp}.xmi"
    diagram_name = f"Pełny diagram aktywności {timestamp}"

    # Przykładowy, złożony kod PlantUML do testów
    plantuml_example_code = ""
    
    try:
        #with open(input_puml_file, 'w', encoding='utf-8') as f:
         #   f.write(plantuml_example_code)
        
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