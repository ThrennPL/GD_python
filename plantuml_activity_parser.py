import re
import pprint
import uuid
from datetime import datetime
from logger_utils import log_debug, log_info, log_error, log_exception, log_warning, setup_logger
import unittest
import os

setup_logger("plantuml_activity_parser.log")

class PlantUMLActivityParser:
    """
    Parsuje tekstowy opis diagramu aktywności PlantUML
    i przekształca go w strukturyzowane dane.
    """

    def __init__(self, plantuml_code: str, debug_options=None):
        """
        Inicjalizuje parser.

        Args:
            plantuml_code: Ciąg znaków zawierający kod diagramu PlantUML.
            debug_options: Słownik z opcjami debugowania.
        """
        self.code = plantuml_code
        self.title = ""
        self.swimlanes = {}  # Słownik na swimlanes {name: {'activities': []}}
        self.flow = []       # Lista przechowująca przebieg aktywności
        self.current_swimlane = None
        
        # Opcje debugowania
        self.debug_options = debug_options or {
            'parsing': False,      # Debugowanie procesu parsowania
            'decisions': True,     # Szczegółowe informacje o decyzjach
            'structure': False,    # Informacje o strukturze stosu
            'connections': True,   # Informacje o połączeniach między elementami
        }

    def _generate_id(self):
        """Generuje unikalny identyfikator dla elementu."""
        return f"id_{uuid.uuid4().hex[:8]}"

    def parse(self):
        """
        Główna metoda parsująca, która analizuje kod linia po linii.
        """
        if self.debug_options.get('parsing'):
            log_debug("Rozpoczynam parsowanie kodu PlantUML")
            print("Rozpoczynam parsowanie kodu PlantUML")
        
        lines = self.code.strip().split('\n')
        
        # Stos do śledzenia zagnieżdżonych struktur (if, while, fork)
        structure_stack = []

        # Rejestr połączeń - do debugowania i weryfikacji poprawności
        connections = []
        last_element = None

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("'") or line in ["@startuml", "@enduml"]:
                continue # Pomiń puste linie, komentarze i znaczniki start/end

            if self.debug_options.get('parsing'):
                log_debug(f"Przetwarzanie linii {line_num}: {line}")
                print(f"Przetwarzanie linii {line_num}: {line}")

            # Parsowanie tytułu
            if line.startswith('title'):
                match = re.match(r'^title\s+(.*)$', line)
                if match:
                    self.title = match.group(1).strip()
                    if self.debug_options.get('parsing'):
                        log_debug(f"Znaleziono tytuł: {self.title}")
                        print(f"Znaleziono tytuł: {self.title}")
                    continue

            # Parsowanie swimlane
            if line.startswith('|'):
                match = re.match(r'^\|([^|]+)\|$', line)
                if match:
                    swimlane_name = match.group(1).strip()
                    self.current_swimlane = swimlane_name
                    if swimlane_name not in self.swimlanes:
                        self.swimlanes[swimlane_name] = {'activities': []}
                    
                    element = {
                        'type': 'swimlane',
                        'name': swimlane_name,
                        'id': self._generate_id()
                    }
                    self.flow.append(element)
                    
                    if self.debug_options.get('parsing'):
                        log_debug(f"Dodano swimlane: {swimlane_name}")
                        print(f"Dodano swimlane: {swimlane_name}")
                    
                    # Rejestracja elementu do debugowania połączeń
                    self._register_connection(last_element, element, connections)
                    last_element = element
                    continue

            # Parsowanie aktywności - podstawowe
            if line.startswith(':') and line.endswith(';'):
                activity_text = line[1:-1].strip()
                element = {
                    'type': 'activity',
                    'text': activity_text,
                    'swimlane': self.current_swimlane,
                    'id': self._generate_id()
                }
                self.flow.append(element)
                if self.current_swimlane and self.current_swimlane in self.swimlanes:
                    self.swimlanes[self.current_swimlane]['activities'].append(element)
                
                if self.debug_options.get('parsing'):
                    log_debug(f"Dodano aktywność: {activity_text} w {self.current_swimlane or 'bez swimlane'}")
                    print(f"Dodano aktywność: {activity_text} w {self.current_swimlane or 'bez swimlane'}")
                
                # Rejestracja elementu do debugowania połączeń
                self._register_connection(last_element, element, connections)
                last_element = element
                continue

            # Parsowanie start/stop
            if line in ['start', 'stop', 'end']:
                element = {
                    'type': 'control',
                    'action': line,
                    'swimlane': self.current_swimlane,
                    'id': self._generate_id()
                }
                self.flow.append(element)
                
                if self.debug_options.get('parsing'):
                    log_debug(f"Dodano element kontrolny: {line} w {self.current_swimlane or 'bez swimlane'}")
                    print(f"Dodano element kontrolny: {line} w {self.current_swimlane or 'bez swimlane'}")
                
                # Rejestracja elementu do debugowania połączeń
                self._register_connection(last_element, element, connections)
                last_element = element
                continue

            # Parsowanie decyzji (if/then/else)
            if_match = re.match(r'^if\s*\((.*?)\)\s*then\s*\((.*?)\)$', line)
            if if_match:
                condition, then_label = if_match.groups()
                decision_id = self._generate_id()
                element = {
                    'type': 'decision_start',
                    'condition': condition.strip(),
                    'then_label': then_label.strip(),
                    'swimlane': self.current_swimlane,
                    'id': decision_id,
                    'needs_else': True  # Flaga wskazująca, że decyzja wymaga gałęzi else
                }
                self.flow.append(element)
                structure_stack.append({
                    'type': 'decision',
                    'id': len(self.flow) - 1,  # Indeks w liście flow
                    'element': element,
                    'has_else': False,
                    'decision_id': decision_id
                })
                
                if self.debug_options.get('decisions'):
                    log_debug(f"Rozpoczęto blok decyzyjny: [{condition}] z gałęzią 'then': {then_label}")
                    print(f"Rozpoczęto blok decyzyjny: [{condition}] z gałęzią 'then': {then_label}")
                
                # Rejestracja elementu do debugowania połączeń
                self._register_connection(last_element, element, connections, label=then_label)
                last_element = element
                continue

            # Parsowanie else
            else_match = re.match(r'^else\s*\((.*?)\)$', line)
            if else_match:
                else_label = else_match.group(1).strip()
                
                # Oznacz w strukturze stosu, że mamy else
                decision_id = None
                if structure_stack and structure_stack[-1]['type'] == 'decision':
                    structure_stack[-1]['has_else'] = True
                    decision_id = structure_stack[-1]['decision_id']
                else:
                    log_warning("Znaleziono 'else' bez pasującego 'if'")
                
                element = {
                    'type': 'decision_else',
                    'else_label': else_label,
                    'swimlane': self.current_swimlane,
                    'id': self._generate_id(),
                    'decision_id': decision_id  # Powiązanie z decyzją
                }
                self.flow.append(element)
                
                if self.debug_options.get('decisions'):
                    log_debug(f"Dodano gałąź 'else': {else_label}")
                    print(f"Dodano gałąź 'else': {else_label}")
                
                # Dla else nie rejestrujemy standardowego połączenia,
                # to jest specjalny element strukturalny
                last_element = element
                continue

            # Parsowanie endif
            if line == 'endif':
                if structure_stack:
                    decision_info = structure_stack.pop()
                    has_else = decision_info.get('has_else', False)
                    decision_id = decision_info.get('decision_id')
                    
                    element = {
                        'type': 'decision_end',
                        'swimlane': self.current_swimlane,
                        'id': self._generate_id(),
                        'decision_id': decision_id,  # Powiązanie z decision_start
                        'has_else': has_else         # Informacja, czy ta decyzja miała gałąź else
                    }
                    self.flow.append(element)
                    
                    if self.debug_options.get('decisions'):
                        log_debug(f"Zakończono blok decyzyjny, miał gałąź else: {has_else}")
                        print(f"Zakończono blok decyzyjny, miał gałąź else: {has_else}")
                    
                    # Rejestracja elementu do debugowania połączeń
                    self._register_connection(last_element, element, connections)
                    last_element = element
                continue

            # Parsowanie fork/join
            if line == 'fork':
                fork_id = self._generate_id()
                element = {
                    'type': 'fork_start',
                    'swimlane': self.current_swimlane,
                    'id': fork_id
                }
                self.flow.append(element)
                structure_stack.append({
                    'type': 'fork',
                    'id': len(self.flow) - 1,
                    'element': element,
                    'branches': 1,  # Licznik gałęzi
                    'fork_id': fork_id,
                    'branch_elements': []  # Lista elementów w bieżącej gałęzi
                })
                
                if self.debug_options.get('structure'):
                    log_debug(f"Rozpoczęto blok fork (ID: {fork_id})")
                    print(f"Rozpoczęto blok fork (ID: {fork_id})")
                
                # Rejestracja elementu do debugowania połączeń
                self._register_connection(last_element, element, connections)
                last_element = element
                continue

            if line == 'fork again':
                fork_id = None
                if structure_stack and structure_stack[-1]['type'] == 'fork':
                    # Zapisz elementy poprzedniej gałęzi
                    branch_elements = structure_stack[-1].get('branch_elements', [])
                    if branch_elements:
                        structure_stack[-1]['branches_data'] = structure_stack[-1].get('branches_data', []) + [branch_elements]
                    
                    # Zresetuj dla nowej gałęzi
                    structure_stack[-1]['branch_elements'] = []
                    structure_stack[-1]['branches'] += 1
                    fork_id = structure_stack[-1]['fork_id']
                else:
                    log_warning("Znaleziono 'fork again' bez pasującego 'fork'")
                
                element = {
                    'type': 'fork_again',
                    'swimlane': self.current_swimlane,
                    'id': self._generate_id(),
                    'fork_id': fork_id  # Powiązanie z fork_start
                }
                self.flow.append(element)
                
                if self.debug_options.get('structure'):
                    log_debug(f"Dodano gałąź fork dla {fork_id}")
                    print(f"Dodano gałąź fork dla {fork_id}")
                
                # Dla fork_again nie rejestrujemy standardowego połączenia,
                # to jest specjalny element strukturalny
                last_element = element
                continue

            if line == 'end fork':
                join_id = self._generate_id()
                branches = 1
                fork_id = None
                
                if structure_stack:
                    fork_info = structure_stack.pop()
                    # Zapisz elementy ostatniej gałęzi
                    branch_elements = fork_info.get('branch_elements', [])
                    if branch_elements:
                        fork_info['branches_data'] = fork_info.get('branches_data', []) + [branch_elements]
                    
                    branches = fork_info.get('branches', 1)
                    fork_id = fork_info.get('fork_id')
                else:
                    log_warning("Znaleziono 'end fork' bez pasującego 'fork'")
                
                element = {
                    'type': 'fork_end',
                    'swimlane': self.current_swimlane,
                    'id': join_id,
                    'fork_id': fork_id,  # Powiązanie z fork_start
                    'branches_count': branches
                }
                self.flow.append(element)
                
                if self.debug_options.get('structure'):
                    log_debug(f"Zakończono blok fork (ID: {fork_id}), liczba gałęzi: {branches}, join ID: {join_id}")
                    print(f"Zakończono blok fork (ID: {fork_id}), liczba gałęzi: {branches}, join ID: {join_id}")
                
                # Rejestracja elementu do debugowania połączeń
                self._register_connection(last_element, element, connections)
                last_element = element
                continue

            # Parsowanie notatek
            note_match = re.match(r'^note\s+(left|right|top|bottom)\s*:\s*(.*)$', line)
            if note_match:
                position, text = note_match.groups()
                element = {
                    'type': 'note',
                    'position': position.strip(),
                    'text': text.strip(),
                    'swimlane': self.current_swimlane,
                    'id': self._generate_id()
                }
                self.flow.append(element)
                
                if self.debug_options.get('parsing'):
                    log_debug(f"Dodano notatkę: {text[:30]}... ({position})")
                    print(f"Dodano notatkę: {text[:30]}... ({position})")
                
                # Notatki nie uczestniczą w przepływie, więc nie aktualizujemy last_element
                continue

        # Wykonaj post-processing
        self.post_process()

        # Po zakończeniu parsowania, sprawdź i zaloguj statystyki i problemy
        self._debug_parser_results(connections)

        return {
            'title': self.title,
            'swimlanes': self.swimlanes,
            'flow': self.flow
        }
    
    def _get_element_description(self, element):
        """Tworzy czytelny opis elementu do logowania."""
        if not element:
            return "None"
            
        desc = f"{element['type']}"
        if 'text' in element:
            desc += f" '{element['text'][:20]}...'"
        elif 'condition' in element:
            desc += f" '{element['condition'][:20]}...'"
        elif 'action' in element:
            desc += f" '{element['action']}'"
        
        if 'id' in element:
            desc += f" [ID:{element['id'][-6:]}]"
            
        return desc
    
    def _register_connection(self, source, target, connections, label=""):
        """Rejestruje połączenie między elementami dla celów debugowania."""
        if source and target:
            # Sprawdź, czy to połączenie strukturalne czy logiczne
            is_structural = (source.get('type') == 'swimlane' or target.get('type') == 'swimlane')
            
            connection = {
                'source': source,
                'target': target,
                'label': label,
                'structural': is_structural,  # Oznacz, czy to połączenie strukturalne czy logiczne
                'cross_swimlane': source.get('swimlane') != target.get('swimlane') and 
                                 source.get('swimlane') and target.get('swimlane')
            }
            connections.append(connection)
            
            # Loguj połączenie
            if self.debug_options.get('connections'):
                source_desc = self._get_element_description(source)
                target_desc = self._get_element_description(target)
                
                conn_type = "strukturalne" if is_structural else "logiczne"
                if connection['cross_swimlane']:
                    conn_type += " (między torami)"
                
                log_debug(f"Połączenie {conn_type}: {source_desc} → {target_desc}")
                print(f"Połączenie {conn_type}: {source_desc} → {target_desc}")
    
    def post_process(self):
        """
        Funkcja wykonywana po parsowaniu w celu wykrycia i naprawy problemów.
        """
        # Oznacz niekompletne decyzje (bez gałęzi else)
        self._mark_incomplete_decisions()
        
        # Oznacz przejścia między torami
        self._mark_cross_swimlane_transitions()
        
        # Weryfikacja ciągłości przepływu
        self._verify_flow_continuity()
        
        return self.flow
    
    def _mark_incomplete_decisions(self):
        """Oznacza decyzje, którym brakuje gałęzi else."""
        decision_stack = []
        
        for i, item in enumerate(self.flow):
            if item['type'] == 'decision_start':
                decision_stack.append({
                    'index': i,
                    'item': item,
                    'has_else': False
                })
            elif item['type'] == 'decision_else':
                if decision_stack:
                    decision_stack[-1]['has_else'] = True
            elif item['type'] == 'decision_end':
                if decision_stack:
                    decision_info = decision_stack.pop()
                    # Jeśli decyzja nie ma gałęzi else, oznacz to w flow
                    if not decision_info['has_else']:
                        log_warning(f"Decyzja '{decision_info['item']['condition']}' nie ma gałęzi 'else' - oznaczam jako niekompletną")
                        self.flow[decision_info['index']]['missing_else'] = True
    
    def _mark_cross_swimlane_transitions(self):
        """Oznacza przejścia między różnymi torami."""
        for i in range(1, len(self.flow)):
            prev_item = self.flow[i-1]
            curr_item = self.flow[i]
            
            # Pomijamy specjalne elementy, które nie są częścią logicznego przepływu
            if curr_item['type'] in ['note', 'decision_else', 'fork_again']:
                continue
            
            # Jeśli swimlane się zmienił, oznacz przejście między torami
            if (prev_item.get('swimlane') != curr_item.get('swimlane') and 
                prev_item.get('swimlane') and curr_item.get('swimlane')):
                curr_item['cross_swimlane'] = True
                curr_item['from_swimlane'] = prev_item.get('swimlane')
    
    def _verify_flow_continuity(self):
        """Weryfikuje ciągłość przepływu (od start do stop)."""
        # Szukaj elementów start i stop
        start_elements = [i for i, item in enumerate(self.flow) 
                         if item['type'] == 'control' and item['action'] == 'start']
        stop_elements = [i for i, item in enumerate(self.flow) 
                         if item['type'] == 'control' and item['action'] in ['stop', 'end']]
        
        if not start_elements:
            log_warning("Diagram nie ma elementu początkowego (start)")
        if not stop_elements:
            log_warning("Diagram nie ma elementu końcowego (stop/end)")
        
        # TODO: Bardziej zaawansowana weryfikacja ścieżek przepływu
    
    def _debug_parser_results(self, connections):
        """Analizuje i loguje wyniki parsowania oraz potencjalne problemy."""
        if not self.debug_options.get('parsing'):
            return
            
        # Statystyki
        stats = self.get_statistics()
        log_debug("\n=== STATYSTYKI PARSOWANIA ===")
        print("\n=== STATYSTYKI PARSOWANIA ===")
        
        for key, value in stats.items():
            log_debug(f"  {key}: {value}")
            print(f"  {key}: {value}")
            
        # Wykrywanie potencjalnych problemów
        log_debug("\n=== POTENCJALNE PROBLEMY ===")
        print("\n=== POTENCJALNE PROBLEMY ===")
        
        # 1. Sprawdź niezamknięte bloki strukturalne
        decisions_start = len([x for x in self.flow if x['type'] == 'decision_start'])
        decisions_end = len([x for x in self.flow if x['type'] == 'decision_end'])
        forks_start = len([x for x in self.flow if x['type'] == 'fork_start'])
        forks_end = len([x for x in self.flow if x['type'] == 'fork_end'])
        
        if decisions_start != decisions_end:
            msg = f"Niezgodność bloków decision: start={decisions_start}, end={decisions_end}"
            log_warning(msg)
            print(f"⚠️ {msg}")
            
        if forks_start != forks_end:
            msg = f"Niezgodność bloków fork: start={forks_start}, end={forks_end}"
            log_warning(msg)
            print(f"⚠️ {msg}")
            
        # 2. Sprawdź czy wszystkie decyzje mają gałęzie else
        decision_elements = [i for i, x in enumerate(self.flow) if x['type'] == 'decision_start']
        for idx in decision_elements:
            # Sprawdź czy między decision_start a jego decision_end jest decision_else
            has_else = False
            depth = 1
            for i in range(idx + 1, len(self.flow)):
                if self.flow[i]['type'] == 'decision_start':
                    depth += 1
                elif self.flow[i]['type'] == 'decision_end':
                    depth -= 1
                    if depth == 0:  # Znaleźliśmy pasujący decision_end
                        break
                elif depth == 1 and self.flow[i]['type'] == 'decision_else':
                    has_else = True
            
            if not has_else:
                condition = self.flow[idx].get('condition', 'unknown')
                msg = f"Decyzja '{condition}' nie ma gałęzi 'else'"
                log_warning(msg)
                print(f"⚠️ {msg}")
                # Zaznacz tę decyzję jako niekompletną
                self.flow[idx]['missing_else'] = True
        
        # 3. Sprawdź połączenia między torami
        transitions_between_swimlanes = [x for x in self.flow if x.get('cross_swimlane')]
        if transitions_between_swimlanes:
            log_debug(f"Wykryto {len(transitions_between_swimlanes)} przejść między torami")
            print(f"Wykryto {len(transitions_between_swimlanes)} przejść między torami")
        
        # 4. Sprawdź poprawność połączeń
        if connections:
            log_debug("\n=== ZAREJESTROWANE POŁĄCZENIA ===")
            print("\n=== ZAREJESTROWANE POŁĄCZENIA ===")
            
            logical_connections = [c for c in connections if not c.get('structural', False)]
            structural_connections = [c for c in connections if c.get('structural', False)]
            
            log_debug(f"  Połączenia logiczne: {len(logical_connections)}")
            log_debug(f"  Połączenia strukturalne: {len(structural_connections)}")
            print(f"  Połączenia logiczne: {len(logical_connections)}")
            print(f"  Połączenia strukturalne: {len(structural_connections)}")
            
            for i, conn in enumerate(connections):
                source = conn['source']
                target = conn['target']
                
                source_desc = self._get_element_description(source)
                target_desc = self._get_element_description(target)
                
                conn_type = "strukturalne" if conn.get('structural') else "logiczne"
                if conn.get('cross_swimlane'):
                    conn_type += " (między torami)"
                
                log_debug(f"  {i+1}. [{conn_type}] {source_desc} → {target_desc}")
                print(f"  {i+1}. [{conn_type}] {source_desc} → {target_desc}")

    def get_statistics(self):
        """Zwraca statystyki diagramu."""
        # Oznacz niekompletne decyzje
        incomplete_decisions = sum(1 for item in self.flow 
                                if item['type'] == 'decision_start' and 
                                item.get('missing_else', False))
        
        stats = {
            'total_activities': len([item for item in self.flow if item['type'] == 'activity']),
            'total_decisions': len([item for item in self.flow if item['type'] == 'decision_start']),
            'total_loops': len([item for item in self.flow if item['type'] == 'loop_start']),
            'total_forks': len([item for item in self.flow if item['type'] == 'fork_start']),
            'total_swimlanes': len(self.swimlanes),
            'total_notes': len([item for item in self.flow if item['type'] == 'note']),
            'cross_swimlane_transitions': len([item for item in self.flow if item.get('cross_swimlane')]),
            'decision_branches': {
                'with_else': len([item for item in self.flow 
                                if item['type'] == 'decision_start' and not item.get('missing_else', False)]),
                'without_else': incomplete_decisions
            }
        }
        return stats

