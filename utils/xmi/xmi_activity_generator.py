import xml.etree.ElementTree as ET
import uuid
from datetime import datetime
import xml.dom.minidom
import sys
import re
import os
import copy
from logger_utils import log_debug, log_info, log_error, log_exception, log_warning, setup_logger
from utils.plantuml.improved_plantuml_activity_parser import (
        ImprovedPlantUMLActivityParser as PlantUMLActivityParser,
    )
from utils.xmi.graph_layout_manager import GraphLayoutManager

setup_logger()
class LayoutManagerAdapter:
    """Adapter zapewniający jednolity interfejs layoutu z wieloma fallbackami."""

    def __init__(
        self,
        swimlane_ids,
        parsed_data=None,
        transitions=None,
        id_map=None,
        debug_positioning=False,
    ):
        self.swimlane_ids = swimlane_ids or {}
        self.parsed_data = parsed_data or {}
        self.transitions = transitions or []
        self.id_map = id_map or {}
        self.debug_positioning = debug_positioning
        self.element_positions = {}
        self.grid = {'rows': 0, 'columns': 0}
        self.swimlanes_geometry = {}
        self._parser_mapping = {}
        self._lane_order = list(self.swimlane_ids.keys())
        self._graph_manager = (
            GraphLayoutManager(debug=debug_positioning)
        )

    def set_parser_mapping(self, parser_mapping):
        self._parser_mapping = parser_mapping or {}

    def analyze_diagram_structure(self, parsed_data):
        self.parsed_data = parsed_data or {}

        if self._graph_manager is not None:
            try:
                positions, grid = self._graph_manager.analyze_diagram_structure(self.parsed_data)
                if positions:
                    self.element_positions = {
                        key: self._coerce_dimensions(value)
                        for key, value in positions.items()
                    }
                else:
                    self.element_positions = {}
                self.grid = grid or {'rows': 0, 'columns': 0}
            except Exception as layout_err:
                log_warning(f"⚠️ Błąd GraphLayoutManager: {layout_err}")
                self.element_positions, self.grid = self._generate_fallback_positions()
        else:
            self.element_positions, self.grid = self._generate_fallback_positions()

        return self.element_positions, self.grid

    def update_swimlane_geometry(self):
        self.swimlanes_geometry = {}
        horizontal_margin = 60
        vertical_margin_top = 80
        vertical_margin_bottom = 100

        flow = self.parsed_data.get('flow', []) if isinstance(self.parsed_data, dict) else []

        for index, (lane_name, partition_id) in enumerate(self.swimlane_ids.items()):
            lane_positions = []
            for item in flow:
                if item.get('swimlane') != lane_name:
                    continue
                parser_id = item.get('id')
                if parser_id and parser_id in self.element_positions:
                    lane_positions.append(self.element_positions[parser_id])

            if lane_positions:
                min_left = min(int(pos.get('x', 0)) for pos in lane_positions)
                max_right = max(int(pos.get('x', 0)) + int(pos.get('width', 140)) for pos in lane_positions)
                min_top = min(int(pos.get('y', 0)) for pos in lane_positions)
                max_bottom = max(int(pos.get('y', 0)) + int(pos.get('height', 60)) for pos in lane_positions)

                left = max(0, min_left - horizontal_margin)
                right = max_right + horizontal_margin
                top = max(0, min_top - vertical_margin_top)
                bottom = max_bottom + vertical_margin_bottom
            else:
                # Fallback do stałych wartości, jeśli brak pozycji
                left = 100 + index * 280
                right = left + 250
                top = 80
                bottom = top + 700

            self.swimlanes_geometry[partition_id] = {
                'x': left,
                'y': top,
                'width': max(200, right - left),
                'height': max(300, bottom - top),
            }

        return self.swimlanes_geometry

    def get_position_for_element(self, node):
        if node is None:
            return None

        xmi_id = node.attrib.get('xmi:id')
        if not xmi_id:
            if self.debug_positioning:
                log_warning("Brak xmi:id podczas pobierania pozycji elementu")
            return None

        parser_id = None
        for pid, mapped_id in self._parser_mapping.items():
            if mapped_id == xmi_id:
                parser_id = pid
                break

        if not parser_id:
            if self.debug_positioning:
                log_warning(f"Nie znaleziono parser_id dla elementu XMI {xmi_id}")
            return None

        pos = self.element_positions.get(parser_id)
        if not pos:
            if self.debug_positioning:
                log_warning(f"Brak pozycji layoutu dla parser_id {parser_id}")
            return None

        x = int(pos.get('x', 0))
        y = int(pos.get('y', 0))
        width = int(max(20, pos.get('width', 140)))
        height = int(max(20, pos.get('height', 60)))

        return f"Left={x};Top={y};Right={x + width};Bottom={y + height};"

    def get_element_positions(self):
        return self.element_positions

    # ---- Sekcje pomocnicze ----

    def _generate_fallback_positions(self):
        positions = {}
        grid_rows = 0
        lane_offsets = {lane: 0 for lane in self._lane_order}

        flow = self.parsed_data.get('flow', [])
        for index, item in enumerate(flow):
            parser_id = item.get('id')
            if not parser_id:
                continue

            lane_name = item.get('swimlane')
            if lane_name not in lane_offsets:
                lane_offsets[lane_name] = 0
                self._lane_order.append(lane_name)

            lane_index = self._lane_order.index(lane_name) if lane_name in self._lane_order else 0
            lane_offset = lane_offsets.get(lane_name, 0)
            lane_offsets[lane_name] = lane_offset + 1

            x = 130 + lane_index * 280
            y = 120 + lane_offset * 160

            positions[parser_id] = {
                'x': x,
                'y': y,
                'width': 140,
                'height': 60,
                'row': lane_offset,
                'column': lane_index,
            }

            grid_rows = max(grid_rows, lane_offset + 1)

        grid_columns = max(1, len(self._lane_order))

        return positions, {
            'rows': grid_rows,
            'columns': grid_columns,
            'width': 1400,
            'height': max(800, grid_rows * 160 + 200),
        }

    def _coerce_dimensions(self, pos):
        coerced = dict(pos)
        coerced['x'] = int(coerced.get('x', 0))
        coerced['y'] = int(coerced.get('y', 0))
        coerced['width'] = int(max(20, coerced.get('width', 140)))
        coerced['height'] = int(max(20, coerced.get('height', 60)))
        return coerced

    def _debug_position_mapping(self):
        if not self.debug_positioning:
            return

        log_debug("📍 Mapowanie pozycji elementów (parser_id → x,y,w,h)")
        for pid, pos in self.element_positions.items():
            log_debug(f"   {pid}: {pos}")

# setup_logger('xmi_activity_generator.log')



