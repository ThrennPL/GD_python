"""
BPMN v2 - JSON to XML Generator
Prosty generator BPMN XML z JSON (bez warstw pośrednich)

Ten moduł zawiera:
1. Direct JSON → BPMN XML conversion
2. Automatic layout calculation
3. Complete BPMN 2.0 XML generation
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET

from structure_definition import (
    BPMNDiagram, Process, Pool, Lane, Task, Gateway, StartEvent, EndEvent,
    SequenceFlow, MessageFlow, ElementType, TaskType, GatewayType
)


class BPMNLayoutCalculator:
    """Kalkulator pozycji elementów BPMN"""
    
    def __init__(self):
        self.pool_height = 200
        self.pool_width = 1200
        self.element_spacing = 150
        self.lane_height = 150
        self.start_x = 100
        self.start_y = 100
    
    def calculate_layout(self, bpmn_data: Dict) -> Dict[str, Dict]:
        """
        Oblicza pozycje wszystkich elementów
        
        Args:
            bpmn_data: Dane BPMN z JSON
            
        Returns:
            Dictionary z pozycjami {element_id: {x, y, width, height}}
        """
        positions = {}
        
        participants = bpmn_data.get('participants', [])
        elements = bpmn_data.get('elements', [])
        
        if len(participants) > 1:
            # Layout z poolami
            positions.update(self._calculate_pool_layout(participants, elements))
        else:
            # Layout prosty (bez pooli)
            positions.update(self._calculate_simple_layout(elements))
        
        return positions
    
    def _calculate_pool_layout(self, participants: List[Dict], elements: List[Dict]) -> Dict[str, Dict]:
        """Oblicza layout z poolami"""
        positions = {}
        current_y = self.start_y
        
        for participant in participants:
            participant_id = participant['id']
            participant_elements = [e for e in elements if e.get('participant') == participant_id]
            
            # Pool position
            positions[f"pool_{participant_id}"] = {
                'x': self.start_x,
                'y': current_y,
                'width': self.pool_width,
                'height': self.pool_height
            }
            
            # Elements within pool
            element_x = self.start_x + 50
            element_y = current_y + 60
            
            for i, element in enumerate(participant_elements):
                elem_width, elem_height = self._get_element_dimensions(element['type'])
                
                positions[element['id']] = {
                    'x': element_x + (i * self.element_spacing),
                    'y': element_y,
                    'width': elem_width,
                    'height': elem_height
                }
            
            current_y += self.pool_height + 50
        
        return positions
    
    def _calculate_simple_layout(self, elements: List[Dict]) -> Dict[str, Dict]:
        """Oblicza prosty layout poziomy"""
        positions = {}
        current_x = self.start_x
        current_y = self.start_y + 100
        
        for element in elements:
            elem_width, elem_height = self._get_element_dimensions(element['type'])
            
            positions[element['id']] = {
                'x': current_x,
                'y': current_y,
                'width': elem_width,
                'height': elem_height
            }
            
            current_x += self.element_spacing
        
        return positions
    
    def _get_element_dimensions(self, element_type: str) -> Tuple[int, int]:
        """Zwraca wymiary elementu (width, height)"""
        dimensions = {
            'startEvent': (36, 36),
            'endEvent': (36, 36),
            'userTask': (100, 80),
            'serviceTask': (100, 80),
            'task': (100, 80),
            'exclusiveGateway': (50, 50),
            'parallelGateway': (50, 50)
        }
        return dimensions.get(element_type, (100, 80))


class BPMNXMLGenerator:
    """Generator BPMN XML z JSON"""
    
    def __init__(self):
        self.layout_calculator = BPMNLayoutCalculator()
        self.namespaces = {
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'dc': 'http://www.omg.org/spec/DD/20100524/DC', 
            'di': 'http://www.omg.org/spec/DD/20100524/DI'
        }
    
    def generate_bpmn_xml(self, bpmn_json: Dict) -> str:
        """
        Główna metoda generująca kompletny BPMN XML
        
        Args:
            bpmn_json: Dane procesu w JSON
            
        Returns:
            Kompletny BPMN XML string
        """
        # Register namespaces
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
        
        # Calculate layout
        positions = self.layout_calculator.calculate_layout(bpmn_json)
        
        # Create root element
        root = self._create_root_element(bpmn_json)
        
        # Add collaboration (if multiple participants)
        if len(bpmn_json.get('participants', [])) > 1:
            self._add_collaboration(root, bpmn_json)
        
        # Add processes
        self._add_processes(root, bpmn_json)
        
        # Add diagram (visual layout)
        self._add_diagram(root, bpmn_json, positions)
        
        # Generate XML string
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        
        # Add XML declaration and format
        formatted_xml = self._format_xml(xml_str)
        
        return formatted_xml
    
    def _create_root_element(self, bpmn_json: Dict) -> Element:
        """Tworzy główny element definitions"""
        root = Element('bpmn:definitions')
        root.set('xmlns:bpmn', self.namespaces['bpmn'])
        root.set('xmlns:bpmndi', self.namespaces['bpmndi'])
        root.set('xmlns:dc', self.namespaces['dc'])
        root.set('xmlns:di', self.namespaces['di'])
        root.set('id', f"definitions_{uuid.uuid4().hex[:8]}")
        root.set('targetNamespace', 'http://bpmn.io/schema/bpmn')
        root.set('exporter', 'BPMN Generator v2')
        root.set('exporterVersion', '1.0.0')
        
        return root
    
    def _add_collaboration(self, root: Element, bpmn_json: Dict):
        """Dodaje współpracę między uczestnikami"""
        collaboration = SubElement(root, 'bpmn:collaboration')
        collaboration.set('id', 'collaboration_1')
        
        # Add participants
        for participant in bpmn_json.get('participants', []):
            participant_elem = SubElement(collaboration, 'bpmn:participant')
            participant_elem.set('id', f"participant_{participant['id']}")
            participant_elem.set('name', participant['name'])
            participant_elem.set('processRef', f"process_{participant['id']}")
        
        # Detect and add all cross-participant flows as message flows
        all_flows = bpmn_json.get('flows', [])
        elements = bpmn_json.get('elements', [])
        
        # Create mapping: element_id -> participant_id
        element_to_participant = {e['id']: e.get('participant') for e in elements}
        
        # Find cross-participant flows
        cross_participant_flows = []
        for flow in all_flows:
            source_participant = element_to_participant.get(flow['source'])
            target_participant = element_to_participant.get(flow['target'])
            
            # If source and target are in different participants, it's a message flow
            if (source_participant and target_participant and 
                source_participant != target_participant):
                cross_participant_flows.append(flow)
        
        # Add explicit message flows (flows marked as 'message')
        explicit_message_flows = [f for f in all_flows if f.get('type') == 'message']
        
        # Combine both types
        all_message_flows = cross_participant_flows + explicit_message_flows
        
        # Remove duplicates (if a flow is both cross-participant and marked as message)
        seen_flows = set()
        unique_message_flows = []
        for flow in all_message_flows:
            if flow['id'] not in seen_flows:
                unique_message_flows.append(flow)
                seen_flows.add(flow['id'])
        
        # Add message flows to collaboration
        for flow in unique_message_flows:
            message_flow = SubElement(collaboration, 'bpmn:messageFlow')
            message_flow.set('id', flow['id'])
            message_flow.set('sourceRef', flow['source'])
            message_flow.set('targetRef', flow['target'])
            if flow.get('name'):
                message_flow.set('name', flow['name'])
                
        print(f"🔗 Wykryto {len(unique_message_flows)} message flows między uczestnikami")
    
    def _add_processes(self, root: Element, bpmn_json: Dict):
        """Dodaje procesy"""
        participants = bpmn_json.get('participants', [])
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        if len(participants) > 1:
            # Multiple processes for each participant
            for participant in participants:
                self._add_participant_process(root, participant, elements, flows)
        else:
            # Single main process
            self._add_main_process(root, bpmn_json, elements, flows)
    
    def _add_participant_process(self, root: Element, participant: Dict, all_elements: List[Dict], all_flows: List[Dict]):
        """Dodaje proces dla konkretnego uczestnika"""
        process = SubElement(root, 'bpmn:process')
        process.set('id', f"process_{participant['id']}")
        process.set('name', f"Process for {participant['name']}")
        process.set('isExecutable', 'true')
        
        # Get elements for this participant
        participant_elements = [e for e in all_elements if e.get('participant') == participant['id']]
        
        # Add elements to process
        for element in participant_elements:
            self._add_process_element(process, element)
        
        # Create mapping: element_id -> participant_id for all elements
        element_to_participant = {e['id']: e.get('participant') for e in all_elements}
        
        # Add flows within this process (excluding cross-participant flows)
        participant_element_ids = {e['id'] for e in participant_elements}
        internal_flows = []
        
        for flow in all_flows:
            source_participant = element_to_participant.get(flow['source'])
            target_participant = element_to_participant.get(flow['target'])
            
            # Include only flows that:
            # 1. Are within this participant (source and target in same participant)
            # 2. Are not explicitly marked as message flows
            # 3. Have both source and target in this participant's elements
            is_internal_flow = (
                source_participant == participant['id'] and
                target_participant == participant['id'] and
                flow.get('type', 'sequence') == 'sequence' and
                flow['source'] in participant_element_ids and
                flow['target'] in participant_element_ids
            )
            
            if is_internal_flow:
                internal_flows.append(flow)
        
        # Add internal sequence flows to process
        for flow in internal_flows:
            self._add_sequence_flow(process, flow)
            
        print(f"🔧 Proces '{participant['id']}': {len(participant_elements)} elementów, {len(internal_flows)} przepływów wewnętrznych")
    
    def _add_main_process(self, root: Element, bpmn_json: Dict, elements: List[Dict], flows: List[Dict]):
        """Dodaje główny proces (bez pooli)"""
        process = SubElement(root, 'bpmn:process')
        process.set('id', 'main_process')
        process.set('name', bpmn_json.get('process_name', 'Main Process'))
        process.set('isExecutable', 'true')
        
        # Add all elements
        for element in elements:
            self._add_process_element(process, element)
        
        # Add sequence flows
        sequence_flows = [f for f in flows if f.get('type', 'sequence') == 'sequence']
        for flow in sequence_flows:
            self._add_sequence_flow(process, flow)
    
    def _add_process_element(self, process: Element, element: Dict):
        """Dodaje pojedynczy element do procesu"""
        element_type = element['type']
        
        if element_type == 'startEvent':
            elem = SubElement(process, 'bpmn:startEvent')
        elif element_type == 'endEvent':
            elem = SubElement(process, 'bpmn:endEvent')
        elif element_type == 'intermediateCatchEvent':
            elem = SubElement(process, 'bpmn:intermediateCatchEvent')
        elif element_type == 'intermediateThrowEvent':
            elem = SubElement(process, 'bpmn:intermediateThrowEvent')
        elif element_type in ['userTask', 'serviceTask', 'task']:
            if element_type == 'userTask':
                elem = SubElement(process, 'bpmn:userTask')
                # Add user task attributes
                if element.get('assignee'):
                    elem.set('camunda:assignee', element['assignee'])
            elif element_type == 'serviceTask':
                elem = SubElement(process, 'bpmn:serviceTask')
                # Add service task attributes
                if element.get('implementation'):
                    elem.set('camunda:class', element['implementation'])
            else:
                elem = SubElement(process, 'bpmn:task')
        elif element_type in ['exclusiveGateway', 'parallelGateway']:
            elem = SubElement(process, f'bpmn:{element_type}')
        else:
            # Default to task
            elem = SubElement(process, 'bpmn:task')
        
        elem.set('id', element['id'])
        elem.set('name', element['name'])
    
    def _add_sequence_flow(self, process: Element, flow: Dict):
        """Dodaje przepływ sekwencyjny"""
        flow_elem = SubElement(process, 'bpmn:sequenceFlow')
        flow_elem.set('id', flow['id'])
        flow_elem.set('sourceRef', flow['source'])
        flow_elem.set('targetRef', flow['target'])
        
        if flow.get('name'):
            flow_elem.set('name', flow['name'])
        
        # Add condition expression if present
        if flow.get('condition'):
            condition_expr = SubElement(flow_elem, 'bpmn:conditionExpression')
            condition_expr.set('xsi:type', 'bpmn:tFormalExpression')
            condition_expr.text = flow['condition']
    
    def _add_diagram(self, root: Element, bpmn_json: Dict, positions: Dict[str, Dict]):
        """Dodaje diagram (wizualizację)"""
        diagram = SubElement(root, 'bpmndi:BPMNDiagram')
        diagram.set('id', 'diagram_1')
        
        plane = SubElement(diagram, 'bpmndi:BPMNPlane')
        
        # Set plane element reference
        if len(bpmn_json.get('participants', [])) > 1:
            plane.set('bpmnElement', 'collaboration_1')
        else:
            plane.set('bpmnElement', 'main_process')
        
        # Add participant shapes (pools)
        participants = bpmn_json.get('participants', [])
        if len(participants) > 1:
            for participant in participants:
                pool_key = f"pool_{participant['id']}"
                if pool_key in positions:
                    self._add_pool_shape(plane, participant, positions[pool_key])
        
        # Add element shapes
        for element in bpmn_json.get('elements', []):
            if element['id'] in positions:
                self._add_element_shape(plane, element, positions[element['id']])
        
        # Add flow edges - TYLKO dla flows które rzeczywiście istnieją w modelu
        # Zbierz wszystkie ID flows które zostały dodane do modelu
        existing_flow_ids = set()
        
        # Flows z collaboration (messageFlows)
        participants = bpmn_json.get('participants', [])
        if len(participants) > 1:
            all_elements = bpmn_json.get('elements', [])
            element_to_participant = {e['id']: e.get('participant') for e in all_elements}
            
            for flow in bpmn_json.get('flows', []):
                source_participant = element_to_participant.get(flow['source'])
                target_participant = element_to_participant.get(flow['target'])
                
                # Jeśli flow jest między uczestnikami -> messageFlow w collaboration
                if source_participant and target_participant and source_participant != target_participant:
                    existing_flow_ids.add(flow['id'])
        
        # Flows z procesów (sequenceFlows) 
        # Przeszukaj wszystkie procesy w XML aby znaleźć dodane sequenceFlows
        # Na potrzeby uproszczenia - dodajmy wszystkie flows które są w tym samym procesie
        for flow in bpmn_json.get('flows', []):
            if flow['id'] not in existing_flow_ids:
                # Sprawdź czy source i target są w tym samym procesie
                all_elements = bpmn_json.get('elements', [])
                element_to_participant = {e['id']: e.get('participant') for e in all_elements}
                
                source_participant = element_to_participant.get(flow['source'])
                target_participant = element_to_participant.get(flow['target'])
                
                # Jeśli są w tym samym procesie lub nie ma wielu uczestników
                if (not source_participant or not target_participant or 
                    source_participant == target_participant or len(participants) <= 1):
                    existing_flow_ids.add(flow['id'])
        
        # Dodaj edges tylko dla flows które istnieją w modelu
        for flow in bpmn_json.get('flows', []):
            if flow['id'] in existing_flow_ids:
                self._add_flow_edge(plane, flow, positions)
    
    def _add_pool_shape(self, plane: Element, participant: Dict, position: Dict):
        """Dodaje kształt poolu"""
        shape = SubElement(plane, 'bpmndi:BPMNShape')
        shape.set('id', f"participant_{participant['id']}_di")
        shape.set('bpmnElement', f"participant_{participant['id']}")
        shape.set('isHorizontal', 'true')
        
        bounds = SubElement(shape, 'dc:Bounds')
        bounds.set('x', str(position['x']))
        bounds.set('y', str(position['y']))
        bounds.set('width', str(position['width']))
        bounds.set('height', str(position['height']))
    
    def _add_element_shape(self, plane: Element, element: Dict, position: Dict):
        """Dodaje kształt elementu"""
        shape = SubElement(plane, 'bpmndi:BPMNShape')
        shape.set('id', f"{element['id']}_di")
        shape.set('bpmnElement', element['id'])
        
        bounds = SubElement(shape, 'dc:Bounds')
        bounds.set('x', str(position['x']))
        bounds.set('y', str(position['y']))
        bounds.set('width', str(position['width']))
        bounds.set('height', str(position['height']))
        
        # Add label for elements with text
        if element.get('name') and len(element['name']) > 15:
            self._add_element_label(shape, element, position)
    
    def _add_element_label(self, shape: Element, element: Dict, position: Dict):
        """Dodaje etykietę elementu"""
        label = SubElement(shape, 'bpmndi:BPMNLabel')
        label_bounds = SubElement(label, 'dc:Bounds')
        
        # Calculate label position (below element)
        label_x = position['x']
        label_y = position['y'] + position['height'] + 5
        label_width = max(80, len(element['name']) * 6)
        label_height = 20
        
        label_bounds.set('x', str(label_x))
        label_bounds.set('y', str(label_y))
        label_bounds.set('width', str(label_width))
        label_bounds.set('height', str(label_height))
    
    def _add_flow_edge(self, plane: Element, flow: Dict, positions: Dict[str, Dict]):
        """Dodaje krawędź przepływu"""
        edge = SubElement(plane, 'bpmndi:BPMNEdge')
        edge.set('id', f"{flow['id']}_di")
        edge.set('bpmnElement', flow['id'])
        
        # Calculate waypoints
        source_pos = positions.get(flow['source'])
        target_pos = positions.get(flow['target'])
        
        if source_pos and target_pos:
            # Source waypoint (right side of source element)
            source_x = source_pos['x'] + source_pos['width']
            source_y = source_pos['y'] + (source_pos['height'] // 2)
            
            # Target waypoint (left side of target element)  
            target_x = target_pos['x']
            target_y = target_pos['y'] + (target_pos['height'] // 2)
            
            # Add waypoints
            waypoint1 = SubElement(edge, 'di:waypoint')
            waypoint1.set('x', str(source_x))
            waypoint1.set('y', str(source_y))
            
            waypoint2 = SubElement(edge, 'di:waypoint')
            waypoint2.set('x', str(target_x))
            waypoint2.set('y', str(target_y))
    
    def _format_xml(self, xml_string: str) -> str:
        """Formatuje XML z deklaracją i wcięciami"""
        # Add XML declaration
        formatted = '<?xml version="1.0" encoding="UTF-8"?>\n'
        
        # Add formatted XML (basic formatting)
        lines = xml_string.split('><')
        if len(lines) > 1:
            formatted_lines = [lines[0] + '>']
            
            indent_level = 0
            for line in lines[1:-1]:
                if line.startswith('/'):
                    indent_level -= 1
                
                formatted_lines.append('  ' * indent_level + '<' + line + '>')
                
                if not line.startswith('/') and not line.endswith('/'):
                    indent_level += 1
            
            formatted_lines.append('<' + lines[-1])
            formatted += '\n'.join(formatted_lines)
        else:
            formatted += xml_string
            
        return formatted


class BPMNJSONConverter:
    """Główna klasa konwertera JSON → BPMN XML"""
    
    def __init__(self):
        self.xml_generator = BPMNXMLGenerator()
    
    def convert_json_to_bpmn(self, json_data: Dict) -> str:
        """
        Konwertuje JSON procesu na kompletny BPMN XML
        
        Args:
            json_data: Dane procesu w JSON (zgodne z schema)
            
        Returns:
            Kompletny BPMN XML string
        """
        return self.xml_generator.generate_bpmn_xml(json_data)
    
    def convert_from_file(self, json_file_path: str) -> str:
        """
        Konwertuje plik JSON na BPMN XML
        
        Args:
            json_file_path: Ścieżka do pliku JSON
            
        Returns:
            BPMN XML string
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        return self.convert_json_to_bpmn(json_data)
    
    def save_bpmn_file(self, json_data: Dict, output_path: str):
        """
        Generuje BPMN XML i zapisuje do pliku
        
        Args:
            json_data: Dane procesu w JSON
            output_path: Ścieżka wyjściowa pliku BPMN
        """
        bpmn_xml = self.convert_json_to_bpmn(json_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(bpmn_xml)


if __name__ == "__main__":
    # Test JSON → BPMN conversion
    print("=== BPMN v2 JSON→XML Generator Test ===")
    
    # Przykładowy proces BLIK
    blik_process = {
        "process_name": "Płatność BLIK",
        "description": "Proces płatności BLIK w sklepie",
        "participants": [
            {"id": "klient", "name": "Klient", "type": "human"},
            {"id": "system_blik", "name": "System BLIK", "type": "system"}
        ],
        "elements": [
            {"id": "start1", "name": "Klient chce zapłacić", "type": "startEvent", "participant": "klient"},
            {"id": "task1", "name": "Wybierz płatność BLIK", "type": "userTask", "participant": "klient", "task_type": "user"},
            {"id": "task2", "name": "Wprowadź kod BLIK", "type": "userTask", "participant": "klient", "task_type": "user"},
            {"id": "task3", "name": "Sprawdź dostępność środków", "type": "serviceTask", "participant": "system_blik", "task_type": "service"},
            {"id": "gateway1", "name": "Środki dostępne?", "type": "exclusiveGateway", "participant": "system_blik", "gateway_type": "exclusive"},
            {"id": "task4", "name": "Zablokuj środki", "type": "serviceTask", "participant": "system_blik", "task_type": "service"},
            {"id": "task5", "name": "Wyślij potwierdzenie", "type": "serviceTask", "participant": "system_blik", "task_type": "service"},
            {"id": "end1", "name": "Płatność zakończona", "type": "endEvent", "participant": "system_blik"}
        ],
        "flows": [
            {"id": "flow1", "source": "start1", "target": "task1"},
            {"id": "flow2", "source": "task1", "target": "task2"},
            {"id": "flow3", "source": "task2", "target": "task3", "type": "message"},
            {"id": "flow4", "source": "task3", "target": "gateway1"},
            {"id": "flow5", "source": "gateway1", "target": "task4", "name": "tak", "condition": "środki_dostępne"},
            {"id": "flow6", "source": "gateway1", "target": "end1", "name": "nie", "condition": "brak_środków"},
            {"id": "flow7", "source": "task4", "target": "task5"},
            {"id": "flow8", "source": "task5", "target": "end1"}
        ]
    }
    
    # Konwertuj JSON → BPMN XML
    converter = BPMNJSONConverter()
    
    try:
        bpmn_xml = converter.convert_json_to_bpmn(blik_process)
        
        # Zapisz do pliku
        output_file = f"test_blik_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bpmn"
        converter.save_bpmn_file(blik_process, output_file)
        
        print(f"✅ SUKCES! BPMN XML wygenerowany")
        print(f"📁 Zapisano do: {output_file}")
        print(f"📊 Rozmiar: {len(bpmn_xml)} znaków")
        print(f"🔧 Elementy: {len(blik_process['elements'])}")
        print(f"🔗 Przepływy: {len(blik_process['flows'])}")
        print(f"👥 Uczestnicy: {len(blik_process['participants'])}")
        
        # Pokaż fragment XML
        print("\n📄 Fragment wygenerowanego XML:")
        print(bpmn_xml[:500] + "..." if len(bpmn_xml) > 500 else bpmn_xml)
        
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()