"""
Template-Based Quick Fixes Engine
Gotowe wzorce naprawek dla typowych problemów BPMN

Autor: AI Assistant  
Data: 2025-11-29
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import copy
import uuid

@dataclass
class FixTemplate:
    """Szablon szybkiej naprawki"""
    id: str
    name: str
    description: str
    applicable_rules: List[str]  # Reguły, których dotyczy
    fix_function: Callable[[Dict, Dict], bool]
    confidence: float  # 0-1, pewność naprawki
    risk_level: str  # 'safe', 'moderate', 'risky'
    prerequisites: List[str]  # Warunki wstępne

class TemplateQuickFixes:
    """Silnik szybkich naprawek opartych na szablonach"""
    
    def __init__(self):
        self.templates = []
        self.success_rate = {}  # Tracking success rate per template
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Inicjalizuje bibliotekę szablonów naprawek"""
        
        # Template 1: Add missing Start Event
        self.templates.append(FixTemplate(
            id='add_start_event',
            name='Add Missing Start Event',
            description='Dodaje brakujący Start Event do Pool',
            applicable_rules=['STRUCT_001'],
            fix_function=self._fix_add_start_event,
            confidence=0.95,
            risk_level='safe',
            prerequisites=['has_activities']
        ))
        
        # Template 2: Add missing End Event
        self.templates.append(FixTemplate(
            id='add_end_event',
            name='Add Missing End Event', 
            description='Dodaje brakujący End Event do Pool',
            applicable_rules=['STRUCT_001'],
            fix_function=self._fix_add_end_event,
            confidence=0.95,
            risk_level='safe',
            prerequisites=['has_activities']
        ))
        
        # Template 3: Fix Gateway outgoing flows
        self.templates.append(FixTemplate(
            id='fix_gateway_flows',
            name='Fix Gateway Outgoing Flows',
            description='Dodaje brakujące przepływy wyjściowe dla Gateway',
            applicable_rules=['STRUCT_004'],
            fix_function=self._fix_gateway_outgoing_flows,
            confidence=0.85,
            risk_level='moderate', 
            prerequisites=['gateway_exists']
        ))
        
        # Template 4: Connect orphaned elements
        self.templates.append(FixTemplate(
            id='connect_orphans',
            name='Connect Orphaned Elements',
            description='Łączy elementy bez połączeń',
            applicable_rules=['STRUCT_003'],
            fix_function=self._fix_connect_orphans,
            confidence=0.75,
            risk_level='moderate',
            prerequisites=['has_orphaned_elements']
        ))
        
        # Template 5: Fix Message Flow types
        self.templates.append(FixTemplate(
            id='fix_message_flow_types',
            name='Fix Message Flow Event Types',
            description='Naprawia typy Event dla Message Flow',
            applicable_rules=['STRUCT_009', 'STRUCT_010'],
            fix_function=self._fix_message_flow_event_types,
            confidence=0.90,
            risk_level='safe',
            prerequisites=['has_message_flows']
        ))
        
        # Template 6: Improve element naming
        self.templates.append(FixTemplate(
            id='improve_naming',
            name='Improve Element Naming',
            description='Poprawia nazewnictwo elementów',
            applicable_rules=['SEM_001', 'STYLE_001'],
            fix_function=self._fix_element_naming,
            confidence=0.80,
            risk_level='safe',
            prerequisites=['has_unnamed_elements']
        ))
        
        # Template 7: Add default flows for gateways
        self.templates.append(FixTemplate(
            id='add_default_flows',
            name='Add Default Gateway Flows',
            description='Dodaje domyślne przepływy dla Gateway',
            applicable_rules=['SEM_002'],
            fix_function=self._fix_add_default_flows,
            confidence=0.85,
            risk_level='moderate',
            prerequisites=['has_unconditioned_gateways']
        ))
    
    def find_applicable_templates(self, bpmn_json: Dict, issues: List[Dict]) -> List[FixTemplate]:
        """Znajduje odpowiednie szablony dla problemów"""
        applicable = []
        issue_rules = {issue.get('rule_code', '') for issue in issues}
        
        for template in self.templates:
            # Check if template applies to any of the issues
            if any(rule in issue_rules for rule in template.applicable_rules):
                # Check prerequisites
                if self._check_prerequisites(bpmn_json, template.prerequisites):
                    applicable.append(template)
        
        # Sort by confidence descending
        return sorted(applicable, key=lambda t: t.confidence, reverse=True)
    
    def apply_template_fixes(self, bpmn_json: Dict, templates: List[FixTemplate]) -> Dict[str, Any]:
        """Aplikuje szablonowe naprawki"""
        fixed_process = copy.deepcopy(bpmn_json)
        applied_fixes = []
        failed_fixes = []
        
        for template in templates:
            try:
                # Prepare issue context for this template
                issue_context = self._prepare_issue_context(fixed_process, template)
                
                # Apply fix
                success = template.fix_function(fixed_process, issue_context)
                
                if success:
                    applied_fixes.append({
                        'template_id': template.id,
                        'template_name': template.name,
                        'description': template.description,
                        'confidence': template.confidence,
                        'risk_level': template.risk_level
                    })
                    self._update_success_rate(template.id, True)
                else:
                    failed_fixes.append({
                        'template_id': template.id,
                        'reason': 'Function returned False'
                    })
                    self._update_success_rate(template.id, False)
                    
            except Exception as e:
                failed_fixes.append({
                    'template_id': template.id,
                    'reason': f'Exception: {str(e)}'
                })
                self._update_success_rate(template.id, False)
        
        return {
            'fixed_process': fixed_process,
            'applied_fixes': applied_fixes,
            'failed_fixes': failed_fixes,
            'success_rate': len(applied_fixes) / max(1, len(templates))
        }
    
    def _check_prerequisites(self, bpmn_json: Dict, prerequisites: List[str]) -> bool:
        """Sprawdza czy spełnione są warunki wstępne"""
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        for prereq in prerequisites:
            if prereq == 'has_activities':
                activities = [e for e in elements if e.get('type') in ['userTask', 'serviceTask', 'manualTask']]
                if not activities:
                    return False
            
            elif prereq == 'gateway_exists':
                gateways = [e for e in elements if 'gateway' in e.get('type', '').lower()]
                if not gateways:
                    return False
            
            elif prereq == 'has_orphaned_elements':
                # Check for elements not connected by flows
                connected_elements = set()
                for flow in flows:
                    connected_elements.add(flow.get('source', ''))
                    connected_elements.add(flow.get('target', ''))
                
                all_element_ids = {e.get('id', '') for e in elements}
                orphaned = all_element_ids - connected_elements
                if not orphaned:
                    return False
            
            elif prereq == 'has_message_flows':
                message_flows = [f for f in flows if f.get('type') == 'message']
                if not message_flows:
                    return False
            
            elif prereq == 'has_unnamed_elements':
                unnamed = [e for e in elements if not e.get('name') or len(e.get('name', '').strip()) < 3]
                if not unnamed:
                    return False
                    
            elif prereq == 'has_unconditioned_gateways':
                gateways = [e for e in elements if e.get('type') == 'exclusiveGateway']
                unconditioned = [g for g in gateways if not self._has_conditions(g, flows)]
                if not unconditioned:
                    return False
        
        return True
    
    def _prepare_issue_context(self, bpmn_json: Dict, template: FixTemplate) -> Dict[str, Any]:
        """Przygotowuje kontekst problemów dla szablonu"""
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        flows = bpmn_json.get('flows', [])
        
        return {
            'elements': elements,
            'participants': participants,
            'flows': flows,
            'template': template
        }
    
    # === TEMPLATE FIX FUNCTIONS ===
    
    def _fix_add_start_event(self, bpmn_json: Dict, context: Dict) -> bool:
        """Dodaje brakujący Start Event"""
        elements = context['elements']
        participants = context['participants']
        flows = context['flows']
        
        for participant in participants:
            participant_id = participant.get('id', '')
            
            # Check if participant has activities but no start event
            pool_elements = [e for e in elements if e.get('participant') == participant_id]
            activities = [e for e in pool_elements if e.get('type') in ['userTask', 'serviceTask', 'manualTask']]
            start_events = [e for e in pool_elements if e.get('type') == 'startEvent']
            
            if activities and not start_events:
                # Add start event
                start_event_id = f'startEvent_{participant_id}_{uuid.uuid4().hex[:8]}'
                start_event = {
                    'id': start_event_id,
                    'name': f'Start {participant.get("name", participant_id)}',
                    'type': 'startEvent',
                    'participant': participant_id
                }
                elements.append(start_event)
                
                # Connect to first activity
                if activities:
                    first_activity = activities[0]
                    flow_id = f'flow_{start_event_id}_{first_activity["id"]}'
                    sequence_flow = {
                        'id': flow_id,
                        'source': start_event_id,
                        'target': first_activity['id'],
                        'type': 'sequence'
                    }
                    flows.append(sequence_flow)
        
        return True
    
    def _fix_add_end_event(self, bpmn_json: Dict, context: Dict) -> bool:
        """Dodaje brakujący End Event"""
        elements = context['elements']
        participants = context['participants']
        flows = context['flows']
        
        for participant in participants:
            participant_id = participant.get('id', '')
            
            # Check if participant has activities but no end event
            pool_elements = [e for e in elements if e.get('participant') == participant_id]
            activities = [e for e in pool_elements if e.get('type') in ['userTask', 'serviceTask', 'manualTask']]
            end_events = [e for e in pool_elements if e.get('type') == 'endEvent']
            
            if activities and not end_events:
                # Add end event
                end_event_id = f'endEvent_{participant_id}_{uuid.uuid4().hex[:8]}'
                end_event = {
                    'id': end_event_id,
                    'name': f'End {participant.get("name", participant_id)}',
                    'type': 'endEvent',
                    'participant': participant_id
                }
                elements.append(end_event)
                
                # Find activities without outgoing flows (potential last activities)
                outgoing_sources = {f.get('source', '') for f in flows if f.get('type') == 'sequence'}
                last_activities = [a for a in activities if a.get('id', '') not in outgoing_sources]
                
                # Connect last activities to end event
                for activity in last_activities:
                    flow_id = f'flow_{activity["id"]}_{end_event_id}'
                    sequence_flow = {
                        'id': flow_id,
                        'source': activity['id'],
                        'target': end_event_id,
                        'type': 'sequence'
                    }
                    flows.append(sequence_flow)
        
        return True
    
    def _fix_gateway_outgoing_flows(self, bpmn_json: Dict, context: Dict) -> bool:
        """Naprawia Gateway z niewystarczającą liczbą przepływów wyjściowych"""
        elements = context['elements']
        flows = context['flows']
        
        gateways = [e for e in elements if e.get('type') == 'exclusiveGateway']
        
        for gateway in gateways:
            gateway_id = gateway.get('id', '')
            participant_id = gateway.get('participant', '')
            
            # Check outgoing flows
            outgoing = [f for f in flows if f.get('source') == gateway_id and f.get('type') == 'sequence']
            
            if len(outgoing) < 2:
                # Find or create end event for default path
                pool_elements = [e for e in elements if e.get('participant') == participant_id]
                end_events = [e for e in pool_elements if e.get('type') == 'endEvent']
                
                if not end_events:
                    # Create end event
                    end_event_id = f'endEvent_default_{uuid.uuid4().hex[:8]}'
                    end_event = {
                        'id': end_event_id,
                        'name': 'Default End',
                        'type': 'endEvent',
                        'participant': participant_id
                    }
                    elements.append(end_event)
                    target_id = end_event_id
                else:
                    target_id = end_events[0]['id']
                
                # Add default flow
                default_flow_id = f'flow_{gateway_id}_default_{uuid.uuid4().hex[:8]}'
                default_flow = {
                    'id': default_flow_id,
                    'source': gateway_id,
                    'target': target_id,
                    'name': 'default',
                    'condition': 'default',
                    'type': 'sequence'
                }
                flows.append(default_flow)
        
        return True
    
    def _fix_connect_orphans(self, bpmn_json: Dict, context: Dict) -> bool:
        """Łączy elementy bez połączeń"""
        elements = context['elements']
        flows = context['flows']
        
        # Find connected elements
        connected = set()
        for flow in flows:
            if flow.get('type') == 'sequence':
                connected.add(flow.get('source', ''))
                connected.add(flow.get('target', ''))
        
        # Find orphaned elements (excluding start/end events)
        all_elements = {e.get('id', ''): e for e in elements}
        orphaned_ids = set(all_elements.keys()) - connected
        
        orphaned_activities = [
            all_elements[oid] for oid in orphaned_ids 
            if all_elements[oid].get('type') in ['userTask', 'serviceTask', 'manualTask']
        ]
        
        # Connect orphaned activities to the process flow
        for activity in orphaned_activities:
            participant_id = activity.get('participant', '')
            
            # Find start event in the same pool
            start_events = [
                e for e in elements 
                if e.get('type') == 'startEvent' and e.get('participant') == participant_id
            ]
            
            if start_events:
                # Connect start event to activity
                flow_id = f'flow_connect_{start_events[0]["id"]}_{activity["id"]}'
                sequence_flow = {
                    'id': flow_id,
                    'source': start_events[0]['id'],
                    'target': activity['id'],
                    'type': 'sequence'
                }
                flows.append(sequence_flow)
        
        return True
    
    def _fix_message_flow_event_types(self, bpmn_json: Dict, context: Dict) -> bool:
        """Naprawia typy Event dla Message Flow"""
        elements = context['elements']
        flows = context['flows']
        
        message_flows = [f for f in flows if f.get('type') == 'message']
        
        for mf in message_flows:
            source_id = mf.get('source', '')
            target_id = mf.get('target', '')
            
            # Find source and target elements
            source_element = next((e for e in elements if e.get('id') == source_id), None)
            target_element = next((e for e in elements if e.get('id') == target_id), None)
            
            # Fix end events with outgoing message flows
            if source_element and source_element.get('type') == 'endEvent':
                # Should be message end event
                source_element['name'] = f"Message {source_element.get('name', 'End')}"
                source_element['eventDefinitionType'] = 'message'
            
            # Fix intermediate events with message flows
            if target_element and 'intermediate' in target_element.get('type', '').lower():
                target_element['name'] = f"Message {target_element.get('name', 'Event')}"
                target_element['eventDefinitionType'] = 'message'
        
        return True
    
    def _fix_element_naming(self, bpmn_json: Dict, context: Dict) -> bool:
        """Poprawia nazewnictwo elementów"""
        elements = context['elements']
        
        naming_rules = {
            'startEvent': 'Start Process',
            'endEvent': 'End Process', 
            'userTask': 'User Task',
            'serviceTask': 'Service Task',
            'exclusiveGateway': 'Decision Gateway',
            'parallelGateway': 'Parallel Gateway'
        }
        
        for element in elements:
            element_type = element.get('type', '')
            current_name = element.get('name', '')
            
            # Fix empty or very short names
            if not current_name or len(current_name.strip()) < 3:
                default_name = naming_rules.get(element_type, f'{element_type} Element')
                element['name'] = default_name
            
            # Fix overly long names
            elif len(current_name) > 50:
                element['name'] = current_name[:47] + '...'
        
        return True
    
    def _fix_add_default_flows(self, bpmn_json: Dict, context: Dict) -> bool:
        """Dodaje domyślne przepływy dla Gateway"""
        elements = context['elements']
        flows = context['flows']
        
        exclusive_gateways = [e for e in elements if e.get('type') == 'exclusiveGateway']
        
        for gateway in exclusive_gateways:
            gateway_id = gateway.get('id', '')
            
            # Check if gateway has conditions on outgoing flows
            outgoing_flows = [f for f in flows if f.get('source') == gateway_id]
            
            # Add conditions if missing
            for i, flow in enumerate(outgoing_flows):
                if not flow.get('condition'):
                    if i == 0:
                        flow['condition'] = 'yes'
                        flow['name'] = 'Yes'
                    elif i == 1:
                        flow['condition'] = 'no'
                        flow['name'] = 'No'
                    else:
                        flow['condition'] = f'option_{i+1}'
                        flow['name'] = f'Option {i+1}'
        
        return True
    
    def _has_conditions(self, gateway: Dict, flows: List[Dict]) -> bool:
        """Sprawdza czy Gateway ma warunki na przepływach"""
        gateway_id = gateway.get('id', '')
        outgoing_flows = [f for f in flows if f.get('source') == gateway_id]
        
        return any(f.get('condition') for f in outgoing_flows)
    
    def _update_success_rate(self, template_id: str, success: bool) -> None:
        """Aktualizuje statystyki sukcesu szablonu"""
        if template_id not in self.success_rate:
            self.success_rate[template_id] = {'success': 0, 'total': 0}
        
        self.success_rate[template_id]['total'] += 1
        if success:
            self.success_rate[template_id]['success'] += 1
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki szablonów"""
        stats = {}
        
        for template in self.templates:
            template_id = template.id
            if template_id in self.success_rate:
                sr = self.success_rate[template_id]
                success_percentage = (sr['success'] / sr['total']) * 100 if sr['total'] > 0 else 0
            else:
                success_percentage = 0
                sr = {'success': 0, 'total': 0}
            
            stats[template_id] = {
                'name': template.name,
                'confidence': template.confidence,
                'risk_level': template.risk_level,
                'success_rate': success_percentage,
                'times_used': sr['total']
            }
        
        return stats
