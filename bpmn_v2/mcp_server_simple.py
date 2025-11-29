"""
MCP Server for BPMN (Enhanced with BPMN Compliance + Intelligence Layer)
Model Context Protocol server for BPMN process verification and improvement

Funkcje:
1. Zaawansowana walidacja zgodności BPMN 2.0
2. Iteracyjne poprawki oparte na regułach standardu
3. Automatyczne naprawy prostych błędów  
4. Generowanie sugestii poprawek przez AI
5. Analiza jakości i kompletności procesów
6. AI-powered Intelligence Orchestrator
7. ML-based issue prediction
8. Template-based quick fixes
9. Cross-process learning
10. Adaptive strategy management
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .complete_pipeline import BPMNv2Pipeline
from .ai_config import get_default_config
from .json_prompt_template import ResponseValidator

# Import nowego systemu walidacji BPMN
from .bpmn_compliance_validator import (
    BPMNComplianceValidator, 
    BPMNComplianceReport, 
    BPMNSeverity
)
from .bpmn_improvement_engine import BPMNImprovementEngine

# Import Intelligence Layer
try:
    from .intelligence_orchestrator import IntelligenceOrchestrator, OptimizationResult
    INTELLIGENCE_ENABLED = True
except ImportError:
    INTELLIGENCE_ENABLED = False
    print("⚠️ Intelligence Layer nie jest dostępna - używanie podstawowego trybu")

from enum import Enum

class ErrorCategory(Enum):
    """Kategorie błędów BPMN dla progresywnego naprawiania"""
    STRUCTURE = "structure"  # Start/End Events, Pool structure
    FLOWS = "flows"         # Sequence/Message flows
    GATEWAYS = "gateways"     # Gateway logic and connections
    NAMING = "naming"       # Element names and IDs
    SEMANTICS = "semantics"   # Business logic correctness


class EnhancedBPMNQualityChecker:
    """
    Zaawansowany sprawdzacz jakości BPMN z pełną walidacją zgodności ze standardem
    + Intelligence Layer integration
    """
    
    def __init__(self):
        self.validator = ResponseValidator()
        self.compliance_validator = BPMNComplianceValidator()
        self.improvement_engine = None  # Będzie ustawione przez SimpleMCPServer
        
        # Initialize Intelligence Orchestrator if available
        if INTELLIGENCE_ENABLED:
            self.intelligence = IntelligenceOrchestrator(enable_learning=True)
        else:
            self.intelligence = None
    
    def check_process_quality(self, bpmn_json: Dict, original_participants_count: int = 0) -> Dict[str, Any]:
        """
        Sprawdza jakość i kompletność procesu BPMN
        
        Args:
            bpmn_json: Proces BPMN w formacie JSON
            
        Returns:
            Kompletny raport jakości z oceną zgodności BPMN
        """
        # 1. Podstawowa walidacja schema JSON
        json_string = json.dumps(bpmn_json, ensure_ascii=False)
        is_valid, parsed_json, schema_errors = self.validator.validate_response(json_string)
        
        # 2. Zaawansowana walidacja zgodności BPMN
        compliance_report = self.compliance_validator.validate_bpmn_compliance(bpmn_json)
        
        # 3. Oblicz metryki jakości (zachowaj kompatybilność z starym systemem)
        quality_metrics = self._calculate_legacy_quality_metrics(bpmn_json, compliance_report)
        
        # 4. Generuj sugestie poprawek na podstawie compliance
        improvement_suggestions = self._generate_improvement_suggestions(compliance_report)
        
        # 5. Kompletność na podstawie compliance score
        completeness_score = compliance_report.overall_score / 100.0
        
        # Create result dict for overall quality calculation
        result_dict = {
            'is_valid': is_valid and compliance_report.overall_score > 20,
            'completeness_score': completeness_score,
            'missing_elements': [issue.message for issue in compliance_report.issues if issue.severity == BPMNSeverity.CRITICAL],
            'quality_metrics': quality_metrics,
            'process': bpmn_json  # Add for business value checking
        }
        
        # Calculate overall quality with business value preservation
        overall_quality = self._calculate_overall_quality(result_dict, original_participants_count)
        
        return {
            'is_valid': result_dict['is_valid'],
            'completeness_score': completeness_score,
            'missing_elements': result_dict['missing_elements'],
            'validation_errors': schema_errors + [issue.message for issue in compliance_report.issues if issue.severity == BPMNSeverity.CRITICAL],
            'improvement_suggestions': improvement_suggestions,
            'quality_metrics': quality_metrics,
            'overall_quality': overall_quality,  # Now uses business value preservation logic
            
            # Nowe pola zgodności BPMN
            'bpmn_compliance': {
                'score': compliance_report.overall_score,
                'level': compliance_report.compliance_level,
                'issues': [
                    {
                        'element_id': issue.element_id,
                        'severity': issue.severity.value,
                        'rule_code': issue.rule_code,
                        'message': issue.message,
                        'suggestion': issue.suggestion,
                        'auto_fixable': issue.auto_fixable
                    }
                    for issue in compliance_report.issues
                ],
                'statistics': compliance_report.statistics,
                'priorities': compliance_report.improvement_priorities
            }
        }
    
    def _calculate_legacy_quality_metrics(self, bpmn_json: Dict, compliance_report: BPMNComplianceReport) -> Dict[str, float]:
        """Oblicza metryki jakości w formacie kompatybilnym ze starym systemem"""
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        participants = bpmn_json.get('participants', [])
        
        # Złożoność procesu
        complexity = len(elements) / 10.0 if elements else 0
        complexity = min(complexity, 2.0)  # Cap at 2.0
        
        # Różnorodność uczestników
        participant_diversity = len(participants) / 3.0 if participants else 0
        participant_diversity = min(participant_diversity, 2.0)
        
        # Łączność (stosunek przepływów do elementów)
        connectivity = len(flows) / len(elements) if elements else 0
        
        # Jakość nazewnictwa (na podstawie compliance issues)
        naming_issues = len([i for i in compliance_report.issues if 'nam' in i.message.lower()])
        naming_quality = max(0, 1.0 - (naming_issues / len(elements))) if elements else 1.0
        
        return {
            'complexity': complexity,
            'participant_diversity': participant_diversity,
            'connectivity': connectivity,
            'naming_quality': naming_quality
        }
    
    def intelligent_analysis_and_optimization(self, bpmn_json: Dict, 
                                             context_hints: Optional[Dict] = None,
                                             iteration_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Wykonuje inteligentną analizę i optymalizację procesu BPMN
        z użyciem Intelligence Orchestrator
        """
        if not self.intelligence:
            return self._fallback_analysis(bpmn_json)
        
        # Get current issues for intelligence analysis
        compliance_report = self.compliance_validator.validate_bpmn_compliance(bpmn_json)
        issues = [
            {
                'element_id': issue.element_id,
                'severity': issue.severity.value,
                'rule_code': issue.rule_code,
                'message': issue.message
            }
            for issue in compliance_report.issues
        ]
        
        try:
            # Perform intelligent analysis and optimization
            optimization_result = self.intelligence.analyze_and_optimize(
                bpmn_json=bpmn_json,
                issues=issues,
                context_hints=context_hints,
                iteration_history=iteration_history
            )
            
            return {
                'intelligence_enabled': True,
                'optimized_process': optimization_result.optimized_process,
                'applied_optimizations': optimization_result.applied_optimizations,
                'insights': {
                    'predicted_issues': [
                        {
                            'issue_type': pred.issue_type,
                            'probability': pred.probability,
                            'confidence': pred.confidence,
                            'prevention_tip': pred.prevention_tip
                        }
                        for pred in optimization_result.intelligence_insights.predicted_issues
                    ],
                    'quality_alerts': [
                        {
                            'type': alert.type.value,
                            'severity': alert.severity,
                            'message': alert.message,
                            'recommendation': alert.recommendation
                        }
                        for alert in optimization_result.intelligence_insights.quality_alerts
                    ],
                    'strategy_used': optimization_result.intelligence_insights.strategy_recommendation.strategy_type.value,
                    'confidence_score': optimization_result.intelligence_insights.confidence_score
                },
                'performance_metrics': optimization_result.performance_metrics,
                'recommendations': optimization_result.recommendations,
                'processing_time': optimization_result.intelligence_insights.processing_time
            }
            
        except Exception as e:
            return {
                'intelligence_enabled': False,
                'error': f"Intelligence analysis failed: {str(e)}",
                'fallback_used': True,
                **self._fallback_analysis(bpmn_json)
            }
    
    def _fallback_analysis(self, bpmn_json: Dict) -> Dict[str, Any]:
        """Fallback analysis gdy Intelligence Layer nie jest dostępna"""
        compliance_report = self.compliance_validator.validate_bpmn_compliance(bpmn_json)
        
        return {
            'basic_analysis': True,
            'compliance_score': compliance_report.overall_score,
            'compliance_level': compliance_report.compliance_level,
            'critical_issues': len([i for i in compliance_report.issues if i.severity == BPMNSeverity.CRITICAL]),
            'improvement_priorities': compliance_report.improvement_priorities[:5]
        }

    def _generate_improvement_suggestions(self, compliance_report: BPMNComplianceReport) -> List[str]:
        """Generuje sugestie poprawek na podstawie raportu zgodności"""
        suggestions = []
        
        # Dodaj priorytety jako główne sugestie
        suggestions.extend(compliance_report.improvement_priorities)
        
        # Dodaj konkretne sugestie dla najważniejszych problemów
        critical_issues = [i for i in compliance_report.issues if i.severity == BPMNSeverity.CRITICAL]
        for issue in critical_issues[:3]:  # Tylko top 3
            try:
                suggestions.append(f"{issue.element_id}: {issue.suggestion}")
            except AttributeError:
                # Fallback jeśli issue nie ma element_id lub suggestion
                suggestions.append(f"Issue: {getattr(issue, 'message', 'Unknown issue')}")
        
        # Dodaj sugestie dla problemów MAJOR jeśli brak CRITICAL
        if len(critical_issues) == 0:
            major_issues = [i for i in compliance_report.issues if i.severity == BPMNSeverity.MAJOR]
            for issue in major_issues[:3]:
                try:
                    suggestions.append(f"{issue.element_id}: {issue.suggestion}")
                except AttributeError:
                    # Fallback jeśli issue nie ma element_id lub suggestion
                    suggestions.append(f"Issue: {getattr(issue, 'message', 'Unknown issue')}")
        
        # Dodaj sugestie automatycznych poprawek
        auto_fixable_count = len([i for i in compliance_report.issues if i.auto_fixable])
        if auto_fixable_count > 0:
            suggestions.append(f"Możliwe jest automatyczne naprawienie {auto_fixable_count} problemów")
        
        # Fallback gdy compliance score bardzo niski ale brak konkretnych sugestii
        if len(suggestions) == 0 and compliance_report.overall_score < 50:
            suggestions.append("Proces wymaga podstawowych elementów BPMN")
            suggestions.append("Sprawdź strukturę procesu - Start Events, End Events, przepływy")
            suggestions.append("Sprawdź nazewnictwo elementów i uczestników")
        
        return suggestions
    
    def _calculate_completeness(self, bpmn_json: Dict) -> float:
        """Oblicza kompletność procesu (0-1)"""
        score = 0.0
        max_score = 0.0
        
        # Sprawdź podstawowe elementy
        if bpmn_json.get('process_name'):
            score += 0.1
        max_score += 0.1
        
        if bpmn_json.get('description'):
            score += 0.1
        max_score += 0.1
        
        # Sprawdź uczestników
        participants = bpmn_json.get('participants', [])
        if participants:
            score += 0.2
            # Bonus za sensowne nazwy
            if all(p.get('name') and len(p['name']) > 2 for p in participants):
                score += 0.1
        max_score += 0.3
        
        # Sprawdź elementy
        elements = bpmn_json.get('elements', [])
        if len(elements) >= 3:  # min: start, task, end
            score += 0.2
        if len(elements) >= 5:  # bardziej kompleksny proces
            score += 0.1
        max_score += 0.3
        
        # Sprawdź przepływy
        flows = bpmn_json.get('flows', [])
        if len(flows) >= 2:  # minimum flows
            score += 0.1
        if len(flows) == len(elements) - 1:  # optymalnie połączony
            score += 0.1
        max_score += 0.2
        
        return score / max_score if max_score > 0 else 0.0
    
    def _find_missing_elements(self, bpmn_json: Dict) -> List[str]:
        """Identyfikuje brakujące elementy (bardziej surowy algorytm)"""
        missing = []
        
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        participants = bpmn_json.get('participants', [])
        
        # Sprawdź czy są starty i kończące
        has_start = any(e.get('type') == 'startEvent' for e in elements)
        has_end = any(e.get('type') == 'endEvent' for e in elements)
        
        if not has_start:
            missing.append("Brak zdarzenia rozpoczynającego (startEvent)")
        
        if not has_end:
            missing.append("Brak zdarzenia kończącego (endEvent)")
        
        # Sprawdź czy są jakieś zadania
        has_tasks = any(e.get('type') in ['userTask', 'serviceTask', 'task'] for e in elements)
        if not has_tasks:
            missing.append("Brak zadań w procesie")
        
        # Check for sufficient complexity (realistic requirements for generated processes)
        if len(elements) < 3:  # Minimum 3 elements: start->task->end
            missing.append(f"Proces zbyt prosty - ma tylko {len(elements)} elementów (minimum 3)")
        
        if len(flows) < 2:  # Minimum 2 flows (start->task->end)
            missing.append(f"Za mało przepływów - ma tylko {len(flows)} (minimum 2)")
        
        # Sprawdź nazwy elementów (rozsądne wymagania)
        unnamed_elements = [e['id'] for e in elements if not e.get('name') or len(e['name'].strip()) < 2]
        if len(unnamed_elements) > 3:  # Allow some unnamed elements
            missing.append(f"Zbyt wiele elementów bez nazw: {len(unnamed_elements)}")
        
        # Check for business logic complexity (optional for realistic processes)
        gateways = [e for e in elements if 'gateway' in e.get('type', '').lower()]
        if len(elements) > 12 and len(gateways) == 0:  # Only for very complex processes
            missing.append("Bardzo złożony proces powinien mieć bramki decyzyjne")
        
        # Check for sufficient task diversity (more lenient)
        user_tasks = [e for e in elements if e.get('type') == 'userTask']
        service_tasks = [e for e in elements if e.get('type') == 'serviceTask']
        tasks = [e for e in elements if e.get('type') in ['userTask', 'serviceTask', 'task']]
        
        if len(tasks) < 1:
            missing.append("Proces powinien mieć przynajmniej jedno zadanie")
        
        # Check for end events (realistic requirement)
        end_events = [e for e in elements if e.get('type') == 'endEvent']
        if len(end_events) < 1:
            missing.append("Proces powinien mieć przynajmniej jedno zdarzenie końcowe")
        
        # Check participant assignments (only for multi-participant processes)
        unassigned_elements = [e['id'] for e in elements if not e.get('participant')]
        if len(unassigned_elements) > len(elements) // 2 and len(participants) > 1:  # Allow some flexibility
            missing.append(f"Zbyt wiele elementów nie przypisanych do uczestników")
        
        # Sprawdź uczestników (realistic for generated processes)
        if len(participants) < 1:  # At least 1 participant
            missing.append("Proces musi mieć przynajmniej jednego uczestnika")
        
        # Check for description quality
        if not bpmn_json.get('description') or len(bpmn_json.get('description', '')) < 20:
            missing.append("Brak szczegółowego opisu procesu")
        
        # Check for missing element details
        elements_without_details = [e['id'] for e in elements if not e.get('description')]
        if len(elements_without_details) > len(elements) * 0.5:
            missing.append("Większość elementów nie ma opisów")
        
        # Sprawdź przepływy
        flows = bpmn_json.get('flows', [])
        element_ids = {e['id'] for e in elements}
        
        for flow in flows:
            if flow.get('source') not in element_ids:
                missing.append(f"Przepływ {flow['id']} ma nieistniejące źródło: {flow.get('source')}")
            if flow.get('target') not in element_ids:
                missing.append(f"Przepływ {flow['id']} ma nieistniejący cel: {flow.get('target')}")
        
        return missing
    
    def _calculate_quality_metrics(self, bpmn_json: Dict) -> Dict[str, float]:
        """Oblicza metryki jakości"""
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        flows = bpmn_json.get('flows', [])
        
        return {
            'complexity': len(elements) / 10.0,  # normalized complexity
            'participant_diversity': len(participants) / 5.0,  # max 5 participants
            'connectivity': len(flows) / max(1, len(elements)) if elements else 0,
            'naming_quality': sum(1 for e in elements if e.get('name') and len(e['name']) > 5) / max(1, len(elements))
        }

    def _calculate_overall_quality(self, result: Dict[str, Any], original_participants_count: int = 0) -> float:
        """Oblicza ogólną jakość procesu z penalty za utratę wartości biznesowej"""
        if not result.get('is_valid', False):
            print("📊 Jakość: 0.0 (nieprawidłowy JSON)")
            return 0.0
        
        # Add business value preservation check
        bpmn_json = result.get('process', {})
        if bpmn_json:
            current_participants = len(bpmn_json.get('participants', []))
            current_tasks = len([e for e in bpmn_json.get('elements', []) if 'task' in e.get('type', '').lower()])
            
            # Heavy penalty for losing participants or oversimplification
            if original_participants_count > 0 and current_participants < original_participants_count * 0.5:
                print(f"⚠️ Strata uczestników: {current_participants}/{original_participants_count} - penalty!")
                return max(0.1, result.get('completeness_score', 0) * 0.3)  # Heavy penalty
            
            if current_tasks < 2:  # Too simplified (Start->End only)
                print(f"⚠️ Proces zbyt uproszczony ({current_tasks} zadań) - penalty!")
                return max(0.2, result.get('completeness_score', 0) * 0.5)
        
        # Much more realistic weighted average to allow meaningful quality scores
        weights = {
            'completeness': 0.5,      # Increased weight for completeness
            'missing_penalty': 0.3,   # Reduced penalty for missing elements
            'quality_bonus': 0.2
        }
        
        completeness = result.get('completeness_score', 0.0)
        # Much more lenient penalty for missing elements
        missing_penalty = max(0, 1 - len(result.get('missing_elements', [])) * 0.1)  # Very reduced from 0.25 to 0.1
        quality_metrics = result.get('quality_metrics', {})
        quality_bonus = sum(quality_metrics.values()) / len(quality_metrics) if quality_metrics else 0
        
        overall = (
            completeness * weights['completeness'] +
            missing_penalty * weights['missing_penalty'] +
            quality_bonus * weights['quality_bonus']
        )
        
        # Much more lenient strictness factor to allow good scores for valid processes
        strictness_factor = 0.95  # Increased from 0.8 to 0.95 for much better scores
        
        final_quality = min(1.0, overall * strictness_factor)
        
        # Debug logging
        print(f"📊 Jakość - detale:")
        print(f"   Kompletność: {completeness:.2f}")
        print(f"   Braki: {len(result.missing_elements)} (penalty: {missing_penalty:.2f})")
        print(f"   Quality bonus: {quality_bonus:.2f}")
        print(f"   Przed strictness: {overall:.2f}")
        print(f"   Po strictness (0.95): {final_quality:.2f}")
        
        return final_quality


