"""
Integration Plan: Advanced BPMN Auto-Fixer
Plan integracji zaawansowanego systemu automatycznych napraw

Autor: AI Assistant  
Data: 2025-11-27

Szczegółowy plan jak zintegrować advanced_auto_fixer.py z główną aplikacją
"""

# === 1. INTEGRATION POINTS (Punkty integracji) ===

"""
KLUCZOWE MIEJSCA DO INTEGRACJI:

1. streamlit_app.py
   - Dodać opcję "Auto-fix BPMN" w UI
   - Integrować z przyciskiem "Popraw diagram"
   
2. bpmn_v2/mcp_server_simple.py  
   - Rozszerzyć _apply_automatic_improvements()
   - Dodać advanced_auto_fixer jako opcję
   
3. src/bpmn_integration.py
   - Dodać metodę improve_bpmn_with_advanced_fixer()
   - Integrować z istniejącym improve_bpmn()
   
4. bpmn_v2/bpmn_improvement_engine.py
   - Dodać advanced fixer jako opcję w improve_bpmn_process()
   - Kombinować z istniejącymi regułami
"""

# === 2. PROPOSED INTEGRATION ARCHITECTURE ===

import sys
import os
from typing import Dict, List, Any, Tuple, Optional

# Przykładowa integracja z głównym systemem
class IntegratedBPMNAutoFixer:
    """
    Zintegrowany system napraw BPMN łączący:
    - Istniejący BPMNImprovementEngine (JSON based)
    - Nowy AdvancedBPMNAutoFixer (XML based)
    """
    
    def __init__(self):
        from bpmn_improvement_engine import BPMNImprovementEngine
        from advanced_auto_fixer import AdvancedBPMNAutoFixer
        from bpmn_compliance_validator import BPMNComplianceValidator
        
        self.json_engine = BPMNImprovementEngine()
        self.xml_fixer = AdvancedBPMNAutoFixer()
        self.validator = BPMNComplianceValidator()
        
    def comprehensive_bpmn_fix(self, bpmn_input: str, input_format: str = "auto") -> Dict[str, Any]:
        """
        Kompleksowa naprawa BPMN łącząca wszystkie metody
        
        Args:
            bpmn_input: BPMN jako JSON dict lub XML string
            input_format: "json", "xml", "auto"
            
        Returns:
            Kompleksowy raport z naprawami
        """
        results = {
            'input_format': input_format,
            'fixes_applied': [],
            'original_quality': 0.0,
            'final_quality': 0.0,
            'improvement': 0.0,
            'fixed_bpmn': bpmn_input,
            'recommendations': []
        }
        
        try:
            # 1. Detect format if auto
            if input_format == "auto":
                input_format = self._detect_format(bpmn_input)
                results['input_format'] = input_format
            
            # 2. Apply appropriate fixes based on format
            if input_format == "json":
                results.update(self._fix_json_bpmn(bpmn_input))
            elif input_format == "xml":
                results.update(self._fix_xml_bpmn(bpmn_input))
            else:
                raise ValueError(f"Unsupported format: {input_format}")
            
            # 3. Generate final recommendations
            results['recommendations'] = self._generate_integration_recommendations(results)
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            results['success'] = False
            return results
    
    def _detect_format(self, bpmn_input) -> str:
        """Auto-detect input format"""
        if isinstance(bpmn_input, dict):
            return "json"
        elif isinstance(bpmn_input, str):
            if bpmn_input.strip().startswith('<?xml') or bpmn_input.strip().startswith('<bpmn'):
                return "xml"
            else:
                try:
                    import json
                    json.loads(bpmn_input)
                    return "json"
                except:
                    return "unknown"
        else:
            return "unknown"
    
    def _fix_json_bpmn(self, bpmn_json) -> Dict[str, Any]:
        """Naprawia BPMN w formacie JSON używając istniejącego silnika"""
        # Convert string to dict if needed
        if isinstance(bpmn_json, str):
            import json
            bpmn_json = json.loads(bpmn_json)
        
        # Use existing JSON-based engine
        improvement_result = self.json_engine.improve_bpmn_process(bpmn_json)
        
        return {
            'success': True,
            'method': 'JSON-based improvements',
            'original_quality': improvement_result['summary']['initial_compliance_score'],
            'final_quality': improvement_result['summary']['final_compliance_score'], 
            'improvement': improvement_result['summary']['improvement'],
            'fixed_bpmn': improvement_result['improved_process'],
            'fixes_applied': improvement_result['improvement_history']
        }
    
    def _fix_xml_bpmn(self, bpmn_xml: str) -> Dict[str, Any]:
        """Naprawia BPMN w formacie XML używając zaawansowanego fixera"""
        
        # Measure original quality (convert to JSON for measurement)
        original_quality = self._estimate_xml_quality(bpmn_xml)
        
        # Apply XML-based fixes
        fixed_xml, fix_summary = self.xml_fixer.apply_comprehensive_auto_fixes(bpmn_xml)
        
        # Measure final quality
        final_quality = self._estimate_xml_quality(fixed_xml)
        
        return {
            'success': True,
            'method': 'XML-based structural fixes',
            'original_quality': original_quality,
            'final_quality': final_quality,
            'improvement': final_quality - original_quality,
            'fixed_bpmn': fixed_xml,
            'fixes_applied': fix_summary['all_fixes'],
            'fix_summary': fix_summary
        }
    
    def _estimate_xml_quality(self, xml_content: str) -> float:
        """Szacuje jakość XML BPMN (uproszony scoring)"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            score = 0.0
            max_score = 100.0
            
            # Check basic structure (20 points)
            if root.find('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}collaboration') is not None:
                score += 10
            
            processes = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}process')
            if processes:
                score += 10
            
            # Check for pools (15 points)
            participants = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}participant')
            if participants:
                score += 15
            
            # Check for start events (20 points)
            start_events = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}startEvent')
            intermediate_events = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}intermediateCatchEvent')
            if start_events or intermediate_events:
                score += 20
            
            # Check for end events (15 points)
            end_events = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}endEvent')
            if end_events:
                score += 15
            
            # Check for message flows (10 points)
            message_flows = root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}messageFlow')
            if message_flows:
                score += 10
            
            # Check for proper IDs (10 points)
            elements_with_ids = root.findall('.//*[@id]')
            total_elements = len(list(root.iter()))
            id_ratio = len(elements_with_ids) / max(1, total_elements)
            score += 10 * id_ratio
            
            return min(score, max_score)
            
        except Exception:
            return 0.0
    
    def _generate_integration_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generuje rekomendacje na podstawie wyników napraw"""
        recommendations = []
        
        improvement = results.get('improvement', 0)
        final_quality = results.get('final_quality', 0)
        
        if improvement > 20:
            recommendations.append("Znaczące poprawy zostały zastosowane - diagram jest teraz bardziej zgodny z BPMN 2.0")
        
        if final_quality > 80:
            recommendations.append("Diagram osiągnął wysoki poziom zgodności ze standardem BPMN")
        elif final_quality > 60:
            recommendations.append("Diagram ma dobrą zgodność - rozważ drobne poprawki stylistyczne") 
        else:
            recommendations.append("Diagram wymaga dalszych poprawek strukturalnych")
        
        fixes_applied = results.get('fixes_applied', [])
        if len(fixes_applied) > 5:
            recommendations.append("Wiele automatycznych napraw zostało zastosowanych - sprawdź wynik")
        
        return recommendations

