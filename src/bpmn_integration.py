"""
BPMN Integration Module
Moduł integracji systemu BPMN v2 z główną aplikacją Streamlit

Funkcje:
1. Integracja konfiguracji AI z istniejącym .env
2. Wywołanie pipeline'u BPMN z UI
3. Obsługa wyników i błędów BPMN
"""

import sys
import os
from pathlib import Path

# Add bpmn_v2 to path
bpmn_path = Path(__file__).parent.parent / "bpmn_v2"
sys.path.append(str(bpmn_path))

try:
    from bpmn_v2.ai_integration import AIConfig, AIProvider, AIClientFactory
    from bpmn_v2.ai_config import create_bpmn_config
    from bpmn_v2.complete_pipeline import BPMNv2Pipeline
    from bpmn_v2.iterative_pipeline import IterativeImprovementPipeline
    from bpmn_v2.mcp_server_simple import EnhancedBPMNQualityChecker
    from bpmn_v2.integration_manager import BPMNIntegrationManager, quick_fix_bpmn
    BPMN_MODULES_AVAILABLE = True
    ADVANCED_AUTO_FIX_AVAILABLE = True
    print("✅ BPMN v2 modules imported successfully")
    print("✅ Advanced Auto-Fixer available")
except ImportError as e:
    print(f"❌ Warning: BPMN v2 modules not available: {e}")
    import traceback
    print(f"❌ Full import error:\n{traceback.format_exc()}")
    BPMN_MODULES_AVAILABLE = False
    ADVANCED_AUTO_FIX_AVAILABLE = False
    
    # Define dummy classes for graceful degradation only if import failed
    class AIConfig:
        @classmethod
        def from_main_app_env(cls, *args, **kwargs):
            return None
    
    class BPMNv2Pipeline:
        def __init__(self, *args, **kwargs):
            pass
        
        def run_complete_pipeline(self, *args, **kwargs):
            return {'success': False, 'error': 'BPMN not available'}
    
    class IterativeImprovementPipeline:
        def __init__(self, *args, **kwargs):
            pass
        
        def generate_and_improve_process(self, *args, **kwargs):
            return {'success': False, 'error': 'BPMN not available'}
    
    class BPMNQualityChecker:
        def verify_bpmn_quality(self, *args, **kwargs):
            return None

from typing import Optional, Dict, Any, Tuple
import streamlit as st


