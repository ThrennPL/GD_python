"""
BPMN v2.0 Compliance and Quality Assessment System

This module provides comprehensive BPMN 2.0 standard compliance validation,
iterative improvement capabilities, professional quality assessment tools,
and advanced AI-powered intelligence layer for optimization.
"""

from .bpmn_compliance_validator import (
    BPMNComplianceValidator,
    BPMNComplianceReport, 
    BPMNComplianceIssue,
    BPMNSeverity
)

from .bpmn_improvement_engine import BPMNImprovementEngine

from .mcp_server_simple import (
    SimpleMCPServer,
    EnhancedBPMNQualityChecker
)

# Intelligence Layer (optional)
try:
    from .intelligence_orchestrator import IntelligenceOrchestrator
    from .ml_issue_predictor import MLIssuePredictor
    from .template_quick_fixes import TemplateQuickFixes
    from .quality_degradation_detector import QualityDegradationDetector
    from .cross_process_learner import CrossProcessLearner
    from .adaptive_strategy_manager import AdaptiveStrategyManager
    INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Intelligence Layer not fully available: {e}")
    INTELLIGENCE_AVAILABLE = False

__version__ = "2.3.0"
__author__ = "BPMN Compliance Team + AI Intelligence"

__all__ = [
    'BPMNComplianceValidator',
    'BPMNComplianceReport',
    'BPMNComplianceIssue', 
    'BPMNSeverity',
    'BPMNImprovementEngine',
    'SimpleMCPServer',
    'EnhancedBPMNQualityChecker',
    'INTELLIGENCE_AVAILABLE'
]

if INTELLIGENCE_AVAILABLE:
    __all__.extend([
        'IntelligenceOrchestrator',
        'MLIssuePredictor',
        'TemplateQuickFixes',
        'QualityDegradationDetector',
        'CrossProcessLearner',
        'AdaptiveStrategyManager'
    ])