"""
Analiza luk w systemie iteracyjnej poprawy BPMN
Sprawdzenie co brakuje aby osiągnąć nasze ręczne rezultaty

Autor: AI Assistant 
Data: 2025-11-27
"""

import sys
import os
sys.path.append('.')

from bpmn_compliance_validator import BPMNComplianceValidator, BPMNComplianceIssue
from bpmn_improvement_engine import BPMNImprovementEngine

def analyze_gaps():
    """Analizuje luki w systemie poprawek względem naszych ręcznych napraw"""
    
    print("🔍 ANALIZA LUK W IMPROVEMENT ENGINE")
    print("=" * 70)
    
    validator = BPMNComplianceValidator()
    engine = BPMNImprovementEngine()
    
    print(f"📊 System ma {len(validator.rules)} reguł walidacji")
    
    # Sprawdź które reguły mają auto-fix
    print(f"\n🔧 REGUŁY Z AUTO-FIX:")
    auto_fixable_rules = []
    
    # Test problematycznego BPMN z naszego case'u
    problematic_bpmn = {
        "process_name": "Polski proces BLIK",
        "participants": [
            {"id": "Klient", "name": "Klient", "type": "human"},
            {"id": "Sprzedawca", "name": "Sprzedawca/Terminal", "type": "system"},
            {"id": "Aplikacja", "name": "Aplikacja mobilna banku", "type": "system"},
            {"id": "SystemBLIK", "name": "System BLIK banku", "type": "system"},
            {"id": "Clearing", "name": "Clearing BLIK", "type": "system"},
            {"id": "CoreBanking", "name": "System core banking", "type": "system"}
        ],
        "elements": [
            # Brak Start/End Events - tak jak było w naszym oryginalnym problemie
            {"id": "task_wybor", "name": "Wybór płatności BLIK", "type": "userTask", "participant": "Klient"},
            {"id": "task_kod", "name": "Podanie kodu", "type": "userTask", "participant": "Sprzedawca"},
            {"id": "task_autoryzacja", "name": "Autoryzacja płatności", "type": "userTask", "participant": "Aplikacja"},
            {"id": "task_sprawdzenie", "name": "Sprawdzenie środków", "type": "serviceTask", "participant": "SystemBLIK"},
            {"id": "task_clearing", "name": "Przetwarzanie", "type": "serviceTask", "participant": "Clearing"},
            {"id": "task_transfer", "name": "Transfer środków", "type": "serviceTask", "participant": "CoreBanking"}
        ],
        "flows": [
            # Message Flows - tak jak w naszym oryginalnym problemie
            {"id": "mf1", "source": "task_wybor", "target": "task_kod", "type": "message"},
            {"id": "mf2", "source": "task_autoryzacja", "target": "task_sprawdzenie", "type": "message"},
            {"id": "mf3", "source": "task_sprawdzenie", "target": "task_clearing", "type": "message"},
            {"id": "mf4", "source": "task_clearing", "target": "task_transfer", "type": "message"}
        ]
    }
    
    # Uruchom walidację
    print(f"\n🧪 Test na problematycznym BPMN (reprezentuje nasz oryginalny problem):")
    compliance_report = validator.validate_bpmn_compliance(problematic_bpmn)
    
    print(f"   Jakość początkowa: {compliance_report.overall_score:.1f}/100")
    print(f"   Problemów wykrytych: {len(compliance_report.issues)}")
    
    # Kategoryzuj problemy
    critical_issues = [i for i in compliance_report.issues if i.severity.value == 'CRITICAL']
    auto_fixable_issues = [i for i in compliance_report.issues if i.auto_fixable]
    
    print(f"   Krytyczne problemy: {len(critical_issues)}")
    print(f"   Auto-fixable problemy: {len(auto_fixable_issues)}")
    
    print(f"\n📋 SZCZEGÓŁOWA ANALIZA PROBLEMÓW:")
    
    # Kategoryzuj problemy według typów (jak nasze ręczne naprawy)
    missing_start_events = []
    missing_end_events = []
    message_flow_issues = []
    pool_structure_issues = []
    
    for issue in compliance_report.issues:
        if "Start Event" in issue.message and "nie ma" in issue.message:
            missing_start_events.append(issue)
        elif "End Event" in issue.message and "nie ma" in issue.message:
            missing_end_events.append(issue)
        elif "Message Flow" in issue.message:
            message_flow_issues.append(issue)
        elif "Pool" in issue.message:
            pool_structure_issues.append(issue)
    
    print(f"   🎯 Brakujące Start Events: {len(missing_start_events)} (Nasze ręczne: 5 Intermediate Catch Events)")
    for issue in missing_start_events[:3]:
        auto_icon = "🔧" if issue.auto_fixable else "❌"
        print(f"      {auto_icon} {issue.rule_code}: {issue.message}")
    
    print(f"   🏁 Brakujące End Events: {len(missing_end_events)} (Nasze ręczne: 8 End Events)")
    for issue in missing_end_events[:3]:
        auto_icon = "🔧" if issue.auto_fixable else "❌"
        print(f"      {auto_icon} {issue.rule_code}: {issue.message}")
    
    print(f"   💬 Message Flow problemy: {len(message_flow_issues)} (Nasze ręczne: przekierowanie targeting)")
    for issue in message_flow_issues[:3]:
        auto_icon = "🔧" if issue.auto_fixable else "❌"
        print(f"      {auto_icon} {issue.rule_code}: {issue.message}")
    
    print(f"   🏗️ Pool structure problemy: {len(pool_structure_issues)}")
    for issue in pool_structure_issues[:3]:
        auto_icon = "🔧" if issue.auto_fixable else "❌"
        print(f"      {auto_icon} {issue.rule_code}: {issue.message}")
    
    # Test improvement engine
    print(f"\n🔧 TEST IMPROVEMENT ENGINE:")
    try:
        improvement_result = engine.improve_bpmn_process(problematic_bpmn, target_score=80, max_iterations=3)
        
        print(f"   Sukces: {improvement_result.get('success', 'Nieznany')}")
        print(f"   Jakość końcowa: {improvement_result['final_compliance'].overall_score:.1f}")
        print(f"   Poprawa: +{improvement_result['summary']['improvement']:.1f}")
        print(f"   Zastosowane naprawy: {improvement_result['summary']['total_fixes_applied']}")
        
        # Sprawdź co zostało dodane
        improved_bpmn = improvement_result['improved_process']
        
        # Policz dodane elementy
        original_elements = len(problematic_bpmn['elements'])
        improved_elements = len(improved_bpmn['elements'])
        added_elements = improved_elements - original_elements
        
        print(f"   Dodane elementy: {added_elements}")
        
        # Sprawdź typy dodanych elementów
        new_elements = improved_bpmn['elements'][original_elements:]
        start_events_added = len([e for e in new_elements if e.get('type') == 'startEvent'])
        end_events_added = len([e for e in new_elements if e.get('type') == 'endEvent'])
        intermediate_catch_added = len([e for e in new_elements if e.get('type') == 'intermediateCatchEvent'])
        
        print(f"   Start Events dodane: {start_events_added}")
        print(f"   End Events dodane: {end_events_added}")
        print(f"   Intermediate Catch Events dodane: {intermediate_catch_added}")
        
    except Exception as e:
        print(f"   ❌ Błąd improvement engine: {e}")
        import traceback
        traceback.print_exc()
    
    # Analiza luk
    print(f"\n" + "=" * 70)
    print(f"🎯 ANALIZA LUK (porównanie z naszymi ręcznymi naprawami)")
    print(f"=" * 70)
    
    print(f"\n✅ NASZE RĘCZNE NAPRAWY (SUKCES):")
    print(f"   • 5 Intermediate Catch Events dla Pool z incoming Message Flows")
    print(f"   • 8 End Events w różnych Pool")
    print(f"   • Przekierowanie Message Flow z Start Events na Intermediate Catch Events")
    print(f"   • Zachowanie logiki biznesowej")
    print(f"   • 100% zgodność BPMN 2.0")
    
    print(f"\n❌ LUKI W IMPROVEMENT ENGINE:")
    
    # Luka 1: Brak logiki Intermediate Catch Events
    print(f"\n1. 🎯 BRAK LOGIKI INTERMEDIATE CATCH EVENTS:")
    print(f"   Problem: _fix_missing_start_event() zawsze dodaje Start Event")
    print(f"   Potrzeba: Sprawdzać incoming Message Flows i dodawać Intermediate Catch Event")
    print(f"   Auto-fixable: Tak, ale logika niepełna")
    
    # Luka 2: Message Flow targeting
    print(f"\n2. 💬 BRAK AUTO-FIX MESSAGE FLOW TARGETING:")
    print(f"   Problem: System wykrywa że Message Flow wskazuje na Start Event")
    print(f"   Potrzeba: Auto-fix przekierowujący na Intermediate Catch Event")
    print(f"   Auto-fixable: Nie - oznaczone jako False")
    
    # Luka 3: End Events per Pool
    print(f"\n3. 🏁 END EVENTS - LOGIKA GLOBALNA ZAMIAST PER POOL:")
    print(f"   Problem: _fix_missing_end_event() dodaje globalnie")
    print(f"   Potrzeba: Dodawać End Event do każdego Pool z aktywnościami")
    print(f"   Auto-fixable: Częściowo, ale logika niepełna")
    
    # Luka 4: Brak reguł specyficznych dla multi-pool
    print(f"\n4. 🏗️ BRAK REGUŁ MULTI-POOL:")
    print(f"   Problem: Wiele reguł traktuje proces jako single-pool")
    print(f"   Potrzeba: Rozszerzone reguły dla procesów z wieloma Pool")
    print(f"   Auto-fixable: Trzeba dodać")
    
    print(f"\n🔧 KONKRETNE ZMIANY WYMAGANE:")
    print(f"\n   A. W bpmn_improvement_engine.py:")
    print(f"      • Rozszerz _fix_missing_start_event() o logikę Message Flows")
    print(f"      • Dodaj _fix_message_flow_targeting()")
    print(f"      • Popraw _fix_missing_end_event() dla multi-pool")
    print(f"      • Dodaj _add_intermediate_catch_events()")
    
    print(f"\n   B. W bpmn_compliance_validator.py:")
    print(f"      • Ustaw auto_fixable=True dla Message Flow targeting")
    print(f"      • Dodaj więcej reguł multi-pool")
    print(f"      • Lepsze wykrywanie Pool wymagających Intermediate Catch Events")
    
    print(f"\n📈 OCZEKIWANY REZULTAT PO POPRAWKACH:")
    print(f"   • Auto-fix osiągnie podobne rezultaty jak nasze ręczne naprawy")
    print(f"   • 5 Intermediate Catch Events dodanych automatycznie")
    print(f"   • 8 End Events w odpowiednich Pool")
    print(f"   • Message Flow targeting poprawiony")
    print(f"   • Jakość BPMN 85-95 (vs nasze ręczne 100)")

if __name__ == "__main__":
    analyze_gaps()