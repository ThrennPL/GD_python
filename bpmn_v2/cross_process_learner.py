"""
Cross-Process Learning Engine
Uczy się z różnych procesów BPMN i buduje bazę wiedzy

Autor: AI Assistant
Data: 2025-11-29
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
import json
import hashlib
from datetime import datetime
import numpy as np

@dataclass
class ProcessKnowledge:
    """Wiedza wydobyta z procesu BPMN"""
    process_id: str
    process_hash: str
    domain: Optional[str]
    patterns: Dict[str, Any]
    successful_fixes: List[Dict]
    failed_fixes: List[Dict]
    quality_evolution: List[float]
    lessons_learned: List[str]
    created_at: datetime

@dataclass
class FixPattern:
    """Wzorzec naprawki"""
    pattern_id: str
    fix_type: str
    success_rate: float
    applicable_conditions: Dict[str, Any]
    fix_steps: List[Dict]
    confidence: float
    usage_count: int

class CrossProcessLearner:
    """Silnik uczenia międzyprocesowego"""
    
    def __init__(self):
        self.knowledge_base = []
        self.fix_patterns = {}
        self.domain_insights = defaultdict(list)
        self.success_statistics = defaultdict(int)
        self.pattern_effectiveness = {}
        
    def learn_from_process(self, process_data: Dict, improvements: List[Dict], 
                          final_quality: float, domain: Optional[str] = None) -> ProcessKnowledge:
        """Uczy się z kompletnego procesu naprawy"""
        
        process_id = self._generate_process_id(process_data)
        process_hash = self._calculate_process_hash(process_data)
        
        # Extract patterns from the process
        patterns = self._extract_process_patterns(process_data)
        
        # Classify fixes as successful/failed
        successful_fixes, failed_fixes = self._classify_fixes(improvements, final_quality)
        
        # Extract quality evolution
        quality_evolution = self._extract_quality_evolution(improvements)
        
        # Generate lessons learned
        lessons_learned = self._generate_lessons(improvements, final_quality, patterns)
        
        # Create knowledge entry
        knowledge = ProcessKnowledge(
            process_id=process_id,
            process_hash=process_hash,
            domain=domain,
            patterns=patterns,
            successful_fixes=successful_fixes,
            failed_fixes=failed_fixes,
            quality_evolution=quality_evolution,
            lessons_learned=lessons_learned,
            created_at=datetime.now()
        )
        
        # Add to knowledge base
        self.knowledge_base.append(knowledge)
        
        # Update fix patterns
        self._update_fix_patterns(successful_fixes, patterns)
        
        # Update domain insights
        if domain:
            self.domain_insights[domain].append(knowledge)
        
        # Update statistics
        self._update_statistics(improvements, final_quality)
        
        return knowledge
    
    def get_recommendations(self, current_process: Dict, current_issues: List[Dict], 
                          domain: Optional[str] = None) -> List[Dict]:
        """Zwraca rekomendacje na podstawie podobnych procesów"""
        
        if not self.knowledge_base:
            return self._get_baseline_recommendations()
        
        # Find similar processes
        similar_processes = self._find_similar_processes(current_process, domain)
        
        # Get recommendations from similar processes
        recommendations = []
        
        for similar_process, similarity_score in similar_processes[:5]:
            process_recommendations = self._extract_recommendations(
                similar_process, current_issues, similarity_score
            )
            recommendations.extend(process_recommendations)
        
        # Rank and deduplicate recommendations
        ranked_recommendations = self._rank_recommendations(recommendations)
        
        return ranked_recommendations[:10]  # Top 10 recommendations
    
    def _generate_process_id(self, process_data: Dict) -> str:
        """Generuje unikalny ID procesu"""
        elements = process_data.get('elements', [])
        participants = process_data.get('participants', [])
        
        # Create signature based on structure
        signature_parts = [
            str(len(elements)),
            str(len(participants)),
            '_'.join(sorted([e.get('type', '') for e in elements]))
        ]
        
        signature = '_'.join(signature_parts)
        return f"process_{hashlib.md5(signature.encode()).hexdigest()[:8]}"
    
    def _calculate_process_hash(self, process_data: Dict) -> str:
        """Oblicza hash procesu dla detekcji duplikatów"""
        # Normalize process data for hashing
        normalized = {
            'element_types': sorted([e.get('type', '') for e in process_data.get('elements', [])]),
            'participant_count': len(process_data.get('participants', [])),
            'flow_count': len(process_data.get('flows', []))
        }
        
        hash_string = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def _extract_process_patterns(self, process_data: Dict) -> Dict[str, Any]:
        """Wydobywa wzorce z procesu"""
        elements = process_data.get('elements', [])
        flows = process_data.get('flows', [])
        participants = process_data.get('participants', [])
        
        patterns = {
            'structure': {
                'elements_count': len(elements),
                'participants_count': len(participants),
                'flows_count': len(flows),
                'element_types': Counter([e.get('type', '') for e in elements]),
                'complexity_score': self._calculate_complexity_score(elements, flows, participants)
            },
            'connectivity': {
                'avg_connections_per_element': len(flows) / max(1, len(elements)),
                'orphaned_elements': self._count_orphaned_elements(elements, flows),
                'gateway_complexity': self._analyze_gateway_complexity(elements, flows)
            },
            'participants': {
                'cross_participant_flows': self._count_cross_participant_flows(flows, elements),
                'participant_balance': self._analyze_participant_balance(participants, elements)
            }
        }
        
        return patterns
    
    def _classify_fixes(self, improvements: List[Dict], final_quality: float) -> Tuple[List[Dict], List[Dict]]:
        """Klasyfikuje naprawki jako udane/nieudane"""
        successful = []
        failed = []
        
        for improvement in improvements:
            quality_before = improvement.get('quality_before', 0)
            quality_after = improvement.get('quality_after', 0)
            
            if quality_after > quality_before:
                successful.append(improvement)
            else:
                failed.append(improvement)
        
        return successful, failed
    
    def _extract_quality_evolution(self, improvements: List[Dict]) -> List[float]:
        """Wydobywa ewolucję jakości"""
        quality_evolution = []
        
        for improvement in improvements:
            quality_after = improvement.get('quality_after', 0)
            quality_evolution.append(quality_after)
        
        return quality_evolution
    
    def _generate_lessons(self, improvements: List[Dict], final_quality: float, 
                         patterns: Dict[str, Any]) -> List[str]:
        """Generuje wnioski z procesu"""
        lessons = []
        
        # Quality-based lessons
        if final_quality > 0.8:
            lessons.append("High-quality outcome achieved - successful improvement strategy")
        elif final_quality < 0.5:
            lessons.append("Low final quality - improvement strategy needs refinement")
        
        # Pattern-based lessons
        complexity = patterns['structure']['complexity_score']
        if complexity > 7 and final_quality > 0.7:
            lessons.append("Complex processes can achieve high quality with proper approach")
        elif complexity < 3 and final_quality < 0.6:
            lessons.append("Simple processes should achieve higher quality - check basic fixes")
        
        # Improvement-based lessons
        if improvements:
            successful_count = len([i for i in improvements if i.get('quality_after', 0) > i.get('quality_before', 0)])
            success_rate = successful_count / len(improvements)
            
            if success_rate > 0.8:
                lessons.append("High fix success rate - effective improvement approach")
            elif success_rate < 0.4:
                lessons.append("Low fix success rate - consider different strategies")
        
        return lessons
    
    def _update_fix_patterns(self, successful_fixes: List[Dict], patterns: Dict[str, Any]) -> None:
        """Aktualizuje wzorce naprawek"""
        
        for fix in successful_fixes:
            fix_type = fix.get('fix_type', 'unknown')
            
            # Create or update fix pattern
            if fix_type not in self.fix_patterns:
                self.fix_patterns[fix_type] = FixPattern(
                    pattern_id=f"pattern_{fix_type}_{len(self.fix_patterns)}",
                    fix_type=fix_type,
                    success_rate=0.0,
                    applicable_conditions={},
                    fix_steps=[],
                    confidence=0.5,
                    usage_count=0
                )
            
            pattern = self.fix_patterns[fix_type]
            pattern.usage_count += 1
            
            # Update success rate
            total_attempts = pattern.usage_count
            current_successes = int(pattern.success_rate * (total_attempts - 1)) + 1
            pattern.success_rate = current_successes / total_attempts
            
            # Update confidence based on usage
            pattern.confidence = min(1.0, pattern.usage_count / 10.0)
    
    def _find_similar_processes(self, target_process: Dict, domain: Optional[str] = None) -> List[Tuple[ProcessKnowledge, float]]:
        """Znajduje podobne procesy"""
        target_patterns = self._extract_process_patterns(target_process)
        similarities = []
        
        for knowledge in self.knowledge_base:
            # Skip if different domain (unless no domain specified)
            if domain and knowledge.domain and knowledge.domain != domain:
                continue
            
            similarity = self._calculate_pattern_similarity(target_patterns, knowledge.patterns)
            if similarity > 0.3:  # Minimum similarity threshold
                similarities.append((knowledge, similarity))
        
        # Sort by similarity descending
        return sorted(similarities, key=lambda x: x[1], reverse=True)
    
    def _calculate_pattern_similarity(self, patterns1: Dict, patterns2: Dict) -> float:
        """Oblicza podobieństwo między wzorcami procesów"""
        similarities = []
        
        # Structure similarity
        struct1 = patterns1['structure']
        struct2 = patterns2['structure']
        
        element_diff = abs(struct1['elements_count'] - struct2['elements_count']) / max(struct1['elements_count'], struct2['elements_count'])
        complexity_diff = abs(struct1['complexity_score'] - struct2['complexity_score']) / max(struct1['complexity_score'], struct2['complexity_score'])
        
        structure_similarity = 1 - (element_diff + complexity_diff) / 2
        similarities.append(structure_similarity)
        
        # Connectivity similarity
        conn1 = patterns1['connectivity']
        conn2 = patterns2['connectivity']
        
        orphan_diff = abs(conn1['orphaned_elements'] - conn2['orphaned_elements']) / max(conn1['orphaned_elements'] + conn2['orphaned_elements'], 1)
        connectivity_similarity = 1 - orphan_diff
        similarities.append(connectivity_similarity)
        
        # Participants similarity
        part1 = patterns1['participants']
        part2 = patterns2['participants']
        
        cross_flow_diff = abs(part1['cross_participant_flows'] - part2['cross_participant_flows'])
        participants_similarity = 1 - (cross_flow_diff / max(part1['cross_participant_flows'] + part2['cross_participant_flows'], 1))
        similarities.append(participants_similarity)
        
        # Weighted average
        weights = [0.5, 0.3, 0.2]  # Structure most important
        return sum(s * w for s, w in zip(similarities, weights))
    
    def _extract_recommendations(self, similar_process: ProcessKnowledge, 
                               current_issues: List[Dict], similarity_score: float) -> List[Dict]:
        """Wydobywa rekomendacje z podobnego procesu"""
        recommendations = []
        
        # Get issue types from current issues
        current_issue_types = {issue.get('rule_code', '') for issue in current_issues}
        
        # Check successful fixes from similar process
        for fix in similar_process.successful_fixes:
            fix_addresses = fix.get('addresses_issues', [])
            
            # If this fix addresses current issues
            if any(issue_type in current_issue_types for issue_type in fix_addresses):
                recommendations.append({
                    'type': 'successful_fix_pattern',
                    'description': fix.get('description', ''),
                    'fix_type': fix.get('fix_type', ''),
                    'confidence': similarity_score * 0.8,  # Adjusted by similarity
                    'source_process': similar_process.process_id,
                    'addresses_issues': fix_addresses,
                    'expected_quality_improvement': fix.get('quality_improvement', 0.1)
                })
        
        # Add lessons learned as recommendations
        for lesson in similar_process.lessons_learned:
            recommendations.append({
                'type': 'lesson_learned',
                'description': f"From similar process: {lesson}",
                'confidence': similarity_score * 0.6,
                'source_process': similar_process.process_id,
                'category': 'strategic_advice'
            })
        
        return recommendations
    
    def _rank_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Rankinguje rekomendacje"""
        # Sort by confidence descending
        ranked = sorted(recommendations, key=lambda r: r.get('confidence', 0), reverse=True)
        
        # Deduplicate similar recommendations
        unique_recommendations = []
        seen_descriptions = set()
        
        for rec in ranked:
            desc_key = rec.get('description', '')[:50]  # First 50 chars as key
            if desc_key not in seen_descriptions:
                unique_recommendations.append(rec)
                seen_descriptions.add(desc_key)
        
        return unique_recommendations
    
    def _get_baseline_recommendations(self) -> List[Dict]:
        """Bazowe rekomendacje gdy brak historii"""
        return [
            {
                'type': 'baseline',
                'description': 'Start with structural fixes (missing start/end events)',
                'confidence': 0.7,
                'category': 'structural'
            },
            {
                'type': 'baseline',
                'description': 'Ensure proper gateway outgoing flows',
                'confidence': 0.6,
                'category': 'connectivity'
            },
            {
                'type': 'baseline',
                'description': 'Improve element naming for clarity',
                'confidence': 0.5,
                'category': 'semantic'
            }
        ]
    
    def _calculate_complexity_score(self, elements: List[Dict], flows: List[Dict], 
                                  participants: List[Dict]) -> float:
        """Oblicza score złożoności procesu"""
        base_score = len(elements) * 0.1
        flow_score = len(flows) * 0.05
        participant_score = len(participants) * 0.2
        
        # Gateway complexity bonus
        gateways = [e for e in elements if 'gateway' in e.get('type', '').lower()]
        gateway_score = len(gateways) * 0.3
        
        return min(10.0, base_score + flow_score + participant_score + gateway_score)
    
    def _count_orphaned_elements(self, elements: List[Dict], flows: List[Dict]) -> int:
        """Liczy elementy bez połączeń"""
        connected = set()
        for flow in flows:
            if flow.get('type') == 'sequence':
                connected.add(flow.get('source', ''))
                connected.add(flow.get('target', ''))
        
        all_elements = {e.get('id', '') for e in elements}
        return len(all_elements - connected)
    
    def _analyze_gateway_complexity(self, elements: List[Dict], flows: List[Dict]) -> Dict[str, Any]:
        """Analizuje złożoność bramek"""
        gateways = [e for e in elements if 'gateway' in e.get('type', '').lower()]
        
        gateway_analysis = {
            'total_gateways': len(gateways),
            'avg_outgoing_flows': 0,
            'max_outgoing_flows': 0
        }
        
        if gateways:
            outgoing_counts = []
            for gateway in gateways:
                gateway_id = gateway.get('id', '')
                outgoing = len([f for f in flows if f.get('source') == gateway_id])
                outgoing_counts.append(outgoing)
            
            gateway_analysis['avg_outgoing_flows'] = sum(outgoing_counts) / len(outgoing_counts)
            gateway_analysis['max_outgoing_flows'] = max(outgoing_counts) if outgoing_counts else 0
        
        return gateway_analysis
    
    def _count_cross_participant_flows(self, flows: List[Dict], elements: List[Dict]) -> int:
        """Liczy przepływy między uczestnikami"""
        element_participants = {e.get('id', ''): e.get('participant', '') for e in elements}
        
        cross_flows = 0
        for flow in flows:
            source_participant = element_participants.get(flow.get('source', ''), '')
            target_participant = element_participants.get(flow.get('target', ''), '')
            
            if source_participant and target_participant and source_participant != target_participant:
                cross_flows += 1
        
        return cross_flows
    
    def _analyze_participant_balance(self, participants: List[Dict], elements: List[Dict]) -> Dict[str, Any]:
        """Analizuje równowagę uczestników"""
        participant_elements = defaultdict(int)
        
        for element in elements:
            participant_id = element.get('participant', '')
            if participant_id:
                participant_elements[participant_id] += 1
        
        element_counts = list(participant_elements.values())
        
        return {
            'participants_with_elements': len(participant_elements),
            'avg_elements_per_participant': sum(element_counts) / max(1, len(element_counts)),
            'max_elements_in_participant': max(element_counts) if element_counts else 0,
            'min_elements_in_participant': min(element_counts) if element_counts else 0
        }
    
    def _update_statistics(self, improvements: List[Dict], final_quality: float) -> None:
        """Aktualizuje statystyki"""
        self.success_statistics['total_processes'] += 1
        
        if final_quality > 0.8:
            self.success_statistics['high_quality_processes'] += 1
        elif final_quality > 0.6:
            self.success_statistics['medium_quality_processes'] += 1
        else:
            self.success_statistics['low_quality_processes'] += 1
        
        # Update fix type statistics
        for improvement in improvements:
            fix_type = improvement.get('fix_type', 'unknown')
            self.success_statistics[f'fix_type_{fix_type}'] += 1
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Zwraca wglądy z procesu uczenia"""
        if not self.knowledge_base:
            return {'message': 'No learning data available yet'}
        
        # Calculate success rates by domain
        domain_stats = defaultdict(lambda: {'count': 0, 'avg_quality': 0.0})
        
        for knowledge in self.knowledge_base:
            domain = knowledge.domain or 'unknown'
            final_quality = knowledge.quality_evolution[-1] if knowledge.quality_evolution else 0
            
            domain_stats[domain]['count'] += 1
            domain_stats[domain]['avg_quality'] = (
                (domain_stats[domain]['avg_quality'] * (domain_stats[domain]['count'] - 1) + final_quality) /
                domain_stats[domain]['count']
            )
        
        # Most effective fix patterns
        effective_patterns = sorted(
            self.fix_patterns.values(),
            key=lambda p: p.success_rate * p.confidence,
            reverse=True
        )[:5]
        
        return {
            'total_processes_learned': len(self.knowledge_base),
            'domain_insights': dict(domain_stats),
            'most_effective_patterns': [
                {
                    'fix_type': p.fix_type,
                    'success_rate': p.success_rate,
                    'confidence': p.confidence,
                    'usage_count': p.usage_count
                }
                for p in effective_patterns
            ],
            'overall_statistics': dict(self.success_statistics),
            'learning_velocity': len(self.knowledge_base) / max(1, (datetime.now() - self.knowledge_base[0].created_at).days)
        }