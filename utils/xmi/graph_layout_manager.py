import sys
import os
from typing import Dict, List, Tuple, Set, Optional
from collections import deque, defaultdict
import math

# Dodaj ścieżkę do logger_utils
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)

try:
    from logger_utils import log_debug, log_info, log_error, log_exception, log_warning
except ImportError:
    def log_debug(msg): print(f"DEBUG: {msg}")
    def log_info(msg): print(f"INFO: {msg}")
    def log_error(msg): print(f"ERROR: {msg}")
    def log_warning(msg): print(f"WARNING: {msg}")


class Node:
    """Reprezentacja węzła grafu dla własnego algorytmu Sugiyamy"""
    
    def __init__(self, node_id: str, node_type: str = "", node_name: str = "", swimlane: str = None):
        self.id = node_id
        self.type = node_type.lower()
        self.name = node_name
        self.swimlane = swimlane
        
        # ✅ Przełóż klasyfikację AFTER ustawienia action
        self.action = None
        
        # Pozycjonowanie
        self.layer = -1
        self.position_in_layer = 0
        self.x = 0.0
        self.y = 0.0
        
        # ✅ TYMCZASOWO: Ustaw role na podstawie typu (bez action)
        self.role = self._classify_role_basic()
        
        # Wymiary - AFTER role classification
        self.width, self.height = self._calculate_dimensions()
        
        # Połączenia
        self.successors: List['Node'] = []
        self.predecessors: List['Node'] = []
        
        # Pomocnicze
        self.is_virtual = False
        self.barycenter = 0.0

    def _classify_role_basic(self) -> str:
        """NOWA METODA: Klasyfikacja tylko na podstawie typu (bez action)"""
        
        # Sprawdź typ bezpośrednio
        if self.type in [
            'start',
            'initial',
            'initialnode',
        ]:
            return 'start'
        elif self.type in [
            'end',
            'final',
            'finalnode',
            'activityfinal',
        ]:
            return 'end'
        if self.type == 'control':
            # Dla węzłów control - sprawdź nazwę jako fallback
            name_lower = self.name.lower() if self.name else ''
            if 'start' in name_lower or 'initial' in name_lower:
                return 'start'
            elif 'end' in name_lower or 'final' in name_lower or 'stop' in name_lower:
                return 'end'
            else:
                return 'control'  # Ogólny control
        
        elif self.type == 'decision_start':
            return 'decision'
        elif self.type == 'decision_else':
            return 'decision_else'
        elif self.type == 'decision_end':
            return 'decision_end'
        elif self.type == 'merge':
            return 'decision'
        elif self.type == 'note':
            return 'note'
        elif self.type == 'activity':
            # Sprawdź czy to błąd na podstawie tekstu
            name_lower = self.name.lower() if self.name else ''
            if 'błąd' in name_lower or 'error' in name_lower:
                return 'error'
            else:
                return 'activity'
        elif 'fork' in self.type:
            return 'fork'
        elif 'join' in self.type:
            return 'join'
        else:
            return 'activity'  # Fallback

    def update_role_after_action(self):
        """NOWA METODA: Aktualizuj role po ustawieniu action"""
        
        if self.type == 'control' and hasattr(self, 'action') and self.action:
            if self.action == 'start':
                self.role = 'start'
            elif self.action in ['end', 'stop']:
                self.role = 'end'
            
            # Przelicz wymiary ponownie
            self.width, self.height = self._calculate_dimensions()
        
    def _calculate_dimensions(self) -> Tuple[int, int]:
        """POPRAWIONE obliczanie wymiarów - zmniejszone o połowę"""
        
        debug_enabled = hasattr(self, 'debug') and getattr(self, 'debug', False)
        
        if debug_enabled:
            log_debug(f"🔍 Calculating dimensions: id={self.id[-8:]}, type='{self.type}', role='{getattr(self, 'role', 'N/A')}', action='{getattr(self, 'action', 'N/A')}'")

        # ✅ UŻYWAJ ROLE ZAMIAST ACTION (bo action może być None)
        if hasattr(self, 'role') and self.role:
            if self.role == 'start':
                if debug_enabled:
                    log_debug(f"   ✅ START node (by role) → 25×25px")  # ← POŁOWA z 50×50
                return (25, 25)
            elif self.role == 'end':
                if debug_enabled:
                    log_debug(f"   ✅ END node (by role) → 25×25px")   # ← POŁOWA z 50×50
                return (25, 25) 
            elif self.role in ['decision', 'decision_start', 'merge']:
                if debug_enabled:
                    log_debug(f"   ✅ DECISION node (by role) → 40×40px")  # ← POŁOWA z 80×80
                return (40, 40)
            elif self.role == 'note':
                if debug_enabled:
                    log_debug(f"   ✅ NOTE node (by role) → 80×40px")  # ← POŁOWA z 160×80
                return (80, 40)

        # ✅ BACKUP: Sprawdź action dla węzłów control (jeśli role nie zadziałała)
        if self.type == 'control':
            action = getattr(self, 'action', '')
            if debug_enabled:
                log_debug(f"   📝 Control node detected, action='{action}'")
                
            if action == 'start':
                if debug_enabled:
                    log_debug(f"   ✅ START node (by action) → 25×25px")
                return (25, 25)
            elif action in ['end', 'stop']:
                if debug_enabled:
                    log_debug(f"   ✅ END/STOP node (by action) → 25×25px")
                return (25, 25)

        # ✅ FALLBACK: Sprawdź typ bezpośrednio
        type_lower = self.type.lower()
        
        if 'initial' in type_lower:
            if debug_enabled:
                log_debug(f"   ✅ Initial type detected → 25×25px")
            return (25, 25)
        elif 'final' in type_lower:
            if debug_enabled:
                log_debug(f"   ✅ Final type detected → 25×25px")
            return (25, 25)
        elif 'decision' in type_lower or 'merge' in type_lower:
            if debug_enabled:
                log_debug(f"   ✅ Decision type detected → 40×40px")
            return (40, 40)
        elif 'fork' in type_lower or 'join' in type_lower:
            if debug_enabled:
                log_debug(f"   ✅ Fork/Join type detected → 100×10px")  # ← POŁOWA z 200×20
            return (100, 10)
        elif 'note' in type_lower or 'comment' in type_lower:
            if debug_enabled:
                log_debug(f"   ✅ Note/Comment type detected → 80×40px")
            return (80, 40)
        else:
            # ✅ ACTIVITY - prostokąt zależny od tekstu (ZMNIEJSZONE!)
            text_length = len(self.name) if self.name else 20
            
            if debug_enabled:
                log_debug(f"   📝 Activity node, text_length={text_length}")
            
            if text_length > 40:
                width, height = 148, 40  # ← POŁOWA z 296×80
                if debug_enabled:
                    log_debug(f"   ✅ Long text activity → {width}×{height}px")
            elif text_length > 25:
                width, height = 120, 40  # ← POŁOWA z 240×80
                if debug_enabled:
                    log_debug(f"   ✅ Medium text activity → {width}×{height}px")
            else:
                width, height = 100, 40  # ← POŁOWA z 200×80
                if debug_enabled:
                    log_debug(f"   ✅ Standard activity → {width}×{height}px")
            
            return (width, height)
        
        
    
    def _classify_role(self) -> str:
        """POPRAWIONA klasyfikacja używająca danych z parsera"""
        
        # ✅ UŻYWAJ DOKŁADNYCH TYPÓW Z PARSERA
        if self.type == 'control':
            # Sprawdź akcję dla węzłów kontrolnych
            action = getattr(self, 'action', self.name.lower())
            if action == 'start':
                return 'start'
            elif action in ['end', 'stop']:
                return 'end'
        
        # ✅ DOKŁADNE DOPASOWANIE TYPÓW DECYZJI
        elif self.type == 'decision_start':
            return 'decision'
        elif self.type == 'decision_else':
            return 'decision_else'  # OSOBNA KATEGORIA!
        elif self.type == 'decision_end':
            return 'decision_end'
        elif self.type == 'merge':
            return 'decision'
        
        # ✅ INNE TYPY
        elif self.type == 'note':
            return 'note'
        elif self.type == 'activity':
            # Sprawdź czy to błąd na podstawie tekstu
            if 'błąd' in self.name.lower() or 'error' in self.name.lower():
                return 'error'
            else:
                return 'activity'
        elif 'fork' in self.type:
            return 'fork'
        elif 'join' in self.type:
            return 'join'
        else:
            return 'activity'  # Fallback
    
    def add_successor(self, node: 'Node', label: str = ""):
        """Dodaj następnik z etykietą"""
        if node not in self.successors:
            self.successors.append(node)
        if self not in node.predecessors:
            node.predecessors.append(self)
    
    def __str__(self):
        return f"Node({self.id[-8:]}, {self.role}, L{self.layer}, {self.width}x{self.height})"
    
    def __repr__(self):
        return self.__str__()


