"""
BPMN Iterative Improvement Engine
System iteracyjnych poprawek opartych na regułach zgodności BPMN

Autor: AI Assistant
Data: 2025-11-26
"""

from typing import Dict, List, Any, Tuple
import json
from dataclasses import asdict

from .bpmn_compliance_validator import (
    BPMNComplianceValidator, 
    BPMNComplianceReport, 
    BPMNComplianceIssue, 
    BPMNSeverity
)

class BPMNImprovementEngine:
    """
    Silnik iteracyjnych poprawek procesów BPMN
    
    Funkcjonalności:
    1. Automatyczne naprawy prostych błędów
    2. Generowanie promptów AI dla skomplikowanych poprawek
    3. Iteracyjna poprawa jakości procesu
    4. Priorytetyzacja poprawek według ważności
    """
    
    def __init__(self, ai_pipeline=None):
        self.validator = BPMNComplianceValidator()
        self.ai_pipeline = ai_pipeline
        self.max_iterations = 5
        self.target_compliance_score = 85.0
        
    def improve_bpmn_process(self, bpmn_json: Dict, target_score: float = None, 
                           max_iterations: int = None) -> Dict[str, Any]:
        """
        Główna metoda iteracyjnej poprawy procesu BPMN
        
        Args:
            bpmn_json: Proces BPMN do poprawienia
            target_score: Docelowy wynik zgodności (0-100)
            max_iterations: Maksymalna liczba iteracji
            
        Returns:
            Kompletny raport z historią poprawek
        """
        target_score = target_score or self.target_compliance_score
        max_iterations = max_iterations or self.max_iterations
        
        improvement_history = []
        current_process = bpmn_json.copy()
        iteration = 0
        
        print(f"Starting BPMN improvement process")
        print(f"Target compliance score: {target_score}")
        print(f"🔢 Max iterations: {max_iterations}")
        
        while iteration < max_iterations:
            print(f"\n📍 ITERATION {iteration + 1}")
            
            # Walidacja aktualnego stanu
            compliance_report = self.validator.validate_bpmn_compliance(current_process)
            
            print(f"Current compliance score: {compliance_report.overall_score}")
            print(f"🏷️  Compliance level: {compliance_report.compliance_level}")
            print(f"⚠️  Issues found: {len(compliance_report.issues)}")
            
            # Zapisz stan iteracji
            iteration_data = {
                'iteration': iteration + 1,
                'compliance_report': asdict(compliance_report),
                'process_state': current_process.copy(),
                'improvements_applied': []
            }
            
            # Sprawdź czy osiągnięto cel
            if compliance_report.overall_score >= target_score:
                print(f"Target compliance score achieved!")
                iteration_data['status'] = 'target_achieved'
                improvement_history.append(iteration_data)
                break
            
            # Brak problemów do naprawienia
            if not compliance_report.issues:
                print(f"No more issues to fix!")
                iteration_data['status'] = 'no_issues'
                improvement_history.append(iteration_data)
                break
            
            # Zastosuj poprawki
            improved_process, applied_fixes = self._apply_improvements(
                current_process, compliance_report
            )
            
            # Sprawdź czy coś się zmieniło
            if not applied_fixes:
                print(f"⚠️ No improvements could be applied")
                iteration_data['status'] = 'no_improvements'
                improvement_history.append(iteration_data)
                break
            
            iteration_data['improvements_applied'] = applied_fixes
            iteration_data['status'] = 'improved'
            improvement_history.append(iteration_data)
            
            current_process = improved_process
            iteration += 1
            
            print(f"🔧 Applied {len(applied_fixes)} improvements")
            for fix in applied_fixes:
                print(f"   ✓ {fix['description']}")
        
        # Finalna walidacja
        final_compliance = self.validator.validate_bpmn_compliance(current_process)
        
        return {
            'original_process': bpmn_json,
            'improved_process': current_process,
            'improvement_history': improvement_history,
            'final_compliance': asdict(final_compliance),
            'summary': self._generate_improvement_summary(improvement_history, final_compliance)
        }
    
    def _apply_improvements(self, bpmn_json: Dict, compliance_report: BPMNComplianceReport) -> Tuple[Dict, List[Dict]]:
        """
        Aplikuje poprawki do procesu BPMN
        
        Returns:
            (improved_process, applied_fixes)
        """
        import copy
        improved_process = copy.deepcopy(bpmn_json)
        applied_fixes = []
        
        # Sortuj issues według priorytetu
        prioritized_issues = self._prioritize_issues(compliance_report.issues)
        
        # Zastosuj automatyczne poprawki
        for issue in prioritized_issues:
            if issue.auto_fixable:
                fix_result = self._apply_auto_fix(improved_process, issue)
                if fix_result:
                    applied_fixes.append({
                        'type': 'auto_fix',
                        'rule_code': issue.rule_code,
                        'element_id': issue.element_id,
                        'description': f"Auto-fix: {issue.message}",
                        'details': fix_result
                    })
        
        # Zastosuj poprawki AI dla skomplikowanych problemów
        critical_manual_issues = [
            i for i in prioritized_issues 
            if not i.auto_fixable and i.severity == BPMNSeverity.CRITICAL
        ]
        
        if critical_manual_issues and self.ai_pipeline:
            ai_fixes = self._apply_ai_improvements(improved_process, critical_manual_issues)
            applied_fixes.extend(ai_fixes)
        
        return improved_process, applied_fixes
    
    def _prioritize_issues(self, issues: List[BPMNComplianceIssue]) -> List[BPMNComplianceIssue]:
        """Priorytetyzuje issues według ważności"""
        # Sortuj według: severity, auto_fixable, rule_code
        priority_order = {
            BPMNSeverity.CRITICAL: 0,
            BPMNSeverity.MAJOR: 1,
            BPMNSeverity.MINOR: 2,
            BPMNSeverity.WARNING: 3
        }
        
        return sorted(issues, key=lambda x: (
            priority_order.get(x.severity, 999),
            not x.auto_fixable,  # Auto-fixable najpierw
            x.rule_code
        ))
    
    def _apply_auto_fix(self, bpmn_json: Dict, issue: BPMNComplianceIssue) -> Dict[str, Any]:
        """Aplikuje automatyczną poprawkę"""
        try:
            if issue.rule_code == 'STRUCT_001':  # Missing Start Event
                return self._fix_missing_start_event(bpmn_json, issue.element_id)
            elif issue.rule_code == 'STRUCT_002':  # Missing End Event
                return self._fix_missing_end_event(bpmn_json, issue.element_id)
            elif issue.rule_code == 'SYNT_001':  # Duplicate IDs
                return self._fix_duplicate_ids(bpmn_json, issue.element_id)
            elif issue.rule_code == 'SYNT_002':  # Missing required attributes
                return self._fix_missing_attributes(bpmn_json, issue)
            elif issue.rule_code == 'SEM_004':  # Missing task types
                return self._fix_missing_task_types(bpmn_json, issue.element_id)
            elif issue.rule_code == 'STRUCT_003':  # Element connectivity
                return self._fix_element_connectivity(bpmn_json, issue.element_id)
            elif issue.rule_code == 'STRUCT_005':  # Unassigned elements
                return self._fix_unassigned_elements(bpmn_json, issue.element_id)
            elif issue.rule_code == 'STYLE_001':  # Naming conventions
                return self._fix_naming_conventions(bpmn_json, issue.element_id)
            else:
                return None
        except Exception as e:
            print(f"⚠️ Auto-fix failed for {issue.rule_code}: {e}")
            return None
    
    def _fix_missing_start_event(self, bpmn_json: Dict, target_pool: str = None) -> Dict[str, Any]:
        """Dodaje Start Event lub Intermediate Catch Event do procesu lub konkretnego Pool"""
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        message_flows = bpmn_json.get('messageFlows', [])
        
        # Jeśli target_pool jest podany, pracuj na konkretnym Pool
        if target_pool and target_pool != "process":
            # Sprawdź czy target_pool to participant
            target_participant = target_pool
            
            # Sprawdź czy już nie ma start event w tym Pool
            pool_elements = [e for e in elements if e.get('participant') == target_participant]
            start_events = [e for e in pool_elements if e.get('type') == 'startEvent']
            intermediate_catch = [e for e in pool_elements if e.get('type') in ['intermediateCatchEvent', 'intermediateMessageCatchEvent']]
            
            if start_events or intermediate_catch:
                return None
            
            # Sprawdź czy pool ma incoming Message Flow
            has_incoming_message_flow = any(
                mf.get('target_participant') == target_participant for mf in message_flows
            )
            
            # Dodaj odpowiedni typ event na podstawie Message Flow
            if has_incoming_message_flow:
                # Pool z incoming Message Flow -> Intermediate Catch Event  
                start_event = {
                    'id': f'intermediate_catch_event_{target_participant}_auto',
                    'name': 'Otrzymanie wiadomości',
                    'type': 'intermediateCatchEvent',
                    'participant': target_participant,
                    'eventDefinitions': [{'type': 'messageEventDefinition'}]
                }
                event_type = 'intermediate_catch_event'
            else:
                # Pool bez incoming Message Flow -> Start Event
                start_event = {
                    'id': f'start_event_{target_participant}_auto',
                    'name': 'Start',
                    'type': 'startEvent',
                    'participant': target_participant
                }
                event_type = 'start_event'
            
        else:
            # Globalne sprawdzenie (stara logika)
            # Sprawdź czy już nie ma start event
            start_events = [e for e in elements if e.get('type') == 'startEvent']
            if start_events:
                return None
            
            # Znajdź odpowiedniego uczestnika
            first_participant = participants[0]['id'] if participants else 'default_participant'
            
            # NOWA LOGIKA: Sprawdź czy pool ma incoming Message Flow
            has_incoming_message_flow = any(
                mf.get('target_participant') == first_participant for mf in message_flows
            )
            
            # Dodaj odpowiedni typ event na podstawie Message Flow
            if has_incoming_message_flow:
                # Pool z incoming Message Flow -> Intermediate Catch Event  
                start_event = {
                    'id': 'intermediate_catch_event_auto',
                    'name': 'Otrzymanie wiadomości',
                    'type': 'intermediateCatchEvent',
                    'participant': first_participant,
                    'eventDefinitions': [{'type': 'messageEventDefinition'}]
                }
                event_type = 'intermediate_catch_event'
            else:
                # Pool bez incoming Message Flow -> Start Event
                start_event = {
                    'id': 'start_event_auto',
                    'name': 'Start',
                    'type': 'startEvent',
                    'participant': first_participant
                }
                event_type = 'start_event'
        
        # Bezpieczne dodanie do elements
        if 'elements' not in bpmn_json:
            bpmn_json['elements'] = []
        bpmn_json['elements'].insert(0, start_event)
        
        # Podłącz do pierwszego elementu w danym Pool
        if target_pool and target_pool != "process":
            pool_activities = [e for e in elements if e.get('participant') == target_participant and 
                             e.get('type') in ['userTask', 'serviceTask', 'manualTask', 'scriptTask', 'receiveTask', 'sendTask']]
        else:
            pool_activities = elements
        
        if len(pool_activities) > 0:
            first_element = pool_activities[0]
            # Bezpieczne dodanie do flows
            if 'flows' not in bpmn_json:
                bpmn_json['flows'] = []
            flows = bpmn_json['flows']
            
            # Sprawdź czy flow już nie istnieje
            existing_flow = any(f.get('source') == start_event['id'] and f.get('target') == first_element.get('id') for f in flows)
            if not existing_flow:
                flows.insert(0, {
                    'id': f'flow_{event_type}_{target_participant}_auto' if target_pool and target_pool != "process" else f'flow_{event_type}_auto',
                    'source': start_event['id'],
                    'target': first_element.get('id'),
                    'type': 'sequence'
                })
        
        return {'action': f'added_{event_type}', 'element_id': start_event['id'], 'pool': target_pool}
    
    def _fix_element_connectivity(self, bpmn_json: Dict, element_id: str) -> Dict[str, Any]:
        """Naprawia problemy z połączeniami elementów"""
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Znajdź element do naprawienia
        target_element = next((e for e in elements if e.get('id') == element_id), None)
        if not target_element:
            return None
        
        element_type = target_element.get('type')
        participant = target_element.get('participant')
        fixes_applied = []
        
        # Bezpieczne dodanie do flows
        if 'flows' not in bpmn_json:
            bpmn_json['flows'] = []
        
        flows = bpmn_json['flows']
        
        # Fix 1: End Events bez przepływu wchodzącego
        if element_type == 'endEvent':
            has_incoming = any(f.get('target') == element_id for f in flows)
            if not has_incoming:
                # Znajdź ostatnią aktywność w tym samym Pool
                pool_elements = [e for e in elements if e.get('participant') == participant and e.get('id') != element_id]
                
                # Znajdź element bez przepływu wychodzącego w tym Pool
                outgoing_sources = {f.get('source') for f in flows}
                last_activity = None
                for elem in reversed(pool_elements):
                    if (elem.get('type') in ['userTask', 'serviceTask', 'manualTask', 'scriptTask'] and 
                        elem.get('id') not in outgoing_sources):
                        last_activity = elem
                        break
                
                if last_activity:
                    new_flow_id = f'flow_connect_{last_activity.get("id")}_{element_id}_auto'
                    # Sprawdź czy flow już nie istnieje
                    if not any(f.get('id') == new_flow_id for f in flows):
                        flows.append({
                            'id': new_flow_id,
                            'source': last_activity.get('id'),
                            'target': element_id,
                            'type': 'sequence'
                        })
                        fixes_applied.append(f'connected {last_activity.get("id")} to {element_id}')
        
        # Fix 2: Aktywności bez przepływu wychodzącego
        elif element_type in ['userTask', 'serviceTask', 'manualTask', 'scriptTask']:
            has_outgoing = any(f.get('source') == element_id for f in flows)
            if not has_outgoing:
                # Znajdź End Event w tym samym Pool
                pool_end_events = [e for e in elements if 
                                 e.get('participant') == participant and 
                                 e.get('type') == 'endEvent']
                
                if pool_end_events:
                    end_event = pool_end_events[0]  # Użyj pierwszego End Event
                    new_flow_id = f'flow_connect_{element_id}_{end_event.get("id")}_auto'
                    # Sprawdź czy flow już nie istnieje
                    if not any(f.get('id') == new_flow_id for f in flows):
                        flows.append({
                            'id': new_flow_id,
                            'source': element_id,
                            'target': end_event.get('id'),
                            'type': 'sequence'
                        })
                        fixes_applied.append(f'connected {element_id} to {end_event.get("id")}')
        
        # Fix 3: Aktywności bez przepływu wchodzącego
        if element_type in ['userTask', 'serviceTask', 'manualTask', 'scriptTask']:
            has_incoming = any(f.get('target') == element_id for f in flows)
            if not has_incoming:
                # Znajdź Start Event lub Intermediate Catch Event w tym samym Pool
                pool_start_events = [e for e in elements if 
                                   e.get('participant') == participant and 
                                   e.get('type') in ['startEvent', 'intermediateCatchEvent']]
                
                if pool_start_events:
                    start_event = pool_start_events[0]  # Użyj pierwszego Start Event
                    new_flow_id = f'flow_connect_{start_event.get("id")}_{element_id}_auto'
                    # Sprawdź czy flow już nie istnieje
                    if not any(f.get('id') == new_flow_id for f in flows):
                        flows.append({
                            'id': new_flow_id,
                            'source': start_event.get('id'),
                            'target': element_id,
                            'type': 'sequence'
                        })
                        fixes_applied.append(f'connected {start_event.get("id")} to {element_id}')
        
        if fixes_applied:
            return {'action': 'fixed_connectivity', 'element_id': element_id, 'fixes': fixes_applied}
        
        return None
    
    def _fix_missing_end_event(self, bpmn_json: Dict, target_pool: str = None) -> Dict[str, Any]:
        """Dodaje End Event do procesu lub konkretnego Pool"""
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        participants = bpmn_json.get('participants', [])
        
        # Jeśli target_pool jest podany, pracuj na konkretnym Pool
        if target_pool and target_pool != "process":
            target_participant = target_pool
            
            # Sprawdź czy już nie ma end event w tym Pool
            pool_elements = [e for e in elements if e.get('participant') == target_participant]
            end_events = [e for e in pool_elements if e.get('type') == 'endEvent']
            intermediate_throw = [e for e in pool_elements if e.get('type') in ['intermediateThrowEvent', 'intermediateMessageThrowEvent']]
            
            if end_events or intermediate_throw:
                return None
                
            # Znajdź ostatni element bez przepływu wychodzącego w tym Pool
            outgoing_sources = {f.get('source') for f in flows}
            pool_activities = [e for e in pool_elements if e.get('type') in 
                             ['userTask', 'serviceTask', 'manualTask', 'scriptTask', 'receiveTask', 'sendTask']]
            
            last_element = None
            for element in reversed(pool_activities):
                if element.get('id') not in outgoing_sources:
                    last_element = element
                    break
            
            if not last_element and pool_activities:
                last_element = pool_activities[-1]  # Weź ostatnią aktywność
                
            participant = target_participant
        else:
            # Globalne sprawdzenie (stara logika)
            # Sprawdź czy już nie ma end event
            end_events = [e for e in elements if e.get('type') == 'endEvent']
            if end_events:
                return None
            
            # Znajdź element bez przepływu wychodzącego
            outgoing_sources = {f.get('source') for f in flows}
            
            last_element = None
            for element in reversed(elements):
                if element.get('id') not in outgoing_sources:
                    last_element = element
                    break
            
            # Znajdź odpowiedniego uczestnika
            if last_element and last_element.get('participant'):
                participant = last_element['participant']
            elif elements and elements[-1].get('participant'):
                participant = elements[-1]['participant']
            elif participants:
                participant = participants[0]['id']
            else:
                participant = 'default_participant'
        
        # Dodaj End Event z unique ID
        end_event_id = f'end_event_{participant}_auto' if target_pool and target_pool != "process" else 'end_event_auto'
        end_event = {
            'id': end_event_id,
            'name': 'End',
            'type': 'endEvent',
            'participant': participant
        }
        
        # Bezpieczne dodanie do elements
        if 'elements' not in bpmn_json:
            bpmn_json['elements'] = []
        bpmn_json['elements'].append(end_event)
        
        # Podłącz ostatni element
        if last_element:
            # Bezpieczne dodanie do flows
            if 'flows' not in bpmn_json:
                bpmn_json['flows'] = []
            flows = bpmn_json['flows']
            
            # Sprawdź czy flow już nie istnieje
            existing_flow = any(f.get('source') == last_element.get('id') and f.get('target') == end_event_id for f in flows)
            if not existing_flow:
                flows.append({
                    'id': f'flow_end_{participant}_auto' if target_pool and target_pool != "process" else 'flow_end_auto',
                    'source': last_element.get('id'),
                    'target': end_event_id,
                    'type': 'sequence'
                })
        
        return {'action': 'added_end_event', 'element_id': end_event_id, 'pool': target_pool}
    
    def _fix_duplicate_ids(self, bpmn_json: Dict, duplicate_id: str) -> Dict[str, Any]:
        """Naprawia duplikowane ID"""
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Znajdź duplikaty i zmień drugie wystąpienie
        found_first = False
        fixed_elements = []
        
        for element in elements:
            if element.get('id') == duplicate_id:
                if found_first:
                    # To jest duplikat - zmień ID
                    new_id = f"{duplicate_id}_{len(fixed_elements) + 1}"
                    element['id'] = new_id
                    fixed_elements.append(new_id)
                    
                    # Zaktualizuj odwołania w flows
                    for flow in flows:
                        if flow.get('source') == duplicate_id:
                            flow['source'] = new_id
                        if flow.get('target') == duplicate_id:
                            flow['target'] = new_id
                else:
                    found_first = True
        
        return {'action': 'fixed_duplicate_ids', 'new_ids': fixed_elements}
    
    def _fix_missing_attributes(self, bpmn_json: Dict, issue: BPMNComplianceIssue) -> Dict[str, Any]:
        """Naprawia brakujące atrybuty"""
        elements = bpmn_json.get('elements', [])
        
        for element in elements:
            if element.get('id') == issue.element_id or not element.get('id'):
                # Dodaj brakujące ID
                if not element.get('id'):
                    element['id'] = f"element_{len(elements)}_auto"
                
                # Dodaj brakujący typ
                if not element.get('type'):
                    element['type'] = 'userTask'  # Domyślny typ
                
                return {'action': 'added_missing_attributes', 'element_id': element.get('id')}
        
        return None
    
    def _fix_missing_task_types(self, bpmn_json: Dict, element_id: str) -> Dict[str, Any]:
        """Dodaje brakujące task_type do aktywności"""
        elements = bpmn_json.get('elements', [])
        
        for element in elements:
            if element.get('id') == element_id:
                element_type = element.get('type', '')
                
                # Obsłuż różne typy zadań i ogólny 'task'
                if element_type in ['userTask', 'serviceTask', 'manualTask', 'scriptTask', 'receiveTask', 'sendTask', 'task']:
                    # Jeśli już ma task_type, nie zmieniaj
                    if element.get('task_type'):
                        return None
                    
                    # Ustaw task_type na podstawie typu elementu
                    if element_type == 'userTask' or element_type == 'manualTask':
                        element['task_type'] = 'user'
                    elif element_type == 'serviceTask' or element_type == 'scriptTask':
                        element['task_type'] = 'service'
                    elif element_type == 'sendTask':
                        element['task_type'] = 'send'
                    elif element_type == 'receiveTask':
                        element['task_type'] = 'receive'
                    elif element_type == 'task':
                        # Dla ogólnego 'task' spróbuj ustalić na podstawie nazwy
                        name = element.get('name', '').lower()
                        if any(word in name for word in ['użytkownik', 'klient', 'input', 'wprowadza', 'wybiera', 'manual', 'check', 'verify']):
                            element['task_type'] = 'user'
                            element['type'] = 'userTask'  # Zmień także typ elementu
                        else:
                            element['task_type'] = 'service'
                            element['type'] = 'serviceTask'  # Zmień także typ elementu
                    
                    return {'action': 'added_task_type', 'element_id': element_id, 'task_type': element['task_type']}
        
        return None
    
    def _fix_unassigned_elements(self, bpmn_json: Dict, element_id: str) -> Dict[str, Any]:
        """Przypisuje elementy do uczestników"""
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        
        if not participants:
            return None
        
        for element in elements:
            if element.get('id') == element_id and not element.get('participant'):
                # Przypisz do pierwszego uczestnika lub najbardziej odpowiedniego
                element_type = element.get('type', '')
                element_name = element.get('name', '').lower()
                
                # Logika przypisywania na podstawie typu/nazwy
                if 'system' in element_name or element.get('task_type') == 'service':
                    # Szukaj uczestnika typu 'system'
                    system_participant = next((p for p in participants if p.get('type') == 'system'), None)
                    element['participant'] = system_participant['id'] if system_participant else participants[0]['id']
                else:
                    # Przypisz do pierwszego ludzkiego uczestnika
                    human_participant = next((p for p in participants if p.get('type') == 'human'), None)
                    element['participant'] = human_participant['id'] if human_participant else participants[0]['id']
                
                return {'action': 'assigned_participant', 'participant': element['participant']}
        
        return None
    
    def _fix_naming_conventions(self, bpmn_json: Dict, element_id: str) -> Dict[str, Any]:
        """Naprawia konwencje nazewnictwa"""
        elements = bpmn_json.get('elements', [])
        
        for element in elements:
            if element.get('id') == element_id:
                old_id = element['id']
                # Konwertuj do snake_case
                new_id = ''.join(['_' + c.lower() if c.isupper() else c for c in old_id]).lstrip('_')
                # Usuń nieprawidłowe znaki
                new_id = ''.join([c if c.isalnum() or c == '_' else '_' for c in new_id])
                
                if new_id != old_id:
                    element['id'] = new_id
                    
                    # Zaktualizuj odwołania w flows
                    flows = bpmn_json.get('flows', [])
                    for flow in flows:
                        if flow.get('source') == old_id:
                            flow['source'] = new_id
                        if flow.get('target') == old_id:
                            flow['target'] = new_id
                    
                    return {'action': 'fixed_naming_convention', 'old_id': old_id, 'new_id': new_id}
        
        return None
    
    def _apply_ai_improvements(self, bpmn_json: Dict, issues: List[BPMNComplianceIssue]) -> List[Dict]:
        """Aplikuje poprawki AI dla skomplikowanych problemów"""
        ai_fixes = []
        
        if not self.ai_pipeline:
            return ai_fixes
        
        # Generuj prompt dla AI z opisem problemów
        improvement_prompt = self._generate_ai_improvement_prompt(bpmn_json, issues)
        
        try:
            # Wywołaj AI do poprawy procesu
            print("🤖 Requesting AI improvements...")
            result = self.ai_pipeline.run_complete_pipeline(improvement_prompt, "Improvement Process")
            
            if result.get('success') and result.get('bpmn_json'):
                # Merge poprawek z AI
                ai_improved = result['bpmn_json']
                merge_result = self._merge_ai_improvements(bpmn_json, ai_improved, issues)
                
                if merge_result:
                    ai_fixes.append({
                        'type': 'ai_improvement',
                        'rule_codes': [i.rule_code for i in issues],
                        'description': f"AI improved {len(issues)} complex issues",
                        'details': merge_result
                    })
        
        except Exception as e:
            print(f"⚠️ AI improvement failed: {e}")
        
        return ai_fixes
    
    def _generate_ai_improvement_prompt(self, bpmn_json: Dict, issues: List[BPMNComplianceIssue]) -> str:
        """Generuje prompt dla AI do poprawy procesu"""
        process_name = bpmn_json.get('process_name', 'Unknown Process')
        
        issues_description = "\n".join([
            f"- {issue.severity.value.upper()}: {issue.message} (Element: {issue.element_id})"
            for issue in issues[:5]  # Tylko pierwsze 5 najważniejszych
        ])
        
        prompt = f"""
Popraw proces BPMN '{process_name}' aby spełniał standardy zgodności BPMN 2.0.

AKTUALNY PROCES:
{json.dumps(bpmn_json, indent=2, ensure_ascii=False)}

PROBLEMY DO NAPRAWIENIA:
{issues_description}

WYMAGANIA POPRAWEK:
1. Zachowaj oryginalną logikę biznesową procesu
2. Napraw wszystkie problemy strukturalne i semantyczne
3. Upewnij się że każdy element ma prawidłowe połączenia
4. Dodaj brakujące elementy (Start/End Events, nazwy, atrybuty)
5. Zachowaj istniejących uczestników i ich role

Zwróć poprawiony proces w tym samym formacie JSON.
"""
        
        return prompt
    
    def _merge_ai_improvements(self, original: Dict, ai_improved: Dict, issues: List[BPMNComplianceIssue]) -> Dict:
        """Inteligentnie merguje poprawki AI z oryginalnym procesem"""
        # Prosta implementacja - w przyszłości można dodać bardziej zaawansowane mergowanie
        # Na razie zastępujemy tylko elementy które miały problemy
        
        problem_elements = {issue.element_id for issue in issues}
        
        merged = original.copy()
        
        # Merguj elementy
        if 'elements' in ai_improved:
            original_elements = {e.get('id'): e for e in original.get('elements', [])}
            ai_elements = {e.get('id'): e for e in ai_improved.get('elements', [])}
            
            for element_id in problem_elements:
                if element_id in ai_elements:
                    # Zastąp problematyczny element wersją AI
                    for i, elem in enumerate(merged['elements']):
                        if elem.get('id') == element_id:
                            merged['elements'][i] = ai_elements[element_id]
                            break
        
        return {'merged_elements': len(problem_elements)}
    
    def _generate_improvement_summary(self, history: List[Dict], final_compliance: BPMNComplianceReport) -> Dict[str, Any]:
        """Generuje podsumowanie procesu poprawy"""
        total_fixes = sum(len(iter_data.get('improvements_applied', [])) for iter_data in history)
        
        initial_score = history[0]['compliance_report']['overall_score'] if history else 0
        final_score = final_compliance.overall_score
        improvement = final_score - initial_score
        
        return {
            'iterations_completed': len(history),
            'total_fixes_applied': total_fixes,
            'initial_compliance_score': initial_score,
            'final_compliance_score': final_score,
            'improvement': improvement,
            'final_compliance_level': final_compliance.compliance_level,
            'remaining_issues': len(final_compliance.issues),
            'auto_fixes_vs_manual': {
                'auto_fixes': len([f for h in history for f in h.get('improvements_applied', []) if f['type'] == 'auto_fix']),
                'ai_improvements': len([f for h in history for f in h.get('improvements_applied', []) if f['type'] == 'ai_improvement'])
            }
        }

