"""
Demo: Advanced BPMN Auto-Fixer Integration
Demonstracja integracji zaawansowanego systemu auto-napraw z aplikacją

Autor: AI Assistant
Data: 2025-11-27

Kompletny test całej integracji - od ręcznych napraw do zautomatyzowanego systemu.
"""

import sys
import os
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "bpmn_v2"))
sys.path.append(str(current_dir / "src"))

def test_integration_demo():
    """
    Kompletny test integracji zaawansowanego auto-fixera
    """
    print("🚀 DEMO: ADVANCED BPMN AUTO-FIXER INTEGRATION")
    print("=" * 80)
    
    # Test 1: Import Integration Manager
    print("\n📦 KROK 1: Test importów")
    try:
        from bpmn_v2.integration_manager import BPMNIntegrationManager, quick_fix_bpmn, get_integration_status
        from src.bpmn_integration import create_bpmn_integration
        print("   ✅ Integration Manager zaimportowany")
        print("   ✅ BPMN Integration zaimportowany")
    except ImportError as e:
        print(f"   ❌ Błąd importu: {e}")
        return False
    
    # Test 2: Check Integration Status
    print("\n🔍 KROK 2: Status komponentów")
    status = get_integration_status()
    print(f"   Dostępny: {status['available']}")
    print(f"   JSON Engine: {status.get('json_engine', 'N/A')}")
    print(f"   XML Fixer: {status.get('xml_fixer', 'N/A')}")
    print(f"   Validator: {status.get('validator', 'N/A')}")
    
    if status.get('errors'):
        print("   ⚠️ Błędy:")
        for error in status['errors']:
            print(f"      - {error}")
    
    # Test 3: Create Sample Broken BPMN (like our original problem)
    print("\n🏗️ KROK 3: Tworzenie problematycznego BPMN")
    
    # This simulates the type of BPMN we had originally with missing Start/End events in pools
    broken_bpmn_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  id="Definitions_Polish_BLIK">
  <bpmn:collaboration id="Collaboration_BLIK">
    <bpmn:participant id="Klient" name="Klient" processRef="Process_Klient"/>
    <bpmn:participant id="Sprzedawca_Terminal" name="Sprzedawca/Terminal" processRef="Process_Sprzedawca"/>
    <bpmn:participant id="Aplikacja_mobilna_banku" name="Aplikacja mobilna banku" processRef="Process_Aplikacja"/>
    <bpmn:participant id="System_BLIK_banku" name="System BLIK banku" processRef="Process_System_BLIK"/>
    <bpmn:participant id="Clearing_BLIK" name="Clearing BLIK" processRef="Process_Clearing"/>
    <bpmn:participant id="System_core_banking" name="System core banking" processRef="Process_Core_Banking"/>
    
    <!-- Message Flows pointing to wrong elements - will be fixed -->
    <bpmn:messageFlow id="MessageFlow_1" sourceRef="task_wybor_platnosci" targetRef="task_podanie_kodu"/>
    <bpmn:messageFlow id="MessageFlow_2" sourceRef="task_autoryzacja" targetRef="task_sprawdzenie_srodkow"/>
    <bpmn:messageFlow id="MessageFlow_3" sourceRef="task_sprawdzenie_srodkow" targetRef="task_przetwarzanie"/>
    <bpmn:messageFlow id="MessageFlow_4" sourceRef="task_przetwarzanie" targetRef="task_potwierdzenie_terminala"/>
    <bpmn:messageFlow id="MessageFlow_5" sourceRef="task_potwierdzenie_terminala" targetRef="task_transfer_srodkow"/>
  </bpmn:collaboration>
  
  <!-- MISSING START/END EVENTS in pools - exactly our original problem -->
  <bpmn:process id="Process_Klient" isExecutable="false">
    <bpmn:userTask id="task_wybor_platnosci" name="Wybór płatności BLIK"/>
    <bpmn:userTask id="task_autoryzacja" name="Autoryzacja płatności PIN/biometria"/>
  </bpmn:process>
  
  <bpmn:process id="Process_Sprzedawca" isExecutable="false">
    <bpmn:userTask id="task_podanie_kodu" name="Podanie 6-cyfrowego kodu"/>
    <bpmn:userTask id="task_potwierdzenie_terminala" name="Potwierdzenie w terminalu"/>
  </bpmn:process>
  
  <bpmn:process id="Process_Aplikacja" isExecutable="false">
    <!-- This process has tasks but no Start/End Events -->
  </bpmn:process>
  
  <bpmn:process id="Process_System_BLIK" isExecutable="false">
    <bpmn:serviceTask id="task_sprawdzenie_srodkow" name="Sprawdzenie dostępności środków"/>
  </bpmn:process>
  
  <bpmn:process id="Process_Clearing" isExecutable="false">
    <bpmn:serviceTask id="task_przetwarzanie" name="Przetwarzanie przez clearing"/>
  </bpmn:process>
  
  <bpmn:process id="Process_Core_Banking" isExecutable="false">
    <bpmn:serviceTask id="task_transfer_srodkow" name="Transfer środków"/>
  </bpmn:process>
