import re
import pprint
from datetime import datetime
from logger_utils import log_debug, log_info, log_error, log_exception, setup_logger
import unittest
import os

setup_logger()

class PlantUMLActivityParser:
    """
    Parsuje tekstowy opis diagramu aktywności PlantUML
    i przekształca go w strukturyzowane dane.
    """

    def __init__(self, plantuml_code: str):
        """
        Inicjalizuje parser.

        Args:
            plantuml_code: Ciąg znaków zawierający kod diagramu PlantUML.
        """
        self.code = plantuml_code
        self.title = ""
        self.swimlanes = {}  # Słownik na swimlanes {name: {'activities': []}}
        self.flow = []       # Lista przechowująca przebieg aktywności
        self.current_swimlane = None

    def parse(self):
        """
        Główna metoda parsująca, która analizuje kod linia po linii.
        """
        lines = self.code.strip().split('\n')
        
        # Stos do śledzenia zagnieżdżonych struktur (if, while, fork)
        structure_stack = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("'") or line in ["@startuml", "@enduml"]:
                continue # Pomiń puste linie, komentarze i znaczniki start/end

            # Parsowanie tytułu
            if line.startswith('title'):
                match = re.match(r'^title\s+(.*)$', line)
                if match:
                    self.title = match.group(1).strip()
                    continue

            # Parsowanie swimlane
            if line.startswith('|'):
                match = re.match(r'^\|([^|]+)\|$', line)
                if match:
                    swimlane_name = match.group(1).strip()
                    self.current_swimlane = swimlane_name
                    if swimlane_name not in self.swimlanes:
                        self.swimlanes[swimlane_name] = {'activities': []}
                    self.flow.append({
                        'type': 'swimlane',
                        'name': swimlane_name
                    })
                    continue

            # Parsowanie aktywności - podstawowe
            if line.startswith(':') and line.endswith(';'):
                activity_text = line[1:-1].strip()
                activity = {
                    'type': 'activity',
                    'text': activity_text,
                    'swimlane': self.current_swimlane
                }
                self.flow.append(activity)
                if self.current_swimlane and self.current_swimlane in self.swimlanes:
                    self.swimlanes[self.current_swimlane]['activities'].append(activity)
                continue

            # Parsowanie start/stop
            if line in ['start', 'stop', 'end']:
                self.flow.append({
                    'type': 'control',
                    'action': line,
                    'swimlane': self.current_swimlane
                })
                continue

            # Parsowanie decyzji (if/then/else)
            if_match = re.match(r'^if\s*\((.*?)\)\s*then\s*\((.*?)\)$', line)
            if if_match:
                condition, then_label = if_match.groups()
                decision = {
                    'type': 'decision_start',
                    'condition': condition.strip(),
                    'then_label': then_label.strip(),
                    'swimlane': self.current_swimlane
                }
                self.flow.append(decision)
                structure_stack.append(decision)
                continue

            # Parsowanie else
            else_match = re.match(r'^else\s*\((.*?)\)$', line)
            if else_match:
                else_label = else_match.group(1).strip()
                if structure_stack:
                    self.flow.append({
                        'type': 'decision_else',
                        'else_label': else_label,
                        'swimlane': self.current_swimlane
                    })
                continue

            # Parsowanie endif
            if line == 'endif':
                if structure_stack:
                    structure_stack.pop()
                    self.flow.append({
                        'type': 'decision_end',
                        'swimlane': self.current_swimlane
                    })
                continue

            # Parsowanie pętli while
            while_match = re.match(r'^while\s*\((.*?)\)$', line)
            if while_match:
                condition = while_match.group(1).strip()
                loop = {
                    'type': 'loop_start',
                    'condition': condition,
                    'swimlane': self.current_swimlane
                }
                self.flow.append(loop)
                structure_stack.append(loop)
                continue

            # Parsowanie endwhile
            if line == 'endwhile':
                if structure_stack:
                    structure_stack.pop()
                    self.flow.append({
                        'type': 'loop_end',
                        'swimlane': self.current_swimlane
                    })
                continue

            # Parsowanie fork/join
            if line == 'fork':
                fork = {
                    'type': 'fork_start',
                    'swimlane': self.current_swimlane
                }
                self.flow.append(fork)
                structure_stack.append(fork)
                continue

            if line == 'fork again':
                self.flow.append({
                    'type': 'fork_again',
                    'swimlane': self.current_swimlane
                })
                continue

            if line == 'end fork':
                if structure_stack:
                    structure_stack.pop()
                    self.flow.append({
                        'type': 'fork_end',
                        'swimlane': self.current_swimlane
                    })
                continue

            # Parsowanie notatek
            note_match = re.match(r'^note\s+(left|right|top|bottom)\s*:\s*(.*)$', line)
            if note_match:
                position, text = note_match.groups()
                self.flow.append({
                    'type': 'note',
                    'position': position.strip(),
                    'text': text.strip(),
                    'swimlane': self.current_swimlane
                })
                continue

            # Parsowanie partycji
            partition_match = re.match(r'^partition\s+"([^"]+)"\s*\{$', line)
            if partition_match:
                partition_name = partition_match.group(1).strip()
                partition = {
                    'type': 'partition_start',
                    'name': partition_name,
                    'swimlane': self.current_swimlane
                }
                self.flow.append(partition)
                structure_stack.append(partition)
                continue

            # Parsowanie końca partycji
            if line == '}':
                if structure_stack:
                    last_structure = structure_stack[-1]
                    if last_structure.get('type') == 'partition_start':
                        structure_stack.pop()
                        self.flow.append({
                            'type': 'partition_end',
                            'swimlane': self.current_swimlane
                        })
                continue

            # Parsowanie floating/detached aktywności
            floating_match = re.match(r'^floating\s+:([^;]+);$', line)
            if floating_match:
                activity_text = floating_match.group(1).strip()
                self.flow.append({
                    'type': 'floating_activity',
                    'text': activity_text,
                    'swimlane': self.current_swimlane
                })
                continue

            # Parsowanie strzałek z etykietami
            arrow_match = re.match(r'^->\s*\[([^\]]+)\]$', line)
            if arrow_match:
                label = arrow_match.group(1).strip()
                self.flow.append({
                    'type': 'arrow',
                    'label': label,
                    'swimlane': self.current_swimlane
                })
                continue

            # Parsowanie prostych strzałek
            if line == '->':
                self.flow.append({
                    'type': 'arrow',
                    'label': '',
                    'swimlane': self.current_swimlane
                })
                continue

        return {
            'title': self.title,
            'swimlanes': self.swimlanes,
            'flow': self.flow
        }

    def _parse_title(self, line: str) -> bool:
        """Parsuje tytuł diagramu."""
        match = re.match(r'^title\s+(.*)$', line)
        if match:
            self.title = match.group(1).strip()
            return True
        return False

    def _parse_swimlane(self, line: str) -> bool:
        """Parsuje swimlane."""
        match = re.match(r'^\|([^|]+)\|$', line)
        if match:
            swimlane_name = match.group(1).strip()
            self.current_swimlane = swimlane_name
            if swimlane_name not in self.swimlanes:
                self.swimlanes[swimlane_name] = {'activities': []}
            self.flow.append({
                'type': 'swimlane',
                'name': swimlane_name
            })
            return True
        return False

    def _parse_activity(self, line: str) -> bool:
        """Parsuje aktywność."""
        if line.startswith(':') and line.endswith(';'):
            activity_text = line[1:-1].strip()
            activity = {
                'type': 'activity',
                'text': activity_text,
                'swimlane': self.current_swimlane
            }
            self.flow.append(activity)
            if self.current_swimlane and self.current_swimlane in self.swimlanes:
                self.swimlanes[self.current_swimlane]['activities'].append(activity)
            return True
        return False

    def _parse_control(self, line: str) -> bool:
        """Parsuje elementy kontrolne (start, stop, end)."""
        if line in ['start', 'stop', 'end']:
            self.flow.append({
                'type': 'control',
                'action': line,
                'swimlane': self.current_swimlane
            })
            return True
        return False

    def _parse_decision(self, line: str, stack: list) -> bool:
        """Parsuje decyzje (if/then/else)."""
        if_match = re.match(r'^if\s*\((.*?)\)\s*then\s*\((.*?)\)$', line)
        if if_match:
            condition, then_label = if_match.groups()
            decision = {
                'type': 'decision_start',
                'condition': condition.strip(),
                'then_label': then_label.strip(),
                'swimlane': self.current_swimlane
            }
            self.flow.append(decision)
            stack.append(decision)
            return True
        return False

    def _parse_note(self, line: str) -> bool:
        """Parsuje notatki."""
        match = re.match(r'^note\s+(left|right|top|bottom)\s*:\s*(.*)$', line)
        if match:
            position, text = match.groups()
            self.flow.append({
                'type': 'note',
                'position': position.strip(),
                'text': text.strip(),
                'swimlane': self.current_swimlane
            })
            return True
        return False

    def get_statistics(self):
        """Zwraca statystyki diagramu."""
        stats = {
            'total_activities': len([item for item in self.flow if item['type'] == 'activity']),
            'total_decisions': len([item for item in self.flow if item['type'] == 'decision_start']),
            'total_loops': len([item for item in self.flow if item['type'] == 'loop_start']),
            'total_forks': len([item for item in self.flow if item['type'] == 'fork_start']),
            'total_swimlanes': len(self.swimlanes),
            'total_notes': len([item for item in self.flow if item['type'] == 'note'])
        }
        return stats

# --- Przykład użycia ---
if __name__ == '__main__':
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  
    input_file = 'diagram_aktywnosci_PlantUML.puml'
    output_file = f'test_activity_{timestamp}.json'
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
            
        parser = PlantUMLActivityParser(plantuml_code)
        parsed_data = parser.parse()

        print("--- Wynik Parsowania ---")
        pprint.pprint(parsed_data)

        # Wyświetl statystyki
        stats = parser.get_statistics()
        print("\n--- Statystyki ---")
        pprint.pprint(stats)

        # Opcjonalnie zapisz do pliku JSON
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        print(f"\nWynik zapisany do: {output_file}")
        log_info(f"Wynik zapisany do: {output_file}")
        
    except FileNotFoundError:
        print(f"Nie znaleziono pliku: {input_file}")
        log_error(f"Nie znaleziono pliku: {input_file}")
        print("Utwórz przykładowy plik PlantUML lub zmień nazwę pliku w kodzie.")
        log_info("Utwórz przykładowy plik PlantUML lub zmień nazwę pliku w kodzie.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        log_exception(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()