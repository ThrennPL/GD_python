import re
import pprint
from datetime import datetime
import unittest
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)

# PODSTAWOWE IMPORTY - ZAWSZE POTRZEBNE
try:
    from utils.logger_utils import log_debug, log_info, log_error, log_exception, setup_logger
except ImportError as e:
    print(f"❌ Krytyczny błąd importu podstawowych modułów: {e}")
    sys.exit(1)

setup_logger('plantuml_sequance_parser.log')

class PlantUMLSequenceParser:
    """
    Parsuje tekstowy opis diagramu sekwencji PlantUML
    i przekształca go w strukturyzowane dane.
    """

    def __init__(self, plantuml_code: str, debug_options=None):
        """
        Inicjalizuje parser.

        Args:
            plantuml_code: Ciąg znaków zawierający kod diagramu PlantUML.
            debug_options: Słownik opcji debugowania.
        """
        self.code = plantuml_code
        self.title = ""
        self.participants = {}  # Słownik na uczestników {alias: {'name': name, 'type': type}}
        self.flow = []          # Lista przechowująca przebieg interakcji
        self.debug_options = debug_options or {
            'parsing': False,
            'structure': False,
            'messages': False,
            'fragments': False,
        }

    def parse(self):
        """
        Główna metoda parsująca, która analizuje kod linia po linii.
        """
        lines = self.code.strip().split('\n')
        
        # Stos do śledzenia zagnieżdżonych fragmentów (np. alt, loop)
        fragment_stack = []

        if self.debug_options.get('parsing'):
            log_debug("Rozpoczynam parsowanie kodu PlantUML (sekwencja)")
            print("Rozpoczynam parsowanie kodu PlantUML (sekwencja)")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("'") or line in ["@startuml", "@enduml"]:
                continue # Pomiń puste linie, komentarze i znaczniki start/end

            if self.debug_options.get('parsing'):
                log_debug(f"Przetwarzanie linii: {line}")
                print(f"Przetwarzanie linii: {line}")

            if line.startswith('title'):
                match = re.match(r'^title\s+(.*)$', line)
                if match:
                    self.title = match.group(1).strip()
                    if self.debug_options.get('parsing'):
                        log_debug(f"Znaleziono tytuł: {self.title}")
                        print(f"Znaleziono tytuł: {self.title}")
                    continue
            
            participant_paterns = [
                (r'^actor\s+"([^"]+)"\s+as\s+(\w+)', 'actor'),
                (r'^participant\s+"([^"]+)"\s+as\s+(\w+)', 'participant'),
                (r'^boundary\s+"([^"]+)"\s+as\s+(\w+)', 'boundary'),
                (r'^control\s+"([^"]+)"\s+as\s+(\w+)', 'control'),
                (r'^entity\s+"([^"]+)"\s+as\s+(\w+)', 'entity'),
                (r'^database\s+"([^"]+)"\s+as\s+(\w+)', 'database'),
            ]

            participant_found = False
            for pattern, p_type in participant_paterns:
                match = re.match(pattern, line)
                if match:
                    name, alias = match.groups()
                    self.participants[alias] = {
                        'name': name, 
                        'type': p_type
                    }
                    participant_found = True
                    if self.debug_options.get('structure'):
                        log_debug(f"Dodano uczestnika: {name} jako {alias} ({p_type})")
                        print(f"Dodano uczestnika: {name} jako {alias} ({p_type})")
                    break
            if participant_found:
                continue
            
            message_match = re.match(r'^([a-zA-Z0-9_]+)\s*(-{1,2}>>?|-[xX])\s*([a-zA-Z0-9_]+)\s*:\s*(.*)$', line)
            if message_match:
                source, arrow, target, message = message_match.groups()
                self.flow.append({
                    'type': 'message',
                    'source': source.strip(),
                    'target': target.strip(),
                    'arrow': arrow.strip(),
                    'text': message.strip()
                })
                if self.debug_options.get('messages'):
                    log_debug(f"Wiadomość: {source} {arrow} {target}: {message}")
                    print(f"Wiadomość: {source} {arrow} {target}: {message}")
                continue

            activation_match = re.match(r'^(activate|deactivate)\s+([a-zA-Z0-9_]+)$', line)
            if activation_match:
                action, participant = activation_match.groups()
                self.flow.append({
                    'type': 'activation',
                    'action': action,
                    'participant': participant
                })
                if self.debug_options.get('messages'):
                    log_debug(f"Aktywacja: {action} {participant}")
                    print(f"Aktywacja: {action} {participant}")
                continue

            note_match = re.match(r'^note\s+(left|right|over\s+\S+)\s*:\s*(.*)$', line)
            if note_match:
                participant, note = note_match.groups()
                self.flow.append({
                    'type': 'note',
                    'participant': participant.strip(),
                    'text': note.strip()
                })
                if self.debug_options.get('messages'):
                    log_debug(f"Notatka: {participant.strip()} : {note.strip()}")
                    print(f"Notatka: {participant.strip()} : {note.strip()}")
                continue
            
            if re.match(r'^(alt|opt|loop)\s*(.*)$', line):
                match = re.match(r'^(alt|opt|loop)\s*(.*)$', line)
                frag_type, condition = match.groups()
                fragment = {
                    'type': 'fragment_start',
                    'kind': frag_type,
                    'condition': condition.strip()
                }
                self.flow.append(fragment)
                fragment_stack.append(fragment)
                if self.debug_options.get('fragments'):
                    log_debug(f"Fragment start: {frag_type} [{condition.strip()}]")
                    print(f"Fragment start: {frag_type} [{condition.strip()}]")
                continue
            
            if line.startswith('else'):
                match = re.match(r'^else\s*(.*)$', line)
                if match and fragment_stack:
                    condition = match.group(1).strip()
                    self.flow.append({
                        'type': 'fragment_else',
                        'condition': condition
                    })
                    if self.debug_options.get('fragments'):
                        log_debug(f"Fragment else: {condition}")
                        print(f"Fragment else: {condition}")
                    continue

            if line == 'end' and fragment_stack:
                fragment_stack.pop()
                self.flow.append({'type': 'fragment_end'})
                if self.debug_options.get('fragments'):
                    log_debug("Fragment end")
                    print("Fragment end")
                continue

        return {
            'title': self.title,
            'participants': self.participants,
            'flow': self.flow
        }

    def _parse_title(self, line: str) -> bool:
        match = re.match(r'^title\s+(.*)$', line)
        if match:
            self.title = match.group(1).strip()
            return True
        return False

    def _parse_participant(self, line: str) -> bool:
        match = re.match(r'^(actor|participant|boundary|database)\s+"([^"]+)"\s+as\s+([a-zA-Z0-9_]+)$', line)
        if match:
            p_type, p_name, p_alias = match.groups()
            self.participants[p_alias] = {'name': p_name, 'type': p_type}
            return True
        return False

    def _parse_message(self, line: str) -> bool:
        # Wyrażenie regularne dla różnych typów strzałek: ->, -->, -x, -->>
        match = re.match(r'^([a-zA-Z0-9_]+)\s*(-{1,2}>>?|-[xX])\s*([a-zA-Z0-9_]+)\s*:\s*(.*)$', line)
        if match:
            source, arrow, target, message = match.groups()
            self.flow.append({
                'type': 'message',
                'source': source.strip(),
                'target': target.strip(),
                'arrow': arrow.strip(),
                'text': message.strip()
            })
            return True
        return False
        
    def _parse_activation(self, line: str, action: str) -> bool:
        match = re.match(rf'^{action}\s+([a-zA-Z0-9_]+)$', line)
        if match:
            participant = match.group(1)
            self.flow.append({
                'type': 'activation',
                'action': action,
                'participant': participant
            })
            return True
        return False

    def _parse_note(self, line: str) -> bool:
        match = re.match(r'^note\s+(right|left|over\s+\S+)\s*:\s*(.*)$', line)
        if match:
            position, text = match.groups()
            self.flow.append({
                'type': 'note',
                'position': position.strip(),
                'text': text.strip()
            })
            return True
        return False
        
    def _parse_fragment_start(self, line: str, stack: list) -> bool:
        match = re.match(r'^(alt|opt|loop)\s*(.*)$', line)
        if match:
            frag_type, condition = match.groups()
            fragment = {
                'type': 'fragment_start',
                'kind': frag_type,
                'condition': condition.strip()
            }
            self.flow.append(fragment)
            stack.append(fragment)
            return True
        return False
        
    def _parse_fragment_else(self, line: str, stack: list) -> bool:
        match = re.match(r'^else\s*(.*)$', line)
        if match and stack:
            condition = match.group(1).strip()
            self.flow.append({
                'type': 'fragment_else',
                'condition': condition
            })
            return True
        return False

    def _parse_fragment_end(self, line: str, stack: list) -> bool:
        if line == 'end' and stack:
            stack.pop()
            self.flow.append({'type': 'fragment_end'})
            return True
        return False

