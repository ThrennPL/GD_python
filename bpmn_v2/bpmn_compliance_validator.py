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
        
        return BPMNComplianceReport(
            overall_score=overall_score,
            compliance_level=compliance_level,
            issues=issues,
            statistics=statistics,
            improvement_priorities=priorities
        )
    
    # === IMPLEMENTACJA REGUŁ STRUKTURALNYCH ===
    
    def _check_start_events(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza obecność Start Events"""
        issues = []
        elements = bpmn_json.get('elements', [])
        
        start_events = [e for e in elements if e.get('type') == 'startEvent']
        
        if not start_events:
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
        
        return issues
    
    def _check_end_events(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza obecność End Events"""
        issues = []
        elements = bpmn_json.get('elements', [])
        
        end_events = [e for e in elements if e.get('type') == 'endEvent']
        
        if not end_events:
            issues.append(BPMNComplianceIssue(
                element_id="process",
                element_type="process",
                severity=rule_config["severity"],
                rule_code=rule_code,
                message="Proces nie ma End Event",
                suggestion="Dodaj End Event na końcu procesu",
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
            
            # Sprawdź reguły dla różnych typów elementów
            if element_type == 'startEvent':
                if incoming:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message="Start Event nie może mieć przepływów wchodzących",
                        suggestion="Usuń przepływy wchodzące do Start Event",
                        auto_fixable=True
                    ))
                if not outgoing:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message="Start Event musi mieć przepływ wychodzący",
                        suggestion="Połącz Start Event z następną aktywnością",
                        auto_fixable=False
                    ))
                    
            elif element_type == 'endEvent':
                if not incoming:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=rule_config["severity"],
                        rule_code=rule_code,
                        message="End Event musi mieć przepływ wchodzący",
                        suggestion="Połącz poprzednią aktywność z End Event",
                        auto_fixable=False
                    ))
                if outgoing:
                    # W procesach wielopoolowych End Event może mieć Message Flow do innego Pool
                    sequence_outgoing = [f for f in outgoing if f.get('type', 'sequence') == 'sequence']
                    if sequence_outgoing:
                        issues.append(BPMNComplianceIssue(
                            element_id=element_id,
                            element_type=element_type,
                            severity=BPMNSeverity.MAJOR,
                            rule_code=rule_code,
                            message="End Event nie może mieć Sequence Flow wychodzących",
                            suggestion="Usuń Sequence Flow z End Event lub zmień na Message Flow jeśli komunikuje z innym Pool",
                            auto_fixable=False
                        ))
                    
            elif element_type in ['userTask', 'serviceTask', 'manualTask', 'scriptTask']:
                if not incoming:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message=f"Aktywność {element_id} nie ma przepływu wchodzącego",
                        suggestion="Połącz aktywność z poprzednim elementem",
                        auto_fixable=False
                    ))
                if not outgoing:
                    issues.append(BPMNComplianceIssue(
                        element_id=element_id,
                        element_type=element_type,
                        severity=BPMNSeverity.MAJOR,
                        rule_code=rule_code,
                        message=f"Aktywność {element_id} nie ma przepływu wychodzącego",
                        suggestion="Połącz aktywność z następnym elementem",
                        auto_fixable=False
                    ))
        
        return issues
    
    def _check_gateway_flows(self, bpmn_json: Dict, rule_code: str, rule_config: Dict) -> List[BPMNComplianceIssue]:
        """Sprawdza przepływy Gateway"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        gateways = [e for e in elements if e.get('type', '').endswith('Gateway')]
        
        for gateway in gateways:
            gateway_id = gateway.get('id')
            gateway_type = gateway.get('type')
            
            incoming = [f for f in flows if f.get('target') == gateway_id]
            outgoing = [f for f in flows if f.get('source') == gateway_id]
            
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
        """Sprawdza strukturę Pools i Lanes"""
        issues = []
        participants = bpmn_json.get('participants', [])
        elements = bpmn_json.get('elements', [])
        
        # Sprawdź czy elementy są przypisane do uczestników
        unassigned_elements = [e for e in elements if not e.get('participant')]
        
        if unassigned_elements and participants:
            for element in unassigned_elements:
                issues.append(BPMNComplianceIssue(
                    element_id=element.get('id', 'unknown'),
                    element_type=element.get('type', 'unknown'),
                    severity=rule_config["severity"],
                    rule_code=rule_code,
                    message="Element nie jest przypisany do żadnego uczestnika",
                    suggestion="Przypisz element do odpowiedniego Pool/Lane",
                    auto_fixable=True
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
        """Sprawdza Message Flows między uczestnikami - ROZSZERZONA IMPLEMENTACJA"""
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
                
                # Message Flow musi łączyć różne Pools
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
        """Oblicza wynik zgodności (0-100)"""
        if not issues:
            return 100.0
        
        # Wagi dla różnych poziomów
        weights = {
            BPMNSeverity.CRITICAL: -25,
            BPMNSeverity.MAJOR: -10,
            BPMNSeverity.MINOR: -3,
            BPMNSeverity.WARNING: -1
        }
        
        total_penalty = sum(weights.get(issue.severity, 0) for issue in issues)
        score = max(0, 100 + total_penalty)
        
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
            
            # Sprawdź czy Pool ma sposób na rozpoczęcie (Start Event lub Message Flow wchodzący)
            start_events = [e for e in participant_elements if e.get('type') == 'startEvent']
            incoming_messages = [f for f in flows if f.get('target') in [e.get('id') for e in participant_elements] and f.get('type') == 'message']
            
            if not start_events and not incoming_messages:
                # To może być problem tylko jeśli Pool ma aktywności ale nie ma sposobu ich uruchomienia
                issues.append(BPMNComplianceIssue(
                    element_id=participant_id,
                    element_type='pool',
                    severity=BPMNSeverity.MAJOR,  # Obniżone z CRITICAL
                    rule_code=rule_code,
                    message=f"Pool '{participant_name}' ma aktywności ale nie ma sposobu ich uruchomienia",
                    suggestion="Dodaj Start Event lub Message Flow wchodzący do tego Pool",
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