class BPMNIntegration:
    """Klasa integrująca system BPMN v2 z aplikacją Streamlit"""
    
    def __init__(self, api_key: str, model_provider: str, chat_url: Optional[str] = None, 
                 default_model: Optional[str] = None):
        """
        Inicjalizuje integrację BPMN
        
        Args:
            api_key: Klucz API z głównej aplikacji
            model_provider: Dostawca modelu (openai, claude, ollama)
            chat_url: URL endpoint AI (opcjonalny)
            default_model: Domyślny model (opcjonalny)
        """
        self.api_key = api_key
        self.model_provider = model_provider
        self.chat_url = chat_url
        self.default_model = default_model
        
        # Create AI config from main app settings
        try:
            # Use the new dynamic configuration system
            self.ai_config = create_bpmn_config(default_model)
            self.available = True
            print(f"✅ BPMN Integration initialized with {model_provider}")
        except Exception as e:
            print(f"❌ BPMN Integration failed: {e}")
            import traceback
            print(f"❌ Full error:\n{traceback.format_exc()}")
            self.ai_config = None
            self.available = False
    
    def is_available(self) -> bool:
        """Sprawdza czy integracja BPMN jest dostępna"""
        return self.available and self.ai_config is not None
    
    def generate_bpmn_process(self, user_input: str, process_type: str = "business", 
                             quality_target: float = 0.8, max_iterations: int = 10) -> Tuple[bool, str, Dict]:
        """
        Generuje proces BPMN na podstawie opisu użytkownika
        
        Args:
            user_input: Opis procesu od użytkownika
            process_type: Typ procesu (business, technical, etc.)
            quality_target: Docelowa jakość procesu (0.0-1.0)
            max_iterations: Maksymalna liczba iteracji poprawek
            
        Returns:
            Tuple[success, bpmn_xml, metadata]
        """
        if not self.is_available():
            return False, "BPMN Integration not available", {}
        
        try:
            print(f"🔧 Creating BPMN pipeline with AI config: {self.ai_config}")
            print(f"🔧 DEBUG: user_input length: {len(user_input)}")
            print(f"🔧 DEBUG: user_input preview: {user_input[:200]}...")
            
            # Create BPMN pipeline
            pipeline = BPMNv2Pipeline(self.ai_config)
            print(f"🔧 Pipeline created successfully")
            
            print(f"🔧 Running complete pipeline with input length: {len(user_input)}")
            # Run complete pipeline
            result_dict = pipeline.run_complete_pipeline(
                polish_text=user_input,
                process_name="Generated_Process",
                context=process_type,
                save_artifacts=False  # Don't save files in Streamlit
            )
            print(f"🔧 Pipeline completed. Result success: {result_dict.get('success', False)}")
            
            # Use iterative improvement if quality target is set
            if quality_target > 0.5 and result_dict['success']:
                print(f"🔄 Using iterative improvement (target: {quality_target})")
                iterative_pipeline = IterativeImprovementPipeline(
                    ai_config=self.ai_config,
                    max_iterations=max_iterations,
                    target_quality=quality_target
                )
                
                iterative_result = iterative_pipeline.generate_and_improve_process(
                    polish_text=user_input,
                    process_name="Generated_Process",
                    context=process_type
                )
                
                print(f"🔧 Iterative result keys: {list(iterative_result.keys()) if iterative_result else 'None'}")
                print(f"🔧 Iterative result success: {iterative_result.get('success') if iterative_result else 'None'}")
                if iterative_result and iterative_result.get('final_bpmn_xml'):
                    print(f"🔧 final_bpmn_xml length: {len(iterative_result['final_bpmn_xml'])}")
                
                if iterative_result and iterative_result.get('success'):
                    final_xml = iterative_result.get('final_bpmn_xml')
                    print(f"🔧 Iterative final_xml length: {len(final_xml) if final_xml else 0}")
                    if not final_xml:
                        print("⚠️ WARNING: final_bpmn_xml is empty, using base result")
                        final_xml = result_dict.get('bpmn_xml', '')
                        print(f"🔧 Base result XML length: {len(final_xml) if final_xml else 0}")
                    
                    print(f"🔧 Returning final_xml length: {len(final_xml) if final_xml else 0}")
                    return True, final_xml, {
                        "iterations": len(iterative_result.get('iterations', [])),
                        "final_score": iterative_result.get('final_quality', 0.0),
                        "improvements": iterative_result.get('iteration_history', []),
                        "model": self.ai_config.model,
                        "provider": self.ai_config.provider.value,
                        "base_result": result_dict,
                        "iterative_result": iterative_result
                    }
                else:
                    # Fall back to base result if iterative improvement fails
                    print(f"🔧 Iterative improvement failed, using fallback. Error: {iterative_result.get('error', 'Unknown error')}")
                    return True, result_dict['bpmn_xml'], {
                        "model": self.ai_config.model,
                        "provider": self.ai_config.provider.value,
                        "base_result": result_dict,
                        "iterative_error": iterative_result.get('error', 'Unknown error'),
                        "iterations": 1,  # Fallback count
                        "final_score": result_dict.get('quality_score', 0.0)
                    }
            
            elif result_dict['success']:
                # Simple single-shot generation
                print(f"🔧 Returning base result metadata: {result_dict.keys()}")
                return True, result_dict['bpmn_xml'], {
                    "model": self.ai_config.model,
                    "provider": self.ai_config.provider.value,
                    "analysis": result_dict.get('analysis', {}),
                    "validation": result_dict.get('validation', {}),
                    "base_result": result_dict,
                    "iterations": 1,  # Single shot counts as 1 iteration
                    "final_score": result_dict.get('quality_score', 0.0)
                }
            else:
                return False, f"BPMN generation failed: {result_dict.get('error', 'Unknown error')}", {}
                    
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Error in BPMN generation: {str(e)}")
            print(f"❌ Full traceback:\n{error_details}")
            return False, f"Error in BPMN generation: {str(e)}", {"error": str(e), "traceback": error_details}
    
    def validate_bpmn(self, bpmn_xml: str) -> Tuple[bool, float, Dict]:
        """
        Waliduje i ocenia jakość BPMN
        
        Args:
            bpmn_xml: XML procesu BPMN do walidacji
            
        Returns:
            Tuple[is_valid, quality_score, validation_details]
        """
        if not self.is_available():
            return False, 0.0, {"error": "BPMN Integration not available"}
        
        try:
            if BPMN_MODULES_AVAILABLE:
                quality_checker = EnhancedBPMNQualityChecker()
            else:
                quality_checker = BPMNQualityChecker()
            result = quality_checker.verify_bpmn_quality(bpmn_xml)
            
            if result:
                return result.is_valid, result.quality_score, {
                    "issues": result.issues,
                    "suggestions": result.suggestions,
                    "metrics": result.metrics
                }
            else:
                return False, 0.0, {"error": "Validation failed"}
                
        except Exception as e:
            return False, 0.0, {"error": f"Validation error: {str(e)}"}
    
    def improve_bpmn(self, bpmn_xml: str, target_score: float = 0.8) -> Tuple[bool, str, Dict]:
        """
        Ulepsza istniejący proces BPMN
        
        Args:
            bpmn_xml: Aktualny XML BPMN
            target_score: Docelowa jakość
            
        Returns:
            Tuple[success, improved_bpmn_xml, improvement_details]
        """
        if not self.is_available():
            return False, bpmn_xml, {"error": "BPMN Integration not available"}
        
        try:
            if BPMN_MODULES_AVAILABLE:
                quality_checker = EnhancedBPMNQualityChecker()
            else:
                quality_checker = BPMNQualityChecker()
            improved = quality_checker.suggest_improvements(bpmn_xml, target_score)
            
            if improved:
                return True, improved.improved_bpmn, {
                    "original_score": improved.original_quality,
                    "new_score": improved.new_quality,
                    "improvements_made": improved.improvements_applied
                }
            else:
                return False, bpmn_xml, {"error": "Improvement failed"}
                
        except Exception as e:
            return False, bpmn_xml, {"error": f"Improvement error: {str(e)}"}
    
    def improve_bpmn_advanced(self, bpmn_xml: str, method: str = "best") -> Tuple[bool, str, Dict]:
        """
        Ulepsza BPMN używając zaawansowanego auto-fixera
        
        Args:
            bpmn_xml: Aktualny XML BPMN
            method: Metoda napraw ("xml_only", "json_only", "best", "both")
            
        Returns:
            Tuple[success, improved_bpmn_xml, improvement_details]
        """
        if not self.is_available():
            return False, bpmn_xml, {"error": "BPMN Integration not available"}
        
        if not ADVANCED_AUTO_FIX_AVAILABLE:
            # Fallback to regular improvement
            return self.improve_bpmn(bpmn_xml)
        
        try:
            # Use advanced auto-fixer
            success, fixed_bpmn, summary = quick_fix_bpmn(bpmn_xml, method)
            
            if success:
                return True, fixed_bpmn, {
                    "original_quality": summary.get('original_quality', 0),
                    "final_quality": summary.get('final_quality', 0),
                    "improvement": summary.get('improvement', 0),
                    "fixes_count": summary.get('fixes_count', 0),
                    "method": summary.get('method', method),
                    "recommendations": summary.get('recommendations', []),
                    "success_rate": 1.0
                }
            else:
                error_msg = summary.get('error', 'Unknown error')
                # Try fallback to regular improvement
                return self.improve_bpmn(bpmn_xml)
                
        except Exception as e:
            # Fallback to regular improvement on any error
            print(f"Advanced auto-fix failed, falling back: {e}")
            return self.improve_bpmn(bpmn_xml)
    
    def get_advanced_fix_status(self) -> Dict[str, Any]:
        """
        Zwraca status zaawansowanego systemu auto-fix
        
        Returns:
            Dict z informacjami o dostępności i komponentach
        """
        if not ADVANCED_AUTO_FIX_AVAILABLE:
            return {
                "available": False,
                "reason": "Advanced auto-fixer not imported"
            }
        
        try:
            from bpmn_v2.integration_manager import get_integration_status
            return get_integration_status()
        except Exception as e:
            return {
                "available": False,
                "reason": f"Error getting status: {str(e)}"
            }


