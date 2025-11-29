#!/usr/bin/env python3
"""
Test naprawionych metod auto-fix
Sprawdza czy nowy system rzeczywiście rozwiązuje problemy połączeń i task_types
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

# Dodaj główny folder do ścieżki
sys.path.append(r'd:\grzegorz\programowanie\GD_python')
sys.path.append(r'd:\grzegorz\programowanie\GD_python\bpmn_v2')

from bpmn_improvement_engine import BPMNImprovementEngine
from bpmn_compliance_validator import BPMNComplianceValidator

def xml_to_json_format(bpmn_xml: str):
    """Konwertuje XML BPMN do formatu JSON używanego przez walidator"""
    root = ET.fromstring(bpmn_xml)
    
    # Namespace dla BPMN
    ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
    
    elements = []
    participants = []
    message_flows = []
    sequence_flows = []
    
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
        
        # Znajdź participant dla tego procesu
        participant_id = None
        for p in participants:
            if p.get('processRef') == process_id:
                participant_id = p.get('id')
                break
        
        # Start Events
        for elem in process.findall('.//bpmn:startEvent', ns):
            elements.append({
                'id': elem.get('id'),
                'name': elem.get('name', ''),
                'type': 'startEvent',
                'participant': participant_id
            })
        
        # End Events  
        for elem in process.findall('.//bpmn:endEvent', ns):
            elements.append({
                'id': elem.get('id'),
                'name': elem.get('name', ''),
                'type': 'endEvent',
                'participant': participant_id
            })
        
        # Intermediate Events
        for elem in process.findall('.//bpmn:intermediateCatchEvent', ns):
            elements.append({
                'id': elem.get('id'),
                'name': elem.get('name', ''),
                'type': 'intermediateCatchEvent',
                'participant': participant_id
            })
        
        # Tasks
        task_types = ['userTask', 'serviceTask', 'manualTask', 'scriptTask', 'receiveTask', 'sendTask', 'task']
        for task_type in task_types:
            for elem in process.findall(f'.//bpmn:{task_type}', ns):
                element_data = {
                    'id': elem.get('id'),
                    'name': elem.get('name', ''),
                    'type': task_type,
                    'participant': participant_id
                }
                # Sprawdź xsi:type dla task_type
                xsi_type = elem.get('{http://www.w3.org/2001/XMLSchema-instance}type')
                if xsi_type:
                    element_data['task_type'] = xsi_type.replace('bpmn:', '')
                elements.append(element_data)
    
    # Zbierz sequence flows
    for flow in root.findall('.//bpmn:sequenceFlow', ns):
        sequence_flows.append({
            'id': flow.get('id'),
            'source': flow.get('sourceRef'),
            'target': flow.get('targetRef'),
            'type': 'sequence'
        })
    
    # Zbierz message flows
    for flow in root.findall('.//bpmn:messageFlow', ns):
        message_flows.append({
            'id': flow.get('id'),
            'source': flow.get('sourceRef'),
            'target': flow.get('targetRef'),
            'type': 'message'
        })
    
    # Połącz sequence i message flows
    flows = sequence_flows + message_flows
    
    return {
        'elements': elements,
        'participants': participants,
        'flows': flows,
        'messageFlows': message_flows
    }

def main():
    print("=== TEST NAPRAWIONYCH METOD AUTO-FIX ===\n")
    
    # Ścieżka do pliku z problemami
    problematic_bpmn = r"d:\grzegorz\programowanie\GD_python\Generated_Process_improved_20251127_181922.bpmn"
    
    if not os.path.exists(problematic_bpmn):
        print(f"❌ Nie znaleziono pliku: {problematic_bpmn}")
        return
    
    # Inicjalizuj komponenty
    print("🔧 Inicjalizacja komponentów...")
    engine = BPMNImprovementEngine()
    validator = BPMNComplianceValidator()
    
    # Wczytaj i przeanalizuj oryginalny plik
    print("📊 Analiza oryginalnego pliku...")
    with open(problematic_bpmn, 'r', encoding='utf-8') as f:
        original_xml = f.read()
    
    # Konwertuj do JSON dla analizy
    try:
        # Napraw XML - dodaj brakujący namespace xsi jeśli potrzeba
        if 'xsi:type' in original_xml and 'xmlns:xsi' not in original_xml:
            original_xml = original_xml.replace(
                '<bpmn:definitions',
                '<bpmn:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            )
        
        original_json = xml_to_json_format(original_xml)
    except Exception as e:
        print(f"❌ Błąd konwersji XML do JSON: {e}")
        return
    
    # Walidacja oryginalna
    original_report = validator.validate_bpmn_compliance(original_json)
    original_issues = original_report.issues
    original_score = original_report.overall_score
    
    print(f"📋 Oryginalny plik:")
    print(f"   • Liczba problemów: {len(original_issues)}")
    print(f"   • Wynik compliance: {original_score:.2f}")
    print(f"   • Elementy: {len(original_json.get('elements', []))}")
    print(f"   • Przepływy: {len(original_json.get('flows', []))}")
    
    # Sprawdź konkretne problemy
    problem_types = {}
    auto_fixable_count = 0
    
    for issue in original_issues:
        problem_type = issue.rule_code
        problem_types[problem_type] = problem_types.get(problem_type, 0) + 1
        if issue.auto_fixable:
            auto_fixable_count += 1
    
    print(f"\n📊 Typy problemów:")
    for ptype, count in problem_types.items():
        print(f"   • {ptype}: {count}")
    
    print(f"🔧 Problemy do automatycznej naprawy: {auto_fixable_count}")
    
    # Przeprowadź naprawę
    print(f"\n🛠️ Rozpoczynam automatyczną naprawę...")
    
    try:
        # Wyłącz print do testowania
        import builtins
        original_print = builtins.print
        builtins.print = lambda *args, **kwargs: None
        
        improved_json = engine.improve_bpmn_process(original_json)
        
        # Przywróć print
        builtins.print = original_print
        
        if not improved_json:
            print("❌ Proces naprawy zwrócił None")
            return
            
        # Walidacja po naprawie
        print("✅ Walidacja po naprawie...")
        improved_report = validator.validate_bpmn_compliance(improved_json)
        improved_issues = improved_report.issues
        improved_score = improved_report.overall_score
        
        print(f"\n📋 Wyniki naprawy:")
        print(f"   • Liczba problemów: {len(original_issues)} → {len(improved_issues)}")
        print(f"   • Wynik compliance: {original_score:.2f} → {improved_score:.2f}")
        print(f"   • Elementy: {len(original_json.get('elements', []))} → {len(improved_json.get('elements', []))}")
        print(f"   • Przepływy: {len(original_json.get('flows', []))} → {len(improved_json.get('flows', []))}")
        
        improvement = improved_score - original_score
        print(f"   • Poprawa: {improvement:+.2f} punktów")
        
        # Sprawdź co zostało naprawione
        if len(improved_issues) < len(original_issues):
            fixed_count = len(original_issues) - len(improved_issues)
            print(f"   • Naprawione problemy: {fixed_count}")
            
            # Pokaż które problemy zostały naprawione
            original_rule_counts = {}
            for issue in original_issues:
                rule = issue.rule_code
                original_rule_counts[rule] = original_rule_counts.get(rule, 0) + 1
                
            improved_rule_counts = {}
            for issue in improved_issues:
                rule = issue.rule_code
                improved_rule_counts[rule] = improved_rule_counts.get(rule, 0) + 1
            
            print(f"\n🎯 Szczegóły napraw:")
            for rule in original_rule_counts:
                original_count = original_rule_counts[rule]
                improved_count = improved_rule_counts.get(rule, 0)
                if improved_count < original_count:
                    fixed = original_count - improved_count
                    print(f"   ✅ {rule}: {original_count} → {improved_count} (naprawiono {fixed})")
                elif improved_count == original_count:
                    print(f"   ⚠️  {rule}: {original_count} → {improved_count} (bez zmian)")
        
        # Sprawdź pozostałe problemy
        if improved_issues:
            print(f"\n⚠️ Pozostałe problemy ({len(improved_issues)}):")
            remaining_types = {}
            for issue in improved_issues:
                rule = issue.rule_code
                remaining_types[rule] = remaining_types.get(rule, 0) + 1
                
            for rule, count in remaining_types.items():
                print(f"   • {rule}: {count}")
        
        # Podsumowanie
        if improved_score > original_score:
            print(f"\n🎉 SUKCES: Naprawiono BPMN!")
            print(f"   Poprawa o {improvement:.2f} punktów ({improvement/original_score*100:.1f}%)")
        elif improved_score == original_score:
            print(f"\n⚠️  Brak poprawy wyniku (może nie było problemów auto-fixable)")
        else:
            print(f"\n❌ Pogorszenie wyniku o {abs(improvement):.2f} punktów")
            
    except Exception as e:
        # Przywróć print jeśli jest błąd
        import builtins
        builtins.print = lambda *args, **kwargs: __import__('builtins').print(*args, **kwargs)
        
        print(f"❌ Błąd podczas naprawy: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()