class XMIActivityGenerator:
    """
    Generuje w pełni funkcjonalny diagram aktywności w formacie XMI (dla Enterprise Architect)
    na podstawie danych z parsera PlantUML, obsługując wszystkie kluczowe elementy.
    """

    def __init__(self, author: str = "Default_Author", debug_options: dict = None):
        self.author = author
        # Ustaw domyślne opcje debugowania
        self.debug_options = {
            'positioning': False,      # Debugowanie pozycji elementów
            'elements': False,         # Lista elementów diagramu
            'processing': False,       # Śledzenie przetwarzania elementów
            'transitions': False,      # Szczegóły tworzenia przejść
            'xml': False               # Debugowanie struktury XML
        }
        # Nadpisz domyślne opcje tymi przekazanymi w parametrze
        if debug_options:
            self.debug_options.update(debug_options)
        self.debug_positioning = self.debug_options.get('positioning', False)
        
        # DODAJ TU: Inicjalizacja flagi decision_else
        self._processing_decision_else = False
        
        self._reset_state()
        self.ns = {
            'uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi': 'http://schema.omg.org/spec/XMI/2.1'
        }
        self._register_namespaces()
        self.parser_id_to_xmi_id = {}

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
        self._processing_decision_else = False
        self.parser_id_to_xmi_id = {}
        self.node_documentation = {}
        self._pending_note_links = []
        self._activity_sequence = 0

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
        self.parsed_data = parsed_data  # Zapisz sparsowane dane jako atrybut klasy
        
        # Generowanie unikalnych identyfikatorów dla głównych elementów
        self.diagram_id = self._generate_ea_id("EAID")
        self.package_id = self._generate_ea_id("EAPK")
        self.main_activity_id = self._generate_ea_id("EAID")
        
        # Utworzenie podstawowej struktury dokumentu
        root = self._create_document_root()
        model = self._create_uml_model(root)
        package = self._create_diagram_package(model, diagram_name)
        main_activity = self._create_main_activity(package, diagram_name)
        
        # Krok 1: Utwórz wszystkie tory (swimlanes) jako partycje
        self._create_partitions_from_swimlanes(main_activity, parsed_data['swimlanes'])

        # Krok 2: Przetwarzaj przepływ, tworząc węzły i krawędzie (mapa parser→XMI)
        self._process_flow(main_activity, parsed_data['flow'])

        # Krok 3: Upewnij się, że wszystkie decyzje mają kompletne gałęzie
        self._ensure_complete_decision_branches(main_activity)

        # Krok 4: Utwórz i skonfiguruj LayoutManager, a następnie wyznacz pozycje
        self.layout_manager = self._create_layout_manager()
        layout_payload = self._build_layout_payload(parsed_data)
        self.element_positions, self.grid = self.layout_manager.analyze_diagram_structure(layout_payload)
        self.layout_manager.update_swimlane_geometry()

        if self.debug_options.get('positioning', False):
            self._analyze_decision_positioning()

        # Krok 5: Upewnij się, że typy są spójne w całym dokumencie
        self._ensure_element_type_consistency()
        
        # Krok 6: Zaktualizuj powiązania między partycjami a elementami
        self._update_partition_elements(main_activity)
        
        # Krok 7: Weryfikuj spójność diagramu
        self._verify_diagram_consistency()

        # Weryfikacja końcowa
        self._final_validation()

        # Krok 8: Stwórz rozszerzenia specyficzne dla Enterprise Architect
        self._create_ea_extensions(root, diagram_name)
                
        # Krok 8: Zwróć sformatowany XML
        return self._format_xml(root)

    def _final_validation(self):
        """Końcowa weryfikacja diagramu przed generowaniem XMI."""
        
        if self.debug_options.get('processing', False):
            print(f"\n🔍 KOŃCOWA WERYFIKACJA DIAGRAMU")
            log_debug(f"\n🔍 KOŃCOWA WERYFIKACJA DIAGRAMU")
        
        # 1. Sprawdź ActivityFinalNode z wyjściami
        final_nodes_with_outgoing = []
        for trans in self.transitions:
            source_node = self.id_map.get(trans['source_id'])
            if source_node and source_node.attrib.get('xmi:type') == 'uml:ActivityFinalNode':
                final_nodes_with_outgoing.append(trans)
        
        # Usuń nieprawidłowe przejścia
        for bad_trans in final_nodes_with_outgoing:
            self.transitions.remove(bad_trans)
            log_debug(f"Usunięto nieprawidłowe przejście z ActivityFinalNode: {bad_trans['id'][-6:]}")
        
        # 2. Sprawdź duplikaty przejść
        seen_transitions = set()
        duplicates_to_remove = []
        
        for trans in self.transitions:
            key = (trans['source_id'], trans['target_id'], trans.get('name', ''))
            if key in seen_transitions:
                duplicates_to_remove.append(trans)
            else:
                seen_transitions.add(key)
        
        # Usuń duplikaty
        for dup in duplicates_to_remove:
            self.transitions.remove(dup)
            log_debug(f"Usunięto duplikat przejścia: {dup['id'][-6:]}")
        
        # 3. Sprawdź izolowane węzły
        connected_nodes = set()
        for trans in self.transitions:
            connected_nodes.add(trans['source_id'])
            connected_nodes.add(trans['target_id'])
        
        isolated_nodes = []
        for node_id, node in self.id_map.items():
            node_type = node.attrib.get('xmi:type', '')
            if (node_id not in connected_nodes and 
                'ActivityPartition' not in node_type and 
                'Comment' not in node_type):
                isolated_nodes.append(node_id)
        
        if isolated_nodes:
            log_warning(f"Znaleziono {len(isolated_nodes)} izolowanych węzłów")
        
        # Podsumowanie
        if self.debug_options.get('processing', False):
            print(f"   Usunięto: {len(final_nodes_with_outgoing)} złych przejść z Final")
            print(f"   Usunięto: {len(duplicates_to_remove)} duplikatów przejść")
            print(f"   Ostrzeżenia: {len(isolated_nodes)} izolowanych węzłów")
            log_debug(f"Końcowa weryfikacja: usunięto {len(final_nodes_with_outgoing) + len(duplicates_to_remove)} przejść")

    def _analyze_decision_positioning(self):
        """Analizuje pozycjonowanie węzłów decyzyjnych i ich gałęzi."""
        if not self.debug_options.get('positioning', False):
            return
            
        print("\n=== ANALIZA POZYCJONOWANIA DECYZJI ===")
        log_debug("\n=== ANALIZA POZYCJONOWANIA DECYZJI ===")
        
        # Znajdź wszystkie węzły decyzyjne UŻYWAJĄC PEŁNYCH ID XMI
        for node_id, node in self.id_map.items():
            if node.attrib.get('xmi:type') == 'uml:DecisionNode':
                decision_name = node.attrib.get('name', 'unnamed')
                
                print(f"\n🔹 Decyzja: {node_id} '{decision_name}'")  # PEŁNE ID zamiast [-6:]
                log_debug(f"\n🔹 Decyzja: {node_id} '{decision_name}'")
                
                # Znajdź pozycję decyzji UŻYWAJĄC PEŁNEGO ID
                decision_pos = None
                if hasattr(self, 'layout_manager') and hasattr(self.layout_manager, 'element_positions'):
                    # POPRAWKA: Znajdź parser_id używając PEŁNEGO node_id
                    parser_id = None
                    for p_id, x_id in self.parser_id_to_xmi_id.items():
                        if x_id == node_id:  # Porównaj z pełnym ID
                            parser_id = p_id
                            break
                    
                    if parser_id and parser_id in self.layout_manager.element_positions:
                        decision_pos = self.layout_manager.element_positions[parser_id]
                        print(f"   Pozycja decyzji: kolumna={decision_pos['column']}, x={decision_pos['x']}")
                        log_debug(f"   Pozycja decyzji: kolumna={decision_pos['column']}, x={decision_pos['x']}")
                
                # Znajdź gałęzie tej decyzji UŻYWAJĄC PEŁNYCH ID
                yes_branches = []
                no_branches = []
                
                for trans in self.transitions:
                    if trans['source_id'] == node_id:  # PEŁNE ID
                        target_id = trans['target_id']   # PEŁNE ID
                        guard = trans.get('name', '')
                        target_node = self.id_map.get(target_id)
                        target_name = target_node.attrib.get('name', 'unnamed') if target_node else 'unknown'
                        
                        # Znajdź pozycję celu UŻYWAJĄC PEŁNEGO ID
                        target_pos = None
                        if hasattr(self, 'layout_manager') and hasattr(self.layout_manager, 'element_positions'):
                            target_parser_id = None
                            for p_id, x_id in self.parser_id_to_xmi_id.items():
                                if x_id == target_id:  # Porównaj z pełnym ID
                                    target_parser_id = p_id
                                    break
                            
                            if target_parser_id and target_parser_id in self.layout_manager.element_positions:
                                target_pos = self.layout_manager.element_positions[target_parser_id]
                        
                        if guard == 'tak':
                            yes_branches.append({
                                'id': target_id,
                                'name': target_name,
                                'position': target_pos
                            })
                        elif guard == 'nie':
                            no_branches.append({
                                'id': target_id,
                                'name': target_name,
                                'position': target_pos
                            })
                
                # Wyświetl wyniki z pełnymi ID
                print(f"   Gałęzie 'tak' ({len(yes_branches)}):")
                for branch in yes_branches:
                    pos_info = ""
                    if branch['position']:
                        pos_info = f" - kolumna={branch['position']['column']}, x={branch['position']['x']}"
                        if decision_pos:
                            relative = "LEWO" if branch['position']['x'] < decision_pos['x'] else "PRAWO" if branch['position']['x'] > decision_pos['x'] else "ŚRODEK"
                            pos_info += f" ({relative} od decyzji)"
                    
                    print(f"     - {branch['id']} '{branch['name']}'{pos_info}")
                    log_debug(f"     - {branch['id']} '{branch['name']}'{pos_info}")
                
                print(f"   Gałęzie 'nie' ({len(no_branches)}):")
                for branch in no_branches:
                    pos_info = ""
                    if branch['position']:
                        pos_info = f" - kolumna={branch['position']['column']}, x={branch['position']['x']}"
                        if decision_pos:
                            relative = "LEWO" if branch['position']['x'] < decision_pos['x'] else "PRAWO" if branch['position']['x'] > decision_pos['x'] else "ŚRODEK"
                            pos_info += f" ({relative} od decyzji)"
                    
                    print(f"     - {branch['id']} '{branch['name']}'{pos_info}")
                    log_debug(f"     - {branch['id']} '{branch['name']}'{pos_info}")

    def _process_flow(self, main_activity: ET.Element, flow: list):
        """Przetwarza listę elementów z poprawioną logiką gałęzi decyzyjnych."""
        if self._supports_new_parser(flow):
            self._process_flow_v2(main_activity, flow)
            return

        previous_node_id = None
        previous_swimlane = None
        structure_stack = []
        fork_source_id = None
        
        # Inicjalizacja słownika mapującego ID z parsera na ID XMI
        if not hasattr(self, 'parser_id_to_xmi_id'):
            self.parser_id_to_xmi_id = {}

        for i, item in enumerate(flow):
            current_swimlane = item.get('swimlane')
            item_type = item.get('type')
            parser_item_id = item.get('id')
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
            if self.debug_options.get('processing', False):
                print(f"Przetwarzanie elementu {i+1}/{len(flow)}: typ={item_type}, ID={parser_item_id}, tekst={item.get('text', '')}")
                log_debug(f"Przetwarzanie elementu {i+1}/{len(flow)}: typ={item_type}, ID={parser_item_id}, tekst={item.get('text', '')}")

            # Obsługa elementów przez odpowiednie handlery
            handler = handlers.get(item_type)
            if handler:
                # DODAJ TU: Ustaw flagę dla decision_else
                if item_type == 'decision_else':
                    self._processing_decision_else = True
                
                result = handler(item, main_activity, structure_stack, previous_node_id, partition_id)
                current_node_id = result.get('id')
                created_node_id = result.get('created_id')
                
                mapping_target_id = created_node_id or current_node_id

                # Zapisz mapowanie ID tylko jeśli oba ID są dostępne
                if parser_item_id and mapping_target_id:
                    self.parser_id_to_xmi_id[parser_item_id] = mapping_target_id
                    
                    # Dodatkowe debugowanie
                    if self.debug_options.get('processing', False):
                        print(f"  ✅ Mapowanie ID: {parser_item_id} → {mapping_target_id}")
                        log_debug(f"  ✅ Mapowanie ID: {parser_item_id} → {mapping_target_id}")
                        
                        # Sprawdź czy węzeł faktycznie istnieje w id_map
                        if mapping_target_id in self.id_map:
                            log_debug(f"  ✅ Węzeł {mapping_target_id[-6:]} istnieje w id_map")
                        else:
                            log_error(f"  ❌ Węzeł {mapping_target_id[-6:]} NIE istnieje w id_map!")

                    if created_node_id:
                        self._resolve_pending_note_links()
                
                # Obsługa specjalnych przypadków z result
                transition_needed = result.get('transition', True)
                special_source_id = result.get('prev_id')  # Dla fork_again
                
            elif item_type != 'swimlane':
                print(f"ℹ️ Pominięto nieznany element: {item_type}")

            # Tworzenie przejścia, jeśli jest to wymagane
            if transition_needed and previous_node_id and current_node_id:
                # Debugowanie przed utworzeniem przejścia
                if self.debug_options.get('transitions', False):
                    print(f"🔗 Próba utworzenia przejścia: {previous_node_id[-6:]} → {current_node_id[-6:]}")
                    log_debug(f"🔗 Próba utworzenia przejścia: {previous_node_id[-6:]} → {current_node_id[-6:]}")
                    log_debug(f"  Source w id_map: {previous_node_id in self.id_map}")
                    log_debug(f"  Target w id_map: {current_node_id in self.id_map}")
                
                # Sprawdź, czy mamy specjalne źródło dla tego przejścia
                source_id = special_source_id if special_source_id else previous_node_id
                
                # Pobierz ewentualną etykietę przejścia
                guard = self._get_guard_for_transition(structure_stack, item)
                
                # Dodaj przejście od źródła do bieżącego węzła
                self._add_transition(main_activity, source_id, current_node_id, name=guard)
            
            # Obsługa przypadków, gdy current_node_id jest None
            # (np. dla decision_else, które nie tworzy węzła)
            if current_node_id:
                previous_node_id = current_node_id
            # Jeśli current_node_id jest None, zachowaj poprzedni previous_node_id
                
            # Aktualizuj poprzedni swimlane
            if current_swimlane:
                previous_swimlane = current_swimlane
        
        # Po przetworzeniu wszystkich elementów
        self._connect_hanging_elements(main_activity)
        self._update_partition_elements(main_activity)
        self._debug_transitions_graph()

    def _connect_hanging_elements(self, main_activity):
        """Uproszczona metoda łączenia elementów bez wyjść."""
        
        # Znajdź elementy bez wyjść (oprócz węzłów końcowych)
        elements_without_outgoing = []
        final_nodes = []
        
        for node_id, node in self.id_map.items():
            node_type = node.attrib.get('xmi:type')
            
            if node_type == 'uml:ActivityFinalNode':
                final_nodes.append(node_id)
            else:
                # Sprawdź czy ma przejścia wychodzące
                has_outgoing = any(trans['source_id'] == node_id for trans in self.transitions)
                if not has_outgoing:
                    elements_without_outgoing.append(node_id)
        
        # Jeśli nie ma węzła końcowego, utwórz go
        if not final_nodes:
            final_id = self._add_node(main_activity, 'uml:ActivityFinalNode', 'Final', None)
            final_nodes.append(final_id)
            log_debug(f"Utworzono węzeł końcowy: {final_id[-6:]}")
        
        # Połącz elementy bez wyjść z pierwszym węzłem końcowym
        if elements_without_outgoing and final_nodes:
            main_final = final_nodes[0]
            
            for source_id in elements_without_outgoing:
                self._add_transition(main_activity, source_id, main_final)
                log_debug(f"Połączono element bez wyjścia {source_id[-6:]} z Final {main_final[-6:]}")
                
    def _remove_element_from_parent(self, element_to_remove, root_element):
        """Pomocnicza metoda do usuwania elementu z jego rodzica w drzewie XML."""
        # Funkcja rekurencyjna do przeszukiwania drzewa XML
        def find_and_remove(current_element):
            # Sprawdź czy element_to_remove jest bezpośrednim dzieckiem current_element
            for child in list(current_element):  # list() aby bezpiecznie iterować podczas usuwania
                if child is element_to_remove:
                    current_element.remove(child)
                    log_debug(f"Usunięto element z rodzica: {element_to_remove.attrib.get('xmi:id', 'unknown')[-6:]}")
                    return True
                
                # Rekurencyjnie przeszukuj dzieci
                if find_and_remove(child):
                    return True
            
            return False
        
        # Rozpocznij przeszukiwanie od głównego elementu aktywności
        if not find_and_remove(root_element):
            log_warning(f"Nie udało się znaleźć rodzica dla elementu: {element_to_remove.attrib.get('xmi:id', 'unknown')[-6:]}")

    def _debug_find_none_values(self, element, path=""):
        """Funkcja znajdująca wszystkie atrybuty None w drzewie XML."""
        current_path = f"{path}/{element.tag}" if path else element.tag
        
        for key, value in element.attrib.items():
            if value is None:
                print(f"⚠️ Znaleziono atrybut None: {current_path} -> {key}")
        
        for child in element:
            self._debug_find_none_values(child, current_path)

    def _handle_decision_end(self, item, parent, stack, prev_id, partition):
        """Poprawiona obsługa zakończenia bloku decyzyjnego."""
        if stack and stack[-1]['type'] == 'decision':
            decision_data = stack.pop()
            
            # Sprawdź czy potrzebujemy merge node
            if len(decision_data.get('branch_ends', [])) > 1:
                # Utwórz merge node dla łączenia gałęzi
                merge_node_id = self._add_node(parent, 'uml:MergeNode', '', partition)
                
                # Połącz wszystkie końce gałęzi z merge node
                for branch_end_id in decision_data['branch_ends']:
                    if branch_end_id and branch_end_id != merge_node_id:
                        self._add_transition(parent, branch_end_id, merge_node_id)
                
                return {'id': merge_node_id, 'transition': False}
            else:
                # Jeśli była tylko jedna gałąź, kontynuuj z poprzednim elementem
                return {'id': prev_id, 'transition': False}
        
        # Jeśli brak stosu decyzji, kontynuuj normalnie
        return {'id': prev_id, 'transition': False}

    def _debug_transitions_graph(self):
        """Generuje czytelną reprezentację grafu przejść dla celów analizy i debugowania."""
        if not self.debug_options.get('transitions', False):
            return
            
        log_debug("\n=== GRAF PRZEJŚĆ ===")
        print("\n=== GRAF PRZEJŚĆ ===")
        
        # Stwórz słownik węzłów
        nodes = {}
        for node_id, node in self.id_map.items():
            node_type = node.attrib.get('xmi:type', '').replace('uml:', '')
            node_name = node.attrib.get('name', '')
            
            # Skrócenie ID dla czytelności
            short_id = node_id[-6:] if node_id and len(node_id) >= 6 else node_id
            
            nodes[node_id] = {
                'short_id': short_id,
                'type': node_type,
                'name': node_name,
                'outgoing': [],
                'incoming': []
            }
        
        # Znajdź cykle i połączenia specjalne
        cycles = []
        self_connections = []
        decision_branches = {}
        
        # Wypełnij informacje o przejściach
        for trans in self.transitions:
            source_id = trans['source_id']
            target_id = trans['target_id']
            label = trans['name']
            
            # Wykrywanie przejść od węzła do siebie samego
            if source_id == target_id:
                self_connections.append({
                    'node_id': source_id,
                    'label': label
                })
                
            # Dodaj informacje o przejściach wychodzących i przychodzących do węzłów
            if source_id in nodes:
                nodes[source_id]['outgoing'].append((target_id, label))
            if target_id in nodes:
                nodes[target_id]['incoming'].append((source_id, label))
                
            # Identyfikuj gałęzie decyzyjne (tak/nie)
            if label in ['tak', 'nie']:
                if source_id not in decision_branches:
                    decision_branches[source_id] = {'tak': None, 'nie': None}
                decision_branches[source_id][label] = target_id
        
        # Wypisz informacje o każdym węźle
        for node_id, node_data in nodes.items():
            node_type = node_data['type']
            node_name = node_data['name']
            short_id = node_data['short_id']
            
            # Wyświetl podsumowanie węzła
            message = f"Węzeł: {short_id} [{node_type}] '{node_name}'"
            print(message)
            log_debug(message)
            
            # Wyświetl przejścia wchodzące
            if node_data['incoming']:
                print("  Przejścia wchodzące:")
                log_debug("  Przejścia wchodzące:")
                for source_id, label in node_data['incoming']:
                    source_short_id = source_id[-6:] if source_id and len(source_id) >= 6 else source_id
                    source_type = nodes[source_id]['type'] if source_id in nodes else '?'
                    label_str = f" [{label}]" if label else ""
                    in_message = f"    - z {source_short_id} [{source_type}]{label_str}"
                    print(in_message)
                    log_debug(in_message)
            else:
                print("  Brak przejść wchodzących (węzeł początkowy?)")
                log_debug("  Brak przejść wchodzących (węzeł początkowy?)")
            
            # Wyświetl przejścia wychodzące
            if node_data['outgoing']:
                print("  Przejścia wychodzące:")
                log_debug("  Przejścia wychodzące:")
                for target_id, label in node_data['outgoing']:
                    target_short_id = target_id[-6:] if target_id and len(target_id) >= 6 else target_id
                    target_type = nodes[target_id]['type'] if target_id in nodes else '?'
                    label_str = f" [{label}]" if label else ""
                    out_message = f"    - do {target_short_id} [{target_type}]{label_str}"
                    print(out_message)
                    log_debug(out_message)
            else:
                print("  Brak przejść wychodzących (węzeł końcowy?)")
                log_debug("  Brak przejść wychodzących (węzeł końcowy?)")
            
            print("")
            log_debug("")
        
        # Wyświetl zidentyfikowane problemy
        if self_connections:
            print("\n=== WYKRYTE POŁĄCZENIA DO SIEBIE SAMEGO ===")
            log_debug("\n=== WYKRYTE POŁĄCZENIA DO SIEBIE SAMEGO ===")
            for conn in self_connections:
                node_id = conn['node_id']
                node_type = nodes[node_id]['type'] if node_id in nodes else '?'
                node_name = nodes[node_id]['name'] if node_id in nodes else 'unnamed'
                message = f"  * Węzeł {node_id[-6:]} [{node_type}] '{node_name}' ma połączenie do siebie samego"
                print(message)
                log_debug(message)
                
        # Wyświetl informacje o węzłach decyzyjnych
        if decision_branches:
            print("\n=== WĘZŁY DECYZYJNE ===")
            log_debug("\n=== WĘZŁY DECYZYJNE ===")
            for decision_id, branches in decision_branches.items():
                decision_name = nodes[decision_id]['name'] if decision_id in nodes else 'unnamed'
                
                yes_id = branches.get('tak')
                yes_name = nodes[yes_id]['name'] if yes_id and yes_id in nodes else 'none'
                
                no_id = branches.get('nie') 
                no_name = nodes[no_id]['name'] if no_id and no_id in nodes else 'none'
                
                message = f"  * Decyzja: {decision_id[-6:]} '{decision_name}'"
                print(message)
                log_debug(message)
                
                message = f"    - Gałąź 'tak': {yes_id[-6:] if yes_id else 'brak'} '{yes_name}'"
                print(message)
                log_debug(message)
                
                message = f"    - Gałąź 'nie': {no_id[-6:] if no_id else 'brak'} '{no_name}'"
                print(message)
                log_debug(message)

        # Dodajmy sekcję identyfikującą problematyczne elementy
        problematic_nodes = []
        
        for node_id, node_data in nodes.items():
            # Elementy bez przejść wychodzących (niebędące węzłami końcowymi)
            if not node_data['outgoing'] and 'ActivityFinalNode' not in node_data['type']:
                problematic_nodes.append({
                    'id': node_id, 
                    'type': 'missing_outgoing',
                    'info': f"Węzeł {node_id[-6:]} [{node_data['type']}] '{node_data['name']}' nie ma przejść wychodzących"
                })
                
            # Elementy bez przejść wchodzących (niebędące węzłami początkowymi)
            if not node_data['incoming'] and 'InitialNode' not in node_data['type']:
                problematic_nodes.append({
                    'id': node_id, 
                    'type': 'missing_incoming',
                    'info': f"Węzeł {node_id[-6:]} [{node_data['type']}] '{node_data['name']}' nie ma przejść wchodzących"
                })
        
        # Wyświetlanie problemów
        if problematic_nodes:
            print("\n=== PROBLEMATYCZNE ELEMENTY ===")
            log_debug("\n=== PROBLEMATYCZNE ELEMENTY ===")
            for node in problematic_nodes:
                print(f"  * {node['info']}")
                log_debug(f"  * {node['info']}")
        

    def _handle_control(self, item, parent, stack, prev_id, partition):
        """Obsługuje węzły kontrolne z ulepszonym zarządzaniem Final."""
        action = item['action']
        
        if action == 'start':
            node_id = self._add_node(parent, 'uml:InitialNode', 'Initial', partition)
            self.diagram_objects.append({
                'id': node_id,
                'type': 'InitialNode'
            })
            return {'id': node_id, 'transition': True}
        
        elif action in ['end', 'stop']:
            existing_final = None
            for node_id, node in self.id_map.items():
                if node.attrib.get('xmi:type') == 'uml:ActivityFinalNode':
                    # Sprawdź czy ten Final nie ma zbyt wielu połączeń
                    incoming_count = sum(1 for t in self.transitions if t['target_id'] == node_id)
                    if incoming_count < 4:  # Maksymalnie 4 połączenia na Final
                        existing_final = node_id
                        break
            
            if existing_final:
                log_debug(f"Używam istniejącego węzła końcowego: {existing_final[-6:]}")
                return {'id': existing_final, 'transition': False}
            else:
                # Utwórz nowy węzeł końcowy tylko jeśli potrzebny
                node_id = self._add_node(parent, 'uml:ActivityFinalNode', 'Final', partition)
                self.diagram_objects.append({
                    'id': node_id,
                    'type': 'ActivityFinalNode'
                })
                log_debug(f"Utworzono nowy węzeł końcowy: {node_id[-6:]}")
                return {'id': node_id, 'transition': False}

    def _debug_diagram_objects(self):
        """Wyświetla informacje o elementach dodanych do diagramu."""
        if not self.debug_options.get('elements', False):
            return
            
        print(f"\n--- Elementy diagramu ({len(self.diagram_objects)}) ---")
        log_debug(f"\n--- Elementy diagramu ({len(self.diagram_objects)}) ---")
        for obj in self.diagram_objects:
            if isinstance(obj, dict):
                obj_id = obj.get('id', 'brak ID')
                obj_type = obj.get('type', 'nieznany typ')
                print(f" - {obj_type}: {obj_id[-6:]}")
                log_debug(f" - {obj_type}: {obj_id[-6:]}")
            else:
                print(f" - {obj}")
                log_debug(f" - {obj}")

    def _supports_new_parser(self, flow):
        if not flow:
            return False
        modern_types = {
            'start', 'end', 'activity', 'decision', 'merge',
            'repeat_start', 'repeat_end', 'loop_start', 'loop_end',
            'note'
        }
        return any(item.get('type') in modern_types for item in flow)

    def _format_activity_label(self, base_text: str) -> str:
        self._activity_sequence = getattr(self, '_activity_sequence', 0) + 1
        base = (base_text or '').strip()
        prefix = f"K{self._activity_sequence:02d}"
        if not base:
            return f"{prefix}. Activity"
        if base.upper().startswith(prefix.upper()):
            return base
        return f"{prefix}. {base}"

    def _normalize_note_text(self, raw_text: str) -> str:
        if raw_text is None:
            return ''

        text = str(raw_text)
        # Ujednolić znaki końca linii i usunąć sekwencje escape'owane
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = text.replace('\\r\\n', '\n').replace('\\r', '\n')
        text = text.replace('\\n', '\n')

        # Przytnij jedynie zbędne nowe linie na początku/końcu, zachowując wiodące spacje
        return text.strip('\n')

    def _create_comment_node(self, parent: ET.Element, raw_text: str, display_hint: str = None) -> tuple[str, ET.Element, str]:
        normalized = self._normalize_note_text(raw_text)
        label_source = display_hint if display_hint is not None else normalized
        display_label = (label_source or '').strip().replace('\n', ' ')
        if not display_label:
            display_label = 'Notatka'

        comment_id = self._generate_ea_id('EAID')
        attrs = self._sanitize_xml_attrs({
            'xmi:type': 'uml:Comment',
            'xmi:id': comment_id,
            'visibility': 'public',
            'name': display_label[:80]
        })

        comment_node = ET.SubElement(parent, 'ownedComment', attrs)
        if normalized:
            comment_node.set('documentation', normalized)

        body = ET.SubElement(comment_node, 'body')
        if normalized:
            body.text = normalized

        self.id_map[comment_id] = comment_node
        self.node_documentation[comment_id] = normalized
        return comment_id, comment_node, normalized

    def _process_flow_v2(self, main_activity: ET.Element, flow: list):
        self.parser_id_to_xmi_id = {}

        connections = self.parsed_data.get('logical_connections') or []
        referenced_parser_ids = set()
        for conn in connections:
            src = conn.get('source_id')
            tgt = conn.get('target_id')
            if src:
                referenced_parser_ids.add(src)
            if tgt:
                referenced_parser_ids.add(tgt)

        for item in flow:
            node_type = item.get('type')
            parser_id = item.get('id')
            swimlane = item.get('swimlane')
            partition_id = self.swimlane_ids.get(swimlane)
            created_id = None

            if node_type == 'start':
                created_id = self._add_node(main_activity, 'uml:InitialNode', 'Initial', partition_id)
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'InitialNode',
                    'parser_id': parser_id
                })
            elif node_type == 'end':
                final_name = item.get('text') or 'Final'
                created_id = self._add_node(main_activity, 'uml:ActivityFinalNode', final_name, partition_id)
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'ActivityFinalNode',
                    'parser_id': parser_id
                })
            elif node_type == 'activity':
                label = self._format_activity_label(item.get('text') or 'Activity')
                created_id = self._add_node(main_activity, 'uml:Action', label, partition_id)
                color = item.get('color')
                if color and created_id in self.id_map:
                    self.id_map[created_id].set('colorTag', color)
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'UML_ActivityNode',
                    'parser_id': parser_id,
                    'name': label
                })
            elif node_type == 'decision':
                condition = item.get('condition') or item.get('text') or 'Decision'
                created_id = self._add_node(main_activity, 'uml:DecisionNode', condition, partition_id)
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'DecisionNode',
                    'parser_id': parser_id
                })
            elif node_type == 'merge':
                if parser_id and parser_id not in referenced_parser_ids:
                    continue
                created_id = self._add_node(main_activity, 'uml:DecisionNode', 'Decyzja', partition_id)
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'DecisionNode',
                    'parser_id': parser_id,
                    'role': 'merge'
                })
            elif node_type == 'fork':
                variant = (item.get('variant') or 'fork').lower()
                label = 'Fork' if variant == 'fork' else 'Fork Branch'
                created_id = self._add_node(main_activity, 'uml:ForkNode', label, partition_id)
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'ForkNode',
                    'parser_id': parser_id,
                    'variant': variant
                })
            elif node_type == 'join':
                created_id = self._add_node(main_activity, 'uml:JoinNode', 'Join', partition_id)
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'JoinNode',
                    'parser_id': parser_id
                })
            elif node_type == 'repeat_start':
                created_id = self._add_node(main_activity, 'uml:Action', 'Repeat Body', partition_id)
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'UML_ActivityNode',
                    'parser_id': parser_id
                })
            elif node_type == 'repeat_end':
                condition = item.get('condition') or 'Loop Test'
                created_id = self._add_node(main_activity, 'uml:DecisionNode', f'Loop Test: {condition}', partition_id)
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'DecisionNode',
                    'parser_id': parser_id,
                    'role': 'loop_end'
                })
            elif node_type == 'note':
                created_id, comment_node, normalized = self._create_comment_node(
                    main_activity,
                    item.get('text') or 'Notatka',
                    display_hint=item.get('label')
                )
                attached_pid = item.get('attached_to_id') or item.get('attached_to')
                if attached_pid:
                    target_xmi = self.parser_id_to_xmi_id.get(attached_pid)
                    if target_xmi:
                        ET.SubElement(comment_node, 'annotatedElement', {'xmi:idref': target_xmi})
                    else:
                        self._pending_note_links.append((created_id, attached_pid))
                self.diagram_objects.append({
                    'id': created_id,
                    'type': 'Comment',
                    'parser_id': parser_id,
                    'text': normalized
                })
            else:
                # Nieznane typy pozostaw do starszego procesu
                continue

            if parser_id and created_id:
                self.parser_id_to_xmi_id[parser_id] = created_id
                self._resolve_pending_note_links()

        for conn in connections:
            source_parser = conn.get('source_id')
            target_parser = conn.get('target_id')
            source_id = self.parser_id_to_xmi_id.get(source_parser)
            target_id = self.parser_id_to_xmi_id.get(target_parser)
            if not source_id or not target_id:
                continue

            label = (conn.get('label') or conn.get('condition') or '').strip()
            if label.startswith('[') and label.endswith(']'):
                label = label[1:-1].strip()
            lower = label.lower()
            if lower in ('true', 'tak', 'yes'):
                label = 'tak'
            elif lower in ('false', 'nie', 'no'):
                label = 'nie'

            self._add_transition(main_activity, source_id, target_id, label)

        self._resolve_pending_note_links()
        self._verify_diagram_consistency()

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
    
    def _find_appropriate_target_for_missing_branch(self, item):
        """Znajduje odpowiedni węzeł docelowy dla brakującej gałęzi decyzyjnej."""
        partition_id = self.swimlane_ids.get(item.get('swimlane'))
        
        # Strategia 1: Szukaj najbliższego węzła join lub merge w tym samym torze
        for node_id, node in self.id_map.items():
            node_type = node.attrib.get('xmi:type', '')
            node_partition = node.attrib.get('inPartition')
            
            if node_partition == partition_id and ('JoinNode' in node_type or 'MergeNode' in node_type):
                if self.debug_options.get('processing', False):
                    print(f"Znaleziono cel dla brakującej gałęzi: {node_id[-6:]} [{node_type}]")
                    log_debug(f"Znaleziono cel dla brakującej gałęzi: {node_id[-6:]} [{node_type}]")
                return node_id
        
        # Strategia 2: Szukaj węzła końcowego w tym samym torze
        for node_id, node in self.id_map.items():
            node_type = node.attrib.get('xmi:type', '')
            node_partition = node.attrib.get('inPartition')
            
            if node_partition == partition_id and 'ActivityFinalNode' in node_type:
                if self.debug_options.get('processing', False):
                    print(f"Znaleziono węzeł końcowy dla brakującej gałęzi: {node_id[-6:]}")
                    log_debug(f"Znaleziono węzeł końcowy dla brakującej gałęzi: {node_id[-6:]}")
                return node_id
        
        # Strategia 3: Szukaj dowolnego węzła końcowego
        for node_id, node in self.id_map.items():
            if 'ActivityFinalNode' in node.attrib.get('xmi:type', ''):
                if self.debug_options.get('processing', False):
                    print(f"Znaleziono dowolny węzeł końcowy dla brakującej gałęzi: {node_id[-6:]}")
                    log_debug(f"Znaleziono dowolny węzeł końcowy dla brakującej gałęzi: {node_id[-6:]}")
                return node_id
        
        # Jeśli nie znaleziono odpowiedniego celu, zwróć None
        # W takim przypadku _ensure_complete_decision_branches utworzy nowy węzeł końcowy
        if self.debug_options.get('processing', False):
            print("Nie znaleziono odpowiedniego celu dla brakującej gałęzi")
            log_debug("Nie znaleziono odpowiedniego celu dla brakującej gałęzi")
        return None

    def _ensure_complete_decision_branches(self, parent_activity):
        """Upewnia się, że wszystkie węzły decyzyjne mają gałęzie 'tak' i 'nie'."""
        for item in self.parsed_data['flow']:
            if item['type'] == 'decision_start' and item.get('missing_else', False):
                # Pobierz ID węzła decyzyjnego z naszego mapowania
                parser_id = item.get('id')
                if parser_id in self.parser_id_to_xmi_id:
                    node_id = self.parser_id_to_xmi_id[parser_id]
                    
                    # Sprawdź, czy już ma gałąź 'nie'
                    has_no = False
                    for trans in self.transitions:
                        if trans['source_id'] == node_id and trans['name'] == 'nie':
                            has_no = True
                            break
                    
                    # Jeśli brak gałęzi 'nie', dodaj ją
                    if not has_no:
                        # Znajdź odpowiedni węzeł docelowy dla brakującej gałęzi
                        target_id = self._find_appropriate_target_for_missing_branch(item)
                        
                        if not target_id:
                            # Utwórz węzeł końcowy jako cel
                            target_id = self._add_node(parent_activity, 'uml:ActivityFinalNode', 'Final', 
                                                    self.swimlane_ids.get(item.get('swimlane')))
                        
                        # Dodaj przejście
                        self._add_transition(parent_activity, node_id, target_id, 'nie')
                        log_debug(f"Dodano brakującą gałąź 'nie' dla decyzji {node_id[-6:]}")


    def _determine_branch_type(self, node_id, decision_id, graph):
        """Określa typ gałęzi (tak/nie) dla danego węzła po decyzji."""
        # Znajdź przejście od decyzji do tego węzła
        for source_id, target_id in graph['edges']:
            if source_id == decision_id and target_id == node_id:
                # Sprawdź, czy to przejście ma etykietę
                for trans in self.transitions:
                    if trans['source_id'] == source_id and trans['target_id'] == target_id:
                        guard = trans.get('name', '').lower()
                        if 'tak' in guard:
                            return 'yes'
                        elif 'nie' in guard:
                            return 'no'
        
        # Jeśli nie znaleziono etykiety, spróbuj określić na podstawie innych informacji
        # (np. kolejności w flow, dodatkowych atrybutów)
        for i, item in enumerate(self.parsed_data['flow']):
            if item.get('id') == node_id:
                # Sprawdź, czy to element po decision_else
                if i > 0 and self.parsed_data['flow'][i-1].get('type') == 'decision_else':
                    return 'no'
        
        # Domyślnie zwróć 'yes' (gałąź "tak")
        return 'yes'
    
    def _handle_decision_start(self, item, parent, stack, prev_id, partition):
        """Obsługuje początek bloku decyzyjnego z lepszym śledzeniem poziomu."""
        node_id = self._add_node(parent, 'uml:DecisionNode', item.get('condition', 'Decision'), partition)
        
        # Określ poziom tej decyzji
        decision_level = len([s for s in stack if s.get('type') == 'decision']) + 1
        
        # Dodaj do listy obiektów diagramu
        self.diagram_objects.append({
            'id': node_id,
            'type': 'DecisionNode',
            'name': item.get('condition', 'Decision'),
            'parser_id': item.get('id')
        })
        
        # Dodaj na stos informację o decyzji z poziomem
        decision_data = {
            'type': 'decision',
            'id': node_id,
            'decision_level': decision_level,  # NOWE: poziom decyzji
            'missing_else': item.get('missing_else', False),
            'parser_id': item.get('id'),
            'branch_ends': [],
            'has_else': False,
            'then_label': item.get('then_label', 'tak'),
            'else_label': 'nie'
        }
        stack.append(decision_data)
    
        return {'id': node_id, 'transition': True}

    def _handle_decision_else(self, item, parent, stack, prev_id, partition):
        """Poprawiona obsługa else - nie tworzy nowego węzła."""
        if stack and stack[-1]['type'] == 'decision':
            decision_data = stack[-1]
            decision_data['has_else'] = True
            
            # Zwróć ID węzła decyzyjnego bez tworzenia przejścia
            return {
                'id': decision_data['id'],  # Istniejący węzeł decyzyjny
                'transition': False,        # Nie twórz przejścia
                'guard': 'nie'             # Ustaw etykietę dla następnego elementu
            }
        
        return {'id': prev_id, 'transition': False}

    def _handle_fork_start(self, item, parent, stack, prev_id, partition):
        """Obsługuje początek bloku fork."""
        node_id = self._add_node(parent, 'uml:ForkNode', 'Fork', partition)
        
        # Dodaj na stos informację o forku
        fork_data = {
            'type': 'fork',
            'id': node_id,
            'branch_ends': [],
            'parser_fork_id': item.get('id'),
            'branch_count': 0
        }
        stack.append(fork_data)
        
        return {'id': node_id, 'transition': True}

    def _handle_fork_again(self, item, parent, stack, prev_id, partition):
        """Obsługuje element fork again - początek kolejnej gałęzi równoległej."""
        if stack and stack[-1]['type'] == 'fork':
            fork_data = stack[-1]
            
            # Zwiększ licznik gałęzi
            fork_data['branch_count'] += 1
            
            # Dodaj poprzedni element jako koniec poprzedniej gałęzi
            if prev_id:
                fork_data['branch_ends'].append(prev_id)
            
            # Specjalne połączenie - zwróć ID forka jako źródło dla nowej gałęzi
            return {'id': None, 'transition': False, 'prev_id': fork_data['id']}
        
        log_warning("Znaleziono fork_again bez pasującego fork_start")
        return {'id': prev_id, 'transition': False}

    def _handle_fork_end(self, item, parent, stack, prev_id, partition):
        """Obsługuje zakończenie bloku fork/join."""
        if stack and stack[-1]['type'] == 'fork':
            fork_data = stack.pop()
            
            # Dodaj bieżący element jako koniec ostatniej gałęzi
            if prev_id:
                fork_data['branch_ends'].append(prev_id)
            
            # Znajdź powiązany parser_fork_id
            parser_fork_id = fork_data.get('parser_fork_id')
            
            # Utwórz węzeł join
            join_node_id = self._add_node(parent, 'uml:JoinNode', 'Join', partition)
            
            # Dodaj do listy obiektów diagramu
            self.diagram_objects.append({
                'id': join_node_id,
                'type': 'JoinNode',
                'related_fork_id': fork_data['id'],
                'parser_id': item.get('id')
            })
            
            # Połącz końce wszystkich gałęzi z join
            for branch_end_id in fork_data['branch_ends']:
                self._add_transition(parent, branch_end_id, join_node_id)
            
            # Sprawdź czy liczba znalezionych końców gałęzi zgadza się z oczekiwaną
            expected_branches = item.get('branches_count', 0) 
            actual_branches = len(fork_data['branch_ends'])
            
            if expected_branches != actual_branches:
                log_warning(f"Niezgodność liczby gałęzi fork: oczekiwano {expected_branches}, znaleziono {actual_branches}")
            
            log_debug(f"Zakończono blok fork, utworzono join: {join_node_id[-6:]} dla {actual_branches} gałęzi")
            return {'id': join_node_id, 'transition': True}
        
        log_warning("Znaleziono fork_end bez pasującego fork_start")
        return {'id': prev_id, 'transition': True}

    def _verify_diagram_consistency(self):
        """Weryfikuje spójność wygenerowanego diagramu."""
        # Sprawdź czy wszystkie węzły są osiągalne
        reachable_nodes = set()
        start_nodes = []
        
        # Znajdź węzły początkowe
        for node_id, node in self.id_map.items():
            if node.attrib.get('xmi:type') == 'uml:InitialNode':
                start_nodes.append(node_id)
        
        # Wykonaj przeszukiwanie grafu od każdego węzła początkowego
        for start_node in start_nodes:
            self._mark_reachable_nodes(start_node, reachable_nodes)
        
        # Sprawdź nieosiągalne węzły
        for node_id, node in self.id_map.items():
            if node_id not in reachable_nodes and node.attrib.get('xmi:type') != 'uml:ActivityPartition':
                log_warning(f"Nieosiągalny węzeł: {node_id[-6:]} typu {node.attrib.get('xmi:type')}")
        
        # Sprawdź węzły bez wyjść (poza końcowymi)
        for node_id, node in self.id_map.items():
            if node.attrib.get('xmi:type') not in ['uml:ActivityFinalNode', 'uml:ActivityPartition']:
                has_outgoing = False
                for trans in self.transitions:
                    if trans['source_id'] == node_id:
                        has_outgoing = True
                        break
                
                if not has_outgoing:
                    log_warning(f"Węzeł bez wyjść: {node_id[-6:]} typu {node.attrib.get('xmi:type')}")
        
        # Sprawdź błędy połączeń
        for trans in self.transitions:
            if trans['source_id'] == trans['target_id']:
                log_error(f"Przejście z węzła do siebie samego: {trans['id'][-6:]}")
                
            if trans['source_id'] not in self.id_map or trans['target_id'] not in self.id_map:
                log_error(f"Przejście do/z nieistniejącego węzła: {trans['id'][-6:]}")

    def _mark_reachable_nodes(self, node_id, reachable_nodes):
        """Pomocnicza funkcja rekurencyjna do znajdowania osiągalnych węzłów."""
        if node_id in reachable_nodes:
            return
        
        reachable_nodes.add(node_id)
        
        # Znajdź wszystkie węzły osiągalne z bieżącego
        for trans in self.transitions:
            if trans['source_id'] == node_id:
                self._mark_reachable_nodes(trans['target_id'], reachable_nodes)

    def _handle_note(self, item, parent, stack, prev_id, partition):
        """Obsługuje notatki (komentarze)."""
        note_id, note_element, normalized = self._create_comment_node(
            parent,
            item.get('text', ''),
            display_hint=item.get('title')
        )

        if prev_id:
            ET.SubElement(note_element, 'annotatedElement', {'xmi:idref': prev_id})
        else:
            # Jeśli nota odnosi się do konkretnego elementu, a nie ma prev_id, spróbuj z pola attached_to
            attached_to = item.get('attached_to_id') or item.get('attached_to')
            if attached_to:
                target_xmi = self.parser_id_to_xmi_id.get(attached_to)
                if target_xmi:
                    ET.SubElement(note_element, 'annotatedElement', {'xmi:idref': target_xmi})
                else:
                    self._pending_note_links.append((note_id, attached_to))

        self.diagram_objects.append({
            'id': note_id,
            'type': 'Comment',
            'text': normalized,
            'parser_id': item.get('id')
        })
        
        # Notatka sama nie tworzy przejść ani nie zmienia bieżącego elementu
        return {
            'id': prev_id,
            'transition': False,
            'created_id': note_id
        }

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

    def _resolve_pending_note_links(self):
        if not getattr(self, '_pending_note_links', None):
            return

        remaining = []
        for note_id, target_pid in self._pending_note_links:
            target_xmi = self.parser_id_to_xmi_id.get(target_pid)
            if target_xmi and note_id in self.id_map:
                note_element = self.id_map[note_id]
                ET.SubElement(note_element, 'annotatedElement', {'xmi:idref': target_xmi})
            else:
                remaining.append((note_id, target_pid))

        self._pending_note_links = remaining
    
    def _add_transition(self, parent, source_id, target_id, name=""):
        """Dodaje przejście z rozszerzoną walidacją logiczności."""
        
        # Pobierz węzły źródłowy i docelowy
        source_node = self.id_map.get(source_id)
        target_node = self.id_map.get(target_id)
        
        if source_node is None or target_node is None:
            return
        
        source_type = source_node.attrib.get('xmi:type')
        target_type = target_node.attrib.get('xmi:type')
        
        # KRYTYCZNA WALIDACJA LOGICZNOŚCI UML
        
        # 1. ActivityFinalNode NIE MOŻE mieć przejść wychodzących
        if source_type == 'uml:ActivityFinalNode':
            log_error(f"BŁĄD UML: ActivityFinalNode {source_id[-6:]} nie może mieć przejść wychodzących do {target_id[-6:]}")
            return
        
        # 2. InitialNode NIE MOŻE mieć przejść przychodzących (oprócz pierwszego)
        if target_type == 'uml:InitialNode':
            existing_incoming = sum(1 for t in self.transitions if t['target_id'] == target_id)
            if existing_incoming > 0:
                log_error(f"BŁĄD UML: InitialNode {target_id[-6:]} nie może mieć więcej niż jedno przejście przychodzące")
                return
        
        # 3. Sprawdź duplikaty
        existing = any(t['source_id'] == source_id and t['target_id'] == target_id 
                    for t in self.transitions)
        if existing:
            log_debug(f"Pomijam duplikat przejścia: {source_id[-6:]} -> {target_id[-6:]}")
            return
        
        # 4. Sprawdź samo-połączenia
        if source_id == target_id:
            log_warning(f"UWAGA: Samo-połączenie węzła {source_id[-6:]}")
            return
        
        # 5. Dodatkowa walidacja dla decision_else
        if hasattr(self, '_processing_decision_else') and self._processing_decision_else:
            log_debug(f"Przetwarzanie gałęzi NIE dla decyzji: {source_id[-6:]} → {target_id[-6:]}")
            self._processing_decision_else = False  # Reset flagi
        
        # Kontynuuj z tworzeniem przejścia...
        transition_id = self._generate_ea_id("EAID")
        attrs = {
            'xmi:type': 'uml:ControlFlow', 
            'xmi:id': transition_id, 
            'source': source_id, 
            'target': target_id,
            'visibility': 'public'
        }
        if name:
            attrs['name'] = name

        edge = ET.SubElement(parent, 'edge', self._sanitize_xml_attrs(attrs))
        
        # Dodaj referencje do węzłów
        ET.SubElement(source_node, 'outgoing', {'xmi:idref': transition_id})
        ET.SubElement(target_node, 'incoming', {'xmi:idref': transition_id})
        
        self.transitions.append({
            'id': transition_id, 
            'source_id': source_id, 
            'target_id': target_id, 
            'name': name,
            'cross_swimlane': False
        })
        
        log_debug(f"✅ Utworzono poprawne przejście: {source_id[-6:]} → {target_id[-6:]} ['{name}']")

    def _find_element_by_id(self, element_id):
        """Znajduje element XML na podstawie jego ID."""
        if not element_id:
            return None
        
        # Sprawdź, czy element istnieje w mapie ID
        if element_id in self.id_map:
            return self.id_map[element_id]
        
        # Jeśli nie znaleziono elementu, zwróć None
        return None
    
    def _get_guard_for_transition(self, structure_stack, item):
        """Zwraca wartość warunku (guard) dla przejścia na podstawie kontekstu."""
        item_type = item.get('type')
        
        if item_type == 'decision_start':
            return item.get('then_label', 'tak')
        
        if structure_stack:
            last_in_stack = structure_stack[-1]
            if last_in_stack.get('type') == 'decision' and last_in_stack.get('has_else'):
                return last_in_stack.get('else_label', 'nie')
        
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
        """Tworzy główny element dokumentu XMI."""
        root = ET.Element(f'{{{self.ns["xmi"]}}}XMI', {'xmi:version': '2.1'})
        
        # Dodaj dokumentację o eksporterze
        ET.SubElement(root, f'{{{self.ns["xmi"]}}}Documentation', {
            'exporter': 'Enterprise Architect',
            'exporterVersion': '6.5', 
            'exporterID': '1560'
        })
        
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

                if node_type.endswith('Comment'):
                    note_text = self.node_documentation.get(node_id)
                    if note_text:
                        props.set('documentation', note_text)
                        props.set('notes', note_text)
                        note_el = ET.SubElement(node_element, 'notes')
                        note_el.text = note_text

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
    
    def _verify_xmi_positions(self):
            """Weryfikuje rzeczywiste pozycje elementów w XMI względem ich poziomów/kolumn."""
            if not self.debug_positioning:
                return
                
            print(f"\n🔍 WERYFIKACJA POZYCJI XMI vs LOGIKA:")
            log_debug(f"\n🔍 WERYFIKACJA POZYCJI XMI vs LOGIKA:")
            
            # Zbierz informacje o decyzjach i ich gałęziach
            decisions = {}
            
            for parser_id, xmi_id in self.parser_id_to_xmi_id.items():
                # Sprawdź czy to decyzja
                if xmi_id in self.id_map:
                    node = self.id_map[xmi_id]
                    if node.attrib.get('xmi:type') == 'uml:DecisionNode':
                        decisions[xmi_id] = {
                            'parser_id': parser_id,
                            'name': node.attrib.get('name', 'unnamed'),
                            'yes_branches': [],
                            'no_branches': []
                        }
            
            # Znajdź gałęzie dla każdej decyzji
            for trans in self.transitions:
                source_id = trans['source_id']
                target_id = trans['target_id']
                guard = trans.get('name', '')
                
                if source_id in decisions:
                    target_parser_id = None
                    for p_id, x_id in self.parser_id_to_xmi_id.items():
                        if x_id == target_id:
                            target_parser_id = p_id
                            break
                    
                    if target_parser_id:
                        branch_info = {
                            'parser_id': target_parser_id,
                            'xmi_id': target_id,
                            'guard': guard
                        }
                        
                        if guard == 'tak':
                            decisions[source_id]['yes_branches'].append(branch_info)
                        elif guard == 'nie':
                            decisions[source_id]['no_branches'].append(branch_info)
            
            # Analizuj pozycje
            for decision_xmi_id, decision_info in decisions.items():
                decision_parser_id = decision_info['parser_id']
                decision_name = decision_info['name']
                
                print(f"\n🔹 DECYZJA: {decision_name} (XMI: {decision_xmi_id[-6:]}, Parser: {decision_parser_id})")
                log_debug(f"🔹 DECYZJA: {decision_name}")
                
                # Pozycja decyzji
                if hasattr(self, 'layout_manager') and hasattr(self.layout_manager, 'element_positions'):
                    if decision_parser_id in self.layout_manager.element_positions:
                        dec_pos = self.layout_manager.element_positions[decision_parser_id]
                        print(f"   Decyzja: poziom={dec_pos['row']}, kolumna={dec_pos['column']}, X={dec_pos['x']}, Y={dec_pos['y']}")
                        log_debug(f"   Decyzja: poziom={dec_pos['row']}, kolumna={dec_pos['column']}, X={dec_pos['x']}, Y={dec_pos['y']}")
                        
                        # Sprawdź gałęzie TAK
                        print(f"   Gałęzie TAK ({len(decision_info['yes_branches'])}):")
                        for branch in decision_info['yes_branches']:
                            if branch['parser_id'] in self.layout_manager.element_positions:
                                br_pos = self.layout_manager.element_positions[branch['parser_id']]
                                relative_x = "LEWO" if br_pos['x'] < dec_pos['x'] else "PRAWO" if br_pos['x'] > dec_pos['x'] else "ŚRODEK"
                                relative_y = "WYŻEJ" if br_pos['y'] < dec_pos['y'] else "NIŻEJ" if br_pos['y'] > dec_pos['y'] else "TEN SAM"
                                
                                print(f"     - {branch['parser_id']}: poziom={br_pos['row']}, kolumna={br_pos['column']}, X={br_pos['x']} ({relative_x}), Y={br_pos['y']} ({relative_y})")
                                log_debug(f"     - TAK {branch['parser_id']}: {relative_x}, {relative_y}")
                        
                        # Sprawdź gałęzie NIE
                        print(f"   Gałęzie NIE ({len(decision_info['no_branches'])}):")
                        for branch in decision_info['no_branches']:
                            if branch['parser_id'] in self.layout_manager.element_positions:
                                br_pos = self.layout_manager.element_positions[branch['parser_id']]
                                relative_x = "LEWO" if br_pos['x'] < dec_pos['x'] else "PRAWO" if br_pos['x'] > dec_pos['x'] else "ŚRODEK"
                                relative_y = "WYŻEJ" if br_pos['y'] < dec_pos['y'] else "NIŻEJ" if br_pos['y'] > dec_pos['y'] else "TEN SAM"
                                
                                print(f"     - {branch['parser_id']}: poziom={br_pos['row']}, kolumna={br_pos['column']}, X={br_pos['x']} ({relative_x}), Y={br_pos['y']} ({relative_y})")
                                log_debug(f"     - NIE {branch['parser_id']}: {relative_x}, {relative_y}")

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
                    

    def _create_diagrams_section(self, extension: ET.Element, diagram_name: str):
        """POPRAWIONA metoda z przekazywaniem wszystkich pozycji do XMI."""
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
        
        # POPRAWKA: Elementy diagramu - przekaż pozycje dla WSZYSTKICH elementów
        elements = ET.SubElement(diagram, 'elements')
        seq_no = 0
        
        if self.debug_options.get('positioning', False):
            print(f"\n📍 DODAWANIE ELEMENTÓW DO XMI:")
            log_debug(f"\n📍 DODAWANIE ELEMENTÓW DO XMI:")
        
        # KROK 1: Najpierw dodaj tory (swimlanes)
        for i, (name, partition_id) in enumerate(self.swimlane_ids.items()):
            if hasattr(self, 'layout_manager') and hasattr(self.layout_manager, 'swimlanes_geometry'):
                lane_geom = self.layout_manager.swimlanes_geometry.get(partition_id, {})
                left = lane_geom.get('x', 100 + i * 280)
                width = lane_geom.get('width', 250)
                height = lane_geom.get('height', 1050)
                top = lane_geom.get('y', 100)
            else:
                # Fallback pozycje
                left = 100 + i * 280
                width = 250
                height = 1050
                top = 100
            
            right = left + width
            bottom = top + height
            
            ET.SubElement(elements, 'element', self._sanitize_xml_attrs({
                'subject': partition_id,
                'seqno': str(seq_no),
                'geometry': f"Left={left};Top={top};Right={right};Bottom={bottom};",
                'style': "LineColor=15461355;FillColor=14993154;LineWidth=1;BorderStyle=0;VPartition=1;"
            }))
            seq_no += 1
            
            if self.debug_options.get('positioning', False):
                print(f"   🏊 Tor {name}: Left={left}, Top={top}, Right={right}, Bottom={bottom}")
                log_debug(f"   🏊 Tor {name}: Left={left}, Top={top}, Right={right}, Bottom={bottom}")
        
        # KROK 2: Dodaj WSZYSTKIE elementy z diagram_objects z pozycjami
        for obj in self.diagram_objects:
            if isinstance(obj, dict):
                node_id = obj.get('id')
                obj_type = obj.get('type', 'unknown')
                
                if node_id and node_id in self.id_map:
                    node = self.id_map[node_id]
                    
                    parser_id = next((p_id for p_id, x_id in self.parser_id_to_xmi_id.items() if x_id == node_id), None)

                    position = None
                    if hasattr(self, 'layout_manager'):
                        position = self.layout_manager.get_position_for_element(node)

                    if not position:
                        if parser_id:
                            raise RuntimeError(
                                f"Brak pozycji layoutu dla elementu parser_id={parser_id} (XMI {node_id})"
                            )
                        # Element bez powiązania z parserem (np. syntetyczny) – użyj kontrolowanego fallbacku
                        x = 350
                        y = 100 + seq_no * 80
                        width, height = self._get_element_dimensions_from_type(obj_type)
                        position = f"Left={x};Top={y};Right={x + width};Bottom={y + height};"
                        if self.debug_options.get('positioning', False):
                            log_warning(f"Fallback pozycji dla syntetycznego elementu {node_id[-6:]} ({obj_type})")

                    if position:
                        # Określ styl na podstawie typu elementu
                        style = self._get_element_style_from_type(obj_type, node)
                        
                        # Dodaj element do diagramu
                        element_attrs = {
                            'subject': node_id,
                            'seqno': str(seq_no),
                            'geometry': position,
                            'style': style
                        }

                        note_text = self.node_documentation.get(node_id)
                        if obj_type == 'Comment' and note_text:
                            element_attrs['documentation'] = note_text

                        element_el = ET.SubElement(elements, 'element', self._sanitize_xml_attrs(element_attrs))

                        if obj_type == 'Comment' and note_text:
                            notes_el = ET.SubElement(element_el, 'notes')
                            notes_el.text = note_text
                        seq_no += 1
                        
                        if self.debug_options.get('positioning', False):
                            print(f"   ✅ Dodano {obj_type} {node_id[-6:]}: {position}")
                            log_debug(f"   ✅ Dodano {obj_type} {node_id[-6:]}: {position}")
                    else:
                        log_error(f"Nie udało się nadać pozycji elementowi {node_id}")
        
        # KROK 3: Dodaj pozostałe elementy z id_map, które nie są w diagram_objects
        added_ids = {obj.get('id') for obj in self.diagram_objects if isinstance(obj, dict) and obj.get('id')}
        added_ids.update(self.swimlane_ids.values())  # Dodaj ID torów
        
        for node_id, node in self.id_map.items():
            if node_id not in added_ids:
                parser_id = next((p_id for p_id, x_id in self.parser_id_to_xmi_id.items() if x_id == node_id), None)

                position = None
                if hasattr(self, 'layout_manager'):
                    position = self.layout_manager.get_position_for_element(node)

                if not position:
                    if parser_id:
                        raise RuntimeError(
                            f"Brak pozycji layoutu dla elementu parser_id={parser_id} (XMI {node_id})"
                        )
                    # Element syntetyczny – zastosuj kontrolowany fallback
                    x = 350
                    y = 100 + seq_no * 80
                    width, height = 140, 60
                    position = f"Left={x};Top={y};Right={x + width};Bottom={y + height};"

                if position:
                    node_type = node.attrib.get('xmi:type', '')
                    style = self._get_style_for_element(node)
                    
                    element_attrs = {
                        'subject': node_id,
                        'seqno': str(seq_no),
                        'geometry': position,
                        'style': style
                    }
                    note_text = self.node_documentation.get(node_id)
                    if node_type.endswith('Comment') and note_text:
                        element_attrs['documentation'] = note_text

                    element_el = ET.SubElement(elements, 'element', self._sanitize_xml_attrs(element_attrs))

                    if node_type.endswith('Comment') and note_text:
                        notes_el = ET.SubElement(element_el, 'notes')
                        notes_el.text = note_text
                    seq_no += 1
                    
                    if self.debug_options.get('positioning', False):
                        print(f"   📎 Dodano dodatkowy element {node_id[-6:]}: {position}")
                        log_debug(f"   📎 Dodano dodatkowy element {node_id[-6:]}: {position}")
        
        # KROK 4: Dodaj linki diagramu
        self._add_diagram_links(diagram)
        
        if self.debug_options.get('positioning', False):
            print(f"✅ Zakończono dodawanie elementów: {seq_no} elementów w XMI")
            log_debug(f"✅ Zakończono dodawanie elementów: {seq_no} elementów w XMI")
        
        return diagram

    def _get_element_dimensions_from_type(self, obj_type):
        """Zwraca wymiary elementu na podstawie jego typu."""
        dimensions = {
            'InitialNode': (20, 20),
            'ActivityFinalNode': (20, 20),
            'DecisionNode': (40, 40),
            'MergeNode': (40, 40),
            'ForkNode': (60, 10),
            'JoinNode': (60, 10),
            'UML_ActivityNode': (140, 60),
            'Comment': (120, 80),
            'ActivityPartition': (250, 1050)
        }
        return dimensions.get(obj_type, (140, 60))  # Domyślne wymiary

    def _get_element_style_from_type(self, obj_type, node):
        """Zwraca styl elementu na podstawie typu z obj_type."""
        node_name = node.attrib.get('name', '').lower()
        
        if obj_type == 'InitialNode':
            return "BorderColor=-1;BorderWidth=-1;BColor=0;FontColor=-1;BorderWidth=0;Shape=Circle;"
        elif obj_type == 'ActivityFinalNode':
            return "BorderColor=-1;BorderWidth=-1;BColor=0;FontColor=-1;BorderWidth=1;Shape=Circle;"
        elif obj_type in ['DecisionNode', 'MergeNode']:
            return "BorderColor=-1;BorderWidth=-1;BColor=16777062;FontColor=-1;Shape=Diamond;"
        elif obj_type in ['ForkNode', 'JoinNode']:
            return "BorderColor=-1;BorderWidth=-1;BColor=0;FontColor=-1;LineWidth=3;Shape=Rectangle;"
        elif obj_type == 'Comment':
            return "BorderColor=-1;BorderWidth=-1;BColor=16777215;FontColor=-1;BorderStyle=Dashed;"
        elif obj_type == 'UML_ActivityNode':
            # Kolorowanie na podstawie nazwy
            if 'pozytywny' in node_name:
                return "BorderColor=-1;BorderWidth=-1;BColor=8454143;FontColor=-1;BorderRadius=10;"
            elif 'negatywny' in node_name or 'błąd' in node_name or 'blad' in node_name:
                return "BorderColor=-1;BorderWidth=-1;BColor=5263615;FontColor=-1;BorderRadius=10;"
            elif 'wizualn' in node_name:
                return "BorderColor=-1;BorderWidth=-1;BColor=42495;FontColor=-1;BorderRadius=10;"
            else:
                return "BorderColor=-1;BorderWidth=-1;BColor=13434828;FontColor=-1;BorderRadius=10;"
        else:
            # Domyślny styl
            return "BorderColor=-1;BorderWidth=-1;BColor=16777215;FontColor=-1;"

    def _get_element_style(self, obj_id):
        """Zwraca styl elementu na podstawie jego typu."""
        if obj_id in self.id_map and 'xmi:type' in self.id_map[obj_id].attrib:
            uml_type = self.id_map[obj_id].attrib['xmi:type']
            
            if 'uml:InitialNode' in uml_type or 'uml:ActivityFinalNode' in uml_type:
                return "BorderColor=-1;BorderWidth=-1;BColor=0;FontColor=-1;BorderWidth=1;Shape=Circle;"
            elif 'uml:DecisionNode' in uml_type:
                return "BorderColor=-1;BorderWidth=-1;BColor=16777062;FontColor=-1;Shape=Diamond;"
            elif 'uml:Action' in uml_type:
                return "BorderColor=-1;BorderWidth=-1;BColor=13434828;FontColor=-1;BorderRadius=10;"
            elif 'uml:Comment' in uml_type:
                return "BorderColor=-1;BorderWidth=-1;BColor=16777215;FontColor=-1;BorderStyle=Dashed;"
        
        # Domyślny styl
        return "BorderColor=-1;BorderWidth=-1;BColor=16777215;FontColor=-1;"

    def _add_diagram_links(self, diagram):
        """Dodaje linki między elementami na diagramie."""
        diagramlinks = ET.SubElement(diagram, 'diagramlinks')
        
        # Dodaj link dla każdego przejścia
        for trans in self.transitions:
            connector_id = trans['id']
            link = ET.SubElement(diagramlinks, 'diagramlink', {
                'connectorID': connector_id,
                'hidden': 'false'
            })
            
            # Dodaj styl dla linku
            style_value = ""
            if trans.get('cross_swimlane', False):
                style_value = "mode=3;routestyle=1;"
                
            ET.SubElement(link, 'style', {'value': style_value})

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

    def _build_layout_payload(self, parsed_data: dict) -> dict:
        """Przygotowuje dane wejściowe dla layoutu, dodając przejścia z generatora."""
        payload = copy.deepcopy(parsed_data) if parsed_data else {}

        logical_connections = list(payload.get('logical_connections', []))
        existing_keys = {
            (
                conn.get('source_id') or conn.get('from'),
                conn.get('target_id') or conn.get('to'),
                (conn.get('label') or conn.get('condition') or '').strip(),
            )
            for conn in logical_connections
        }

        inverse_mapping = {xmi_id: parser_id for parser_id, xmi_id in self.parser_id_to_xmi_id.items()}

        for transition in self.transitions:
            src_parser = inverse_mapping.get(transition['source_id'])
            tgt_parser = inverse_mapping.get(transition['target_id'])
            if not src_parser or not tgt_parser:
                continue

            label = (transition.get('name') or '').strip()
            key = (src_parser, tgt_parser, label)
            if key in existing_keys:
                continue

            logical_connections.append({
                'source_id': src_parser,
                'target_id': tgt_parser,
                'label': label,
            })
            existing_keys.add(key)

        payload['logical_connections'] = logical_connections
        return payload

    def _create_layout_manager(self):
        """Tworzy instancję LayoutManager z wszystkimi potrzebnymi danymi."""
        layout_manager = LayoutManagerAdapter(
            self.swimlane_ids,
            parsed_data=self.parsed_data,
            transitions=self.transitions,
            id_map=self.id_map,
            debug_positioning=self.debug_options.get('positioning', False)
        )
        
        # Przekaż mapowanie parser_id → xmi_id
        if hasattr(self, 'parser_id_to_xmi_id'):
            layout_manager.set_parser_mapping(self.parser_id_to_xmi_id)

        # Diagnostyka po utworzeniu
        if self.debug_options.get('positioning', False):
            layout_manager._debug_position_mapping()
        
        return layout_manager

    def set_parser_mapping(self, parser_id_to_xmi_id):
        """Ustawia mapowanie między parser_id a xmi_id."""
        self.parser_id_to_xmi_id = parser_id_to_xmi_id or {}

        if hasattr(self, 'layout_manager') and self.layout_manager:
            self.layout_manager.set_parser_mapping(self.parser_id_to_xmi_id)

        if self.debug_positioning:
            print(f"📋 Ustawiono mapowanie parser→XMI: {len(self.parser_id_to_xmi_id)} elementów")
            log_debug(f"📋 Mapowanie parser→XMI ustawione: {len(self.parser_id_to_xmi_id)} elementów")

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
        if self.debug_options.get('xml', False):
            print("Sprawdzanie wartości None w drzewie XML...")
            log_debug("Sprawdzanie wartości None w drzewie XML...")
            self._debug_find_none_values(root)
        
        # Zastosuj sanityzację do całego drzewa XML rekurencyjnie
        self._sanitize_tree(root)
        
        xml_string = ET.tostring(root, encoding='unicode', method='xml', xml_declaration=True)
        xml_string_fixed = xml_string.replace("<?xml version='1.0' encoding='unicode'?>", '<?xml version="1.0" encoding="UTF-8"?>')
        dom = xml.dom.minidom.parseString(xml_string_fixed)
        return dom.toprettyxml(indent="  ")