class Edge:
    """Reprezentacja krawędzi grafu"""
    
    def __init__(self, source: Node, target: Node, label: str = "", condition: str = ""):
        self.source = source
        self.target = target
        self.label = label or condition
        self.is_virtual = False  # Czy przechodzi przez węzły wirtualne
        
        
    def __str__(self):
        return f"Edge({self.source.id[-6:]} → {self.target.id[-6:]}, '{self.label}')"


class Swimlane:
    """Reprezentacja toru/partycji"""
    
    def __init__(self, name: str, x_start: int = 0, width: int = 300):
        self.name = name
        self.x_start = x_start
        self.width = width
        self.nodes: List[Node] = []
    
    @property
    def x_end(self):
        return self.x_start + self.width


class GraphLayoutManager:
    """WŁASNY ALGORYTM SUGIYAMY - specjalnie dla diagramów aktywności UML"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        
        # Struktura grafu
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.swimlanes: Dict[str, Swimlane] = {}
        
        # Hierarchiczne warstwy
        self.layers: List[List[Node]] = []
        
        # Parametry layoutu
        self.canvas_width = 1600      # ← było 1400, zwiększone o 200px
        self.canvas_height = 1400     # ← było 1000, zwiększone o 400px
        self.margin_x = 120           # ← było 100, zwiększone o 20px
        self.margin_y = 100           # ← było 80, zwiększone o 20px
        self.layer_spacing = 100      # zmniejszone o połowę, by zagęścić warstwy pionowo
        self.node_spacing = 150   
        self.intra_lane_spacing = 80  # dodatkowy margines w obrębie jednego toru
        self.swimlane_gap = 100       # odstęp pomiędzy torami (≈ szerokość aktywności)
        
        # Wyniki
        self.element_positions = {}
        self._lane_layouts: Dict[str, int] = {}
    
    def analyze_diagram_structure(self, parsed_data):
        """🎯 GŁÓWNA METODA: Własny algorytm Sugiyamy krok po kroku"""
        
        try:
            if self.debug:
                log_debug("🚀 WŁASNY ALGORYTM SUGIYAMY - start!")
            
            # 🔧 KROK 1: Reprezentacja diagramu jako grafu
            self._build_graph_representation(parsed_data)
            
            # 🏗️ KROK 2: Przypisanie węzłów do warstw (Ranking)
            self._assign_nodes_to_layers()
            
            # ➕ KROK 2.5: Dodaj węzły wirtualne dla długich krawędzi
            self._insert_virtual_nodes()
            
            # 🔀 KROK 3: Minimalizacja przecięć krawędzi (Crossing Reduction)
            self._minimize_edge_crossings()
            
            # 📐 Dostosuj wymiary płótna do liczby warstw i szerokości torów
            self._adjust_canvas_dimensions()

            # 📍 KROK 4: Przypisanie współrzędnych (Coordinate Assignment)
            self._assign_coordinates()
            
            # 🎨 KROK 5: Optymalizacja dla swimlanes i UML
            self._optimize_for_activity_diagrams()
            
            # 📊 Tworzenie wyników
            grid_info = self._calculate_grid_info()
            
            if self.debug:
                log_debug(f"✅ Własny Sugiyama: {len(self.element_positions)} pozycji")
                log_debug(f"📊 Hierarchia: {len(self.layers)} warstw")
                log_debug(f"🏛️ Siatka: {grid_info['columns']} kolumn × {grid_info['rows']} rzędów")
            
            return self.element_positions, grid_info
            
        except Exception as e:
            log_error(f"❌ Błąd w własnym algorytmie Sugiyamy: {e}")
            return self._fallback_layout(parsed_data)
    
    # ===== 🔧 KROK 1: REPREZENTACJA GRAFU =====
    
    def _build_graph_representation(self, parsed_data):
        """Zbuduj matematyczną reprezentację grafu"""
        
        if self.debug:
            log_debug("🔧 KROK 1: Budowanie reprezentacji grafu")
        
        # 1A. Stwórz węzły
        flow_elements = parsed_data.get('flow', [])
        for element in flow_elements:
            node_id = element.get('id')
            node_type = element.get('type', 'activity')
            node_name = element.get('text', element.get('name', ''))
            swimlane = element.get('swimlane')
            
            if node_id:
                node = Node(node_id, node_type, node_name, swimlane)
            
                # ✅ USTAW WSZYSTKIE ATRYBUTY
                node.action = element.get('action')
                node.condition = element.get('condition')
                node.then_label = element.get('then_label')
                node.else_label = element.get('else_label')
                node.decision_id = element.get('decision_id')
                node.color = element.get('color')
                
                # ✅ KLUCZOWE: Aktualizuj role po ustawieniu action
                node.update_role_after_action()
                
                self.nodes[node_id] = node
                
                # Dodaj do swimlane jeśli istnieje
                if swimlane and swimlane not in self.swimlanes:
                    self.swimlanes[swimlane] = Swimlane(swimlane)
                if swimlane:
                    self.swimlanes[swimlane].nodes.append(node)
        
        # 1B. Stwórz krawędzie Z LOGICAL_CONNECTIONS
        connections = parsed_data.get('logical_connections', [])
        if not connections:
            connections = parsed_data.get('relationships', [])
        
        # ✅ UNIKAJ DUPLIKATÓW - śledź już dodane połączenia
        added_edges = set()
        
        for conn in connections:
            source_id = conn.get('source_id') or conn.get('from')
            target_id = conn.get('target_id') or conn.get('to')
            label = conn.get('label', conn.get('condition', ''))
            
            # ✅ KLUCZOWE: Sprawdź duplikaty
            edge_key = (source_id, target_id, label)
            if edge_key in added_edges:
                continue  # Pomiń duplikat
            
            if source_id in self.nodes and target_id in self.nodes:
                source_node = self.nodes[source_id]
                target_node = self.nodes[target_id]
                
                edge = Edge(source_node, target_node, label)
                self.edges.append(edge)
                
                source_node.add_successor(target_node, label)
                added_edges.add(edge_key)  # Oznacz jako dodane
        
        # 1C. NAPRAWIONE: Połącz decision_start z decision_else (BEZ DUPLIKATÓW)
        decision_mapping = {}
        
        # Mapuj decision_else do ich decision_start
        for element in flow_elements:
            if element.get('type') == 'decision_else':
                decision_id = element.get('decision_id')
                if decision_id and decision_id not in decision_mapping:  # ✅ UNIKAJ DUPLIKATÓW
                    decision_mapping[element.get('id')] = decision_id
        
        # ✅ DODAJ UNIKALNE POŁĄCZENIA decision_start → decision_else
        for else_id, start_id in decision_mapping.items():
            edge_key = (start_id, else_id, "nie")
            if edge_key not in added_edges and else_id in self.nodes and start_id in self.nodes:
                start_node = self.nodes[start_id]
                else_node = self.nodes[else_id]
                
                # Dodaj krawędź "nie"
                edge = Edge(start_node, else_node, "nie")
                self.edges.append(edge)
                start_node.add_successor(else_node, "nie")
                added_edges.add(edge_key)
                
                if self.debug:
                    log_debug(f"   🔗 Połączono decision: {start_id[-6:]} → {else_id[-6:]} [nie]")

        if self.debug:
            log_debug(f"   📊 Reprezentacja: {len(self.nodes)} węzłów, {len(self.edges)} krawędzi")
            log_debug(f"   🏊 Swimlanes: {len(self.swimlanes)} torów")
            log_debug(f"   🔗 Dodano {len(decision_mapping)} UNIKALNYCH połączeń decision")
    
    # ===== 🏗️ KROK 2: PRZYPISANIE DO WARSTW =====

    def _assign_nodes_to_layers(self):
        """NAPRAWIONA metoda przypisania węzłów do warstw używając BFS"""
        
        if self.debug:
            log_debug("🏗️ KROK 2: NAPRAWIONE przypisanie węzłów do warstw (Ranking)")
        
        # ✅ RESETUJ wszystkie węzły
        for node in self.nodes.values():
            node.layer = -1  # Oznacz jako nieprzypisany
        
        # ✅ KROK 2A: ZNAJDŹ PRAWDZIWE START WĘZŁY
        start_nodes = []
        
        # PRIORYTET 1: control + action=start
        for node in self.nodes.values():
            if (node.type == 'control' and 
                hasattr(node, 'action') and 
                node.action == 'start'):
                start_nodes.append(node)
                if self.debug:
                    log_debug(f"   🏁 START przez action: {node.id[-8:]} (type={node.type}, action={node.action})")
        
        # PRIORYTET 2: role=start
        if not start_nodes:
            for node in self.nodes.values():
                if node.role == 'start':
                    start_nodes.append(node)
                    if self.debug:
                        log_debug(f"   🏁 START przez role: {node.id[-8:]} (role={node.role})")
        
        # PRIORYTET 3: Węzły bez poprzedników (ale nie decision_else/note!)
        if not start_nodes:
            for node in self.nodes.values():
                if (not node.predecessors and 
                    node.type not in ['decision_else', 'note', 'decision_end', 'merge'] and
                    'else' not in node.type):
                    start_nodes.append(node)
                    if self.debug:
                        log_debug(f"   🏁 START przez brak poprzedników: {node.id[-8:]} (type={node.type})")
        
        # EMERGENCY FALLBACK
        if not start_nodes and self.nodes:
            first_node = list(self.nodes.values())[0]
            start_nodes = [first_node]
            log_warning(f"⚠️ EMERGENCY: Używam pierwszego węzła jako START: {first_node.id[-8:]}")
        
        if self.debug:
            log_debug(f"   🏁 FINALNE START węzły: {[n.id[-8:] for n in start_nodes]}")
        
        # ✅ KROK 2B: MULTI-SOURCE BFS (wszystkie start_nodes jednocześnie)
        queue = deque([(node, 0) for node in start_nodes])
        visited = set()
        layers_dict = {}  # node_id -> layer
        
        # Ustaw START węzły na warstwę 0
        for start_node in start_nodes:
            start_node.layer = 0
            visited.add(start_node)
            layers_dict[start_node.id] = 0
        
        processed_count = 0
        
        while queue and processed_count < 200:  # Zabezpieczenie przed nieskończoną pętlą
            current_node, current_layer = queue.popleft()
            processed_count += 1
            
            if self.debug and processed_count <= 8:
                log_debug(f"      {processed_count:2d}. Przetwarzam {current_node.role}:{current_node.id[-6:]} na warstwie {current_layer}")
            
            # Sprawdź wszystkich następników
            for successor in current_node.successors:
                next_layer = current_layer + 1
                
                if successor.id not in layers_dict:
                    # Pierwszy raz widzimy ten węzeł
                    successor.layer = next_layer
                    layers_dict[successor.id] = next_layer
                    visited.add(successor)
                    queue.append((successor, next_layer))
                    
                    if self.debug and processed_count <= 8:
                        log_debug(f"         ↳ Nowy następnik: {successor.role}:{successor.id[-6:]} → warstwa {next_layer}")
                    
                else:
                    # Węzeł już był odwiedzony - sprawdź czy trzeba go przesunąć dalej
                    existing_layer = layers_dict[successor.id]
                    if existing_layer < next_layer:
                        successor.layer = next_layer
                        layers_dict[successor.id] = next_layer
                        queue.append((successor, next_layer))
                        
                        if self.debug and processed_count <= 8:
                            log_debug(f"         ↳ Przesuwam następnik: {successor.role}:{successor.id[-6:]} z L{existing_layer} → L{next_layer}")
        
        # ✅ KROK 2C: ZNAJDŹ WĘZŁY KTÓRE NIE ZOSTAŁY PRZYPISANE
        unassigned = [node for node in self.nodes.values() if node.layer == -1]
        flow_unassigned = [node for node in unassigned if node.role not in ('note', 'comment')]

        if flow_unassigned:
            if self.debug:
                log_warning(f"⚠️ {len(flow_unassigned)} węzłów nie zostało osiągniętych przez BFS:")
                for node in flow_unassigned[:5]:
                    preds = [p.id[-6:] for p in node.predecessors[:3]]
                    succs = [s.id[-6:] for s in node.successors[:3]]
                    log_debug(f"      {node.role}:{node.id[-6:]} (pred:{preds}, succ:{succs})")

            # Przypisz nieosiągnięte węzły do kolejnych warstw
            max_assigned_layer = max(n.layer for n in self.nodes.values() if n.layer != -1) if layers_dict else 0
            
            for i, node in enumerate(unassigned):
                node.layer = max_assigned_layer + 1 + i
                layers_dict[node.id] = node.layer
        
        # ✅ KROK 2D: ZORGANIZUJ WARSTWY
        if layers_dict:
            max_layer = max(layers_dict.values())
            self.layers = [[] for _ in range(max_layer + 1)]
            
            for node in self.nodes.values():
                if 0 <= node.layer <= max_layer:
                    self.layers[node.layer].append(node)
        else:
            self.layers = [[]]
            log_warning("⚠️ Nie utworzono żadnych warstw!")
        
        # ✅ KROK 2E: FORCE END węzły na ostatnią warstwę
        end_nodes = [node for node in self.nodes.values() if node.role == 'end']
        if end_nodes and len(self.layers) > 1:
            last_layer = len(self.layers) - 1
            moves = 0
            
            for end_node in end_nodes:
                if end_node.layer != last_layer:
                    # Usuń z obecnej warstwy
                    if end_node in self.layers[end_node.layer]:
                        self.layers[end_node.layer].remove(end_node)
                    
                    # Dodaj do ostatniej warstwy
                    end_node.layer = last_layer
                    if end_node not in self.layers[last_layer]:
                        self.layers[last_layer].append(end_node)
                    moves += 1
            
            if self.debug and moves > 0:
                log_debug(f"   🏁 Przesunięto {moves} węzłów END na ostatnią warstwę")

        # ✅ KROK 2E.5: SKOMPRESUJ PUSTE WARSTWY
        self._compress_layers()
        
        # ✅ KROK 2F: FINALNE STATYSTYKI
        total_assigned = sum(len(layer) for layer in self.layers)
        
        if self.debug:
            log_debug(f"   📊 WYNIK: Utworzono {len(self.layers)} warstw dla {total_assigned}/{len(self.nodes)} węzłów")
            
            for i, layer_nodes in enumerate(self.layers):
                if layer_nodes:
                    roles = [f"{n.role}:{n.id[-4:]}" for n in layer_nodes[:4]]
                    if len(layer_nodes) > 4:
                        roles.append(f"...+{len(layer_nodes)-4}")
                    log_debug(f"      Warstwa {i}: {len(layer_nodes)} węzłów - {roles}")
            
            # Weryfikacja hierarchii
            start_layers = [n.layer for n in self.nodes.values() if n.role == 'start']
            end_layers = [n.layer for n in self.nodes.values() if n.role == 'end']
            
            if start_layers and end_layers:
                min_start, max_start = min(start_layers), max(start_layers)
                min_end, max_end = min(end_layers), max(end_layers)
                log_debug(f"   ⭐ Hierarchia: START L{min_start}-{max_start}, END L{min_end}-{max_end}")
                
                if min_start >= min_end:
                    log_warning("⚠️ UWAGA: START nie jest przed END!")
                else:
                    log_debug("   ✅ Hierarchia START→END jest poprawna")
            
            assigned_ids = {node.id for layer in self.layers for node in layer}
            missing_nodes = [node for node in self.nodes.values() if node.id not in assigned_ids and node.role not in ('note', 'comment')]

            if missing_nodes:
                log_warning(f"⚠️ UWAGA: {len(missing_nodes)} węzłów nie zostało przypisanych do warstw!")
        
    # ===== ➕ KROK 2.5: WĘZŁY WIRTUALNE =====

    def _compress_layers(self):
        """Usuń puste warstwy i zbij indeksy, by uniknąć sztucznego rozciągania osi Y."""

        if not self.layers:
            self.layers = [[]]
            return

        new_layers = []
        removed = 0

        for idx, layer in enumerate(self.layers):
            if not layer:
                removed += 1
                continue

            new_index = len(new_layers)
            for node in layer:
                node.layer = new_index
            new_layers.append(layer)

        if not new_layers:
            self.layers = [[]]
            return

        if removed and self.debug:
            log_debug(f"   📏 Skompresowano warstwy: -{removed} pustych")

        self.layers = new_layers
    
    def _insert_virtual_nodes(self):
        """Dodaj wirtualne węzły dla krawędzi przechodzących przez wiele warstw"""
        
        if self.debug:
            log_debug("➕ KROK 2.5: Wstawianie węzłów wirtualnych")
        
        edges_to_virtualize = []
        
        # Znajdź krawędzie przechodzące przez więcej niż jedną warstwę
        for edge in self.edges[:]:  # ✅ SKOPIUJ listę żeby uniknąć modyfikacji podczas iteracji
            layer_diff = edge.target.layer - edge.source.layer
            if layer_diff > 1:
                edges_to_virtualize.append(edge)
        
        virtual_node_counter = 0
        
        for edge in edges_to_virtualize:
            source = edge.source
            target = edge.target
            label = edge.label
            
            # ✅ SPRAWDŹ czy krawędź nadal istnieje przed usunięciem
            if edge in self.edges:
                # Usuń oryginalną krawędź
                self.edges.remove(edge)
                
                # Usuń z węzłów tylko jeśli istnieją
                if target in source.successors:
                    source.successors.remove(target)
                if source in target.predecessors:
                    target.predecessors.remove(source)
                
                # Reszta kodu bez zmian...
                current_node = source
                
                for layer in range(source.layer + 1, target.layer):
                    virtual_id = f"virtual_{virtual_node_counter}"
                    virtual_node = Node(virtual_id, "virtual", "", source.swimlane)
                    virtual_node.is_virtual = True
                    virtual_node.layer = layer
                    virtual_node.width = 10
                    virtual_node.height = 10
                    
                    self.nodes[virtual_id] = virtual_node
                    
                    # ✅ BEZPIECZNE DODANIE do warstwy
                    if layer < len(self.layers):
                        self.layers[layer].append(virtual_node)
                    
                    virtual_edge = Edge(current_node, virtual_node)
                    self.edges.append(virtual_edge)
                    current_node.add_successor(virtual_node)
                    
                    current_node = virtual_node
                    virtual_node_counter += 1
                
                # Połącz ostatni wirtualny węzeł z celem
                final_edge = Edge(current_node, target, label)
                self.edges.append(final_edge)
                current_node.add_successor(target, label)
        
        if self.debug and edges_to_virtualize:
            log_debug(f"   ➕ Dodano {virtual_node_counter} węzłów wirtualnych dla {len(edges_to_virtualize)} krawędzi")
    
    # ===== 🔀 KROK 3: MINIMALIZACJA PRZECIĘĆ =====
    
    def _minimize_edge_crossings(self):
        """Minimalizuj przecięcia krawędzi metodą barycentrum"""
        
        if self.debug:
            log_debug("🔀 KROK 3: Minimalizacja przecięć krawędzi")
        
        iterations = 5  # Liczba iteracji optymalizacji
        
        for iteration in range(iterations):
            improved = False
            
            # 3A. W dół - optymalizuj na podstawie poprzedników
            for layer_idx in range(1, len(self.layers)):
                layer = self.layers[layer_idx]
                
                # Oblicz barycenter dla każdego węzła
                for node in layer:
                    if node.predecessors:
                        positions = [pred.position_in_layer for pred in node.predecessors]
                        node.barycenter = sum(positions) / len(positions)
                    else:
                        node.barycenter = node.position_in_layer
                
                # Sortuj węzły według barycenter
                old_order = [(node.position_in_layer, node.id) for node in layer]
                layer.sort(key=lambda n: n.barycenter)
                
                # Zaktualizuj pozycje w warstwie
                for i, node in enumerate(layer):
                    node.position_in_layer = i
                
                new_order = [(node.position_in_layer, node.id) for node in layer]
                if old_order != new_order:
                    improved = True
            
            # 3B. W górę - optymalizuj na podstawie następników
            for layer_idx in range(len(self.layers) - 2, -1, -1):
                layer = self.layers[layer_idx]
                
                # Oblicz barycenter dla każdego węzła
                for node in layer:
                    if node.successors:
                        positions = [succ.position_in_layer for succ in node.successors]
                        node.barycenter = sum(positions) / len(positions)
                    else:
                        node.barycenter = node.position_in_layer
                
                # Sortuj węzły według barycenter
                layer.sort(key=lambda n: n.barycenter)
                
                # Zaktualizuj pozycje w warstwie
                for i, node in enumerate(layer):
                    node.position_in_layer = i
            
            if not improved:
                break
        
        if self.debug:
            log_debug(f"   🔀 Minimalizacja przecięć: {iterations} iteracji")
    
    # ===== 📍 KROK 4: PRZYPISANIE WSPÓŁRZĘDNYCH =====

    def _adjust_canvas_dimensions(self):
        """Dopasuj dynamicznie wielkość płótna do liczby warstw i kolumn."""

        visible_nodes = [node for node in self.nodes.values() if not node.is_virtual]

        # Dostosuj wysokość do liczby warstw
        valid_layers = [node.layer for node in visible_nodes if isinstance(node.layer, int) and node.layer >= 0]
        if valid_layers:
            max_layer_index = max(valid_layers)
            max_node_height = max((node.height for node in visible_nodes), default=40)
            required_height = (
                2 * self.margin_y
                + max_layer_index * self.layer_spacing
                + max_node_height
            )
            if required_height > self.canvas_height:
                self.canvas_height = required_height

        # Dostosuj szerokość do liczby kolumn (swimlanes lub węzły w warstwie)
        if self.swimlanes:
            lane_padding = 40
            min_lane_width = 240
            lane_layouts: Dict[str, int] = {}

            for name, swimlane in self.swimlanes.items():
                lane_nodes = [node for node in swimlane.nodes if not node.is_virtual and isinstance(node.layer, int) and node.layer >= 0]
                if not lane_nodes:
                    lane_layouts[name] = min_lane_width
                    continue

                per_layer_widths: Dict[int, int] = defaultdict(int)
                per_layer_counts: Dict[int, int] = defaultdict(int)
                for node in lane_nodes:
                    per_layer_widths[node.layer] += node.width
                    per_layer_counts[node.layer] += 1

                max_layer_width = 0
                for layer in per_layer_widths:
                    count = per_layer_counts[layer]
                    span = per_layer_widths[layer] + self.intra_lane_spacing * max(0, count - 1)
                    if span > max_layer_width:
                        max_layer_width = span

                max_node_width = max(node.width for node in lane_nodes)
                base_width = max(max_node_width, max_layer_width)
                lane_required = max(min_lane_width, base_width + 2 * lane_padding)
                lane_layouts[name] = lane_required

            total_width = 2 * self.margin_x
            lane_names = list(self.swimlanes.keys())
            for idx, name in enumerate(lane_names):
                total_width += lane_layouts.get(name, min_lane_width)
                if idx < len(lane_names) - 1:
                    total_width += self.swimlane_gap

            if total_width > self.canvas_width:
                self.canvas_width = total_width

            self._lane_layouts = lane_layouts
        else:
            layer_widths = []
            for layer in self.layers:
                layer_nodes = [node for node in layer if not node.is_virtual]
                if not layer_nodes:
                    continue

                total_node_width = sum(node.width for node in layer_nodes)
                spacing_width = self.node_spacing * max(0, len(layer_nodes) - 1)
                layer_widths.append(total_node_width + spacing_width)

            if layer_widths:
                required_width = 2 * self.margin_x + max(layer_widths)
                if required_width > self.canvas_width:
                    self.canvas_width = required_width

            self._lane_layouts = {}
    
    def _assign_coordinates(self):
        """Przypisz współrzędne - z obsługą swimlanes"""
        
        if self.swimlanes:
            self._assign_coordinates_with_swimlanes()
        else:
            self._assign_coordinates_simple()

    def _assign_coordinates_simple(self):
        """Proste przypisanie współrzędnych bez swimlanes"""
        
        if self.debug:
            log_debug("📍 KROK 4: Przypisanie współrzędnych (bez swimlanes)")
        
        usable_width = self.canvas_width - 2 * self.margin_x
        
        # Y dla warstw
        for layer_idx, layer in enumerate(self.layers):
            y = self.margin_y + layer_idx * self.layer_spacing
            
            for node in layer:
                node.y = y
        
        # X w warstwach
        for layer in self.layers:
            if not layer:
                continue
            
            if len(layer) == 1:
                layer[0].x = self.canvas_width // 2
            else:
                # Rozłóż równomiernie
                total_width = sum(node.width for node in layer)
                available_space = usable_width - total_width
                
                if available_space > 0:
                    spacing = available_space / (len(layer) + 1)
                    current_x = self.margin_x + spacing
                else:
                    # Minimalne odstępy
                    spacing = 50
                    current_x = self.margin_x
                
                for node in layer:
                    node.x = current_x + node.width // 2
                    current_x += node.width + spacing

    def _assign_coordinates_with_swimlanes(self):
        """NOWA metoda przypisania współrzędnych Z OBSŁUGĄ SWIMLANES"""
        
        if self.debug:
            log_debug("📍 KROK 4: Przypisanie współrzędnych z swimlanes")
        
        # Konfiguracja swimlanes
        num_swimlanes = len(self.swimlanes)
        if num_swimlanes == 0:
            return self._assign_coordinates_simple()
        
        lane_names = list(self.swimlanes.keys())
        lane_layouts = self._lane_layouts or {}
        swimlane_width = (self.canvas_width - 2 * self.margin_x) // num_swimlanes
        swimlane_margin = 20  # Margines wewnętrzny toru
        
        # Przypisz pozycje X dla swimlanes
        swimlane_positions = {}
        current_x = self.margin_x
        
        for idx, (name, swimlane) in enumerate(self.swimlanes.items()):
            lane_width = lane_layouts.get(name, swimlane_width)
            swimlane_positions[name] = {
                'x_start': current_x,
                'x_center': current_x + lane_width / 2,
                'x_end': current_x + lane_width,
                'width': lane_width,
                'content_width': lane_width - 2 * swimlane_margin
            }
            current_x += lane_width
            if idx < num_swimlanes - 1:
                current_x += self.swimlane_gap
            
            if self.debug:
                log_debug(f"   🏊 Tor '{name}': x={current_x-swimlane_width}-{current_x}, width={swimlane_width}")
        
        # Przypisz Y dla warstw (jak w simple)
        for layer_idx, layer in enumerate(self.layers):
            y = self.margin_y + layer_idx * self.layer_spacing
            
            for node in layer:
                node.y = y
        
        # Przypisz X dla węzłów w torach
        for layer_idx, layer in enumerate(self.layers):
            if not layer:
                continue
            
            # Grupuj węzły według swimlanes
            nodes_by_swimlane = {}
            nodes_without_swimlane = []
            
            for node in layer:
                swimlane = node.swimlane
                if swimlane and swimlane in swimlane_positions:
                    if swimlane not in nodes_by_swimlane:
                        nodes_by_swimlane[swimlane] = []
                    nodes_by_swimlane[swimlane].append(node)
                else:
                    nodes_without_swimlane.append(node)
            
            if self.debug and layer_idx < 3:
                log_debug(f"   📍 Warstwa {layer_idx}: {len(nodes_by_swimlane)} torów, {len(nodes_without_swimlane)} bez toru")
            
            # Pozycjonuj węzły w każdym torze
            for swimlane_name, nodes in nodes_by_swimlane.items():
                pos = swimlane_positions[swimlane_name]
                
                if len(nodes) == 1:
                    # Pojedynczy węzeł - wyśrodkuj w torze
                    nodes[0].x = pos['x_center']
                else:
                    # Wiele węzłów - rozłóż w torze
                    total_width = sum(node.width for node in nodes)
                    available_width = pos['content_width']
                    
                    if total_width <= available_width:
                        free_space = max(0, available_width - total_width)
                        spacing = min(self.intra_lane_spacing, free_space // (len(nodes) + 1))
                        start_x = pos['x_start'] + swimlane_margin + (available_width - total_width - spacing * (len(nodes) - 1)) / 2
                    else:
                        spacing = max(10, self.intra_lane_spacing // 2)
                        start_x = pos['x_start'] + swimlane_margin
                    
                    current_x = start_x
                    for node in nodes:
                        node.x = current_x + node.width / 2
                        current_x += node.width + spacing
            
            # Węzły bez toru - umieść na prawej stronie
            if nodes_without_swimlane:
                rightmost_x = max(swimlane_positions.values(), key=lambda p: p['x_end'])['x_end'] + 50
                
                for i, node in enumerate(nodes_without_swimlane):
                    node.x = rightmost_x + i * 200
        
        # Korekty – upewnij się, że wszystkie węzły mieszczą się w swoich torach
        for swimlane_name, pos in swimlane_positions.items():
            lane_nodes = [node for node in self.nodes.values() if node.swimlane == swimlane_name and not node.is_virtual]
            for node in lane_nodes:
                min_x = pos['x_start'] + swimlane_margin + node.width / 2
                max_x = pos['x_end'] - swimlane_margin - node.width / 2
                if max_x <= min_x:
                    node.x = pos['x_center']
                else:
                    node.x = max(min_x, min(node.x, max_x))

        if self.debug:
            log_debug(f"   📍 Przypisano współrzędne dla {num_swimlanes} torów")
            
            # Debug przykładów
            for i, layer in enumerate(self.layers[:2]):
                for node in layer[:2]:
                    swimlane = f"[{node.swimlane}]" if node.swimlane else "[no-lane]"
                    log_debug(f"      {node.role} {swimlane}: ({node.x:.0f}, {node.y:.0f})")
    
    # ===== 🎨 KROK 5: OPTYMALIZACJA UML =====
    
    def _optimize_for_activity_diagrams(self):
        """POPRAWIONA optymalizacja dla diagramów aktywności UML"""
        
        if self.debug:
            log_debug("🎨 KROK 5: Optymalizacje dla diagramów aktywności")
        
        # 5A. ✅ SILNE WYMUSZENIE: START na warstwę 0, END na ostatnią
        start_nodes = [node for node in self.nodes.values() if node.role == 'start']
        end_nodes = [node for node in self.nodes.values() if node.role == 'end']
        
        if start_nodes:
            for start_node in start_nodes:
                if start_node.layer != 0 and len(self.layers) > 0:
                    # Usuń z obecnej warstwy
                    if start_node in self.layers[start_node.layer]:
                        self.layers[start_node.layer].remove(start_node)
                    
                    # Dodaj na początek warstwy 0
                    start_node.layer = 0
                    if start_node not in self.layers[0]:
                        self.layers[0].insert(0, start_node)
                    
                    # Ustaw Y na górze
                    start_node.y = self.margin_y
                    
                    if self.debug:
                        log_debug(f"   🏁 FORCE START {start_node.id[-6:]} → warstwa 0")
        
        if end_nodes and len(self.layers) > 1:
            last_layer = len(self.layers) - 1
            
            for end_node in end_nodes:
                if end_node.layer != last_layer:
                    # Usuń z obecnej warstwy
                    if end_node in self.layers[end_node.layer]:
                        self.layers[end_node.layer].remove(end_node)
                    
                    # Dodaj na koniec ostatniej warstwy
                    end_node.layer = last_layer
                    if end_node not in self.layers[last_layer]:
                        self.layers[last_layer].append(end_node)
                    
                    # Ustaw Y na dole
                    end_node.y = self.margin_y + last_layer * self.layer_spacing
                    
                    if self.debug:
                        log_debug(f"   🏁 FORCE END {end_node.id[-6:]} → warstwa {last_layer}")
        
        # 5B. Konwersja do element_positions
        self.element_positions = {}
        
        nodes_processed = 0
        for node in self.nodes.values():
            if not node.is_virtual:  # Pomiń węzły wirtualne
                # Pozycja lewego górnego rogu (standard XMI)
                x_final = int(node.x - node.width // 2)
                y_final = int(node.y - node.height // 2)
                
                # Upewnij się że mieści się w canvas
                x_final = max(self.margin_x, 
                            min(x_final, self.canvas_width - node.width - self.margin_x))
                y_final = max(self.margin_y, 
                            min(y_final, self.canvas_height - node.height - self.margin_y))
                
                self.element_positions[node.id] = {
                    'x': x_final,
                    'y': y_final,
                    'width': node.width,
                    'height': node.height,
                    'column': int(x_final // (self.canvas_width // 8)),  # 8 kolumn
                    'row': int(node.layer),  # Użyj layer jako row
                    'layer': node.layer,
                    'role': node.role
                }
                
                nodes_processed += 1
                
                if self.debug and nodes_processed <= 5:
                    log_debug(f"      Position {nodes_processed}: {node.role}:{node.id[-6:]} → ({x_final}, {y_final}) L{node.layer}")
        
        if self.debug:
            log_debug(f"   🎨 Element_positions: {len(self.element_positions)}/{len(self.nodes)} elementów")
            
            # Weryfikacja końcowych pozycji
            start_positions = [(p['y'], node_id) for node_id, p in self.element_positions.items() 
                            if self.nodes[node_id].role == 'start']
            end_positions = [(p['y'], node_id) for node_id, p in self.element_positions.items() 
                            if self.nodes[node_id].role == 'end']
            
            if start_positions and end_positions:
                min_start_y = min(start_positions)[0]
                max_end_y = max(end_positions)[0]
                log_debug(f"   ⭐ FINALNE pozycje Y: START={min_start_y}, END={max_end_y}")
                
                if min_start_y >= max_end_y:
                    log_warning("⚠️ UWAGA: START nadal nie jest nad END!")
                else:
                    log_debug("   ✅ Hierarchia START→END NAPRAWIONA")
    
    def _optimize_swimlanes(self):
        """Optymalizuj pozycje dla swimlanes/partycji"""
        
        if not self.swimlanes:
            return
        
        # Przypisz szerokość każdej swimlane
        swimlane_width = (self.canvas_width - 2 * self.margin_x) // len(self.swimlanes)
        current_x = self.margin_x
        
        for swimlane_name, swimlane in self.swimlanes.items():
            swimlane.x_start = current_x
            swimlane.width = swimlane_width
            
            # Przesuń wszystkie węzły do granic swimlane
            for node in swimlane.nodes:
                # Upewnij się że węzeł mieści się w swimlane
                min_x = swimlane.x_start + node.width // 2
                max_x = swimlane.x_start + swimlane.width - node.width // 2
                node.x = max(min_x, min(node.x, max_x))
            
            current_x += swimlane_width
        
        if self.debug:
            log_debug(f"   🏊 Swimlanes: {len(self.swimlanes)} torów @ {swimlane_width}px każdy")
    
    # ===== 📊 POMOCNICZE METODY =====
    
    def _calculate_grid_info(self):
        """Oblicz informacje o siatce"""
        
        if not self.element_positions:
            return {'columns': 1, 'rows': 1, 'width': self.canvas_width, 'height': self.canvas_height}
        
        x_positions = set()
        y_positions = set()
        
        for pos in self.element_positions.values():
            # Grupuj podobne pozycje (tolerancja 50px)
            x_group = (pos['x'] // 50) * 50
            y_group = (pos['y'] // 50) * 50
            x_positions.add(x_group)
            y_positions.add(y_group)
        
        max_x = max(pos['x'] + pos['width'] for pos in self.element_positions.values())
        max_y = max(pos['y'] + pos['height'] for pos in self.element_positions.values())
        
        return {
            'columns': len(x_positions),
            'rows': len(y_positions),
            'width': min(max_x + self.margin_x, self.canvas_width),
            'height': min(max_y + self.margin_y, self.canvas_height)
        }
    
    def _fallback_layout(self, parsed_data):
        """Fallback - prosty layout pionowy"""
        
        positions = {}
        
        for i, element in enumerate(parsed_data.get('flow', [])):
            node_id = element.get('id')
            if node_id:
                positions[node_id] = {
                    'x': 600,
                    'y': 100 + i * 120,
                    'width': 160,
                    'height': 70,
                    'column': 1,
                    'row': i,
                    'layer': i,
                    'role': 'activity'
                }
        
        self.element_positions = positions
        return positions, {'columns': 1, 'rows': len(positions), 'width': 1400, 'height': 1000}
    
    # ===== KOMPATYBILNOŚĆ Z ISTNIEJĄCYM KODEM =====
    
    def update_swimlane_geometry(self):
        """Placeholder dla kompatybilności"""
        pass
    
    @property
    def swimlanes_geometry(self):
        return getattr(self, '_swimlanes_geometry', {})
    
    @swimlanes_geometry.setter
    def swimlanes_geometry(self, value):
        self._swimlanes_geometry = value
