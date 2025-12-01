"""
Test poprawionych reguł strukturalnych dla procesów wielopoolowych
Sprawdzenie czy STRUCT_001, STRUCT_002, STRUCT_003 działają prawidłowo
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bpmn_v2'))

from bpmn_compliance_validator import BPMNComplianceValidator
import json

def test_improved_structural_rules():
    validator = BPMNComplianceValidator()
    print("🔧 TEST POPRAWIONYCH REGUŁ STRUKTURALNYCH")
    print("=" * 70)
    
    # === TEST 1: Proces jednopoolowy (zachowanie jak wcześniej) ===
    print("\n📍 TEST 1: PROCES JEDNOPOOLOWY")
    
    single_pool_process = {
        "process_name": "Proces jednopoolowy",
        "participants": [{"id": "pool1", "name": "Pool 1", "type": "human"}],
        "elements": [
            {"id": "task1", "name": "Zadanie", "type": "userTask", "participant": "pool1"}
            # Brak Start i End Event
        ],
        "flows": []
    }
    
    result = validator.validate_bpmn_compliance(single_pool_process)
    struct_issues = [i for i in result.issues if i.rule_code in ['STRUCT_001', 'STRUCT_002']]
    print(f"   Problemy Start/End Event: {len(struct_issues)}")
    for issue in struct_issues:
        print(f"   ❌ {issue.rule_code}: {issue.message}")
    
    # === TEST 2: Proces wielopoolowy - każdy Pool z aktywnościami ===
    print("\n📍 TEST 2: PROCES WIELOPOOLOWY - POPRAWNY")
    
    multi_pool_correct = {
        "process_name": "Proces wielopoolowy poprawny",
        "participants": [
            {"id": "pool1", "name": "Klient", "type": "human"},
            {"id": "pool2", "name": "System", "type": "system"},
            {"id": "pool3", "name": "Analityk", "type": "human"}
        ],
        "elements": [
            # Pool 1: Ma Start Event
            {"id": "start1", "name": "Rozpoczęcie", "type": "startEvent", "participant": "pool1"},
            {"id": "task1", "name": "Zadanie klienta", "type": "userTask", "participant": "pool1"},
            
            # Pool 2: Rozpoczyna Message Flow (bez Start Event - OK)
            {"id": "task2", "name": "Zadanie systemowe", "type": "serviceTask", "participant": "pool2"},
            {"id": "task3", "name": "Przetwarzanie", "type": "serviceTask", "participant": "pool2"},
            
            # Pool 3: Ma End Event
            {"id": "task4", "name": "Analiza", "type": "userTask", "participant": "pool3"},
            {"id": "end1", "name": "Zakończenie", "type": "endEvent", "participant": "pool3"}
        ],
        "flows": [
            # Sequence Flows wewnątrz Pool
            {"id": "seq1", "source": "start1", "target": "task1", "type": "sequence"},
            {"id": "seq2", "source": "task2", "target": "task3", "type": "sequence"},
            {"id": "seq3", "source": "task4", "target": "end1", "type": "sequence"},
            
            # Message Flows między Pool
            {"id": "msg1", "source": "task1", "target": "task2", "type": "message"},
            {"id": "msg2", "source": "task3", "target": "task4", "type": "message"}
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
    
    # === TEST 3: Start Event z Message Flow przychodzącym (dozwolone) ===
    print("\n📍 TEST 3: START EVENT Z MESSAGE FLOW PRZYCHODZĄCYM")\n    \n    start_with_message = {\n        \"participants\": [\n            {\"id\": \"pool1\", \"name\": \"Pool 1\"},\n            {\"id\": \"pool2\", \"name\": \"Pool 2\"}\n        ],\n        \"elements\": [\n            {\"id\": \"task1\", \"type\": \"userTask\", \"participant\": \"pool1\"},\n            {\"id\": \"start2\", \"type\": \"startEvent\", \"participant\": \"pool2\"},  # Start z Message Flow\n            {\"id\": \"task2\", \"type\": \"userTask\", \"participant\": \"pool2\"}\n        ],\n        \"flows\": [\n            {\"id\": \"msg1\", \"source\": \"task1\", \"target\": \"start2\", \"type\": \"message\"},  # Message do Start\n            {\"id\": \"seq1\", \"source\": \"start2\", \"target\": \"task2\", \"type\": \"sequence\"}\n        ]\n    }\n    \n    result = validator.validate_bpmn_compliance(start_with_message)\n    start_issues = [i for i in result.issues if i.rule_code == 'STRUCT_003' and 'Start Event' in i.message]\n    print(f\"   Problemy z Start Event: {len(start_issues)}\")\n    if start_issues:\n        for issue in start_issues:\n            print(f\"   ❌ {issue.message}\")\n    else:\n        print(\"   ✅ Start Event z Message Flow przychodzącym jest dozwolony!\")\n    \n    # === TEST 4: End Event z Message Flow wychodzącym (dozwolone) ===\n    print(\"\\n📍 TEST 4: END EVENT Z MESSAGE FLOW WYCHODZĄCYM\")\n    \n    end_with_message = {\n        \"participants\": [\n            {\"id\": \"pool1\", \"name\": \"Pool 1\"},\n            {\"id\": \"pool2\", \"name\": \"Pool 2\"}\n        ],\n        \"elements\": [\n            {\"id\": \"task1\", \"type\": \"userTask\", \"participant\": \"pool1\"},\n            {\"id\": \"end1\", \"type\": \"endEvent\", \"participant\": \"pool1\"},  # End z Message Flow\n            {\"id\": \"task2\", \"type\": \"userTask\", \"participant\": \"pool2\"}\n        ],\n        \"flows\": [\n            {\"id\": \"seq1\", \"source\": \"task1\", \"target\": \"end1\", \"type\": \"sequence\"},\n            {\"id\": \"msg1\", \"source\": \"end1\", \"target\": \"task2\", \"type\": \"message\"}  # Message z End\n        ]\n    }\n    \n    result = validator.validate_bpmn_compliance(end_with_message)\n    end_issues = [i for i in result.issues if i.rule_code == 'STRUCT_003' and 'End Event' in i.message]\n    print(f\"   Problemy z End Event: {len(end_issues)}\")\n    if end_issues:\n        for issue in end_issues:\n            print(f\"   ❌ {issue.message}\")\n    else:\n        print(\"   ✅ End Event z Message Flow wychodzącym jest dozwolony!\")\n    \n    # === TEST 5: Sequence Flow do Start Event (niedozwolone) ===\n    print(\"\\n📍 TEST 5: SEQUENCE FLOW DO START EVENT (BŁĄD)\")\n    \n    sequence_to_start = {\n        \"elements\": [\n            {\"id\": \"task1\", \"type\": \"userTask\"},\n            {\"id\": \"start1\", \"type\": \"startEvent\"}\n        ],\n        \"flows\": [\n            {\"id\": \"seq1\", \"source\": \"task1\", \"target\": \"start1\", \"type\": \"sequence\"}  # BŁĄD!\n        ]\n    }\n    \n    result = validator.validate_bpmn_compliance(sequence_to_start)\n    bad_sequence_issues = [i for i in result.issues if 'Sequence Flow' in i.message and 'Start Event' in i.message]\n    print(f\"   Wykryte błędy Sequence Flow: {len(bad_sequence_issues)}\")\n    for issue in bad_sequence_issues:\n        print(f\"   ❌ {issue.message}\")\n        print(f\"   🔧 Auto-fix: {issue.auto_fixable}\")\n    \n    # === PODSUMOWANIE ===\n    print(\"\\n\" + \"=\" * 70)\n    print(\"📊 PODSUMOWANIE TESTÓW POPRAWIONYCH REGUŁ\")\n    print(\"\\n✅ POPRAWKI ZAIMPLEMENTOWANE:\")\n    print(\"   • STRUCT_001: Sprawdza Start Events per Pool (nie globalnie)\")\n    print(\"   • STRUCT_002: Sprawdza End Events per Pool (nie globalnie)\")\n    print(\"   • STRUCT_003: Rozróżnia Sequence Flow vs Message Flow\")\n    print(\"   • Start Event: Message Flow przychodzące ✅, Sequence Flow ❌\")\n    print(\"   • End Event: Message Flow wychodzące ✅, Sequence Flow ❌\")\n    print(\"   • Aktywności: Zarówno Sequence Flow jak i Message Flow ✅\")\n\nif __name__ == \"__main__\":\n    test_improved_structural_rules()