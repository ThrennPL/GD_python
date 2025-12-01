"""
Test poprawionych reguł strukturalnych dla procesów wielopoolowych
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bpmn_v2'))

from bpmn_compliance_validator import BPMNComplianceValidator

def test_multipool_rules():
    validator = BPMNComplianceValidator()
    print("🔧 TEST POPRAWIONYCH REGUŁ WIELOPOOLOWYCH")
    print("=" * 70)
    
    # TEST 1: Proces wielopoolowy poprawny
    print("\n📍 TEST 1: PROCES WIELOPOOLOWY - POPRAWNY")
    
    multi_pool_correct = {
        "process_name": "Proces wielopoolowy poprawny",
        "participants": [
            {"id": "pool1", "name": "Klient", "type": "human"},
            {"id": "pool2", "name": "System", "type": "system"}
        ],
        "elements": [
            # Pool 1: Ma Start Event
            {"id": "start1", "name": "Rozpoczęcie", "type": "startEvent", "participant": "pool1"},
            {"id": "task1", "name": "Zadanie klienta", "type": "userTask", "participant": "pool1"},
            
            # Pool 2: Rozpoczyna Message Flow (bez Start Event - OK)
            {"id": "task2", "name": "Zadanie systemowe", "type": "serviceTask", "participant": "pool2"},
            {"id": "end1", "name": "Zakończenie", "type": "endEvent", "participant": "pool2"}
        ],
        "flows": [
            # Sequence Flows wewnątrz Pool
            {"id": "seq1", "source": "start1", "target": "task1", "type": "sequence"},
            {"id": "seq2", "source": "task2", "target": "end1", "type": "sequence"},
            
            # Message Flow między Pool
            {"id": "msg1", "source": "task1", "target": "task2", "type": "message"}
        ]
    }
    
    result = validator.validate_bpmn_compliance(multi_pool_correct)
    struct_issues = [i for i in result.issues if i.rule_code in ['STRUCT_001', 'STRUCT_002', 'STRUCT_003']]
    print(f"   Problemy strukturalne: {len(struct_issues)}")
    
    if struct_issues:
        for issue in struct_issues:
            print(f"   ❌ {issue.rule_code}: {issue.message}")
    else:
        print("   ✅ Wszystkie reguły strukturalne spełnione!")
    
    # TEST 2: Start Event z Message Flow przychodzącym
    print("\n📍 TEST 2: START EVENT Z MESSAGE FLOW PRZYCHODZĄCYM")
    
    start_with_message = {
        "participants": [
            {"id": "pool1", "name": "Pool 1"},
            {"id": "pool2", "name": "Pool 2"}
        ],
        "elements": [
            {"id": "task1", "type": "userTask", "participant": "pool1"},
            {"id": "start2", "type": "startEvent", "participant": "pool2"},
            {"id": "task2", "type": "userTask", "participant": "pool2"}
        ],
        "flows": [
            {"id": "msg1", "source": "task1", "target": "start2", "type": "message"},
            {"id": "seq1", "source": "start2", "target": "task2", "type": "sequence"}
        ]
    }
    
    result = validator.validate_bpmn_compliance(start_with_message)
    start_issues = [i for i in result.issues if i.rule_code == 'STRUCT_003' and 'Start Event' in i.message]
    print(f"   Problemy z Start Event: {len(start_issues)}")
    
    if start_issues:
        for issue in start_issues:
            print(f"   ❌ {issue.message}")
    else:
        print("   ✅ Start Event z Message Flow przychodzącym jest dozwolony!")
    
    # TEST 3: Sequence Flow do Start Event (błąd)
    print("\n📍 TEST 3: SEQUENCE FLOW DO START EVENT (BŁĄD)")
    
    sequence_to_start = {
        "elements": [
            {"id": "task1", "type": "userTask"},
            {"id": "start1", "type": "startEvent"}
        ],
        "flows": [
            {"id": "seq1", "source": "task1", "target": "start1", "type": "sequence"}
        ]
    }
    
    result = validator.validate_bpmn_compliance(sequence_to_start)
    bad_sequence_issues = [i for i in result.issues if 'Sequence Flow' in i.message and 'Start Event' in i.message]
    print(f"   Wykryte błędy Sequence Flow: {len(bad_sequence_issues)}")
    
    for issue in bad_sequence_issues:
        print(f"   ❌ {issue.message}")
        print(f"   🔧 Auto-fix: {issue.auto_fixable}")
    
    # PODSUMOWANIE
    print("\n" + "=" * 70)
    print("📊 PODSUMOWANIE POPRAWEK")
    print("\n✅ ZAIMPLEMENTOWANE POPRAWKI:")
    print("   • STRUCT_001: Sprawdza Start Events per Pool (nie globalnie)")
    print("   • STRUCT_002: Sprawdza End Events per Pool (nie globalnie)")  
    print("   • STRUCT_003: Rozróżnia Sequence Flow vs Message Flow")
    print("   • Start Event: Message Flow przychodzące ✅, Sequence Flow ❌")
    print("   • End Event: Message Flow wychodzące ✅, Sequence Flow ❌")
    print("   • Aktywności: Zarówno Sequence Flow jak i Message Flow ✅")

if __name__ == "__main__":
    test_multipool_rules()