# --- Przykład użycia ---
# Na końcu pliku, w sekcji "if __name__ == '__main__':"
if __name__ == '__main__':
    import argparse
    
    # Konfiguracja parsera argumentów
    parser = argparse.ArgumentParser(description='Parser diagramów aktywności PlantUML')
    parser.add_argument('input_file', nargs='?', default='diagram_aktywnosci_PlantUML.puml',
                        help='Plik wejściowy z kodem PlantUML')
    parser.add_argument('--output', '-o', help='Plik wyjściowy JSON (domyślnie: generowana nazwa)')
    parser.add_argument('--debug', '-d', action='store_true', help='Włącz tryb debugowania')
    parser.add_argument('--all', '-a', action='store_true', help='Włącz wszystkie opcje debugowania')
    parser.add_argument('--parsing', '-p', action='store_true', help='Debugowanie procesu parsowania')
    parser.add_argument('--decisions', '-dec', action='store_true', help='Debugowanie decyzji')
    parser.add_argument('--structure', '-s', action='store_true', help='Debugowanie struktury')
    parser.add_argument('--connections', '-c', action='store_true', help='Debugowanie połączeń')
    
    # Parsowanie argumentów
    args = parser.parse_args()
    
    # Konfiguracja opcji debugowania na podstawie argumentów
    debug_options = {
        'parsing': args.parsing or args.all or args.debug,
        'decisions': args.decisions or args.all or args.debug,
        'structure': args.structure or args.all or args.debug,
        'connections': args.connections or args.all or args.debug,
    }
    
    # Ustawienie nazwy pliku wyjściowego
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        output_file = args.output
    else:
        output_file = f'test_activity_{timestamp}.json'
    
    setup_logger("plantuml_activity_parser.log")
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        # Inicjalizacja i uruchomienie parsera
        parser = PlantUMLActivityParser(plantuml_code, debug_options)
        parsed_data = parser.parse()

        print("--- Wynik Parsowania ---")
        log_info("Rozpoczęto parsowanie diagramu aktywności PlantUML.")
        log_info(f"Parsowanie zakończone. Tytuł: {parsed_data['title']}")
        
        if args.debug or args.all:
            pprint.pprint(parsed_data)

        # Wyświetl statystyki
        stats = parser.get_statistics()
        print("\n--- Statystyki ---")
        log_info("Wyświetlanie statystyk diagramu aktywności.")
        log_info(f"Statystyki: {stats}")
        pprint.pprint(stats)

        # Zapisz do pliku JSON
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        print(f"\nWynik zapisany do: {output_file}")
        log_info(f"Wynik zapisany do: {output_file}")
        
    except FileNotFoundError:
        print(f"Nie znaleziono pliku: {args.input_file}")
        log_error(f"Nie znaleziono pliku: {args.input_file}")
        print("Utwórz przykładowy plik PlantUML lub podaj poprawną ścieżkę.")
        log_info("Utwórz przykładowy plik PlantUML lub podaj poprawną ścieżkę.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        log_exception(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()