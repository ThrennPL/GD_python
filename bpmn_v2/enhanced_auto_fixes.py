"""
Enhanced Auto-Fix Engine for Critical BPMN Issues
Dodatkowe naprawki dla krytycznych problemów BPMN

Autor: AI Assistant
Data: 2025-11-29
"""

import copy
from typing import Dict, List, Any

def fix_end_event_incoming_flows(process: Dict) -> bool:
    """Naprawia End Events bez przepływów wchodzących"""
    try:
        elements = process.get('elements', [])
        flows = process.get('flows', [])
        
        changes_made = False
        
        for element in elements:
            if element.get('type') == 'endEvent':
                element_id = element.get('id')
                participant = element.get('participant')
                
                # Sprawdź czy ma incoming flow
                incoming = [f for f in flows if f.get('target') == element_id]
                
                if not incoming:
                    print(f"   🔧 Fixing End Event {element_id} without incoming flow")
                    
                    # Znajdź elementy w tym Pool
                    pool_elements = [e for e in elements if e.get('participant') == participant]
                    
                    # Strategia 1: Połącz z aktywnością bez outgoing
                    activities = [e for e in pool_elements 
                                if e.get('type') in ['userTask', 'serviceTask', 'manualTask']
                                and e.get('id') != element_id]
                    
                    for activity in activities:
                        outgoing = [f for f in flows if f.get('source') == activity.get('id') and f.get('type') == 'sequence']
                        if not outgoing:
                            flow_id = f"flow_{activity['id']}_{element_id}_autofix"
                            new_flow = {
                                'id': flow_id,
                                'source': activity['id'],
                                'target': element_id,
                                'type': 'sequence',
                                'name': 'auto-added'
                            }
                            flows.append(new_flow)
                            changes_made = True
                            print(f"     ✓ Connected {activity['id']} → {element_id}")
                            # Sprawdź czy faktycznie dodano
                            verify_incoming = [f for f in flows if f.get('target') == element_id]
                            print(f"     📊 End Event {element_id} now has {len(verify_incoming)} incoming flows")
                            break
                    
                    # Sprawdź czy naprawiono
                    current_incoming = [f for f in flows if f.get('target') == element_id]
                    if current_incoming:
                        print(f"     ✅ End Event {element_id} now connected")
                        continue
                        
                    # Strategia 2: Znajdź gateway i połącz
                    gateways = [e for e in pool_elements if 'gateway' in e.get('type', '').lower()]
                    for gateway in gateways:
                        # Sprawdź czy gateway już nie ma outgoing do tego End Event
                        existing_connection = [f for f in flows if f.get('source') == gateway.get('id') and f.get('target') == element_id]
                        if not existing_connection:
                            flow_id = f"flow_{gateway['id']}_{element_id}_autofix"
                            new_flow = {
                                'id': flow_id,
                                'source': gateway['id'],
                                'target': element_id,
                                'type': 'sequence',
                                'name': 'default',
                                'condition': 'default'
                            }
                            flows.append(new_flow)
                            changes_made = True
                            print(f"     ✓ Connected gateway {gateway['id']} → {element_id}")
                            # Verify
                            verify_incoming = [f for f in flows if f.get('target') == element_id]
                            print(f"     📊 End Event {element_id} now has {len(verify_incoming)} incoming flows")
                            break
                    
                    # Final check strategy 3: Connect to previous elements
                    final_incoming = [f for f in flows if f.get('target') == element_id]
                    if not final_incoming:
                        print(f"     ⚠️ Still no incoming flow for {element_id}, trying fallback")
                        
                        # Znajdź dowolny element w pool i połącz
                        other_elements = [e for e in pool_elements 
                                        if e.get('id') != element_id 
                                        and e.get('type') not in ['endEvent']]
                        
                        if other_elements:
                            fallback_element = other_elements[0]
                            flow_id = f"flow_{fallback_element['id']}_{element_id}_fallback"
                            fallback_flow = {
                                'id': flow_id,
                                'source': fallback_element['id'],
                                'target': element_id,
                                'type': 'sequence',
                                'name': 'fallback'
                            }
                            flows.append(fallback_flow)
                            changes_made = True
                            print(f"     ✓ Fallback: Connected {fallback_element['id']} → {element_id}")
                        
        return changes_made
        
    except Exception as e:
        print(f"❌ Error fixing end event incoming flows: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_gateway_outgoing_flows(process: Dict) -> bool:
    """Naprawia Gateway z niewystarczającą liczbą przepływów wyjściowych"""
    try:
        elements = process.get('elements', [])
        flows = process.get('flows', [])
        
        changes_made = False
        
        for element in elements:
            if element.get('type') == 'exclusiveGateway':
                gateway_id = element.get('id')
                participant = element.get('participant')
                
                # Sprawdź outgoing flows
                outgoing = [f for f in flows if f.get('source') == gateway_id and f.get('type') == 'sequence']
                
                if len(outgoing) < 2:
                    # Znajdź End Event w tym Pool
                    pool_elements = [e for e in elements if e.get('participant') == participant]
                    end_events = [e for e in pool_elements if e.get('type') == 'endEvent']
                    
                    if end_events:
                        end_event = end_events[0]
                        
                        # Sprawdź czy End Event nie ma już incoming flow z tego gateway
                        existing = [f for f in flows if f.get('source') == gateway_id and f.get('target') == end_event.get('id')]
                        
                        if not existing:
                            # Dodaj default flow do End Event
                            flow_id = f"flow_{gateway_id}_{end_event['id']}_default"
                            default_flow = {
                                'id': flow_id,
                                'source': gateway_id,
                                'target': end_event['id'],
                                'type': 'sequence',
                                'name': 'default',
                                'condition': 'default'
                            }
                            flows.append(default_flow)
                            changes_made = True
                            print(f"   ✓ Added default flow: {gateway_id} → {end_event['id']}")
                    
                    # Jeśli nadal mało outgoing flows, dodaj alternatywną ścieżkę
                    outgoing_after = [f for f in flows if f.get('source') == gateway_id and f.get('type') == 'sequence']
                    if len(outgoing_after) < 2:
                        # Utwórz dodatkową aktywność
                        alt_task_id = f"task_alt_{gateway_id}_autofix"
                        alt_task = {
                            'id': alt_task_id,
                            'name': 'Alternative Path',
                            'type': 'userTask',
                            'participant': participant
                        }
                        elements.append(alt_task)
                        
                        # Dodaj flow do alternatywnej aktywności
                        alt_flow_id = f"flow_{gateway_id}_{alt_task_id}_alt"
                        alt_flow = {
                            'id': alt_flow_id,
                            'source': gateway_id,
                            'target': alt_task_id,
                            'type': 'sequence',
                            'name': 'alternative',
                            'condition': 'else'
                        }
                        flows.append(alt_flow)
                        
                        # Połącz alternatywną aktywność z End Event
                        if end_events:
                            final_flow_id = f"flow_{alt_task_id}_{end_events[0]['id']}_final"
                            final_flow = {
                                'id': final_flow_id,
                                'source': alt_task_id,
                                'target': end_events[0]['id'],
                                'type': 'sequence'
                            }
                            flows.append(final_flow)
                        
                        changes_made = True
                        print(f"   ✓ Added alternative path: {gateway_id} → {alt_task_id}")
                        
        return changes_made
        
    except Exception as e:
        print(f"❌ Error fixing gateway outgoing flows: {e}")
        return False

def fix_missing_start_events(process: Dict) -> bool:
    """Naprawia brakujące Start Events w Pool"""
    try:
        elements = process.get('elements', [])
        flows = process.get('flows', [])
        participants = process.get('participants', [])
        
        changes_made = False
        
        for participant in participants:
            pool_id = participant.get('id')
            pool_elements = [e for e in elements if e.get('participant') == pool_id]
            
            # Sprawdź czy Pool ma activities ale nie ma Start Event
            activities = [e for e in pool_elements if e.get('type') in ['userTask', 'serviceTask', 'manualTask']]
            start_events = [e for e in pool_elements if e.get('type') == 'startEvent']
            
            if activities and not start_events:
                # Dodaj Start Event
                start_event_id = f"start_{pool_id}_autofix"
                start_event = {
                    'id': start_event_id,
                    'name': f"Start {participant.get('name', pool_id)}",
                    'type': 'startEvent',
                    'participant': pool_id
                }
                elements.append(start_event)
                
                # Połącz z pierwszą aktywnością
                first_activity = activities[0]
                flow_id = f"flow_{start_event_id}_{first_activity['id']}_autofix"
                start_flow = {
                    'id': flow_id,
                    'source': start_event_id,
                    'target': first_activity['id'],
                    'type': 'sequence'
                }
                flows.append(start_flow)
                
                changes_made = True
                print(f"   ✓ Added Start Event to {participant.get('name', pool_id)}")
                
        return changes_made
        
    except Exception as e:
        print(f"❌ Error fixing missing start events: {e}")
        return False

def apply_enhanced_auto_fixes(process: Dict) -> int:
    """Aplikuje zaawansowane auto-fixy"""
    fixes_applied = 0
    
    print("🔧 Applying enhanced auto-fixes...")
    
    if fix_missing_start_events(process):
        fixes_applied += 1
        print("   ✅ Fixed missing Start Events")
    
    if fix_end_event_incoming_flows(process):
        fixes_applied += 1
        print("   ✅ Fixed End Event incoming flows")
    
    if fix_gateway_outgoing_flows(process):
        fixes_applied += 1
        print("   ✅ Fixed Gateway outgoing flows")
    
    return fixes_applied