# --- Przykład użycia ---
if __name__ == '__main__':
    import argparse
    import os
    from datetime import datetime
    
    setup_logger('xmi_activity_generator.log')
    
    # Utworzenie parsera argumentów z bezpośrednią obsługą plików PlantUML
    parser = argparse.ArgumentParser(description='Generator XMI dla diagramów aktywności')
    parser.add_argument('input_file', nargs='?', default='diagram_aktywnosci_PlantUML.puml',
                        help='Plik wejściowy z kodem PlantUML')
    parser.add_argument('--output', '-o', 
                        help='Plik wyjściowy XMI (domyślnie: diagram_aktywnosci_[timestamp].xmi)')
    
    # Opcje parsowania PlantUML
    parser.add_argument('--parse-debug', '-pd', action='store_true', 
                        help='Włącz debugowanie parsowania')
    parser.add_argument('--parse-decisions', '-pdec', action='store_true', 
                        help='Włącz debugowanie decyzji w parserze')
    parser.add_argument('--parse-structure', '-ps', action='store_true', 
                        help='Włącz debugowanie struktury w parserze')
    parser.add_argument('--parse-connections', '-pc', action='store_true', 
                        help='Włącz debugowanie połączeń w parserze')
    
    # Opcje generowania XMI
    parser.add_argument('--debug-positioning', '-dp', action='store_true', 
                        help='Włącz debugowanie pozycjonowania elementów')
    parser.add_argument('--debug-elements', '-de', action='store_true', 
                        help='Pokaż listę elementów diagramu')
    parser.add_argument('--debug-processing', '-dpr', action='store_true', 
                        help='Włącz szczegółowe śledzenie przetwarzania elementów')
    parser.add_argument('--debug-transitions', '-dt', action='store_true', 
                        help='Pokaż szczegóły tworzenia przejść')
    parser.add_argument('--debug-xml', '-dx', action='store_true', 
                        help='Włącz debugowanie struktury XML')
    parser.add_argument('--debug', '-d', action='store_true', 
                        help='Włącz podstawowe opcje debugowania')
    parser.add_argument('--debug-all', '-da', action='store_true', 
                        help='Włącz wszystkie opcje debugowania')
    
    args = parser.parse_args()
    
    # Konfiguracja opcji debugowania dla parsera PlantUML
    parser_debug_options = {
        'parsing': args.parse_debug or args.debug or args.debug_all,
        'decisions': args.parse_decisions or args.debug or args.debug_all,
        'structure': args.parse_structure or args.debug_all,
        'connections': args.parse_connections or args.debug or args.debug_all,
    }
    
    # Konfiguracja opcji debugowania dla generatora XMI
    generator_debug_options = {
        'positioning': args.debug_positioning or args.debug_all,
        'elements': args.debug_elements or args.debug or args.debug_all,
        'processing': args.debug_processing or args.debug_all,
        'transitions': args.debug_transitions or args.debug or args.debug_all,
        'xml': args.debug_xml or args.debug_all
    }
    
    # Ustawienie nazwy pliku wyjściowego
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        output_filename = args.output
    else:
        basename = os.path.splitext(os.path.basename(args.input_file))[0]
        output_filename = f"{basename}_{timestamp}.xmi"
    
    # Nazwa diagramu - użyj nazwy pliku wejściowego bez rozszerzenia
    diagram_name = os.path.splitext(os.path.basename(args.input_file))[0].replace("_", " ").title()
    
    try:
        # Wczytaj plik PlantUML
        with open(args.input_file, 'r', encoding='utf-8') as f:
            puml_content = f.read()
        
        # Wyświetl informacje o uruchamianiu
        print(f"🔍 Przetwarzanie pliku: {args.input_file}")
        print(f"📊 Nazwa diagramu: {diagram_name}")
        
        # Parsowanie PlantUML bezpośrednio
        print("🔄 Parsowanie kodu PlantUML...")
        parser = PlantUMLActivityParser(puml_content, parser_debug_options)
        parsed_data = parser.parse()
        
        # Generowanie XMI
        print("🔄 Generowanie XMI...")
        generator = XMIActivityGenerator(author="Generator XMI", debug_options=generator_debug_options)
        xml_content = generator.generate_activity_diagram(diagram_name, parsed_data)
        
        # Zapisz wynikowy XMI
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"\n✅ Gotowe! Diagram XMI zapisany do pliku: {output_filename}")
        
    except FileNotFoundError:
        print(f"❌ Błąd: Nie znaleziono pliku {args.input_file}")
    except Exception as e:
        print(f"❌ Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()
