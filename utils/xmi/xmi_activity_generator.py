import xml.etree.ElementTree as ET
import uuid
from datetime import datetime
import xml.dom.minidom
import sys
import re 
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)

# PODSTAWOWE IMPORTY - ZAWSZE POTRZEBNE
try:
    from utils.logger_utils import log_debug, log_info, log_error, log_exception, log_warning, setup_logger
    from utils.plantuml.plantuml_activity_parser import PlantUMLActivityParser
except ImportError as e:
    print(f"❌ Krytyczny błąd importu podstawowych modułów: {e}")
    sys.exit(1)

try:
    from utils.xmi.ai_layout_manager import AILayoutManager
    AI_LAYOUT_AVAILABLE = True
    log_info("✅ AI Layout Manager zaimportowany pomyślnie!")
except ImportError as e:
    AI_LAYOUT_AVAILABLE = False
    log_warning(f"⚠️ AI Layout Manager niedostępny: {e}")
except Exception as e:
    AI_LAYOUT_AVAILABLE = False
    log_error(f"❌ Błąd importu AI Layout Manager: {e}")

try:
    graph_layout_path = os.path.join(os.path.dirname(__file__), 'graph_layout_manager.py')
    if os.path.exists(graph_layout_path):
        from utils.xmi.graph_layout_manager import GraphLayoutManager
        GRAPH_LAYOUT_AVAILABLE = True
        log_info("✅ GraphLayoutManager dostępny")
    else:
        GRAPH_LAYOUT_AVAILABLE = False
        log_warning("⚠️ graph_layout_manager.py nie istnieje")
except ImportError as e:
    GRAPH_LAYOUT_AVAILABLE = False
    log_warning(f"⚠️ GraphLayoutManager niedostępny: {e}")

