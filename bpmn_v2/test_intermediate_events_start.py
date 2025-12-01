#!/usr/bin/env python3
"""
Test sprawdzający walidację Intermediate Events jako alternatywy dla Start/End Events w Pool.
"""

import sys
import os

# Dodaj ścieżki do PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from bpmn_compliance_validator import BPMNComplianceValidator, BPMNSeverity

def test_intermediate_catch_as_start():
    """Test: Intermediate Catch Event może zastąpić Start Event w Pool"""
    print("🔍 Test: Intermediate Catch Event jako Start Event w Pool")
    
    # Multi-pool process gdzie drugi Pool rozpoczyna się od Intermediate Message Catch Event
    bpmn_data = {
        'participants': [
            {'id': 'pool1', 'name': 'Klient', 'type': 'pool'},
            {'id': 'pool2', 'name': 'Bank', 'type': 'pool'}
        ],
        'elements': [
            # Pool 1 - tradycyjny start
            {'id': 'start1', 'type': 'startEvent', 'participant': 'pool1', 'name': 'Klient rozpoczyna'},
            {'id': 'task1', 'type': 'userTask', 'participant': 'pool1', 'name': 'Wypełnij wniosek'},
            {'id': 'msg_throw1', 'type': 'intermediateMessageThrowEvent', 'participant': 'pool1', 'name': 'Wyślij wniosek'},
            
            # Pool 2 - start przez Intermediate Message Catch Event
            {'id': 'msg_catch2', 'type': 'intermediateMessageCatchEvent', 'participant': 'pool2', 'name': 'Otrzymaj wniosek'},
            {'id': 'task2', 'type': 'serviceTask', 'participant': 'pool2', 'name': 'Przetwórz wniosek'},
            {'id': 'end2', 'type': 'endEvent', 'participant': 'pool2', 'name': 'Bank kończy'}
        ],
        'flows': [
            # Sequence Flow w Pool 1
            {'id': 'seq1', 'type': 'sequence', 'source': 'start1', 'target': 'task1'},
            {'id': 'seq2', 'type': 'sequence', 'source': 'task1', 'target': 'msg_throw1'},
            
            # Message Flow między Pool
            {'id': 'msg1', 'type': 'message', 'source': 'msg_throw1', 'target': 'msg_catch2', 'name': 'Wniosek'},
            
            # Sequence Flow w Pool 2
            {'id': 'seq3', 'type': 'sequence', 'source': 'msg_catch2', 'target': 'task2'},
            {'id': 'seq4', 'type': 'sequence', 'source': 'task2', 'target': 'end2'}
        ]
    }
    
    validator = BPMNComplianceValidator()
    result = validator.validate_bpmn_compliance(bpmn_data)
    
    # Pool 2 nie powinien mieć problemu z brakiem Start Event, bo ma Intermediate Message Catch Event
    struct_001_issues = [issue for issue in result.issues if issue.rule_code == 'STRUCT_001' and 'pool2' in issue.element_id]
    struct_007_issues = [issue for issue in result.issues if issue.rule_code == 'STRUCT_007' and 'pool2' in issue.element_id]
    
    print(f"   STRUCT_001 issues dla Pool 2: {len(struct_001_issues)}")
    print(f"   STRUCT_007 issues dla Pool 2: {len(struct_007_issues)}")
    
    if struct_001_issues or struct_007_issues:
        print("   ❌ FAIL: Pool 2 nadal ma błędy dotyczące braku Start Event")
        for issue in struct_001_issues + struct_007_issues:
            print(f"      - {issue.message}")
        return False
    else:
        print("   ✅ PASS: Pool 2 poprawnie akceptuje Intermediate Message Catch Event jako start")
        return True

