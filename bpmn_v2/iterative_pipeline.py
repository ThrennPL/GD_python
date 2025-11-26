"""
BPMN v2 - Iterative Improvement Pipeline
Pipeline z automatyczną weryfikacją i poprawkami przez AI

Ten moduł:
1. Generuje pierwotny proces z AI
2. Weryfikuje jakość przez MCP server
3. Automatycznie poprawia braki
4. Iteruje aż do uzyskania wysokiej jakości
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from complete_pipeline import BPMNv2Pipeline
from mcp_server_simple import SimpleMCPServer
from ai_config import get_default_config


class IterativeImprovementPipeline:
    """Pipeline z iteracyjną poprawą procesów BPMN"""
    
    def __init__(self, ai_config=None, max_iterations=10, target_quality=0.8):
        # Use the same config for both pipelines
        config = ai_config or get_default_config()
        self.pipeline = BPMNv2Pipeline(config)
        self.mcp_server = SimpleMCPServer(ai_config=config)  # Pass the same config!
        self.max_iterations = min(max_iterations, 10)  # Limit to 10 for performance
        self.target_quality = target_quality
        
        print("🔄 Iterative Improvement Pipeline initialized")
        print(f"🎯 Target quality: {target_quality}")
        print(f"🔢 Max iterations: {max_iterations} (capped at 10)")
    
    def generate_and_improve_process(self, polish_text: str, process_name: str, 
                                   context: str = "banking") -> Dict[str, Any]:
        """
        Główna metoda - generuje i iteracyjnie poprawia proces
        
        Args:
            polish_text: Opis procesu po polsku
            process_name: Nazwa procesu
            context: Kontekst biznesowy
            
        Returns:
            Finalny proces z historią iteracji
        """
        print(f"\n{'='*60}")
        print(f"🚀 STARTING ITERATIVE IMPROVEMENT")
        print(f"📋 Process: {process_name}")
        print(f"🎯 Target quality: {self.target_quality}")
        print(f"{'='*60}")
        
        result = {
            'process_name': process_name,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'iterations': [],
            'final_process': None,
            'final_bpmn_xml': None,
            'success': False,
            'total_improvements': 0
        }
        
        current_process = None
        iteration = 0
        
        try:
            # ITERATION 0: Generate initial process
            print(f"\n🔄 ITERACJA 0: Generowanie początkowego procesu")
            
            initial_result = self.pipeline.run_complete_pipeline(
                polish_text=polish_text,
                process_name=process_name,
                context=context,
                save_artifacts=False  # Save only final version
            )
            
            if not initial_result['success']:
                raise ValueError(f"Initial generation failed: {initial_result.get('error')}")
            
            current_process = initial_result['ai_response']
            
            # Verify initial process
            initial_verification = self.mcp_server.verify_bpmn_process(current_process)
            
            # Record initial iteration
            iteration_result = {
                'iteration': 0,
                'type': 'initial_generation',
                'process': current_process,
                'verification': initial_verification,
                'improvements_applied': [],
                'quality_score': initial_verification['overall_quality']
            }
            result['iterations'].append(iteration_result)
            
            print(f"📊 Początkowa jakość: {initial_verification['overall_quality']:.2f}")
            
            # Check if initial quality is already good enough
            if initial_verification['overall_quality'] >= self.target_quality:
                print(f"🎯 Początkowa jakość już wystarczająca! ({initial_verification['overall_quality']:.2f})")
                result.update({
                    'final_process': current_process,
                    'final_verification': initial_verification,
                    'success': True,
                    'final_quality': initial_verification['overall_quality']
                })
            else:
                # ITERATIVE IMPROVEMENT LOOP
                iteration_count = 0
                # Note: iteration 0 was initial generation, now iterations 1-max_iterations are improvements
                for iteration in range(1, self.max_iterations):
                    iteration_count = iteration
                    print(f"\n🔄 ITERACJA {iteration}: Weryfikacja i poprawa")
                    
                    # Verify current process
                    verification = self.mcp_server.verify_bpmn_process(current_process)
                    iteration_result['verification'] = verification
                    iteration_result['quality_score'] = verification['overall_quality']
                    
                    print(f"📊 Jakość procesu: {verification['overall_quality']:.2f}")
                    print(f"📋 Braki: {len(verification['missing_elements'])}")
                    print(f"💡 Sugestie: {len(verification['improvement_suggestions'])}")
                    
                    # DEBUG: Sprawdzenie szczegółów verification
                    print(f"🔍 DEBUG - Missing elements: {verification['missing_elements'][:3]}")
                    print(f"🔍 DEBUG - Improvement suggestions: {verification['improvement_suggestions'][:3]}")
                    print(f"🔍 DEBUG - BPMN compliance score: {verification.get('bpmn_compliance', {}).get('score', 'N/A')}")
                    
                    # Create new iteration result for this iteration
                    current_iteration_result = {
                        'iteration': iteration,
                        'type': 'verification_and_improvement',
                        'process': current_process,
                        'verification': verification,
                        'improvements_applied': [],
                        'quality_score': verification['overall_quality']
                    }
                    
                    # Check if we've reached target quality
                    if verification['overall_quality'] >= self.target_quality:
                        print(f"🎯 Osiągnięto docelową jakość! ({verification['overall_quality']:.2f})")
                        current_iteration_result['type'] = 'target_reached'
                        result['iterations'].append(current_iteration_result)
                        break
                
                    # Apply improvements - kontynuuj jeśli jakość niska LUB są konkretne problemy
                    should_improve = (
                        verification['overall_quality'] < self.target_quality and (
                            verification['missing_elements'] or 
                            verification['improvement_suggestions'] or
                            verification['overall_quality'] < 0.5  # Force improvement if quality very low
                        )
                    )
                    
                    if should_improve:
                        print(f"🔧 Aplikowanie ulepszeń...")
                        
                        # Generate improvement prompt
                        improvement_prompt = self.mcp_server.generate_improvement_prompt(
                            current_process, verification
                        )
                        
                        # Get AI to improve the process
                        ai_response = self.pipeline.ai_client.generate_response(improvement_prompt)
                        
                        if ai_response.success:
                            # Parse improved process
                            json_success, improved_process, parse_errors = self.pipeline.response_parser.extract_json(ai_response)
                            
                            if json_success:
                                # Use improved process from AI directly
                                current_process = improved_process
                                
                                # Apply only light auto-fix for critical issues
                                verification_check = self.mcp_server.verify_bpmn_process(current_process)
                                critical_issues = [i for i in verification_check.get('improvement_suggestions', []) 
                                                 if 'CRITICAL' in str(i)]
                                
                                changes = [f"AI improved process structure"]
                                if critical_issues:
                                    changes.append(f"Detected {len(critical_issues)} critical issues for future fixing")
                                
                                current_iteration_result['type'] = 'ai_improvement'
                                current_iteration_result['improvements_applied'] = changes
                                current_iteration_result['process'] = current_process
                                
                                result['total_improvements'] += len(changes)
                                
                                print(f"✅ Zastosowano {len(changes)} ulepszeń")
                                for change in changes[:3]:  # Show first 3
                                    print(f"   - {change}")
                            else:
                                print(f"❌ AI improvement failed: {parse_errors}")
                                # Fall back to automatic improvements only
                                auto_improvements = self.mcp_server.improve_bpmn_process(current_process)
                                current_process = auto_improvements['improved_process']
                                current_iteration_result['improvements_applied'] = auto_improvements['changes_made']
                                current_iteration_result['type'] = 'automatic_improvement_fallback'
                        else:
                            print(f"❌ AI call failed: {ai_response.error}")
                            # Fall back to automatic improvements
                            auto_improvements = self.mcp_server.improve_bpmn_process(current_process)
                            current_process = auto_improvements['improved_process']
                            current_iteration_result['improvements_applied'] = auto_improvements['changes_made']
                            current_iteration_result['type'] = 'automatic_improvement_ai_failed'
                    else:
                        print(f"⚠️ Zakończenie iteracji - jakość: {verification['overall_quality']:.2f}, braki: {len(verification['missing_elements'])}, sugestie: {len(verification['improvement_suggestions'])}")
                        current_iteration_result['type'] = 'no_improvements_needed'
                    
                    # Add current iteration to results
                    result['iterations'].append(current_iteration_result)
                    
                    # Check iteration limit (excluding iteration 0)
                    if iteration >= self.max_iterations - 1:
                        print(f"🔚 Osiągnięto maksymalną liczbę iteracji ({self.max_iterations})")
                        current_iteration_result['type'] = 'max_iterations_reached'
                        break
            
                # Final verification and finalization
                final_verification = self.mcp_server.verify_bpmn_process(current_process)
                
                # DEBUG: Check if final process has required structure
                print(f"\n🔍 DEBUGGING FINALNY PROCES:")
                print(f"   ✓ process_name: {current_process.get('process_name', 'BRAK!')}")
                print(f"   ✓ elements count: {len(current_process.get('elements', []))}")
                start_events = [e for e in current_process.get('elements', []) if e.get('type') == 'startEvent']
                end_events = [e for e in current_process.get('elements', []) if e.get('type') == 'endEvent']
                print(f"   ✓ startEvents: {len(start_events)} {[e.get('id') for e in start_events]}")
                print(f"   ✓ endEvents: {len(end_events)} {[e.get('id') for e in end_events]}")
                
                print(f"\n📊 FINALNA JAKOŚĆ: {final_verification['overall_quality']:.2f}")
                
                # Generate final BPMN XML - ensure process is valid
                if current_process and isinstance(current_process, dict) and current_process.get('elements'):
                    print(f"🔧 Converting final process to BPMN XML...")
                    final_bpmn_xml = self.pipeline.convert_json_to_bpmn(current_process)
                    print(f"🔧 Final XML length: {len(final_bpmn_xml) if final_bpmn_xml else 0}")
                else:
                    print("⚠️ WARNING: Final process is empty or invalid, using initial process")
                    # Fall back to initial process from iteration 0
                    initial_process = result['iterations'][0]['process'] if result['iterations'] else None
                    if initial_process:
                        current_process = initial_process
                        final_verification = result['iterations'][0]['verification']
                    else:
                        current_process = {'elements': [], 'flows': [], 'participants': []}
                    print(f"🔧 Converting fallback process to BPMN XML...")
                    final_bpmn_xml = self.pipeline.convert_json_to_bpmn(current_process)
                    print(f"🔧 Fallback XML length: {len(final_bpmn_xml) if final_bpmn_xml else 0}")
                
                # Save final artifacts
                final_files = self.pipeline.save_pipeline_outputs(
                    process_name + "_improved", 
                    polish_text, 
                    "Iteratively improved process",
                    current_process, 
                    final_bpmn_xml
                )
                
                result.update({
                    'final_process': current_process,
                    'final_verification': final_verification,
                    'final_bpmn_xml': final_bpmn_xml,
                    'final_files': final_files,
                    'success': True,
                    'final_quality': final_verification['overall_quality']
                })
            
            print(f"\n{'='*60}")
            print(f"✅ ITERATIVE IMPROVEMENT COMPLETED!")
            print(f"📊 Finalna jakość: {result.get('final_quality', 0):.2f}")
            print(f"🔄 Iteracji: {len(result['iterations'])} (max {self.max_iterations})")
            print(f"🔧 Łączne ulepszenia: {result['total_improvements']}")
            if 'final_files' in result:
                print(f"📁 Zapisane pliki: {len(result['final_files'])}")
            print(f"{'='*60}")
            
        except Exception as e:
            print(f"\n❌ BŁĄD ITERATIVE IMPROVEMENT: {e}")
            result['error'] = str(e)
            import traceback
            result['traceback'] = traceback.format_exc()
        
        return result
    
    def compare_iterations(self, result: Dict) -> Dict[str, Any]:
        """Porównuje jakość między iteracjami"""
        if not result.get('iterations'):
            return {'error': 'No iterations to compare'}
        
        comparison = {
            'iteration_count': len(result['iterations']),
            'quality_progression': [],
            'improvements_timeline': [],
            'total_changes': 0
        }
        
        for iteration in result['iterations']:
            comparison['quality_progression'].append({
                'iteration': iteration['iteration'],
                'quality': iteration['quality_score'],
                'type': iteration['type']
            })
            
            if iteration['improvements_applied']:
                comparison['improvements_timeline'].append({
                    'iteration': iteration['iteration'],
                    'changes': iteration['improvements_applied']
                })
                comparison['total_changes'] += len(iteration['improvements_applied'])
        
        # Calculate improvement rate
        if len(comparison['quality_progression']) > 1:
            initial_quality = comparison['quality_progression'][0]['quality']
            final_quality = comparison['quality_progression'][-1]['quality']
            comparison['quality_improvement'] = final_quality - initial_quality
            comparison['improvement_rate'] = comparison['quality_improvement'] / len(result['iterations'])
        
        return comparison
    
    def generate_improvement_report(self, result: Dict) -> str:
        """Generuje raport z ulepszeń"""
        if not result['success']:
            return f"❌ Process improvement failed: {result.get('error', 'Unknown error')}"
        
        comparison = self.compare_iterations(result)
        
        report = f"""