# === 3. INTEGRATION STEPS (Kroki integracji) ===

"""
PLAN WDROŻENIA - KROK PO KROKU:

KROK 1: Dodanie do streamlit_app.py
----------------------------------------
W funkcji handle_bpmn_improvement() dodać opcję:

if st.button("🔧 Zaawansowane Auto-naprawy", key="advanced_auto_fix"):
    with st.spinner("Stosowanie zaawansowanych napraw..."):
        from bpmn_v2.integration_manager import IntegratedBPMNAutoFixer
        
        fixer = IntegratedBPMNAutoFixer()
        result = fixer.comprehensive_bpmn_fix(current_bpmn_xml, "xml")
        
        if result.get('success'):
            st.success(f"Zastosowano {len(result['fixes_applied'])} napraw!")
            st.info(f"Poprawa jakości: +{result['improvement']:.1f} punktów")
            
            # Update current BPMN
            st.session_state.current_bpmn_xml = result['fixed_bpmn']
            
            # Show recommendations
            for rec in result['recommendations']:
                st.write(f"💡 {rec}")
        else:
            st.error(f"Błąd napraw: {result.get('error', 'Unknown error')}")

KROK 2: Rozszerzenie BPMNIntegration
------------------------------------
W src/bpmn_integration.py dodać metodę:

def improve_bpmn_advanced(self, bpmn_xml: str) -> Tuple[bool, str, Dict]:
    try:
        from bpmn_v2.integration_manager import IntegratedBPMNAutoFixer
        
        fixer = IntegratedBPMNAutoFixer()
        result = fixer.comprehensive_bpmn_fix(bpmn_xml, "xml")
        
        if result.get('success'):
            return True, result['fixed_bpmn'], result
        else:
            return False, bpmn_xml, {"error": result.get('error')}
            
    except Exception as e:
        return False, bpmn_xml, {"error": str(e)}

KROK 3: Integracja z MCP Server
-------------------------------
W bpmn_v2/mcp_server_simple.py rozszerzyć metodę improve_bpmn_process():

def improve_bpmn_process_advanced(self, bpmn_json: Dict, use_xml_fixer: bool = False) -> Dict[str, Any]:
    if use_xml_fixer:
        # Convert JSON to XML, apply XML fixes, convert back
        from json_to_bpmn_generator import BPMNJSONConverter
        from integration_manager import IntegratedBPMNAutoFixer
        
        converter = BPMNJSONConverter()
        xml_bpmn = converter.convert_to_xml_bpmn(bpmn_json)
        
        fixer = IntegratedBPMNAutoFixer()
        fix_result = fixer.comprehensive_bpmn_fix(xml_bpmn, "xml")
        
        # Convert back to JSON if needed
        # ... implementation details ...
        
        return fix_result
    else:
        # Use existing JSON-based improvement
        return self.improvement_engine.improve_bpmn_process(bpmn_json)

KROK 4: Configuration Options
-----------------------------
Dodać ustawienia w AI Config:

"auto_fix_settings": {
    "enable_xml_fixes": true,
    "enable_advanced_structural_fixes": true,
    "auto_add_intermediate_catch_events": true,
    "fix_message_flow_targeting": true,
    "max_auto_fixes_per_iteration": 20
}

KROK 5: UI Options in Streamlit
-------------------------------
Dodać w sidebar opcje konfiguracyjne:

st.sidebar.subheader("🔧 Opcje Auto-napraw")
enable_xml_fixes = st.sidebar.checkbox("Zaawansowane naprawy XML", True)
enable_structural_fixes = st.sidebar.checkbox("Naprawy strukturalne", True)
add_catch_events = st.sidebar.checkbox("Auto-dodawanie Catch Events", True)

KROK 6: Testing Integration
--------------------------
Stworzyć test_integration.py:

def test_full_integration():
    # Test JSON -> XML -> naprawy -> XML -> wynik
    # Test różnych scenariuszy błędów
    # Test kompatybilności z istniejącym kodem
"""

