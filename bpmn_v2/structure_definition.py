"""
BPMN v2 - Clean Architecture
Definicja minimalnej struktury BPMN procesu

Ten moduł definiuje:
1. Minimalne wymagania dla poprawnego BPMN
2. Strukturę danych dla procesów
3. Walidację kompletności procesu
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid


class ElementType(Enum):
    """Typy elementów BPMN"""
    START_EVENT = "startEvent"
    END_EVENT = "endEvent"
    TASK = "task"
    USER_TASK = "userTask"
    SERVICE_TASK = "serviceTask"
    EXCLUSIVE_GATEWAY = "exclusiveGateway"
    PARALLEL_GATEWAY = "parallelGateway"
    SEQUENCE_FLOW = "sequenceFlow"
    MESSAGE_FLOW = "messageFlow"


class TaskType(Enum):
    """Podtypy zadań"""
    GENERIC = "task"
    USER = "userTask"
    SERVICE = "serviceTask"
    SEND = "sendTask"
    RECEIVE = "receiveTask"
    SCRIPT = "scriptTask"
    MANUAL = "manualTask"


class GatewayType(Enum):
    """Typy bramek"""
    EXCLUSIVE = "exclusiveGateway"  # XOR - jedna ścieżka
    PARALLEL = "parallelGateway"    # AND - równolegle
    INCLUSIVE = "inclusiveGateway"  # OR - jedna lub więcej


@dataclass
class BPMNElement:
    """Bazowy element BPMN"""
    id: str = field(default_factory=lambda: f"element_{uuid.uuid4().hex[:8]}")
    name: Optional[str] = None
    type: ElementType = ElementType.TASK
    
    def __post_init__(self):
        """Walidacja po utworzeniu"""
        if not self.id:
            self.id = f"element_{uuid.uuid4().hex[:8]}"


@dataclass
class StartEvent(BPMNElement):
    """Zdarzenie początkowe"""
    type: ElementType = field(default=ElementType.START_EVENT, init=False)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.id.startswith('start'):
            self.id = f"startEvent_{uuid.uuid4().hex[:8]}"


@dataclass
class EndEvent(BPMNElement):
    """Zdarzenie końcowe"""
    type: ElementType = field(default=ElementType.END_EVENT, init=False)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.id.startswith('end'):
            self.id = f"endEvent_{uuid.uuid4().hex[:8]}"


@dataclass
class Task(BPMNElement):
    """Zadanie/Aktywność"""
    task_type: TaskType = TaskType.GENERIC
    assignee: Optional[str] = None  # Dla userTask
    candidate_groups: List[str] = field(default_factory=list)
    implementation: Optional[str] = None  # Dla serviceTask
    type: ElementType = field(default=ElementType.TASK, init=False)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.id.startswith('task'):
            self.id = f"task_{uuid.uuid4().hex[:8]}"


@dataclass
class Gateway(BPMNElement):
    """Bramka decyzyjna"""
    gateway_type: GatewayType = GatewayType.EXCLUSIVE
    conditions: Dict[str, str] = field(default_factory=dict)  # {target_id: condition}
    type: ElementType = field(default=ElementType.EXCLUSIVE_GATEWAY, init=False)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.id.startswith('gateway'):
            self.id = f"gateway_{uuid.uuid4().hex[:8]}"


@dataclass
class SequenceFlow(BPMNElement):
    """Przepływ sekwencyjny"""
    source_ref: str = ""
    target_ref: str = ""
    condition_expression: Optional[str] = None
    type: ElementType = field(default=ElementType.SEQUENCE_FLOW, init=False)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.id.startswith('flow'):
            self.id = f"flow_{uuid.uuid4().hex[:8]}"
    
    def is_valid(self) -> bool:
        """Sprawdza czy flow ma źródło i cel"""
        return bool(self.source_ref and self.target_ref)


@dataclass
class MessageFlow(BPMNElement):
    """Przepływ komunikatów między poolami"""
    source_ref: str = ""
    target_ref: str = ""
    type: ElementType = field(default=ElementType.MESSAGE_FLOW, init=False)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.id.startswith('message'):
            self.id = f"messageFlow_{uuid.uuid4().hex[:8]}"


@dataclass
class Lane:
    """Tor w poolu (rola/system)"""
    id: str = field(default_factory=lambda: f"lane_{uuid.uuid4().hex[:8]}")
    name: str = ""
    element_refs: List[str] = field(default_factory=list)  # ID elementów w torze


@dataclass
class Pool:
    """Pool/Uczestnik procesu"""
    id: str = field(default_factory=lambda: f"pool_{uuid.uuid4().hex[:8]}")
    name: str = ""
    process_ref: str = ""
    lanes: List[Lane] = field(default_factory=list)
    
    def add_lane(self, name: str) -> Lane:
        """Dodaje nowy tor do poolu"""
        lane = Lane(name=name)
        self.lanes.append(lane)
        return lane


@dataclass
class Process:
    """Proces BPMN"""
    id: str = field(default_factory=lambda: f"process_{uuid.uuid4().hex[:8]}")
    name: str = ""
    is_executable: bool = True
    
    # Elementy procesu
    start_events: List[StartEvent] = field(default_factory=list)
    end_events: List[EndEvent] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    gateways: List[Gateway] = field(default_factory=list)
    sequence_flows: List[SequenceFlow] = field(default_factory=list)
    
    def get_all_elements(self) -> List[BPMNElement]:
        """Zwraca wszystkie elementy procesu"""
        return (self.start_events + self.end_events + 
                self.tasks + self.gateways + self.sequence_flows)
    
    def validate(self) -> Dict[str, List[str]]:
        """Waliduje poprawność procesu"""
        errors = {
            'structure': [],
            'flows': [],
            'elements': []
        }
        
        # Sprawdź czy są zdarzenia start/end
        if not self.start_events:
            errors['structure'].append("Brak zdarzenia początkowego")
        if not self.end_events:
            errors['structure'].append("Brak zdarzenia końcowego")
            
        # Sprawdź flows
        all_element_ids = {e.id for e in self.get_all_elements() if e.type != ElementType.SEQUENCE_FLOW}
        for flow in self.sequence_flows:
            if not flow.is_valid():
                errors['flows'].append(f"Flow {flow.id} nie ma źródła lub celu")
            if flow.source_ref not in all_element_ids:
                errors['flows'].append(f"Flow {flow.id}: nieznane źródło {flow.source_ref}")
            if flow.target_ref not in all_element_ids:
                errors['flows'].append(f"Flow {flow.id}: nieznany cel {flow.target_ref}")
        
        return errors


@dataclass
class BPMNDiagram:
    """Kompletny diagram BPMN"""
    id: str = field(default_factory=lambda: f"diagram_{uuid.uuid4().hex[:8]}")
    name: str = ""
    
    # Struktura procesu
    pools: List[Pool] = field(default_factory=list)
    processes: List[Process] = field(default_factory=list)
    message_flows: List[MessageFlow] = field(default_factory=list)
    
    # Metadane
    created_by: str = "BPMN Generator v2"
    description: str = ""
    
    def add_pool(self, name: str) -> Pool:
        """Dodaje nowy pool"""
        process = Process(name=f"Process for {name}")
        self.processes.append(process)
        
        pool = Pool(name=name, process_ref=process.id)
        self.pools.append(pool)
        return pool
    
    def get_main_process(self) -> Process:
        """Zwraca główny proces (dla przypadku bez pooli)"""
        if not self.processes:
            self.processes.append(Process(name=self.name or "Main Process"))
        return self.processes[0]
    
    def validate(self) -> Dict[str, Any]:
        """Waliduje cały diagram"""
        validation_result = {
            'is_valid': True,
            'errors': {
                'diagram': [],
                'pools': [],
                'processes': []
            },
            'warnings': []
        }
        
        # Waliduj procesy
        for process in self.processes:
            process_errors = process.validate()
            if any(process_errors.values()):
                validation_result['errors']['processes'].append({
                    'process_id': process.id,
                    'errors': process_errors
                })
                validation_result['is_valid'] = False
        
        # Sprawdź powiązania pools-processes
        pool_process_refs = {p.process_ref for p in self.pools}
        process_ids = {p.id for p in self.processes}
        
        orphaned_refs = pool_process_refs - process_ids
        if orphaned_refs:
            validation_result['errors']['pools'].extend([
                f"Pool odnosi się do nieistniejącego procesu: {ref}"
                for ref in orphaned_refs
            ])
            validation_result['is_valid'] = False
        
        return validation_result


class MinimalBPMNRequirements:
    """Definicja minimalnych wymagań dla poprawnego BPMN"""
    
    @staticmethod
    def get_minimal_requirements() -> Dict[str, Any]:
        """Zwraca minimalne wymagania"""
        return {
            'required_elements': {
                'start_events': {'min': 1, 'description': 'Co najmniej jedno zdarzenie początkowe'},
                'end_events': {'min': 1, 'description': 'Co najmniej jedno zdarzenie końcowe'},
                'activities': {'min': 1, 'description': 'Co najmniej jedna aktywność'}
            },
            'flow_rules': {
                'connectivity': 'Wszystkie elementy muszą być połączone',
                'start_flow': 'Zdarzenie początkowe musi mieć wychodzący flow',
                'end_flow': 'Zdarzenie końcowe musi mieć przychodzący flow',
                'gateway_completeness': 'Bramki muszą mieć wszystkie ścieżki zdefiniowane'
            },
            'naming_rules': {
                'unique_ids': 'Wszystkie ID muszą być unikalne',
                'descriptive_names': 'Elementy powinny mieć opisowe nazwy',
                'id_format': 'ID powinny być bezpieczne dla XML'
            }
        }
    
    @staticmethod
    def create_minimal_process(name: str) -> BPMNDiagram:
        """Tworzy minimalny poprawny proces"""
        diagram = BPMNDiagram(name=name)
        main_process = diagram.get_main_process()
        
        # Minimalne elementy
        start = StartEvent(name="Start")
        task = Task(name="Główna aktywność")
        end = EndEvent(name="End")
        
        # Połączenia
        flow1 = SequenceFlow(
            source_ref=start.id,
            target_ref=task.id,
            name="start->task"
        )
        flow2 = SequenceFlow(
            source_ref=task.id,
            target_ref=end.id,
            name="task->end"
        )
        
        # Dodaj do procesu
        main_process.start_events.append(start)
        main_process.tasks.append(task)
        main_process.end_events.append(end)
        main_process.sequence_flows.extend([flow1, flow2])
        
        return diagram


if __name__ == "__main__":
    # Test minimalnej struktury
    print("=== BPMN v2 Structure Definition ===")
    
    # Utwórz minimalny proces
    diagram = MinimalBPMNRequirements.create_minimal_process("Test Process")
    
    # Waliduj
    validation = diagram.validate()
    print(f"Walidacja: {validation['is_valid']}")
    
    if not validation['is_valid']:
        print("Błędy:", validation['errors'])
    else:
        print("✅ Minimalny proces jest poprawny!")
        
    print(f"\nElementy procesu:")
    main_process = diagram.get_main_process()
    print(f"- Start events: {len(main_process.start_events)}")
    print(f"- Tasks: {len(main_process.tasks)}")
    print(f"- End events: {len(main_process.end_events)}")
    print(f"- Sequence flows: {len(main_process.sequence_flows)}")