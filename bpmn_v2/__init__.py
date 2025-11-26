"""
BPMN v2.0 Compliance and Quality Assessment System

This module provides comprehensive BPMN 2.0 standard compliance validation,
iterative improvement capabilities, and professional quality assessment tools.
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

__version__ = "2.0.0"
__author__ = "BPMN Compliance Team"

__all__ = [
    'BPMNComplianceValidator',
    'BPMNComplianceReport',
    'BPMNComplianceIssue', 
    'BPMNSeverity',
    'BPMNImprovementEngine',
    'SimpleMCPServer',
    'EnhancedBPMNQualityChecker'
]