setup_logger('xmi_activity_generator.log')

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
        

        self.canvas_width = 1800   # Szerokość canvas
        self.canvas_height = 1600  # Wysokość canvas
        self.margin_x = 50         # Margines poziomy
        self.margin_y = 50         # Margines pionowy
        
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
        
        # Utwórz i zapisz instancję LayoutManager
        self.layout_manager = self._create_layout_manager()
        
        # Przeprowadź analizę struktury diagramu i utwórz siatkę pozycjonowania
        if self.debug_options.get('positioning', False):
            log_debug(f"🚀 WYWOŁANIE analyze_diagram_structure z {len(parsed_data.get('flow', []))} elementami")
    
        # DEBUGOWANIE: Sprawdź co faktycznie zwraca metoda
        result = self.layout_manager.analyze_diagram_structure(parsed_data)
        
        if self.debug_options.get('positioning', False):
            log_debug(f"🔍 analyze_diagram_structure zwróciło: {type(result)}")
            log_debug(f"🔍 Zawartość: {result if not isinstance(result, dict) or len(result) < 10 else f'dict z {len(result)} kluczami'}")
        
        # Inteligentne przypisanie na podstawie typu zwróconej wartości
        if isinstance(result, tuple) and len(result) == 2:
            # Prawidłowy format - tuple (positions, grid)
            self.element_positions, self.grid = result
        elif isinstance(result, dict):
            # Zwrócono tylko positions
            self.element_positions = result
            self.grid = None
        else:
            # Nieoczekiwany format
            log_warning(f"⚠️ analyze_diagram_structure zwróciło nieoczekiwany typ: {type(result)}")
            self.element_positions = {}
            self.grid = None
        
        if self.debug_options.get('positioning', False):
            if isinstance(self.element_positions, dict):
                log_debug(f"🎯 ELEMENT POSITIONS: {len(self.element_positions)} pozycji")
                for elem_id, pos in list(self.element_positions.items())[:3]:
                    log_debug(f"   {elem_id}: {pos}")
            log_debug(f"🎯 GRID: {self.grid}")
        
        # Krok 2: Przetwarzaj przepływ, tworząc węzły i krawędzie
        self._process_flow(main_activity, parsed_data['flow'])

        # ✅ KROK 2.5: Dodaj brakujące gałęzie "tak" dla decyzji
        missing_branches = self._add_missing_decision_branches(main_activity)  
        if missing_branches > 0:
            log_debug(f"🔗 Naprawiono {missing_branches} brakujących gałęzi decyzji")

        #Zaktualizuj geometrię torów na podstawie faktycznych pozycji elementów
        self.layout_manager.update_swimlane_geometry()
        
        # Krok 3: Upewnij się, że wszystkie decyzje mają kompletne gałęzie
        self._ensure_complete_decision_branches(main_activity)
        
        # Krok 4: Upewnij się, że typy są spójne w całym dokumencie
        self._ensure_element_type_consistency()
        
        # Krok 5: Zaktualizuj powiązania między partycjami a elementami
        self._update_partition_elements(main_activity)
        
        # Krok 6: Weryfikuj spójność diagramu
        self._verify_diagram_consistency()
        
        
        self._final_validation()


        if not self._validate_unique_elements():
            log_warning("⚠️ Wykryto duplikaty elementów - sprawdź logi")

        # Krok 7: Stwórz rozszerzenia specyficzne dla Enterprise Architect
        self._create_ea_extensions(root, diagram_name)
                
        # Krok 8: Zwróć sformatowany XML
        return self._format_xml(root)

    def _analyze_decision_positioning(self):
        """POPRAWIONA analiza z wykrywaniem duplikatów i weryfikacją pozycji."""
        if not self.debug_options.get('positioning', False):
            return
            
        log_debug("\n=== ANALIZA POZYCJONOWANIA DECYZJI ===")
        
        # ✅ KROK 1: GRUPUJ DECYZJE WEDŁUG NAZWY (wykryj duplikaty)
        decision_groups = {}
        for node_id, node in self.id_map.items():
            if node.attrib.get('xmi:type') == 'uml:DecisionNode':
                decision_name = node.attrib.get('name', 'unnamed')
                
                if decision_name not in decision_groups:
                    decision_groups[decision_name] = []
                decision_groups[decision_name].append({
                    'xmi_id': node_id,
                    'name': decision_name
                })
        
        # ✅ KROK 2: WYKRYJ I ZGŁOŚ DUPLIKATY
        duplicates = {name: nodes for name, nodes in decision_groups.items() if len(nodes) > 1}
        
        if duplicates:
            log_debug(f"\n⚠️ WYKRYTO DUPLIKATY DECYZJI:")
            for decision_name, node_list in duplicates.items():
                log_debug(f"   '{decision_name}': {len(node_list)} wystąpień")
                for i, node_data in enumerate(node_list):
                    log_debug(f"      {i+1}. XMI: {node_data['xmi_id'][-6:]}")
        
        # ✅ KROK 3: ANALIZUJ KAŻDĄ UNIKALNĄ DECYZJĘ
        unique_decisions = {name: nodes[0] for name, nodes in decision_groups.items() if len(nodes) == 1}
        
        for decision_name, decision_data in unique_decisions.items():
            node_id = decision_data['xmi_id']
            
            log_debug(f"\n🔹 DECYZJA: '{decision_name}' (XMI: {node_id[-6:]})")
            
            # ✅ KROK 3A: ZNAJDŹ POZYCJĘ DECYZJI
            decision_pos = None
            decision_parser_id = None
            
            # Znajdź parser_id dla tej decyzji
            if hasattr(self, 'parser_id_to_xmi_id'):
                for p_id, x_id in self.parser_id_to_xmi_id.items():
                    if x_id == node_id:
                        decision_parser_id = p_id
                        break
            
            # Pobierz pozycję z layout managera
            if (decision_parser_id and 
                hasattr(self, 'layout_manager') and 
                hasattr(self.layout_manager, 'element_positions') and
                decision_parser_id in self.layout_manager.element_positions):
                
                decision_pos = self.layout_manager.element_positions[decision_parser_id]
                log_debug(f"   📍 Pozycja decyzji: row={decision_pos.get('grid_row', 'N/A')}, column={decision_pos.get('grid_col', 'N/A')}, X={decision_pos['x']}, Y={decision_pos['y']}")
            else:
                log_debug(f"   ⚠️ Brak pozycji dla decyzji (parser_id: {decision_parser_id})")
            
            # ✅ KROK 3B: ZNAJDŹ WSZYSTKIE GAŁĘZIE TEJ DECYZJI
            yes_branches = []
            no_branches = []
            unlabeled_branches = []
            
            for trans in self.transitions:
                if trans['source_id'] == node_id:
                    label = trans.get('name', '').lower()
                    target_id = trans['target_id']
                    target_name = "unknown"
                    
                    # ✅ NAPRAWIONE: Sprawdź czy target_node istnieje
                    if target_id in self.id_map:
                        target_node = self.id_map[target_id] 
                        target_name = target_node.attrib.get('name', 'unnamed') if target_node is not None else 'unknown'
                    
                    branch_info = f"{target_id[-6:]} ({target_name})"
                    
                    if label in ['tak', 'yes', 'true']:
                        yes_branches.append(branch_info)
                    elif label in ['nie', 'no', 'false']:
                        no_branches.append(branch_info)
                    else:
                        unlabeled_branches.append(branch_info)
            
            # ✅ KROK 3C: WYŚWIETL GAŁĘZIE "TAK"
            log_debug(f"   🟢 Gałęzie 'TAK' ({len(yes_branches)}):")
            if yes_branches:
                for branch in yes_branches:
                    log_debug(f"     → {branch}")
            else:
                log_debug(f"     ❌ BRAK gałęzi 'tak' - TO JEST PROBLEM!")
            
            # ✅ KROK 3D: WYŚWIETL GAŁĘZIE "NIE"
            log_debug(f"   🔴 Gałęzie 'NIE' ({len(no_branches)}):")
            if no_branches:
                for branch in no_branches:
                    log_debug(f"     → {branch}")
            else:
                log_debug(f"     ⚠️ Brak gałęzi 'nie'")
            
            # ✅ KROK 3E: WYŚWIETL GAŁĘZIE BEZ ETYKIET
            if unlabeled_branches:
                log_debug(f"   ❓ Gałęzie BEZ ETYKIET ({len(unlabeled_branches)}):")
                for branch in unlabeled_branches:
                    log_debug(f"     → {branch}")
            
            # ✅ KROK 3F: SPRAWDŹ POPRAWNOŚĆ LOGICZNĄ
            total_branches = len(yes_branches) + len(no_branches) + len(unlabeled_branches)
            
            if total_branches == 0:
                log_debug(f"     ❌ BŁĄD: Decyzja nie ma ŻADNYCH gałęzi!")
            elif len(yes_branches) == 0:
                log_debug(f"     ⚠️ PROBLEM: Decyzja nie ma gałęzi 'tak'")
            elif len(no_branches) == 0:
                log_debug(f"     ⚠️ UWAGA: Decyzja nie ma gałęzi 'nie'")
            else:
                log_debug(f"     ✅ OK: Decyzja ma obie gałęzie ({len(yes_branches)} tak, {len(no_branches)} nie)")
        
        # ✅ KROK 4: PODSUMOWANIE STATYSTYK
        total_decisions = len(decision_groups)
        unique_decisions_count = len(unique_decisions)
        duplicate_groups = len(duplicates)
        
        # Sprawdź węzły końcowe
        final_nodes = [node_id for node_id, node in self.id_map.items() 
                    if node.attrib.get('xmi:type') == 'uml:ActivityFinalNode']
        
        # Sprawdź czy liczba końców odpowiada liczbie w parsed_data
        expected_endings = 0
        if hasattr(self, 'parsed_data') and 'flow' in self.parsed_data:
            expected_endings = len([item for item in self.parsed_data['flow'] 
                                if item.get('type') == 'control' and 
                                item.get('action') in ['end', 'stop']])
        
        log_debug(f"\n📊 PODSUMOWANIE ANALIZY DECYZJI:")
        log_debug(f"   🔹 Wszystkich grup decyzji: {total_decisions}")
        log_debug(f"   ✅ Unikalnych decyzji: {unique_decisions_count}")
        log_debug(f"   ⚠️ Grup z duplikatami: {duplicate_groups}")
        log_debug(f"   🏁 Węzły końcowe: {len(final_nodes)} (oczekiwano: {expected_endings})")
        
        # ✅ KROK 5: REKOMENDACJE
        if duplicates:
            log_debug(f"\n💡 REKOMENDACJE:")
            log_debug(f"   • Usuń duplikaty decyzji - każda unikalna decyzja powinna mieć tylko jeden węzeł")
            log_debug(f"   • Sprawdź parser PlantUML - może tworzyć niepotrzebne duplikaty")
        
        if len(final_nodes) != expected_endings:
            log_debug(f"   • Sprawdź mapowanie end/stop - może być błąd w tworzeniu węzłów końcowych")

    def _process_flow(self, main_activity: ET.Element, flow: list):
        """Obsługa alternatywnych zakończeń bez łączenia ich między sobą"""
        previous_node_id = None
        previous_parser_id = None
        previous_swimlane = None
        structure_stack = []
        
        next_transition_label = ""
        
        if not hasattr(self, 'parser_id_to_xmi_id'):
            self.parser_id_to_xmi_id = {}

        for i, item in enumerate(flow):
            current_swimlane = item.get('swimlane')
            item_type = item.get('type')
            parser_item_id = item.get('id')
            current_node_id = None
            transition_needed = True
            special_source_id = None
            
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

            if self.debug_options.get('processing', False):
                log_debug(f"Przetwarzanie elementu {i+1}/{len(flow)}: typ={item_type}, ID={parser_item_id}, tekst={item.get('text', '')}")

            # Obsługa elementów przez odpowiednie handlery
            handler = handlers.get(item_type)
            if handler:
                if item_type == 'decision_else':
                    self._processing_decision_else = True
                
                # Znajdź decision_start dla tego decision_else
                decision_id = item.get('decision_id')
                if decision_id:
                    # Znajdź etykietę "nie" w logical_connections
                    for conn in self.parsed_data['logical_connections']:
                        if (conn.get('source_id') == decision_id and 
                            conn.get('target_id') == parser_item_id and
                            conn.get('label') == 'nie'):
                            
                            # Następne przejście będzie miało etykietę "nie"
                            next_transition_label = 'nie'
                            break

                result = handler(item, main_activity, structure_stack, previous_node_id, partition_id)
                current_node_id = result.get('id')
                
                if 'next_label' in result:
                    next_transition_label = result['next_label']
                
                if parser_item_id and current_node_id:
                    # ✅ SPRAWDŹ CZY MAPOWANIE JUŻ ISTNIEJE
                    if parser_item_id in self.parser_id_to_xmi_id:
                        existing_xmi_id = self.parser_id_to_xmi_id[parser_item_id]
                        if existing_xmi_id != current_node_id:
                            if self.debug_options.get('processing', False):
                                log_warning(f"⚠️ DUPLIKAT MAPOWANIA: {parser_item_id} już mapowane na {existing_xmi_id[-6:]}, próba mapowania na {current_node_id[-6:]}")
                            
                            # Użyj istniejącego mapowania
                            current_node_id = existing_xmi_id
                        else:
                            if self.debug_options.get('positioning', False):
                                log_debug(f"   ✅ Mapowanie już istnieje: {parser_item_id} → {current_node_id[-6:]}")
                    else:
                        # ✅ NOWE MAPOWANIE
                        self.parser_id_to_xmi_id[parser_item_id] = current_node_id
                        if self.debug_options.get('positioning', False):
                            log_debug(f"   ✅ Nowe mapowanie ID: {parser_item_id} → {current_node_id[-6:]}")

                
                transition_needed = result.get('transition', True)
                special_source_id = result.get('prev_id')
                
            elif item_type != 'swimlane':
                log_debug(f"ℹ️ Pominięto nieznany element: {item_type}")

            # ✅ KLUCZOWA POPRAWKA: SPRAWDŹ CZY POPRZEDNI WĘZEŁ TO ActivityFinalNode
            if transition_needed and previous_node_id and current_node_id:
                
                # 🚨 SPRAWDŹ CZY ŹRÓDŁO TO ActivityFinalNode
                source_id = special_source_id if special_source_id else previous_node_id
                source_node = self.id_map.get(source_id)
                
                if source_node is not None and source_node.attrib.get('xmi:type') == 'uml:ActivityFinalNode':
                    if self.debug_options.get('transitions', False):
                        log_debug(f"🚫 POMINIĘTO przejście z ActivityFinalNode {source_id[-6:]} → {current_node_id[-6:]}")
                        log_debug(f"   ❌ ActivityFinalNode nie może mieć przejść wychodzących")
                    
                    # NIE TWÓRZ PRZEJŚCIA - po prostu kontynuuj
                else:
                    # NORMALNIE UTWÓRZ PRZEJŚCIE (nie jest to ActivityFinalNode)
                    if self.debug_options.get('transitions', False):
                        log_debug(f"🔗 Próba utworzenia przejścia: {source_id[-6:]} → {current_node_id[-6:]}")
                    
                    # ✅ ZAINICJALIZUJ transition_label NA POCZĄTKU
                    transition_label = ""
                    
                    # ✅ SPRAWDŹ next_transition_label NAJPIERW
                    if next_transition_label:
                        transition_label = next_transition_label
                        next_transition_label = ""  # Reset
                        
                        if self.debug_options.get('transitions'):
                            log_debug(f"   ✅ UŻYTO next_transition_label: '{transition_label}'")
                    
                    # ✅ JEŚLI BRAK ETYKIETY, SZUKAJ W LOGICAL_CONNECTIONS
                    if not transition_label and hasattr(self, 'parsed_data') and 'logical_connections' in self.parsed_data:
                        
                        # Znajdź parser_id dla źródła i celu
                        source_parser_id = None
                        target_parser_id = None
                        
                        for p_id, x_id in self.parser_id_to_xmi_id.items():
                            if x_id == source_id:
                                source_parser_id = p_id
                            if x_id == current_node_id:
                                target_parser_id = p_id
                        
                        if self.debug_options.get('transitions', False):
                            log_debug(f"🔍 Szukam etykiety dla: {source_parser_id[-6:] if source_parser_id else 'None'} → {target_parser_id[-6:] if target_parser_id else 'None'}")
                        
                        if source_parser_id and target_parser_id:
                            
                            # METODA 1: Bezpośrednie wyszukiwanie (dla etykiet "tak")
                            for conn in self.parsed_data['logical_connections']:
                                if (conn.get('source_id') == source_parser_id and 
                                    conn.get('target_id') == target_parser_id):
                                    transition_label = conn.get('label', '')
                                    
                                    if self.debug_options.get('transitions') and transition_label:
                                        log_debug(f"   ✅ BEZPOŚREDNIA etykieta '{transition_label}' znaleziona")
                                    break
                            
                            # METODA 2: Specjalne wyszukiwanie dla etykiet "nie" przez decision_else
                            if not transition_label:
                                # Sprawdź czy źródło to DecisionNode
                                source_node = self.id_map.get(source_id)
                                if source_node is not None and source_node.attrib.get('xmi:type') == 'uml:DecisionNode':
                                    
                                    if self.debug_options.get('transitions'):
                                        log_debug(f"   🔍 Źródło to DecisionNode - szukam etykiety 'nie'")
                                    
                                    # Znajdź wszystkie połączenia "nie" z tej decyzji
                                    for conn in self.parsed_data['logical_connections']:
                                        if (conn.get('source_id') == source_parser_id and 
                                            conn.get('label') == 'nie'):
                                            
                                            decision_else_id = conn.get('target_id')
                                            
                                            if self.debug_options.get('transitions'):
                                                log_debug(f"   🎯 Znaleziono decision_else: {decision_else_id[-6:]}")
                                            
                                            # Sprawdź czy decision_else prowadzi do naszego celu
                                            for conn2 in self.parsed_data['logical_connections']:
                                                if (conn2.get('source_id') == decision_else_id and 
                                                    conn2.get('target_id') == target_parser_id):
                                                    
                                                    transition_label = 'nie'
                                                    
                                                    if self.debug_options.get('transitions'):
                                                        log_debug(f"   ✅ PRZEZ DECISION_ELSE: etykieta 'nie' dla {source_parser_id[-6:]} → {target_parser_id[-6:]}")
                                                    break
                                            
                                            if transition_label:
                                                break
                            
                            # METODA 3: Fallback - sprawdź czy cel ma "negatywną" nazwę
                            if not transition_label:
                                source_node = self.id_map.get(source_id)
                                target_node = self.id_map.get(current_node_id)
                                
                                if (source_node is not None and source_node.attrib.get('xmi:type') == 'uml:DecisionNode' and 
                                    target_node is not None and target_node.attrib.get('name', '')):
                                    
                                    target_name = target_node.attrib.get('name', '').lower()
                                    
                                    # Sprawdź czy nazwa sugeruje gałąź "nie"
                                    negative_keywords = ['nieudana', 'zablokowane', 'błąd', 'error', 'przekazanie', 'ponowne']
                                    
                                    if any(keyword in target_name for keyword in negative_keywords):
                                        transition_label = 'nie'
                                        
                                        if self.debug_options.get('transitions'):
                                            log_debug(f"   ✅ PRZEZ NAZWĘ: etykieta 'nie' dla decyzji → '{target_name}'")
                            
                            # ✅ METODA 4: INTELIGENTNE WYKRYWANIE "NIE" - jeśli decyzja ma "tak", reszta to "nie"
                            if not transition_label:
                                source_node = self.id_map.get(source_id)
                                if source_node is not None and source_node.attrib.get('xmi:type') == 'uml:DecisionNode':
                                    
                                    # Sprawdź czy decyzja ma już gałąź "tak"
                                    has_yes_branch = False
                                    for trans in self.transitions:
                                        if trans['source_id'] == source_id and trans.get('name') == 'tak':
                                            has_yes_branch = True
                                            break
                                    
                                    # Jeśli ma gałąź "tak", to pozostałe gałęzie to prawdopodobnie "nie"
                                    if has_yes_branch:
                                        target_node = self.id_map.get(current_node_id)
                                        if target_node is not None:
                                            target_name = target_node.attrib.get('name', '').lower()
                                            
                                            # Lista słów kluczowych wskazujących na gałąź "nie"
                                            negative_indicators = [
                                                'nieudana', 'nieudany', 'zablokowane', 'zablokowany',
                                                'błąd', 'error', 'przekazanie', 'ponowne', 'ponowny',
                                                'klient zrezygnował', 'proces nieudany', 'rezygnacja'
                                            ]
                                            
                                            is_negative_flow = any(keyword in target_name for keyword in negative_indicators)
                                            
                                            # Sprawdź w danych parsera czy to był "decision_else"
                                            is_decision_else = False
                                            if hasattr(self, 'parsed_data') and 'flow' in self.parsed_data:
                                                for flow_item in self.parsed_data['flow']:
                                                    if (flow_item.get('id') == target_parser_id and 
                                                        flow_item.get('type') == 'decision_else'):
                                                        is_decision_else = True
                                                        break
                                            
                                            # Jeśli to negatywny przepływ lub decision_else, przypisz "nie"
                                            if is_negative_flow or is_decision_else:
                                                transition_label = 'nie'
                                                
                                                if self.debug_options.get('transitions'):
                                                    reason = "decision_else" if is_decision_else else "negatywne słowa kluczowe"
                                                    log_debug(f"   ✅ INTELIGENTNE WYKRYWANIE: etykieta 'nie' przez {reason}")

                    # ✅ FINALNE LOGOWANIE I DODANIE PRZEJŚCIA
                    if self.debug_options.get('transitions'):
                        if transition_label:
                            log_debug(f"🏷️ FINALNA etykieta: '{transition_label}' dla {source_id[-6:]} → {current_node_id[-6:]}")
                        else:
                            log_debug(f"🏷️ BRAK etykiety dla {source_id[-6:]} → {current_node_id[-6:]}")

                    # ✅ DODAJ PRZEJŚCIE Z ETYKIETĄ
                    self._add_transition(main_activity, source_id, current_node_id, name=transition_label)
            
            # ✅ AKTUALIZUJ POPRZEDNI WĘZEŁ
            if current_node_id:
                previous_node_id = current_node_id
                previous_parser_id = parser_item_id
                
            if current_swimlane:
                previous_swimlane = current_swimlane
        
        # Po przetworzeniu wszystkich elementów
        self._connect_hanging_elements(main_activity)
        self._update_partition_elements(main_activity)
        self._debug_transitions_graph()
        self._analyze_decision_positioning()

    def _connect_hanging_elements(self, parent_activity):
        """Metoda łączenia wiszących elementów"""
        
        # Znajdź wszystkie Final nodes
        final_nodes = []
        for node_id, node in self.id_map.items():
            if node.attrib.get('xmi:type') == 'uml:ActivityFinalNode':
                final_nodes.append(node_id)
        
        if not final_nodes:
            return
        
        # Użyj pierwszego Final node jako główny
        main_final = final_nodes[0]
        
        # Znajdź węzły bez przejść wychodzących (oprócz Final nodes)
        hanging_elements = []
        
        for node_id, node in self.id_map.items():
            node_type = node.attrib.get('xmi:type', '')
            if node_type in ["uml:ActivityPartition", "uml:Comment", "uml:ActivityFinalNode"]:
                continue
            
            has_outgoing = any(t['source_id'] == node_id for t in self.transitions)
            if not has_outgoing:
                hanging_elements.append(node_id)
        
        # Połącz z głównym Final node
        connected = 0
        for element_id in hanging_elements:
            if self._add_transition(parent_activity, element_id, main_final):
                connected += 1
                if self.debug_options.get('transitions', False):
                    log_debug(f"Połączono element bez wyjścia {element_id[-6:]} z Final {main_final[-6:]}")
        
        if self.debug_options.get('transitions', False) and connected > 0:
            log_debug(f"Połączono {connected} wiszących elementów")
                
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
                log_debug(f"⚠️ Znaleziono atrybut None: {current_path} -> {key}")
        
        for child in element:
            self._debug_find_none_values(child, current_path)

    def _handle_decision_end(self, item, parent, stack, prev_id, partition):
        """POPRAWIONA: Obsługa decision_end - tworzy MergeNode zamiast mapowania na prev_id"""
        
        if self.debug_options.get('processing', False):
            log_debug(f"🔚 Przetwarzanie decision_end dla elementu: {item.get('id')}")
        
        if not stack:
            if self.debug_options.get('processing', False):
                log_warning("⚠️ Brak elementów na stosie dla decision_end")
            return {'id': prev_id, 'transition': True}
        
        # Znajdź decyzję na stosie
        decision_info = None
        decision_index = -1
        
        for i in range(len(stack) - 1, -1, -1):
            if stack[i].get('type') == 'decision':
                decision_info = stack[i]
                decision_index = i
                break
        
        if not decision_info:
            if self.debug_options.get('processing', False):
                log_warning("⚠️ Nie znaleziono decyzji na stosie dla decision_end")
            return {'id': prev_id, 'transition': True}
        
        # ✅ UTWÓRZ MERGE NODE dla decision_end (nie mapuj na istniejący element!)
        merge_node_id = self._add_node(parent, 'uml:MergeNode', 'Merge', partition)
        
        self.diagram_objects.append({
            'id': merge_node_id,
            'type': 'MergeNode',
            'decision_id': decision_info['id']
        })
        
        if self.debug_options.get('processing', False):
            log_debug(f"    ✅ Utworzono MergeNode: {merge_node_id[-6:]} dla decyzji {decision_info['id'][-6:]}")
        
        # Usuń decyzję ze stosu
        stack.pop(decision_index)
        
        # ✅ POŁĄCZ prev_id z merge node (jeśli istnieje)
        if prev_id:
            self._add_transition(parent, prev_id, merge_node_id)
            if self.debug_options.get('processing', False):
                log_debug(f"    🔗 Połączono {prev_id[-6:]} → {merge_node_id[-6:]}")
        
        return {'id': merge_node_id, 'transition': True}

    def _debug_transitions_graph(self):
        """Generuje czytelną reprezentację grafu przejść dla celów analizy i debugowania."""
        if not self.debug_options.get('transitions', False):
            return
            
        log_debug("\n=== GRAF PRZEJŚĆ ===")
        
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
            log_debug(message)
            
            # Wyświetl przejścia wchodzące
            if node_data['incoming']:
                log_debug("  Przejścia wchodzące:")
                for source_id, label in node_data['incoming']:
                    source_short_id = source_id[-6:] if source_id and len(source_id) >= 6 else source_id
                    source_type = nodes[source_id]['type'] if source_id in nodes else '?'
                    label_str = f" [{label}]" if label else ""
                    in_message = f"    - z {source_short_id} [{source_type}]{label_str}"
                    log_debug(in_message)
            else:
                log_debug("  Brak przejść wchodzących (węzeł początkowy?)")
            
            # Wyświetl przejścia wychodzące
            if node_data['outgoing']:
                log_debug("  Przejścia wychodzące:")
                for target_id, label in node_data['outgoing']:
                    target_short_id = target_id[-6:] if target_id and len(target_id) >= 6 else target_id
                    target_type = nodes[target_id]['type'] if target_id in nodes else '?'
                    label_str = f" [{label}]" if label else ""
                    out_message = f"    - do {target_short_id} [{target_type}]{label_str}"
                    log_debug(out_message)
            else:
                log_debug("  Brak przejść wychodzących (węzeł końcowy?)")
            log_debug("")
        
        # Wyświetl zidentyfikowane problemy
        if self_connections:
            log_debug("\n=== WYKRYTE POŁĄCZENIA DO SIEBIE SAMEGO ===")
            for conn in self_connections:
                node_id = conn['node_id']
                node_type = nodes[node_id]['type'] if node_id in nodes else '?'
                node_name = nodes[node_id]['name'] if node_id in nodes else 'unnamed'
                message = f"  * Węzeł {node_id[-6:]} [{node_type}] '{node_name}' ma połączenie do siebie samego"
                log_debug(message)
                
        # Wyświetl informacje o węzłach decyzyjnych
        if decision_branches:
            log_debug("\n=== WĘZŁY DECYZYJNE ===")
            for decision_id, branches in decision_branches.items():
                decision_name = nodes[decision_id]['name'] if decision_id in nodes else 'unnamed'
                
                yes_id = branches.get('tak')
                yes_name = nodes[yes_id]['name'] if yes_id and yes_id in nodes else 'none'
                
                no_id = branches.get('nie') 
                no_name = nodes[no_id]['name'] if no_id and no_id in nodes else 'none'
                
                message = f"  * Decyzja: {decision_id[-6:]} '{decision_name}'"
                log_debug(message)
                
                message = f"    - Gałąź 'tak': {yes_id[-6:] if yes_id else 'brak'} '{yes_name}'"
                
                log_debug(message)
                
                message = f"    - Gałąź 'nie': {no_id[-6:] if no_id else 'brak'} '{no_name}'"
                
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
            
            log_debug("\n=== PROBLEMATYCZNE ELEMENTY ===")
            for node in problematic_nodes:
                
                log_debug(f"  * {node['info']}")
        

    def _handle_control(self, item, parent, stack, prev_id, partition):
        """Obsługa węzłów kontrolnych z wieloma zakończeniami."""
        action = item['action']
        
        if action == 'start':
            node_id = self._add_node(parent, 'uml:InitialNode', 'Initial', partition)
            self.diagram_objects.append({
                'id': node_id,
                'type': 'InitialNode'
            })
            
            if self.debug_options.get('processing', False):
                log_debug(f"✅ Utworzono węzeł początkowy: {node_id[-6:]}")
            
            return {'id': node_id, 'transition': True}
        
        elif action in ['end', 'stop']:
            # Każde zakończenie to osobny węzeł
            activity_text = item.get('text', f'{action.capitalize()} Node')
            
            # Utwórz unikalny węzeł końcowy dla każdego zakończenia
            node_id = self._add_node(parent, 'uml:ActivityFinalNode', activity_text, partition)
            
            self.diagram_objects.append({
                'id': node_id,
                'type': 'ActivityFinalNode',
                'action': action,
                'context': activity_text
            })
            
            if self.debug_options.get('processing', False):
                log_debug(f"✅ Utworzono węzeł końcowy: {node_id[-6:]} ({action})")
            
            return {'id': node_id, 'transition': True}
        
        return {'id': None, 'transition': False}

    def _debug_diagram_objects(self):
        """Wyświetla informacje o elementach dodanych do diagramu."""
        if not self.debug_options.get('elements', False):
            return
            
        
        log_debug(f"\n--- Elementy diagramu ({len(self.diagram_objects)}) ---")
        for obj in self.diagram_objects:
            if isinstance(obj, dict):
                obj_id = obj.get('id', 'brak ID')
                obj_type = obj.get('type', 'nieznany typ')
                
                log_debug(f" - {obj_type}: {obj_id[-6:]}")
            else:
            
                log_debug(f" - {obj}")

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
                    
                    log_debug(f"Znaleziono cel dla brakującej gałęzi: {node_id[-6:]} [{node_type}]")
                return node_id
        
        # Strategia 2: Szukaj węzła końcowego w tym samym torze
        for node_id, node in self.id_map.items():
            node_type = node.attrib.get('xmi:type', '')
            node_partition = node.attrib.get('inPartition')
            
            if node_partition == partition_id and 'ActivityFinalNode' in node_type:
                if self.debug_options.get('processing', False):
                    
                    log_debug(f"Znaleziono węzeł końcowy dla brakującej gałęzi: {node_id[-6:]}")
                return node_id
        
        # Strategia 3: Szukaj dowolnego węzła końcowego
        for node_id, node in self.id_map.items():
            if 'ActivityFinalNode' in node.attrib.get('xmi:type', ''):
                if self.debug_options.get('processing', False):
                    
                    log_debug(f"Znaleziono dowolny węzeł końcowy dla brakującej gałęzi: {node_id[-6:]}")
                return node_id
        
        # Jeśli nie znaleziono odpowiedniego celu, zwróć None
        # W takim przypadku _ensure_complete_decision_branches utworzy nowy węzeł końcowy
        if self.debug_options.get('processing', False):
            
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
        """Obsługa decyzji z eliminacją duplikatów."""
        condition = item.get('condition', 'Decision')
        decision_id = item.get('id')
        then_label = item.get('then_label', 'tak')
        
        # ✅ SPRAWDŹ CZY DECYZJA O TAKIEJ NAZWIE JUŻ ISTNIEJE
        existing_decision_id = None
        for existing_item in self.diagram_objects:
            if (existing_item.get('type') == 'DecisionNode' and 
                existing_item.get('name') == condition):
                existing_decision_id = existing_item.get('id')
                break
        
        if existing_decision_id:
            # ✅ UŻYJ ISTNIEJĄCEJ DECYZJI
            if self.debug_options.get('processing', False):
                log_debug(f"🔄 Używam istniejącej decyzji: {existing_decision_id[-6:]} '{condition}'")
            
            # Dodaj nową gałąź do istniejącej decyzji
            stack.append({
                'type': 'decision',
                'id': existing_decision_id,
                'condition': condition,
                'branch_ends': [],
                'then_label': then_label
            })
            
            return {'id': existing_decision_id, 'transition': False}
        else:
            # ✅ UTWÓRZ NOWĄ DECYZJĘ
            node_id = self._add_node(parent, 'uml:DecisionNode', condition, partition)
            
            self.diagram_objects.append({
                'id': node_id,
                'type': 'DecisionNode',
                'name': condition
            })
            
            # Dodaj do stosu
            stack.append({
                'type': 'decision',
                'id': node_id,
                'condition': condition,
                'branch_ends': [],
                'then_label': then_label
            })
            
            if self.debug_options.get('processing', False):
                log_debug(f"✅ Utworzono nową decyzję: {node_id[-6:]} '{condition}'")
            
            return {'id': node_id, 'transition': True}

    def _handle_decision_else(self, item, parent, stack, prev_id, partition):
        """POPRAWIONA: decision_else NIE mapuje się na istniejące DecisionNode"""
        
        decision_id = item.get('decision_id')  
        
        if self.debug_options.get('processing', False):
            log_debug(f"🔀 Przetwarzanie decision_else dla decyzji: {decision_id}")
        
        # ✅ KLUCZOWA ZMIANA: decision_else to "wirtualny" element
        # NIE tworzymy fizycznego węzła, tylko oznaczamy że następne przejście będzie "nie"
        
        self._processing_decision_else = True
        next_transition_label = "nie"
        
        # ✅ ZWRÓĆ SPECJALNY WYNIK - nie mapuj na istniejące ID
        return {
            'id': None,  # Brak fizycznego węzła
            'transition': False,  # Nie twórz przejścia z decision_else
            'next_label': next_transition_label,
            'virtual': True  # Oznacz jako wirtualny element
        }

    def _handle_fork_start(self, item, parent, stack, prev_id, partition):
        """Obsługuje początek bloku fork."""
        node_id = self._add_node(parent, 'uml:ForkNode', 'Fork', partition)
        
        # Dodaj do listy obiektów diagramu
        self.diagram_objects.append({
            'id': node_id,
            'type': 'ForkNode',
            'parser_id': item.get('id')
        })
        
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

    def _add_node(self, parent, node_type, name, partition_id=None, force_unique=True):
        """Wykrywa i zapobiega duplikatom węzłów o tej samej nazwie"""
        
        # ✅ SPRAWDŹ CZY WĘZEŁ O TEJ NAZWIE JUŻ ISTNIEJE
        if force_unique and hasattr(self, 'created_nodes'):
            for existing_id, node_info in self.created_nodes.items():
                if (node_info.get('name') == name and 
                    node_info.get('type') == node_type and
                    node_info.get('partition') == partition_id):
                    
                    if self.debug_options.get('processing', False):
                        log_debug(f"🔁 UŻYTO ISTNIEJĄCY węzeł: {name} → {existing_id[-6:]}")
                    
                    return existing_id
        
        # ✅ UTWÓRZ NOWY WĘZEŁ
        node_id = self._generate_ea_id()
        node = ET.SubElement(parent, 'node', attrib={
            'xmi:type': node_type,
            'xmi:id': f'EAID_{node_id}',
            'visibility': 'public',
            'name': name
        })
        
        if partition_id:
            node.set('inPartition', partition_id)
        
        # ✅ ZAPISZ INFORMACJE O WĘŹLE
        if not hasattr(self, 'created_nodes'):
            self.created_nodes = {}
        
        full_id = f'EAID_{node_id}'
        self.created_nodes[full_id] = {
            'name': name,
            'type': node_type, 
            'partition': partition_id,
            'element': node
        }
        
        self.id_map[full_id] = node
        self.diagram_objects.append({'id': full_id, 'type': node_type.split(':')[-1]})
        
        return full_id
    
    def _add_transition(self, parent_activity, source_id, target_id, name=""):
        """Metoda dodawania przejść z walidacją UML"""
        
        if self.debug_options.get('transitions', False):
            log_debug(f"🔗 Próba utworzenia przejścia: {source_id[-6:]} → {target_id[-6:]}")
        
        # 1. WALIDACJA: Sprawdź czy węzły istnieją
        if source_id not in self.id_map or target_id not in self.id_map:
            if self.debug_options.get('transitions', False):
                log_error(f"BŁĄD: Węzły nie istnieją - source: {source_id in self.id_map}, target: {target_id in self.id_map}")
            return False
        
        # 2. WALIDACJA: ActivityFinalNode nie może mieć przejść wychodzących
        source_node = self.id_map[source_id]
        if source_node.attrib.get('xmi:type') == 'uml:ActivityFinalNode':
            if self.debug_options.get('transitions', False):
                log_error(f"BŁĄD UML: ActivityFinalNode {source_id[-6:]} nie może mieć przejść wychodzących do {target_id[-6:]}")
            return False
        
        # 3. WALIDACJA: Unikaj samo-połączeń
        if source_id == target_id:
            if self.debug_options.get('transitions', False):
                log_warning(f"UWAGA: Samo-połączenie węzła {source_id[-6:]}")
            return False
        
        # 4. WALIDACJA: Unikaj duplikatów
        for existing in self.transitions:
            if (existing['source_id'] == source_id and 
                existing['target_id'] == target_id and 
                existing['name'] == name):
                if self.debug_options.get('transitions', False):
                    log_warning(f"DUPLIKAT: Przejście już istnieje")
                return False
        
        # 5. UTWORZ przejście
        transition_id = self._generate_ea_id("EAID")
        
        # Utwórz element przejścia w XML
        edge = ET.SubElement(parent_activity, 'edge', self._sanitize_xml_attrs({
            'xmi:type': 'uml:ControlFlow',
            'xmi:id': transition_id,
            'visibility': 'public',
            'source': source_id,
            'target': target_id
        }))
        
        # Dodaj etykietę jeśli istnieje (guard condition)
        if name:
            edge.set('name', name)
            
            # Dodaj guard element dla warunków decyzji
            guard = ET.SubElement(edge, 'guard', {
                'xmi:type': 'uml:LiteralString',
                'value': name
            })
        
        # 6. ZAPISZ w liście przejść
        transition = {
            'id': transition_id,
            'source_id': source_id,
            'target_id': target_id,
            'name': name,
            'cross_swimlane': self._is_cross_swimlane_transition(source_id, target_id)
        }
        self.transitions.append(transition)
        
        if self.debug_options.get('transitions', False):
            final_label = f" [{name}]" if name else ""
            log_debug(f"✅ Utworzono poprawne przejście: {source_id[-6:]} → {target_id[-6:]}{final_label}")
        
        return True

    def _is_cross_swimlane_transition(self, source_id, target_id):
        """Sprawdza czy przejście przekracza granice torów."""
        if source_id not in self.id_map or target_id not in self.id_map:
            return False
            
        source_partition = self.id_map[source_id].attrib.get('inPartition')
        target_partition = self.id_map[target_id].attrib.get('inPartition')
        
        return source_partition != target_partition and source_partition and target_partition
    
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
            log_debug(f"🏊 Utworzono tor (partition): {name}")

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
            if not self.debug_options.get('positioning', False):
                return
                
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
                
                log_debug(f"\n🔹 DECYZJA: {decision_name} (XMI: {decision_xmi_id[-6:]}, Parser: {decision_parser_id})")
                
                
                # Pozycja decyzji
                if hasattr(self, 'layout_manager') and hasattr(self.layout_manager, 'element_positions'):
                    if decision_parser_id in self.layout_manager.element_positions:
                        dec_pos = self.layout_manager.element_positions[decision_parser_id]
                        
                        log_debug(f"   Decyzja: poziom={dec_pos['row']}, kolumna={dec_pos['column']}, X={dec_pos['x']}, Y={dec_pos['y']}")
                        
                        # Sprawdź gałęzie TAK
                        log_debug(f"   Gałęzie TAK ({len(decision_info['yes_branches'])}):")
                        for branch in decision_info['yes_branches']:
                            if branch['parser_id'] in self.layout_manager.element_positions:
                                br_pos = self.layout_manager.element_positions[branch['parser_id']]
                                relative_x = "LEWO" if br_pos['x'] < dec_pos['x'] else "PRAWO" if br_pos['x'] > dec_pos['x'] else "ŚRODEK"
                                relative_y = "WYŻEJ" if br_pos['y'] < dec_pos['y'] else "NIŻEJ" if br_pos['y'] > dec_pos['y'] else "TEN SAM"
                                
                                log_debug(f"     - {branch['parser_id']}: poziom={br_pos['row']}, kolumna={br_pos['column']}, X={br_pos['x']} ({relative_x}), Y={br_pos['y']} ({relative_y})")
                                
                        
                        # Sprawdź gałęzie NIE
                        log_debug(f"   Gałęzie NIE ({len(decision_info['no_branches'])}):")
                        for branch in decision_info['no_branches']:
                            if branch['parser_id'] in self.layout_manager.element_positions:
                                br_pos = self.layout_manager.element_positions[branch['parser_id']]
                                relative_x = "LEWO" if br_pos['x'] < dec_pos['x'] else "PRAWO" if br_pos['x'] > dec_pos['x'] else "ŚRODEK"
                                relative_y = "WYŻEJ" if br_pos['y'] < dec_pos['y'] else "NIŻEJ" if br_pos['y'] > dec_pos['y'] else "TEN SAM"
                                
                                log_debug(f"     - {branch['parser_id']}: poziom={br_pos['row']}, kolumna={br_pos['column']}, X={br_pos['x']} ({relative_x}), Y={br_pos['y']} ({relative_y})")
                                

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
            
            log_debug(f"\n📍 DODAWANIE ELEMENTÓW DO XMI:")
        
        # KROK 1: Najpierw dodaj tory (swimlanes)
        for i, (name, partition_id) in enumerate(self.swimlane_ids.items()):
            if hasattr(self, 'layout_manager') and hasattr(self.layout_manager, 'swimlanes_geometry'):
                lane_geom = self.layout_manager.swimlanes_geometry.get(partition_id, {})
                left = lane_geom.get('x', 100 + i * 400)
                width = lane_geom.get('width', 350)
                height = lane_geom.get('height', 1450)
                top = lane_geom.get('y', 50)
            else:
                # Fallback pozycje
                left = 100 + i * 400
                width = 350
                height = 1450
                top = 50
            
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
                
                log_debug(f"   🏊 Tor {name}: Left={left}, Top={top}, Right={right}, Bottom={bottom}")
        
        # KROK 2: Dodaj WSZYSTKIE elementy z diagram_objects z pozycjami
        elements = ET.SubElement(diagram, 'elements')
        seq_no = 0
        
        if self.debug_options.get('positioning', False):
            log_debug(f"\n📍 === ANALIZA POZYCJI WSZYSTKICH ELEMENTÓW ===")

        for obj in self.diagram_objects:
            if isinstance(obj, dict):
                node_id = obj.get('id')
                obj_type = obj.get('type', 'unknown')
                
                if node_id and node_id in self.id_map:
                    node = self.id_map[node_id]
                    node_name = node.attrib.get('name', '')
                    
                    # Pobierz geometrię
                    position = self._get_element_geometry(node_id, obj_type)
                    
                    if self.debug_options.get('positioning', False):
                        log_debug(f"🔍 Element: {obj_type} '{node_name[:30]}' ID={node_id[-6:]}")
                        log_debug(f"    Pozycja: {position}")
                    
                    # WALIDUJ POZYCJĘ
                    if position and position != "Left=0;Top=0;Right=0;Bottom=0;":
                        if self._validate_geometry(position, node_id):
                            # Dodaj element
                            style = self._get_element_style_from_type(obj_type, node)
                            
                            ET.SubElement(elements, 'element', self._sanitize_xml_attrs({
                                'subject': node_id,
                                'seqno': str(seq_no),
                                'geometry': position,
                                'style': style
                            }))
                            seq_no += 1
                            
                            if self.debug_options.get('positioning', False):
                                log_debug(f"    ✅ DODANO do XMI")
                        else:
                            if self.debug_options.get('positioning', False):
                                log_debug(f"    ❌ POZYCJA NIEPRAWIDŁOWA - pomijam")
                    else:
                        if self.debug_options.get('positioning', False):
                            log_debug(f"    ❌ BRAK POZYCJI - pomijam")
        
        if self.debug_options.get('positioning', False):
            log_debug(f"✅ UTWORZONO DIAGRAM z {seq_no} elementami")
        
        # KROK 3: Dodaj pozostałe elementy z id_map
        added_ids = {obj.get('id') for obj in self.diagram_objects if isinstance(obj, dict) and obj.get('id')}
        added_ids.update(self.swimlane_ids.values())
        
        for node_id, node in self.id_map.items():
            if node_id not in added_ids:
                # POPRAWKA: Użyj _get_element_geometry
                node_type = node.attrib.get('xmi:type', '').replace('uml:', '')
                position = self._get_element_geometry(node_id, node_type)
                
                if position and position != "Left=0;Top=0;Right=0;Bottom=0;":
                    style = self._get_style_for_element(node)
                    
                    ET.SubElement(elements, 'element', self._sanitize_xml_attrs({
                        'subject': node_id,
                        'seqno': str(seq_no),
                        'geometry': position,
                        'style': style
                    }))
                    seq_no += 1                    
                    if self.debug_options.get('positioning', False):
                        
                        log_debug(f"   📎 Dodano dodatkowy element {node_id[-6:]}: {position}")
        
        # KROK 4: Dodaj linki diagramu
        self._add_diagram_links(diagram)
        
        if self.debug_options.get('positioning', False):
            
            log_debug(f"✅ Zakończono dodawanie elementów: {seq_no} elementów w XMI")
        
        return diagram

    def _get_element_dimensions_from_type(self, obj_type):
        """Zwraca wymiary elementu na podstawie jego typu."""
        dimensions = {
            'InitialNode': (25, 25),        # ← POŁOWA z 50×50
            'ActivityFinalNode': (25, 25),  # ← POŁOWA z 50×50
            'DecisionNode': (40, 40),       # ← POŁOWA z 80×80
            'MergeNode': (40, 40),          # ← POŁOWA z 80×80
            'ForkNode': (100, 10),          # ← POŁOWA z 200×20
            'JoinNode': (100, 10),          # ← POŁOWA z 200×20
            'UML_ActivityNode': (100, 40),  # ← POŁOWA z 200×80
            'Comment': (80, 40),            # ← POŁOWA z 160×80
            'ActivityPartition': (125, 500) # ← POŁOWA z 250×1000
        }
        return dimensions.get(obj_type, (100, 40))  # ← POŁOWA z 200×80

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

    def _create_layout_manager(self):
        """Tworzy najlepszy dostępny Layout Manager"""
        
        OLD_LAYOUT_AVAILABLE = False

        if self.debug_options.get('positioning', False):
            log_debug("🔧 Wybór Layout Managera...")
            log_debug(f"🔍 use_ai_positioning = {getattr(self, 'use_ai_positioning', 'NIE USTAWIONE')}")

        log_info(f"🧠 AI POSITIONING: {getattr(self, 'use_ai_positioning', False)}")

            # PRIORYTET 0: ImprovedLayoutManager (jeśli dostępny)
        try:
            from utils.xmi.improved_layout_manager import ImprovedLayoutManager
            layout_manager = ImprovedLayoutManager(
                debug=self.debug_options.get('positioning', False)
            )
            log_info("✅ Użyto ImprovedLayoutManager - nowe 6-krokowe podejście")
            return layout_manager
        except ImportError:
            log_warning("⚠️ ImprovedLayoutManager niedostępny - próbuję alternatywy")
        except Exception as e:
            log_error(f"❌ Błąd ImprovedLayoutManager: {e}")


        # ✅ NOWY PRIORYTET 1: AI Layout Manager (jeśli włączony)
        if getattr(self, 'use_ai_positioning', False):
            try:
                #from utils.xmi.ai_layout_manager import AILayoutManager
                
                # ✅ PRZEKAŻ OPCJĘ DEBUG KOMUNIKACJI I REAL AI
                debug_ai_comm = (self.debug_options.get('ai_communication', False) or 
                            self.debug_options.get('positioning', False))
                
                layout_manager = AILayoutManager(
                    debug=self.debug_options.get('positioning', False),
                    debug_ai_communication=debug_ai_comm,
                    use_real_ai=getattr(self, 'use_real_ai', False)  # ← DODAJ TĘ LINIĘ
                )
                
                log_info("✅ SUKCES: Użyto AI Layout Manager!")
                
                if getattr(self, 'use_real_ai', False):
                    log_info("🤖 REAL AI MODE: Używa prawdziwego modelu AI")
                else:
                    log_info("🧠 DETERMINISTIC AI MODE: Używa reguł deterministycznych")
                
                if debug_ai_comm:
                    log_info("🤖 AI komunikacja: logowanie włączone")
                
                self._add_compatibility_methods(layout_manager)
                return layout_manager
                
            except ImportError as e:
                log_error(f"❌ AI Layout Manager - ImportError: {e}")
            except Exception as e:
                log_error(f"❌ AI Layout Manager - Exception: {e}")
        else:
            log_warning("⚠️ AI positioning WYŁĄCZONY lub nie ustawiony")
        
        # PRIORYTET 2: Nowy GraphLayoutManager (jeśli dostępny)
        if GRAPH_LAYOUT_AVAILABLE:
            try:
                layout_manager = GraphLayoutManager(debug=self.debug_options.get('positioning', False))
                
                if self.debug_options.get('positioning', False):
                    log_debug("✅ Użyto GraphLayoutManager (NetworkX)")
                
                # Dodaj metody kompatybilności
                self._add_compatibility_methods(layout_manager)
                return layout_manager
                
            except Exception as e:
                if self.debug_options.get('positioning', False):
                    log_debug(f"❌ Błąd GraphLayoutManager: {e}")
        
        # PRIORYTET 3: Stary LayoutManager (jeśli dostępny)
        if OLD_LAYOUT_AVAILABLE:
            try:
                layout_manager = LayoutManager(debug=self.debug_options.get('positioning', False))
                
                if self.debug_options.get('positioning', False):
                    log_debug("✅ Użyto starego LayoutManager")
                
                # Dodaj metody kompatybilności
                self._add_compatibility_methods(layout_manager)
                return layout_manager
                
            except Exception as e:
                if self.debug_options.get('positioning', False):
                    log_debug(f"❌ Błąd starego LayoutManager: {e}")
        
        # PRIORYTET 4: Awaryjny Layout Manager
        if self.debug_options.get('positioning', False):
            log_debug("⚠️ Tworzę awaryjny Layout Manager")
        
        return self._create_emergency_layout_manager()

    def _add_compatibility_methods(self, layout_manager):
        """Dodaje brakujące metody dla kompatybilności"""
        
        if not hasattr(layout_manager, 'update_swimlane_geometry'):
            def update_swimlane_geometry():
                if self.debug_options.get('positioning', False):
                    log_debug("🏊 update_swimlane_geometry - placeholder")
                
                # Ustaw geometrie torów
                if not hasattr(layout_manager, 'swimlanes_geometry'):
                    layout_manager.swimlanes_geometry = {}
                
                for i, (name, partition_id) in enumerate(self.swimlane_ids.items()):
                    layout_manager.swimlanes_geometry[partition_id] = {
                        'x': 100 + i * 280,
                        'y': 50, 
                        'width': 250,
                        'height': 1000
                    }
            
            layout_manager.update_swimlane_geometry = update_swimlane_geometry
        
        if not hasattr(layout_manager, 'swimlanes_geometry'):
            layout_manager.swimlanes_geometry = {}
        
        if not hasattr(layout_manager, 'element_positions'):
            layout_manager.element_positions = {}

    def _create_emergency_layout_manager(self):
        """Tworzy awaryjny layout manager jako ostateczna deska ratunku"""
        
        class EmergencyLayoutManager:
            def __init__(self, debug=False):
                self.debug = debug
                self.element_positions = {}
                self.swimlanes_geometry = {}
                
            def analyze_diagram_structure(self, parsed_data):
                """Awaryjny layout - inteligentny 3-kolumnowy układ"""
                
                if self.debug:
                    log_debug(f"🚨 AWARYJNY LAYOUT dla {len(parsed_data.get('flow', []))} elementów")
                
                positions = {}
                
                # Pozycje kolumn
                left_x, center_x, right_x = 200, 675, 1200
                
                for i, element in enumerate(parsed_data.get('flow', [])):
                    element_id = element.get('id')
                    element_type = element.get('type', 'activity')
                    element_name = element.get('text', '').lower()
                    
                    if element_id:
                        # Inteligentne przypisanie kolumn
                        if 'błąd' in element_name or 'negatywn' in element_name:
                            if 'składni' in element_name or 'wizualn' in element_name:
                                col_x = left_x    # Błędy składni/wizualne → lewa
                            else:
                                col_x = right_x   # Błędy generowania → prawa
                        elif element_type in ['control'] and 'start' in element.get('action', ''):
                            col_x = center_x      # START → środek
                        elif element_type in ['control'] and element.get('action') in ['end', 'stop']:
                            col_x = center_x      # END → środek  
                        elif element_type == 'decision_start':
                            col_x = center_x      # Decyzje → środek
                        else:
                            col_x = center_x      # Główna ścieżka → środek
                        
                        # Oblicz wysokość
                        y = 100 + i * 120
                        
                        positions[element_id] = {
                            'x': col_x,
                            'y': y,
                            'width': 50 if element_type == 'control' else 140,
                            'height': 50 if element_type == 'control' else 60,
                            'row': i,
                            'column': 0 if col_x == left_x else 1 if col_x == center_x else 2
                        }
                
                grid = {'columns': 3, 'rows': len(positions)}
                
                if self.debug:
                    log_debug(f"✅ Awaryjny layout: {len(positions)} pozycji w 3 kolumnach")
                
                return positions, grid
                
            def update_swimlane_geometry(self):
                """Ustaw geometrie torów"""
                partition_ids = getattr(self, '_partition_ids', {})
                for i, (name, partition_id) in enumerate(partition_ids.items()):
                    self.swimlanes_geometry[partition_id] = {
                        'x': 100 + i * 280,
                        'y': 50,
                        'width': 250, 
                        'height': 1000
                    }
        
        layout_manager = EmergencyLayoutManager(debug=self.debug_options.get('positioning', False))
        
        # Przekaż informacje o torach
        if hasattr(self, 'swimlane_ids'):
            layout_manager._partition_ids = self.swimlane_ids
        
        return layout_manager

    def set_parser_mapping(self, parser_id_to_xmi_id):
        """Ustawia mapowanie między parser_id a xmi_id."""
        self.parser_id_to_xmi_id = parser_id_to_xmi_id
        
        if self.debug_options.get('positioning', False):
            
            log_debug(f"📋 Mapowanie parser→XMI ustawione: {len(parser_id_to_xmi_id)} elementów")

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

    def _get_element_geometry(self, element_id, element_type):
        """POPRAWIONA METODA: Lepsze debugowanie i walidacja pozycji"""
        
        if self.debug_options.get('positioning', False):
            log_debug(f"🎯 _get_element_geometry dla {element_id[-6:]}: typ={element_type}")
        
        # ============================================================================
        # METODA 1: AI Layout Manager positions (GŁÓWNA)
        # ============================================================================
        if (hasattr(self, 'layout_manager') and 
            hasattr(self.layout_manager, 'element_positions')):
            
            layout_positions = self.layout_manager.element_positions
            
            if self.debug_options.get('positioning', False):
                log_debug(f"   🔍 Layout ma {len(layout_positions)} pozycji")
                log_debug(f"   🔍 Szukam pozycji dla {element_id}")
            
            # A. Szukaj bezpośrednio po element_id
            if element_id in layout_positions:
                pos = layout_positions[element_id]
                geometry = f"Left={pos['x']};Top={pos['y']};Right={pos['x'] + pos['width']};Bottom={pos['y'] + pos['height']};"
                
                if self.debug_options.get('positioning', False):
                    log_debug(f"✅ ZNALEZIONO BEZPOŚREDNIO: {element_id[-6:]} → {geometry}")
                
                # WALIDACJA ROZMIARÓW
                if self._validate_geometry(geometry, element_id):
                    return geometry
                else:
                    if self.debug_options.get('positioning', False):
                        log_debug(f"❌ POZYCJA NIEPRAWIDŁOWA: {geometry}")
            
            # B. Mapowanie przez parser_id → xmi_id
            if hasattr(self, 'parser_id_to_xmi_id'):
                parser_id = None
                for p_id, x_id in self.parser_id_to_xmi_id.items():
                    if x_id == element_id:
                        parser_id = p_id
                        break
                
                if parser_id and parser_id in layout_positions:
                    pos = layout_positions[parser_id]
                    geometry = f"Left={pos['x']};Top={pos['y']};Right={pos['x'] + pos['width']};Bottom={pos['y'] + pos['height']};"
                    
                    if self.debug_options.get('positioning', False):
                        log_debug(f"✅ ZNALEZIONO PRZEZ MAPOWANIE: {element_id[-6:]} ← {parser_id[-6:]} → {geometry}")
                    
                    # WALIDACJA ROZMIARÓW
                    if self._validate_geometry(geometry, element_id):
                        return geometry
                    else:
                        if self.debug_options.get('positioning', False):
                            log_debug(f"❌ POZYCJA NIEPRAWIDŁOWA: {geometry}")
            
            # C. Częściowe dopasowanie ID
            for layout_id, pos in layout_positions.items():
                if (layout_id.endswith(element_id[-8:]) or 
                    element_id.endswith(layout_id[-8:])):
                    
                    geometry = f"Left={pos['x']};Top={pos['y']};Right={pos['x'] + pos['width']};Bottom={pos['y'] + pos['height']};"
                    
                    if self.debug_options.get('positioning', False):
                        log_debug(f"✅ DOPASOWANIE CZĘŚCIOWE: {element_id[-6:]} ≈ {layout_id[-8:]} → {geometry}")
                    
                    # WALIDACJA ROZMIARÓW
                    if self._validate_geometry(geometry, element_id):
                        return geometry
            
            if self.debug_options.get('positioning', False):
                log_debug(f"   ❌ Nie znaleziono w AI positions")
                log_debug(f"   🔍 Dostępne klucze: {list(layout_positions.keys())[:3]}...")
        
        # ============================================================================
        # METODA 2: INTELIGENTNY FALLBACK (POPRAWIONY)
        # ============================================================================
        if self.debug_options.get('positioning', False):
            log_debug(f"   🔧 Używam inteligentnego fallback dla {element_id[-6:]}")
        
        return self._generate_smart_fallback_position(element_id, element_type)

    def _validate_geometry(self, geometry, element_id):
        """Waliduje czy geometria elementu jest sensowna"""
        
        try:
            # Parse geometry string
            parts = geometry.split(';')
            coords = {}
            for part in parts:
                if '=' in part:
                    key, value = part.split('=')
                    if value.isdigit():
                        coords[key] = int(value)
            
            left = coords.get('Left', 0)
            top = coords.get('Top', 0)  
            right = coords.get('Right', 0)
            bottom = coords.get('Bottom', 0)
            
            width = right - left
            height = bottom - top
            
            # WALIDACJA ROZMIARÓW
            if width <= 0 or height <= 0:
                if self.debug_options.get('positioning', False):
                    log_debug(f"❌ NIEPRAWIDŁOWE WYMIARY: width={width}, height={height}")
                return False
            
            # WALIDACJA ROZMIARÓW - zbyt duże (zgodnie z twoim problemem)
            if width > 300 or height > 150:  # ← Zmniejszone limity
                if self.debug_options.get('positioning', False):
                    log_debug(f"❌ ZBYT DUŻE WYMIARY: width={width}, height={height}")
                return False
            
            # ✅ WALIDACJA UNIKALNOŚCI POZYCJI
            if not hasattr(self, '_used_xmi_positions'):
                self._used_xmi_positions = set()
            
            pos_key = (left, top)
            if pos_key in self._used_xmi_positions:
                if self.debug_options.get('positioning', False):
                    log_debug(f"❌ DUPLIKAT POZYCJI: ({left},{top}) już używana")
                return False
            
            self._used_xmi_positions.add(pos_key)
            
            # WALIDACJA POZYCJI - poza canvas
            canvas_width = getattr(self, 'canvas_width', 1800)
            canvas_height = getattr(self, 'canvas_height', 1600)
            
            if left < 0 or top < 0 or right > canvas_width or bottom > canvas_height:
                if self.debug_options.get('positioning', False):
                    log_debug(f"❌ POZYCJA POZA CANVAS: ({left},{top}) - ({right},{bottom})")
                return False
            
            return True
            
        except Exception as e:
            if self.debug_options.get('positioning', False):
                log_debug(f"❌ BŁĄD WALIDACJI: {e}")
            return False

    def _generate_smart_fallback_position(self, element_id, element_type):
        """Generuje inteligentną pozycję fallback bez duplikatów"""
        
        # ✅ BEZPIECZNE POBRANIE CANVAS DIMENSIONS
        canvas_width = getattr(self, 'canvas_width', 1800)
        canvas_height = getattr(self, 'canvas_height', 1600)
        
        # Utwórz unique seed na podstawie element_id
        import hashlib
        seed = int(hashlib.md5(element_id.encode()).hexdigest()[:8], 16) % 10000
        
        # Pobierz nazwę elementu dla lepszego pozycjonowania
        element_name = ""
        if element_id in self.id_map:
            element_name = self.id_map[element_id].attrib.get('name', '').lower()
        
        if self.debug_options.get('positioning', False):
            log_debug(f"   🔧 FALLBACK dla '{element_name[:30]}' typ={element_type}")
        
        # POZYCJONOWANIE WEDŁUG TYPU I NAZWY
        if element_type in ['InitialNode'] or 'start' in str(element_name):
            # START - góra centrum
            x, y = 600 + (seed % 3 - 1) * 50, 80 + (seed % 2) * 30
            width, height = 60, 60
            
        elif element_type in ['ActivityFinalNode'] or any(word in str(element_name) for word in ['end', 'final', 'koniec']):
            # END - dół centrum  
            x, y = 600 + (seed % 3 - 1) * 50, 1400 + (seed % 3) * 40
            width, height = 60, 60
            
        elif element_type in ['DecisionNode'] or 'decyzja' in element_name or '?' in element_name:
            # DECYZJE - centrum z przestrzenią
            decision_index = (seed % 5)
            x, y = 650 + decision_index * 100, 300 + decision_index * 150
            width, height = 120, 80
            
        elif any(word in element_name for word in ['aktywacja', 'konto aktywowane', 'sukces']):
            # ELEMENTY SUKCESU - prawa strona
            x, y = 1000 + (seed % 2) * 150, 800 + (seed % 4) * 100
            width, height = 160, 70
            
        elif any(word in element_name for word in ['blokada', 'zablokowane', 'niepowodzenie', 'błąd']):
            # ELEMENTY BŁĘDÓW - prawa strona, niżej
            x, y = 1000 + (seed % 2) * 150, 1000 + (seed % 4) * 80
            width, height = 160, 70
            
        elif any(word in element_name for word in ['ponowne', 'powtórz', 'retry']):
            # PONOWNE AKCJE - lewa strona
            x, y = 200 + (seed % 2) * 100, 600 + (seed % 3) * 120
            width, height = 180, 80
            
        elif any(word in element_name for word in ['weryfikacja', 'sprawdź', 'validate']):
            # WERYFIKACJE - centrum
            x, y = 550 + (seed % 4) * 80, 500 + (seed % 4) * 100
            width, height = 160, 70
            
        elif 'manualna' in element_name or 'analityk' in element_name:
            # MANUALNE OPERACJE - prawa strona
            x, y = 900 + (seed % 2) * 100, 700 + (seed % 3) * 80
            width, height = 160, 70
            
        else:
            # STANDARDOWE AKTYWNOŚCI - centrum z rozrzutem
            col = seed % 5  # 5 kolumn
            row = (seed // 5) % 10  # 10 wierszy
            x, y = 300 + col * 150, 200 + row * 100
            width, height = 140, 60
        
        # WALIDACJA I KOREKTA POZYCJI
        if x < 50:
            x = 50
        if y < 50:
            y = 50
        if x + width > canvas_width - 50:
            x = canvas_width - width - 50
        if y + height > canvas_height - 50:
            y = canvas_height - height - 50
        
        geometry = f"Left={x};Top={y};Right={x + width};Bottom={y + height};"
        
        if self.debug_options.get('positioning', False):
            log_debug(f"   📐 FALLBACK RESULT: {element_id[-6:]} → {geometry}")
        
        return geometry

    def _add_missing_decision_branches(self, parent_activity):
        """Metoda dodawania brakujących gałęzi 'tak' w decyzjach"""
        
        if self.debug_options.get('processing', False):
            log_debug("🔗 ANALIZA BRAKUJĄCYCH GAŁĘZI 'TAK' W DECYZJACH")
        
        # Znajdź elementy sukcesu (nieosiągalne)
        success_keywords = ['konto aktywowane', 'aktywacja', 'sukces', 'pozytywn']
        unreachable_success = []
        
        for node_id, node in self.id_map.items():
            if (node.attrib.get('xmi:type') == 'uml:Action' and 
                any(kw in node.attrib.get('name', '').lower() for kw in success_keywords)):
                
                # Sprawdź czy węzeł nie ma przejść przychodzących
                has_incoming = any(t['target_id'] == node_id for t in self.transitions)
                if not has_incoming:
                    unreachable_success.append(node_id)
        
        if self.debug_options.get('processing', False):
            log_debug(f"    🔍 Znaleziono {len(unreachable_success)} nieosiągalnych elementów sukcesu")
        
        # Znajdź decyzje które mają tylko gałąź 'nie'
        decisions_missing_yes = []
        
        for node_id, node in self.id_map.items():
            if node.attrib.get('xmi:type') == 'uml:DecisionNode':
                yes_branches = [t for t in self.transitions if t['source_id'] == node_id and t['name'] == 'tak']
                no_branches = [t for t in self.transitions if t['source_id'] == node_id and t['name'] == 'nie']
                
                if len(no_branches) > 0 and len(yes_branches) == 0:
                    decisions_missing_yes.append(node_id)
                    if self.debug_options.get('processing', False):
                        decision_name = node.attrib.get('name', 'unnamed')
                        log_debug(f"    ⚠️ Decyzja '{decision_name[:30]}...' ma tylko gałąź 'nie'")
        
        # Połącz decyzje z elementami sukcesu
        added_branches = 0
        
        for i, decision_id in enumerate(decisions_missing_yes):
            if i < len(unreachable_success):
                success_node_id = unreachable_success[i]
                
                # Dodaj gałąź 'tak'
                if self._add_transition(parent_activity, decision_id, success_node_id, 'tak'):
                    added_branches += 1
                    
                    if self.debug_options.get('processing', False):
                        log_debug(f"      ✅ Dodano gałąź 'tak': {decision_id[-6:]} → {success_node_id[-6:]}")
        
        if added_branches > 0 and self.debug_options.get('processing', False):
            log_debug(f"    ✅ DODANO {added_branches} brakujących gałęzi 'tak'")
        
        return added_branches

    def _format_xml(self, root: ET.Element) -> str:
        """Poprawia nagłówek i formatuje XML do czytelnej postaci."""
        # Debugowanie - znajdź wszystkie wartości None przed serializacją
        if self.debug_options.get('xml', False):
            
            log_debug("Sprawdzanie wartości None w drzewie XML...")
            self._debug_find_none_values(root)
        
        # Zastosuj sanityzację do całego drzewa XML rekurencyjnie
        self._sanitize_tree(root)
        
        xml_string = ET.tostring(root, encoding='unicode', method='xml', xml_declaration=True)
        xml_string_fixed = xml_string.replace("<?xml version='1.0' encoding='unicode'?>", '<?xml version="1.0" encoding="UTF-8"?>')
        dom = xml.dom.minidom.parseString(xml_string_fixed)
        return dom.toprettyxml(indent="  ")

    def _final_validation(self):
        """Końcowa walidacja diagramu"""
        
        if self.debug_options.get('processing', False):
            log_debug("🔍 KOŃCOWA WERYFIKACJA DIAGRAMU")
        
        # 1. Usuń nieprawidłowe przejścia z ActivityFinalNode
        invalid_transitions = []
        
        for transition in self.transitions[:]:
            source_id = transition['source_id']
            source_node = self.id_map.get(source_id)
            
            if source_node is not None and source_node.attrib.get('xmi:type') == 'uml:ActivityFinalNode':
                invalid_transitions.append(transition)
                self.transitions.remove(transition)
        
        # 2. Usuń samo-połączenia
        self_loops = []
        
        for transition in self.transitions[:]:
            if transition['source_id'] == transition['target_id']:
                self_loops.append(transition)
                self.transitions.remove(transition)
        
        # 3. Usuń duplikaty przejść
        seen_transitions = set()
        duplicate_transitions = []
        
        for transition in self.transitions[:]:
            key = (transition['source_id'], transition['target_id'], transition.get('name', ''))
            if key in seen_transitions:
                duplicate_transitions.append(transition)
                self.transitions.remove(transition)
            else:
                seen_transitions.add(key)
        
        if self.debug_options.get('processing', False):
            total_removed = len(invalid_transitions) + len(self_loops) + len(duplicate_transitions)
            log_debug(f"Końcowa weryfikacja: usunięto {total_removed} nieprawidłowych przejść")

    def _validate_unique_elements(self):
        """Waliduje unikalność elementów przed zapisem XMI"""
        
        if not hasattr(self, 'created_nodes'):
            return True
        
        duplicates = []
        names_by_type = {}
        
        for node_id, node_info in self.created_nodes.items():
            key = f"{node_info['type']}:{node_info['name']}:{node_info['partition']}"
            
            if key not in names_by_type:
                names_by_type[key] = []
            names_by_type[key].append(node_id)
        
        # Znajdź duplikaty
        for key, node_ids in names_by_type.items():
            if len(node_ids) > 1:
                duplicates.append({
                    'key': key,
                    'nodes': node_ids,
                    'count': len(node_ids)
                })
        
        if duplicates:
            log_warning(f"⚠️ WYKRYTO {len(duplicates)} grup duplikatów węzłów:")
            for dup in duplicates:
                log_warning(f"   • {dup['key']}: {dup['count']} duplikatów")
                if self.debug_options.get('processing', False):
                    for node_id in dup['nodes']:
                        log_debug(f"      - {node_id}")
            return False
        
        return True

# --- Przykład użycia ---
if __name__ == '__main__':
    import argparse
    import os
    from utils.plantuml.plantuml_activity_parser import PlantUMLActivityParser
    from datetime import datetime
    
    setup_logger('xmi_activity_generator.log')
    
    # Utworzenie parsera argumentów z bezpośrednią obsługą plików PlantUML
    parser = argparse.ArgumentParser(description='Generator XMI dla diagramów aktywności')
    parser.add_argument('input_file', nargs='?', default='Diagram_aktywności_nowy.puml',
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
    parser.add_argument('--ai-positioning', '-ai', action='store_true', 
                    help='Użyj AI do inteligentnego pozycjonowania elementów')
    parser.add_argument('--ai-communication', '-aic', action='store_true', 
                    help='Włącz szczegółowe logowanie komunikacji z modelem AI')
    parser.add_argument('--real-ai', '-rai', action='store_true', 
                    help='Użyj prawdziwego modelu AI zamiast deterministycznego')
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
        'ai_communication': args.ai_communication or args.debug_all,  # ← NOWE
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
        log_debug(f"🔍 Przetwarzanie pliku: {args.input_file}")
        log_debug(f"📊 Nazwa diagramu: {diagram_name}")
        
        # Parsowanie PlantUML bezpośrednio
        log_debug("🔄 Parsowanie kodu PlantUML...")
        parser = PlantUMLActivityParser(puml_content, parser_debug_options)
        parsed_data = parser.parse()
        diagram_title = parsed_data.get("title", "Diagram aktywności")
        
        # Generowanie XMI
        log_debug("🔄 Generowanie XMI...")
        generator = XMIActivityGenerator(author="Generator XMI", debug_options=generator_debug_options)
        # ✅ PRZEKAŻ OPCJĘ AI
        if args.ai_positioning:
            generator.use_ai_positioning = True
            generator.use_real_ai = args.real_ai  # ← DODAJ TĘ LINIĘ
            log_debug("🧠 Włączono AI pozycjonowanie elementów")
            
            if args.real_ai:
                log_info("🤖 Włączono prawdziwy model AI dla pozycjonowania")
            else:
                log_info("🧠 Włączono deterministyczne AI pozycjonowanie")

        xml_content = generator.generate_activity_diagram(diagram_name = diagram_title, parsed_data=parsed_data)
        
        # Zapisz wynikowy XMI
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        log_debug(f"\n✅ Gotowe! Diagram XMI zapisany do pliku: {output_filename}")
        
    except FileNotFoundError:
        log_debug(f"❌ Błąd: Nie znaleziono pliku {args.input_file}")
    except Exception as e:
        log_debug(f"❌ Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()