# === 4. FALLBACK STRATEGY ===

"""
STRATEGIA BEZPIECZEŃSTWA:

1. ALWAYS preserve original BPMN before applying fixes
2. Implement rollback mechanism if fixes fail
3. Graceful degradation - if XML fixes fail, use JSON fixes
4. Clear error reporting and logging
5. User confirmation for major structural changes

EXAMPLE IMPLEMENTATION:

def safe_apply_fixes(bpmn_input):
    original_backup = copy.deepcopy(bpmn_input)
    
    try:
        # Try advanced fixes first
        result = advanced_fixer.apply_fixes(bpmn_input)
        
        # Validate result
        if validate_result(result):
            return result
        else:
            # Fall back to original method
            return standard_fixer.apply_fixes(original_backup)
            
    except Exception:
        # Complete fallback
        return original_backup
"""

# === 5. BENEFITS OF THIS INTEGRATION ===

"""
KORZYŚCI Z INTEGRACJI:

1. STRUCTURAL IMPROVEMENTS
   - Automatic addition of missing Start/End Events
   - Proper Intermediate Catch Events for Message Flows
   - Pool/Process structure validation and repair

2. BPMN 2.0 COMPLIANCE  
   - Message Flow targeting fixes (Start Event → Intermediate Catch Event)
   - Proper element placement within Pools
   - Standard-compliant element connections

3. USER EXPERIENCE
   - One-click comprehensive fixes
   - Clear before/after comparison
   - Detailed fix reporting
   - Rollback capability

4. QUALITY ASSURANCE
   - Multi-layer validation (JSON + XML)
   - Comprehensive error checking
   - Success rate tracking
   - Fix effectiveness measurement

5. MAINTAINABILITY
   - Modular architecture
   - Easy to extend with new fix types
   - Clear separation of concerns
   - Comprehensive testing framework
"""

if __name__ == "__main__":
    print("📋 PLAN INTEGRACJI ADVANCED AUTO-FIXER")
    print("=" * 70)
    print("Ten plik zawiera kompletny plan integracji zaawansowanego")
    print("systemu automatycznych napraw z główną aplikacją.")
    print("\nNajważniejsze punkty:")
    print("✅ 1. Integracja z streamlit_app.py")
    print("✅ 2. Rozszerzenie BPMNIntegration")
    print("✅ 3. Integracja z MCP Server")
    print("✅ 4. Opcje konfiguracyjne")
    print("✅ 5. Testowanie integracji")
    print("✅ 6. Strategia bezpieczeństwa")