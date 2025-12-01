"""
Comprehensive BPMN Optimization Test
Test kompleksowej optymalizacji procesu BPMN z wieloma problemami

Autor: AI Assistant
Data: 2025-11-29
"""

import json
import sys
import os

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server_simple import SimpleMCPServer
from enhanced_auto_fixes import apply_enhanced_auto_fixes

def create_problematic_bpmn_process():
    """Tworzy proces BPMN z wieloma problemami do naprawy"""
    return {
        "process_name": "Problematyczny Proces Biznesowy",
        "description": "Proces z wieloma błędami BPMN do testowania optymalizacji",
        "participants": [
            {"id": "klient", "name": "Klient", "type": "human"},
            {"id": "pracownik", "name": "Pracownik", "type": "human"},
            {"id": "system", "name": "System IT", "type": "system"}
        ],
        "elements": [
            # Pool 1: Klient - PROBLEMY: brak Start/End Event
            {"id": "task_1", "name": "", "type": "userTask", "participant": "klient"},
            {"id": "task_2", "name": "Wypełnij formularz", "type": "task", "participant": "klient"},  # Błędny typ
            
            # Pool 2: Pracownik - PROBLEMY: Gateway bez wystarczających przepływów
            {"id": "start_2", "name": "Start", "type": "startEvent", "participant": "pracownik"},
            {"id": "gateway_1", "name": "", "type": "exclusiveGateway", "participant": "pracownik"},
            {"id": "task_3", "name": "Sprawdź wniosek", "type": "userTask", "participant": "pracownik"},
            # Brak End Event
            
            # Pool 3: System - PROBLEMY: Message Flow problemy
            {"id": "start_3", "name": "Start", "type": "startEvent", "participant": "system"},
            {"id": "task_4", "name": "Przetwórz dane", "type": "serviceTask", "participant": "system"},
            {"id": "end_3", "name": "End", "type": "endEvent", "participant": "system"}
        ],
        "flows": [
            # PROBLEMY: Sequence flows między Pool (powinny być Message flows)
            {"id": "flow_1", "source": "task_1", "target": "start_2", "type": "sequence"},
            {"id": "flow_2", "source": "task_2", "target": "task_3", "type": "sequence"},
            
            # Prawidłowe flows
            {"id": "flow_3", "source": "start_2", "target": "gateway_1", "type": "sequence"},
            {"id": "flow_4", "source": "gateway_1", "target": "task_3", "type": "sequence"},  # Gateway ma tylko 1 outgoing
            {"id": "flow_5", "source": "start_3", "target": "task_4", "type": "sequence"},
            {"id": "flow_6", "source": "task_4", "target": "end_3", "type": "sequence"},
            
            # Message flow z problemami
            {"id": "msg_flow_1", "source": "end_3", "target": "task_1", "type": "message"}  # End Event bez message type
        ]
    }

