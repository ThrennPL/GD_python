"""
Test mechanizmów automatycznego naprawiania błędów strukturalnych
Demonstracja jak system naprawia wykryte problemy
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bpmn_v2'))

from bpmn_compliance_validator import BPMNComplianceValidator
from bpmn_improvement_engine import BPMNImprovementEngine
import json

def test_auto_fixes():
    validator = BPMNComplianceValidator()
    engine = BPMNImprovementEngine()
    
    print("🔧 TEST MECHANIZMÓW AUTOMATYCZNEGO NAPRAWIANIA")
    print("=" * 70)
    
    # Proces z wieloma błędami strukturalnymi
    broken_process = {
        "process_name": "Proces z błędami do naprawienia",
        "participants": [
            {"id": "pool1", "name": "Pool 1", "type": "human"},
            {"id": "pool2", "name": "Pool 2", "type": "system"}
        ],
        "elements": [
            # Brak Start Event - będzie dodany
            {"id": "task1", "name": "Zadanie bez Pool", "type": "userTask"},  # Brak participant
            {"id": "task2", "name": "", "type": "serviceTask", "participant": "pool1"},  # Brak nazwy
            {"id": "gateway1", "name": "Decyzja", "type": "exclusiveGateway", "participant": "pool2"},
            {"id": "task3", "name": "Zadanie końcowe", "type": "userTask", "participant": "pool2"}
            # Brak End Event - będzie dodany
        ],
        "flows": [
            {"id": "flow1", "source": "task1", "target": "task2", "type": "message"},  # Message w Pool - błąd
            {"id": "flow2", "source": "task2", "target": "gateway1", "type": "sequence"},
            {"id": "flow3", "source": "gateway1", "target": "task3", "type": "sequence"}  # Gateway z 1 wyjściem
        ]
    }
    
    print("📊 ANALIZA POCZĄTKOWA:")
    initial_report = validator.validate_bpmn_compliance(broken_process)
    print(f"   Jakość początkowa: {initial_report.overall_score:.1f}/100")
    print(f"   Poziom zgodności: {initial_report.compliance_level}")
    print(f"   Łączna liczba problemów: {len(initial_report.issues)}")
    
    # Kategoryzuj problemy
    structural_issues = [i for i in initial_report.issues if i.rule_code.startswith('STRUCT')]
    auto_fixable = [i for i in initial_report.issues if i.auto_fixable]
    
    print(f"\n🔍 SZCZEGÓŁY PROBLEMÓW:")
    print(f"   Problemy strukturalne: {len(structural_issues)}")
    print(f"   Auto-fixable: {len(auto_fixable)}")
    
    print(f"\n📋 LISTA PROBLEMÓW DO NAPRAWIENIA:")
    for i, issue in enumerate(initial_report.issues, 1):
        auto_fix_icon = "🔧" if issue.auto_fixable else "⚠️ "
        print(f"   {i:2d}. {auto_fix_icon} [{issue.rule_code}] {issue.message}")
        if issue.auto_fixable:
            print(f"       💡 Naprawa: {issue.suggestion}")
    
    # Test automatycznych napraw
    print(f"\n" + "=" * 70)
    print("🛠️  ZASTOSOWANIE AUTOMATYCZNYCH NAPRAW")
    
    auto_fix_suggestions = validator.get_auto_fix_suggestions(initial_report.issues)
    print(f"   Możliwych auto-fixes: {len(auto_fix_suggestions['auto_fixes'])}")
    print(f"   Wymaga ręcznej poprawy: {len(auto_fix_suggestions['manual_review_required'])}")
    
    if auto_fix_suggestions['auto_fixes']:
        print(f"\n🔧 SZCZEGÓŁY AUTOMATYCZNYCH NAPRAW:")
        for fix in auto_fix_suggestions['auto_fixes']:
            print(f"   - Element: {fix['element_id']}")
            print(f"     Typ naprawy: {fix['fix_type']}")
            print(f"     Reguła: {fix['rule_code']}")
    
    # Iteracyjna poprawa
    print(f"\n" + "=" * 70)
    print("🔄 ITERACYJNY PROCES POPRAWIANIA")
    
    improved_process = broken_process.copy()
    iteration = 0
    max_iterations = 3
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n📍 ITERACJA {iteration}:")
        
        # Walidacja
        current_report = validator.validate_bpmn_compliance(improved_process)
        print(f"   Jakość: {current_report.overall_score:.1f}/100")
        print(f"   Problemy: {len(current_report.issues)}")
        
        if not current_report.issues:
            print("   ✅ Wszystkie problemy naprawione!")
            break
        
        # Zastosuj proste naprawy
        improvements_applied = []
        
        # Naprawa 1: Dodaj Start Event jeśli brakuje
        start_issues = [i for i in current_report.issues if 'Start Event' in i.message and 'nie ma' in i.message]
        if start_issues:
            new_start = {
                "id": "start_auto", 
                "name": "Start (auto-generated)", 
                "type": "startEvent",
                "participant": improved_process.get("participants", [{}])[0].get("id", "default_pool")
            }
            improved_process["elements"].insert(0, new_start)
            improvements_applied.append("Dodano Start Event")
        
        # Naprawa 2: Dodaj End Event jeśli brakuje
        end_issues = [i for i in current_report.issues if 'End Event' in i.message and 'nie ma' in i.message]
        if end_issues:
            new_end = {
                "id": "end_auto",
                "name": "Koniec (auto-generated)",
                "type": "endEvent", 
                "participant": improved_process.get("participants", [{}])[-1].get("id", "default_pool")
            }
            improved_process["elements"].append(new_end)
            improvements_applied.append("Dodano End Event")
        
        # Naprawa 3: Przypisz elementy do Pool
        unassigned_issues = [i for i in current_report.issues if 'nie jest przypisany' in i.message]
        for issue in unassigned_issues:
            for element in improved_process.get("elements", []):
                if element.get("id") == issue.element_id and not element.get("participant"):
                    element["participant"] = improved_process.get("participants", [{}])[0].get("id", "default_pool")
                    improvements_applied.append(f"Przypisano {issue.element_id} do Pool")
        
        # Naprawa 4: Zamień Message Flow na Sequence Flow wewnątrz Pool
        message_flow_issues = [i for i in current_report.issues if 'Message Flow zamiast Sequence Flow' in i.message]
        for issue in message_flow_issues:
            for flow in improved_process.get("flows", []):
                if flow.get("type") == "message":
                    # Sprawdź czy oba elementy są w tym samym Pool
                    source_elem = next((e for e in improved_process["elements"] if e.get("id") == flow.get("source")), None)
                    target_elem = next((e for e in improved_process["elements"] if e.get("id") == flow.get("target")), None)
                    if source_elem and target_elem and source_elem.get("participant") == target_elem.get("participant"):
                        flow["type"] = "sequence"
                        improvements_applied.append(f"Zamieniono Message Flow na Sequence Flow")
        
        if improvements_applied:
            print(f"   🔧 Zastosowane naprawy:")
            for improvement in improvements_applied:
                print(f"      - {improvement}")
        else:
            print("   ⚠️  Brak możliwych automatycznych napraw")
            break
    
    # Finalna ocena
    print(f"\n" + "=" * 70)
    print("📊 PODSUMOWANIE NAPRAW")
    
    final_report = validator.validate_bpmn_compliance(improved_process)
    
    print(f"\n📈 PORÓWNANIE WYNIKÓW:")
    print(f"   Jakość początkowa: {initial_report.overall_score:.1f}/100")
    print(f"   Jakość końcowa: {final_report.overall_score:.1f}/100")
    print(f"   Poprawa: +{final_report.overall_score - initial_report.overall_score:.1f} punktów")
    
    print(f"\n🔢 LICZBA PROBLEMÓW:")
    print(f"   Początkowa: {len(initial_report.issues)}")
    print(f"   Końcowa: {len(final_report.issues)}")
    print(f"   Naprawiono: {len(initial_report.issues) - len(final_report.issues)} problemów")
    
    print(f"\n📋 POZOSTAŁE PROBLEMY:")
    if final_report.issues:
        for issue in final_report.issues:
            print(f"   ❌ [{issue.rule_code}] {issue.message}")
    else:
        print("   ✅ Wszystkie problemy zostały naprawione!")
    
    # Wyświetl finalną strukturę
    print(f"\n🏗️  FINALNA STRUKTURA PROCESU:")
    print(f"   Uczestnicy: {len(improved_process.get('participants', []))}")
    print(f"   Elementy: {len(improved_process.get('elements', []))}")
    print(f"   Przepływy: {len(improved_process.get('flows', []))}")
    
    types_count = {}
    for element in improved_process.get('elements', []):
        elem_type = element.get('type', 'unknown')
        types_count[elem_type] = types_count.get(elem_type, 0) + 1
    
    print(f"   Typy elementów:")
    for elem_type, count in sorted(types_count.items()):
        print(f"     - {elem_type}: {count}")

if __name__ == "__main__":
    test_auto_fixes()