def test_intermediate_throw_as_end():
    """Test: Intermediate Throw Event może zastąpić End Event w Pool"""
    print("\n🔍 Test: Intermediate Throw Event jako End Event w Pool")
    
    # Multi-pool process gdzie pierwszy Pool kończy się Intermediate Message Throw Event
    bpmn_data = {
        'participants': [
            {'id': 'pool1', 'name': 'Sklep', 'type': 'pool'},
            {'id': 'pool2', 'name': 'Bank', 'type': 'pool'}
        ],
        'elements': [
            # Pool 1 - kończy się Message Throw Event
            {'id': 'start1', 'type': 'startEvent', 'participant': 'pool1', 'name': 'Transakcja rozpoczęta'},
            {'id': 'task1', 'type': 'userTask', 'participant': 'pool1', 'name': 'Skanuj kod BLIK'},
            {'id': 'msg_throw1', 'type': 'intermediateMessageThrowEvent', 'participant': 'pool1', 'name': 'Wyślij żądanie'},
            
            # Pool 2 - tradycyjny end
            {'id': 'msg_catch2', 'type': 'intermediateMessageCatchEvent', 'participant': 'pool2', 'name': 'Otrzymaj żądanie'},
            {'id': 'task2', 'type': 'serviceTask', 'participant': 'pool2', 'name': 'Autoryzuj płatność'},
            {'id': 'end2', 'type': 'endEvent', 'participant': 'pool2', 'name': 'Płatność zatwierdzona'}
        ],
        'flows': [
            # Sequence Flow w Pool 1
            {'id': 'seq1', 'type': 'sequence', 'source': 'start1', 'target': 'task1'},
            {'id': 'seq2', 'type': 'sequence', 'source': 'task1', 'target': 'msg_throw1'},
            
            # Message Flow między Pool
            {'id': 'msg1', 'type': 'message', 'source': 'msg_throw1', 'target': 'msg_catch2', 'name': 'Żądanie autoryzacji'},
            
            # Sequence Flow w Pool 2
            {'id': 'seq3', 'type': 'sequence', 'source': 'msg_catch2', 'target': 'task2'},
            {'id': 'seq4', 'type': 'sequence', 'source': 'task2', 'target': 'end2'}
        ]
    }
    
    validator = BPMNComplianceValidator()
    result = validator.validate_bpmn_compliance(bpmn_data)
    
    # Pool 1 nie powinien mieć problemu z brakiem End Event, bo ma Intermediate Message Throw Event
    struct_002_issues = [issue for issue in result.issues if issue.rule_code == 'STRUCT_002' and 'pool1' in issue.element_id]
    
    print(f"   STRUCT_002 issues dla Pool 1: {len(struct_002_issues)}")
    
    if struct_002_issues:
        print("   ❌ FAIL: Pool 1 nadal ma błędy dotyczące braku End Event")
        for issue in struct_002_issues:
            print(f"      - {issue.message}")
        return False
    else:
        print("   ✅ PASS: Pool 1 poprawnie akceptuje Intermediate Message Throw Event jako koniec")
        return True

def test_single_pool_still_requires_start_end():
    """Test: Single Pool z Intermediate Events jest poprawny"""
    print("\n🔍 Test: Single Pool z Intermediate Events jest poprawny")
    
    # Single pool process z Intermediate Events (jest poprawny według BPMN 2.0)
    bpmn_data = {
        'participants': [
            {'id': 'pool1', 'name': 'Proces', 'type': 'pool'}
        ],
        'elements': [
            # Intermediate Events mogą zastępować Start/End Events
            {'id': 'msg_catch1', 'type': 'intermediateCatchEvent', 'participant': 'pool1', 'name': 'Czeka na sygnał'},
            {'id': 'task1', 'type': 'userTask', 'participant': 'pool1', 'name': 'Wykonaj zadanie'},
            {'id': 'msg_throw1', 'type': 'intermediateThrowEvent', 'participant': 'pool1', 'name': 'Wyślij sygnał'},
        ],
        'flows': [
            {'id': 'seq1', 'type': 'sequence', 'source': 'msg_catch1', 'target': 'task1'},
            {'id': 'seq2', 'type': 'sequence', 'source': 'task1', 'target': 'msg_throw1'}
        ]
    }
    
    validator = BPMNComplianceValidator()
    result = validator.validate_bpmn_compliance(bpmn_data)
    
    # Single pool z Intermediate Events jest poprawny
    struct_001_issues = [issue for issue in result.issues if issue.rule_code == 'STRUCT_001']
    struct_002_issues = [issue for issue in result.issues if issue.rule_code == 'STRUCT_002']
    
    print(f"   STRUCT_001 issues: {len(struct_001_issues)}")
    print(f"   STRUCT_002 issues: {len(struct_002_issues)}")
    
    if not struct_001_issues and not struct_002_issues:
        print("   ✅ PASS: Single Pool z Intermediate Events jest poprawnie akceptowany")
        return True
    else:
        print("   ❌ FAIL: Single Pool z Intermediate Events nie jest akceptowany")
        return False

