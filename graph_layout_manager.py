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
            elif self.role in ['decision', 'decision_start']:
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
        elif 'decision' in type_lower:
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
        self.canvas_width = 1400
        self.canvas_height = 1000
        self.margin_x = 100
        self.margin_y = 80
        self.layer_spacing = 120  # Odstęp między warstwami
        self.node_spacing = 80    # Minimalny odstęp między węzłami
        
        # Wyniki
        self.element_positions = {}
    
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
        
        # 1B. Stwórz krawędzie
        connections = parsed_data.get('logical_connections', [])
        if not connections:
            connections = parsed_data.get('relationships', [])
        
        for conn in connections:
            source_id = conn.get('source_id') or conn.get('from')
            target_id = conn.get('target_id') or conn.get('to')
            label = conn.get('label', conn.get('condition', ''))
            
            if source_id in self.nodes and target_id in self.nodes:
                source_node = self.nodes[source_id]
                target_node = self.nodes[target_id]
                
                edge = Edge(source_node, target_node, label)
                self.edges.append(edge)
                
                source_node.add_successor(target_node, label)
        
            # 1C. NOWE: Połącz decision_start z decision_else
            decision_mapping = {}
            
            # Mapuj decision_else do ich decision_start
            for element in flow_elements:
                if element.get('type') == 'decision_else':
                    decision_id = element.get('decision_id')
                    if decision_id:
                        decision_mapping[element.get('id')] = decision_id
            
            # Dodaj połączenia decision_start → decision_else
            for else_id, start_id in decision_mapping.items():
                if else_id in self.nodes and start_id in self.nodes:
                    start_node = self.nodes[start_id]
                    else_node = self.nodes[else_id]
                    
                    # Dodaj krawędź "nie"
                    edge = Edge(start_node, else_node, "nie")
                    self.edges.append(edge)
                    start_node.add_successor(else_node, "nie")
                    
                    if self.debug:
                        log_debug(f"   🔗 Połączono decision: {start_id[-6:]} → {else_id[-6:]} [nie]")

        if self.debug:
            log_debug(f"   📊 Reprezentacja: {len(self.nodes)} węzłów, {len(self.edges)} krawędzi")
            log_debug(f"   🏊 Swimlanes: {len(self.swimlanes)} torów")
            log_debug(f"   🔗 Dodano {len(decision_mapping)} połączeń decision")
    
    # ===== 🏗️ KROK 2: PRZYPISANIE DO WARSTW =====
    
    def _assign_nodes_to_layers(self):
        """Przypisanie węzłów do warstw używając danych parsera"""
        
        if self.debug:
            log_debug("🏗️ KROK 2: POPRAWIONE przypisanie węzłów do warstw (Ranking)")
        
        # ✅ KROK 2A: DOKŁADNA DETEKCJA START WĘZŁÓW
        start_nodes = []
        
        # PRIORYTET 1: control + action=start (prawdziwy START)
        for node in self.nodes.values():
            if (node.type == 'control' and 
                hasattr(node, 'action') and 
                node.action == 'start' and 
                node.role == 'start'):
                start_nodes.append(node)
        
        # PRIORYTET 2: Węzły bez poprzedników (ale NIE decision_else/note!)
        if not start_nodes:
            for node in self.nodes.values():
                if (not node.predecessors and 
                    node.role not in ['decision_else', 'note', 'decision_end'] and
                    'else' not in node.type and
                    'note' not in node.type):
                    start_nodes.append(node)
        
        # FALLBACK: pierwszy węzeł (jeśli nie jest problematyczny)
        if not start_nodes and self.nodes:
            first_node = list(self.nodes.values())[0]
            if first_node.role not in ['decision_else', 'note']:
                start_nodes = [first_node]
        
        if self.debug:
            log_debug(f"   🏁 POPRAWIONE START węzły: {[n.id[-8:] for n in start_nodes]}")
            log_debug(f"   🏁 Ich typy/akcje: {[(n.type, getattr(n, 'action', 'N/A'), n.role) for n in start_nodes]}")
            
            # DEBUG: Pokaż wszystkie węzły control dla diagnostyki
            control_nodes = [n for n in self.nodes.values() if n.type == 'control']
            log_debug(f"   🔍 Wszystkie węzły control ({len(control_nodes)}):")
            for node in control_nodes[:5]:  # Pokaż maksymalnie 5
                action = getattr(node, 'action', 'N/A')
                log_debug(f"      {node.id[-8:]}: type={node.type}, action={action}, role={node.role}")
            
            # DEBUG: Pokaż problematyczne węzły które NIE są START
            non_start_roles = ['decision_else', 'note', 'decision_end']
            problematic = [n for n in self.nodes.values() if n.role in non_start_roles]
            if problematic:
                log_debug(f"   🚫 Węzły wykluczone z START ({len(problematic)}):")
                for node in problematic[:3]:
                    log_debug(f"      {node.id[-8:]}: type={node.type}, role={node.role}")
        
        # Sprawdź czy mamy prawidłowe START węzły
        if not start_nodes:
            log_warning("⚠️ Nie znaleziono prawidłowych węzłów START! Używam fallback.")
            # Emergency fallback - pierwszy dostępny węzeł
            if self.nodes:
                start_nodes = [list(self.nodes.values())[0]]
        
        # ✅ KROK 2B: BFS dla przypisania warstw
        queue = deque([(node, 0) for node in start_nodes])
        visited = set()
        nodes_processed = 0
        
        while queue:
            current_node, layer = queue.popleft()
            
            if current_node in visited:
                # Jeśli węzeł już był odwiedzony, sprawdź czy należy go przesunąć do późniejszej warstwy
                if current_node.layer < layer:
                    if self.debug and nodes_processed < 10:  # Debug pierwszych 10
                        log_debug(f"      🔄 Przesuwam {current_node.role}:{current_node.id[-6:]} z L{current_node.layer} → L{layer}")
                    current_node.layer = layer
                continue
            
            visited.add(current_node)
            current_node.layer = layer
            nodes_processed += 1
            
            if self.debug and nodes_processed <= 5:  # Debug pierwszych 5 węzłów
                log_debug(f"      ✅ {current_node.role}:{current_node.id[-6:]} → warstwa {layer}")
            
            # Dodaj następników do kolejnej warstwy
            successors_added = 0
            for successor in current_node.successors:
                if successor not in visited:
                    queue.append((successor, layer + 1))
                    successors_added += 1
                else:
                    # Upewnij się że następnik jest w późniejszej warstwie
                    if successor.layer <= layer:
                        successor.layer = layer + 1
                        queue.append((successor, layer + 1))
                        successors_added += 1
            
            if self.debug and nodes_processed <= 5 and successors_added > 0:
                log_debug(f"         ↳ Dodano {successors_added} następników do warstwy {layer + 1}")
        
        # ✅ KROK 2C: Zorganizuj węzły według warstw
        max_layer = max(node.layer for node in self.nodes.values()) if self.nodes else 0
        self.layers = [[] for _ in range(max_layer + 1)]
        
        for node in self.nodes.values():
            if node.layer >= 0:
                self.layers[node.layer].append(node)
        
        # ✅ KROK 2D: POPRAW END WĘZŁY - przesuń na ostatnią warstwę
        end_nodes = [node for node in self.nodes.values() if node.role == 'end']
        if end_nodes and max_layer >= 0:
            moves_made = 0
            for end_node in end_nodes:
                if end_node.layer != max_layer:
                    # Przesuń END na ostatnią warstwę
                    if end_node in self.layers[end_node.layer]:
                        self.layers[end_node.layer].remove(end_node)
                    end_node.layer = max_layer
                    if end_node not in self.layers[max_layer]:
                        self.layers[max_layer].append(end_node)
                    moves_made += 1
            
            if self.debug and moves_made > 0:
                log_debug(f"   🏁 Przesunięto {moves_made} węzłów END na ostatnią warstwę ({max_layer})")
        
        # ✅ KROK 2E: WERYFIKACJA I DEBUG
        if self.debug:
            log_debug(f"   📊 WYNIK: Utworzono {len(self.layers)} warstw dla {len(self.nodes)} węzłów:")
            
            total_nodes_in_layers = 0
            for i, layer_nodes in enumerate(self.layers):
                if layer_nodes:  # Tylko niepuste warstwy
                    node_info = [f"{n.role}:{n.id[-6:]}" for n in layer_nodes[:4]]  # Max 4 węzły
                    if len(layer_nodes) > 4:
                        node_info.append(f"...+{len(layer_nodes)-4}")
                    
                    log_debug(f"      Warstwa {i}: {len(layer_nodes)} węzłów - {node_info}")
                    total_nodes_in_layers += len(layer_nodes)
            
            # Sprawdź czy wszystkie węzły są w warstwach
            if total_nodes_in_layers != len(self.nodes):
                missing = len(self.nodes) - total_nodes_in_layers
                log_warning(f"⚠️ UWAGA: {missing} węzłów nie zostało przypisanych do warstw!")
                
                # Znajdź zagubione węzły
                nodes_in_layers = set()
                for layer in self.layers:
                    nodes_in_layers.update(layer)
                
                missing_nodes = [n for n in self.nodes.values() if n not in nodes_in_layers]
                for missing_node in missing_nodes[:3]:  # Pokaż maksymalnie 3
                    log_debug(f"      🔍 Zagubiony: {missing_node.role}:{missing_node.id[-6:]} (layer={missing_node.layer})")
            
            # Sprawdź hierarchię START → END
            start_layers = [n.layer for n in self.nodes.values() if n.role == 'start']
            end_layers = [n.layer for n in self.nodes.values() if n.role == 'end']
            
            if start_layers and end_layers:
                min_start = min(start_layers)
                max_end = max(end_layers)
                log_debug(f"   ⭐ Hierarchia: START na warstwie {min_start}, END na warstwie {max_end}")
                
                if min_start >= max_end:
                    log_warning("⚠️ PROBLEM: START nie jest przed END w hierarchii!")
    
    # ===== ➕ KROK 2.5: WĘZŁY WIRTUALNE =====
    
    def _insert_virtual_nodes(self):
        """Dodaj wirtualne węzły dla krawędzi przechodzących przez wiele warstw"""
        
        if self.debug:
            log_debug("➕ KROK 2.5: Wstawianie węzłów wirtualnych")
        
        edges_to_virtualize = []
        
        # Znajdź krawędzie przechodzące przez więcej niż jedną warstwę
        for edge in self.edges:
            layer_diff = edge.target.layer - edge.source.layer
            if layer_diff > 1:
                edges_to_virtualize.append(edge)
        
        virtual_node_counter = 0
        
        for edge in edges_to_virtualize:
            source = edge.source
            target = edge.target
            label = edge.label
            
            # Usuń oryginalną krawędź
            self.edges.remove(edge)
            source.successors.remove(target)
            target.predecessors.remove(source)
            
            # Stwórz węzły wirtualne w warstwach pośrednich
            current_node = source
            
            for layer in range(source.layer + 1, target.layer):
                virtual_id = f"virtual_{virtual_node_counter}"
                virtual_node = Node(virtual_id, "virtual", "", source.swimlane)
                virtual_node.is_virtual = True
                virtual_node.layer = layer
                virtual_node.width = 10  # Bardzo mały
                virtual_node.height = 10
                
                self.nodes[virtual_id] = virtual_node
                self.layers[layer].append(virtual_node)
                
                # Połącz z poprzednim węzłem
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
    
    def _assign_coordinates(self):
        """Przypisz końcowe współrzędne X, Y"""
        
        if self.debug:
            log_debug("📍 KROK 4: Przypisanie współrzędnych")
        
        usable_width = self.canvas_width - 2 * self.margin_x
        usable_height = self.canvas_height - 2 * self.margin_y
        
        # 4A. Przypisz współrzędne Y (warstwy)
        if len(self.layers) > 1:
            layer_height = usable_height / (len(self.layers) - 1)
        else:
            layer_height = 0
        
        for layer_idx, layer in enumerate(self.layers):
            y = self.margin_y + layer_idx * layer_height
            
            for node in layer:
                node.y = y
        
        # 4B. Przypisz współrzędne X (pozycje w warstwach)
        for layer in self.layers:
            if not layer:
                continue
            
            if len(layer) == 1:
                # Pojedynczy węzeł - wyśrodkuj
                layer[0].x = self.canvas_width // 2
            else:
                # Wiele węzłów - rozłóż równomiernie
                total_width = sum(node.width for node in layer)
                total_spacing = self.node_spacing * (len(layer) - 1)
                required_width = total_width + total_spacing
                
                if required_width <= usable_width:
                    # Wyśrodkuj całą grupę
                    start_x = self.margin_x + (usable_width - required_width) // 2
                    spacing = self.node_spacing
                else:
                    # Ściśnij - zmniejsz spacing
                    start_x = self.margin_x
                    spacing = max(20, (usable_width - total_width) // (len(layer) - 1))
                
                current_x = start_x
                for node in layer:
                    node.x = current_x + node.width // 2  # Środek węzła
                    current_x += node.width + spacing
        
        if self.debug:
            log_debug(f"   📍 Współrzędne przypisane dla {sum(len(layer) for layer in self.layers)} węzłów")
            
            # Debug kilku przykładów
            for i, layer in enumerate(self.layers[:3]):
                for node in layer[:2]:
                    log_debug(f"      {node.role} L{i}: ({node.x:.0f}, {node.y:.0f}) {node.width}×{node.height}")
    
    # ===== 🎨 KROK 5: OPTYMALIZACJA UML =====
    
    def _optimize_for_activity_diagrams(self):
        """Optymalizacje specyficzne dla diagramów aktywności UML"""
        
        if self.debug:
            log_debug("🎨 KROK 5: Optymalizacje dla diagramów aktywności")
        
        # 5A. Upewnij się że START jest na górze, END na dole
        start_nodes = [node for node in self.nodes.values() if node.role == 'start']
        end_nodes = [node for node in self.nodes.values() if node.role == 'end']
        
        if start_nodes and self.layers:
            for start_node in start_nodes:
                if start_node.layer != 0:
                    # Przenieś START na warstwę 0
                    self.layers[start_node.layer].remove(start_node)
                    start_node.layer = 0
                    if start_node not in self.layers[0]:
                        self.layers[0].insert(0, start_node)
                    # Przelicz Y
                    start_node.y = self.margin_y
        
        if end_nodes and self.layers:
            last_layer = len(self.layers) - 1
            for end_node in end_nodes:
                if end_node.layer != last_layer:
                    self.layers[end_node.layer].remove(end_node)
                    end_node.layer = last_layer
                    if end_node not in self.layers[last_layer]:
                        self.layers[last_layer].append(end_node)
                    # Przelicz Y
                    end_node.y = self.margin_y + last_layer * self.layer_spacing
        
        # 5B. Optymalizacja dla swimlanes
        if self.swimlanes:
            self._optimize_swimlanes()
        
        # 5C. Konwersja do element_positions
        self.element_positions = {}
        
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
                    'column': int(x_final // (self.canvas_width // 6)),
                    'row': int(y_final // 100),
                    'layer': node.layer,
                    'role': node.role
                }
        
        if self.debug:
            log_debug(f"   🎨 Element_positions: {len(self.element_positions)} elementów")
    
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
