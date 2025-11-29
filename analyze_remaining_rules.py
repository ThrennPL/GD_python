#!/usr/bin/env python3
"""
Analiza pozostałych reguł BPMN pod kątem zgodności z multi-pool
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bpmn_v2'))

from bpmn_compliance_validator import BPMNComplianceValidator, BPMNSeverity

def analyze_multi_pool_rules():
    """Analizuj reguły pod kątem zgodności z multi-pool BPMN"""
    
    validator = BPMNComplianceValidator()
    
    print("🔍 ANALIZA REGUŁ POD KĄTEM MULTI-POOL BPMN")
    print("=" * 60)
    
    # Test process multi-pool
    test_multipool_process = {
        "process_name": "Test Multi-Pool Process",
        "participants": [
            {"id": "pool1", "name": "Pool 1", "type": "human"},
            {"id": "pool2", "name": "Pool 2", "type": "system"}
        ],
        "elements": [
            # Pool 1 elements
            {"id": "start1", "name": "Start 1", "type": "startEvent", "participant": "pool1"},
            {"id": "task1", "name": "Task 1", "type": "userTask", "participant": "pool1", "task_type": "user"},
            {"id": "end1", "name": "End 1", "type": "endEvent", "participant": "pool1"},
            
            # Pool 2 elements  
            {"id": "start2", "name": "Start 2", "type": "startEvent", "participant": "pool2", "event_type": "message"},
            {"id": "task2", "name": "Task 2", "type": "serviceTask", "participant": "pool2", "task_type": "service"},
            {"id": "end2", "name": "End 2", "type": "endEvent", "participant": "pool2"},
            
            # Unassigned element (testing STRUCT_005)
            {"id": "orphan", "name": "Orphan Task", "type": "userTask", "task_type": "user"},
            
            # Gateway for testing STRUCT_004
            {"id": "gateway1", "name": "Decision", "type": "exclusiveGateway", "participant": "pool1"}
        ],
        "flows": [
            # Pool 1 sequence flows
            {"id": "seq1", "source": "start1", "target": "task1", "type": "sequence"},
            {"id": "seq2", "source": "task1", "target": "gateway1", "type": "sequence"}, 
            {"id": "seq3", "source": "gateway1", "target": "end1", "type": "sequence"},
            
            # Pool 2 sequence flows
            {"id": "seq4", "source": "start2", "target": "task2", "type": "sequence"},
            {"id": "seq5", "source": "task2", "target": "end2", "type": "sequence"},
            
            # Message flows between pools (good)
            {"id": "msg1", "source": "task1", "target": "start2", "type": "message"},
            
            # Problem: Message flow inside same pool (testing STRUCT_006, STRUCT_008)
            {"id": "msg_bad", "source": "start1", "target": "task1", "type": "message"},
            
            # Problem: No outgoing from gateway (testing STRUCT_004)
            # Gateway already has only one outgoing - this is a problem
        ]
    }
    
    print("\n📋 Test Case: Multi-pool process z różnymi problemami")
    print(f"   Participants: {len(test_multipool_process['participants'])}")
    print(f"   Elements: {len(test_multipool_process['elements'])}")  
    print(f"   Flows: {len(test_multipool_process['flows'])}")
    
    # Run validation
    report = validator.validate_bpmn_compliance(test_multipool_process)
    
    print(f"\n📊 Wyniki walidacji:")
    print(f"   Overall Score: {report.overall_score}")
    print(f"   Compliance Level: {report.compliance_level}")
    print(f"   Total Issues: {len(report.issues)}")
    
    print("\n🚨 Issues by rule:")
    rule_counts = {}
    
    for issue in report.issues:
        rule = issue.rule_code
        if rule not in rule_counts:
            rule_counts[rule] = []
        rule_counts[rule].append(issue)
    
    for rule_code, issues in sorted(rule_counts.items()):
        print(f"\n   {rule_code}: {len(issues)} issues")
        for issue in issues:
            severity_icon = {
                BPMNSeverity.CRITICAL: "🔴",
                BPMNSeverity.MAJOR: "🟡", 
                BPMNSeverity.MINOR: "🔵",
                BPMNSeverity.WARNING: "⚠️"
            }
            print(f"      {severity_icon.get(issue.severity, '❓')} {issue.element_id}: {issue.message}")
    
    print("\n" + "=" * 60)
    
    # Analyze which rules need multi-pool fixes
    print("\n🔧 ANALIZA REGUŁ WYMAGAJĄCYCH POPRAWEK MULTI-POOL:")
    
    rules_analysis = {
        "STRUCT_001": "✅ NAPRAWIONA - per-pool Start Event validation",
        "STRUCT_002": "✅ NAPRAWIONA - per-pool End Event validation", 
        "STRUCT_003": "✅ NAPRAWIONA - Message Flow vs Sequence Flow handling",
        "STRUCT_004": "⚠️ WYMAGA PRZEGLĄDU - Gateway flow validation",
        "STRUCT_005": "⚠️ WYMAGA PRZEGLĄDU - Pool structure validation", 
        "STRUCT_006": "✅ IMPLEMENTOWANA - Pool continuity checks",
        "STRUCT_007": "✅ IMPLEMENTOWANA - Pool autonomy checks",
        "STRUCT_008": "⚠️ WYMAGA PRZEGLĄDU - Message Flow validation",
        "SEM_001": "❓ DO ANALIZY - Element naming per pool",
        "SEM_002": "❓ DO ANALIZY - Gateway conditions per pool", 
        "SEM_003": "❓ DO ANALIZY - Message Flow semantic validation",
        "SEM_004": "❓ DO ANALIZY - Activity types per pool",
        "SYNT_001": "❓ DO ANALIZY - Unique IDs across pools",
        "SYNT_002": "❓ DO ANALIZY - Required attributes per pool",
        "SYNT_003": "❓ DO ANALIZY - Flow references across pools",
        "STYLE_001": "❓ DO ANALIZY - Naming conventions per pool",
        "STYLE_002": "❓ DO ANALIZY - Process complexity per pool",
        "STYLE_003": "❓ DO ANALIZY - Participant distribution"
    }
    
    for rule_code, status in rules_analysis.items():
        print(f"   {rule_code}: {status}")
    
    return report, rule_counts

def detailed_rule_analysis():
    """Szczegółowa analiza konkretnych reguł"""
    
    print("\n\n🔎 SZCZEGÓŁOWA ANALIZA WYBRANYCH REGUŁ")
    print("=" * 60)
    
    # Test cases for specific problematic rules
    test_cases = {
        "STRUCT_004_problem": {
            "process_name": "Gateway Flow Test",
            "participants": [
                {"id": "pool1", "name": "Pool 1", "type": "human"},
                {"id": "pool2", "name": "Pool 2", "type": "system"}
            ],
            "elements": [
                {"id": "start1", "name": "Start", "type": "startEvent", "participant": "pool1"},
                {"id": "gateway1", "name": "Decision", "type": "exclusiveGateway", "participant": "pool1"},
                {"id": "task1", "name": "Path A", "type": "userTask", "participant": "pool1", "task_type": "user"},
                {"id": "task2", "name": "Path B", "type": "userTask", "participant": "pool2", "task_type": "user"},
                {"id": "end1", "name": "End", "type": "endEvent", "participant": "pool1"}
            ],
            "flows": [
                {"id": "seq1", "source": "start1", "target": "gateway1", "type": "sequence"},
                {"id": "seq2", "source": "gateway1", "target": "task1", "type": "sequence"},
                # Problem: Gateway rozgałęziający do innego Pool przez Sequence Flow
                {"id": "seq3", "source": "gateway1", "target": "task2", "type": "sequence"},
                {"id": "msg1", "source": "task2", "target": "end1", "type": "message"}
            ]
        },
        
        "STRUCT_008_problem": {
            "process_name": "Message Flow Test", 
            "participants": [
                {"id": "pool1", "name": "Pool 1", "type": "human"},
                {"id": "pool2", "name": "Pool 2", "type": "system"}
            ],
            "elements": [
                {"id": "start1", "name": "Start 1", "type": "startEvent", "participant": "pool1"},
                {"id": "task1", "name": "Task 1", "type": "userTask", "participant": "pool1", "task_type": "user"},
                {"id": "task2", "name": "Task 2", "type": "userTask", "participant": "pool1", "task_type": "user"},
                {"id": "task3", "name": "Task 3", "type": "serviceTask", "participant": "pool2", "task_type": "service"},
                {"id": "end2", "name": "End 2", "type": "endEvent", "participant": "pool2"}
            ],
            "flows": [
                {"id": "seq1", "source": "start1", "target": "task1", "type": "sequence"},
                # Problem: Message Flow wewnątrz tego samego Pool
                {"id": "msg_bad", "source": "task1", "target": "task2", "type": "message"},
                # Good: Message Flow między Pool
                {"id": "msg_good", "source": "task2", "target": "task3", "type": "message"},
                {"id": "seq2", "source": "task3", "target": "end2", "type": "sequence"}
            ]
        }
    }
    
    validator = BPMNComplianceValidator()
    
    for test_name, test_case in test_cases.items():
        print(f"\n📋 Test Case: {test_name}")
        print(f"   {test_case['process_name']}")
        
        report = validator.validate_bpmn_compliance(test_case)
        
        relevant_issues = []
        rule_filter = test_name.split('_')[0] + '_' + test_name.split('_')[1]
        
        for issue in report.issues:
            if issue.rule_code.startswith(rule_filter):
                relevant_issues.append(issue)
        
        print(f"   Issues for {rule_filter}: {len(relevant_issues)}")
        for issue in relevant_issues:
            print(f"      🚨 {issue.element_id}: {issue.message}")
            print(f"         💡 {issue.suggestion}")

if __name__ == "__main__":
    try:
        print("🚀 Starting BPMN Multi-Pool Rules Analysis...")
        
        # Basic analysis
        report, rule_counts = analyze_multi_pool_rules()
        
        # Detailed analysis
        detailed_rule_analysis()
        
        print(f"\n✅ Analysis completed")
        print(f"📊 Found rules requiring attention")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()