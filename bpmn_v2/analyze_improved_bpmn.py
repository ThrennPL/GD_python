#!/usr/bin/env python3
"""Analiza poprawionego BPMN - dlaczego ma ocenę 0.00?"""

import xml.etree.ElementTree as ET
from bpmn_compliance_validator import BPMNComplianceValidator

def analyze_improved_bpmn():
    print("🔍 ANALIZA POPRAWIONEGO BPMN")
    print("=" * 60)
    
    # Wczytaj BPMN XML
    file_path = "../Generated_Process_improved_20251127_181922.bpmn"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            bpmn_xml = f.read()
        
        print(f"📄 Wczytano plik: {file_path}")
        print(f"📊 Rozmiar XML: {len(bpmn_xml)} znaków")
        
        # Napraw XML - dodaj brakujący namespace xsi
        if 'xsi:type' in bpmn_xml and 'xmlns:xsi' not in bpmn_xml:
            bpmn_xml = bpmn_xml.replace(
                '<bpmn:definitions',
                '<bpmn:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            )
            print("🔧 Naprawiono brakujący namespace xsi")
        
        # Parsuj XML do sprawdzenia struktury
        root = ET.fromstring(bpmn_xml)
        
        # Znajdź wszystkie elementy
        elements = []
        participants = []
        message_flows = []
        sequence_flows = []
        
        # Namespace dla BPMN
        ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
        
        # Zbierz participants
        for participant in root.findall('.//bpmn:participant', ns):
            participants.append({
                'id': participant.get('id'),
                'name': participant.get('name'),
                'processRef': participant.get('processRef')
            })
        
        # Zbierz wszystkie elementy z procesów
        for process in root.findall('.//bpmn:process', ns):
            process_id = process.get('id')
            
            # Start Events
            for elem in process.findall('.//bpmn:startEvent', ns):
                elements.append({
                    'id': elem.get('id'),
                    'name': elem.get('name'),
                    'type': 'startEvent',
                    'process': process_id
                })
            
            # End Events
            for elem in process.findall('.//bpmn:endEvent', ns):
                elements.append({
                    'id': elem.get('id'),
                    'name': elem.get('name'),
                    'type': 'endEvent',
                    'process': process_id
                })
            
            # Intermediate Catch Events
            for elem in process.findall('.//bpmn:intermediateCatchEvent', ns):
                elements.append({
                    'id': elem.get('id'),
                    'name': elem.get('name'),
                    'type': 'intermediateCatchEvent',
                    'process': process_id
                })
            
            # Tasks
            for task_type in ['userTask', 'serviceTask', 'task']:
                for elem in process.findall(f'.//bpmn:{task_type}', ns):
                    elements.append({
                        'id': elem.get('id'),
                        'name': elem.get('name'),
                        'type': task_type,
                        'process': process_id
                    })
            
            # Gateways
            for gateway_type in ['exclusiveGateway', 'parallelGateway']:
                for elem in process.findall(f'.//bpmn:{gateway_type}', ns):
                    elements.append({
                        'id': elem.get('id'),
                        'name': elem.get('name'),
                        'type': gateway_type,
                        'process': process_id
                    })
        
        # Zbierz Message Flows
        for mf in root.findall('.//bpmn:messageFlow', ns):
            message_flows.append({
                'id': mf.get('id'),
                'sourceRef': mf.get('sourceRef'),
                'targetRef': mf.get('targetRef'),
                'name': mf.get('name')
            })
        
        # Zbierz Sequence Flows
        for sf in root.findall('.//bpmn:sequenceFlow', ns):
            sequence_flows.append({
                'id': sf.get('id'),
                'sourceRef': sf.get('sourceRef'),
                'targetRef': sf.get('targetRef'),
                'name': sf.get('name')
            })
        
        print("\n📊 STRUKTURA BPMN:")
        print(f"   👥 Participants: {len(participants)}")
        print(f"   🔧 Elements: {len(elements)}")
        print(f"   💬 Message Flows: {len(message_flows)}")
        print(f"   ➡️  Sequence Flows: {len(sequence_flows)}")
        
        print("\n👥 PARTICIPANTS:")
        for p in participants:
            print(f"   • {p['id']} - {p['name']}")
        
        print("\n🔧 ELEMENTS PER TYPE:")
        element_types = {}
        for elem in elements:
            elem_type = elem['type']
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        for elem_type, count in element_types.items():
            print(f"   • {elem_type}: {count}")
        
        print("\n🎯 START EVENTS:")
        start_events = [e for e in elements if e['type'] == 'startEvent']
        for se in start_events:
            print(f"   • {se['id']} ({se['process']}) - {se['name']}")
        
        print("\n📨 INTERMEDIATE CATCH EVENTS:")
        catch_events = [e for e in elements if e['type'] == 'intermediateCatchEvent']
        for ce in catch_events:
            print(f"   • {ce['id']} ({ce['process']}) - {ce['name']}")
        
        print("\n🏁 END EVENTS:")
        end_events = [e for e in elements if e['type'] == 'endEvent']
        for ee in end_events:
            print(f"   • {ee['id']} ({ee['process']}) - {ee['name']}")
        
        print("\n💬 MESSAGE FLOWS:")
        for mf in message_flows:
            print(f"   • {mf['id']}: {mf['sourceRef']} → {mf['targetRef']}")
        
        # TERAZ SPRÓBUJ WALIDACJI Z NASZYM SYSTEMEM
        print("\n" + "="*60)
        print("🔍 WALIDACJA Z NASZYM SYSTEMEM")
        print("="*60)
        
        # Konwersja do formatu JSON dla walidatora
        bpmn_json = {
            'elements': [],
            'participants': [],
            'flows': [],
            'messageFlows': []
        }
        
        # Mapowanie participants
        for p in participants:
            bpmn_json['participants'].append({
                'id': p['id'].replace('participant_', ''),
                'name': p['name']
            })
        
        # Mapowanie elements
        participant_map = {p['processRef']: p['id'].replace('participant_', '') for p in participants}
        
        for elem in elements:
            participant_id = participant_map.get(elem['process'], 'unknown')
            bpmn_json['elements'].append({
                'id': elem['id'],
                'name': elem['name'],
                'type': elem['type'],
                'participant': participant_id
            })
        
        # Mapowanie flows
        for sf in sequence_flows:
            bpmn_json['flows'].append({
                'id': sf['id'],
                'source': sf['sourceRef'],
                'target': sf['targetRef'],
                'type': 'sequence'
            })
        
        for mf in message_flows:
            bpmn_json['messageFlows'].append({
                'id': mf['id'],
                'source': mf['sourceRef'],
                'target': mf['targetRef'],
                'type': 'message'
            })
        
        print(f"📊 JSON dla walidatora:")
        print(f"   Elements: {len(bpmn_json['elements'])}")
        print(f"   Participants: {len(bpmn_json['participants'])}")
        print(f"   Flows: {len(bpmn_json['flows'])}")
        print(f"   Message Flows: {len(bpmn_json['messageFlows'])}")
        
        # Uruchom walidację
        validator = BPMNComplianceValidator()
        compliance_report = validator.validate_bpmn_compliance(bpmn_json)
        
        print(f"\n📈 WYNIKI WALIDACJI:")
        print(f"   Overall Score: {compliance_report.overall_score}")
        print(f"   Compliance Level: {compliance_report.compliance_level}")
        print(f"   Issues Found: {len(compliance_report.issues)}")
        
        print(f"\n⚠️ PROBLEMY:")
        for issue in compliance_report.issues:
            print(f"   • {issue.rule_code}: {issue.message}")
            if issue.auto_fixable:
                print(f"     🔧 Auto-fixable: TAK")
            else:
                print(f"     ❌ Auto-fixable: NIE")
        
        # Sprawdź czy są problemy strukturalne
        structural_issues = [i for i in compliance_report.issues if i.rule_code.startswith('STRUCT')]
        print(f"\n🏗️ PROBLEMY STRUKTURALNE: {len(structural_issues)}")
        
        return bpmn_json, compliance_report
        
    except Exception as e:
        print(f"❌ Błąd analizy: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    analyze_improved_bpmn()