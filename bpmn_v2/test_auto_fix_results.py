#!/usr/bin/env python3
"""Test auto-fix results - sprawdza jakie konkretnie eventy zostały dodane"""

import json
from bpmn_improvement_engine import BPMNImprovementEngine
from bpmn_compliance_validator import BPMNComplianceValidator

# Load problematic BPMN (taki jak w naszym oryginalnym problemie)
problematic_bpmn = {
    "elements": [
        {"id": "task1", "name": "Logowanie", "type": "userTask", "participant": "Klient"},
        {"id": "task2", "name": "Autoryzacja", "type": "serviceTask", "participant": "Aplikacja mobilna banku"},
        {"id": "task3", "name": "Płatność", "type": "userTask", "participant": "Sprzedawca/Terminal"},
        {"id": "task4", "name": "BLIK", "type": "serviceTask", "participant": "System BLIK"},
        {"id": "task5", "name": "Clearing", "type": "serviceTask", "participant": "Clearing"},
        {"id": "task6", "name": "Core Banking", "type": "serviceTask", "participant": "System core banking"}
    ],
    "participants": [
        {"id": "Klient", "name": "Klient"},
        {"id": "Aplikacja mobilna banku", "name": "Aplikacja mobilna banku"},
        {"id": "Sprzedawca/Terminal", "name": "Sprzedawca/Terminal"},
        {"id": "System BLIK", "name": "System BLIK"},
        {"id": "Clearing", "name": "Clearing"},
        {"id": "System core banking", "name": "System core banking"}
    ],
    "flows": [
        {"id": "flow1", "source": "task1", "target": "task2"},
        {"id": "flow2", "source": "task2", "target": "task3"},
        {"id": "flow3", "source": "task3", "target": "task4"},
        {"id": "flow4", "source": "task4", "target": "task5"},
        {"id": "flow5", "source": "task5", "target": "task6"}
    ],
    "messageFlows": [
        {"id": "msg1", "source": "external", "target": "task1", "source_participant": "external", "target_participant": "Klient"},
        {"id": "msg2", "source": "task1", "target": "task2", "source_participant": "Klient", "target_participant": "Aplikacja mobilna banku"}
    ]
}

def test_auto_fix():
    print("🔧 SZCZEGÓŁOWY TEST AUTO-FIX RESULTS")
    print("=" * 80)
    
    # Initialize engine
    engine = BPMNImprovementEngine()
    
    # Przed naprawą
    print("📋 PRZED AUTO-FIX:")
    print(f"   Elementy: {len(problematic_bpmn['elements'])}")
    print(f"   Start Events: {len([e for e in problematic_bpmn['elements'] if e.get('type') == 'startEvent'])}")
    print(f"   Intermediate Catch Events: {len([e for e in problematic_bpmn['elements'] if e.get('type') == 'intermediateCatchEvent'])}")
    print(f"   End Events: {len([e for e in problematic_bpmn['elements'] if e.get('type') == 'endEvent'])}")
    print()
    
    # Uruchom improvement
    print("🔄 URUCHAMIANIE AUTO-FIX...")
    result = engine.improve_bpmn_process(problematic_bpmn.copy(), target_score=80, max_iterations=3)
    
    print(f"\n📊 RESULT STRUCTURE: {result.keys()}")
    
    if result.get('improved_process') is not None:
        improved_bpmn = result['improved_process']
        
        print("✅ PO AUTO-FIX:")
        print(f"   Elementy: {len(improved_bpmn['elements'])}")
        print(f"   Start Events: {len([e for e in improved_bpmn['elements'] if e.get('type') == 'startEvent'])}")
        print(f"   Intermediate Catch Events: {len([e for e in improved_bpmn['elements'] if e.get('type') == 'intermediateCatchEvent'])}")
        print(f"   End Events: {len([e for e in improved_bpmn['elements'] if e.get('type') == 'endEvent'])}")
        print()
        
        print("🎯 DODANE START/CATCH EVENTS:")
        start_events = [e for e in improved_bpmn['elements'] if e.get('type') in ['startEvent', 'intermediateCatchEvent']]
        for event in start_events:
            print(f"   • {event.get('type')} '{event.get('name')}' w Pool '{event.get('participant')}'")
        
        print("\n🏁 DODANE END EVENTS:")
        end_events = [e for e in improved_bpmn['elements'] if e.get('type') == 'endEvent']
        for event in end_events:
            print(f"   • {event.get('type')} '{event.get('name')}' w Pool '{event.get('participant')}'")
            
        print("\n📊 PORÓWNANIE Z NASZYMI RĘCZNYMI NAPRAWAMI:")
        print(f"   Nasze ręczne: 5 Intermediate Catch Events + 8 End Events = 13 events")
        print(f"   Auto-fix:     {len(start_events)} Start/Catch Events + {len(end_events)} End Events = {len(start_events) + len(end_events)} events")
        
        # Sprawdź Message Flows
        print("\n💬 MESSAGE FLOWS:")
        if 'messageFlows' in improved_bpmn:
            for mf in improved_bpmn['messageFlows']:
                print(f"   • {mf.get('id')}: {mf.get('source')} -> {mf.get('target')}")
        
        # Sprawdź jakość końcową
        print(f"\n📈 Jakość końcowa: {result.get('final_score', 'unknown')}")
        
        # Zapisz wynik dla dalszej analizy
        with open('auto_fix_result.json', 'w', encoding='utf-8') as f:
            json.dump(improved_bpmn, f, indent=2, ensure_ascii=False)
        print("\n💾 Wynik zapisany do: auto_fix_result.json")
        
    else:
        print(f"❌ Auto-fix failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_auto_fix()