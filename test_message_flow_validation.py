#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test nowych reguł walidacji Message Flow
"""

from bpmn_v2.bpmn_compliance_validator import BPMNComplianceValidator

# Test JSON z problemami Message Flow
test_bpmn_json = {
    "process_name": "Test Message Flow",
    "participants": [
        {"id": "pool_a", "name": "Pool A", "type": "human"},
        {"id": "pool_b", "name": "Pool B", "type": "system"}
    ],
    "elements": [
        {"id": "start1", "name": "Start", "type": "startEvent", "participant": "pool_a"},
        {"id": "task1", "name": "Task 1", "type": "userTask", "participant": "pool_a"},
        {"id": "end1", "name": "End Event", "type": "endEvent", "participant": "pool_a"},
        {"id": "inter1", "name": "Intermediate", "type": "intermediateCatchEvent", "participant": "pool_b"},
        {"id": "end2", "name": "Message End", "type": "endEvent", "participant": "pool_b", "event_type": "message"}
    ],
    "flows": [
        {"id": "flow1", "source": "start1", "target": "task1", "type": "sequence"},
        {"id": "flow2", "source": "task1", "target": "end1", "type": "sequence"},
        {"id": "msg_flow1", "source": "task1", "target": "end1", "type": "message"},  # Błąd: Message Flow do End Event bez typu message
        {"id": "msg_flow2", "source": "task1", "target": "inter1", "type": "message"},  # Błąd: Message Flow do Intermediate Event bez typu message
        {"id": "msg_flow3", "source": "end2", "target": "task1", "type": "message"}  # OK: Message Flow z End Event typu message
    ]
}

def test_message_flow_validation():
    """Test nowych reguł walidacji Message Flow"""
    print("🔧 Test nowych reguł walidacji Message Flow")
    
    validator = BPMNComplianceValidator()
    
    try:
        # Sprawdź walidację
        validation_result = validator.validate_bpmn_compliance(test_bpmn_json)
        
        print(f"📊 Wynik walidacji:")
        print(f"   Score: {validation_result['score']}")
        print(f"   Level: {validation_result['level']}")
        print(f"   Total issues: {validation_result['statistics']['total_issues']}")
        
        # Sprawdź czy nowe reguły zostały wykryte
        struct_009_found = False
        struct_010_found = False
        struct_011_found = False
        
        for issue in validation_result['issues']:
            print(f"🔍 Issue: {issue['rule_code']} - {issue['message']}")
            
            if issue['rule_code'] == 'STRUCT_009':
                struct_009_found = True
                print("  ✅ STRUCT_009: Message Flow End Event validation works!")
            elif issue['rule_code'] == 'STRUCT_010':
                struct_010_found = True
                print("  ✅ STRUCT_010: Message Flow Intermediate Event validation works!")
            elif issue['rule_code'] == 'STRUCT_011':
                struct_011_found = True
                print("  ✅ STRUCT_011: Message Flow target validation works!")
        
        print(f"\n🎯 Rezultat testów:")
        print(f"   STRUCT_009 (End Event): {'✅ PASS' if struct_009_found else '❌ FAIL'}")
        print(f"   STRUCT_010 (Intermediate): {'✅ PASS' if struct_010_found else '❌ FAIL'}")
        print(f"   STRUCT_011 (Targets): {'✅ PASS' if struct_011_found else '❌ FAIL'}")
        
        return struct_009_found and struct_010_found and struct_011_found
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_message_flow_validation()
    print(f"\n🏁 Test zakończony: {'✅ SUCCESS' if success else '❌ FAILED'}")