#!/usr/bin/env python3
"""
Test kompletności poprawek multi-pool BPMN validation rules
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bpmn_v2'))

from bpmn_compliance_validator import BPMNComplianceValidator, BPMNSeverity

def test_corrected_multipool_rules():
    """Test wszystkich naprawionych reguł"""
    
    validator = BPMNComplianceValidator()
    
    print("🎯 TEST KOMPLETNOŚCI POPRAWEK MULTI-POOL BPMN")
    print("=" * 60)
    
    # Test przypadek: Poprawnie skonfigurowany proces multi-pool
    correct_multipool_process = {
        "process_name": "Correct Multi-Pool Process",
        "participants": [
            {"id": "customer", "name": "Customer", "type": "human"},
            {"id": "bank_system", "name": "Bank System", "type": "system"},
            {"id": "analyst", "name": "Credit Analyst", "type": "human"}
        ],
        "elements": [
            # Customer pool - complete flow
            {"id": "start_customer", "name": "Customer starts", "type": "startEvent", "participant": "customer"},
            {"id": "fill_form", "name": "Fill application", "type": "userTask", "participant": "customer", "task_type": "user"},
            {"id": "send_app", "name": "Send application", "type": "intermediateMessageThrowEvent", "participant": "customer"},
            {"id": "receive_decision", "name": "Receive decision", "type": "intermediateCatchEvent", "participant": "customer", "event_type": "message"},
            {"id": "end_customer", "name": "Customer ends", "type": "endEvent", "participant": "customer"},
            
            # Bank system pool
            {"id": "receive_app", "name": "Receive application", "type": "startEvent", "participant": "bank_system", "event_type": "message"},
            {"id": "verify_data", "name": "Verify data", "type": "serviceTask", "participant": "bank_system", "task_type": "service"},
            {"id": "decision_gate", "name": "Decision gate", "type": "exclusiveGateway", "participant": "bank_system"},
            {"id": "approve_task", "name": "Approve", "type": "serviceTask", "participant": "bank_system", "task_type": "service"},
            {"id": "reject_task", "name": "Reject", "type": "serviceTask", "participant": "bank_system", "task_type": "service"},
            {"id": "notify_customer", "name": "Notify customer", "type": "intermediateMessageThrowEvent", "participant": "bank_system"},
            {"id": "end_bank", "name": "Bank process ends", "type": "endEvent", "participant": "bank_system"},
            
            # Analyst pool
            {"id": "start_analysis", "name": "Analysis requested", "type": "startEvent", "participant": "analyst", "event_type": "message"},
            {"id": "analyze_credit", "name": "Analyze creditworthiness", "type": "userTask", "participant": "analyst", "task_type": "user"},
            {"id": "send_opinion", "name": "Send opinion", "type": "intermediateMessageThrowEvent", "participant": "analyst"},
            {"id": "end_analysis", "name": "Analysis complete", "type": "endEvent", "participant": "analyst"}
        ],
        "flows": [
            # Customer pool sequence flows
            {"id": "seq1", "source": "start_customer", "target": "fill_form", "type": "sequence"},
            {"id": "seq2", "source": "fill_form", "target": "send_app", "type": "sequence"},
            {"id": "seq3", "source": "receive_decision", "target": "end_customer", "type": "sequence"},
            
            # Bank system sequence flows
            {"id": "seq4", "source": "receive_app", "target": "verify_data", "type": "sequence"},
            {"id": "seq5", "source": "verify_data", "target": "decision_gate", "type": "sequence"},
            {"id": "seq6", "source": "decision_gate", "target": "approve_task", "type": "sequence", "condition": "approved"},
            {"id": "seq7", "source": "decision_gate", "target": "reject_task", "type": "sequence", "condition": "rejected"},
            {"id": "seq8", "source": "approve_task", "target": "notify_customer", "type": "sequence"},
            {"id": "seq9", "source": "reject_task", "target": "notify_customer", "type": "sequence"},
            {"id": "seq10", "source": "notify_customer", "target": "end_bank", "type": "sequence"},
            
            # Analyst pool sequence flows
            {"id": "seq11", "source": "start_analysis", "target": "analyze_credit", "type": "sequence"},
            {"id": "seq12", "source": "analyze_credit", "target": "send_opinion", "type": "sequence"},
            {"id": "seq13", "source": "send_opinion", "target": "end_analysis", "type": "sequence"},
            
            # Message flows between pools (CORRECT usage)
            {"id": "msg1", "source": "send_app", "target": "receive_app", "type": "message"},
            {"id": "msg2", "source": "verify_data", "target": "start_analysis", "type": "message"},
            {"id": "msg3", "source": "send_opinion", "target": "decision_gate", "type": "message"},
            {"id": "msg4", "source": "notify_customer", "target": "receive_decision", "type": "message"}
        ]
    }
    
    print("\n📋 Test Case: Poprawnie skonfigurowany proces multi-pool")
    print(f"   Participants: {len(correct_multipool_process['participants'])}")
    print(f"   Elements: {len(correct_multipool_process['elements'])}")
    print(f"   Flows: {len(correct_multipool_process['flows'])}")
    
    # Run validation
    report = validator.validate_bpmn_compliance(correct_multipool_process)
    
    print(f"\n📊 Wyniki walidacji:")
    print(f"   Overall Score: {report.overall_score}")
    print(f"   Compliance Level: {report.compliance_level}")
    print(f"   Total Issues: {len(report.issues)}")
    
    # Analyze issues by severity
    issues_by_severity = {}
    for issue in report.issues:
        severity = issue.severity.value
        if severity not in issues_by_severity:
            issues_by_severity[severity] = []
        issues_by_severity[severity].append(issue)
    
    print("\n🚨 Issues by severity:")
    for severity, issues in issues_by_severity.items():
        severity_icons = {
            'critical': '🔴',
            'major': '🟡',
            'minor': '🔵', 
            'warning': '⚠️'
        }
        print(f"   {severity_icons.get(severity, '❓')} {severity.upper()}: {len(issues)}")
        for issue in issues[:3]:  # Show first 3
            print(f"      • {issue.element_id}: {issue.message}")
        if len(issues) > 3:
            print(f"      ... and {len(issues) - 3} more")
    
    # Summary of rule coverage
    print("\n🔍 POKRYCIE REGUŁ:")
    tested_rules = set(issue.rule_code for issue in report.issues)
    all_rules = set(validator.rules.keys())
    
    print(f"   Aktywowane reguły: {len(tested_rules)}/{len(all_rules)}")
    print(f"   Nieaktywne reguły: {all_rules - tested_rules}")
    
    # Check specific multi-pool rules
    multipool_rules = [
        'STRUCT_001', 'STRUCT_002', 'STRUCT_003', 'STRUCT_004', 
        'STRUCT_005', 'STRUCT_006', 'STRUCT_007', 'STRUCT_008'
    ]
    
    print("\n✅ STATUS POPRAWEK MULTI-POOL:")
    for rule in multipool_rules:
        rule_issues = [i for i in report.issues if i.rule_code == rule]
        if rule_issues:
            if any(i.severity in [BPMNSeverity.CRITICAL, BPMNSeverity.MAJOR] for i in rule_issues):
                print(f"   {rule}: ❌ Ma poważne problemy ({len(rule_issues)} issues)")
            else:
                print(f"   {rule}: ⚠️ Ma drobne problemy ({len(rule_issues)} issues)")
        else:
            print(f"   {rule}: ✅ Brak problemów")
    
    return report

def test_problematic_cases():
    """Test specyficznych problemów które miały być naprawione"""
    
    validator = BPMNComplianceValidator()
    
    print("\n\n🧪 TEST SPECYFICZNYCH PROBLEMÓW")
    print("=" * 60)
    
    # Problem case 1: Gateway wysyłający do innego Pool 
    gateway_problem = {
        "process_name": "Gateway Cross-Pool Problem",
        "participants": [
            {"id": "pool1", "name": "Pool 1", "type": "human"},
            {"id": "pool2", "name": "Pool 2", "type": "system"}
        ],
        "elements": [
            {"id": "start1", "name": "Start", "type": "startEvent", "participant": "pool1"},
            {"id": "gateway1", "name": "Decision", "type": "exclusiveGateway", "participant": "pool1"},
            {"id": "task1", "name": "Task in Pool 1", "type": "userTask", "participant": "pool1", "task_type": "user"},
            {"id": "task2", "name": "Task in Pool 2", "type": "serviceTask", "participant": "pool2", "task_type": "service"},
            {"id": "end1", "name": "End", "type": "endEvent", "participant": "pool1"}
        ],
        "flows": [
            {"id": "seq1", "source": "start1", "target": "gateway1", "type": "sequence"},
            {"id": "seq2", "source": "gateway1", "target": "task1", "type": "sequence"},
            # PROBLEM: Gateway wysyłający sequence flow do innego Pool
            {"id": "seq3", "source": "gateway1", "target": "task2", "type": "sequence"},
            {"id": "seq4", "source": "task1", "target": "end1", "type": "sequence"}
        ]
    }
    
    print("\n📋 Problem Case 1: Gateway cross-pool sequence flow")
    report1 = validator.validate_bpmn_compliance(gateway_problem)
    gateway_issues = [i for i in report1.issues if i.rule_code == 'STRUCT_004']
    print(f"   STRUCT_004 issues: {len(gateway_issues)}")
    for issue in gateway_issues:
        if "innego Pool" in issue.message:
            print(f"   ✅ Wykryto problem: {issue.message}")
        
    # Problem case 2: Message Flow wewnątrz Pool
    messageflow_problem = {
        "process_name": "Message Flow Internal Problem",
        "participants": [
            {"id": "pool1", "name": "Pool 1", "type": "human"}
        ],
        "elements": [
            {"id": "start1", "name": "Start", "type": "startEvent", "participant": "pool1"},
            {"id": "task1", "name": "Task 1", "type": "userTask", "participant": "pool1", "task_type": "user"},
            {"id": "task2", "name": "Task 2", "type": "userTask", "participant": "pool1", "task_type": "user"},
            {"id": "end1", "name": "End", "type": "endEvent", "participant": "pool1"}
        ],
        "flows": [
            {"id": "seq1", "source": "start1", "target": "task1", "type": "sequence"},
            # PROBLEM: Message flow wewnątrz tego samego Pool (single-pool - to ma być OK)
            {"id": "msg1", "source": "task1", "target": "task2", "type": "message"}, 
            {"id": "seq2", "source": "task2", "target": "end1", "type": "sequence"}
        ]
    }
    
    print("\n📋 Problem Case 2: Message flow internal (single-pool)")
    report2 = validator.validate_bpmn_compliance(messageflow_problem)
    message_issues = [i for i in report2.issues if i.rule_code == 'STRUCT_008']
    print(f"   STRUCT_008 issues: {len(message_issues)}")
    if not message_issues:
        print("   ✅ Single-pool Message Flow dozwolony (poprawnie)")
    else:
        print(f"   ❌ Single-pool Message Flow blokowany (błąd): {message_issues[0].message}")

if __name__ == "__main__":
    try:
        print("🚀 Starting Multi-Pool Rules Completeness Test...")
        
        # Test main corrected multi-pool process
        report = test_corrected_multipool_rules()
        
        # Test specific edge cases
        test_problematic_cases()
        
        print(f"\n✅ Test completed")
        print(f"📊 Final compliance score: {report.overall_score}")
        
        # Overall assessment
        if report.overall_score >= 80:
            print("🎉 Multi-pool BPMN validation rules working correctly!")
        elif report.overall_score >= 60:
            print("⚠️ Multi-pool validation mostly working with minor issues")
        else:
            print("❌ Multi-pool validation needs more work")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()