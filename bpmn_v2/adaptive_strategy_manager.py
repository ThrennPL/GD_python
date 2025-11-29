"""
Adaptive Strategy Manager
Dynamicznie dobiera strategie naprawy na podstawie kontekstu procesu

Autor: AI Assistant
Data: 2025-11-29
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import defaultdict

class StrategyType(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    QUALITY_FOCUSED = "quality_focused"
    SPEED_FOCUSED = "speed_focused"

@dataclass
class StrategyConfig:
    """Konfiguracja strategii naprawy"""
    strategy_type: StrategyType
    ai_calls_limit: int
    quality_threshold: float
    max_iterations: int
    risk_tolerance: float
    focus_areas: List[str]
    template_usage: bool
    learning_enabled: bool

@dataclass
class ContextFactors:
    """Czynniki kontekstowe procesu"""
    complexity_score: float
    elements_count: int
    participants_count: int
    critical_issues_count: int
    domain: Optional[str]
    time_constraint: Optional[str]  # 'urgent', 'normal', 'flexible'
    quality_requirement: Optional[str]  # 'minimum', 'standard', 'high'

class AdaptiveStrategyManager:
    """Manager strategii adaptujący się do kontekstu procesu"""
    
    def __init__(self):
        self.strategy_performance = defaultdict(lambda: {'success_count': 0, 'total_count': 0, 'avg_quality': 0.0})
        self.context_strategy_mapping = {}
        self.domain_preferences = defaultdict(lambda: StrategyType.BALANCED)
        
        # Initialize default strategies
        self.strategy_templates = self._initialize_strategy_templates()
    
    def _initialize_strategy_templates(self) -> Dict[StrategyType, StrategyConfig]:
        """Inicjalizuje szablony strategii"""
        return {
            StrategyType.CONSERVATIVE: StrategyConfig(
                strategy_type=StrategyType.CONSERVATIVE,
                ai_calls_limit=50,
                quality_threshold=0.6,
                max_iterations=5,
                risk_tolerance=0.3,
                focus_areas=['structure', 'compliance'],
                template_usage=True,
                learning_enabled=True
            ),
            StrategyType.BALANCED: StrategyConfig(
                strategy_type=StrategyType.BALANCED,
                ai_calls_limit=100,
                quality_threshold=0.7,
                max_iterations=8,
                risk_tolerance=0.5,
                focus_areas=['structure', 'flows', 'naming'],
                template_usage=True,
                learning_enabled=True
            ),
            StrategyType.AGGRESSIVE: StrategyConfig(
                strategy_type=StrategyType.AGGRESSIVE,
                ai_calls_limit=150,
                quality_threshold=0.85,
                max_iterations=12,
                risk_tolerance=0.8,
                focus_areas=['structure', 'flows', 'gateways', 'naming', 'semantics'],
                template_usage=False,
                learning_enabled=True
            ),
            StrategyType.QUALITY_FOCUSED: StrategyConfig(
                strategy_type=StrategyType.QUALITY_FOCUSED,
                ai_calls_limit=120,
                quality_threshold=0.9,
                max_iterations=10,
                risk_tolerance=0.4,
                focus_areas=['compliance', 'semantics', 'naming'],
                template_usage=True,
                learning_enabled=True
            ),
            StrategyType.SPEED_FOCUSED: StrategyConfig(
                strategy_type=StrategyType.SPEED_FOCUSED,
                ai_calls_limit=30,
                quality_threshold=0.5,
                max_iterations=3,
                risk_tolerance=0.7,
                focus_areas=['structure'],
                template_usage=True,
                learning_enabled=False
            )
        }
    
    def select_strategy(self, bpmn_json: Dict, issues: List[Dict], 
                       context_hints: Optional[Dict] = None) -> StrategyConfig:
        """Wybiera optymalną strategię na podstawie kontekstu"""
        
        # Analyze process context
        context = self._analyze_context(bpmn_json, issues, context_hints)
        
        # Get strategy recommendation
        recommended_strategy = self._recommend_strategy(context)
        
        # Customize strategy based on context
        customized_config = self._customize_strategy(recommended_strategy, context)
        
        # Learn from strategy selection
        self._record_strategy_selection(context, recommended_strategy)
        
        return customized_config
    
    def _analyze_context(self, bpmn_json: Dict, issues: List[Dict], 
                        context_hints: Optional[Dict] = None) -> ContextFactors:
        """Analizuje kontekst procesu"""
        
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        flows = bpmn_json.get('flows', [])
        
        # Calculate complexity
        complexity = self._calculate_complexity_score(elements, flows, participants)
        
        # Count critical issues
        critical_issues = len([i for i in issues if i.get('severity') == 'critical'])
        
        # Extract context hints
        domain = context_hints.get('domain') if context_hints else None
        time_constraint = context_hints.get('time_constraint', 'normal') if context_hints else 'normal'
        quality_requirement = context_hints.get('quality_requirement', 'standard') if context_hints else 'standard'
        
        return ContextFactors(
            complexity_score=complexity,
            elements_count=len(elements),
            participants_count=len(participants),
            critical_issues_count=critical_issues,
            domain=domain,
            time_constraint=time_constraint,
            quality_requirement=quality_requirement
        )
    
    def _recommend_strategy(self, context: ContextFactors) -> StrategyType:
        """Rekomenduje strategię na podstawie kontekstu"""
        
        # Time constraint considerations
        if context.time_constraint == 'urgent':
            return StrategyType.SPEED_FOCUSED
        
        # Quality requirement considerations
        if context.quality_requirement == 'high':
            return StrategyType.QUALITY_FOCUSED
        elif context.quality_requirement == 'minimum':
            return StrategyType.SPEED_FOCUSED
        
        # Complexity considerations
        if context.complexity_score > 8:
            if context.critical_issues_count > 5:
                return StrategyType.AGGRESSIVE
            else:
                return StrategyType.BALANCED
        elif context.complexity_score < 3:
            return StrategyType.CONSERVATIVE
        
        # Critical issues considerations
        if context.critical_issues_count > 10:
            return StrategyType.AGGRESSIVE
        elif context.critical_issues_count < 3:
            return StrategyType.CONSERVATIVE
        
        # Domain-based recommendations
        if context.domain:
            domain_preference = self.domain_preferences.get(context.domain, StrategyType.BALANCED)
            return domain_preference
        
        # Default to balanced
        return StrategyType.BALANCED
    
    def _customize_strategy(self, strategy_type: StrategyType, context: ContextFactors) -> StrategyConfig:
        """Dostosowuje strategię do kontekstu"""
        
        # Get base strategy
        base_strategy = self.strategy_templates[strategy_type]
        
        # Create customized copy
        customized = StrategyConfig(
            strategy_type=base_strategy.strategy_type,
            ai_calls_limit=base_strategy.ai_calls_limit,
            quality_threshold=base_strategy.quality_threshold,
            max_iterations=base_strategy.max_iterations,
            risk_tolerance=base_strategy.risk_tolerance,
            focus_areas=base_strategy.focus_areas.copy(),
            template_usage=base_strategy.template_usage,
            learning_enabled=base_strategy.learning_enabled
        )
        
        # Adjust based on complexity
        if context.complexity_score > 8:
            customized.ai_calls_limit = int(customized.ai_calls_limit * 1.3)
            customized.max_iterations += 2
        elif context.complexity_score < 3:
            customized.ai_calls_limit = int(customized.ai_calls_limit * 0.7)
            customized.max_iterations = max(3, customized.max_iterations - 2)
        
        # Adjust based on critical issues
        if context.critical_issues_count > 10:
            customized.quality_threshold = max(0.8, customized.quality_threshold)
            if 'structure' not in customized.focus_areas:
                customized.focus_areas.insert(0, 'structure')
        
        # Adjust based on size
        if context.elements_count > 50:
            customized.ai_calls_limit = int(customized.ai_calls_limit * 1.2)
        elif context.elements_count < 10:
            customized.ai_calls_limit = int(customized.ai_calls_limit * 0.8)
        
        # Adjust based on participants
        if context.participants_count > 5:
            if 'flows' not in customized.focus_areas:
                customized.focus_areas.append('flows')
            customized.risk_tolerance = min(0.8, customized.risk_tolerance + 0.1)
        
        return customized
    
    def _calculate_complexity_score(self, elements: List[Dict], flows: List[Dict], 
                                  participants: List[Dict]) -> float:
        """Oblicza score złożoności procesu"""
        base_score = len(elements) * 0.1
        flow_score = len(flows) * 0.05
        participant_score = len(participants) * 0.2
        
        # Gateway complexity
        gateways = [e for e in elements if 'gateway' in e.get('type', '').lower()]
        gateway_score = len(gateways) * 0.3
        
        # Branching complexity
        branching_score = 0
        for gateway in gateways:
            gateway_id = gateway.get('id', '')
            outgoing_flows = len([f for f in flows if f.get('source') == gateway_id])
            branching_score += (outgoing_flows - 1) * 0.2  # Each branch adds complexity
        
        total_score = base_score + flow_score + participant_score + gateway_score + branching_score
        return min(10.0, total_score)
    
    def adapt_strategy_during_execution(self, current_strategy: StrategyConfig, 
                                      iteration_results: List[Dict], 
                                      current_quality: float) -> Optional[StrategyConfig]:
        """Adaptuje strategię podczas wykonywania"""
        
        if len(iteration_results) < 3:
            return None  # Need more data
        
        # Analyze recent performance
        recent_results = iteration_results[-3:]
        quality_trend = self._analyze_quality_trend(recent_results)
        progress_rate = self._calculate_progress_rate(recent_results)
        
        # Determine if strategy change is needed
        should_adapt = False
        adaptation_reason = ""
        
        # Check for stagnation
        if progress_rate < 0.01 and len(iteration_results) > 5:
            should_adapt = True
            adaptation_reason = "quality_stagnation"
        
        # Check for quality degradation
        elif quality_trend < -0.05:
            should_adapt = True
            adaptation_reason = "quality_degradation"
        
        # Check for resource exhaustion without results
        elif current_quality < 0.5 and len(iteration_results) >= current_strategy.max_iterations * 0.7:
            should_adapt = True
            adaptation_reason = "resource_inefficiency"
        
        if not should_adapt:
            return None
        
        # Select new strategy based on adaptation reason
        new_strategy = self._select_adaptation_strategy(
            current_strategy, adaptation_reason, current_quality
        )
        
        return new_strategy
    
    def _analyze_quality_trend(self, results: List[Dict]) -> float:
        """Analizuje trend jakości"""
        if len(results) < 2:
            return 0.0
        
        qualities = [r.get('quality_after', 0.0) for r in results]
        
        # Simple linear trend
        x = list(range(len(qualities)))
        slope = np.polyfit(x, qualities, 1)[0] if len(qualities) > 1 else 0
        
        return slope
    
    def _calculate_progress_rate(self, results: List[Dict]) -> float:
        """Oblicza tempo postępu"""
        if len(results) < 2:
            return 0.0
        
        first_quality = results[0].get('quality_after', 0.0)
        last_quality = results[-1].get('quality_after', 0.0)
        
        return (last_quality - first_quality) / len(results)
    
    def _select_adaptation_strategy(self, current_strategy: StrategyConfig, 
                                  reason: str, current_quality: float) -> StrategyConfig:
        """Wybiera strategię adaptacyjną"""
        
        if reason == "quality_stagnation":
            # Try more aggressive approach
            if current_strategy.strategy_type in [StrategyType.CONSERVATIVE, StrategyType.BALANCED]:
                return self._customize_strategy_for_adaptation(
                    StrategyType.AGGRESSIVE, current_strategy
                )
            else:
                # Already aggressive, try quality-focused
                return self._customize_strategy_for_adaptation(
                    StrategyType.QUALITY_FOCUSED, current_strategy
                )
        
        elif reason == "quality_degradation":
            # Be more conservative
            return self._customize_strategy_for_adaptation(
                StrategyType.CONSERVATIVE, current_strategy
            )
        
        elif reason == "resource_inefficiency":
            if current_quality < 0.3:
                # Switch to speed-focused for basic fixes
                return self._customize_strategy_for_adaptation(
                    StrategyType.SPEED_FOCUSED, current_strategy
                )
            else:
                # Try balanced approach
                return self._customize_strategy_for_adaptation(
                    StrategyType.BALANCED, current_strategy
                )
        
        # Fallback to balanced
        return self._customize_strategy_for_adaptation(StrategyType.BALANCED, current_strategy)
    
    def _customize_strategy_for_adaptation(self, new_strategy_type: StrategyType, 
                                         current_strategy: StrategyConfig) -> StrategyConfig:
        """Dostosowuje nową strategię zachowując kontekst poprzedniej"""
        
        new_strategy = self.strategy_templates[new_strategy_type]
        
        # Preserve some context from current strategy
        adapted_strategy = StrategyConfig(
            strategy_type=new_strategy.strategy_type,
            ai_calls_limit=min(new_strategy.ai_calls_limit, current_strategy.ai_calls_limit + 20),
            quality_threshold=new_strategy.quality_threshold,
            max_iterations=max(3, min(new_strategy.max_iterations, current_strategy.max_iterations + 2)),
            risk_tolerance=new_strategy.risk_tolerance,
            focus_areas=new_strategy.focus_areas.copy(),
            template_usage=new_strategy.template_usage,
            learning_enabled=new_strategy.learning_enabled
        )
        
        return adapted_strategy
    
    def record_strategy_performance(self, strategy: StrategyConfig, final_quality: float, 
                                  iterations_used: int, success: bool) -> None:
        """Rejestruje wydajność strategii"""
        
        strategy_key = strategy.strategy_type.value
        
        # Update performance stats
        perf = self.strategy_performance[strategy_key]
        perf['total_count'] += 1
        
        if success:
            perf['success_count'] += 1
        
        # Update average quality
        current_avg = perf['avg_quality']
        total_count = perf['total_count']
        perf['avg_quality'] = ((current_avg * (total_count - 1)) + final_quality) / total_count
        
        # Store additional metrics
        if f'{strategy_key}_iterations' not in perf:
            perf[f'{strategy_key}_iterations'] = []
        perf[f'{strategy_key}_iterations'].append(iterations_used)
    
    def _record_strategy_selection(self, context: ContextFactors, strategy: StrategyType) -> None:
        """Rejestruje wybór strategii dla kontekstu"""
        
        # Create context signature
        context_signature = f"complexity_{int(context.complexity_score)}_elements_{context.elements_count//10*10}_critical_{context.critical_issues_count}"
        
        # Record mapping
        if context_signature not in self.context_strategy_mapping:
            self.context_strategy_mapping[context_signature] = defaultdict(int)
        
        self.context_strategy_mapping[context_signature][strategy.value] += 1
        
        # Update domain preferences
        if context.domain:
            # Simple learning: if strategy performs well, prefer it for domain
            domain_stats = self.strategy_performance.get(strategy.value, {})
            success_rate = domain_stats.get('success_count', 0) / max(1, domain_stats.get('total_count', 1))
            
            if success_rate > 0.7:  # Good performance threshold
                self.domain_preferences[context.domain] = strategy
    
    def get_strategy_insights(self) -> Dict[str, Any]:
        """Zwraca wglądy na temat strategii"""
        
        insights = {
            'strategy_performance': {},
            'best_strategies_by_context': {},
            'domain_preferences': dict(self.domain_preferences),
            'recommendations': []
        }
        
        # Calculate strategy performance metrics
        for strategy_name, perf in self.strategy_performance.items():
            total = perf['total_count']
            success = perf['success_count']
            
            success_rate = success / max(1, total)
            avg_quality = perf['avg_quality']
            
            insights['strategy_performance'][strategy_name] = {
                'success_rate': success_rate,
                'average_quality': avg_quality,
                'usage_count': total,
                'performance_score': success_rate * avg_quality  # Combined metric
            }
        
        # Find best strategies by context
        for context_sig, strategy_counts in self.context_strategy_mapping.items():
            most_used_strategy = max(strategy_counts.items(), key=lambda x: x[1])[0]
            insights['best_strategies_by_context'][context_sig] = most_used_strategy
        
        # Generate recommendations
        if insights['strategy_performance']:
            best_strategy = max(
                insights['strategy_performance'].items(),
                key=lambda x: x[1]['performance_score']
            )[0]
            
            insights['recommendations'].append(
                f"Best overall strategy: {best_strategy}"
            )
        
        return insights
    
    def get_strategy_for_context_signature(self, context_signature: str) -> Optional[StrategyType]:
        """Zwraca preferowaną strategię dla sygnatury kontekstu"""
        
        if context_signature in self.context_strategy_mapping:
            strategy_counts = self.context_strategy_mapping[context_signature]
            most_used = max(strategy_counts.items(), key=lambda x: x[1])[0]
            return StrategyType(most_used)
        
        return None