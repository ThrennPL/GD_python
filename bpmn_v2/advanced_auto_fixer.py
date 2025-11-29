"""
Advanced BPMN Auto-Fixer
Zaawansowany system automatycznych napraw BPMN oparty na sukcessie ręcznych poprawek

Autor: AI Assistant
Data: 2025-11-27

Implementuje logikę napraw podobną do tych które ręcznie zastosowaliśmy
w pliku Generated_Process_improved_20251127_181922.bpmn
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
import uuid
from datetime import datetime

@dataclass
class BPMNAutoFix:
    """Reprezentuje pojedynczą automatyczną naprawę"""
    fix_id: str
    element_id: str
    fix_type: str
    description: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    success: bool
    error_message: str = None

class AdvancedBPMNAutoFixer:
    """
    Zaawansowany system automatycznych napraw BPMN
    Implementuje strategie napraw podobne do ręcznych poprawek
    """
    
    def __init__(self):
        self.fix_history: List[BPMNAutoFix] = []
        self.namespace = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
        
    def apply_comprehensive_auto_fixes(self, bpmn_xml: str) -> Tuple[str, List[BPMNAutoFix]]:
        """
        Stosuje zaawansowane automatyczne naprawy do XML BPMN
        
        Args:
            bpmn_xml: XML BPMN do naprawienia
            
        Returns:
            Tuple[fixed_xml, applied_fixes]
        """
        self.fix_history = []
        
        try:
            # Parse XML
            root = ET.fromstring(bpmn_xml)
            
            # 1. Fix Pool/Process Structure - najważniejsze
            self._fix_pool_process_structure(root)
            
            # 2. Add missing Start/End Events to pools - kluczowa naprawa
            self._fix_missing_pool_events(root)
            
            # 3. Fix Message Flow targeting - bardzo ważne
            self._fix_message_flow_targeting(root)
            
            # 4. Add intermediate catch events if needed - zaawansowane
            self._add_intermediate_catch_events_for_message_flows(root)
            
            # 5. Fix sequence flow connections - standardowe
            self._fix_sequence_flow_connections(root)
            
            # 6. Fix naming and IDs - kosmetyczne ale ważne
            self._fix_naming_and_ids(root)
            
            # Convert back to string
            fixed_xml = ET.tostring(root, encoding='unicode')
            
            return fixed_xml, self.fix_history
            
        except Exception as e:
            error_fix = BPMNAutoFix(
                fix_id=self._generate_fix_id(),
                element_id="XML_ROOT",
                fix_type="PARSE_ERROR",
                description=f"Błąd parsowania XML: {str(e)}",
                before_state={},
                after_state={},
                success=False,
                error_message=str(e)
            )
            self.fix_history.append(error_fix)
            return bpmn_xml, self.fix_history

    def _fix_pool_process_structure(self, root: ET.Element):
        """
        Naprawia strukturę Pool/Process - zapewnia że każdy Pool ma odpowiadający Process
        """
        # Find all pools
        pools = root.findall('.//bpmn:participant', self.namespace)
        processes = root.findall('.//bpmn:process', self.namespace)
        
        process_ids = {p.get('id') for p in processes}
        
        for pool in pools:
            pool_id = pool.get('id')
            process_ref = pool.get('processRef')
            
            if not process_ref or process_ref not in process_ids:
                # Create new process for this pool
                new_process_id = f"process_{pool_id}"
                new_process = ET.SubElement(root, '{http://www.omg.org/spec/BPMN/20100524/MODEL}process')
                new_process.set('id', new_process_id)
                new_process.set('isExecutable', 'false')
                
                # Update pool reference
                pool.set('processRef', new_process_id)
                
                fix = BPMNAutoFix(
                    fix_id=self._generate_fix_id(),
                    element_id=pool_id,
                    fix_type="POOL_PROCESS_LINK",
                    description=f"Dodano Process '{new_process_id}' dla Pool '{pool_id}'",
                    before_state={'processRef': process_ref},
                    after_state={'processRef': new_process_id},
                    success=True
                )
                self.fix_history.append(fix)

    def _fix_missing_pool_events(self, root: ET.Element):
        """
        Dodaje brakujące Start/End Events do Pool - kluczowa naprawa!
        
        Implementuje strategię z naszego sukcesu:
        - Intermediate Catch Event zamiast Start Event dla Pool odbierających Message Flow
        - End Events na końcu każdego Pool
        """
        pools = root.findall('.//bpmn:participant', self.namespace)
        processes = root.findall('.//bpmn:process', self.namespace)
        
        for pool in pools:
            pool_id = pool.get('id')
            process_ref = pool.get('processRef')
            
            # Find corresponding process
            process = None
            for p in processes:
                if p.get('id') == process_ref:
                    process = p
                    break
            
            if not process:
                continue
            
            # Check if pool has incoming message flows
            has_incoming_messages = self._pool_has_incoming_message_flows(root, pool_id)
            
            # Check for existing start events in this process
            start_events = process.findall('.//bpmn:startEvent', self.namespace)
            intermediate_events = process.findall('.//bpmn:intermediateCatchEvent', self.namespace)
            
            # Add start event if missing (Intermediate Catch Event if has incoming messages)
            if not start_events and not intermediate_events:
                if has_incoming_messages:
                    # Add Intermediate Catch Event (like we did manually)
                    start_element = ET.SubElement(process, '{http://www.omg.org/spec/BPMN/20100524/MODEL}intermediateCatchEvent')
                    start_id = f"start_{pool_id.lower().replace(' ', '_')}"
                    start_element.set('id', start_id)
                    start_element.set('name', f"Start {pool.get('name', pool_id)}")
                    
                    fix = BPMNAutoFix(
                        fix_id=self._generate_fix_id(),
                        element_id=start_id,
                        fix_type="ADD_INTERMEDIATE_CATCH_EVENT",
                        description=f"Dodano Intermediate Catch Event dla Pool '{pool.get('name', pool_id)}'",
                        before_state={'events': len(start_events) + len(intermediate_events)},
                        after_state={'events': len(start_events) + len(intermediate_events) + 1},
                        success=True
                    )
                else:
                    # Add regular Start Event
                    start_element = ET.SubElement(process, '{http://www.omg.org/spec/BPMN/20100524/MODEL}startEvent')
                    start_id = f"start_{pool_id.lower().replace(' ', '_')}"
                    start_element.set('id', start_id)
                    start_element.set('name', f"Start")
                    
                    fix = BPMNAutoFix(
                        fix_id=self._generate_fix_id(),
                        element_id=start_id,
                        fix_type="ADD_START_EVENT",
                        description=f"Dodano Start Event dla Pool '{pool.get('name', pool_id)}'",
                        before_state={'start_events': len(start_events)},
                        after_state={'start_events': len(start_events) + 1},
                        success=True
                    )
                
                self.fix_history.append(fix)
            
            # Check for end events
            end_events = process.findall('.//bpmn:endEvent', self.namespace)
            
            if not end_events:
                # Add End Event
                end_element = ET.SubElement(process, '{http://www.omg.org/spec/BPMN/20100524/MODEL}endEvent')
                end_id = f"end_{pool_id.lower().replace(' ', '_')}"
                end_element.set('id', end_id)
                end_element.set('name', f"Koniec")
                
                fix = BPMNAutoFix(
                    fix_id=self._generate_fix_id(),
                    element_id=end_id,
                    fix_type="ADD_END_EVENT",
                    description=f"Dodano End Event dla Pool '{pool.get('name', pool_id)}'",
                    before_state={'end_events': len(end_events)},
                    after_state={'end_events': len(end_events) + 1},
                    success=True
                )
                self.fix_history.append(fix)

    def _pool_has_incoming_message_flows(self, root: ET.Element, pool_id: str) -> bool:
        """Sprawdza czy Pool ma przychodzące Message Flows"""
        message_flows = root.findall('.//bpmn:messageFlow', self.namespace)
        
        for mf in message_flows:
            target_ref = mf.get('targetRef')
            # Check if target is in this pool
            if target_ref and self._element_belongs_to_pool(root, target_ref, pool_id):
                return True
        
        return False

    def _element_belongs_to_pool(self, root: ET.Element, element_id: str, pool_id: str) -> bool:
        """Sprawdza czy element należy do danego Pool"""
        pools = root.findall('.//bpmn:participant', self.namespace)
        
        for pool in pools:
            if pool.get('id') == pool_id:
                process_ref = pool.get('processRef')
                
                # Find process and check if element exists there
                process = root.find(f".//bpmn:process[@id='{process_ref}']", self.namespace)
                if process is not None:
                    element = process.find(f".//*[@id='{element_id}']")
                    if element is not None:
                        return True
        
        return False

    def _fix_message_flow_targeting(self, root: ET.Element):
        """
        Naprawia targetowanie Message Flow - kluczowa naprawa!
        
        Implementuje strategię: Message Flow powinno wskazywać na Intermediate Catch Event,
        nie na Start Event
        """
        message_flows = root.findall('.//bpmn:messageFlow', self.namespace)
        
        for mf in message_flows:
            target_ref = mf.get('targetRef')
            
            if target_ref:
                # Find target element
                target_element = root.find(f".//*[@id='{target_ref}']")
                
                if target_element is not None and target_element.tag.endswith('startEvent'):
                    # Replace start event with intermediate catch event
                    pool_id = self._find_pool_for_element(root, target_ref)
                    
                    if pool_id:
                        new_target_id = f"start_{pool_id.lower().replace(' ', '_')}"
                        
                        # Update message flow target
                        old_target = target_ref
                        mf.set('targetRef', new_target_id)
                        
                        fix = BPMNAutoFix(
                            fix_id=self._generate_fix_id(),
                            element_id=mf.get('id', 'unknown'),
                            fix_type="FIX_MESSAGE_FLOW_TARGET",
                            description=f"Przekierowano Message Flow z {old_target} na {new_target_id}",
                            before_state={'targetRef': old_target},
                            after_state={'targetRef': new_target_id},
                            success=True
                        )
                        self.fix_history.append(fix)

    def _find_pool_for_element(self, root: ET.Element, element_id: str) -> str:
        """Znajduje Pool dla danego elementu"""
        pools = root.findall('.//bpmn:participant', self.namespace)
        
        for pool in pools:
            if self._element_belongs_to_pool(root, element_id, pool.get('id')):
                return pool.get('id')
        
        return None

    def _add_intermediate_catch_events_for_message_flows(self, root: ET.Element):
        """
        Dodaje Intermediate Catch Events dla Pool odbierających Message Flows
        jeśli jeszcze ich nie ma - zaawansowana naprawa
        """
        message_flows = root.findall('.//bpmn:messageFlow', self.namespace)
        
        for mf in message_flows:
            target_ref = mf.get('targetRef')
            source_ref = mf.get('sourceRef')
            
            if target_ref and source_ref:
                # Find target pool
                target_pool = self._find_pool_for_element(root, target_ref)
                source_pool = self._find_pool_for_element(root, source_ref)
                
                if target_pool and source_pool and target_pool != source_pool:
                    # Ensure there's an Intermediate Catch Event in target pool
                    process = self._find_process_for_pool(root, target_pool)
                    
                    if process is not None:
                        # Check if intermediate catch event already exists
                        catch_events = process.findall('.//bpmn:intermediateCatchEvent', self.namespace)
                        
                        expected_id = f"start_{target_pool.lower().replace(' ', '_')}"
                        exists = any(ce.get('id') == expected_id for ce in catch_events)
                        
                        if not exists:
                            # Create intermediate catch event
                            catch_event = ET.SubElement(process, '{http://www.omg.org/spec/BPMN/20100524/MODEL}intermediateCatchEvent')
                            catch_event.set('id', expected_id)
                            catch_event.set('name', f"Odbierz komunikat")
                            
                            # Update message flow to point to this event
                            mf.set('targetRef', expected_id)
                            
                            fix = BPMNAutoFix(
                                fix_id=self._generate_fix_id(),
                                element_id=expected_id,
                                fix_type="ADD_INTERMEDIATE_CATCH_FOR_MESSAGE",
                                description=f"Dodano Intermediate Catch Event {expected_id} dla Message Flow",
                                before_state={'catch_events': len(catch_events)},
                                after_state={'catch_events': len(catch_events) + 1},
                                success=True
                            )
                            self.fix_history.append(fix)

    def _find_process_for_pool(self, root: ET.Element, pool_id: str) -> ET.Element:
        """Znajduje Process dla danego Pool"""
        pool = root.find(f".//bpmn:participant[@id='{pool_id}']", self.namespace)
        if pool is not None:
            process_ref = pool.get('processRef')
            return root.find(f".//bpmn:process[@id='{process_ref}']", self.namespace)
        return None

    def _fix_sequence_flow_connections(self, root: ET.Element):
        """Naprawia połączenia Sequence Flow"""
        sequence_flows = root.findall('.//bpmn:sequenceFlow', self.namespace)
        
        for sf in sequence_flows:
            source_ref = sf.get('sourceRef')
            target_ref = sf.get('targetRef')
            
            if source_ref and target_ref:
                # Validate that both elements exist
                source_elem = root.find(f".//*[@id='{source_ref}']")
                target_elem = root.find(f".//*[@id='{target_ref}']")
                
                if source_elem is None:
                    # Remove invalid sequence flow
                    parent = sf.getparent()
                    if parent is not None:
                        parent.remove(sf)
                        
                        fix = BPMNAutoFix(
                            fix_id=self._generate_fix_id(),
                            element_id=sf.get('id', 'unknown'),
                            fix_type="REMOVE_INVALID_SEQUENCE_FLOW",
                            description=f"Usunięto nieprawidłowy Sequence Flow (brak source: {source_ref})",
                            before_state={'exists': True},
                            after_state={'exists': False},
                            success=True
                        )
                        self.fix_history.append(fix)

    def _fix_naming_and_ids(self, root: ET.Element):
        """Naprawia nazewnictwo i ID zgodnie z BPMN best practices"""
        # Fix empty names
        elements_with_names = root.findall(".//*[@name]")
        
        for elem in elements_with_names:
            name = elem.get('name', '').strip()
            if not name:
                elem_id = elem.get('id', 'unknown')
                elem_type = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                
                new_name = self._generate_meaningful_name(elem_type, elem_id)
                elem.set('name', new_name)
                
                fix = BPMNAutoFix(
                    fix_id=self._generate_fix_id(),
                    element_id=elem_id,
                    fix_type="FIX_EMPTY_NAME",
                    description=f"Dodano nazwę '{new_name}' dla elementu {elem_id}",
                    before_state={'name': ''},
                    after_state={'name': new_name},
                    success=True
                )
                self.fix_history.append(fix)

    def _generate_meaningful_name(self, element_type: str, element_id: str) -> str:
        """Generuje sensowną nazwę dla elementu"""
        type_names = {
            'startEvent': 'Początek',
            'endEvent': 'Koniec', 
            'intermediateCatchEvent': 'Odebranie komunikatu',
            'userTask': 'Zadanie użytkownika',
            'serviceTask': 'Zadanie systemowe',
            'exclusiveGateway': 'Decyzja',
            'parallelGateway': 'Rozgałęzienie'
        }
        
        base_name = type_names.get(element_type, element_type)
        return f"{base_name} ({element_id})"

    def _generate_fix_id(self) -> str:
        """Generuje unikalny ID dla naprawy"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"fix_{timestamp}_{len(self.fix_history):03d}"

    def get_fix_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie zastosowanych napraw"""
        success_fixes = [f for f in self.fix_history if f.success]
        failed_fixes = [f for f in self.fix_history if not f.success]
        
        fix_types = {}
        for fix in success_fixes:
            fix_types[fix.fix_type] = fix_types.get(fix.fix_type, 0) + 1
        
        return {
            'total_fixes_attempted': len(self.fix_history),
            'successful_fixes': len(success_fixes),
            'failed_fixes': len(failed_fixes),
            'fix_types': fix_types,
            'success_rate': len(success_fixes) / len(self.fix_history) if self.fix_history else 1.0,
            'all_fixes': self.fix_history
        }

# === FUNKCJE HELPER DO INTEGRACJI ===

def integrate_advanced_auto_fixer(bpmn_xml: str) -> Tuple[str, Dict[str, Any]]:
    """
    Funkcja integracyjna do użytku w głównym systemie
    
    Args:
        bpmn_xml: XML BPMN do naprawienia
        
    Returns:
        Tuple[fixed_xml, summary_report]
    """
    auto_fixer = AdvancedBPMNAutoFixer()
    fixed_xml, applied_fixes = auto_fixer.apply_comprehensive_auto_fixes(bpmn_xml)
    summary = auto_fixer.get_fix_summary()
    
    return fixed_xml, summary

def demo_advanced_auto_fixer():
    """Demonstracja zaawansowanego auto-fixera"""
    
    # Przykładowy BPMN z błędami (podobny do naszego oryginalnego)
    sample_bpmn = '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  id="Definitions_1">
  <bpmn:collaboration id="Collaboration_1">
    <bpmn:participant id="klient" name="Klient" processRef="Process_Klient"/>
    <bpmn:participant id="sprzedawca" name="Sprzedawca/Terminal" processRef="Process_Sprzedawca"/>
    <bpmn:participant id="aplikacja" name="Aplikacja mobilna banku" processRef="Process_Aplikacja"/>
    
    <bpmn:messageFlow id="MessageFlow_1" sourceRef="task_wybor_blik" targetRef="task_wprowadz_kod"/>
    <bpmn:messageFlow id="MessageFlow_2" sourceRef="task_autoryzacja" targetRef="task_sprawdzenie_dostepnosci"/>
  </bpmn:collaboration>
  
  <!-- Process bez Start/End Events - będą dodane -->
  <bpmn:process id="Process_Klient" isExecutable="false">
    <bpmn:userTask id="task_wybor_blik" name="Wybór płatności BLIK"/>
  </bpmn:process>
  
  <bpmn:process id="Process_Sprzedawca" isExecutable="false">
    <bpmn:userTask id="task_wprowadz_kod" name="Wprowadzenie kodu"/>
  </bpmn:process>
  
  <bpmn:process id="Process_Aplikacja" isExecutable="false">
    <bpmn:userTask id="task_autoryzacja" name="Autoryzacja płatności"/>
    <bpmn:serviceTask id="task_sprawdzenie_dostepnosci" name="Sprawdzenie dostępności środków"/>
  </bpmn:process>
</bpmn:definitions>'''
    
    print("🔧 DEMONSTRACJA ZAAWANSOWANEGO AUTO-FIXERA")
    print("=" * 70)
    
    print("📝 Oryginalny BPMN:")
    print(f"   Długość XML: {len(sample_bpmn)} znaków")
    
    # Apply fixes
    fixed_xml, summary = integrate_advanced_auto_fixer(sample_bpmn)
    
    print(f"\n✅ PODSUMOWANIE NAPRAW:")
    print(f"   Próby napraw: {summary['total_fixes_attempted']}")
    print(f"   Udane naprawy: {summary['successful_fixes']}")
    print(f"   Nieudane naprawy: {summary['failed_fixes']}")
    print(f"   Wskaźnik sukcesu: {summary['success_rate']:.1%}")
    
    print(f"\n🔧 TYPY ZASTOSOWANYCH NAPRAW:")
    for fix_type, count in summary['fix_types'].items():
        print(f"   {fix_type}: {count}")
    
    print(f"\n📋 SZCZEGÓŁY NAPRAW:")
    for i, fix in enumerate(summary['all_fixes'][:10], 1):  # Pierwszych 10
        status = "✅" if fix.success else "❌"
        print(f"   {i:2d}. {status} [{fix.fix_type}] {fix.description}")
    
    print(f"\n📊 WYNIKOWY XML:")
    print(f"   Długość XML: {len(fixed_xml)} znaków")
    print(f"   Przyrost rozmiaru: +{len(fixed_xml) - len(sample_bpmn)} znaków")

if __name__ == "__main__":
    demo_advanced_auto_fixer()