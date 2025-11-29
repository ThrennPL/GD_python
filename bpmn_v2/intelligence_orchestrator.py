"""
Intelligence Orchestrator
Koordynuje wszystkie komponenty inteligencji dla optymalnej naprawy BPMN

Autor: AI Assistant
Data: 2025-11-29
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

# Import all intelligence components
try:
    from .ml_issue_predictor import MLIssuePredictor, IssuePrediction
    from .template_quick_fixes import TemplateQuickFixes, FixTemplate
    from .quality_degradation_detector import QualityDegradationDetector, DegradationAlert
    from .cross_process_learner import CrossProcessLearner, ProcessKnowledge
    from .adaptive_strategy_manager import AdaptiveStrategyManager, StrategyConfig, ContextFactors
except ImportError:
    # Fallback for direct execution
    from ml_issue_predictor import MLIssuePredictor, IssuePrediction
    from template_quick_fixes import TemplateQuickFixes, FixTemplate
    from quality_degradation_detector import QualityDegradationDetector, DegradationAlert
    from cross_process_learner import CrossProcessLearner, ProcessKnowledge
    from adaptive_strategy_manager import AdaptiveStrategyManager, StrategyConfig, ContextFactors

@dataclass
class IntelligenceInsights:
    """Wglądy z analizy inteligencji"""
    predicted_issues: List[IssuePrediction]
    recommended_templates: List[FixTemplate]
    quality_alerts: List[DegradationAlert]
    strategy_recommendation: StrategyConfig
    cross_process_recommendations: List[Dict]
    confidence_score: float
    processing_time: float

@dataclass
class OptimizationResult:
    """Wynik optymalizacji procesu"""
    optimized_process: Dict[str, Any]
    applied_optimizations: List[Dict]
    intelligence_insights: IntelligenceInsights
    performance_metrics: Dict[str, Any]
    recommendations: List[str]

class IntelligenceOrchestrator:
    """Orkiestrator inteligencji - koordynuje wszystkie komponenty AI"""
    
    def __init__(self, enable_learning: bool = True):
        # Initialize all intelligence components
        self.ml_predictor = MLIssuePredictor()
        self.template_engine = TemplateQuickFixes()
        self.quality_detector = QualityDegradationDetector()
        self.cross_learner = CrossProcessLearner() if enable_learning else None
        self.strategy_manager = AdaptiveStrategyManager()
        
        # Orchestrator state
        self.enable_learning = enable_learning
        self.session_history = []
        self.optimization_cache = {}
        
    def analyze_and_optimize(self, bpmn_json: Dict, issues: List[Dict],
                           context_hints: Optional[Dict] = None,
                           iteration_history: Optional[List[Dict]] = None) -> OptimizationResult:
        """Główna funkcja analizy i optymalizacji procesu BPMN"""
        
        start_time = datetime.now()
        
        # Phase 1: Intelligence Analysis
        insights = self._perform_intelligence_analysis(
            bpmn_json, issues, context_hints, iteration_history
        )
        
        # Phase 2: Strategy Selection
        selected_strategy = insights.strategy_recommendation
        
        # Phase 3: Process Optimization
        optimization_result = self._optimize_process(
            bpmn_json, issues, insights, selected_strategy
        )
        
        # Phase 4: Learning Update (if enabled)
        if self.enable_learning:
            self._update_learning_systems(bpmn_json, issues, optimization_result, insights)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        insights.processing_time = processing_time
        
        # Create final result
        result = OptimizationResult(
            optimized_process=optimization_result['optimized_process'],
            applied_optimizations=optimization_result['applied_optimizations'],
            intelligence_insights=insights,
            performance_metrics=self._calculate_performance_metrics(optimization_result, insights),
            recommendations=self._generate_recommendations(insights, optimization_result)
        )
        
        # Store in session history
        self.session_history.append({
            'timestamp': datetime.now(),
            'input_quality': self._estimate_quality(bpmn_json, issues),
            'output_quality': result.performance_metrics.get('estimated_quality', 0),
            'strategy_used': selected_strategy.strategy_type.value,
            'processing_time': processing_time
        })
        
        return result
    
    def _perform_intelligence_analysis(self, bpmn_json: Dict, issues: List[Dict],
                                     context_hints: Optional[Dict],
                                     iteration_history: Optional[List[Dict]]) -> IntelligenceInsights:
        """Wykonuje kompleksową analizę inteligencji"""
        
        # 1. ML Issue Prediction
        predicted_issues = self.ml_predictor.predict_issues(bpmn_json)
        
        # 2. Template Recommendations
        applicable_templates = self.template_engine.find_applicable_templates(bpmn_json, issues)
        
        # 3. Quality Degradation Analysis
        quality_alerts = []
        if iteration_history:
            for i, iteration in enumerate(iteration_history):
                alerts = self.quality_detector.add_iteration_metrics(
                    iteration.get('bpmn_json', bpmn_json),
                    iteration.get('verification_result', {}),
                    i + 1
                )
                quality_alerts.extend(alerts)
        
        # 4. Cross-Process Learning
        cross_process_recommendations = []
        if self.cross_learner:
            domain = context_hints.get('domain') if context_hints else None
            cross_process_recommendations = self.cross_learner.get_recommendations(
                bpmn_json, issues, domain
            )
        
        # 5. Strategy Selection
        strategy_recommendation = self.strategy_manager.select_strategy(
            bpmn_json, issues, context_hints
        )
        
        # 6. Calculate Confidence Score
        confidence_score = self._calculate_confidence_score(
            predicted_issues, applicable_templates, quality_alerts, cross_process_recommendations
        )
        
        return IntelligenceInsights(
            predicted_issues=predicted_issues,
            recommended_templates=applicable_templates,
            quality_alerts=quality_alerts,
            strategy_recommendation=strategy_recommendation,
            cross_process_recommendations=cross_process_recommendations,
            confidence_score=confidence_score,
            processing_time=0.0  # Will be set later
        )
    
    def _optimize_process(self, bpmn_json: Dict, issues: List[Dict],
                         insights: IntelligenceInsights,
                         strategy: StrategyConfig) -> Dict[str, Any]:
        """Optymalizuje proces na podstawie insights"""
        
        optimized_process = bpmn_json.copy()
        applied_optimizations = []
        
        # 1. Apply Template Fixes (if strategy allows)
        if strategy.template_usage and insights.recommended_templates:
            template_result = self.template_engine.apply_template_fixes(
                optimized_process,
                insights.recommended_templates[:3]  # Top 3 templates
            )
            
            if template_result['applied_fixes']:
                optimized_process = template_result['fixed_process']
                applied_optimizations.extend([{
                    'type': 'template_fix',
                    'details': fix,
                    'confidence': fix.get('confidence', 0.5)
                } for fix in template_result['applied_fixes']])
        
        # 2. Apply Predictive Fixes
        predictive_fixes = self._apply_predictive_fixes(
            optimized_process, insights.predicted_issues, strategy
        )
        applied_optimizations.extend(predictive_fixes)
        
        # 3. Apply Cross-Process Learning Recommendations
        if insights.cross_process_recommendations:
            learning_fixes = self._apply_learning_recommendations(
                optimized_process, insights.cross_process_recommendations[:2], strategy
            )
            applied_optimizations.extend(learning_fixes)
        
        # 4. Quality-based Optimizations
        quality_fixes = self._apply_quality_optimizations(
            optimized_process, insights.quality_alerts, strategy
        )
        applied_optimizations.extend(quality_fixes)
        
        return {
            'optimized_process': optimized_process,
            'applied_optimizations': applied_optimizations
        }
    
    def _apply_predictive_fixes(self, process: Dict, predictions: List[IssuePrediction],
                              strategy: StrategyConfig) -> List[Dict]:
        """Aplikuje naprawki na podstawie przewidywań ML"""
        applied_fixes = []
        
        # Filter predictions by confidence and strategy risk tolerance
        relevant_predictions = [
            p for p in predictions 
            if p.probability >= (1.0 - strategy.risk_tolerance)
        ]
        
        for prediction in relevant_predictions[:3]:  # Top 3 predictions
            if prediction.issue_type in ['STRUCT_001', 'STRUCT_004']:
                # Apply structural fixes
                fix_applied = self._apply_structural_prediction_fix(process, prediction)
                if fix_applied:
                    applied_fixes.append({
                        'type': 'predictive_fix',
                        'issue_type': prediction.issue_type,
                        'probability': prediction.probability,
                        'confidence': prediction.probability,
                        'description': f"Preventive fix for {prediction.issue_type}"
                    })
        
        return applied_fixes
    
    def _apply_structural_prediction_fix(self, process: Dict, prediction: IssuePrediction) -> bool:
        """Aplikuje strukturalne naprawki przewidywanej"""
        elements = process.get('elements', [])
        flows = process.get('flows', [])
        
        if prediction.issue_type == 'STRUCT_001':  # Missing start/end events
            # Add placeholders for missing events if predicted
            participants = process.get('participants', [])
            for participant in participants:
                pool_elements = [e for e in elements if e.get('participant') == participant.get('id')]
                start_events = [e for e in pool_elements if e.get('type') == 'startEvent']
                if not start_events and len(pool_elements) > 1:
                    # Add warning marker for missing start event
                    elements.append({
                        'id': f"predicted_start_{participant.get('id')}",
                        'name': f"Predicted Start Event",
                        'type': 'startEvent',
                        'participant': participant.get('id'),
                        'predicted': True
                    })
                    return True
        
        return False
    
    def _apply_learning_recommendations(self, process: Dict, recommendations: List[Dict],
                                      strategy: StrategyConfig) -> List[Dict]:
        """Aplikuje rekomendacje z cross-process learning"""
        applied_fixes = []
        
        for rec in recommendations:
            if rec.get('confidence', 0) >= 0.6:  # Confidence threshold
                # Apply high-confidence learning recommendations
                if rec.get('type') == 'successful_fix_pattern':
                    applied_fixes.append({
                        'type': 'learning_recommendation',
                        'description': rec.get('description', ''),
                        'confidence': rec.get('confidence', 0),
                        'source': rec.get('source_process', 'unknown')
                    })
        
        return applied_fixes
    
    def _apply_quality_optimizations(self, process: Dict, alerts: List[DegradationAlert],
                                   strategy: StrategyConfig) -> List[Dict]:
        """Aplikuje optymalizacje na podstawie alertów jakości"""
        applied_fixes = []
        
        # Handle critical quality alerts
        critical_alerts = [a for a in alerts if a.severity == 'critical']
        
        for alert in critical_alerts:
            if 'quality_drop' in alert.type.value:
                # Apply conservative fixes for quality drops
                applied_fixes.append({
                    'type': 'quality_stabilization',
                    'description': f"Applied conservative fix for: {alert.message}",
                    'confidence': alert.confidence,
                    'recommendation': alert.recommendation
                })
        
        return applied_fixes
    
    def _calculate_confidence_score(self, predictions: List[IssuePrediction],
                                  templates: List[FixTemplate],
                                  alerts: List[DegradationAlert],
                                  recommendations: List[Dict]) -> float:
        """Oblicza ogólny score pewności analiz"""
        
        confidence_factors = []
        
        # ML predictions confidence
        if predictions:
            avg_prediction_confidence = sum(p.probability for p in predictions) / len(predictions)
            confidence_factors.append(avg_prediction_confidence * 0.3)
        
        # Template confidence
        if templates:
            avg_template_confidence = sum(t.confidence for t in templates) / len(templates)
            confidence_factors.append(avg_template_confidence * 0.25)
        
        # Quality alerts (inverse - more alerts = less confidence)
        critical_alerts = len([a for a in alerts if a.severity == 'critical'])
        quality_confidence = max(0.0, 1.0 - (critical_alerts * 0.2))
        confidence_factors.append(quality_confidence * 0.2)
        
        # Cross-process recommendations
        if recommendations:
            avg_rec_confidence = sum(r.get('confidence', 0.5) for r in recommendations) / len(recommendations)
            confidence_factors.append(avg_rec_confidence * 0.25)
        
        return sum(confidence_factors) if confidence_factors else 0.5
    
    def _update_learning_systems(self, bpmn_json: Dict, issues: List[Dict],
                               optimization_result: Dict, insights: IntelligenceInsights) -> None:
        """Aktualizuje systemy uczenia"""
        
        if not self.cross_learner:
            return
        
        # Extract quality metrics
        estimated_quality = self._estimate_quality(
            optimization_result['optimized_process'],
            []  # Assume optimized process has fewer issues
        )
        
        # Learn from the optimization process
        self.cross_learner.learn_from_process(
            process_data=bpmn_json,
            improvements=optimization_result['applied_optimizations'],
            final_quality=estimated_quality,
            domain=None  # Could be extracted from context
        )
        
        # Update ML predictor with actual vs predicted issues
        compliance_issues = [{'rule_code': issue.get('rule_code', ''), 'element_id': issue.get('element_id', '')} for issue in issues]
        self.ml_predictor.learn_from_process(bpmn_json, compliance_issues, estimated_quality)
    
    def _estimate_quality(self, bpmn_json: Dict, issues: List[Dict]) -> float:
        """Estymuje jakość procesu"""
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        flows = bpmn_json.get('flows', [])
        
        # Basic quality estimation
        base_quality = 1.0
        
        # Penalize for issues
        critical_issues = len([i for i in issues if i.get('severity') == 'critical'])
        major_issues = len([i for i in issues if i.get('severity') == 'major'])
        
        base_quality -= (critical_issues * 0.1) + (major_issues * 0.05)
        
        # Boost for completeness
        if participants:
            pools_with_start = 0
            pools_with_end = 0
            
            for participant in participants:
                pool_elements = [e for e in elements if e.get('participant') == participant.get('id')]
                if any(e.get('type') == 'startEvent' for e in pool_elements):
                    pools_with_start += 1
                if any(e.get('type') == 'endEvent' for e in pool_elements):
                    pools_with_end += 1
            
            completeness = (pools_with_start + pools_with_end) / (2 * len(participants))
            base_quality = (base_quality + completeness) / 2
        
        return max(0.0, min(1.0, base_quality))
    
    def _calculate_performance_metrics(self, optimization_result: Dict,
                                     insights: IntelligenceInsights) -> Dict[str, Any]:
        """Oblicza metryki wydajności"""
        
        applied_optimizations = optimization_result['applied_optimizations']
        
        return {
            'optimizations_applied': len(applied_optimizations),
            'template_fixes': len([o for o in applied_optimizations if o.get('type') == 'template_fix']),
            'predictive_fixes': len([o for o in applied_optimizations if o.get('type') == 'predictive_fix']),
            'learning_recommendations': len([o for o in applied_optimizations if o.get('type') == 'learning_recommendation']),
            'confidence_score': insights.confidence_score,
            'processing_time': insights.processing_time,
            'estimated_quality': self._estimate_quality(optimization_result['optimized_process'], []),
            'strategy_used': insights.strategy_recommendation.strategy_type.value
        }
    
    def _generate_recommendations(self, insights: IntelligenceInsights,
                                optimization_result: Dict) -> List[str]:
        """Generuje rekomendacje na podstawie analizy"""
        recommendations = []
        
        # Strategy recommendations
        strategy = insights.strategy_recommendation
        recommendations.append(
            f"Selected {strategy.strategy_type.value} strategy with {strategy.ai_calls_limit} AI calls limit"
        )
        
        # Quality alerts recommendations
        critical_alerts = [a for a in insights.quality_alerts if a.severity == 'critical']
        if critical_alerts:
            recommendations.append(
                f"⚠️  {len(critical_alerts)} critical quality alerts detected - manual review recommended"
            )
        
        # Predictive recommendations
        high_prob_predictions = [p for p in insights.predicted_issues if p.probability > 0.8]
        if high_prob_predictions:
            recommendations.append(
                f"🔮 High probability issues predicted: {[p.issue_type for p in high_prob_predictions]}"
            )
        
        # Cross-process learning recommendations
        if insights.cross_process_recommendations:
            recommendations.append(
                f"📚 {len(insights.cross_process_recommendations)} recommendations from similar processes available"
            )
        
        # Performance recommendations
        if insights.confidence_score < 0.6:
            recommendations.append(
                "⚡ Low confidence score - consider manual validation of optimizations"
            )
        
        return recommendations
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie inteligencji systemu"""
        
        summary = {
            'components_status': {
                'ml_predictor': self._get_predictor_status(),
                'template_engine': self._get_template_status(),
                'quality_detector': self._get_quality_detector_status(),
                'cross_learner': self._get_cross_learner_status(),
                'strategy_manager': self._get_strategy_manager_status()
            },
            'session_statistics': self._get_session_statistics(),
            'learning_insights': self._get_learning_insights()
        }
        
        return summary
    
    def _get_predictor_status(self) -> Dict[str, Any]:
        """Status przewidywacza ML"""
        return self.ml_predictor.get_learning_stats()
    
    def _get_template_status(self) -> Dict[str, Any]:
        """Status silnika szablonów"""
        return self.template_engine.get_template_stats()
    
    def _get_quality_detector_status(self) -> Dict[str, Any]:
        """Status detektora jakości"""
        return self.quality_detector.get_degradation_summary()
    
    def _get_cross_learner_status(self) -> Dict[str, Any]:
        """Status cross-process learnera"""
        if self.cross_learner:
            return self.cross_learner.get_learning_insights()
        return {'status': 'disabled'}
    
    def _get_strategy_manager_status(self) -> Dict[str, Any]:
        """Status managera strategii"""
        return self.strategy_manager.get_strategy_insights()
    
    def _get_session_statistics(self) -> Dict[str, Any]:
        """Statystyki sesji"""
        if not self.session_history:
            return {'message': 'No session data yet'}
        
        return {
            'total_optimizations': len(self.session_history),
            'average_processing_time': sum(s['processing_time'] for s in self.session_history) / len(self.session_history),
            'quality_improvement': self._calculate_average_quality_improvement(),
            'most_used_strategy': self._get_most_used_strategy()
        }
    
    def _calculate_average_quality_improvement(self) -> float:
        """Oblicza średnią poprawę jakości"""
        if not self.session_history:
            return 0.0
        
        improvements = []
        for session in self.session_history:
            improvement = session['output_quality'] - session['input_quality']
            improvements.append(improvement)
        
        return sum(improvements) / len(improvements)
    
    def _get_most_used_strategy(self) -> str:
        """Zwraca najczęściej używaną strategię"""
        if not self.session_history:
            return 'none'
        
        strategies = [s['strategy_used'] for s in self.session_history]
        return max(set(strategies), key=strategies.count)
    
    def _get_learning_insights(self) -> Dict[str, Any]:
        """Zwraca ogólne wglądy z uczenia"""
        insights = {}
        
        if self.cross_learner:
            insights['cross_process'] = self.cross_learner.get_learning_insights()
        
        insights['ml_predictions'] = self.ml_predictor.get_learning_stats()
        insights['strategy_performance'] = self.strategy_manager.get_strategy_insights()
        
        return insights