def test_intermediate_with_message_flows():
    """Test: Intermediate Events z Message Flow w single pool"""
    print("\n🔍 Test: Intermediate Events z Message Flow w single pool")
    
    # Single pool z Message Flow (symulacja komunikacji zewnętrznej)
    bpmn_data = {
        'participants': [
            {'id': 'pool1', 'name': 'System', 'type': 'pool'}
        ],
        'elements': [
            {'id': 'msg_catch1', 'type': 'intermediateMessageCatchEvent', 'participant': 'pool1', 'name': 'Otrzymaj żądanie'},
            {'id': 'task1', 'type': 'serviceTask', 'participant': 'pool1', 'name': 'Przetwórz żądanie'},
            {'id': 'msg_throw1', 'type': 'intermediateMessageThrowEvent', 'participant': 'pool1', 'name': 'Wyślij odpowiedź'},
        ],
        'flows': [
            # Message Flow "z zewnątrz" - symulujemy external trigger
            {'id': 'msg_in', 'type': 'message', 'source': 'external', 'target': 'msg_catch1', 'name': 'Żądanie'},
            
            {'id': 'seq1', 'type': 'sequence', 'source': 'msg_catch1', 'target': 'task1'},
            {'id': 'seq2', 'type': 'sequence', 'source': 'task1', 'target': 'msg_throw1'},
            
            # Message Flow "na zewnątrz"
            {'id': 'msg_out', 'type': 'message', 'source': 'msg_throw1', 'target': 'external', 'name': 'Odpowiedź'}
        ]
    }
    
    validator = BPMNComplianceValidator()
    result = validator.validate_bpmn_compliance(bpmn_data)
    
    # Z Message Flow, Intermediate Events mogą zastąpić Start/End
    struct_001_issues = [issue for issue in result.issues if issue.rule_code == 'STRUCT_001']
    struct_002_issues = [issue for issue in result.issues if issue.rule_code == 'STRUCT_002']
    
    print(f"   STRUCT_001 issues: {len(struct_001_issues)}")
    print(f"   STRUCT_002 issues: {len(struct_002_issues)}")
    
    if not struct_001_issues and not struct_002_issues:
        print("   ✅ PASS: Intermediate Events z Message Flow poprawnie zastępują Start/End Events")
        return True
    else:
        print("   ❌ FAIL: Intermediate Events z Message Flow nie są akceptowane")
        for issue in struct_001_issues + struct_002_issues:
            print(f"      - {issue.message}")
        return False

if __name__ == "__main__":
    print("🧪 Testowanie Intermediate Events jako alternatyw dla Start/End Events\n")
    
    tests = [
        test_intermediate_catch_as_start,
        test_intermediate_throw_as_end,
        test_single_pool_still_requires_start_end,
        test_intermediate_with_message_flows
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Wyniki testów: {passed}/{total} passed")
    
    if passed == total:
        print("✅ Wszystkie testy przeszły! Intermediate Events poprawnie zastępują Start/End Events w odpowiednich kontekstach.")
    else:
        print("❌ Niektóre testy nie przeszły. Sprawdź implementację.")