import os
import sys
import math
from typing import Dict, List, Tuple, Any

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)

from utils.logger_utils import log_debug, log_info, log_error, log_warning, log_exception

class ImprovedLayoutManager:
    """
    Ulepszona klasa do zarządzania układem diagramu aktywności.
    
    Implementuje 6-krokowe podejście do rozmieszczania elementów:
    1. Określenie wielkości każdego elementu
    2. Określenie przestrzeni roboczej (siatki)
    3. Pozycjonowanie elementów według reguł
    4. Korekta nakładających się elementów
    5. Weryfikacja logiki diagramu
    6. Wyrównanie diagramu i optymalizacja
    """
    
    def __init__(self, canvas_width=1800, canvas_height=1600, debug=False):
        # Podstawowa konfiguracja
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.debug = debug
        
        # Margines canvas
        self.margin_x = 80
        self.margin_y = 60
        
        # Struktury danych przechowujące elementy i ich pozycje
        self.elements = {}          # oryginalne elementy z parsera
        self.element_positions = {} # wynikowe pozycje
        self.element_dimensions = {} # wymiary elementów
        self.connections = []       # połączenia między elementami
        self.swimlanes = {}         # informacje o torach
        self.swimlanes_geometry = {} # geometria torów
        
        # Struktura siatki
        self.grid = None
        self.rows = []
        self.columns = []

    def analyze_diagram_structure(self, parsed_data):
        """Główna metoda wykonująca wszystkie 6 kroków"""
        try:
            self._prepare_input_data(parsed_data)
            
            if not self.elements:
                log_warning("Brak elementów do analizy")
                return {}, {}
                
            # Krok 1: Określenie wielkości elementów
            self._calculate_element_dimensions()
            
            # Krok 2: Definiowanie przestrzeni roboczej
            self._define_grid()
            
            # Krok 3: Pozycjonowanie elementów według reguł
            # self._position_elements_by_rules()  # Stara metoda pozycjonowania
            self._layered_assignment()  # Nowy algorytm warstwowy
            
            # Sprawdź czy wszystkie elementy mają pozycje
            positioned_count = len(self.element_positions)
            total_count = len(self.elements)
            
            if positioned_count < total_count:
                log_warning(f"Tylko {positioned_count} z {total_count} elementów ma przypisane pozycje. Uruchamiam awaryjne pozycjonowanie.")
                self._emergency_position_remaining_elements()
            
            # Krok 4: Korekta nakładających się elementów
            self._resolve_overlaps()
            
            # Krok 5: Weryfikacja logiki diagramu
            self._verify_diagram_logic()
            
            # Krok 6: Wyrównanie i optymalizacja przestrzeni
            self._align_diagram()
            
            # Aktualizuj geometrię torów
            self.update_swimlane_geometry()
            
            return self.element_positions, self._get_grid_info()
        except Exception as e:
            log_error(f"Błąd w ImprovedLayoutManager: {e}")
            # W przypadku błędu zwróć puste pozycje
            return {}, {
                "canvas_width": self.canvas_width,
                "canvas_height": self.canvas_height
            }
    
    def _prepare_input_data(self, parsed_data):
        """Konwertuje dane z parsera do wewnętrznego formatu"""
        # Kopiuj elementy
        self.elements = {}
        for idx, element in enumerate(parsed_data.get('flow', [])):
            element_id = element.get('id', f"elem_{idx}")
            self.elements[element_id] = element.copy()
        
        # Debugowanie - sprawdź liczbę elementów
        if self.debug:
            log_debug(f"Wczytano {len(self.elements)} elementów diagramu")
        
        # Zapisz informacje o torach
        self.swimlanes = parsed_data.get('swimlanes', {})
        
        # Normalizuj połączenia logiczne
        self.connections = []
        for conn in parsed_data.get('logical_connections', []):
            # Sprawdź poprawność połączenia
            source = conn.get("source")
            target = conn.get("target")
            
            if not source or not target:
                continue
                    
            if source not in self.elements or target not in self.elements:
                log_warning(f"Pominięto nieprawidłowe połączenie: {source} -> {target}")
                continue
            
            self.connections.append(conn.copy())  # ✅ Poprawne wcięcie - linia w pętli
        
        # Debugowanie - sprawdź liczbę połączeń
        if self.debug:
            log_debug(f"Wczytano {len(self.connections)} połączeń logicznych")

    def _calculate_element_dimensions(self):
        """Oblicza wymiary każdego elementu na podstawie typu i treści"""
        for element_id, element in self.elements.items():
            element_type = element.get("type", "activity")
            element_text = element.get("text", "")
            
            # Stałe wymiary dla elementów kontrolnych
            if element_type == "control" and element.get("action") == "start":
                width, height = 40, 40  # Start node
            elif element_type == "control" and element.get("action") in ["end", "stop"]:
                width, height = 40, 40  # End node
            elif element_type in ["decision_start", "decision_else"]:
                width, height = 80, 80  # Decision
            elif element_type == "note":
                # Notatki - szerokość zależna od długości tekstu
                width = min(300, max(160, len(element_text) * 6))
                height = 80
            else:
                # Standardowe aktywności - wymiar zależy od długości tekstu
                text_length = len(element_text)
                if text_length > 50:
                    width, height = 280, 80
                elif text_length > 30:
                    width, height = 220, 70
                else:
                    width, height = 180, 60
            
            # Zapisz wymiary w słowniku elementu
            self.elements[element_id]["width"] = width
            self.elements[element_id]["height"] = height
            
            if self.debug:
                log_debug(f"Element {element_id[-6:]}: {width}×{height} ({element_type})")

    def _define_grid(self):
        """Definiuje siatkę zgodnie z liczbą i wielkością elementów"""
        
        # Sprawdź liczbę elementów
        element_count = len(self.elements)
        
        # Znajdź najszerszy i najwyższy element
        max_width = 0
        max_height = 0
        
        for element_id, element in self.elements.items():
            width = element.get("width", 100)
            height = element.get("height", 60)
            max_width = max(max_width, width)
            max_height = max(max_height, height)
        
        # Zdefiniuj wymiary komórek siatki
        cell_width = max_width * 2  # 2x szerokość najszerszego
        cell_height = max_height * 2  # 2x wysokość najwyższego
        
        # Ustal liczbę wierszy i kolumn na podstawie pierwiastka liczby elementów
        # aby zbliżyć się do kwadratu
        grid_size = math.ceil(math.sqrt(element_count))
        num_cols = grid_size
        num_rows = math.ceil(element_count / num_cols)
        
        # Uwzględnij tory (swimlanes) jeśli istnieją
        swimlanes = self._extract_swimlanes()
        if swimlanes:
            num_cols = max(num_cols, len(swimlanes))
        
        # Oblicz całkowite wymiary siatki
        grid_width = cell_width * num_cols
        grid_height = cell_height * num_rows
        
        # Dostosuj canvas jeśli potrzeba
        self.canvas_width = max(self.canvas_width, grid_width + 2 * self.margin_x)
        self.canvas_height = max(self.canvas_height, grid_height + 2 * self.margin_y)
        
        # Utwórz wiersze i kolumny
        self.rows = []
        self.columns = []
        
        for i in range(num_rows):
            y = self.margin_y + i * cell_height
            self.rows.append({
                'y': y,
                'height': cell_height,
                'center_y': y + cell_height/2
            })
        
        for i in range(num_cols):
            x = self.margin_x + i * cell_width
            self.columns.append({
                'x': x,
                'width': cell_width,
                'center_x': x + cell_width/2,
                'swimlane': swimlanes[i] if swimlanes and i < len(swimlanes) else None
            })
        
        self.grid = {
            'rows': num_rows,
            'columns': num_cols,
            'row_height': cell_height,
            'col_width': cell_width
        }
        
        if self.debug:
            log_debug(f"Siatka: {num_rows} wierszy × {num_cols} kolumn")
            log_debug(f"Wymiary komórki: {cell_width}×{cell_height}")

    def _position_elements_by_rules(self):
        """Pozycjonuje elementy według ich typu i roli w diagramie"""
        # Znajdź elementy typu "start" - umieść je w górnym wierszu, na środku
        start_nodes = self._find_elements_by_type("control", action="start")
        
        # Jeśli nie ma wyraźnych węzłów startowych, znajdź inne elementy początkowe
        if not start_nodes:
            incoming_connections = {conn.get("target") for conn in self.connections 
                                if conn.get("target") in self.elements}
            for element_id in self.elements:
                if element_id not in incoming_connections:
                    # Element bez przychodzących połączeń - to potencjalny początek
                    start_nodes.append(element_id)
                    if self.debug:
                        log_debug(f"Dodano element początkowy: {element_id} (brak wejść)")
        
        # Rozpocznij budowanie diagramu od węzłów początkowych
        if start_nodes:
            # Rozmieść elementy początkowe równomiernie w pierwszym wierszu
            total_cols = len(self.columns)
            spacing = max(1, total_cols // (len(start_nodes) + 1))
            
            for i, start_id in enumerate(start_nodes):
                col = (i + 1) * spacing
                if col >= total_cols:
                    col = total_cols - 1
                
                self._place_element(start_id, col=col, row=0)
                
                # Wykonaj algorytm przydziału pozycji BFS zaczynając od start
                visited = set([start_id])
                self._assign_positions_recursive(start_id, visited, 1)
    
    def _resolve_overlaps(self):
        """Wykrywa i rozwiązuje nakładające się elementy"""
        overlaps_found = True
        iterations = 0
        max_iterations = 10
        
        while overlaps_found and iterations < max_iterations:
            overlaps_found = False
            iterations += 1
            
            # Sprawdź wszystkie pary elementów
            positioned_elements = list(self.element_positions.items())
            
            for i, (id1, pos1) in enumerate(positioned_elements):
                for j, (id2, pos2) in enumerate(positioned_elements[i+1:], i+1):
                    # Sprawdź czy nakładają się
                    if self._elements_overlap(pos1, pos2):
                        overlaps_found = True
                        # Rozwiąż nakładanie się - przesuń jeden z elementów
                        self._resolve_single_overlap(id1, id2)
            
            if self.debug and overlaps_found:
                log_debug(f"Iteracja {iterations}: znaleziono nakładania, rozwiązuję...")
        
        if iterations == max_iterations and overlaps_found:
            log_warning(f"Osiągnięto maksymalną liczbę iteracji ({max_iterations}), mogą pozostać nakładania")

    def update_swimlane_geometry(self):
        """Aktualizuje geometrię torów na podstawie pozycji elementów"""
        if not self.swimlanes:
            return
        
        # Dla każdego toru znajdź elementy i określ granice
        swimlane_elements = {}
        for element_id, position in self.element_positions.items():
            swimlane = self.elements[element_id].get('swimlane')
            if swimlane:
                if swimlane not in swimlane_elements:
                    swimlane_elements[swimlane] = []
                swimlane_elements[swimlane].append(position)
        
        # Oblicz geometrię każdego toru
        for name, elements in swimlane_elements.items():
            if not elements:
                continue
                
            min_x = min(e['x'] for e in elements)
            max_x = max(e['x'] + e['width'] for e in elements)
            min_y = min(e['y'] for e in elements)
            max_y = max(e['y'] + e['height'] for e in elements)
            
            # Dodaj marginesy
            min_x = max(0, min_x - 50)
            min_y = max(0, min_y - 50)
            max_x = min(self.canvas_width, max_x + 50)
            max_y = min(self.canvas_height, max_y + 100)
            
            self.swimlanes_geometry[name] = {
                'x': min_x,
                'y': min_y,
                'width': max_x - min_x,
                'height': max_y - min_y
            }
    
    def _analyze_flow_depth(self):
        """Analizuje głębokość przepływu dla określenia liczby wierszy"""
        # Buduje graf połączeń z elementów przepływu
        graph = {}
        for element_id in self.elements:
            graph[element_id] = []
        
        for conn in self.connections:
            source = conn.get("source")
            target = conn.get("target")
            if source and target and source in graph:
                graph[source].append(target)
        
        # Znajdź węzeł startowy
        start_nodes = self._find_elements_by_type("control", action="start")
        if not start_nodes:
            start_nodes = []
            # Znajdź elementy bez przychodzących połączeń
            incoming_connections = {conn.get("target") for conn in self.connections if conn.get("target")}
            for element_id in self.elements:
                if element_id not in incoming_connections:
                    start_nodes.append(element_id)
        
        if not start_nodes:
            log_warning("Nie znaleziono węzła startowego ani elementu bez wejść")
            return 8  # Wartość domyślna
        
        # Obliczenie maksymalnej głębokości ścieżki od startu
        def calc_depth(node, visited=None):
            if visited is None:
                visited = set()
            if node in visited:
                return 0
            visited.add(node)
            
            if node not in graph or not graph[node]:
                return 1
            
            return 1 + max([calc_depth(child, visited.copy()) for child in graph[node]], default=0)
        
        max_depth = max([calc_depth(node) for node in start_nodes])
        return max_depth

    def _extract_swimlanes(self):
        """Wyodrębnia tory (swimlanes) z danych wejściowych"""
        if not self.swimlanes:
            return []
        
        # Zwróć listę unikalnych torów używanych przez elementy
        used_swimlanes = set()
        for element in self.elements.values():
            if 'swimlane' in element and element['swimlane']:
                used_swimlanes.add(element['swimlane'])
        
        return list(used_swimlanes)

    def _find_elements_by_type(self, element_type, action=None):
        """Znajduje elementy określonego typu i opcjonalnie akcji"""
        result = []
        for element_id, element in self.elements.items():
            if element.get("type") == element_type:
                if action is None or element.get("action") == action:
                    result.append(element_id)
        return result

    def _place_element(self, element_id, col, row):
        """Umieszcza element w określonej pozycji siatki"""
        if row < 0 or row >= len(self.rows) or col < 0 or col >= len(self.columns):
            log_warning(f"Próba umieszczenia elementu {element_id} poza siatką: row={row}, col={col}")
            # Używamy ostatniego poprawnego wiersza/kolumny
            row = max(0, min(row, len(self.rows) - 1))
            col = max(0, min(col, len(self.columns) - 1))
        
        element = self.elements[element_id]
        width = element.get("width", 100)
        height = element.get("height", 60)
        
        # Oblicz współrzędne środka komórki
        center_x = self.columns[col]['center_x']
        center_y = self.rows[row]['center_y']
        
        # Umieść element z jego środkiem w środku komórki
        x = center_x - width / 2
        y = center_y - height / 2
        
        self.element_positions[element_id] = {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "grid_col": col,
            "grid_row": row
        }

    def _assign_positions_recursive(self, current_id, visited, current_row, max_depth=20):
        """Rekurencyjnie przypisuje pozycje elementom, zaczynając od podanego"""
        # Ochrona przed zbyt głęboką rekurencją
        if current_row > max_depth:
            log_warning(f"Osiągnięto maksymalną głębokość rekurencji ({max_depth}) dla {current_id}")
            return
            
        # Znajdź wszystkie następniki bieżącego elementu
        successors = []
        for conn in self.connections:
            if conn.get("source") == current_id:
                target_id = conn.get("target")
                if target_id and target_id in self.elements:
                    # Sprawdź czy już nie ma pozycji
                    if target_id not in self.element_positions:
                        successors.append((target_id, conn.get("condition", "")))
        
        if not successors:
            return
        
        # Przydziel kolumny następnikom
        current_pos = self.element_positions.get(current_id)
        if not current_pos:
            log_warning(f"Brak pozycji dla elementu {current_id}")
            return
            
        center_col = current_pos.get("grid_col", len(self.columns) // 2)
        num_successors = len(successors)
        
        # Specjalne traktowanie dla różnych typów elementów
        element_type = self.elements[current_id].get("type")
        
        # Dla decyzji umieść gałęzie true po prawej, false po lewej
        if element_type in ["decision_start", "decision_else"]:
            true_targets = [(id, cond) for id, cond in successors if cond == "true"]
            false_targets = [(id, cond) for id, cond in successors if cond != "true"]
            
            # Umieść gałąź true po prawej
            for i, (target_id, _) in enumerate(true_targets):
                col = center_col + (i + 1)
                if col >= len(self.columns):
                    col = len(self.columns) - 1
                self._place_element(target_id, col, current_row)
                visited.add(target_id)
                
            # Umieść gałąź false po lewej
            for i, (target_id, _) in enumerate(false_targets):
                col = center_col - (i + 1)
                if col < 0:
                    col = 0
                self._place_element(target_id, col, current_row)
                visited.add(target_id)
                
            # Rekurencyjne przypisanie dla gałęzi
            for target_id, _ in true_targets + false_targets:
                self._assign_positions_recursive(target_id, visited, current_row + 1, max_depth)
        else:
            # Standardowe rozmieszczenie dla innych typów elementów
            if num_successors == 1:
                # Pojedynczy następnik - umieść w tej samej kolumnie
                successor_id, _ = successors[0]
                self._place_element(successor_id, center_col, current_row)
                visited.add(successor_id)
                self._assign_positions_recursive(successor_id, visited, current_row + 1, max_depth)
            else:
                # Wielu następników - rozłóż równomiernie
                span = min(num_successors * 2 - 1, len(self.columns) - 1)
                start_col = max(0, center_col - span // 2)
                
                # Sprawdź czy mieści się w siatce
                if start_col + span >= len(self.columns):
                    start_col = max(0, len(self.columns) - span - 1)
                
                # Umieść następniki
                for i, (successor_id, _) in enumerate(successors):
                    col = start_col + i * 2  # Większy odstęp między elementami
                    if col >= len(self.columns):
                        col = len(self.columns) - 1
                        
                    self._place_element(successor_id, col, current_row)
                    visited.add(successor_id)
                
                # Rekurencyjne przypisanie dla następników
                for successor_id, _ in successors:
                    self._assign_positions_recursive(successor_id, visited, current_row + 1, max_depth)

    def _position_elements_without_start(self):
        """Umieszcza elementy gdy brak węzła startowego"""
        # Znajdź elementy bez wejść
        incoming_connections = {conn.get("target") for conn in self.connections if conn.get("target")}
        root_elements = []
        for element_id in self.elements:
            if element_id not in incoming_connections:
                root_elements.append(element_id)
        
        if not root_elements:
            # Jeśli nie znaleziono elementów bez wejść, weź pierwszy
            root_elements = [list(self.elements.keys())[0]]
        
        # Rozmieść elementy główne równomiernie w pierwszym wierszu
        num_roots = len(root_elements)
        total_cols = len(self.columns)
        spacing = max(1, total_cols // (num_roots + 1))
        
        for i, element_id in enumerate(root_elements):
            col = (i + 1) * spacing
            if col >= total_cols:
                col = total_cols - 1
            
            # Umieść element i jego następniki
            self._place_element(element_id, col, 0)
            visited = set([element_id])
            self._assign_positions_recursive(element_id, visited, 1)
        
        # Dla elementów, które nie zostały umieszczone, dodaj na końcu
        unpositioned = [eid for eid in self.elements if eid not in self.element_positions]
        if unpositioned:
            log_warning(f"Znaleziono {len(unpositioned)} elementów bez połączeń, umieszczam je na dole diagramu")
            row = len(self.rows) - 1
            for i, element_id in enumerate(unpositioned):
                col = i % len(self.columns)
                self._place_element(element_id, col, row)

    def _apply_special_positioning_rules(self):
        """Stosuje specjalne reguły pozycjonowania dla typów elementów"""
        # Przykładowa implementacja dla decyzji i ich następników
        decision_elements = self._find_elements_by_type("decision_start")
        for decision_id in decision_elements:
            if decision_id not in self.element_positions:
                continue
            
            # Znajdź gałęzie true i false
            true_branch = None
            false_branch = None
            
            for conn in self.connections:
                if conn.get("source") == decision_id:
                    target_id = conn.get("target")
                    if not target_id:
                        continue
                        
                    if conn.get("condition", "") == "true":
                        true_branch = target_id
                    else:
                        false_branch = target_id
            
            # Jeśli znaleziono obie gałęzie, dostosuj ich pozycje
            if true_branch and false_branch:
                decision_pos = self.element_positions[decision_id]
                decision_col = decision_pos.get("grid_col", 0)
                decision_row = decision_pos.get("grid_row", 0)
                
                # Gałąź true idzie w prawo, false w lewo
                if true_branch in self.element_positions:
                    true_pos = self.element_positions[true_branch]
                    self._place_element(true_branch, decision_col + 1, decision_row + 1)
                
                if false_branch in self.element_positions:
                    false_pos = self.element_positions[false_branch]
                    self._place_element(false_branch, decision_col - 1, decision_row + 1)

    def _elements_overlap(self, pos1, pos2):
        """Sprawdza czy dwa elementy nakładają się"""
        # Sprawdź nakładanie się prostokątów
        return not (
            pos1["x"] + pos1["width"] <= pos2["x"] or
            pos1["x"] >= pos2["x"] + pos2["width"] or
            pos1["y"] + pos1["height"] <= pos2["y"] or
            pos1["y"] >= pos2["y"] + pos2["height"]
        )

    def _resolve_single_overlap(self, id1, id2):
        """Rozwiązuje pojedyncze nakładanie się elementów"""
        pos1 = self.element_positions[id1]
        pos2 = self.element_positions[id2]
        
        # Sprawdź który element jest wyżej w hierarchii
        row1 = pos1.get("grid_row", 0)
        row2 = pos2.get("grid_row", 0)
        
        # Oblicz nakładanie się
        overlap_x = min(pos1["x"] + pos1["width"], pos2["x"] + pos2["width"]) - max(pos1["x"], pos2["x"])
        overlap_y = min(pos1["y"] + pos1["height"], pos2["y"] + pos2["height"]) - max(pos1["y"], pos2["y"])
        
        # Jeśli elementy są w tym samym wierszu, przesuń w poziomie
        if row1 == row2:
            if pos1["x"] < pos2["x"]:
                # Element 1 jest z lewej strony
                pos1["x"] -= overlap_x / 2
                pos2["x"] += overlap_x / 2
            else:
                pos1["x"] += overlap_x / 2
                pos2["x"] -= overlap_x / 2
        else:
            # Elementy w różnych wierszach, rozsuń je w pionie
            if pos1["y"] < pos2["y"]:
                pos2["y"] += overlap_y
            else:
                pos1["y"] += overlap_y

    def _verify_diagram_logic(self):
        """Weryfikuje logikę i kompletność diagramu"""
        # Podstawowa implementacja: sprawdź czy wszystkie elementy są umieszczone
        unpositioned = [eid for eid in self.elements if eid not in self.element_positions]
        if unpositioned:
            log_warning(f"UWAGA: {len(unpositioned)} elementów nie ma przypisanej pozycji")
            
        # Sprawdź czy wszystkie elementy są osiągalne (mają połączenia)
        graph = {}
        for element_id in self.elements:
            graph[element_id] = []
        
        for conn in self.connections:
            source = conn.get("source")
            target = conn.get("target")
            if source and target and source in graph:
                graph[source].append(target)
        
        # Znajdź węzły startowe
        start_nodes = self._find_elements_by_type("control", action="start")
        if not start_nodes:
            start_nodes = []
            # Znajdź elementy bez przychodzących połączeń
            incoming_connections = {conn.get("target") for conn in self.connections if conn.get("target")}
            for element_id in self.elements:
                if element_id not in incoming_connections:
                    start_nodes.append(element_id)
        
        # Oznacz osiągalne elementy
        reachable = set()
        def mark_reachable(node):
            if node in reachable:
                return
            reachable.add(node)
            for target in graph.get(node, []):
                mark_reachable(target)
        
        for start in start_nodes:
            mark_reachable(start)
        
        # Znajdź nieosiągalne elementy
        unreachable = [eid for eid in self.elements if eid not in reachable]
        if unreachable:
            log_warning(f"UWAGA: {len(unreachable)} elementów jest nieosiągalnych w diagramie")

    def _align_diagram(self):
        """Wyrównuje diagram i optymalizuje przestrzeń"""
        if not self.element_positions:
            return
        
        # Znajdź skrajne współrzędne diagramu
        min_x = min(pos["x"] for pos in self.element_positions.values())
        min_y = min(pos["y"] for pos in self.element_positions.values())
        
        # Jeśli diagram nie zaczyna się od (0,0), przesuń wszystkie elementy
        if min_x > self.margin_x or min_y > self.margin_y:
            x_shift = min_x - self.margin_x
            y_shift = min_y - self.margin_y
            
            # Przesuń elementy
            for element_id in self.element_positions:
                self.element_positions[element_id]["x"] -= x_shift
                self.element_positions[element_id]["y"] -= y_shift
                
            if self.debug:
                log_debug(f"Przesunięto diagram o X:{x_shift}, Y:{y_shift}")

    def _get_grid_info(self):
        """Zwraca informacje o siatce do generatora XMI"""
        return {
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "rows": len(self.rows),
            "columns": len(self.columns),
            "swimlanes": self.swimlanes,
            "swimlanes_geometry": self.swimlanes_geometry
        }
    
    def _emergency_position_remaining_elements(self):
        """Awaryjne pozycjonowanie elementów, które nie mają jeszcze pozycji"""
        unpositioned = [eid for eid in self.elements if eid not in self.element_positions]
        
        if not unpositioned:
            return
            
        log_info(f"Awaryjne pozycjonowanie dla {len(unpositioned)} elementów")
        
        # Znajdź grupę połączonych elementów i pozycjonuj je razem
        graph = {}
        for element_id in unpositioned:
            graph[element_id] = []
        
        # Buduj graf tylko dla niepozycjonowanych elementów
        for conn in self.connections:
            source = conn.get("source")
            target = conn.get("target")
            if source in unpositioned and target in unpositioned:
                if source not in graph:
                    graph[source] = []
                graph[source].append(target)
        
        # Znajdź grupy połączonych elementów
        visited = set()
        groups = []
        
        for element_id in unpositioned:
            if element_id in visited:
                continue
                
            # Znajdź grupę połączonych elementów
            group = []
            queue = [element_id]
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                    
                visited.add(current)
                group.append(current)
                
                # Dodaj sąsiadów
                for neighbor in graph.get(current, []):
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            if group:
                groups.append(group)
        
        # Rozmieść każdą grupę w osobnym obszarze diagramu
        row_offset = 0
        num_cols = len(self.columns)
        
        for i, group in enumerate(groups):
            # Oblicz początkową pozycję dla grupy
            start_row = len(self.rows) // 2 + row_offset
            start_col = (i % num_cols)
            
            # Rozmieść elementy grupy w siatce
            for j, element_id in enumerate(group):
                row = start_row + (j // num_cols)
                col = (start_col + j) % num_cols
                
                # Sprawdź czy mieszczą się w siatce
                if row >= len(self.rows):
                    row = len(self.rows) - 1
                
                self._place_element(element_id, col, row)
            
            # Zwiększ offset dla następnej grupy
            row_offset += len(group) // num_cols + 1
        
        # Pozostałe pojedyncze elementy
        remaining = [eid for eid in unpositioned if eid not in visited]
        if remaining:
            start_row = 0
            for i, element_id in enumerate(remaining):
                row = start_row + (i // num_cols)
                col = i % num_cols
                
                if row >= len(self.rows):
                    row = len(self.rows) - 1
                    
                self._place_element(element_id, col, row)

    def _build_element_graph(self):
        """Buduje graf połączeń między elementami dla lepszej analizy"""
        # Inicjalizuj struktury grafowe
        self.forward_graph = {}  # element_id -> [następniki]
        self.backward_graph = {} # element_id -> [poprzedniki]
        
        # Inicjalizuj grafy dla wszystkich elementów
        for element_id in self.elements:
            self.forward_graph[element_id] = []
            self.backward_graph[element_id] = []
        
        # Wypełnij grafy na podstawie połączeń
        for conn in self.connections:
            source = conn.get("source")
            target = conn.get("target")
            
            if source and target and source in self.elements and target in self.elements:
                if target not in self.forward_graph[source]:
                    self.forward_graph[source].append(target)
                if source not in self.backward_graph[target]:
                    self.backward_graph[target].append(source)
        
        # Oblicz liczbę połączeń wejściowych/wyjściowych
        self.in_degree = {node: len(edges) for node, edges in self.backward_graph.items()}
        self.out_degree = {node: len(edges) for node, edges in self.forward_graph.items()}
        
        # Identyfikuj węzły specjalne
        self.start_nodes = [node for node, degree in self.in_degree.items() if degree == 0]
        self.end_nodes = [node for node, degree in self.out_degree.items() if degree == 0]
        self.junction_nodes = [node for node, degree in self.in_degree.items() 
                            if degree > 1 or self.out_degree[node] > 1]
    
    def _layered_assignment(self):
        """Przypisuje elementy do warstw (poziomów) dla lepszego układu hierarchicznego"""
        # Zbuduj graf
        self._build_element_graph()
        
        # Inicjalizuj warstwy
        self.layers = []
        assigned_nodes = set()
        
        # Rozpocznij od węzłów startowych (warstwa 0)
        current_layer = self.start_nodes[:]
        layer_index = 0
        
        # Iteracyjnie przypisuj kolejne warstwy
        while current_layer:
            self.layers.append(current_layer)
            assigned_nodes.update(current_layer)
            
            # Przejdź do następnej warstwy
            next_layer = []
            for node in current_layer:
                for successor in self.forward_graph[node]:
                    # Dodaj do następnej warstwy tylko jeśli wszystkie poprzedniki już przypisane
                    if successor not in assigned_nodes and all(pred in assigned_nodes 
                                                            for pred in self.backward_graph[successor]):
                        next_layer.append(successor)
            
            current_layer = next_layer
            layer_index += 1
        
        # Przypisz pozostałe elementy do odpowiednich warstw
        unassigned = [node for node in self.elements if node not in assigned_nodes]
        if unassigned:
            # Przypisz elementy bez powiązań
            self.layers.append(unassigned)
        
        # Przypisz pozycje na podstawie warstw
        self._position_elements_by_layers()

    def _position_elements_by_layers(self):
        """Przypisuje pozycje elementom na podstawie ich warstw"""
        # Sprawdź czy mamy warstwy do pracy
        if not hasattr(self, 'layers') or not self.layers:
            log_warning("Brak warstw do pozycjonowania elementów")
            return
        
        # Dla każdej warstwy przypisz wiersz
        for row_idx, layer in enumerate(self.layers):
            # Rozmieść elementy w warstwie równomiernie w kolumnach
            num_elements = len(layer)
            if num_elements == 0:
                continue
                
            # Oblicz odstępy między elementami w warstwie
            total_cols = len(self.columns)
            if num_elements == 1:
                # Jeden element - umieść na środku
                self._place_element(layer[0], total_cols // 2, row_idx)
            else:
                # Wiele elementów - rozmieść równomiernie
                spacing = max(1, total_cols // (num_elements + 1))
                
                for i, element_id in enumerate(layer):
                    col = (i + 1) * spacing
                    if col >= total_cols:
                        col = total_cols - 1
                    
                    self._place_element(element_id, col, row_idx)

    def _resolve_branch_overlaps(self):
        """Rozwiązuje nakładanie się poprzez przesunięcie całych gałęzi"""
        overlaps_found = True
        iterations = 0
        max_iterations = 15  # Zwiększ liczbę iteracji
        
        while overlaps_found and iterations < max_iterations:
            overlaps_found = False
            iterations += 1
            
            # Sprawdź wszystkie pary elementów
            positioned_elements = list(self.element_positions.items())
            
            for i, (id1, pos1) in enumerate(positioned_elements):
                for j, (id2, pos2) in enumerate(positioned_elements[i+1:], i+1):
                    # Sprawdź czy nakładają się
                    if self._elements_overlap(pos1, pos2):
                        overlaps_found = True
                        
                        # Znajdź korzennie gałęzi dla obu elementów
                        root1 = self._find_branch_root(id1)
                        root2 = self._find_branch_root(id2)
                        
                        # Jeśli są z różnych gałęzi, przesuń jedną z nich
                        if root1 != root2:
                            # Oblicz szerokość przesunięcia
                            shift_x = pos1['width'] + 50
                            
                            # Decyzja, którą gałąź przesunąć
                            if pos1['x'] < pos2['x']:
                                self._shift_branch(root2, shift_x)
                            else:
                                self._shift_branch(root1, -shift_x)

    