🔄 RAPORT ITERACYJNYCH ULEPSZEŃ
{'='*50}

📋 Proces: {result['process_name']}
⏰ Data: {result['timestamp'][:19]}
🎯 Docelowa jakość: {self.target_quality}

📊 WYNIKI:
   Finalna jakość: {result['final_quality']:.2f}
   Iteracji wykonano: {comparison['iteration_count']}
   Łączne zmiany: {comparison['total_changes']}
   
📈 PROGRESJA JAKOŚCI:
"""
        
        for prog in comparison['quality_progression']:
            report += f"   Iteracja {prog['iteration']}: {prog['quality']:.2f} ({prog['type']})\n"
        
        if comparison.get('quality_improvement'):
            report += f"\n📈 Poprawa jakości: +{comparison['quality_improvement']:.2f}\n"
        
        if comparison['improvements_timeline']:
            report += f"\n🔧 ZASTOSOWANE ZMIANY:\n"
            for timeline in comparison['improvements_timeline']:
                report += f"   Iteracja {timeline['iteration']}:\n"
                for change in timeline['changes']:
                    report += f"     - {change}\n"
        
        final_verification = result.get('final_verification', {})
        if final_verification.get('missing_elements'):
            report += f"\n⚠️ POZOSTAŁE BRAKI:\n"
            for missing in final_verification['missing_elements']:
                report += f"   - {missing}\n"
        
        if final_verification.get('improvement_suggestions'):
            report += f"\n💡 DALSZE SUGESTIE:\n"
            for suggestion in final_verification['improvement_suggestions'][:3]:
                report += f"   - {suggestion}\n"
        
        return report


def test_iterative_pipeline():
    """Test iteracyjnego pipeline"""
    print("🧪 Testing Iterative Improvement Pipeline")
    
    # Create pipeline with Mock AI
    pipeline = IterativeImprovementPipeline(
        ai_config=None,  # Will use default from env
        max_iterations=2,
        target_quality=0.7
    )
    
    # Test with simple Polish text
    test_text = """
    Klient loguje się do systemu bankowego.
    Sprawdza swoje saldo.
    Jeśli saldo jest wystarczające, wykonuje przelew.
    System potwierdza operację.
    """
    
    result = pipeline.generate_and_improve_process(
        polish_text=test_text,
        process_name="Test Banking Process",
        context="banking"
    )
    
    # Generate report
    if result['success']:
        report = pipeline.generate_improvement_report(result)
        print(report)
        
        return True
    else:
        print(f"❌ Test failed: {result.get('error')}")
        return False


if __name__ == "__main__":
    success = test_iterative_pipeline()
    print(f"\n🎯 Iterative Pipeline test: {'✅ PASSED' if success else '❌ FAILED'}")