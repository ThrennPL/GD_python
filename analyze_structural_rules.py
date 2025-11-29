"""
Kompletny test wszystkich 8 reguł strukturalnych BPMN
Szczegółowa analiza implementacji każdej reguły
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bpmn_v2'))

from bpmn_compliance_validator import BPMNComplianceValidator
import json

def analyze_structural_rules():
    validator = BPMNComplianceValidator()
    print("🔬 ANALIZA STRUKTURALNYCH REGUŁ BPMN")
    print("=" * 80)
    
    # Wyświetl definicje wszystkich reguł strukturalnych
    print("\n📋 DEFINICJE REGUŁ STRUKTURALNYCH:")
    for rule_code, rule_info in validator.rules.items():
        if rule_code.startswith('STRUCT'):
            print(f"\n🔧 {rule_code}: {rule_info['name']}")
            print(f"   📄 Opis: {rule_info['description']}")
            print(f"   ⚠️  Poziom: {rule_info['severity'].value}")
    
    print("\n" + "=" * 80)
    print("🧪 TESTY PRAKTYCZNE KAŻDEJ REGUŁY")
    
    # === STRUCT_001: Start Event Required ===
    print("\n🔧 STRUCT_001: Start Event Required")
    test_struct_001(validator)
    
    # === STRUCT_002: End Event Required ===
    print("\n🔧 STRUCT_002: End Event Required")  
    test_struct_002(validator)
    
    # === STRUCT_003: Element Connectivity ===
    print("\n🔧 STRUCT_003: Element Connectivity")
    test_struct_003(validator)
    
    # === STRUCT_004: Gateway Flows ===
    print("\n🔧 STRUCT_004: Gateway Flows")
    test_struct_004(validator)
    
    # === STRUCT_005: Pool Lane Structure ===
    print("\n🔧 STRUCT_005: Pool Lane Structure")
    test_struct_005(validator)
    
    # === STRUCT_006: Pool Process Continuity ===
    print("\n🔧 STRUCT_006: Pool Process Continuity")
    test_struct_006(validator)
    
    # === STRUCT_007: Pool Autonomy ===
    print("\n🔧 STRUCT_007: Pool Autonomy")
    test_struct_007(validator)
    
    # === STRUCT_008: Message Flow Validation ===
    print("\n🔧 STRUCT_008: Message Flow Validation")
    test_struct_008(validator)

def test_struct_001(validator):
    """Test Start Event Required"""
    print("   📝 Sprawdza: Obecność i poprawność Start Events")
    
    # Test case 1: Brak Start Event
    process = {
        "elements": [
            {"id": "task1", "type": "userTask"},
            {"id": "end1", "type": "endEvent"}
        ],
        "flows": []
    }
    
    result = validator.validate_bpmn_compliance(process)
    issues = [i for i in result.issues if i.rule_code == "STRUCT_001"]
    print(f"   🧪 Test 1 - Brak Start Event: {len(issues)} błędów")
    if issues:
        print(f"      ❌ {issues[0].message}")
        print(f"      🔧 Auto-fix: {issues[0].auto_fixable}")

def test_struct_002(validator):
    """Test End Event Required"""
    print("   📝 Sprawdza: Obecność End Events")
    
    process = {
        "elements": [
            {"id": "start1", "type": "startEvent"},
            {"id": "task1", "type": "userTask"}
        ],
        "flows": []
    }
    
    result = validator.validate_bpmn_compliance(process)
    issues = [i for i in result.issues if i.rule_code == "STRUCT_002"]
    print(f"   🧪 Test - Brak End Event: {len(issues)} błędów")
    if issues:
        print(f"      ❌ {issues[0].message}")

def test_struct_003(validator):
    """Test Element Connectivity"""
    print("   📝 Sprawdza: Poprawność połączeń między elementami")
    
    # Test: Start Event z przepływem wchodzącym
    process = {
        "elements": [
            {"id": "start1", "type": "startEvent"},
            {"id": "task1", "type": "userTask"},
            {"id": "end1", "type": "endEvent"}
        ],
        "flows": [
            {"id": "flow1", "source": "task1", "target": "start1"},  # BŁĄD!
            {"id": "flow2", "source": "start1", "target": "task1"},
        ]
    }
    
    result = validator.validate_bpmn_compliance(process)
    issues = [i for i in result.issues if i.rule_code == "STRUCT_003"]
    print(f"   🧪 Test - Błędne połączenia: {len(issues)} błędów")
    
    connectivity_types = {}
    for issue in issues:
        error_type = "Start Event incoming" if "Start Event nie może" in issue.message else \
                    "End Event missing incoming" if "End Event musi mieć przepływ wchodzący" in issue.message else \
                    "Activity missing connection" if "nie ma przepływu" in issue.message else "Other"
        connectivity_types[error_type] = connectivity_types.get(error_type, 0) + 1
    
    for error_type, count in connectivity_types.items():
        print(f"      📊 {error_type}: {count}")

def test_struct_004(validator):
    """Test Gateway Flows"""
    print("   📝 Sprawdza: Poprawność przepływów Gateway")
    
    # Test: Exclusive Gateway z jednym wyjściem
    process = {
        "elements": [
            {"id": "start1", "type": "startEvent"},
            {"id": "gateway1", "type": "exclusiveGateway"},
            {"id": "task1", "type": "userTask"},
            {"id": "end1", "type": "endEvent"}
        ],
        "flows": [
            {"id": "flow1", "source": "start1", "target": "gateway1"},
            {"id": "flow2", "source": "gateway1", "target": "task1"},  # Tylko 1 wyjście!
        ]
    }
    
    result = validator.validate_bpmn_compliance(process)
    issues = [i for i in result.issues if i.rule_code == "STRUCT_004"]
    print(f"   🧪 Test - Gateway z jednym wyjściem: {len(issues)} błędów")
    if issues:
        print(f"      ❌ {issues[0].message}")

def test_struct_005(validator):
    """Test Pool Lane Structure"""
    print("   📝 Sprawdza: Przypisanie elementów do Pool/Lane")
    
    # Test: Element bez przypisanego uczestnika
    process = {
        "participants": [{"id": "pool1", "name": "Pool 1"}],
        "elements": [
            {"id": "start1", "type": "startEvent", "participant": "pool1"},
            {"id": "task1", "type": "userTask"},  # Brak participant!
        ],
        "flows": []
    }
    
    result = validator.validate_bpmn_compliance(process)
    issues = [i for i in result.issues if i.rule_code == "STRUCT_005"]
    print(f"   🧪 Test - Element bez Pool: {len(issues)} błędów")
    if issues:
        print(f"      ❌ {issues[0].message}")
        print(f"      🔧 Auto-fix: {issues[0].auto_fixable}")

def test_struct_006(validator):
    """Test Pool Process Continuity"""
    print("   📝 Sprawdza: Ciągłość procesów w Pool (Sequence Flow)")
    
    # Test: Message Flow wewnątrz Pool
    process = {
        "participants": [{"id": "pool1", "name": "Pool 1"}],
        "elements": [
            {"id": "start1", "type": "startEvent", "participant": "pool1"},
            {"id": "task1", "type": "userTask", "participant": "pool1"},
            {"id": "task2", "type": "userTask", "participant": "pool1"}
        ],
        "flows": [
            {"id": "flow1", "source": "start1", "target": "task1", "type": "sequence"},
            {"id": "flow2", "source": "task1", "target": "task2", "type": "message"}  # BŁĄD!
        ]
    }
    
    result = validator.validate_bpmn_compliance(process)
    issues = [i for i in result.issues if i.rule_code == "STRUCT_006"]
    print(f"   🧪 Test - Message Flow w Pool: {len(issues)} błędów")
    for issue in issues:
        print(f"      ❌ {issue.message}")
        print(f"      🔧 Auto-fix: {issue.auto_fixable}")

def test_struct_007(validator):
    """Test Pool Autonomy"""
    print("   📝 Sprawdza: Autonomię Pool (sposób uruchomienia)")
    
    # Test: Pool z aktywnościami ale bez Start Event ani Message Flow
    process = {
        "participants": [
            {"id": "pool1", "name": "Pool 1"},
            {"id": "pool2", "name": "Pool 2"}
        ],
        "elements": [
            {"id": "start1", "type": "startEvent", "participant": "pool1"},
            {"id": "task1", "type": "userTask", "participant": "pool1"},
            {"id": "task2", "type": "serviceTask", "participant": "pool2"},  # Pool2 bez sposobu uruchomienia!
            {"id": "end1", "type": "endEvent", "participant": "pool2"}
        ],
        "flows": [
            {"id": "flow1", "source": "start1", "target": "task1", "type": "sequence"},
            {"id": "flow2", "source": "task1", "target": "task2", "type": "message"},
            {"id": "flow3", "source": "task2", "target": "end1", "type": "sequence"}
        ]
    }
    
    result = validator.validate_bpmn_compliance(process)
    issues = [i for i in result.issues if i.rule_code == "STRUCT_007"]
    print(f"   🧪 Test - Pool bez uruchomienia: {len(issues)} problemów")
    for issue in issues:
        print(f"      ⚠️  Pool: {issue.element_id}")
        print(f"      ❌ {issue.message}")

def test_struct_008(validator):
    """Test Message Flow Validation"""
    print("   📝 Sprawdza: Poprawność Message Flow między Pool")
    
    # Test: Message Flow w tym samym Pool
    process = {
        "participants": [{"id": "pool1", "name": "Pool 1"}],
        "elements": [
            {"id": "task1", "type": "userTask", "participant": "pool1"},
            {"id": "task2", "type": "userTask", "participant": "pool1"}
        ],
        "flows": [
            {"id": "flow1", "source": "task1", "target": "task2", "type": "message"}  # Powinien być sequence!
        ]
    }
    
    result = validator.validate_bpmn_compliance(process)
    issues = [i for i in result.issues if i.rule_code == "STRUCT_008"]
    print(f"   🧪 Test - Message Flow w tym samym Pool: {len(issues)} błędów")
    if issues:
        print(f"      ❌ {issues[0].message}")
        print(f"      🔧 Auto-fix: {issues[0].auto_fixable}")

if __name__ == "__main__":
    analyze_structural_rules()