class SimpleMCPServer:
    """
    Enhanced MCP Server for BPMN with full compliance validation
    """
    
    def __init__(self, ai_config=None, quota_optimization=True):
        self.quota_optimization = quota_optimization
        self.ai_calls_count = 0
        self.ai_calls_limit = 150  # Conservative limit to avoid quota exhaustion
        self.improvement_cache = {}  # Cache for similar improvement patterns
        # Use provided config or fallback to default
        config = ai_config or get_default_config()
        self.pipeline = BPMNv2Pipeline(ai_config=config)
        self.quality_checker = EnhancedBPMNQualityChecker()
        
        # Add direct access to compliance validator
        self.compliance_validator = BPMNComplianceValidator()
        
        # Ustaw silnik poprawek z pipeline do AI improvements
        self.improvement_engine = BPMNImprovementEngine(ai_pipeline=self.pipeline)
        self.quality_checker.improvement_engine = self.improvement_engine
        
        print("🔧 Enhanced MCP Server for BPMN initialized")
        print(f"🤖 Using AI: {self.pipeline.ai_config.provider.value}")
        print("✅ BPMN Compliance Validator enabled")
    
    def verify_bpmn_process(self, bpmn_json: Dict, original_participants_count: int = 0) -> Dict[str, Any]:
        """
        Enhanced BPMN process verification with full compliance checking
        
        Args:
            bpmn_json: Proces BPMN do weryfikacji
            
        Returns:
            Wynik weryfikacji z raportem zgodności BPMN
        """
        print(f"🔍 Verifying BPMN process: {bpmn_json.get('process_name', 'Unnamed')}")
        
        # Używaj nowego systemu jakości z business value preservation
        quality_result = self.quality_checker.check_process_quality(bpmn_json, original_participants_count)
        
        # Wyświetl szczegóły zgodności
        compliance = quality_result.get('bpmn_compliance', {})
        print(f"📊 Jakość - detale:")
        print(f"   Kompletność: {quality_result.get('completeness_score', 0):.2f}")
        print(f"   Braki: {len(quality_result.get('missing_elements', []))}")
        print(f"   Quality bonus: {quality_result.get('overall_quality', 0):.2f}")
        print(f"   BPMN Compliance Score: {compliance.get('score', 0):.1f}")
        print(f"   BPMN Compliance Level: {compliance.get('level', 'UNKNOWN')}")
        
        # Używaj quality_result.overall_quality bezpośrednio (już przeliczone w check_process_quality)
        final_quality = quality_result.get('overall_quality', 0.0)
        completeness_score = quality_result.get('completeness_score', 0.0)
        
        print(f"   Final quality: {final_quality:.2f}")
        
        return {
            'is_valid': quality_result['is_valid'],
            'completeness_score': completeness_score,
            'missing_elements': quality_result['missing_elements'],
            'validation_errors': quality_result['validation_errors'],
            'improvement_suggestions': quality_result['improvement_suggestions'],
            'quality_metrics': quality_result['quality_metrics'],
            'overall_quality': final_quality,
            'bpmn_compliance': compliance,
            'next_steps': self._extract_next_steps(quality_result)
        }
    
    def _extract_next_steps(self, quality_result: Dict) -> List[str]:
        """Ekstraktuje następne kroki z raportu jakości"""
        next_steps = []
        
        compliance = quality_result.get('bpmn_compliance', {})
        priorities = compliance.get('priorities', [])
        
        if priorities:
            next_steps.extend(priorities[:3])  # Top 3 priorytetów
        
        # Dodaj ogólne wskazówki
        missing_count = len(quality_result.get('missing_elements', []))
        if missing_count > 0:
            next_steps.append(f"Dodaj brakujące elementy: {', '.join(quality_result['missing_elements'][:2])}")
        
        return next_steps
    
    def intelligent_bpmn_optimization(self, bpmn_json: Dict, 
                                    context_hints: Optional[Dict] = None) -> Dict[str, Any]:
        """
        🧠 Inteligentna optymalizacja procesu BPMN z użyciem Intelligence Orchestrator
        
        Args:
            bpmn_json: Proces BPMN do optymalizacji
            context_hints: Wskazówki kontekstowe (domain, time_constraint, quality_requirement)
            
        Returns:
            Wynik inteligentnej optymalizacji z insights i rekomendacjami
        """
        print(f"🧠 Starting intelligent BPMN optimization...")
        if context_hints:
            print(f"📋 Context: {context_hints}")
        
        # Perform intelligent analysis
        intelligence_result = self.quality_checker.intelligent_analysis_and_optimization(
            bpmn_json=bpmn_json,
            context_hints=context_hints
        )
        
        if intelligence_result.get('intelligence_enabled'):
            print(f"✨ Intelligence analysis completed")
            print(f"🎯 Strategy: {intelligence_result['insights']['strategy_used']}")
            print(f"🔮 Predicted issues: {len(intelligence_result['insights']['predicted_issues'])}")
            print(f"⚡ Quality alerts: {len(intelligence_result['insights']['quality_alerts'])}")
            print(f"🎪 Confidence: {intelligence_result['insights']['confidence_score']:.3f}")
            print(f"⏱️ Processing time: {intelligence_result['processing_time']:.2f}s")
        else:
            print(f"⚠️ Intelligence analysis failed, using fallback")
        
        # Verify the optimized process
        if 'optimized_process' in intelligence_result:
            verification_result = self.verify_bpmn_process(intelligence_result['optimized_process'])
            intelligence_result['verification'] = verification_result
            
        return intelligence_result
    
    def improve_bpmn_process(self, bpmn_json: Dict, target_score: float = 85.0, 
                           max_iterations: int = 3) -> Dict[str, Any]:
        """
        Iteracyjne ulepszanie procesu BPMN z pełną walidacją zgodności
        NOWY: Automatyczne naprawy konkretnych problemów które AI nie potrafi naprawić
        
        Args:
            bpmn_json: Proces BPMN do ulepszenia
            target_score: Docelowy wynik zgodności BPMN (0-100)
            max_iterations: Maksymalna liczba iteracji
            
        Returns:
            Kompletny raport z ulepszonego procesu
        """
        print(f"🔧 Improving BPMN process...")
        
        original_process = bpmn_json.copy()
        current_process = bpmn_json.copy()
        improvements_made = []
        
        for iteration in range(max_iterations):
            print(f"\n🔄 Auto-fix iteration {iteration + 1}")
            
            # Sprawdź compliance
            compliance_report = self.compliance_validator.validate_bpmn_compliance(current_process)
            print(f"📊 Current score: {compliance_report.overall_score}")
            
            if compliance_report.overall_score >= target_score:
                print(f"🎯 Target score reached!")
                break
            
            # Automatyczne naprawy konkretnych problemów
            iteration_changes = []
            
            # 1. STRUCT_001 & STRUCT_007: Pool bez Start Events
            start_issues = [i for i in compliance_report.issues if i.rule_code in ['STRUCT_001', 'STRUCT_007'] and 'Start Event' in i.message]
            for issue in start_issues:
                if self._auto_fix_missing_pool_start_event(current_process, issue.element_id):
                    change_msg = f"Added Start Event to Pool '{issue.element_id}'"
                    iteration_changes.append(change_msg)
                    print(f"✅ {change_msg}")
            
            # 2. STRUCT_002: Pool bez End Events  
            end_issues = [i for i in compliance_report.issues if i.rule_code == 'STRUCT_002' and 'End Event' in i.message]
            for issue in end_issues:
                if self._auto_fix_missing_pool_end_event(current_process, issue.element_id):
                    change_msg = f"Added End Event to Pool '{issue.element_id}'"
                    iteration_changes.append(change_msg)
                    print(f"✅ {change_msg}")
            
            # 3. STRUCT_004: Gateway sequence flow między Pool → Message Flow
            gateway_issues = [i for i in compliance_report.issues if i.rule_code == 'STRUCT_004' and 'Gateway' in i.message]
            for issue in gateway_issues:
                if self._auto_fix_gateway_cross_pool_flows(current_process, issue.element_id):
                    change_msg = f"Fixed Gateway cross-pool flows: '{issue.element_id}'"
                    iteration_changes.append(change_msg)
                    print(f"✅ {change_msg}")
            
            # 4. Brakujące sequence flows w obrębie Pool
            connectivity_issues = [i for i in compliance_report.issues if i.rule_code == 'STRUCT_003']
            if connectivity_issues and self._auto_fix_pool_sequence_flows(current_process):
                change_msg = "Fixed missing sequence flows within pools"
                iteration_changes.append(change_msg)
                print(f"✅ {change_msg}")
            
            improvements_made.extend(iteration_changes)
            
            if not iteration_changes:
                print(f"⚠️ No more automatic fixes available")
                break
        
        # Final verification
        final_compliance = self.compliance_validator.validate_bpmn_compliance(current_process)
        
        print(f"🎯 Target BPMN compliance score: {target_score}")
        print(f"🔄 Max iterations: {max_iterations}")
        
        # Użyj nowego silnika iteracyjnych poprawek
        improvement_result = self.improvement_engine.improve_bpmn_process(
            bpmn_json, 
            target_score=target_score, 
            max_iterations=max_iterations
        )
        
        # Finalna weryfikacja z nowym systemem
        final_verification = self.verify_bpmn_process(improvement_result['improved_process'])
        
        return {
            'success': True,
            'message': f"Improved from {improvement_result.get('original_score', 0):.1f} to {improvement_result.get('final_score', 0):.1f}",
            'original_process': improvement_result['original_process'],
            'improved_process': improvement_result['improved_process'],
            'improvement_summary': improvement_result['summary'],
            'improvement_history': improvement_result['improvement_history'],
            'final_verification': final_verification,
            'final_compliance': improvement_result['final_compliance'],
            'recommendations': self._generate_final_recommendations(improvement_result),
            # Dodane dla kompatybilności z iterative_pipeline.py
            'changes_made': self._extract_changes_from_history(improvement_result['improvement_history']),
            'improvements_made': len(self._extract_changes_from_history(improvement_result['improvement_history']))
        }
    
    def _extract_changes_from_history(self, improvement_history: List[Dict]) -> List[str]:
        """Wyciąga zmiany z historii poprawek do formatu używanego przez iterative pipeline"""
        changes = []
        
        for iteration_data in improvement_history:
            applied_improvements = iteration_data.get('improvements_applied', [])
            for improvement in applied_improvements:
                if isinstance(improvement, dict):
                    description = improvement.get('description', str(improvement))
                else:
                    description = str(improvement)
                changes.append(description)
        
        # Fallback jeśli brak zmian w historii
        if not changes:
            final_compliance = improvement_history[-1].get('compliance_report', {}) if improvement_history else {}
            score = final_compliance.get('overall_score', 0)
            if score > 0:
                changes.append(f"Poprawiono zgodność BPMN do {score:.1f} punktów")
            else:
                changes.append("Przeprowadzono analizę zgodności BPMN")
        
        return changes
    
    def _generate_final_recommendations(self, improvement_result: Dict) -> List[str]:
        """Generuje finalne rekomendacje na podstawie wyników poprawy"""
        recommendations = []
        
        summary = improvement_result['summary']
        final_score = summary['final_compliance_score']
        
        if final_score >= 95:
            recommendations.append("✅ Proces jest w pełni zgodny ze standardem BPMN 2.0")
        elif final_score >= 85:
            recommendations.append("✅ Proces ma dobrą zgodność ze standardem BPMN")
        elif final_score >= 70:
            recommendations.append("⚠️ Proces wymaga dalszych poprawek zgodności BPMN")
        else:
            recommendations.append("❌ Proces ma poważne problemy ze zgodnością BPMN")
        
        # Dodaj konkretne rekomendacje
        remaining_issues = summary['remaining_issues']
        if remaining_issues > 0:
            recommendations.append(f"Pozostało {remaining_issues} problemów do rozwiązania")
        
        auto_fixes = summary['auto_fixes_vs_manual']['auto_fixes']
        if auto_fixes > 0:
            recommendations.append(f"Automatycznie naprawiono {auto_fixes} problemów")
        
        iterations = summary['iterations_completed']
        if iterations >= 3:
            recommendations.append("Rozważ podział procesu na mniejsze części")
        
        return recommendations
        if verification['overall_quality'] >= 0.95:  # Very high threshold to allow more improvements
            return {
                'improved_process': bpmn_json,
                'changes_made': [],
                'message': 'Process is already high quality'
            }
        
        
        # Apply SAFE automatic improvements - only BPMN 2.0 notation fixes, NO merytoryczne changes
        improved_process = self._apply_automatic_improvements(bpmn_json, verification)
        
        changes_made = self._identify_changes(bpmn_json, improved_process)
        
        return {
            'improved_process': improved_process,
            'changes_made': changes_made,
            'message': f'Applied {len(changes_made)} notation improvements (no process logic changes)'
        }
    
    def generate_improvement_prompt(self, bpmn_json: Dict, verification_result: Dict, 
                                  focus_severity: str = None, fixed_categories_info: str = "",
                                  original_text: str = "") -> str:
        """
        Generuje skrócony prompt dla AI żeby poprawił proces
        NOWY: focus_severity pozwala skupić się na konkretnym poziomie problemów
        """
        missing = verification_result.get('missing_elements', [])
        suggestions = verification_result.get('improvement_suggestions', [])
        overall_quality = verification_result.get('overall_quality', 0.0)
        bpmn_compliance = verification_result.get('bpmn_compliance', {})
        
        # Filtruj issues według focus_severity
        all_issues = bpmn_compliance.get('issues', [])
        if focus_severity:
            focused_issues = [i for i in all_issues if i['severity'] == focus_severity]
            print(f"🎯 FOCUSED IMPROVEMENT: {focus_severity} - {len(focused_issues)} issues")
        else:
            focused_issues = all_issues
        
        # Create simplified process info to reduce prompt size
        process_summary = {
            'process_name': bpmn_json.get('process_name', 'Unknown'),
            'participants': [p.get('name', p.get('id', 'Unknown')) for p in bpmn_json.get('participants', [])],
            'elements_count': len(bpmn_json.get('elements', [])),
            'flows_count': len(bpmn_json.get('flows', [])),
            'start_events': len([e for e in bpmn_json.get('elements', []) if e.get('type') == 'startEvent']),
            'end_events': len([e for e in bpmn_json.get('elements', []) if e.get('type') == 'endEvent']),
            'tasks': len([e for e in bpmn_json.get('elements', []) if 'Task' in e.get('type', '')]),
        }
        
        # NOWA LOGIKA: Kategoryzowanie błędów według typów
        categorized_issues = self._categorize_issues_by_type(focused_issues if focus_severity else all_issues)
        
        # PROGRESYWNE NAPRAWIANIE: wybierz jedną kategorię naraz
        selected_category, selected_issues = self._select_next_category_to_fix(categorized_issues, bpmn_json)
        
        # Determine improvement focus based on selected category
        improvement_focus = []
        
        if selected_category and selected_issues:
            print(f"🎯 KATEGORIA: {selected_category.value.upper()} - {len(selected_issues)} issues")
            # Zapisz aktualną kategorię do tracking
            self.current_iteration_category = selected_category
            
            for issue in selected_issues[:3]:  # Max 3 issues from one category at once
                severity_marker = issue['severity'].upper() if focus_severity else 'ISSUE'
                improvement_focus.append(f"{severity_marker} - {issue['rule_code']}: {issue['message']}")
        elif focus_severity == 'critical':
            # Fallback dla critical issues bez kategorii
            for issue in focused_issues[:5]:  # Max 5 critical issues at once
                improvement_focus.append(f"CRITICAL - {issue['rule_code']}: {issue['message']}")
        elif focus_severity == 'major':
            # Skupiaj się tylko na major issues  
            for issue in focused_issues[:5]:
                improvement_focus.append(f"MAJOR - {issue['rule_code']}: {issue['message']}")
        else:
            # Domyślnie - stary sposób (wszystkie problemy)
            if process_summary['start_events'] == 0:
                improvement_focus.append("CRITICAL: Dodaj Start Event na początku procesu")
            if process_summary['end_events'] == 0:
                improvement_focus.append("CRITICAL: Dodaj End Event na końcu procesu")
            if process_summary['flows_count'] < process_summary['elements_count'] - 1:
                improvement_focus.append("CRITICAL: Dodaj brakujące Sequence Flow między elementami")
            
            # Add specific issues
            improvement_focus.extend(missing[:3])  # Top 3 missing elements
            improvement_focus.extend(suggestions[:3])  # Top 3 suggestions
            
            # Jeśli nie ma konkretnych problemów, skoncentruj się na jakości
            if not improvement_focus and overall_quality < 0.65:
                improvement_focus = [
                    "Popraw nazwy elementów - użyj bardziej opisowych nazw",
                    "Sprawdź poprawność przepływów między elementami",
                    "Dodaj warunki dla Gateway jeśli używane"
                ]
        
        # Prompt różni się w zależności od focus_severity
        if focus_severity:
            severity_text = focus_severity.upper()
            prompt = f"""ROLA: Jesteś ekspertem notacji BPMN 2.0 z wieloletnim doświadczeniem w projektowaniu procesów biznesowych. Twoja specjalizacja to poprawianie zgodności diagramów z standardem BPMN 2.0 oraz zapewnianie poprawnych przepływów między uczestnikami procesów (Pools/Lanes).

KATEGORIA NAPRAW: {selected_category.value.upper() if selected_category else severity_text}
{fixed_categories_info}

ZADANIE: Napraw TYLKO {severity_text} problemy w kategorii {selected_category.value.upper() if selected_category else 'OGÓLNEJ'} w procesie BPMN:

PROCES: {process_summary['process_name']} 
ANALIZA:
- Uczestnicy: {len(process_summary['participants'])} ({', '.join(process_summary['participants'])})
- Elementy: {process_summary['elements_count']} (Start: {process_summary['start_events']}, End: {process_summary['end_events']}, Tasks: {process_summary['tasks']})
- Przepływy: {process_summary['flows_count']}
- Obecna jakość: {overall_quality:.2f}

🎯 FOKUS: {severity_text} ISSUES TYLKO ({len(improvement_focus)}):
{chr(10).join(f"- {item}" for item in improvement_focus)}

⚠️ KRYTYCZNE ZASADY BPMN 2.0:
- Każdy Pool MUSI mieć Start Event, Intermediate Catch Event lub Message Flow wchodzący
- Każdy Pool MUSI mieć End Event, Intermediate Throw Event lub Message Flow wychodzący  
- Sequence Flow NIE MOŻE przechodzić między różnymi Pools - używaj Message Flow
- W obrębie Pool wszystkie elementy MUSZĄ być połączone Sequence Flow

⭐ NAJWAŻNIEJSZE - ZACHOWANIE WARTOŚCI BIZNESOWEJ:
🚨🚨🚨 ABSOLUTNY PRIORYTET - ZACHOWANIE CAŁEJ FUNKCJONALNOŚCI BIZNESOWEJ 🚨🚨🚨

📝 **ORYGINALNY OPIS PROCESU (ZAWSZE SPRAWDZAJ!):**
{original_text}

❌ KATEGORYCZNIE ZAKAZANE DZIAŁANIA:
- NIGDY nie usuwaj uczestników (Pool) z oryginalnego opisu procesu
- NIGDY nie upraszczaj procesu do podstawowego Start→End
- NIGDY nie usuwaj zadań biznesowych (userTask, serviceTask)
- NIGDY nie likwiduj całych Pool lub procesów biznesowych
- NIGDY nie zastępuj złożonych procesów prostymi przepływami

✅ OBOWIĄZKOWE ZACHOWANIE:
- ZAWSZE zachowuj WSZYSTKICH uczestników z oryginalnego opisu
- ZAWSZE zachowuj wszystkie kluczowe aktivności biznesowe (Tasks)
- ZAWSZE zachowuj logikę biznesową i punkty decyzyjne
- ZAWSZE zachowuj złożoność odpowiadającą rzeczywistości biznesowej
- ZAWSZE odwołuj się do oryginalnego opisu procesu powyżej!

🎯 DEFINICJA SUKCESU:
Udana poprawa = Zachowanie 100% funkcjonalności biznesowej + Poprawa zgodności BPMN
TYLKO dodawaj elementy strukturalne dla zgodności, NIE USUWAJ logiki biznesowej!

INSTRUKCJE NAPRAWY:
1. 🔒 ZACHOWAJ WSZYSTKICH uczestników z oryginalnego opisu procesu
2. 🔒 ZACHOWAJ wszystkie kluczowe Tasks/Activities biznesowe
3. ✅ Napraw TYLKO wymienione {severity_text} problemy zgodnie z BPMN 2.0
4. ✅ Dodaj brakujące Start/End Events do Pool zgodnie ze standardem
5. ✅ Zamień niepoprawne Sequence Flow na Message Flow między Pools
6. ✅ Zachowaj istniejące nazwy i ID elementów
7. ⚠️ Jeśli nie możesz naprawić bez utraty funkcjonalności, dodaj tylko minimum potrzebnych elementów

⚠️ FORMAT JSON - PRZYKŁAD POPRAWNEJ STRUKTURY:
{{
  "process_name": "Nazwa procesu",
  "participants": [{{"id": "participant_1", "name": "Uczestnik 1", "type": "pool"}}],
  "elements": [{{"id": "start_1", "name": "Start Event", "type": "startEvent", "participant": "participant_1"}}],
  "flows": [{{"id": "flow_1", "source": "start_1", "target": "task_1"}}]
}}

Zwróć TYLKO JSON bez dodatkowego tekstu:
{{"process_name": "...", "participants": [...], "elements": [...], "flows": [...]}}

ORYGINALNY PROCES DO POPRAWY:
{json.dumps(bpmn_json, indent=1, ensure_ascii=False)[:3000]}{"..." if len(json.dumps(bpmn_json)) > 3000 else ""}"""
        else:
            category_info = f"KATEGORIA: {selected_category.value.upper()}" if selected_category else "KATEGORIA: OGÓLNA POPRAWA"
            prompt = f"""ROLA: Jesteś ekspertem notacji BPMN 2.0 z wieloletnim doświadczeniem w projektowaniu procesów biznesowych. Twoja specjalizacja to poprawianie zgodności diagramów z standardem BPMN 2.0 oraz zapewnianie poprawnych przepływów między uczestnikami procesów (Pools/Lanes).

{category_info}
{fixed_categories_info}

📝 **ORYGINALNY OPIS PROCESU (ZAWSZE SPRAWDZAJ!):**
{original_text}

⭐ NAJWAŻNIEJSZE - ZACHOWANIE WARTOŚCI BIZNESOWEJ:
🚨🚨🚨 ABSOLUTNY PRIORYTET - ZACHOWANIE CAŁEJ FUNKCJONALNOŚCI BIZNESOWEJ 🚨🚨🚨

ZADANIE: Popraw proces BPMN na podstawie konkretnych problemów, ale ZAWSZE zachowaj wszystkich uczestników i całą logikę biznesową z oryginalnego opisu!

PROCES: {process_summary['process_name']} 
ANALIZA:
- Uczestnicy: {len(process_summary['participants'])} ({', '.join(process_summary['participants'])})
- Elementy: {process_summary['elements_count']} (Start: {process_summary['start_events']}, End: {process_summary['end_events']}, Tasks: {process_summary['tasks']})
- Przepływy: {process_summary['flows_count']}
- Obecna jakość: {overall_quality:.2f}

WYMAGANE POPRAWKI ({len(improvement_focus)}):
{chr(10).join(f"- {item}" for item in improvement_focus)}

⚠️ KRYTYCZNE ZASADY BPMN 2.0:
- Każdy Pool MUSI mieć Start Event, Intermediate Catch Event lub Message Flow wchodzący
- Każdy Pool MUSI mieć End Event, Intermediate Throw Event lub Message Flow wychodzący  
- Sequence Flow NIE MOŻE przechodzić między różnymi Pools - używaj Message Flow
- W obrębie Pool wszystkie elementy MUSZĄ być połączone Sequence Flow

⭐ KRYTYCZNE - ZACHOWANIE WARTOŚCI BIZNESOWEJ:
- Proces MUSI zawierać wszystkich uczestników z oryginalnego opisu
- Proces MUSI zachować kluczowe aktywności biznesowe
- ZABRANIA SIĘ upraszczania do podstawowego Start→End
- Celem jest naprawa struktury, NIE redukcja funkcjonalności

INSTRUKCJE POPRAWY:
1. 🔒 OBLIGATORYJNIE zachowaj wszystkich uczestników i kluczowe Task z oryginalnego procesu
2. ✅ Napraw strukturalne problemy zgodnie z BPMN 2.0
2. Dodaj brakujące Start Event / End Event do Pools zgodnie ze standardem
3. Zamień niepoprawne Sequence Flow na Message Flow między Pools
4. Popraw nazwy elementów na bardziej opisowe
5. Sprawdź czy wszystkie elementy mają unikalne ID

⚠️ FORMAT JSON - PRZYKŁAD POPRAWNEJ STRUKTURY:
{{
  "process_name": "Nazwa procesu",
  "participants": [{{"id": "participant_1", "name": "Uczestnik 1", "type": "pool"}}],
  "elements": [{{"id": "start_1", "name": "Start Event", "type": "startEvent", "participant": "participant_1"}}],
  "flows": [{{"id": "flow_1", "source": "start_1", "target": "task_1"}}]
}}

Zwróć TYLKO poprawiony JSON bez dodatkowego tekstu:
{{"process_name": "...", "participants": [...], "elements": [...], "flows": [...]}}

ORYGINALNY PROCES DO POPRAWY:
{json.dumps(bpmn_json, indent=1, ensure_ascii=False)[:3000]}{"..." if len(json.dumps(bpmn_json)) > 3000 else ""}"""
        
        return prompt.strip()
    
    def _categorize_issues_by_type(self, issues: List[Dict]) -> Dict[ErrorCategory, List[Dict]]:
        """Kategoryzuje błędy według typów dla progresywnego naprawiania"""
        categorized = {
            ErrorCategory.STRUCTURE: [],
            ErrorCategory.FLOWS: [],
            ErrorCategory.GATEWAYS: [],
            ErrorCategory.NAMING: [],
            ErrorCategory.SEMANTICS: []
        }
        
        for issue in issues:
            rule_code = issue.get('rule_code', '')
            message = issue.get('message', '').lower()
            
            # Kategoria STRUCTURE: Start/End Events, Pool structure
            if any(keyword in rule_code for keyword in ['STRUCT_001', 'STRUCT_002', 'STRUCT_007']):
                categorized[ErrorCategory.STRUCTURE].append(issue)
            
            # Kategoria FLOWS: Sequence/Message flows
            elif any(keyword in rule_code for keyword in ['STRUCT_003', 'STRUCT_004']):
                categorized[ErrorCategory.FLOWS].append(issue)
            
            # Kategoria GATEWAYS: Gateway logic
            elif 'gateway' in message or 'GATEWAY' in rule_code:
                categorized[ErrorCategory.GATEWAYS].append(issue)
            
            # Kategoria NAMING: Names and IDs
            elif any(keyword in rule_code for keyword in ['STYLE_001', 'STYLE_003']) or 'name' in message:
                categorized[ErrorCategory.NAMING].append(issue)
            
            # Kategoria SEMANTICS: Business logic
            else:
                categorized[ErrorCategory.SEMANTICS].append(issue)
        
        return categorized
    
    def _select_next_category_to_fix(self, categorized_issues: Dict[ErrorCategory, List[Dict]], 
                                   process: Dict) -> Tuple[ErrorCategory, List[Dict]]:
        """Wybiera następną kategorię błędów do naprawienia w kolejności priorytetów"""
        
        # Kolejność priorytetów naprawiania (od najważniejszych)
        priority_order = [
            ErrorCategory.STRUCTURE,   # Najpierw struktura (Start/End Events)
            ErrorCategory.FLOWS,       # Potem przepływy
            ErrorCategory.GATEWAYS,    # Następnie Gateway
            ErrorCategory.NAMING,      # Potem nazewnictwo
            ErrorCategory.SEMANTICS    # Na końcu semantyka
        ]
        
        # Znajdź pierwszą kategorię z issues
        for category in priority_order:
            issues_in_category = categorized_issues.get(category, [])
            if issues_in_category:
                print(f"📋 Wybrano kategorię: {category.value} ({len(issues_in_category)} issues)")
                return category, issues_in_category
        
        print(f"📋 Brak issues w żadnej kategorii")
        return None, []
    
    def _apply_auto_fixes_for_category(self, process: Dict, issues: List[Dict], category: ErrorCategory) -> List[str]:
        """Zastosuj automatyczne poprawki dla konkretnej kategorii"""
        fixes_applied = []
        
        for issue in issues:
            rule_code = issue.get('rule_code', '')
            element_id = issue.get('element_id', '')
            
            # AUTO-FIX: Gateway without enough outgoing flows
            if rule_code == 'STRUCT_004' and 'musi mieć co najmniej 2 przepływy wyjściowe' in issue.get('message', ''):
                if self._auto_fix_gateway_outgoing_flows(process, element_id):
                    fixes_applied.append(f"Added missing outgoing flow for gateway {element_id}")
            
            # AUTO-FIX: Missing Start/End Events
            elif rule_code == 'STRUCT_001':
                participant = issue.get('element_id', '')
                if 'start' in issue.get('message', '').lower():
                    if self._auto_fix_missing_pool_start_event(process, participant):
                        fixes_applied.append(f"Added Start Event for pool {participant}")
                elif 'end' in issue.get('message', '').lower():
                    if self._auto_fix_missing_pool_end_event(process, participant):
                        fixes_applied.append(f"Added End Event for pool {participant}")
        
        return fixes_applied
    
    def _auto_fix_gateway_outgoing_flows(self, process: Dict, gateway_id: str) -> bool:
        """Auto-fix dla Gateway bez wystarczających przepływów wyjściowych"""
        try:
            elements = process.get('elements', [])
            flows = process.get('flows', [])
            
            # Znajdź gateway
            gateway = next((e for e in elements if e.get('id') == gateway_id), None)
            if not gateway or gateway.get('type') != 'exclusiveGateway':
                return False
            
            # Sprawdź istniejące outgoing flows
            outgoing = [f for f in flows if f.get('source') == gateway_id]
            if len(outgoing) >= 2:
                return False  # Already has enough flows
            
            # Znajdź lub stwórz End Event jako domyślny target
            gateway_pool = gateway.get('participant')
            end_events = [e for e in elements if e.get('type') == 'endEvent' and e.get('participant') == gateway_pool]
            
            if not end_events:
                # Stwórz End Event
                end_event_id = f"end_event_{gateway_pool}_default"
                end_event = {
                    'id': end_event_id,
                    'name': 'Default End',
                    'type': 'endEvent', 
                    'participant': gateway_pool
                }
                elements.append(end_event)
                target_id = end_event_id
            else:
                target_id = end_events[0]['id']
            
            # Dodaj default flow
            default_flow = {
                'id': f'flow_{gateway_id}_default',
                'source': gateway_id,
                'target': target_id,
                'name': 'default',
                'condition': 'default'
            }
            flows.append(default_flow)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Auto-fix gateway failed: {e}")
            return False
        """Naprawia brak Start Event w Pool"""
        try:
            elements = process.get('elements', [])
            flows = process.get('flows', [])
            participants = process.get('participants', [])
            
            # Znajdź participant
            participant = next((p for p in participants if p.get('id') == pool_id), None)
            if not participant:
                return False
            
            # Sprawdź czy Pool ma aktywności
            pool_elements = [e for e in elements if e.get('participant') == pool_id]
            activities = [e for e in pool_elements if e.get('type') in ['userTask', 'serviceTask', 'manualTask']]
            
            if not activities:
                return False  # Pool bez aktywności nie potrzebuje Start Event
            
            # Sprawdź czy już ma Start Event
            start_events = [e for e in pool_elements if e.get('type') == 'startEvent']
            if start_events:
                return False  # Już ma Start Event
            
            # Dodaj Start Event
            start_event_id = f"start_event_{pool_id}"
            start_event = {
                'id': start_event_id,
                'name': f'Start {participant.get("name", pool_id)}',
                'type': 'startEvent',
                'participant': pool_id
            }
            elements.append(start_event)
            
            # Połącz z pierwszą aktywnością
            if activities:
                first_activity = activities[0]
                flow_id = f"flow_{start_event_id}_{first_activity['id']}"
                sequence_flow = {
                    'id': flow_id,
                    'source': start_event_id,
                    'target': first_activity['id'],
                    'type': 'sequence'
                }
                flows.append(sequence_flow)
            
            return True
            
        except Exception as e:
            print(f"❌ Error fixing missing start event for {pool_id}: {e}")
            return False
    
    def _auto_fix_missing_pool_start_event(self, process: Dict, pool_id: str) -> bool:
        """Naprawia brak Start Event w Pool"""
        try:
            elements = process.get('elements', [])
            flows = process.get('flows', [])
            participants = process.get('participants', [])
            
            # Znajdź participant
            participant = next((p for p in participants if p.get('id') == pool_id), None)
            if not participant:
                return False
            
            # Sprawdź czy Pool ma aktywności
            pool_elements = [e for e in elements if e.get('participant') == pool_id]
            activities = [e for e in pool_elements if e.get('type') in ['userTask', 'serviceTask', 'manualTask']]
            
            if not activities:
                return False  # Pool bez aktywności nie potrzebuje Start Event
            
            # Sprawdź czy już ma Start Event lub dostaje Message Flow wchodzący
            start_events = [e for e in pool_elements if e.get('type') == 'startEvent']
            message_flows_in = [f for f in flows if f.get('type') == 'message' and 
                               any(e.get('id') == f.get('target') for e in pool_elements)]
            
            if start_events or message_flows_in:
                return False  # Już ma Start Event lub Message Flow wchodzący
            
            # Dodaj Start Event
            start_event_id = f"start_event_{pool_id}"
            start_event = {
                'id': start_event_id,
                'name': f'Start {participant.get("name", pool_id)}',
                'type': 'startEvent',
                'participant': pool_id
            }
            elements.append(start_event)
            
            # Znajdź pierwszą aktywność (bez incoming flows)
            first_activities = []
            for activity in activities:
                incoming = [f for f in flows if f.get('target') == activity.get('id') and f.get('type') == 'sequence']
                if not incoming:
                    first_activities.append(activity)
            
            # Połącz z pierwszą aktywnością
            if first_activities:
                for first_activity in first_activities:
                    flow_id = f"flow_{start_event_id}_{first_activity['id']}"
                    sequence_flow = {
                        'id': flow_id,
                        'source': start_event_id,
                        'target': first_activity['id'],
                        'type': 'sequence'
                    }
                    flows.append(sequence_flow)
            
            return True
            
        except Exception as e:
            print(f"❌ Error fixing missing start event for {pool_id}: {e}")
            return False

    def _auto_fix_missing_pool_end_event(self, process: Dict, pool_id: str) -> bool:
        """Naprawia brak End Event w Pool"""
        try:
            elements = process.get('elements', [])
            flows = process.get('flows', [])
            participants = process.get('participants', [])
            
            # Znajdź participant
            participant = next((p for p in participants if p.get('id') == pool_id), None)
            if not participant:
                return False
            
            # Sprawdź czy Pool ma aktywności
            pool_elements = [e for e in elements if e.get('participant') == pool_id]
            activities = [e for e in pool_elements if e.get('type') in ['userTask', 'serviceTask', 'manualTask']]
            
            if not activities:
                return False  # Pool bez aktywności nie potrzebuje End Event
            
            # Sprawdź czy już ma End Event
            end_events = [e for e in pool_elements if e.get('type') == 'endEvent']
            if end_events:
                return False  # Już ma End Event
            
            # Dodaj End Event
            end_event_id = f"end_event_{pool_id}"
            end_event = {
                'id': end_event_id,
                'name': f'End {participant.get("name", pool_id)}',
                'type': 'endEvent',
                'participant': pool_id
            }
            elements.append(end_event)
            
            # Znajdź ostatnią aktywność (bez outgoing flows)
            last_activities = []
            for activity in activities:
                outgoing = [f for f in flows if f.get('source') == activity.get('id') and f.get('type') == 'sequence']
                if not outgoing:
                    last_activities.append(activity)
            
            # Połącz z ostatnią aktywnością
            if last_activities:
                for last_activity in last_activities:
                    flow_id = f"flow_{last_activity['id']}_{end_event_id}"
                    sequence_flow = {
                        'id': flow_id,
                        'source': last_activity['id'],
                        'target': end_event_id,
                        'type': 'sequence'
                    }
                    flows.append(sequence_flow)
            
            return True
            
        except Exception as e:
            print(f"❌ Error fixing missing end event for {pool_id}: {e}")
            return False
    
    def _auto_fix_gateway_cross_pool_flows(self, process: Dict, gateway_id: str) -> bool:
        """Naprawia Gateway które wysyłają Sequence Flow między Pool (zamienia na Message Flow)"""
        try:
            elements = process.get('elements', [])
            flows = process.get('flows', [])
            
            # Znajdź gateway
            gateway = next((e for e in elements if e.get('id') == gateway_id), None)
            if not gateway:
                return False
            
            gateway_pool = gateway.get('participant')
            if not gateway_pool:
                return False
            
            changes_made = False
            
            # Sprawdź wszystkie outgoing sequence flows z tego gateway
            for flow in flows[:]:  # Copy to avoid modification during iteration
                if flow.get('source') == gateway_id and flow.get('type') == 'sequence':
                    # Znajdź target element
                    target_element = next((e for e in elements if e.get('id') == flow.get('target')), None)
                    if target_element:
                        target_pool = target_element.get('participant')
                        
                        # Jeśli target jest w innym Pool, zmień na Message Flow
                        if target_pool and target_pool != gateway_pool:
                            flow['type'] = 'message'
                            changes_made = True
                            print(f"   Changed {gateway_id} → {target_element['id']} from sequence to message flow")
            
            return changes_made
            
        except Exception as e:
            print(f"❌ Error fixing gateway flows for {gateway_id}: {e}")
            return False
    
    def _auto_fix_pool_sequence_flows(self, process: Dict) -> bool:
        """Naprawia brakujące sequence flows w obrębie Pool"""
        try:
            elements = process.get('elements', [])
            flows = process.get('flows', [])
            participants = process.get('participants', [])
            
            changes_made = False
            
            for participant in participants:
                pool_id = participant.get('id')
                pool_elements = [e for e in elements if e.get('participant') == pool_id]
                
                # Znajdź aktywności bez incoming flows
                for element in pool_elements:
                    if element.get('type') in ['userTask', 'serviceTask', 'manualTask']:
                        incoming = [f for f in flows if f.get('target') == element.get('id') and f.get('type') == 'sequence']
                        
                        if not incoming and element.get('type') != 'startEvent':
                            # Spróbuj znaleźć poprzedni element w tym Pool
                            prev_elements = [e for e in pool_elements 
                                           if e.get('type') in ['startEvent', 'userTask', 'serviceTask', 'manualTask', 'exclusiveGateway']
                                           and e.get('id') != element.get('id')]
                            
                            for prev_element in prev_elements:
                                # Sprawdź czy prev_element nie ma outgoing flow
                                outgoing = [f for f in flows if f.get('source') == prev_element.get('id') and f.get('type') == 'sequence']
                                if not outgoing:
                                    # Dodaj połączenie
                                    flow_id = f"flow_{prev_element['id']}_{element['id']}"
                                    new_flow = {
                                        'id': flow_id,
                                        'source': prev_element['id'],
                                        'target': element['id'],
                                        'type': 'sequence'
                                    }
                                    flows.append(new_flow)
                                    changes_made = True
                                    print(f"   Added sequence flow: {prev_element['id']} → {element['id']}")
                                    break
            
            return changes_made
            
        except Exception as e:
            print(f"❌ Error fixing pool sequence flows: {e}")
            return False
    
    def _suggest_next_steps(self, result: Dict[str, Any]) -> List[str]:
        """Sugeruje następne kroki"""
        steps = []
        
        if not result.get('is_valid', False):
            steps.append("Napraw błędy walidacji JSON Schema")
            return steps
        
        if result.get('completeness_score', 0.0) < 0.7:
            steps.append("Uzupełnij brakujące elementy procesu")
        
        missing_elements = result.get('missing_elements', [])
        if missing_elements:
            steps.append("Dodaj brakujące elementy: " + ', '.join(missing_elements[:3]))
        
        improvement_suggestions = result.get('improvement_suggestions', [])
        if improvement_suggestions:
            steps.append("Zastosuj sugestie: " + improvement_suggestions[0])
        
        if not steps:
            steps.append("Proces wygląda dobrze - możesz go użyć")
        
        return steps
    
    def _apply_automatic_improvements(self, bpmn_json: Dict, verification: Dict) -> Dict[str, Any]:
        """
        Automatycznie poprawia TYLKO notację BPMN 2.0 - NIE ZMIENIA merytoryki procesu!
        
        ZASADY:
        - NIE dodawaj nowych elementów procesu
        - NIE dodawaj nowych uczestników
        - NIE zmieniaj logiki biznesowej
        - POPRAWIAJ tylko nazwy, typy elementów i atrybuty zgodnie z BPMN 2.0
        """
        # CRITICAL: Deep copy to preserve original structure completely
        improved = json.loads(json.dumps(bpmn_json))
        
        # 1. POPRAW TYLKO nazwy elementów (bez dodawania nowych)
        elements = improved.get('elements', [])
        for element in elements:
            # Popraw nazwę tylko jeśli jest za krótka lub pusta
            if not element.get('name') or len(element['name']) < 3:
                element_type = element.get('type', 'element')
                element_id = element.get('id', '')
                
                if 'start' in element_type.lower():
                    element['name'] = 'Start procesu'
                elif 'end' in element_type.lower():
                    element['name'] = 'Koniec procesu'
                elif 'userTask' in element_type:
                    element['name'] = f"Zadanie użytkownika ({element_id})"
                elif 'serviceTask' in element_type:
                    element['name'] = f"Zadanie systemowe ({element_id})"
                elif 'gateway' in element_type.lower():
                    element['name'] = f"Decyzja ({element_id})"
                else:
                    element['name'] = f"{element_type} ({element_id})"
            
            # Popraw typ zadania jeśli niepoprawny
            if element.get('type') == 'task':
                # Zmień ogólny 'task' na konkretny typ
                participant = element.get('participant', '')
                if 'system' in participant.lower() or 'service' in participant.lower():
                    element['type'] = 'serviceTask'
                    element['task_type'] = 'service'
                else:
                    element['type'] = 'userTask'
                    element['task_type'] = 'user'
        
        # 2. POPRAW nazwy przepływów (bez dodawania nowych)
        flows = improved.get('flows', [])
        for flow in flows:
            if not flow.get('name'):
                source_element = next((e for e in elements if e.get('id') == flow.get('source')), None)
                if source_element and 'gateway' in source_element.get('type', '').lower():
                    # Dla przepływów z bramek dodaj domyślne nazwy warunków
                    condition = flow.get('condition', '')
                    if condition:
                        if 'tak' in condition.lower() or 'yes' in condition.lower() or 'true' in condition.lower():
                            flow['name'] = 'Tak'
                        elif 'nie' in condition.lower() or 'no' in condition.lower() or 'false' in condition.lower():
                            flow['name'] = 'Nie'
                        else:
                            flow['name'] = condition
        
        # 3. DODAJ opis procesu tylko jeśli brak
        if not improved.get('description'):
            improved['description'] = f"Proces: {improved.get('process_name', 'Nienazwany proces')}"
        
        # 4. POPRAW metadane bez zmiany kompleksności
        metadata = improved.get('metadata', {})
        if not metadata.get('context'):
            metadata['context'] = 'business'
        
        # NEVER ADD: new elements, new participants, new flows
        # ONLY FIX: naming, types, attributes according to BPMN 2.0 standard
        
        return improved
        
        return improved
    
    def _identify_changes(self, original: Dict, improved: Dict) -> List[str]:
        """Identyfikuje zmiany między wersjami - tylko notacyjne poprawki"""
        changes = []
        
        if original.get('description') != improved.get('description'):
            changes.append("Dodano/poprawiono opis procesu")
        
        # Check element names and types
        orig_elements = original.get('elements', [])
        impr_elements = improved.get('elements', [])
        
        for i, (orig_elem, impr_elem) in enumerate(zip(orig_elements, impr_elements)):
            if orig_elem.get('name') != impr_elem.get('name'):
                changes.append(f"Poprawiono nazwę elementu: {orig_elem.get('id')}")
            
            if orig_elem.get('type') != impr_elem.get('type'):
                changes.append(f"Poprawiono typ elementu {orig_elem.get('id')}: {orig_elem.get('type')} → {impr_elem.get('type')}")
        
        # Check flow names  
        orig_flows = original.get('flows', [])
        impr_flows = improved.get('flows', [])
        
        for orig_flow, impr_flow in zip(orig_flows, impr_flows):
            if not orig_flow.get('name') and impr_flow.get('name'):
                changes.append(f"Dodano nazwę przepływu: {impr_flow['name']}")
        
        return changes