def create_bpmn_integration(api_key: str, model_provider: str, chat_url: Optional[str] = None,
                           default_model: Optional[str] = None) -> Optional[BPMNIntegration]:
    """
    Factory function do tworzenia integracji BPMN
    
    Args:
        api_key: Klucz API
        model_provider: Dostawca AI 
        chat_url: URL endpoint (opcjonalny)
        default_model: Model domyślny (opcjonalny)
        
    Returns:
        BPMNIntegration instance lub None jeśli niedostępne
    """
    try:
        integration = BPMNIntegration(
            api_key=api_key,
            model_provider=model_provider,
            chat_url=chat_url,
            default_model=default_model
        )
        
        if integration.is_available():
            return integration
        else:
            return None
            
    except Exception as e:
        print(f"Failed to create BPMN integration: {e}")
        return None


# Funkcje pomocnicze dla Streamlit

def display_bpmn_result(success: bool, bpmn_xml: str, metadata: Dict):
    """Wyświetla wynik generowania BPMN w Streamlit z graficznym podglądem"""
    print(f"🔧 Display BPMN result - success: {success}")
    print(f"🔧 Display BPMN result - XML length: {len(bpmn_xml) if bpmn_xml else 0}")
    print(f"🔧 Display BPMN result - metadata keys: {list(metadata.keys())}")
    print(f"🔧 Metadata content: {metadata}")
    
    if success:
        st.success("✅ Proces BPMN został wygenerowany!")
        
        # Show metadata
        with st.expander("📊 Szczegóły generowania", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Model", metadata.get("model", "N/A"))
                st.metric("Dostawca", metadata.get("provider", "N/A"))
            
            with col2:
                if "iterations" in metadata:
                    st.metric("Iteracje", metadata["iterations"])
                    st.metric("Jakość końcowa", f"{metadata.get('final_score', 0):.2f}")
        
        # Store in session state (similar to XML)
        print(f"🔧 DEBUG: Setting session_state.latest_xml - XML length: {len(bpmn_xml) if bpmn_xml else 0}")
        print(f"🔧 DEBUG: XML preview: {bpmn_xml[:200] if bpmn_xml else 'BRAK'}...")
        st.session_state.latest_xml = bpmn_xml
        
        # Import and use BPMN renderer
        try:
            # Try importing from current directory first
            current_dir = Path(__file__).parent
            sys.path.insert(0, str(current_dir))
            from bpmn_renderer import render_bpmn_preview
            render_bpmn_preview(bpmn_xml, show_xml=True)
        except ImportError as e:
            print(f"⚠️ Renderer BPMN niedostępny - {e}")
            # Fallback: show simple XML code
            with st.expander("🔍 Podgląd BPMN XML", expanded=True):
                st.code(bpmn_xml, language="xml")
                st.download_button(
                    label="📥 Pobierz BPMN XML",
                    data=bpmn_xml,
                    file_name="process.bpmn",
                    mime="application/xml"
                )
            
    else:
        st.error(f"❌ Błąd generowania BPMN: {bpmn_xml}")


def display_bpmn_validation(is_valid: bool, quality_score: float, details: Dict):
    """Wyświetla wyniki walidacji BPMN w Streamlit"""
    if is_valid:
        st.success(f"✅ BPMN jest poprawny (jakość: {quality_score:.2f})")
    else:
        st.error(f"❌ BPMN zawiera błędy (jakość: {quality_score:.2f})")
    
    if details.get("issues"):
        with st.expander("⚠️ Znalezione problemy"):
            for issue in details["issues"]:
                st.warning(issue)
    
    if details.get("suggestions"):
        with st.expander("💡 Sugestie poprawek"):
            for suggestion in details["suggestions"]:
                st.info(suggestion)


def display_bpmn_advanced_fix(success: bool, improved_xml: str, fix_details: Dict):
    """
    Wyświetla wyniki zaawansowanych napraw BPMN
    
    Args:
        success: Czy naprawy zostały zastosowane pomyślnie
        improved_xml: Poprawiony XML BPMN
        fix_details: Szczegóły zastosowanych napraw
    """
    if success:
        st.success("✅ Zaawansowane auto-naprawy zastosowane pomyślnie!")
        
        # Show improvement metrics
        with st.expander("📈 Szczegóły poprawek", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                original_quality = fix_details.get('original_quality', 0)
                st.metric("Jakość początkowa", f"{original_quality:.1f}")
            
            with col2:
                final_quality = fix_details.get('final_quality', 0)
                st.metric("Jakość końcowa", f"{final_quality:.1f}")
            
            with col3:
                improvement = fix_details.get('improvement', 0)
                delta_color = "normal" if improvement >= 0 else "inverse"
                st.metric("Poprawa", f"+{improvement:.1f}", delta=f"+{improvement:.1f}", delta_color=delta_color)
            
            with col4:
                fixes_count = fix_details.get('fixes_count', 0)
                st.metric("Ilość napraw", fixes_count)
        
        # Show method used and recommendations
        method = fix_details.get('method', 'unknown')
        st.info(f"🔧 Metoda: **{method}**")
        
        recommendations = fix_details.get('recommendations', [])
        if recommendations:
            with st.expander("💡 Rekomendacje"):
                for i, rec in enumerate(recommendations, 1):
                    st.write(f"{i}. {rec}")
        
        # Update session state with improved XML
        st.session_state.latest_xml = improved_xml
        
        # Show before/after comparison if requested
        if st.button("🔄 Porównaj przed/po", key="compare_before_after"):
            st.session_state.show_bpmn_comparison = True
        
    else:
        error_msg = fix_details.get('error', 'Nieznany błąd')
        st.error(f"❌ Zaawansowane naprawy nie powiodły się: {error_msg}")
        
        # Show fallback info if available
        if 'fallback_used' in fix_details:
            st.warning("⚠️ Użyto metody zapasowej")


def display_advanced_fix_status(status: Dict[str, Any]):
    """
    Wyświetla status zaawansowanego systemu auto-fix
    
    Args:
        status: Status z get_advanced_fix_status()
    """
    if status.get('available', False):
        st.success("✅ Zaawansowane auto-naprawy dostępne")
        
        # Show component status if available
        if 'json_engine' in status:
            col1, col2, col3 = st.columns(3)
            with col1:
                json_status = "✅" if status['json_engine'] else "❌"
                st.write(f"{json_status} JSON Engine")
            with col2:
                xml_status = "✅" if status['xml_fixer'] else "❌"
                st.write(f"{xml_status} XML Fixer")
            with col3:
                validator_status = "✅" if status['validator'] else "❌"
                st.write(f"{validator_status} Validator")
    else:
        reason = status.get('reason', 'Unknown')
        st.warning(f"⚠️ Zaawansowane auto-naprawy niedostępne: {reason}")


def handle_bpmn_improvement_ui(bpmn_integration: BPMNIntegration):
    """
    Obsługuje UI do poprawiania BPMN w Streamlit
    
    Args:
        bpmn_integration: Instancja BPMNIntegration
    """
    if not hasattr(st.session_state, 'latest_xml') or not st.session_state.latest_xml:
        st.info("📄 Brak diagramu BPMN do poprawienia")
        return
    
    st.subheader("🔧 Poprawy BPMN")
    
    # Show advanced fix status
    with st.expander("🔍 Status zaawansowanych napraw"):
        advanced_status = bpmn_integration.get_advanced_fix_status()
        display_advanced_fix_status(advanced_status)
    
    # Improvement options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔧 Standardowe naprawy", key="standard_fix"):
            with st.spinner("Stosowanie standardowych napraw..."):
                success, improved_xml, details = bpmn_integration.improve_bpmn(
                    st.session_state.latest_xml
                )
                display_bpmn_advanced_fix(success, improved_xml, details)
    
    with col2:
        if st.button("🎆 Zaawansowane auto-naprawy", key="advanced_fix"):
            with st.spinner("Stosowanie zaawansowanych napraw..."):
                success, improved_xml, details = bpmn_integration.improve_bpmn_advanced(
                    st.session_state.latest_xml,
                    method="best"
                )
                display_bpmn_advanced_fix(success, improved_xml, details)
    
    with col3:
        # Method selection for advanced fixes
        fix_method = st.selectbox(
            "Metoda napraw",
            ["best", "xml_only", "json_only", "both"],
            help="best: automatycznie wybiera najlepszą metodę"
        )
        
        if st.button("🎯 Naprawy z metodą", key="method_fix"):
            with st.spinner(f"Stosowanie napraw metodą: {fix_method}..."):
                success, improved_xml, details = bpmn_integration.improve_bpmn_advanced(
                    st.session_state.latest_xml,
                    method=fix_method
                )
                display_bpmn_advanced_fix(success, improved_xml, details)
    
    # Quick validation
    st.divider()
    if st.button("🔎 Waliduj aktualny BPMN", key="validate_current"):
        with st.spinner("Walidacja BPMN..."):
            is_valid, quality_score, validation_details = bpmn_integration.validate_bpmn(
                st.session_state.latest_xml
            )
            display_bpmn_validation(is_valid, quality_score, validation_details)


if __name__ == "__main__":
    # Test integration
    test_integration = create_bpmn_integration(
        api_key="test-key",
        model_provider="mock"
    )
    
    if test_integration:
        print("✅ BPMN Integration test successful")
    else:
        print("❌ BPMN Integration test failed")