# --- Przykład użycia ---
if __name__ == '__main__':
    import argparse
    import json
    setup_logger('plantuml_sequance_parser.log')
    parser = argparse.ArgumentParser(description='Parser diagramów sekwencji PlantUML')
    parser.add_argument('input_file', nargs='?', default='diagram_sekwencji_PlantUML.puml',
                        help='Plik wejściowy z kodem PlantUML')
    parser.add_argument('--output', '-o', help='Plik wyjściowy JSON (domyślnie: generowana nazwa)')
    parser.add_argument('--debug', '-d', action='store_true', help='Włącz tryb debugowania')
    parser.add_argument('--parsing', '-p', action='store_true', help='Debugowanie procesu parsowania')
    parser.add_argument('--messages', '-m', action='store_true', help='Debugowanie wiadomości')
    parser.add_argument('--fragments', '-f', action='store_true', help='Debugowanie fragmentów')
    parser.add_argument('--structure', '-s', action='store_true', help='Debugowanie struktury')
    args = parser.parse_args()

    debug_options = {
        'parsing': args.parsing or args.debug,
        'messages': args.messages or args.debug,
        'fragments': args.fragments or args.debug,
        'structure': args.structure or args.debug,
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  
    input_file = args.input_file
    output_file = args.output or f'test_sequance_{timestamp}.json'
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        parser = PlantUMLSequenceParser(plantuml_code, debug_options=debug_options)
        parsed_data = parser.parse()

        print("--- Wynik Parsowania ---")
        pprint.pprint(parsed_data)

        # Opcjonalnie zapisz do pliku JSON
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