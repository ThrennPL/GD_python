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

from .complete_pipeline import BPMNv2Pipeline
from .mcp_server_simple import SimpleMCPServer
from .ai_config import get_default_config


class IterativeImprovementPipeline:
    """Pipeline z iteracyjną poprawą procesów BPMN"""
    
    def __init__(self, ai_config=None, max_iterations=10, target_quality=0.65):
        # Use the same config for both pipelines
        config = ai_config or get_default_config()
        self.pipeline = BPMNv2Pipeline(config)
        self.mcp_server = SimpleMCPServer(ai_config=config)  # Pass the same config!
        self.max_iterations = min(max_iterations, 10)  # Limit to 10 for performance
        self.target_quality = target_quality
        
        # Tracking naprawionych kategorii 
        self.fixed_categories = set()  # Kategorie które już zostały naprawione
        self.current_iteration_category = None  # Aktualna kategoria w naprawie
        
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
        
        # Extract original business requirements for preservation
        original_participants = self._extract_participants_from_text(polish_text)
        original_tasks = self._extract_business_activities_from_text(polish_text)
        
        result = {
            'process_name': process_name,
            'original_text': polish_text,
            'original_participants_count': len(original_participants),
            'original_business_activities': original_tasks,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'iterations': [],
            'final_process': None,
            'final_bpmn_xml': None,
            'success': False,
            'total_improvements': 0,
            'fixed_categories': [],  # Tracking naprawionych kategorii
            'category_progression': []  # Historia kategorii
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
            
            # Verify initial process with original participants count
            initial_verification = self.mcp_server.verify_bpmn_process(current_process, result['original_participants_count'])
            
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
                    verification = self.mcp_server.verify_bpmn_process(current_process, result['original_participants_count'])
                    iteration_result['verification'] = verification
                    iteration_result['quality_score'] = verification['overall_quality']
                    
                    print(f"📊 Jakość procesu: {verification['overall_quality']:.2f}")
                    print(f"📋 Braki: {len(verification['missing_elements'])}")
                    print(f"💡 Sugestie: {len(verification['improvement_suggestions'])}")
                    
                    # SZCZEGÓŁOWY DEBUGGING - co dokładnie wykryto
                    if verification['missing_elements']:
                        print(f"🔍 DETECTED MISSING ELEMENTS:")
                        for i, missing in enumerate(verification['missing_elements'][:5]):
                            print(f"   {i+1}. {missing}")
                    
                    if verification['improvement_suggestions']:
                        print(f"🔍 DETECTED IMPROVEMENT SUGGESTIONS:")
                        for i, suggestion in enumerate(verification['improvement_suggestions'][:5]):
                            print(f"   {i+1}. {suggestion}")
                    
                    # Sprawdź compliance issues details
                    bpmn_compliance = verification.get('bpmn_compliance', {})
                    if bpmn_compliance.get('issues'):
                        critical_issues = [i for i in bpmn_compliance['issues'] if i['severity'] == 'critical']
                        major_issues = [i for i in bpmn_compliance['issues'] if i['severity'] == 'major']
                        print(f"🔍 BPMN COMPLIANCE ISSUES:")
                        print(f"   Critical: {len(critical_issues)}, Major: {len(major_issues)}")
                        
                        if critical_issues:
                            print(f"   Critical details:")
                            for issue in critical_issues[:3]:
                                print(f"      - {issue['rule_code']}: {issue['message']}")
                    
                    # DEBUG: Sprawdzenie szczegółów verification (komunikaty wyłączone)
                    
                    # Initialize changes tracking for this iteration
                    changes = []
                    
                    # Create new iteration result for this iteration
                    current_iteration_result = {
                        'iteration': iteration,
                        'type': 'verification_and_improvement',
                        'process': current_process,
                        'verification': verification,
                        'improvements_applied': [],
                        'quality_score': verification['overall_quality']
                    }
                    
                    # Check AI quota conservation
                    if hasattr(self.mcp_server, 'ai_calls_count') and self.mcp_server.ai_calls_count >= self.mcp_server.ai_calls_limit:
                        print(f"⚠️ AI quota limit reached ({self.mcp_server.ai_calls_count}/{self.mcp_server.ai_calls_limit})")
                        current_iteration_result['type'] = 'quota_limit_reached'
                        result['iterations'].append(current_iteration_result)
                        break
                    
                    # Check if we've reached target quality but preserve business value
                    business_completeness = self._check_business_completeness(current_process, result.get('original_participants_count', 0))
                    if verification['overall_quality'] >= self.target_quality and business_completeness >= 0.7:
                        print(f"🎯 Osiągnięto docelową jakość! ({verification['overall_quality']:.2f}) z zachowaniem wartości biznesowej ({business_completeness:.2f})")
                        current_iteration_result['type'] = 'target_reached'
                        result['iterations'].append(current_iteration_result)
                        break
                    elif verification['overall_quality'] >= self.target_quality:
                        print(f"⚠️ Wysoka jakość ({verification['overall_quality']:.2f}) ale strata wartości biznesowej ({business_completeness:.2f}) - kontynuowanie...")
                
                    # ENHANCED STOPPING CRITERIA - Progressive quality improvement
                    critical_issues = [i for i in verification.get('bpmn_compliance', {}).get('issues', []) if i.get('severity') == 'critical']
                    major_issues = [i for i in verification.get('bpmn_compliance', {}).get('issues', []) if i.get('severity') == 'major']
                    
                    # Progressive quality thresholds based on iteration
                    quality_threshold = max(0.6, self.target_quality - (iteration * 0.05))  # Gradually lower expectations
                    
                    should_improve = (
                        verification['overall_quality'] < quality_threshold and
                        (critical_issues or  # Always fix critical issues
                         (major_issues and verification['overall_quality'] < 0.7) or  # Fix major issues if quality low
                         (verification['missing_elements'] and iteration < 5) or  # Fix missing elements early
                         verification['overall_quality'] < 0.4)  # Emergency improvement for very poor quality
                    )
                    
                    print(f"🎯 Quality: {verification['overall_quality']:.2f}, Threshold: {quality_threshold:.2f}")
                    print(f"🔍 Critical: {len(critical_issues)}, Major: {len(major_issues)}, Should improve: {should_improve}")
                    
                    # DEBUGGING should_improve logic
                    print(f"🔍 Should improve analysis:")
                    print(f"   Quality: {verification['overall_quality']:.3f} < {self.target_quality} = {verification['overall_quality'] < self.target_quality}")
                    print(f"   Missing elements: {len(verification['missing_elements'])} (bool: {bool(verification['missing_elements'])})")
                    print(f"   Improvement suggestions: {len(verification['improvement_suggestions'])} (bool: {bool(verification['improvement_suggestions'])})")
                    print(f"   Very low quality: {verification['overall_quality']:.3f} < 0.5 = {verification['overall_quality'] < 0.5}")
                    print(f"   Should improve: {should_improve}")
                    
                    if should_improve:
                        print(f"🔧 Aplikowanie ulepszeń...")
                        
                        # Weryfikuj poprawność obecnego procesu przed AI improvement
                        if not self._validate_process_structure(current_process):
                            print("⚠️ Proces ma nieprawidłową strukturę - pomijam AI improvement")
                            current_iteration_result['type'] = 'skipped_invalid_process'
                            result['iterations'].append(current_iteration_result)
                            continue
                        
                        # NOWA LOGIKA: Progresywne naprawianie kategorii błędów
                        bpmn_compliance = verification.get('bpmn_compliance', {})
                        all_issues = bpmn_compliance.get('issues', [])
                        
                        # Podziel na severity levels
                        critical_issues = [i for i in all_issues if i['severity'] == 'critical']
                        major_issues = [i for i in all_issues if i['severity'] == 'major']
                        minor_issues = [i for i in all_issues if i['severity'] == 'minor']
                        
                        # Określ focus na podstawie dostępnych issues i tracking
                        focus_severity = None
                        if critical_issues:
                            focus_severity = 'critical'
                            print(f"🎯 FOCUS: CRITICAL issues ({len(critical_issues)})")
                        elif major_issues:
                            focus_severity = 'major'
                            print(f"🎯 FOCUS: MAJOR issues ({len(major_issues)})")
                        elif minor_issues:
                            focus_severity = 'minor' 
                            print(f"🎯 FOCUS: MINOR issues ({len(minor_issues)})")
                        else:
                            print(f"🎯 FOCUS: General improvement")
                        
                        # Dodaj informację o już naprawionych kategoriach do kontekstu
                        fixed_categories_info = f"Fixed categories: {[cat for cat in self.fixed_categories]}" if self.fixed_categories else "No categories fixed yet"
                        
                        # Generate improvement prompt z informacją o kategoriach
                        improvement_prompt = self.mcp_server.generate_improvement_prompt(
                            current_process, verification, focus_severity, 
                            fixed_categories_info=fixed_categories_info
                        )
                        
                        # Get AI to improve the process
                        print(f"📝 Wywołuję AI z prompt długości: {len(improvement_prompt)}")
                        ai_response = self.pipeline.ai_client.generate_response(improvement_prompt)
                        
                        if ai_response.success:
                            print(f"✅ AI response received - length: {len(str(ai_response.content))}")
                            # Parse improved process
                            json_success, improved_process, parse_errors = self.pipeline.response_parser.extract_json(ai_response)
                            
                            if json_success:
                                print(f"✅ JSON parse success - elements: {len(improved_process.get('elements', []))}")
                                
                                # Porównaj proces przed i po AI improvement
                                old_elements_count = len(current_process.get('elements', []))
                                new_elements_count = len(improved_process.get('elements', []))
                                old_flows_count = len(current_process.get('flows', []))
                                new_flows_count = len(improved_process.get('flows', []))
                                
                                print(f"🔄 Porównanie przed/po AI:")
                                print(f"   Elements: {old_elements_count} → {new_elements_count}")
                                print(f"   Flows: {old_flows_count} → {new_flows_count}")
                                
                                # Check if AI actually made changes
                                old_json_str = json.dumps(current_process, sort_keys=True)
                                new_json_str = json.dumps(improved_process, sort_keys=True)
                                if old_json_str == new_json_str:
                                    print("⚠️ WARNING: AI returned identical process - no changes made")
                                else:
                                    print("✅ AI made structural changes to the process")
                                
                                # NOWY TRACKING: Sprawdź czy konkretne issues zostały naprawione
                                verification_before = verification  # Issues przed AI improvement
                                # Use improved process from AI directly
                                current_process = improved_process
                                
                                # Update changes tracking
                                changes.append(f"AI improved process structure")
                                
                                # Weryfikuj nowy proces aby sprawdzić czy issues zostały naprawione
                                verification_after = self.mcp_server.verify_bpmn_process(current_process, result['original_participants_count'])
                                
                                # Jeśli nadal są critical issues które AI nie naprawiło, spróbuj auto-fix
                                critical_issues_after = [i for i in verification_after.get('bpmn_compliance', {}).get('issues', []) 
                                                       if i['severity'] == 'critical' and i.get('auto_fixable', False)]
                                
                                if critical_issues_after:
                                    print(f"🔧 AI left {len(critical_issues_after)} critical issues. Trying auto-fix...")
                                    auto_improvements = self.mcp_server.improve_bpmn_process(current_process)
                                    if auto_improvements['success'] and auto_improvements['improvements_made'] > 0:
                                        current_process = auto_improvements['improved_process']
                                        verification_after = self.mcp_server.verify_bpmn_process(current_process, result['original_participants_count'])
                                        changes.extend(auto_improvements['changes_made'])
                                        print(f"✅ Auto-fix applied {auto_improvements['improvements_made']} additional fixes")
                                
                                # Porównaj issues before/after
                                issues_before = set()
                                issues_after = set()
                                
                                if verification_before.get('bpmn_compliance', {}).get('issues'):
                                    for issue in verification_before['bpmn_compliance']['issues']:
                                        issues_before.add(f"{issue['rule_code']}_{issue['element_id']}")
                                
                                if verification_after.get('bpmn_compliance', {}).get('issues'):
                                    for issue in verification_after['bpmn_compliance']['issues']:
                                        issues_after.add(f"{issue['rule_code']}_{issue['element_id']}")
                                
                                fixed_issues = issues_before - issues_after
                                new_issues = issues_after - issues_before
                                persistent_issues = issues_before & issues_after
                                
                                print(f"🔧 TRACKING NAPRAW:")
                                print(f"   ✅ Naprawione issues: {len(fixed_issues)}")
                                if fixed_issues:
                                    for issue in list(fixed_issues)[:3]:
                                        print(f"      - {issue}")
                                print(f"   🆕 Nowe issues: {len(new_issues)}")
                                if new_issues:
                                    for issue in list(new_issues)[:3]:
                                        print(f"      - {issue}")
                                print(f"   ⚠️ Nienaprawione issues: {len(persistent_issues)}")
                                if persistent_issues:
                                    for issue in list(persistent_issues)[:3]:
                                        print(f"      - {issue}")
                                
                                # TRACKING: Sprawdź jaką kategorię naprawiono
                                if hasattr(self.mcp_server, 'current_iteration_category') and self.mcp_server.current_iteration_category:
                                    fixed_category = self.mcp_server.current_iteration_category
                                    if fixed_category not in self.fixed_categories:
                                        self.fixed_categories.add(fixed_category)
                                        result['fixed_categories'].append(fixed_category.value)
                                        result['category_progression'].append({
                                            'iteration': iteration,
                                            'category': fixed_category.value,
                                            'issues_fixed': len(fixed_issues),
                                            'quality_improvement': verification_after['overall_quality'] - verification_before['overall_quality']
                                        })
                                        print(f"✅ Naprawiono kategorię: {fixed_category.value}")
                                
                                # Apply only light auto-fix for critical issues
                                verification_check = self.mcp_server.verify_bpmn_process(current_process, result['original_participants_count'])
                                critical_issues = [i for i in verification_check.get('improvement_suggestions', []) 
                                                 if 'CRITICAL' in str(i)]
                                
                                # Update changes list instead of redefining
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
                                print(f"🔧 Trying automatic BPMN fixes...")
                                auto_improvements = self.mcp_server.improve_bpmn_process(current_process)
                                if auto_improvements['success'] and auto_improvements['improvements_made'] > 0:
                                    current_process = auto_improvements['improved_process']
                                    current_iteration_result['improvements_applied'] = auto_improvements['changes_made']
                                    current_iteration_result['type'] = 'automatic_improvement_ai_failed'
                                    print(f"✅ Applied {auto_improvements['improvements_made']} automatic fixes")
                                else:
                                    print(f"❌ No automatic fixes available")
                                    current_iteration_result['type'] = 'no_improvements_possible'
                        else:
                            print(f"❌ AI call failed: {ai_response.error}")
                            # Fall back to automatic improvements
                            print(f"🔧 Trying automatic BPMN fixes...")
                            auto_improvements = self.mcp_server.improve_bpmn_process(current_process)
                            if auto_improvements['success'] and auto_improvements['improvements_made'] > 0:
                                current_process = auto_improvements['improved_process']
                                current_iteration_result['improvements_applied'] = auto_improvements['changes_made']
                                current_iteration_result['type'] = 'automatic_improvement_ai_failed'
                                print(f"✅ Applied {auto_improvements['improvements_made']} automatic fixes")
                            else:
                                print(f"❌ No automatic fixes available")
                                current_iteration_result['type'] = 'no_improvements_possible'
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
                final_verification = self.mcp_server.verify_bpmn_process(current_process, result['original_participants_count'])
                
                # DEBUG: Check if final process has required structure (wyłączone)
                # print(f"\n🔍 DEBUGGING FINALNY PROCES:")
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
                    try:
                        final_bpmn_xml = self.pipeline.convert_json_to_bpmn(current_process)
                        print(f"🔧 Final XML length: {len(final_bpmn_xml) if final_bpmn_xml else 0}")
                    except Exception as e:
                        print(f"⚠️ WARNING: Błąd konwersji JSON→XML: {e}")
                        # Fallback do początkowego procesu
                        if result['iterations'] and result['iterations'][0].get('process'):
                            print(f"🔧 Using initial process as fallback...")
                            try:
                                final_bpmn_xml = self.pipeline.convert_json_to_bpmn(result['iterations'][0]['process'])
                                current_process = result['iterations'][0]['process']
                                final_verification = result['iterations'][0]['verification']
                                print(f"🔧 Fallback XML length: {len(final_bpmn_xml) if final_bpmn_xml else 0}")
                            except Exception as e2:
                                print(f"❌ CRITICAL: Nawet fallback nie działa: {e2}")
                                final_bpmn_xml = None
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
    
    def _validate_process_structure(self, process: Dict) -> bool:
        """Weryfikuje czy proces ma poprawną strukturę przed konwersją"""
        if not process or not isinstance(process, dict):
            return False
            
        # Sprawdź czy ma wymagane klucze
        if not all(key in process for key in ['elements', 'participants']):
            return False
            
        elements = process.get('elements', [])
        participants = process.get('participants', [])
        
        # Sprawdź czy są jakieś elementy i uczestnicy
        if not elements or not participants:
            return False
            
        # Sprawdź czy wszystkie elementy mają prawidłowe participant ID
        participant_ids = {p.get('id') for p in participants if p.get('id')}
        for element in elements:
            element_participant = element.get('participant')
            if not element_participant or element_participant not in participant_ids:
                print(f"❌ Element {element.get('id')} ma nieprawidłowy participant: {element_participant}")
                return False
                
        return True
    
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
                'type': iteration.get('type', 'unknown')
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
            prog_type = prog.get('type', 'unknown')
            report += f"   Iteracja {prog['iteration']}: {prog['quality']:.2f} ({prog_type})\n"
        
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
    
    def _validate_process_structure(self, process: Dict) -> bool:
        """Weryfikuje czy proces ma poprawną strukturę przed konwersją"""
        if not process or not isinstance(process, dict):
            return False
            
        # Sprawdź czy ma wymagane klucze
        if not all(key in process for key in ['elements', 'participants']):
            return False
            
        elements = process.get('elements', [])
        participants = process.get('participants', [])
        
        # Sprawdź czy są jakieś elementy i uczestnicy
        if not elements or not participants:
            return False
            
        # Sprawdź czy wszystkie elementy mają prawid\u0142owe participant ID
        participant_ids = {p.get('id') for p in participants if p.get('id')}
        for element in elements:
            element_participant = element.get('participant')
            if not element_participant or element_participant not in participant_ids:
                print(f"❌ Element {element.get('id')} ma nieprawid\u0142owy participant: {element_participant}")
                return False
                
        return True

    def _extract_participants_from_text(self, polish_text: str) -> List[str]:
        """Wyciąga uczestników z polskiego opisu procesu"""
        import re
        participants = []
        
        # Patterns for common participant mentions
        patterns = [
            r'(?:uczestnicy:|participants:)([^:]+?)(?:regulacje:|$)',
            r'(klient|doradca|analityk|kierownik|komitet|system|bik)',
        ]
        
        text_lower = polish_text.lower()
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                # Split and clean
                parts = re.split(r'[-,\n\r]', match)
                for part in parts:
                    clean_part = part.strip().strip('*-').strip()
                    if clean_part and len(clean_part) > 2:
                        participants.append(clean_part)
        
        # Remove duplicates and return
        return list(set(participants))
    
    def _extract_business_activities_from_text(self, polish_text: str) -> List[str]:
        """Wyciąga kluczowe aktywności biznesowe z opisu"""
        import re
        activities = []
        
        # Common business activity indicators
        activity_patterns = [
            r'(składa|przeprowadza|weryfikuje|sprawdza|ocenia|akceptuje|podejmuje|otrzymuje|podpisuje|wypłaca)',
            r'(wniosek|scoring|wywiad|kalkulacja|decyzja|oferta|umowa|środki)'
        ]
        
        sentences = re.split(r'[.!?]\s*', polish_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Meaningful sentences
                for pattern in activity_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        activities.append(sentence[:50] + "..." if len(sentence) > 50 else sentence)
                        break
        
        return activities[:10]  # Max 10 key activities
    
    def _check_business_completeness(self, current_process: Dict, original_participants_count: int) -> float:
        """Sprawdza czy proces zachował wartość biznesową"""
        if not current_process:
            return 0.0
        
        score = 0.0
        max_score = 0.0
        
        # 1. Participant preservation (40% weight)
        current_participants = len(current_process.get('participants', []))
        if original_participants_count > 0:
            participant_ratio = min(1.0, current_participants / original_participants_count)
            score += participant_ratio * 0.4
        max_score += 0.4
        
        # 2. Activity preservation (40% weight)
        current_activities = len([e for e in current_process.get('elements', []) 
                                if 'task' in e.get('type', '').lower()])
        if current_activities >= 3:  # Minimum meaningful activities
            score += min(0.4, current_activities * 0.1)
        max_score += 0.4
        
        # 3. Structural complexity (20% weight)
        current_elements = len(current_process.get('elements', []))
        if current_elements >= 5:  # More than just Start->End
            complexity_score = min(0.2, (current_elements - 2) * 0.05)
            score += complexity_score
        max_score += 0.2
        
        return score / max_score if max_score > 0 else 0.0


def test_iterative_pipeline():
    """Test iteracyjnego pipeline"""
    print("🧪 Testing Iterative Improvement Pipeline")
    
    # Create pipeline with Mock AI
    pipeline = IterativeImprovementPipeline(
        ai_config=None,  # Will use default from env
        max_iterations=2,
        target_quality=0.65
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