def test_comprehensive_optimization():
    """Test kompleksowej optymalizacji procesu BPMN"""
    print("🧪 COMPREHENSIVE BPMN OPTIMIZATION TEST")
    print("=" * 60)
    
    # Initialize server
    server = SimpleMCPServer()
    
    # Create problematic process
    problematic_process = create_problematic_bpmn_process()
    
    print("\n📋 INITIAL PROCESS ANALYSIS")
    print("-" * 40)
    print(f"Elements: {len(problematic_process['elements'])}")
    print(f"Participants: {len(problematic_process['participants'])}")
    print(f"Flows: {len(problematic_process['flows'])}")
    
    # Step 1: Initial verification
    print("\n🔍 STEP 1: INITIAL VERIFICATION")
    print("-" * 40)
    initial_verification = server.verify_bpmn_process(problematic_process)
    print(f"✓ Initial quality: {initial_verification['overall_quality']:.3f}")
    print(f"✓ BPMN compliance: {initial_verification['bpmn_compliance']['score']:.1f}")
    print(f"✓ Compliance level: {initial_verification['bpmn_compliance']['level']}")
    print(f"✓ Critical issues: {len([i for i in initial_verification['bpmn_compliance']['issues'] if i['severity'] == 'critical'])}")
    print(f"✓ Total issues: {len(initial_verification['bpmn_compliance']['issues'])}")
    
    # Show specific issues
    print("\n📝 Critical Issues Found:")
    for issue in initial_verification['bpmn_compliance']['issues']:
        if issue['severity'] == 'critical':
            print(f"   ❌ {issue['rule_code']}: {issue['message']}")
    
    # Step 2: Intelligence-based optimization
    print("\n🧠 STEP 2: INTELLIGENCE-BASED OPTIMIZATION")
    print("-" * 40)
    context_hints = {
        'domain': 'business_process',
        'time_constraint': 'normal',
        'quality_requirement': 'high'
    }
    
    intelligence_result = server.intelligent_bpmn_optimization(
        problematic_process, 
        context_hints=context_hints
    )
    
    print(f"✓ Intelligence enabled: {intelligence_result.get('intelligence_enabled')}")
    print(f"✓ Strategy used: {intelligence_result.get('insights', {}).get('strategy_used', 'unknown')}")
    print(f"✓ Confidence score: {intelligence_result.get('insights', {}).get('confidence_score', 0):.3f}")
    print(f"✓ Applied optimizations: {len(intelligence_result.get('applied_optimizations', []))}")
    print(f"✓ Processing time: {intelligence_result.get('processing_time', 0):.3f}s")
    
    # Show applied optimizations
    if intelligence_result.get('applied_optimizations'):
        print("\n🔧 Applied Optimizations:")
        for opt in intelligence_result['applied_optimizations']:
            print(f"   ✓ {opt.get('type', 'unknown')}: {opt.get('description', 'N/A')}")
    
    # Step 3: Traditional iterative improvement
    print("\n🔄 STEP 3: ITERATIVE IMPROVEMENT")
    print("-" * 40)
    improvement_result = server.improve_bpmn_process(
        problematic_process, 
        target_score=85.0, 
        max_iterations=5
    )
    
    print(f"✓ Success: {improvement_result['success']}")
    print(f"✓ Applied changes: {len(improvement_result['changes_made'])}")
    print(f"✓ Message: {improvement_result['message']}")
    
    # Show improvement details
    if 'improvement_history' in improvement_result:
        print(f"✓ Improvement iterations: {len(improvement_result['improvement_history'])}")
        for i, iteration in enumerate(improvement_result['improvement_history'], 1):
            print(f"   Iteration {i}: {iteration.get('improvements_count', 0)} improvements")
    
    # Step 4: Enhanced Auto-Fixes
    print("\n🔧 STEP 4: ENHANCED AUTO-FIXES")
    print("-" * 40)
    
    enhanced_process = improvement_result['improved_process'].copy()
    enhanced_fixes = apply_enhanced_auto_fixes(enhanced_process)
    print(f"✓ Enhanced fixes applied: {enhanced_fixes}")
    
    # Apply additional round of fixes if needed
    if enhanced_fixes > 0:
        print("🔧 Applying additional round of enhanced fixes...")
        additional_fixes = apply_enhanced_auto_fixes(enhanced_process)
        enhanced_fixes += additional_fixes
        print(f"✓ Additional fixes: {additional_fixes}")
    
    # Step 5: Final verification
    print("\n✅ STEP 5: FINAL VERIFICATION")
    print("-" * 40)
    
    final_verification = server.verify_bpmn_process(enhanced_process)
    
    print(f"✓ Final quality: {final_verification['overall_quality']:.3f}")
    print(f"✓ Final BPMN compliance: {final_verification['bpmn_compliance']['score']:.1f}")
    print(f"✓ Final compliance level: {final_verification['bpmn_compliance']['level']}")
    print(f"✓ Remaining critical issues: {len([i for i in final_verification['bpmn_compliance']['issues'] if i['severity'] == 'critical'])}")
    print(f"✓ Total remaining issues: {len(final_verification['bpmn_compliance']['issues'])}")
    
    # Step 6: Quality improvement analysis
    print("\n📊 STEP 6: IMPROVEMENT ANALYSIS")
    print("-" * 40)
    
    quality_improvement = final_verification['overall_quality'] - initial_verification['overall_quality']
    compliance_improvement = final_verification['bpmn_compliance']['score'] - initial_verification['bpmn_compliance']['score']
    issues_resolved = len(initial_verification['bpmn_compliance']['issues']) - len(final_verification['bpmn_compliance']['issues'])
    
    print(f"✓ Quality improvement: {quality_improvement:+.3f} ({quality_improvement/initial_verification['overall_quality']*100:+.1f}%)")
    print(f"✓ Compliance improvement: {compliance_improvement:+.1f}")
    print(f"✓ Issues resolved: {issues_resolved}")
    print(f"✓ Enhanced auto-fixes: {enhanced_fixes}")
    
    # Step 7: Structural analysis
    print("\n🏗️ STEP 7: STRUCTURAL ANALYSIS")
    print("-" * 40)
    
    initial_elements = len(problematic_process['elements'])
    final_elements = len(enhanced_process['elements'])
    initial_flows = len(problematic_process['flows'])
    final_flows = len(enhanced_process['flows'])
    
    print(f"✓ Elements: {initial_elements} → {final_elements} ({final_elements-initial_elements:+d})")
    print(f"✓ Flows: {initial_flows} → {final_flows} ({final_flows-initial_flows:+d})")
    
    # Check if all participants have Start and End events
    participants = enhanced_process.get('participants', [])
    elements = enhanced_process.get('elements', [])
    
    print(f"\n👥 Participant Completeness Check:")
    for participant in participants:
        pool_id = participant['id']
        pool_elements = [e for e in elements if e.get('participant') == pool_id]
        start_events = [e for e in pool_elements if e.get('type') == 'startEvent']
        end_events = [e for e in pool_elements if e.get('type') == 'endEvent']
        
        status = "✅" if start_events and end_events else "❌"
        print(f"   {status} {participant['name']}: Start({len(start_events)}) End({len(end_events)})")
    
    # Step 8: BPMN 2.0 Compliance Summary
    print("\n📋 STEP 8: BPMN 2.0 COMPLIANCE SUMMARY")
    print("-" * 40)
    
    remaining_issues = final_verification['bpmn_compliance']['issues']
    issues_by_severity = {'critical': 0, 'major': 0, 'minor': 0}
    
    for issue in remaining_issues:
        severity = issue.get('severity', 'unknown')
        if severity in issues_by_severity:
            issues_by_severity[severity] += 1
    
    print(f"✓ Critical issues: {issues_by_severity['critical']}")
    print(f"✓ Major issues: {issues_by_severity['major']}")
    print(f"✓ Minor issues: {issues_by_severity['minor']}")
    
    # Show remaining critical issues
    if issues_by_severity['critical'] > 0:
        print("\n⚠️ Remaining Critical Issues:")
        for issue in remaining_issues:
            if issue.get('severity') == 'critical':
                print(f"   ❌ {issue['rule_code']}: {issue['message']}")
    
    # Step 9: Success evaluation
    print("\n🎯 STEP 9: SUCCESS EVALUATION")
    print("-" * 40)
    
    success_criteria = {
        'quality_improved': quality_improvement > 0.1,
        'compliance_good': final_verification['bpmn_compliance']['score'] >= 70,
        'no_critical_issues': issues_by_severity['critical'] == 0,
        'structural_integrity': final_elements >= initial_elements and final_flows >= initial_flows
    }
    
    passed_criteria = sum(success_criteria.values())
    total_criteria = len(success_criteria)
    
    print(f"✓ Quality improved (>0.1): {'✅' if success_criteria['quality_improved'] else '❌'}")
    print(f"✓ Good compliance (≥70): {'✅' if success_criteria['compliance_good'] else '❌'}")
    print(f"✓ No critical issues: {'✅' if success_criteria['no_critical_issues'] else '❌'}")
    print(f"✓ Structural integrity: {'✅' if success_criteria['structural_integrity'] else '❌'}")
    
    overall_success = passed_criteria >= total_criteria * 0.75  # 75% criteria must pass
    
    print(f"\n🏆 OVERALL SUCCESS: {'✅ PASSED' if overall_success else '❌ FAILED'} ({passed_criteria}/{total_criteria})")
    
    return {
        'overall_success': overall_success,
        'initial_quality': initial_verification['overall_quality'],
        'final_quality': final_verification['overall_quality'],
        'quality_improvement': quality_improvement,
        'compliance_improvement': compliance_improvement,
        'issues_resolved': issues_resolved,
        'criteria_passed': f"{passed_criteria}/{total_criteria}",
        'enhanced_fixes_applied': enhanced_fixes,
        'final_process': enhanced_process
    }

if __name__ == "__main__":
    results = test_comprehensive_optimization()
    
    print("\n" + "="*60)
    print("🎊 TEST COMPLETION SUMMARY")
    print("="*60)
    print(f"Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}")
    print(f"Quality: {results['initial_quality']:.3f} → {results['final_quality']:.3f} ({results['quality_improvement']:+.3f})")
    print(f"Compliance improvement: {results['compliance_improvement']:+.1f}")
    print(f"Issues resolved: {results['issues_resolved']}")
    print(f"Enhanced auto-fixes: {results['enhanced_fixes_applied']}")
    print(f"Success criteria: {results['criteria_passed']}")