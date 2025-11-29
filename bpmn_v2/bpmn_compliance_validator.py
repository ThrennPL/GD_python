"""
BPMN Compliance Validator
Zaawansowany system oceny zgodności ze standardem BPMN 2.0

Autor: AI Assistant
Data: 2025-11-26
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Tuple, Set
from enum import Enum
import json
import xml.etree.ElementTree as ET

class BPMNSeverity(Enum):
    """Poziomy ważności błędów BPMN"""
    CRITICAL = "critical"      # Błędy naruszające standard BPMN
    MAJOR = "major"           # Poważne problemy wpływające na czytelność
    MINOR = "minor"           # Drobne problemy stylistyczne
    WARNING = "warning"       # Ostrzeżenia o potencjalnych problemach

@dataclass
class BPMNComplianceIssue:
    """Pojedynczy problem ze zgodnością BPMN"""
    element_id: str
    element_type: str
    severity: BPMNSeverity
    rule_code: str
    message: str
    suggestion: str
    auto_fixable: bool = False

@dataclass
class BPMNComplianceReport:
    """Raport zgodności ze standardem BPMN"""
    overall_score: float  # 0-100
    compliance_level: str  # "EXCELLENT", "GOOD", "FAIR", "POOR", "INVALID"
    issues: List[BPMNComplianceIssue]
    statistics: Dict[str, Any]
    improvement_priorities: List[str]

class BPMNComplianceValidator:
    """
    Walidator zgodności ze standardem BPMN 2.0
    
    Implementuje reguły zgodności:
    - Strukturalne (węzły, krawędzie, pools)
    - Semantyczne (nazewnictwo, przepływy)
    - Składniowe (typy elementów, atrybuty)
    - Stylistyczne (layout, czytelność)
    """
    
    def __init__(self):
        self.rules = self._initialize_bpmn_rules()
        
    def _initialize_bpmn_rules(self) -> Dict[str, Dict]:
        """Inicjalizuje reguły zgodności BPMN 2.0"""
        return {
            # === REGUŁY STRUKTURALNE ===
            "STRUCT_001": {
                "name": "Start Event Required",
                "severity": BPMNSeverity.CRITICAL,
                "description": "Każdy proces musi mieć co najmniej jeden Start Event",
                "check": self._check_start_events
            },
            "STRUCT_002": {
                "name": "End Event Required", 
                "severity": BPMNSeverity.CRITICAL,
                "description": "Każdy proces musi mieć co najmniej jeden End Event",
                "check": self._check_end_events
            },
            "STRUCT_003": {
                "name": "Element Connectivity",
                "severity": BPMNSeverity.CRITICAL,
                "description": "Wszystkie elementy muszą być połączone przepływami",
                "check": self._check_element_connectivity
            },
            "STRUCT_004": {
                "name": "Gateway Flows",
                "severity": BPMNSeverity.CRITICAL,
                "description": "Gateway musi mieć prawidłowe przepływy wejściowe i wyjściowe",
                "check": self._check_gateway_flows
            },
            "STRUCT_005": {
                "name": "Pool Lane Structure",
                "severity": BPMNSeverity.MAJOR,
                "description": "Pools i Lanes muszą być prawidłowo zdefiniowane",
                "check": self._check_pool_structure
            },
            "STRUCT_006": {
                "name": "Pool Process Continuity",
                "severity": BPMNSeverity.CRITICAL,
                "description": "Każdy Pool musi mieć ciągły proces z Sequence Flow",
                "check": self._check_pool_continuity
            },
            "STRUCT_007": {
                "name": "Pool Autonomy",
                "severity": BPMNSeverity.CRITICAL,
                "description": "Każdy Pool musi mieć własne Start i End Events",
                "check": self._check_pool_autonomy
            },
            "STRUCT_008": {
                "name": "Message Flow Validation",
                "severity": BPMNSeverity.MAJOR,
                "description": "Message Flow może łączyć tylko różne Pools",
                "check": self._check_message_flows
            },
            "STRUCT_009": {
                "name": "Message Flow End Event Validation",
                "severity": BPMNSeverity.MAJOR,
                "description": "End Event z wyjściowym Message Flow musi być typu Message",
                "check": self._check_message_flow_end_events
            },
            "STRUCT_010": {
                "name": "Message Flow Intermediate Event Validation",
                "severity": BPMNSeverity.MAJOR,
                "description": "Intermediate Event z Message Flow musi być typu Message",
                "check": self._check_message_flow_intermediate_events
            },
            "STRUCT_011": {
                "name": "Message Flow Target Validation",
                "severity": BPMNSeverity.MAJOR,
                "description": "Message Flow może prowadzić tylko do Activity lub Intermediate/End Event",
                "check": self._check_message_flow_targets
            },
            
            # === REGUŁY SEMANTYCZNE ===
            "SEM_001": {
                "name": "Element Naming",
                "severity": BPMNSeverity.MAJOR,
                "description": "Wszystkie elementy muszą mieć znaczące nazwy",
                "check": self._check_element_naming
            },
            "SEM_002": {
                "name": "Gateway Conditions",
                "severity": BPMNSeverity.MAJOR,
                "description": "Exclusive Gateway musi mieć zdefiniowane warunki",
                "check": self._check_gateway_conditions
            },
            "SEM_003": {
                "name": "Message Flow Validation",
                "severity": BPMNSeverity.MAJOR,
                "description": "Message Flows muszą łączyć różnych uczestników",
                "check": self._check_message_flows
            },
            "SEM_004": {
                "name": "Activity Types",
                "severity": BPMNSeverity.MINOR,
                "description": "Aktywności muszą mieć odpowiedni typ (User/Service/Manual Task)",
                "check": self._check_activity_types
            },
            
            # === REGUŁY SKŁADNIOWE ===
            "SYNT_001": {
                "name": "Element IDs",
                "severity": BPMNSeverity.CRITICAL,
                "description": "Wszystkie elementy muszą mieć unikalne ID",
                "check": self._check_unique_ids
            },
            "SYNT_002": {
                "name": "Required Attributes",
                "severity": BPMNSeverity.CRITICAL,
                "description": "Elementy muszą mieć wymagane atrybuty",
                "check": self._check_required_attributes
            },
            "SYNT_003": {
                "name": "Flow References",
                "severity": BPMNSeverity.CRITICAL,
                "description": "Przepływy muszą odwoływać się do istniejących elementów",
                "check": self._check_flow_references
            },
            
            # === REGUŁY STYLISTYCZNE ===
            "STYLE_001": {
                "name": "Naming Conventions",
                "severity": BPMNSeverity.MINOR,
                "description": "Nazwy powinny następować konwencje (CamelCase dla ID, opis dla nazw)",
                "check": self._check_naming_conventions
            },
            "STYLE_002": {
                "name": "Process Complexity",
                "severity": BPMNSeverity.WARNING,
                "description": "Proces nie powinien być zbyt skomplikowany (max 20 elementów)",
                "check": self._check_process_complexity
            },
            "STYLE_003": {
                "name": "Participant Distribution",
                "severity": BPMNSeverity.WARNING,
                "description": "Elementy powinny być równomiernie rozłożone między uczestników",
                "check": self._check_participant_distribution
            }
        }
    
    def validate_bpmn_compliance(self, bpmn_json: Dict) -> BPMNComplianceReport:
        """
        Główna metoda walidacji zgodności BPMN
        
        Args:
            bpmn_json: Proces BPMN w formacie JSON
            
        Returns:
            Kompletny raport zgodności
        """
        issues = []
        
        # Wykonaj wszystkie sprawdzenia
        for rule_code, rule_config in self.rules.items():
            try:
                rule_issues = rule_config["check"](bpmn_json, rule_code, rule_config)
                issues.extend(rule_issues)
            except Exception as e:
                # Dodaj błąd reguły jako issue
                issues.append(BPMNComplianceIssue(
                    element_id="validator",
                    element_type="system",
                    severity=BPMNSeverity.WARNING,
                    rule_code=rule_code,
                    message=f"Błąd wykonania reguły: {e}",
                    suggestion="Sprawdź poprawność struktury procesu",
                    auto_fixable=False
                ))
        
        # Oblicz wynik ogólny
        overall_score = self._calculate_compliance_score(issues)
        compliance_level = self._determine_compliance_level(overall_score)
        statistics = self._generate_statistics(issues, bpmn_json)
        priorities = self._determine_improvement_priorities(issues)
        
        # DEBUG: Pokazuj szczegóły issues
        critical_count = len([i for i in issues if i.severity == BPMNSeverity.CRITICAL])
        major_count = len([i for i in issues if i.severity == BPMNSeverity.MAJOR])
        print(f"🏭 BPMN Compliance Debug:")
        print(f"   Total issues: {len(issues)} (Critical: {critical_count}, Major: {major_count})")
        print(f"   Score: {overall_score}")
        if critical_count > 0:
            print(f"   Critical issues:")
            for issue in [i for i in issues if i.severity == BPMNSeverity.CRITICAL][:3]:
                print(f"      - {issue.rule_code}: {issue.message}")
        
        return BPMNComplianceReport(
            overall_score=overall_score,
            compliance_level=compliance_level,
            issues=issues,
            statistics=statistics,
            improvement_priorities=priorities
        )
    
    # === IMPLEMENTACJA REGUŁ STRUKTURALNYCH ===
    
    def _check_start_events(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza obecność Start Events - per Pool w procesach wielopoolowych"""
        issues = []
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        flows = bpmn_json.get('flows', [])
        
        # Jeśli nie ma Pool lub jest jeden Pool - sprawdź globalnie
        if len(participants) <= 1:
            start_events = [e for e in elements if e.get('type') == 'startEvent']
            
            # Sprawdź czy są Intermediate Catch Events które mogą zastąpić Start Event
            intermediate_catch_events = [e for e in elements if e.get('type') in ['intermediateCatchEvent', 'intermediateMessageCatchEvent']]
            
            # Sprawdź czy są Message Flow z zewnątrz
            external_message_flows = [f for f in flows 
                                    if f.get('type') == 'message' and 
                                    f.get('source') == 'external' and
                                    f.get('target') in [e.get('id') for e in elements]]
            
            # Proces może rozpoczynać się przez Start Event, Intermediate Catch Event, lub Message Flow z zewnątrz
            if not start_events and not intermediate_catch_events and not external_message_flows:
                issues.append(BPMNComplianceIssue(
                    element_id="process",
                    element_type="process",
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="Proces nie ma Start Event",
                    suggestion="Dodaj Start Event na początku procesu",
                    auto_fixable=True
                ))
            elif len(start_events) > 1:
                for se in start_events[1:]:  # Wszystkie oprócz pierwszego
                    issues.append(BPMNComplianceIssue(
                        element_id=se.get('id', 'unknown'),
                        element_type="startEvent",
                        severity=BPMNSeverity.WARNING,
                        rule_code=rule_code,
                        message="Proces ma wiele Start Events - może to utrudniać czytelność",
                        suggestion="Rozważ użycie jednego Start Event z odpowiednimi przepływami",
                        auto_fixable=False
                    ))
        else:
            # Procesy wielopoolowe - sprawdź każdy Pool z aktywnościami
            for participant in participants:
                participant_id = participant.get('id')
                participant_name = participant.get('name', participant_id)
                participant_elements = [e for e in elements if e.get('participant') == participant_id]
                
                # Sprawdź tylko Pool które mają aktywności (nie tylko eventy)
                activities = [e for e in participant_elements if e.get('type') in 
                             ['userTask', 'serviceTask', 'manualTask', 'scriptTask', 'receiveTask', 'sendTask']]
                
                if activities:  # Pool ma aktywności - musi mieć sposób rozpoczęcia
                    pool_start_events = [e for e in participant_elements if e.get('type') == 'startEvent']
                    
                    # Sprawdź czy Pool ma Intermediate Catch Events (mogą zastąpić Start Event w Pool)
                    pool_intermediate_catch = [e for e in participant_elements if e.get('type') in ['intermediateCatchEvent', 'intermediateMessageCatchEvent']]
                    
                    # Sprawdź czy Pool ma Message Flow wchodzący (alternatywa dla Start Event)
                    # Uwzględnij Message Flow z zewnątrz (external) lub z innych Pool
                    incoming_messages = []
                    for f in flows:
                        if f.get('type') == 'message':
                            # Message Flow wchodzący do tego Pool
                            target_id = f.get('target')
                            if target_id in [e.get('id') for e in participant_elements]:
                                incoming_messages.append(f)
                            # Lub Message Flow z zewnętrznego źródła
                            elif f.get('source') == 'external' and target_id in [e.get('id') for e in participant_elements]:
                                incoming_messages.append(f)
                    
                    # Pool może rozpocząć się przez: Start Event, Intermediate Catch Event, lub Message Flow
                    if not pool_start_events and not pool_intermediate_catch and not incoming_messages:
                        issues.append(BPMNComplianceIssue(
                            element_id=participant_id,
                            element_type="pool",
                            severity=rule_config["severity"],
                            rule_code=rule_code,
                            message=f"Pool '{participant_name}' ma aktywności ale nie ma Start Event, Intermediate Catch Event ani Message Flow wchodzącego",
                            suggestion="Dodaj Start Event, Intermediate Catch Event lub Message Flow wchodzący do tego Pool",
                            auto_fixable=True
                        ))
        
        return issues
    
    def _check_end_events(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza obecność End Events - per Pool w procesach wielopoolowych"""
        issues = []
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        flows = bpmn_json.get('flows', [])
        
        # Jeśli nie ma Pool lub jest jeden Pool - sprawdź globalnie
        if len(participants) <= 1:
            end_events = [e for e in elements if e.get('type') == 'endEvent']
            
            # Sprawdź czy są Intermediate Throw Events które mogą zastąpić End Event
            intermediate_throw_events = [e for e in elements if e.get('type') in ['intermediateThrowEvent', 'intermediateMessageThrowEvent']]
            
            # Sprawdź czy są Message Flow na zewnątrz
            external_outgoing_flows = [f for f in flows 
                                     if f.get('type') == 'message' and 
                                     f.get('target') == 'external' and
                                     f.get('source') in [e.get('id') for e in elements]]
            
            # Proces może kończyć się przez End Event, Intermediate Throw Event, lub Message Flow na zewnątrz
            if not end_events and not intermediate_throw_events and not external_outgoing_flows:
                issues.append(BPMNComplianceIssue(
                    element_id="process",
                    element_type="process",
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="Proces nie ma End Event",
                    suggestion="Dodaj End Event na końcu procesu",
                    auto_fixable=True
                ))
        else:
            # Procesy wielopoolowe - sprawdź każdy Pool z aktywnościami
            for participant in participants:
                participant_id = participant.get('id')
                participant_name = participant.get('name', participant_id)
                participant_elements = [e for e in elements if e.get('participant') == participant_id]
                
                # Sprawdź tylko Pool które mają aktywności (nie tylko eventy)
                activities = [e for e in participant_elements if e.get('type') in 
                             ['userTask', 'serviceTask', 'manualTask', 'scriptTask', 'receiveTask', 'sendTask']]
                
                if activities:  # Pool ma aktywności - musi mieć sposób zakończenia
                    pool_end_events = [e for e in participant_elements if e.get('type') == 'endEvent']
                    
                    # Sprawdź czy Pool ma Intermediate Throw Events (mogą zastąpić End Event w Pool)
                    pool_intermediate_throw = [e for e in participant_elements if e.get('type') in ['intermediateThrowEvent', 'intermediateMessageThrowEvent']]
                    
                    # Sprawdź czy Pool ma Message Flow wychodzący (alternatywa dla End Event)
                    # Uwzględnij Message Flow do zewnątrz (external) lub do innych Pool  
                    outgoing_messages = []
                    for f in flows:
                        if f.get('type') == 'message':
                            # Message Flow wychodzący z tego Pool
                            source_id = f.get('source')
                            if source_id in [e.get('id') for e in participant_elements]:
                                outgoing_messages.append(f)
                            # Lub Message Flow do zewnętrznego celu
                            elif f.get('target') == 'external' and source_id in [e.get('id') for e in participant_elements]:
                                outgoing_messages.append(f)
                    
                    # Pool może kończyć się przez: End Event, Intermediate Throw Event, lub Message Flow
                    if not pool_end_events and not pool_intermediate_throw and not outgoing_messages:
                        issues.append(BPMNComplianceIssue(
                            element_id=participant_id,
                            element_type="pool",
                            severity=rule_config["severity"],
                            rule_code=rule_code,
                            message=f"Pool '{participant_name}' ma aktywności ale nie ma End Event, Intermediate Throw Event ani Message Flow wychodzącego",
                            suggestion="Dodaj End Event, Intermediate Throw Event lub Message Flow wychodzący z tego Pool",
                            auto_fixable=True
                        ))
        
        return issues
    
    def _check_element_connectivity(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza połączenia między elementami"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Zbierz ID wszystkich elementów
        element_ids = {e.get('id') for e in elements if e.get('id')}
        
        # Sprawdź każdy element czy ma odpowiednie połączenia
        for element in elements:
            element_id = element.get('id')
            element_type = element.get('type')
            
            if not element_id:
                continue
                
            # Znajdź przepływy wchodzące i wychodzące
            incoming = [f for f in flows if f.get('target') == element_id]
            outgoing = [f for f in flows if f.get('source') == element_id]
            
            # Rozdziel przepływy na Sequence Flow i Message Flow
            sequence_incoming = [f for f in incoming if f.get('type', 'sequence') == 'sequence']
            sequence_outgoing = [f for f in outgoing if f.get('type', 'sequence') == 'sequence']
            message_incoming = [f for f in incoming if f.get('type') == 'message']
            message_outgoing = [f for f in outgoing if f.get('type') == 'message']
            
            # Sprawdź reguły dla różnych typów elementów
            if element_type == 'startEvent':
                # Start Event nie może mieć Sequence Flow wchodzących, ale może mieć Message Flow
                if sequence_incoming:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message="Start Event nie może mieć Sequence Flow wchodzących",
                        suggestion="Usuń Sequence Flow wchodzące do Start Event (Message Flow są dozwolone)",
                        auto_fixable=True
                    ))
                # Start Event musi mieć Sequence Flow LUB Message Flow wychodzący
                if not sequence_outgoing and not message_outgoing:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message="Start Event musi mieć przepływ wychodzący (Sequence Flow lub Message Flow)",
                        suggestion="Połącz Start Event z następną aktywnością",
                        auto_fixable=False
                    ))
                    
            elif element_type == 'endEvent':
                # End Event musi mieć Sequence Flow LUB Message Flow wchodzący
                if not sequence_incoming and not message_incoming:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message="End Event musi mieć przepływ wchodzący (Sequence Flow lub Message Flow)",
                        suggestion="Połącz poprzednią aktywność z End Event",
                        auto_fixable=False
                    ))
                # End Event nie może mieć Sequence Flow wychodzących, ale może mieć Message Flow
                if sequence_outgoing:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message="End Event nie może mieć Sequence Flow wychodzących",
                        suggestion="Usuń Sequence Flow z End Event (Message Flow do innych Pool są dozwolone)",
                        auto_fixable=True
                    ))
                    
            elif element_type in ['intermediateCatchEvent', 'intermediateMessageCatchEvent']:
                # Intermediate Catch Event może rozpoczynać proces w Pool (zastępując Start Event)
                # W multi-pool może mieć tylko Message Flow wchodzący, bez Sequence Flow wchodzących
                if sequence_incoming and len(participants) > 1:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message="Intermediate Catch Event rozpoczynający Pool nie powinien mieć Sequence Flow wchodzących w procesie multi-pool",
                        suggestion="Użyj Message Flow do komunikacji między Pool",
                        auto_fixable=False
                    ))
                    
            elif element_type in ['intermediateThrowEvent', 'intermediateMessageThrowEvent']:
                # Intermediate Throw Event może kończyć proces w Pool (zastępując End Event)
                # W multi-pool może mieć tylko Message Flow wychodzący, bez Sequence Flow wychodzących do innych Pool
                if sequence_outgoing and len(participants) > 1:
                    # Sprawdź czy Sequence Flow idzie do innego Pool
                    cross_pool_sequences = []
                    element_pool = element.get('participant')
                    for seq_flow in sequence_outgoing:
                        target_element = next((e for e in elements if e.get('id') == seq_flow.get('target')), None)
                        if target_element and target_element.get('participant') != element_pool:
                            cross_pool_sequences.append(seq_flow)
                    
                    if cross_pool_sequences:
                        issues.append(BPMNComplianceIssue(
                            element_id=element_id,
                            element_type=element_type,
                            severity=BPMNSeverity.MAJOR,
                            rule_code=rule_code,
                            message="Intermediate Throw Event nie może wysyłać Sequence Flow do innego Pool",
                            suggestion="Użyj Message Flow do komunikacji między Pool",
                            auto_fixable=False
                        ))
                    
            elif element_type in ['userTask', 'serviceTask', 'manualTask', 'scriptTask', 'receiveTask', 'sendTask']:
                # Aktywności muszą mieć przepływy (Sequence Flow lub Message Flow)
                if not sequence_incoming and not message_incoming:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message=f"Aktywność {element_id} nie ma przepływu wchodzącego",
                        suggestion="Połącz aktywność z poprzednim elementem (Sequence Flow lub Message Flow)",
                        auto_fixable=False
                    ))
                if not sequence_outgoing and not message_outgoing:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message=f"Aktywność {element_id} nie ma przepływu wychodzącego",
                        suggestion="Połącz aktywność z następnym elementem (Sequence Flow lub Message Flow)",
                        auto_fixable=False
                    ))
        
        return issues
    
    def _check_gateway_flows(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza przepływy Gateway z uwzględnieniem multi-pool BPMN"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        participants = bpmn_json.get('participants', [])
        
        gateways = [e for e in elements if e.get('type', '').endswith('Gateway')]
        
        for gateway in gateways:
            gateway_id = gateway.get('id')
            gateway_type = gateway.get('type')
            gateway_pool = gateway.get('participant')
            
            incoming = [f for f in flows if f.get('target') == gateway_id]
            outgoing = [f for f in flows if f.get('source') == gateway_id]
            
            # Sprawdź czy Gateway nie wysyła Sequence Flow do innych Pool
            sequence_outgoing = [f for f in outgoing if f.get('type', 'sequence') == 'sequence']
            for seq_flow in sequence_outgoing:
                target_element = next((e for e in elements if e.get('id') == seq_flow.get('target')), None)
                if target_element and target_element.get('participant') != gateway_pool and len(participants) > 1:
                    issues.append(BPMNComplianceIssue(
                        element_id=gateway_id,
                        element_type=gateway_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message=f"Gateway nie może wysyłać Sequence Flow do innego Pool ('{target_element.get('participant')}')",
                        suggestion="Użyj Message Flow do komunikacji między Pool lub przenieś elementy do tego samego Pool",
                        auto_fixable=False
                    ))
            
            # Exclusive Gateway - musi mieć >1 wyjście
            if gateway_type == 'exclusiveGateway':
                if len(outgoing) < 2:
                    issues.append(BPMNComplianceIssue(
                        element_id=gateway_id,
                        element_type=gateway_type,
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message="Exclusive Gateway musi mieć co najmniej 2 przepływy wyjściowe",
                        suggestion="Dodaj alternatywne ścieżki lub usuń gateway",
                        auto_fixable=False
                    ))
                    
            # Parallel Gateway - musi mieć >1 wyjście lub >1 wejście
            elif gateway_type == 'parallelGateway':
                if len(incoming) <= 1 and len(outgoing) <= 1:
                    issues.append(BPMNComplianceIssue(
                        element_id=gateway_id,
                        element_type=gateway_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message="Parallel Gateway powinien mieć wiele wejść lub wyjść",
                        suggestion="Użyj gateway do rozgałęzienia lub łączenia przepływów",
                        auto_fixable=False
                    ))
        
        return issues
    
    def _check_pool_structure(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza strukturę Pools i Lanes z obsługą multi-pool BPMN"""
        issues = []
        participants = bpmn_json.get('participants', [])
        elements = bpmn_json.get('elements', [])
        
        # Sprawdź czy elementy są przypisane do uczestników (tylko w multi-pool)
        unassigned_elements = [e for e in elements if not e.get('participant')]
        
        if unassigned_elements and participants:
            for element in unassigned_elements:
                issues.append(BPMNComplianceIssue(
                    element_id=element.get('id', 'unknown'),
                    element_type=element.get('type', 'unknown'),
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="Element nie jest przypisany do żadnego uczestnika w procesie multi-pool",
                    suggestion="Przypisz element do odpowiedniego Pool/Lane lub usuń nieużywane elementy",
                    auto_fixable=True
                ))
        
        # Sprawdź czy każdy Pool ma sens (ma elementy)
        for participant in participants:
            participant_id = participant.get('id')
            participant_name = participant.get('name', participant_id)
            participant_elements = [e for e in elements if e.get('participant') == participant_id]
            
            if not participant_elements:
                issues.append(BPMNComplianceIssue(
                    element_id=participant_id,
                    element_type='pool',
                    severity=BPMNSeverity.WARNING,
                    rule_code=rule_code,
                    message=f"Pool '{participant_name}' jest pusty - nie zawiera elementów",
                    suggestion="Dodaj elementy do Pool lub usuń nieużywany Pool",
                    auto_fixable=False
                ))
            
        # Sprawdź czy proces nie ma zbyt wielu Pool (complexity check)
        if len(participants) > 5:
            issues.append(BPMNComplianceIssue(
                element_id="process",
                element_type="process", 
                severity=BPMNSeverity.WARNING,
                rule_code=rule_code,
                message=f"Proces ma zbyt wiele Pool ({len(participants)}) - może być trudny do zrozumienia",
                suggestion="Rozważ podział na mniejsze procesy lub grupowanie Pool w Lanes",
                auto_fixable=False
            ))
        
        return issues
    
    # === IMPLEMENTACJA REGUŁ SEMANTYCZNYCH ===
    
    def _check_element_naming(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza nazewnictwo elementów"""
        issues = []
        elements = bpmn_json.get('elements', [])
        
        for element in elements:
            element_id = element.get('id')
            element_name = element.get('name', '').strip()
            element_type = element.get('type')
            
            # Sprawdź czy element ma nazwę
            if not element_name:
                issues.append(BPMNComplianceIssue(
                    element_id=element_id,
                    element_type=element_type,
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="Element nie ma nazwy",
                    suggestion="Dodaj opisową nazwę elementu",
                    auto_fixable=False
                ))
            # Sprawdź jakość nazwy
            elif len(element_name) < 3:
                issues.append(BPMNComplianceIssue(
                    element_id=element_id,
                    element_type=element_type,
                    severity=BPMNSeverity.MINOR,
                    rule_code=rule_code,
                    message="Nazwa elementu jest zbyt krótka",
                    suggestion="Użyj bardziej opisowej nazwy (min. 3 znaki)",
                    auto_fixable=False
                ))
        
        return issues
    
    def _check_gateway_conditions(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza warunki Gateway"""
        issues = []
        elements = bpmn_json.get('elements', [])
        gateways = bpmn_json.get('gateways', [])
        
        exclusive_gateways = [e for e in elements if e.get('type') == 'exclusiveGateway']
        
        for gateway in exclusive_gateways:
            gateway_id = gateway.get('id')
            
            # Znajdź definicję gateway w sekcji gateways
            gateway_def = next((g for g in gateways if g.get('id') == gateway_id), None)
            
            if gateway_def:
                conditions = gateway_def.get('conditions', [])
                if not conditions:
                    issues.append(BPMNComplianceIssue(
                        element_id=gateway_id,
                        element_type='exclusiveGateway',
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message="Exclusive Gateway nie ma zdefiniowanych warunków",
                        suggestion="Dodaj warunki dla wszystkich przepływów wychodzących",
                        auto_fixable=False
                    ))
                else:
                    # Sprawdź czy są sensowne warunki
                    for condition in conditions:
                        condition_text = condition.get('condition', '').strip()
                        if not condition_text:
                            issues.append(BPMNComplianceIssue(
                                element_id=gateway_id,
                                element_type='exclusiveGateway',
                                severity=BPMNSeverity.MINOR,
                                rule_code=rule_code,
                                message="Gateway ma pusty warunek",
                                suggestion="Dodaj opisowy warunek decyzyjny",
                                auto_fixable=False
                            ))
        
        return issues
    
    def _check_message_flows(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza Message Flows między uczestnikami - ROZSZERZONA IMPLEMENTACJA dla multi-pool"""
        issues = []
        flows = bpmn_json.get('flows', [])  # Poprawiono z 'messageFlows'
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        
        # Filtruj tylko message flows
        message_flows = [f for f in flows if f.get('type') == 'message']
        
        for mf in message_flows:
            source_id = mf.get('source')
            target_id = mf.get('target')
            
            source_element = next((e for e in elements if e.get('id') == source_id), None)
            target_element = next((e for e in elements if e.get('id') == target_id), None)
            
            if source_element and target_element:
                source_pool = source_element.get('participant')
                target_pool = target_element.get('participant')
                
                # W procesach single-pool Message Flow jest dozwolony
                if len(participants) > 1:
                    # Message Flow musi łączyć różne Pools (tylko w multi-pool)
                    if source_pool == target_pool and source_pool is not None:
                        issues.append(BPMNComplianceIssue(
                            element_id=mf.get('id', f"messageFlow_{source_id}_{target_id}"),
                            element_type='messageFlow',
                            severity=rule_config["severity"],
                            rule_code=rule_code,
                            message="Message Flow łączy elementy z tego samego Pool - narusza zasadę ciągłości",
                            suggestion="Użyj Sequence Flow w obrębie Pool lub przenieś element do innego Pool",
                            auto_fixable=True
                        ))
                    
                    # W multi-pool sprawdź czy Message Flow rzeczywiście łączy różne Pool
                    if source_pool != target_pool and source_pool is not None and target_pool is not None:
                        # To jest prawidłowe użycie Message Flow
                        pass
                else:
                    # W single-pool Message Flow może być używany w szczególnych przypadkach
                    # np. dla modeling przepływu informacji
                    pass
                
                # Sprawdź czy źródło i cel są odpowiednie dla Message Flow
                invalid_source_types = ['sequenceFlow', 'association']
                invalid_target_types = ['sequenceFlow', 'association']
                
                if source_element.get('type') in invalid_source_types:
                    issues.append(BPMNComplianceIssue(
                        element_id=mf.get('id', f"messageFlow_{source_id}_{target_id}"),
                        element_type='messageFlow',
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message=f"Message Flow nie może pochodzić z elementu typu {source_element.get('type')}",
                        suggestion="Message Flow może pochodzić tylko z Activity, Event lub Gateway",
                        auto_fixable=False
                    ))
                
                if target_element.get('type') in invalid_target_types:
                    issues.append(BPMNComplianceIssue(
                        element_id=mf.get('id', f"messageFlow_{source_id}_{target_id}"),
                        element_type='messageFlow',
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message=f"Message Flow nie może prowadzić do elementu typu {target_element.get('type')}",
                        suggestion="Message Flow może prowadzić tylko do Activity, Event lub Gateway",
                        auto_fixable=False
                    ))
        
        return issues
    
    def _check_process_flow_logic(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza logiczność przepływu procesu"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Sprawdź czy nie ma cykli w przepływach
        visited = set()
        path = set()
        
        def has_cycle(element_id, visited, path):
            if element_id in path:
                return True
            if element_id in visited:
                return False
            
            visited.add(element_id)
            path.add(element_id)
            
            # Znajdź wszystkie wyjścia z tego elementu
            outgoing = [f for f in flows if f.get('source') == element_id and f.get('type', 'sequence') == 'sequence']
            for flow in outgoing:
                if has_cycle(flow.get('target'), visited, path):
                    return True
            
            path.remove(element_id)
            return False
        
        # Sprawdź cykle dla każdego elementu
        start_events = [e for e in elements if e.get('type') == 'startEvent']
        for start in start_events:
            if has_cycle(start.get('id'), visited, path):
                issues.append(BPMNComplianceIssue(
                    element_id=start.get('id'),
                    element_type='startEvent',
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="Wykryto cykl w przepływie procesu",
                    suggestion="Usuń cykliczne połączenia lub użyj odpowiedniego wzorca BPMN",
                    auto_fixable=False
                ))
        
        return issues
    
    def _check_activity_types(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza typy aktywności"""
        issues = []
        elements = bpmn_json.get('elements', [])
        
        activities = [e for e in elements if e.get('type', '').endswith('Task')]
        
        for activity in activities:
            element_id = activity.get('id')
            element_type = activity.get('type')
            task_type = activity.get('task_type')
            
            # Sprawdź czy aktywność ma określony typ
            if not task_type:
                issues.append(BPMNComplianceIssue(
                    element_id=element_id,
                    element_type=element_type,
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="Aktywność nie ma określonego typu (user/service/manual)",
                    suggestion="Dodaj odpowiedni task_type: 'user', 'service', lub 'manual'",
                    auto_fixable=True
                ))
        
        return issues
    
    # === IMPLEMENTACJA REGUŁ SKŁADNIOWYCH ===
    
    def _check_unique_ids(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza unikalność ID elementów"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Zbierz wszystkie ID
        all_ids = []
        for element in elements:
            if element.get('id'):
                all_ids.append(element['id'])
        for flow in flows:
            if flow.get('id'):
                all_ids.append(flow['id'])
        
        # Znajdź duplikaty
        seen_ids = set()
        for id_val in all_ids:
            if id_val in seen_ids:
                issues.append(BPMNComplianceIssue(
                    element_id=id_val,
                    element_type="unknown",
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message=f"Duplikowane ID: {id_val}",
                    suggestion="Zmień ID na unikalne",
                    auto_fixable=True
                ))
            seen_ids.add(id_val)
        
        return issues
    
    def _check_required_attributes(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza wymagane atrybuty"""
        issues = []
        elements = bpmn_json.get('elements', [])
        
        for element in elements:
            element_type = element.get('type')
            
            # Sprawdź ID
            if not element.get('id'):
                issues.append(BPMNComplianceIssue(
                    element_id="unknown",
                    element_type=element_type,
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="Element nie ma ID",
                    suggestion="Dodaj unikalne ID do elementu",
                    auto_fixable=True
                ))
            
            # Sprawdź type
            if not element_type:
                issues.append(BPMNComplianceIssue(
                    element_id=element.get('id', 'unknown'),
                    element_type="unknown",
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="Element nie ma typu",
                    suggestion="Dodaj type elementu (np. 'userTask', 'startEvent')",
                    auto_fixable=False
                ))
        
        return issues
    
    def _check_flow_references(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza odwołania w przepływach"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Zbierz ID wszystkich elementów
        element_ids = {e.get('id') for e in elements if e.get('id')}
        
        # Sprawdź każdy przepływ
        for flow in flows:
            flow_id = flow.get('id', 'unknown')
            source = flow.get('source')
            target = flow.get('target')
            
            if source and source not in element_ids:
                issues.append(BPMNComplianceIssue(
                    element_id=flow_id,
                    element_type="sequenceFlow",
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message=f"Przepływ odwołuje się do nieistniejącego source: {source}",
                    suggestion="Popraw odwołanie source lub dodaj brakujący element",
                    auto_fixable=False
                ))
                
            if target and target not in element_ids:
                issues.append(BPMNComplianceIssue(
                    element_id=flow_id,
                    element_type="sequenceFlow",
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message=f"Przepływ odwołuje się do nieistniejącego target: {target}",
                    suggestion="Popraw odwołanie target lub dodaj brakujący element",
                    auto_fixable=False
                ))
        
        return issues
    
    # === IMPLEMENTACJA REGUŁ STYLISTYCZNYCH ===
    
    def _check_naming_conventions(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza konwencje nazewnictwa"""
        issues = []
        elements = bpmn_json.get('elements', [])
        
        for element in elements:
            element_id = element.get('id', '')
            element_name = element.get('name', '')
            
            # Sprawdź konwencję ID (camelCase lub snake_case)
            if element_id and not (element_id.replace('_', '').isalnum()):
                issues.append(BPMNComplianceIssue(
                    element_id=element_id,
                    element_type=element.get('type'),
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="ID elementu nie następuje konwencji nazewnictwa",
                    suggestion="Użyj camelCase lub snake_case dla ID",
                    auto_fixable=True
                ))
        
        return issues
    
    def _check_process_complexity(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza złożoność procesu"""
        issues = []
        elements = bpmn_json.get('elements', [])
        
        # Sprawdź liczbę elementów
        if len(elements) > 20:
            issues.append(BPMNComplianceIssue(
                element_id="process",
                element_type="process",
                severity=rule_config["severity"],
                rule_code=rule_code,
                message=f"Proces jest zbyt złożony ({len(elements)} elementów)",
                suggestion="Rozważ podział na mniejsze procesy lub subprocesy",
                auto_fixable=False
            ))
        
        return issues
    
    def _check_participant_distribution(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza rozkład elementów między uczestników"""
        issues = []
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        
        if not participants:
            return issues
        
        # Policz elementy na uczestnika
        participant_counts = {}
        for element in elements:
            participant = element.get('participant')
            if participant:
                participant_counts[participant] = participant_counts.get(participant, 0) + 1
        
        # Sprawdź czy któryś uczestnik ma za dużo elementów
        total_elements = len(elements)
        for participant_id, count in participant_counts.items():
            if count > total_elements * 0.7:  # Więcej niż 70%
                issues.append(BPMNComplianceIssue(
                    element_id=participant_id,
                    element_type="participant",
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message=f"Uczestnik ma zbyt wiele elementów ({count}/{total_elements})",
                    suggestion="Rozłóż elementy równomiernie między uczestników",
                    auto_fixable=False
                ))
        
        return issues
    
    # === METODY OBLICZANIA WYNIKÓW ===
    
    def _calculate_compliance_score(self, issues: List[BPMNComplianceIssue]) -> float:
        """Oblicza wynik zgodności (0-100) - ZRÓWNOWAŻONY algorytm"""
        if not issues:
            return 100.0
        
        # ZRÓWNOWAŻONE wagi - mniej surowe dla critical
        weights = {
            BPMNSeverity.CRITICAL: -12,    # Zmniejszone z -25 do -12
            BPMNSeverity.MAJOR: -6,        # Zmniejszone z -10 do -6
            BPMNSeverity.MINOR: -2,        # Zmniejszone z -3 do -2
            BPMNSeverity.WARNING: -0.5     # Zmniejszone z -1 do -0.5
        }
        
        total_penalty = sum(weights.get(issue.severity, 0) for issue in issues)
        score = max(20, 100 + total_penalty)  # Minimum 20% zamiast 0% dla procesów z podstawową strukturą
        
        return round(score, 1)
    
    def _determine_compliance_level(self, score: float) -> str:
        """Określa poziom zgodności"""
        if score >= 95:
            return "EXCELLENT"
        elif score >= 85:
            return "GOOD" 
        elif score >= 70:
            return "FAIR"
        elif score >= 50:
            return "POOR"
        else:
            return "INVALID"
    
    def _generate_statistics(self, issues: List[BPMNComplianceIssue], bpmn_json: Dict) -> Dict[str, Any]:
        """Generuje statystyki zgodności"""
        severity_counts = {}
        for issue in issues:
            severity = issue.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        participants = bpmn_json.get('participants', [])
        
        return {
            'total_issues': len(issues),
            'issues_by_severity': severity_counts,
            'auto_fixable_issues': len([i for i in issues if i.auto_fixable]),
            'process_statistics': {
                'elements_count': len(elements),
                'flows_count': len(flows),
                'participants_count': len(participants),
                'start_events': len([e for e in elements if e.get('type') == 'startEvent']),
                'end_events': len([e for e in elements if e.get('type') == 'endEvent']),
                'gateways': len([e for e in elements if 'Gateway' in e.get('type', '')]),
                'activities': len([e for e in elements if 'Task' in e.get('type', '')])
            }
        }
    
    def _determine_improvement_priorities(self, issues: List[BPMNComplianceIssue]) -> List[str]:
        """Określa priorytety poprawek"""
        priorities = []
        
        # Groupuj issues po severity
        critical_issues = [i for i in issues if i.severity == BPMNSeverity.CRITICAL]
        major_issues = [i for i in issues if i.severity == BPMNSeverity.MAJOR]
        
        if critical_issues:
            priorities.append("CRITICAL: Napraw błędy strukturalne (Start/End Events, ID, przepływy)")
        
        if major_issues:
            priorities.append("MAJOR: Popraw nazewnictwo i semantykę elementów")
        
        auto_fixable = [i for i in issues if i.auto_fixable]
        if auto_fixable:
            priorities.append(f"AUTO-FIX: {len(auto_fixable)} problemów można naprawić automatycznie")
        
        if not priorities:
            priorities.append("Proces jest zgodny ze standardem BPMN - rozważ optymalizację stylistyczną")
        
        return priorities

    def get_auto_fix_suggestions(self, issues: List[BPMNComplianceIssue]) -> Dict[str, Any]:
        """Zwraca sugestie automatycznych poprawek"""
        auto_fixes = []
        
        for issue in issues:
            if issue.auto_fixable:
                auto_fixes.append({
                    'element_id': issue.element_id,
                    'rule_code': issue.rule_code,
                    'fix_type': self._determine_fix_type(issue),
                    'fix_data': self._generate_fix_data(issue)
                })
        
        return {
            'auto_fixes': auto_fixes,
            'manual_review_required': [i for i in issues if not i.auto_fixable]
        }
    
    def _determine_fix_type(self, issue: BPMNComplianceIssue) -> str:
        """Określa typ automatycznej poprawki"""
        if 'ID' in issue.message or issue.rule_code == 'SYNT_001':
            return 'generate_unique_id'
        elif 'Start Event' in issue.message:
            return 'add_start_event'
        elif 'End Event' in issue.message:
            return 'add_end_event'
        elif 'task_type' in issue.message:
            return 'add_task_type'
        elif 'naming convention' in issue.message:
            return 'fix_naming'
        else:
            return 'generic_fix'
    
    def _generate_fix_data(self, issue: BPMNComplianceIssue) -> Dict[str, Any]:
        """Generuje dane do automatycznej poprawki"""
        # Implementacja generowania danych poprawek
        return {
            'element_id': issue.element_id,
            'suggested_value': issue.suggestion,
            'rule_code': issue.rule_code
        }

    # === NOWE IMPLEMENTACJE REGUŁ ===
    
    def _check_pool_continuity(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza ciągłość procesów w Pool - NOWA REGUŁA"""
        issues = []
        participants = bpmn_json.get('participants', [])
        flows = bpmn_json.get('flows', [])  # Poprawiono z 'sequenceFlows' i 'messageFlows'
        elements = bpmn_json.get('elements', [])
        
        # Podziel flows na message flows i sequence flows
        message_flows = [f for f in flows if f.get('type') == 'message']
        
        for participant in participants:
            participant_id = participant.get('id')
            participant_elements = [e for e in elements if e.get('participant') == participant_id]
            
            # Sprawdź czy wszystkie elementy w Pool są połączone Sequence Flow
            for element in participant_elements:
                element_id = element.get('id')
                
                # Szukaj przerywanych połączeń (Message Flow) wewnątrz Pool
                internal_message_flows = [
                    mf for mf in message_flows 
                    if (mf.get('source') == element_id or mf.get('target') == element_id)
                    and self._both_elements_in_same_pool(mf, participant_id, elements)
                ]
                
                if internal_message_flows:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element.get('type', 'unknown'),
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message=f"Element w Pool '{participant.get('name', participant_id)}' używa Message Flow zamiast Sequence Flow",
                        suggestion="Zamień Message Flow na Sequence Flow w obrębie tego samego Pool",
                        auto_fixable=True
                    ))
        
        return issues
    
    def _check_pool_autonomy(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza autonomię Pool - proces musi mieć logiczne rozpoczęcie i zakończenie"""
        issues = []
        participants = bpmn_json.get('participants', [])
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # W procesach wielopoolowych wystarczy jeden globalny Start Event
        global_start_events = [e for e in elements if e.get('type') == 'startEvent']
        global_end_events = [e for e in elements if e.get('type') == 'endEvent']
        
        # Sprawdź czy cały proces ma przynajmniej jeden Start Event
        if not global_start_events:
            issues.append(BPMNComplianceIssue(
                element_id='process',
                element_type='process',
                severity=BPMNSeverity.CRITICAL,
                rule_code=rule_code,
                message="Proces nie ma Start Event",
                suggestion="Dodaj Start Event na początku procesu",
                auto_fixable=True
            ))
        
        # Sprawdź czy cały proces ma przynajmniej jeden End Event
        if not global_end_events:
            issues.append(BPMNComplianceIssue(
                element_id='process',
                element_type='process',
                severity=BPMNSeverity.CRITICAL,
                rule_code=rule_code,
                message="Proces nie ma End Event",
                suggestion="Dodaj End Event na końcu procesu",
                auto_fixable=True
            ))
        
        # Sprawdź czy Pool z aktywnościami ma sposób na rozpoczęcie
        for participant in participants:
            participant_id = participant.get('id')
            participant_name = participant.get('name', participant_id)
            participant_elements = [e for e in elements if e.get('participant') == participant_id]
            
            # Tylko sprawdź Pool które mają aktywności
            activities = [e for e in participant_elements if e.get('type') in ['userTask', 'serviceTask', 'manualTask', 'scriptTask', 'receiveTask', 'sendTask']]
            if not activities:
                continue  # Skip pools without activities
            
            # Sprawdź czy Pool ma sposób na rozpoczęcie (Start Event, Intermediate Catch Event lub Message Flow wchodzący)
            start_events = [e for e in participant_elements if e.get('type') == 'startEvent']
            intermediate_catch_events = [e for e in participant_elements if e.get('type') in ['intermediateCatchEvent', 'intermediateMessageCatchEvent']]
            
            # Sprawdź Message Flow wchodzący (również z external)
            incoming_messages = []
            for f in flows:
                if f.get('type') == 'message':
                    target_id = f.get('target')
                    if target_id in [e.get('id') for e in participant_elements]:
                        incoming_messages.append(f)
            
            if not start_events and not intermediate_catch_events and not incoming_messages:
                # To może być problem tylko jeśli Pool ma aktywności ale nie ma sposobu ich uruchomienia
                issues.append(BPMNComplianceIssue(
                    element_id=participant_id,
                    element_type='pool',
                    severity=BPMNSeverity.MAJOR,  # Obniżone z CRITICAL
                    rule_code=rule_code,
                    message=f"Pool '{participant_name}' ma aktywności ale nie ma sposobu ich uruchomienia",
                    suggestion="Dodaj Start Event, Intermediate Catch Event lub Message Flow wchodzący do tego Pool",
                    auto_fixable=False  # Nie auto-fix bo wymaga analizy logiki
                ))
        
        return issues
    
    def _both_elements_in_same_pool(self, message_flow: Dict, participant_id: str, elements: List[Dict]) -> bool:
        """Sprawdza czy oba elementy Message Flow są w tym samym Pool"""
        source_element = next((e for e in elements if e.get('id') == message_flow.get('source')), None)
        target_element = next((e for e in elements if e.get('id') == message_flow.get('target')), None)
        
        return (source_element and target_element and 
                source_element.get('participant') == participant_id and
                target_element.get('participant') == participant_id)
    
    def _check_message_flow_end_events(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza czy End Event z wyjściowym Message Flow ma odpowiedni typ"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Znajdź wszystkie End Events
        end_events = [e for e in elements if e.get('type') == 'endEvent']
        
        # Sprawdź każdy End Event
        for end_event in end_events:
            event_id = end_event.get('id')
            
            # Sprawdź czy ma wyjściowe Message Flow
            outgoing_message_flows = [
                f for f in flows 
                if f.get('source') == event_id and f.get('type') == 'message'
            ]
            
            # Sprawdź czy ma wejściowe Message Flow (co jest niepoprawne)
            incoming_message_flows = [
                f for f in flows 
                if f.get('target') == event_id and f.get('type') == 'message'
            ]
            
            # End Event nie powinien mieć wejściowego Message Flow
            if incoming_message_flows:
                issues.append(BPMNComplianceIssue(
                    element_id=event_id,
                    element_type='endEvent',
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="End Event nie może mieć wejściowego Message Flow",
                    suggestion="Message Flow może prowadzić tylko do Activity lub Intermediate Event",
                    auto_fixable=False
                ))
            
            # Jeśli End Event ma wyjściowy Message Flow, powinien być typu Message
            if outgoing_message_flows:
                event_type = end_event.get('event_type')
                if event_type != 'message':
                    issues.append(BPMNComplianceIssue(
                        element_id=event_id,
                        element_type='endEvent',
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message="End Event z wyjściowym Message Flow musi być typu 'message'",
                        suggestion="Zmień typ End Event na 'message' lub usuń Message Flow",
                        auto_fixable=True
                    ))
        
        return issues
    
    def _check_message_flow_intermediate_events(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza czy Intermediate Events z Message Flow mają odpowiedni typ"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Znajdź wszystkie Intermediate Events
        intermediate_events = [
            e for e in elements 
            if e.get('type') in ['intermediateCatchEvent', 'intermediateThrowEvent']
        ]
        
        for event in intermediate_events:
            event_id = event.get('id')
            event_type = event.get('type')
            
            # Sprawdź czy ma Message Flow
            if event_type == 'intermediateCatchEvent':
                # Catch Event - sprawdź wejściowe Message Flow
                incoming_message_flows = [
                    f for f in flows 
                    if f.get('target') == event_id and f.get('type') == 'message'
                ]
                
                if incoming_message_flows:
                    sub_type = event.get('event_type', event.get('sub_type'))
                    if sub_type != 'message':
                        issues.append(BPMNComplianceIssue(
                            element_id=event_id,
                            element_type=event_type,
                            severity=rule_config["severity"],
                            rule_code=rule_code,
                            message="Intermediate Catch Event z wejściowym Message Flow musi być typu 'message'",
                            suggestion="Zmień typ na 'message' lub użyj Sequence Flow",
                            auto_fixable=True
                        ))
                        
            elif event_type == 'intermediateThrowEvent':
                # Throw Event - sprawdź wyjściowe Message Flow
                outgoing_message_flows = [
                    f for f in flows 
                    if f.get('source') == event_id and f.get('type') == 'message'
                ]
                
                if outgoing_message_flows:
                    sub_type = event.get('event_type', event.get('sub_type'))
                    if sub_type != 'message':
                        issues.append(BPMNComplianceIssue(
                            element_id=event_id,
                            element_type=event_type,
                            severity=rule_config["severity"],
                            rule_code=rule_code,
                            message="Intermediate Throw Event z wyjściowym Message Flow musi być typu 'message'",
                            suggestion="Zmień typ na 'message' lub użyj Sequence Flow",
                            auto_fixable=True
                        ))
                        
            # Sprawdź czy Intermediate Event może być typu Timer
            if event.get('event_type') == 'timer' or event.get('sub_type') == 'timer':
                # Timer Events są poprawne - mogą być używane do opóźnień czasowych
                pass
        
        return issues
    
    def _check_message_flow_targets(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza czy Message Flow prowadzi do odpowiednich elementów"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Znajdź wszystkie Message Flows
        message_flows = [f for f in flows if f.get('type') == 'message']
        
        for msg_flow in message_flows:
            target_id = msg_flow.get('target')
            source_id = msg_flow.get('source')
            
            # Znajdź target element
            target_element = next((e for e in elements if e.get('id') == target_id), None)
            source_element = next((e for e in elements if e.get('id') == source_id), None)
            
            if target_element:
                target_type = target_element.get('type')
                
                # Message Flow może prowadzić do:
                # - Activity (userTask, serviceTask, etc.)
                # - Intermediate Events
                # - Start Events (w niektórych przypadkach)
                # ALE NIE do End Events
                
                valid_target_types = [
                    'userTask', 'serviceTask', 'manualTask', 'scriptTask', 
                    'receiveTask', 'sendTask', 'businessRuleTask',
                    'intermediateCatchEvent', 'intermediateThrowEvent',
                    'startEvent'  # Message może uruchamiać proces
                ]
                
                if target_type == 'endEvent':
                    issues.append(BPMNComplianceIssue(
                        element_id=msg_flow.get('id', f"messageFlow_{source_id}_{target_id}"),
                        element_type='messageFlow',
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message="Message Flow nie może prowadzić do End Event",
                        suggestion="Message Flow może prowadzić tylko do Activity lub Intermediate Event",
                        auto_fixable=False
                    ))
                    
                elif target_type not in valid_target_types:
                    issues.append(BPMNComplianceIssue(
                        element_id=msg_flow.get('id', f"messageFlow_{source_id}_{target_id}"),
                        element_type='messageFlow',
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message=f"Message Flow nie może prowadzić do elementu typu '{target_type}'",
                        suggestion="Message Flow może prowadzić tylko do Activity, Start Event lub Intermediate Event",
                        auto_fixable=False
                    ))
            
            # Sprawdź source element
            if source_element:
                source_type = source_element.get('type')
                
                # Message Flow może pochodzić z:
                # - Activity
                # - Intermediate Events
                # - End Events (jako wyjście z procesu)
                # ALE NIE ze Start Events
                
                valid_source_types = [
                    'userTask', 'serviceTask', 'manualTask', 'scriptTask',
                    'receiveTask', 'sendTask', 'businessRuleTask',
                    'intermediateCatchEvent', 'intermediateThrowEvent',
                    'endEvent'  # End Event może wysyłać wiadomość na zewnątrz
                ]
                
                if source_type == 'startEvent':
                    issues.append(BPMNComplianceIssue(
                        element_id=msg_flow.get('id', f"messageFlow_{source_id}_{target_id}"),
                        element_type='messageFlow',
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message="Message Flow nie może pochodzić ze Start Event",
                        suggestion="Start Event może tylko odbierać Message Flow, nie wysyłać",
                        auto_fixable=False
                    ))
                    
                elif source_type not in valid_source_types:
                    issues.append(BPMNComplianceIssue(
                        element_id=msg_flow.get('id', f"messageFlow_{source_id}_{target_id}"),
                        element_type='messageFlow',
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message=f"Message Flow nie może pochodzić z elementu typu '{source_type}'",
                        suggestion="Message Flow może pochodzić tylko z Activity, Intermediate Event lub End Event",
                        auto_fixable=False
                    ))
        
        return issues
                
    def parse_bpmn_xml(self, xml_content: str) -> Dict:
        """
        Parsuje BPMN XML do formatu JSON używanego przez walidator
        
        Args:
            xml_content: Zawartość BPMN XML
            
        Returns:
            Dict: BPMN w formacie JSON
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Namespace mapping
            namespaces = {
                'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
                'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
                'dc': 'http://www.omg.org/spec/DD/20100524/DC',
                'di': 'http://www.omg.org/spec/DD/20100524/DI'
            }
            
            # Initialize result structure
            result = {
                "process_name": "Parsed BPMN Process",
                "participants": [],
                "elements": [],
                "flows": []
            }
            
            # Parse collaboration (participants and message flows)
            collaboration = root.find('.//bpmn:collaboration', namespaces)
            if collaboration:
                # Parse participants
                for participant in collaboration.findall('bpmn:participant', namespaces):
                    participant_data = {
                        "id": participant.get('id', ''),
                        "name": participant.get('name', ''),
                        "processRef": participant.get('processRef', ''),
                        "type": "human"  # Default type
                    }
                    result["participants"].append(participant_data)
                
                # Parse message flows
                for msg_flow in collaboration.findall('bpmn:messageFlow', namespaces):
                    flow_data = {
                        "id": msg_flow.get('id', ''),
                        "source": msg_flow.get('sourceRef', ''),
                        "target": msg_flow.get('targetRef', ''),
                        "type": "message",
                        "name": msg_flow.get('name', '')
                    }
                    result["flows"].append(flow_data)
            
            # Parse processes and elements
            for process in root.findall('.//bpmn:process', namespaces):
                process_id = process.get('id', '')
                
                # Find participant for this process
                participant_id = None
                for participant in result["participants"]:
                    if participant.get("processRef") == process_id:
                        participant_id = participant.get("id")
                        break
                
                # Parse all elements in process
                for element in process:
                    tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
                    
                    # Skip sequence flows - they're handled separately
                    if tag_name == 'sequenceFlow':
                        continue
                    
                    element_data = {
                        "id": element.get('id', ''),
                        "name": element.get('name', ''),
                        "type": tag_name,
                        "participant": participant_id or process_id
                    }
                    
                    # Add specific attributes based on element type
                    if tag_name in ['userTask', 'serviceTask', 'sendTask', 'receiveTask']:
                        element_data["task_type"] = tag_name.replace('Task', '').lower()
                    elif tag_name in ['exclusiveGateway', 'parallelGateway', 'inclusiveGateway']:
                        element_data["gateway_type"] = tag_name.replace('Gateway', '').lower()
                    
                    result["elements"].append(element_data)
                
                # Parse sequence flows
                for seq_flow in process.findall('bpmn:sequenceFlow', namespaces):
                    flow_data = {
                        "id": seq_flow.get('id', ''),
                        "source": seq_flow.get('sourceRef', ''),
                        "target": seq_flow.get('targetRef', ''),
                        "type": "sequence",
                        "name": seq_flow.get('name', '')
                    }
                    
                    # Parse condition expression if exists
                    condition_expr = seq_flow.find('bpmn:conditionExpression', namespaces)
                    if condition_expr is not None and condition_expr.text:
                        flow_data["condition"] = condition_expr.text.strip()
                    
                    result["flows"].append(flow_data)
            
            return result
            
        except ET.ParseError as e:
            raise ValueError(f"Błąd parsowania XML: {str(e)}")
        except Exception as e:
            raise ValueError(f"Błąd podczas parsowania BPMN XML: {str(e)}")
    
    def validate_bpmn_xml(self, xml_content: str) -> BPMNComplianceReport:
        """
        Waliduje BPMN XML i zwraca raport zgodności
        
        Args:
            xml_content: Zawartość BPMN XML
            
        Returns:
            BPMNComplianceReport: Raport walidacji
        """
        try:
            # Parse XML to JSON
            bpmn_json = self.parse_bpmn_xml(xml_content)
            
            # Validate using existing JSON validation
            return self.validate_bpmn_compliance(bpmn_json)
            
        except Exception as e:
            # Return error report if parsing fails
            return BPMNComplianceReport(
                overall_score=0.0,
                compliance_level="INVALID",
                issues=[BPMNComplianceIssue(
                    element_id="",
                    element_type="xml",
                    severity=BPMNSeverity.CRITICAL,
                    rule_code="XML_PARSE",
                    message=f"Błąd parsowania BPMN XML: {str(e)}",
                    suggestion="Sprawdź poprawność składni XML i zgodność ze standardem BPMN 2.0",
                    auto_fixable=False
                )],
                statistics={"parse_error": True},
                improvement_priorities=["Naprawa błędów XML"]
            )