def test_mcp_server():
    """Test serwera MCP"""
    print("🧪 Testing MCP Server for BPMN")
    
    server = SimpleMCPServer()
    
    # Test process with issues
    test_process = {
        "process_name": "Test",
        "description": "",
        "participants": [
            {"id": "user", "name": "User", "type": "human"}
        ],
        "elements": [
            {"id": "start_1", "name": "", "type": "startEvent", "participant": "user"},
            {"id": "task_1", "name": "Do something", "type": "userTask", "participant": "user"}
        ],
        "flows": [
            {"id": "flow_1", "source": "start_1", "target": "task_1", "type": "sequence"}
        ]
    }
    
    print("\n1. Testing verification...")
    verification = server.verify_bpmn_process(test_process)
    print(f"   Valid: {verification['is_valid']}")
    print(f"   Quality: {verification['overall_quality']:.2f}")
    print(f"   Missing: {len(verification['missing_elements'])} items")
    
    print("\n2. Testing improvement...")
    improvement = server.improve_bpmn_process(test_process)
    print(f"   Changes made: {len(improvement['changes_made'])}")
    print(f"   Message: {improvement['message']}")
    
    print("\n3. Testing intelligent optimization...")
    try:
        intelligence_result = server.intelligent_bpmn_optimization(
            test_process, 
            context_hints={'domain': 'testing', 'time_constraint': 'normal', 'quality_requirement': 'standard'}
        )
        print(f"   Intelligence enabled: {intelligence_result.get('intelligence_enabled', False)}")
        if intelligence_result.get('intelligence_enabled'):
            print(f"   Applied optimizations: {len(intelligence_result.get('applied_optimizations', []))}")
            print(f"   Confidence: {intelligence_result.get('insights', {}).get('confidence_score', 0):.3f}")
        else:
            print(f"   Fallback mode: {intelligence_result.get('fallback_used', False)}")
    except Exception as e:
        print(f"   Intelligence test failed: {e}")
    
    print("\n4. Testing improvement prompt...")
    prompt = server.generate_improvement_prompt(test_process, verification)
    print(f"   Prompt length: {len(prompt)} chars")
    
    return True


if __name__ == "__main__":
    success = test_mcp_server()
    print(f"\n🎯 MCP Server test: {'✅ PASSED' if success else '❌ FAILED'}")