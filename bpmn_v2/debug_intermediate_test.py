#!/usr/bin/env python3
"""
Debug test dla Intermediate Events z Message Flow
"""

import sys
import os

# Dodaj ścieżki do PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from bpmn_compliance_validator import BPMNComplianceValidator

def debug_intermediate_with_message_flows():
    """Debug: Intermediate Events z Message Flow w single pool"""
    print("🔍 Debug: Intermediate Events z Message Flow w single pool")
    
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
    
    print("Data structure:")
    print(f"  Participants: {bpmn_data['participants']}")
    print(f"  Elements: {bpmn_data['elements']}")
    print(f"  Flows: {bpmn_data['flows']}")
    
    validator = BPMNComplianceValidator()
    result = validator.validate_bpmn_compliance(bpmn_data)
    
    print(f"\nValidation result:")
    print(f"  Total issues: {len(result.issues)}")
    
    for issue in result.issues:
        print(f"  - {issue.rule_code}: {issue.message}")
        
    # Sprawdź konkretne reguły
    struct_001_issues = [issue for issue in result.issues if issue.rule_code == 'STRUCT_001']
    struct_002_issues = [issue for issue in result.issues if issue.rule_code == 'STRUCT_002']
    
    print(f"\nSTRUCT_001 issues: {len(struct_001_issues)}")
    print(f"STRUCT_002 issues: {len(struct_002_issues)}")

if __name__ == "__main__":
    debug_intermediate_with_message_flows()