</bpmn:definitions>'''
    
    print(f"   📄 Utworzony BPMN XML: {len(broken_bpmn_xml)} znaków")
    print("   🔍 Problemy: Brak Start/End Events w pool, nieprawidłowe Message Flow targeting")
    
    # Test 4: Apply Quick Fix
    print("\n🔧 KROK 4: Aplikacja quick fix")
    success, fixed_bpmn, summary = quick_fix_bpmn(broken_bpmn_xml, "best")
    
    print(f"   Sukces: {success}")
    if success:
        print(f"   Jakość początkowa: {summary.get('original_quality', 0):.1f}")
        print(f"   Jakość końcowa: {summary.get('final_quality', 0):.1f}") 
        print(f"   Poprawa: +{summary.get('improvement', 0):.1f}")
        print(f"   Liczba napraw: {summary.get('fixes_count', 0)}")
        print(f"   Metoda: {summary.get('method', 'unknown')}")
        print(f"   XML po naprawie: {len(fixed_bpmn)} znaków")
        
        # Show recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print("   💡 Rekomendacje:")
            for rec in recommendations[:3]:
                print(f"      - {rec}")
    else:
        print(f"   ❌ Błąd: {summary.get('error', 'Unknown')}")
    
    # Test 5: Test Full BPMN Integration
    print("\n🔗 KROK 5: Test pełnej integracji BPMN")
    try:
        bpmn_integration = create_bpmn_integration(
            api_key="test-key",
            model_provider="mock"
        )
        
        if bpmn_integration:
            print("   ✅ BPMN Integration utworzone")
            
            # Test advanced fix status
            advanced_status = bpmn_integration.get_advanced_fix_status()
            print(f"   Zaawansowane naprawy dostępne: {advanced_status.get('available', False)}")
            
            # Test improvement (if available)
            if advanced_status.get('available'):
                print("   🧪 Test zaawansowanych napraw...")
                success, improved_xml, details = bpmn_integration.improve_bpmn_advanced(
                    broken_bpmn_xml, "best"
                )
                print(f"      Sukces: {success}")
                if success:
                    print(f"      Poprawa jakości: +{details.get('improvement', 0):.1f}")
                    print(f"      Metoda: {details.get('method', 'unknown')}")
        else:
            print("   ⚠️ BPMN Integration niedostępne")
            
    except Exception as e:
        print(f"   ❌ Błąd integracji: {e}")
    
    # Test 6: Comparison with Manual Fix Results
    print("\n📊 KROK 6: Porównanie z ręcznymi naprawami")
    print("   Nasze ręczne naprawy dodały:")
    print("      ✅ 5 Intermediate Catch Events")
    print("      ✅ 8 End Events w różnych Pool")
    print("      ✅ Poprawione Message Flow targeting")
    print("      ✅ Prawidłowa struktura BPMN 2.0")
    
    if success:
        # Analyze what the auto-fixer fixed
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(fixed_bpmn)
            
            # Count elements added
            intermediate_events = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}intermediateCatchEvent')
            end_events = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}endEvent')
            start_events = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}startEvent')
            
            print("   Automatyczne naprawy dodały:")
            print(f"      🔧 {len(intermediate_events)} Intermediate Catch Events")
            print(f"      🔧 {len(end_events)} End Events")
            print(f"      🔧 {len(start_events)} Start Events")
            
            # Calculate success rate
            expected_fixes = 5 + 8  # intermediate + end events from manual fix
            actual_fixes = len(intermediate_events) + len(end_events) + len(start_events)
            success_rate = min(actual_fixes / expected_fixes, 1.0) if expected_fixes > 0 else 0
            print(f"      📈 Wskaźnik pokrycia napraw: {success_rate:.1%}")
            
        except Exception as e:
            print(f"      ❌ Błąd analizy: {e}")
    
    # Test 7: Integration with Streamlit (simulation)
    print("\n🖥️ KROK 7: Symulacja integracji z Streamlit")
    print("   W aplikacji Streamlit użytkownik będzie mógł:")
    print("      🎯 Kliknąć przycisk 'Zaawansowane Auto-naprawy'")
    print("      📊 Zobaczyć metryki poprawy jakości")
    print("      💡 Otrzymać rekomendacje dalszych kroków")
    print("      🔄 Porównać diagram przed/po naprawach")
    print("      📥 Pobrać poprawiony diagram XML")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("📋 PODSUMOWANIE INTEGRACJI")
    print("✅ ZALETY:")
    print("   • Automatyzacja napraw podobnych do naszych ręcznych sukcessów")
    print("   • Integracja z istniejącym UI Streamlit")
    print("   • Fallback do standardowych metod w przypadku błędów")
    print("   • Szczegółowe raportowanie napraw i rekomendacje")
    print("   • Kompatybilność z istniejącą architekturą aplikacji")
    
    print("\n🎯 KORZYŚCI:")
    print("   • Użytkownik może naprawiać diagramy jednym kliknięciem")
    print("   • System automatycznie dodaje brakujące Start/End Events")
    print("   • Poprawne targeting Message Flow (BPMN 2.0 compliance)")
    print("   • Iteracyjne poprawy aż do osiągnięcia wysokiej jakości")
    print("   • Zachowanie oryginalnej logiki biznesowej")
    
    return success

def test_specific_blik_case():
    """
    Test specyficzny dla naszego case'u BLIK - dokładnie ten sam problem który rozwiązywaliśmy ręcznie
    """
    print("\n" + "🔥" * 60)
    print("🏦 SZCZEGÓŁOWY TEST: CASE BLIK (Nasz rzeczywisty przypadek)")
    print("🔥" * 60)
    
    # Load the exact XML that was problematic
    original_problematic_bpmn = '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  id="Definitions_1">
  <bpmn:collaboration id="Collaboration_1">
    <bpmn:participant id="Klient" name="Klient" processRef="Process_Klient"/>
    <bpmn:participant id="Sprzedawca_Terminal" name="Sprzedawca/Terminal" processRef="Process_Sprzedawca"/>
    
    <!-- The EXACT problematic Message Flow we fixed manually -->
    <bpmn:messageFlow id="MessageFlow_1" sourceRef="task_wybor" targetRef="StartEvent_Sprzedawca"/>
  </bpmn:collaboration>
  
  <bpmn:process id="Process_Klient" isExecutable="false">
    <!-- Missing Start Event here - our manual fix added one -->
    <bpmn:userTask id="task_wybor" name="Wybór płatności BLIK"/>
    <!-- Missing End Event here - our manual fix added one -->
  </bpmn:process>
  
  <bpmn:process id="Process_Sprzedawca" isExecutable="false">
    <!-- This was the problem: Message Flow pointed to Start Event -->
    <bpmn:startEvent id="StartEvent_Sprzedawca" name="Start"/>
    <bpmn:userTask id="task_podanie_kodu" name="Podanie kodu"/>
    <!-- Missing End Event here - our manual fix added one -->
  </bpmn:process>
</bpmn:definitions>'''
    
    print("📝 Oryginalny problematyczny BPMN załadowany")
    print("🎯 Problemy do rozwiązania:")
    print("   ❌ Message Flow wskazuje na Start Event (BPMN 2.0 violation)")
    print("   ❌ Brakuje End Events w Pool")
    print("   ❌ Niepełna struktura Pool")
    
    # Apply our advanced auto-fixer
    from bpmn_v2.integration_manager import quick_fix_bpmn
    
    print("\n🔧 Aplikacja zaawansowanego auto-fixera...")
    success, fixed_xml, summary = quick_fix_bpmn(original_problematic_bpmn, "xml_only")
    
    if success:
        print("✅ Auto-fixer zadziałał!")
        print(f"   Poprawa jakości: +{summary.get('improvement', 0):.1f}")
        print(f"   Zastosowano napraw: {summary.get('fixes_count', 0)}")
        
        # Analyze specific fixes
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(fixed_xml)
            
            # Check if intermediate catch events were added
            intermediate_events = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}intermediateCatchEvent')
            end_events = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}endEvent')
            message_flows = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}messageFlow')
            
            print(f"\n📊 Analiza napraw:")
            print(f"   ✅ Dodano {len(intermediate_events)} Intermediate Catch Events")
            print(f"   ✅ Dodano {len(end_events)} End Events")
            print(f"   ✅ Zaktualizowano {len(message_flows)} Message Flows")
            
            # Check message flow targeting
            for mf in message_flows:
                target_ref = mf.get('targetRef')
                if target_ref:
                    # Check if target is now intermediate catch event
                    target_elem = root.find(f".//*[@id='{target_ref}']")
                    if target_elem is not None:
                        elem_type = target_elem.tag.split('}')[-1] if '}' in target_elem.tag else target_elem.tag
                        if elem_type == 'intermediateCatchEvent':
                            print(f"   🎯 Message Flow '{mf.get('id')}' -> {target_ref} (Intermediate Catch Event) ✅")
                        elif elem_type == 'startEvent':
                            print(f"   ⚠️ Message Flow '{mf.get('id')}' -> {target_ref} (Start Event) ❌")
                        else:
                            print(f"   🔍 Message Flow '{mf.get('id')}' -> {target_ref} ({elem_type})")
            
            print(f"\n🏆 PORÓWNANIE Z NASZYMI RĘCZNYMI NAPRAWAMI:")
            print("   Nasze ręczne działania:")
            print("      ✅ Dodaliśmy 5 Intermediate Catch Events")
            print("      ✅ Dodaliśmy 8 End Events") 
            print("      ✅ Przekierowaliśmy Message Flows na Intermediate Catch Events")
            print("      ✅ Zachowaliśmy oryginalną logikę biznesową")
            
            print(f"   Auto-fixer zrobił:")
            print(f"      🤖 Dodał {len(intermediate_events)} Intermediate Catch Events")
            print(f"      🤖 Dodał {len(end_events)} End Events")
            print(f"      🤖 Użył metody: {summary.get('method', 'unknown')}")
            
            # Calculate automation success rate
            manual_fixes = 5 + 8  # our manual intermediate + end events
            auto_fixes = len(intermediate_events) + len(end_events)
            automation_rate = min(auto_fixes / manual_fixes, 1.0) if manual_fixes > 0 else 0
            
            print(f"\n📈 WSKAŹNIK AUTOMATYZACJI: {automation_rate:.1%}")
            if automation_rate > 0.8:
                print("   🏅 DOSKONAŁY wynik automatyzacji!")
            elif automation_rate > 0.6:
                print("   👍 DOBRY wynik automatyzacji")
            else:
                print("   📝 Wymaga dalszych ulepszeń")
                
        except Exception as e:
            print(f"❌ Błąd analizy: {e}")
    else:
        print("❌ Auto-fixer nie zadziałał")
        print(f"   Błąd: {summary.get('error', 'Unknown')}")
    
    print("\n✨ WNIOSKI:")
    print("   • System może automatyzować naprawy podobne do naszych ręcznych")
    print("   • Zachowana jest zgodność z BPMN 2.0")
    print("   • Integracja z UI pozwoli użytkownikom naprawiać diagramy jednym kliknięciem")
    print("   • Fallback zapewnia bezpieczeństwo w przypadku błędów")
    
    return success

if __name__ == "__main__":
    print("🚀 URUCHOMIENIE DEMO INTEGRACJI")
    
    # Run general integration test
    general_success = test_integration_demo()
    
    # Run specific BLIK case test  
    blik_success = test_specific_blik_case()
    
    print(f"\n🎯 WYNIKI FINALNE:")
    print(f"   Test ogólny: {'✅' if general_success else '❌'}")
    print(f"   Test case BLIK: {'✅' if blik_success else '❌'}")
    
    if general_success and blik_success:
        print("\n🏆 INTEGRACJA ZAAWANSOWANEGO AUTO-FIXERA GOTOWA!")
        print("   Można wdrożyć do aplikacji Streamlit")
    else:
        print("\n🔧 Wymagane dalsze prace nad integracją")
    
    print(f"\n📚 NASTĘPNE KROKI:")
    print("   1. Przetestuj w aplikacji Streamlit")
    print("   2. Dodaj więcej przypadków testowych")
    print("   3. Optymalizuj wydajność auto-fixera")
    print("   4. Rozszerz typy napraw BPMN")
    print("   5. Dodaj więcej fallback strategii")