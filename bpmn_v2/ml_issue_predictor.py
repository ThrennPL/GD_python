"""
ML-Based Issue Prediction Engine
Przewiduje potencjalne problemy BPMN na podstawie wzorców

Autor: AI Assistant
Data: 2025-11-29
"""

from typing import Dict, List, Any, Tuple, Optional
import json
import numpy as np
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProcessPattern:
    """Wzorzec procesu do analizy ML"""
    elements_count: int
    participants_count: int
    flows_count: int
    gateways_count: int
    start_events: int
    end_events: int
    complexity_score: float
    issue_types: List[str]
    quality_score: float

@dataclass
class IssuePrediction:
    """Przewidywanie problemu BPMN"""
    issue_type: str
    probability: float
    confidence: str  # 'high', 'medium', 'low'
    prevention_tip: str
    affected_elements: List[str]

class MLIssuePredictor:
    """Silnik przewidywania problemów BPMN opartych na ML"""
    
    def __init__(self):
        self.patterns_database = []
        self.issue_frequency = defaultdict(int)
        self.element_risk_scores = defaultdict(float)
        self.correlation_matrix = {}
        
    def learn_from_process(self, bpmn_json: Dict, compliance_issues: List[Dict], 
                          quality_score: float) -> None:
        """Uczy się z analizowanego procesu"""
        pattern = self._extract_pattern(bpmn_json, compliance_issues, quality_score)
        self.patterns_database.append(pattern)
        
        # Update issue frequency
        for issue_type in pattern.issue_types:
            self.issue_frequency[issue_type] += 1
            
        # Update element risk scores
        self._update_risk_scores(bpmn_json, compliance_issues)
        
        # Update correlations every 10 patterns
        if len(self.patterns_database) % 10 == 0:
            self._update_correlations()
    
    def predict_issues(self, bpmn_json: Dict) -> List[IssuePrediction]:
        """Przewiduje potencjalne problemy dla nowego procesu"""
        predictions = []
        
        if not self.patterns_database:
            return self._get_baseline_predictions(bpmn_json)
        
        current_pattern = self._extract_pattern(bpmn_json, [], 0.0)
        
        # Find similar patterns
        similar_patterns = self._find_similar_patterns(current_pattern)
        
        # Predict based on similar patterns
        for pattern in similar_patterns[:5]:  # Top 5 similar
            for issue_type in pattern.issue_types:
                probability = self._calculate_probability(current_pattern, issue_type)
                if probability > 0.3:  # Threshold for meaningful prediction
                    predictions.append(IssuePrediction(
                        issue_type=issue_type,
                        probability=probability,
                        confidence=self._get_confidence_level(probability),
                        prevention_tip=self._get_prevention_tip(issue_type),
                        affected_elements=self._identify_affected_elements(bpmn_json, issue_type)
                    ))
        
        # Remove duplicates and sort by probability
        unique_predictions = self._deduplicate_predictions(predictions)
        return sorted(unique_predictions, key=lambda x: x.probability, reverse=True)
    
    def _extract_pattern(self, bpmn_json: Dict, issues: List[Dict], 
                        quality_score: float) -> ProcessPattern:
        """Wyciąga wzorzec z procesu BPMN"""
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        flows = bpmn_json.get('flows', [])
        
        gateways = [e for e in elements if 'gateway' in e.get('type', '').lower()]
        start_events = [e for e in elements if e.get('type') == 'startEvent']
        end_events = [e for e in elements if e.get('type') == 'endEvent']
        
        complexity_score = self._calculate_complexity(elements, flows, participants)
        issue_types = [issue.get('rule_code', '') for issue in issues]
        
        return ProcessPattern(
            elements_count=len(elements),
            participants_count=len(participants),
            flows_count=len(flows),
            gateways_count=len(gateways),
            start_events=len(start_events),
            end_events=len(end_events),
            complexity_score=complexity_score,
            issue_types=issue_types,
            quality_score=quality_score
        )
    
    def _calculate_complexity(self, elements: List[Dict], flows: List[Dict], 
                            participants: List[Dict]) -> float:
        """Oblicza score złożoności procesu"""
        base_complexity = len(elements) * 0.1
        flow_complexity = len(flows) * 0.05
        participant_complexity = len(participants) * 0.2
        
        # Gateway complexity bonus
        gateways = [e for e in elements if 'gateway' in e.get('type', '').lower()]
        gateway_complexity = len(gateways) * 0.3
        
        return min(10.0, base_complexity + flow_complexity + participant_complexity + gateway_complexity)
    
    def _find_similar_patterns(self, target_pattern: ProcessPattern) -> List[ProcessPattern]:
        """Znajduje podobne wzorce w bazie danych"""
        similarities = []
        
        for pattern in self.patterns_database:
            similarity = self._calculate_similarity(target_pattern, pattern)
            similarities.append((similarity, pattern))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [pattern for _, pattern in similarities]
    
    def _calculate_similarity(self, pattern1: ProcessPattern, pattern2: ProcessPattern) -> float:
        """Oblicza podobieństwo między wzorcami (0-1)"""
        # Normalized differences
        element_diff = abs(pattern1.elements_count - pattern2.elements_count) / max(pattern1.elements_count, pattern2.elements_count, 1)
        participant_diff = abs(pattern1.participants_count - pattern2.participants_count) / max(pattern1.participants_count, pattern2.participants_count, 1)
        complexity_diff = abs(pattern1.complexity_score - pattern2.complexity_score) / max(pattern1.complexity_score, pattern2.complexity_score, 1)
        
        # Calculate similarity (1 - average difference)
        avg_diff = (element_diff + participant_diff + complexity_diff) / 3.0
        return max(0, 1 - avg_diff)
    
    def _calculate_probability(self, current_pattern: ProcessPattern, issue_type: str) -> float:
        """Oblicza prawdopodobieństwo wystąpienia problemu"""
        base_frequency = self.issue_frequency[issue_type] / max(1, len(self.patterns_database))
        
        # Adjust based on complexity
        complexity_factor = min(1.5, current_pattern.complexity_score / 5.0)
        
        # Adjust based on element risk scores
        risk_factor = self.element_risk_scores.get(issue_type, 0.5)
        
        return min(1.0, base_frequency * complexity_factor * risk_factor)
    
    def _update_risk_scores(self, bpmn_json: Dict, issues: List[Dict]) -> None:
        """Aktualizuje scores ryzyka dla elementów"""
        elements = bpmn_json.get('elements', [])
        
        for issue in issues:
            issue_type = issue.get('rule_code', '')
            element_id = issue.get('element_id', '')
            
            # Increase risk for this issue type
            self.element_risk_scores[issue_type] += 0.1
    
    def _get_confidence_level(self, probability: float) -> str:
        """Określa poziom pewności przewidywania"""
        if probability >= 0.8:
            return 'high'
        elif probability >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _get_prevention_tip(self, issue_type: str) -> str:
        """Zwraca tip zapobiegania problemowi"""
        prevention_tips = {
            'STRUCT_001': 'Upewnij się, że każdy Pool ma Start i End Event',
            'STRUCT_004': 'Każdy Exclusive Gateway musi mieć co najmniej 2 przepływy wyjściowe', 
            'STRUCT_003': 'Sprawdź poprawność połączeń Sequence Flow',
            'STRUCT_009': 'End Event z Message Flow musi być typu Message',
            'SEM_001': 'Nadaj znaczące nazwy wszystkim elementom procesu',
            'STYLE_001': 'Unikaj zbyt długich nazw elementów'
        }
        
        return prevention_tips.get(issue_type, 'Sprawdź dokumentację BPMN 2.0')
    
    def _identify_affected_elements(self, bpmn_json: Dict, issue_type: str) -> List[str]:
        """Identyfikuje elementy, których może dotyczyć problem"""
        elements = bpmn_json.get('elements', [])
        
        if 'STRUCT_001' in issue_type:  # Start/End Events
            return [e['id'] for e in elements if e.get('type') in ['startEvent', 'endEvent']]
        elif 'STRUCT_004' in issue_type:  # Gateways
            return [e['id'] for e in elements if 'gateway' in e.get('type', '').lower()]
        elif 'STRUCT_009' in issue_type:  # Message Flow
            return [e['id'] for e in elements if e.get('type') == 'endEvent']
        
        return []
    
    def _deduplicate_predictions(self, predictions: List[IssuePrediction]) -> List[IssuePrediction]:
        """Usuwa duplikaty przewidywań"""
        seen = set()
        unique = []
        
        for pred in predictions:
            key = f"{pred.issue_type}_{pred.probability:.2f}"
            if key not in seen:
                seen.add(key)
                unique.append(pred)
        
        return unique
    
    def _get_baseline_predictions(self, bpmn_json: Dict) -> List[IssuePrediction]:
        """Bazowe przewidywania dla nowych systemów bez historii"""
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        
        predictions = []
        
        # High probability issues for complex processes
        if len(participants) > 3:
            predictions.append(IssuePrediction(
                issue_type='STRUCT_008',
                probability=0.7,
                confidence='medium',
                prevention_tip='Sprawdź poprawność Message Flow między Pool',
                affected_elements=[p['id'] for p in participants]
            ))
        
        # Gateway issues for processes with multiple paths
        gateways = [e for e in elements if 'gateway' in e.get('type', '').lower()]
        if gateways:
            predictions.append(IssuePrediction(
                issue_type='STRUCT_004',
                probability=0.6,
                confidence='medium',
                prevention_tip='Sprawdź czy każdy Gateway ma wystarczające przepływy',
                affected_elements=[g['id'] for g in gateways]
            ))
        
        return predictions
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki uczenia"""
        return {
            'patterns_learned': len(self.patterns_database),
            'most_common_issues': dict(Counter(self.issue_frequency).most_common(5)),
            'average_quality': np.mean([p.quality_score for p in self.patterns_database]) if self.patterns_database else 0,
            'complexity_distribution': {
                'low': len([p for p in self.patterns_database if p.complexity_score < 3]),
                'medium': len([p for p in self.patterns_database if 3 <= p.complexity_score < 7]),
                'high': len([p for p in self.patterns_database if p.complexity_score >= 7])
            }
        }
