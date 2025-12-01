"""
Quality Degradation Detection System
Wykrywa obniżenie jakości w procesie iteracyjnej naprawy

Autor: AI Assistant
Data: 2025-11-29
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from enum import Enum

class DegradationType(Enum):
    QUALITY_DROP = "quality_drop"
    STUCK_IN_LOOP = "stuck_in_loop"
    OSCILLATING_METRICS = "oscillating_metrics"
    COMPLEXITY_EXPLOSION = "complexity_explosion"
    NO_PROGRESS = "no_progress"

@dataclass
class QualityMetrics:
    """Metryki jakości dla pojedynczej iteracji"""
    iteration: int
    overall_quality: float
    compliance_score: float
    completeness: float
    connectivity: float
    naming_quality: float
    elements_count: int
    flows_count: int
    participants_count: int
    critical_issues: int
    major_issues: int
    timestamp: datetime

@dataclass
class DegradationAlert:
    """Alert o degradacji jakości"""
    type: DegradationType
    severity: str  # 'warning', 'critical'
    message: str
    affected_metrics: List[str]
    recommendation: str
    detected_at_iteration: int
    confidence: float

class QualityDegradationDetector:
    """Detektor degradacji jakości w iteracyjnym procesie poprawy BPMN"""
    
    def __init__(self, quality_threshold: float = 0.05, 
                 stuck_threshold: int = 3, oscillation_threshold: float = 0.1):
        self.quality_threshold = quality_threshold  # Minimum progress per iteration
        self.stuck_threshold = stuck_threshold      # Iterations without progress
        self.oscillation_threshold = oscillation_threshold  # Max oscillation allowed
        
        self.metrics_history = []
        self.alerts = []
        self.degradation_patterns = {
            'quality_drops': [],
            'stuck_iterations': 0,
            'oscillation_cycles': 0
        }
    
    def add_iteration_metrics(self, bpmn_json: Dict, verification_result: Dict, 
                            iteration: int) -> List[DegradationAlert]:
        """Dodaje metryki iteracji i wykrywa degradację"""
        
        # Extract metrics
        metrics = self._extract_metrics(bpmn_json, verification_result, iteration)
        self.metrics_history.append(metrics)
        
        # Detect degradation patterns
        new_alerts = []
        
        if len(self.metrics_history) >= 2:
            new_alerts.extend(self._detect_quality_drop())
            new_alerts.extend(self._detect_stuck_progress())
            
        if len(self.metrics_history) >= 3:
            new_alerts.extend(self._detect_oscillation())
            new_alerts.extend(self._detect_complexity_explosion())
            
        if len(self.metrics_history) >= 4:
            new_alerts.extend(self._detect_no_progress_pattern())
        
        self.alerts.extend(new_alerts)
        return new_alerts
    
    def _extract_metrics(self, bpmn_json: Dict, verification_result: Dict, 
                        iteration: int) -> QualityMetrics:
        """Wyciąga metryki z wyników weryfikacji"""
        
        # Basic counts
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        participants = bpmn_json.get('participants', [])
        
        # Quality metrics
        overall_quality = verification_result.get('overall_quality', 0.0)
        
        # Quality components
        quality_metrics = verification_result.get('quality_metrics', {})
        compliance_score = quality_metrics.get('compliance_score', 0.0)
        completeness = quality_metrics.get('completeness', 0.0)
        connectivity = quality_metrics.get('connectivity', 0.0)
        naming_quality = quality_metrics.get('naming_quality', 0.0)
        
        # Issue counts
        bpmn_compliance = verification_result.get('bpmn_compliance', {})
        issues = bpmn_compliance.get('issues', [])
        critical_issues = len([i for i in issues if i.get('severity') == 'critical'])
        major_issues = len([i for i in issues if i.get('severity') == 'major'])
        
        return QualityMetrics(
            iteration=iteration,
            overall_quality=overall_quality,
            compliance_score=compliance_score,
            completeness=completeness,
            connectivity=connectivity,
            naming_quality=naming_quality,
            elements_count=len(elements),
            flows_count=len(flows),
            participants_count=len(participants),
            critical_issues=critical_issues,
            major_issues=major_issues,
            timestamp=datetime.now()
        )
    
    def _detect_quality_drop(self) -> List[DegradationAlert]:
        """Wykrywa gwałtowny spadek jakości"""
        alerts = []
        
        if len(self.metrics_history) < 2:
            return alerts
        
        current = self.metrics_history[-1]
        previous = self.metrics_history[-2]
        
        # Check overall quality drop
        quality_drop = previous.overall_quality - current.overall_quality
        
        if quality_drop > self.quality_threshold:
            self.degradation_patterns['quality_drops'].append(current.iteration)
            
            severity = 'critical' if quality_drop > 0.2 else 'warning'
            
            alerts.append(DegradationAlert(
                type=DegradationType.QUALITY_DROP,
                severity=severity,
                message=f'Quality dropped by {quality_drop:.3f} from {previous.overall_quality:.3f} to {current.overall_quality:.3f}',
                affected_metrics=['overall_quality'],
                recommendation='Rollback to previous iteration or apply conservative fixes',
                detected_at_iteration=current.iteration,
                confidence=min(1.0, quality_drop * 5)  # Higher drop = higher confidence
            ))
        
        # Check individual metric drops
        metric_drops = {
            'compliance_score': previous.compliance_score - current.compliance_score,
            'completeness': previous.completeness - current.completeness,
            'connectivity': previous.connectivity - current.connectivity,
            'naming_quality': previous.naming_quality - current.naming_quality
        }
        
        for metric_name, drop in metric_drops.items():
            if drop > 0.15:  # Significant drop in individual metric
                alerts.append(DegradationAlert(
                    type=DegradationType.QUALITY_DROP,
                    severity='warning',
                    message=f'{metric_name} dropped by {drop:.3f}',
                    affected_metrics=[metric_name],
                    recommendation=f'Focus improvements on {metric_name}',
                    detected_at_iteration=current.iteration,
                    confidence=min(1.0, drop * 3)
                ))
        
        return alerts
    
    def _detect_stuck_progress(self) -> List[DegradationAlert]:
        """Wykrywa brak postępu w iteracjach"""
        alerts = []
        
        if len(self.metrics_history) < self.stuck_threshold:
            return alerts
        
        # Check last N iterations for progress
        recent_metrics = self.metrics_history[-self.stuck_threshold:]
        quality_values = [m.overall_quality for m in recent_metrics]
        
        # Calculate progress over recent iterations
        quality_range = max(quality_values) - min(quality_values)
        
        if quality_range < self.quality_threshold:
            self.degradation_patterns['stuck_iterations'] += 1
            
            current = self.metrics_history[-1]
            
            alerts.append(DegradationAlert(
                type=DegradationType.STUCK_IN_LOOP,
                severity='warning',
                message=f'No significant progress in last {self.stuck_threshold} iterations (range: {quality_range:.4f})',
                affected_metrics=['overall_quality'],
                recommendation='Try different improvement strategy or increase AI creativity',
                detected_at_iteration=current.iteration,
                confidence=1.0 - quality_range  # Less range = higher confidence
            ))
        
        return alerts
    
    def _detect_oscillation(self) -> List[DegradationAlert]:
        """Wykrywa oscylację metryk"""
        alerts = []
        
        if len(self.metrics_history) < 4:
            return alerts
        
        # Check for oscillation patterns in quality metrics
        recent_metrics = self.metrics_history[-4:]
        
        # Check if quality is oscillating up-down-up-down
        quality_values = [m.overall_quality for m in recent_metrics]
        
        # Simple oscillation detection: if direction changes too frequently
        direction_changes = 0
        for i in range(1, len(quality_values) - 1):
            trend_before = quality_values[i] - quality_values[i-1]
            trend_after = quality_values[i+1] - quality_values[i]
            
            # Direction change detected
            if (trend_before > 0 and trend_after < 0) or (trend_before < 0 and trend_after > 0):
                if abs(trend_before) > self.oscillation_threshold or abs(trend_after) > self.oscillation_threshold:
                    direction_changes += 1
        
        if direction_changes >= 2:  # Too many direction changes
            self.degradation_patterns['oscillation_cycles'] += 1
            
            current = self.metrics_history[-1]
            
            alerts.append(DegradationAlert(
                type=DegradationType.OSCILLATING_METRICS,
                severity='warning',
                message=f'Quality metrics oscillating over last 4 iterations (changes: {direction_changes})',
                affected_metrics=['overall_quality'],
                recommendation='Reduce improvement aggressiveness or use dampening factor',
                detected_at_iteration=current.iteration,
                confidence=min(1.0, direction_changes / 3.0)
            ))
        
        return alerts
    
    def _detect_complexity_explosion(self) -> List[DegradationAlert]:
        """Wykrywa eksplozję złożoności"""
        alerts = []
        
        if len(self.metrics_history) < 3:
            return alerts
        
        current = self.metrics_history[-1]
        initial = self.metrics_history[0]
        
        # Check for significant growth in complexity
        element_growth = (current.elements_count - initial.elements_count) / max(1, initial.elements_count)
        flow_growth = (current.flows_count - initial.flows_count) / max(1, initial.flows_count)
        
        # Alert if complexity grew significantly without quality improvement
        quality_improvement = current.overall_quality - initial.overall_quality
        
        if (element_growth > 0.5 or flow_growth > 0.7) and quality_improvement < 0.1:
            alerts.append(DegradationAlert(
                type=DegradationType.COMPLEXITY_EXPLOSION,
                severity='warning',
                message=f'Complexity increased significantly (elements: +{element_growth:.1%}, flows: +{flow_growth:.1%}) with minimal quality gain',
                affected_metrics=['elements_count', 'flows_count'],
                recommendation='Simplify process structure or focus on quality over quantity',
                detected_at_iteration=current.iteration,
                confidence=max(element_growth, flow_growth)
            ))
        
        return alerts
    
    def _detect_no_progress_pattern(self) -> List[DegradationAlert]:
        """Wykrywa wzorce braku postępu"""
        alerts = []
        
        if len(self.metrics_history) < 5:
            return alerts
        
        # Check if critical issues persist across iterations
        recent_metrics = self.metrics_history[-5:]
        critical_issues_trend = [m.critical_issues for m in recent_metrics]
        
        # If critical issues haven't decreased significantly
        if critical_issues_trend[0] > 0 and critical_issues_trend[-1] >= critical_issues_trend[0] * 0.7:
            current = self.metrics_history[-1]
            
            alerts.append(DegradationAlert(
                type=DegradationType.NO_PROGRESS,
                severity='critical',
                message=f'Critical issues persist: {critical_issues_trend[0]} → {critical_issues_trend[-1]} over 5 iterations',
                affected_metrics=['critical_issues'],
                recommendation='Manual intervention required - automatic fixes insufficient',
                detected_at_iteration=current.iteration,
                confidence=0.9
            ))
        
        return alerts
    
    def should_stop_iterations(self) -> Tuple[bool, str]:
        """Określa czy należy zatrzymać iteracje"""
        if not self.alerts:
            return False, ""
        
        recent_alerts = [a for a in self.alerts if 
                        len(self.metrics_history) - a.detected_at_iteration <= 3]
        
        # Stop if multiple critical alerts
        critical_alerts = [a for a in recent_alerts if a.severity == 'critical']
        if len(critical_alerts) >= 2:
            return True, f'Multiple critical degradation alerts: {[a.type.value for a in critical_alerts]}'
        
        # Stop if stuck for too long
        if self.degradation_patterns['stuck_iterations'] >= 2:
            return True, 'Process stuck without progress for multiple cycles'
        
        # Stop if oscillating severely
        if self.degradation_patterns['oscillation_cycles'] >= 3:
            return True, 'Severe quality oscillation detected'
        
        return False, ""
    
    def get_quality_trend(self) -> Dict[str, Any]:
        """Zwraca trend jakości"""
        if not self.metrics_history:
            return {'trend': 'no_data'}
        
        quality_values = [m.overall_quality for m in self.metrics_history]
        
        if len(quality_values) < 2:
            return {'trend': 'insufficient_data', 'current_quality': quality_values[0]}
        
        # Calculate overall trend
        initial_quality = quality_values[0]
        current_quality = quality_values[-1]
        overall_change = current_quality - initial_quality
        
        # Calculate recent trend (last 3 iterations)
        recent_values = quality_values[-min(3, len(quality_values)):]
        recent_trend = recent_values[-1] - recent_values[0] if len(recent_values) > 1 else 0
        
        # Classify trend
        if overall_change > 0.1:
            trend_class = 'improving'
        elif overall_change < -0.1:
            trend_class = 'degrading'
        else:
            trend_class = 'stable'
        
        return {
            'trend': trend_class,
            'overall_change': overall_change,
            'recent_trend': recent_trend,
            'current_quality': current_quality,
            'peak_quality': max(quality_values),
            'iterations_count': len(quality_values),
            'quality_variance': np.var(quality_values) if len(quality_values) > 1 else 0
        }
    
    def get_degradation_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie degradacji"""
        return {
            'total_alerts': len(self.alerts),
            'critical_alerts': len([a for a in self.alerts if a.severity == 'critical']),
            'warning_alerts': len([a for a in self.alerts if a.severity == 'warning']),
            'degradation_patterns': self.degradation_patterns.copy(),
            'quality_trend': self.get_quality_trend(),
            'should_stop': self.should_stop_iterations(),
            'latest_alerts': self.alerts[-3:] if len(self.alerts) >= 3 else self.alerts
        }
