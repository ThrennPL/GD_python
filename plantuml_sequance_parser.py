import re
import pprint
from datetime import datetime
import unittest
import os

class PlantUMLSequenceParser:
    """
    Parsuje tekstowy opis diagramu sekwencji PlantUML
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
        self.participants = {}  # Słownik na uczestników {alias: {'name': name, 'type': type}}
        self.flow = []          # Lista przechowująca przebieg interakcji

    def parse(self):
        """
        Główna metoda parsująca, która analizuje kod linia po linii.
        """
        lines = self.code.strip().split('\n')
        
        # Stos do śledzenia zagnieżdżonych fragmentów (np. alt, loop)
        fragment_stack = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("'") or line in ["@startuml", "@enduml"]:
                continue # Pomiń puste linie, komentarze i znaczniki start/end

            # Sprawdzanie dopasowań w określonej kolejności
            if self._parse_title(line):
                continue
            if self._parse_participant(line):
                continue
            if self._parse_message(line):
                continue
            if self._parse_activation(line, 'activate'):
                continue
            if self._parse_activation(line, 'deactivate'):
                continue
            if self._parse_note(line):
                continue
            
            # Obsługa fragmentów (alt, else, end)
            if self._parse_fragment_start(line, fragment_stack):
                continue
            if self._parse_fragment_else(line, fragment_stack):
                continue
            if self._parse_fragment_end(line, fragment_stack):
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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  
    input_file = 'diagram_sekwencji_PlantUML.puml'
    output_file = f'test_sequance_{timestamp}.xmi'
    with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
    parser = PlantUMLSequenceParser(plantuml_code)
    parsed_data = parser.parse()

    print("--- Wynik Parsowania ---")
    pprint.pprint(parsed_data)