def test_compliance_validator():
    """Test funkcji walidacji zgodności BPMN"""
    print("🧪 Testing BPMN Compliance Validator...")
    
    # Test proces z problemami
    test_process = {
        "process_name": "Test Process",
        "description": "Test process for validation",
        "participants": [
            {"id": "user", "name": "User", "type": "human"},
            {"id": "system", "name": "System", "type": "system"}
        ],
        "elements": [
            # Brakuje Start Event
            {"id": "task1", "name": "Task 1", "type": "userTask", "participant": "user"},
            {"id": "task2", "name": "", "type": "serviceTask", "participant": "system"}  # Brak nazwy
            # Brakuje End Event
        ],
        "flows": [
            {"id": "flow1", "source": "task1", "target": "task2"}
        ]
    }
    
    validator = BPMNComplianceValidator()
    report = validator.validate_bpmn_compliance(test_process)
    
    print(f"Compliance Score: {report.overall_score}")
    print(f"🏷️  Compliance Level: {report.compliance_level}")
    print(f"⚠️  Issues Found: {len(report.issues)}")
    
    for issue in report.issues[:5]:  # Pokaż pierwsze 5
        print(f"   {issue.severity.value}: {issue.message} ({issue.element_id})")
    
    # Test silnika poprawek
    print(f"\n🔧 Testing Improvement Engine...")
    engine = BPMNImprovementEngine()
    improvement_result = engine.improve_bpmn_process(test_process, target_score=90)
    
    print(f"Improvement Summary:")
    summary = improvement_result['summary']
    print(f"   Initial Score: {summary['initial_compliance_score']}")
    print(f"   Final Score: {summary['final_compliance_score']}")
    print(f"   Improvement: +{summary['improvement']:.1f}")
    print(f"   Fixes Applied: {summary['total_fixes_applied']}")
    print(f"   Iterations: {summary['iterations_completed']}")

if __name__ == "__main__":
    test_compliance_validator()