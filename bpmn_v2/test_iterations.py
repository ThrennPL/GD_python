#!/usr/bin/env python3
"""Test iteracji - sprawdza czy system wykonuje więcej niż jedną iterację"""

from bpmn_improvement_engine import BPMNImprovementEngine

def test_iterations():
    print("🔄 TEST WIELOKROTNYCH ITERACJI")
    print("=" * 60)
    
    # Bardzo prosty BPMN z wieloma problemami
    simple_bpmn = {
        "elements": [
            {"id": "task1", "name": "Zadanie 1", "participant": "Pool1"},  # Brak typu
            {"id": "task2", "name": "Zadanie 2", "participant": "Pool2"}   # Brak typu
        ],
        "participants": [
            {"id": "Pool1", "name": "Pool 1"},
            {"id": "Pool2", "name": "Pool 2"}
        ],
        "flows": []
    }
    
    # Initialize engine
    engine = BPMNImprovementEngine()
    
    print("📋 PROBLEMY W SIMPLE BPMN:")
    print("   - Brak Start Events")
    print("   - Brak End Events") 
    print("   - Brak typów zadań")
    print("   - Brak flows między elementami")
    print()
    
    # Test z target_score=90 i max_iterations=10
    print("🎯 Uruchamianie z target_score=90, max_iterations=10")
    result = engine.improve_bpmn_process(simple_bpmn.copy(), target_score=90, max_iterations=10)
    
    print(f"\n📈 WYNIKI:")
    print(f"   Liczba iteracji: {len(result['improvement_history'])}")
    
    for i, iteration in enumerate(result['improvement_history']):
        print(f"   • Iteracja {i+1}: {iteration['status']} - zastosowano {len(iteration['improvements_applied'])} poprawek")
        if iteration['status'] == 'target_achieved':
            print(f"     → Osiągnięto cel: {iteration['compliance_report']['overall_score']}")
        elif iteration['status'] == 'no_improvements':
            print(f"     → Brak możliwych poprawek przy wyniku: {iteration['compliance_report']['overall_score']}")
    
    print(f"\n🏆 Wynik końcowy: {result['final_compliance']['overall_score']}")

if __name__ == "__main__":
    test_iterations()