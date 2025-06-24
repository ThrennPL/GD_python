from dataclasses import dataclass
from typing import List, Optional

@dataclass
class UMLClass:
    name: str
    attributes: List[dict]
    methods: List[dict]
    stereotype: Optional[str] = None
    is_abstract: bool = False

@dataclass
class UMLRelation:
    source: str
    target: str
    relation_type: str
    label: Optional[str] = None
    source_multiplicity: Optional[str] = None
    target_multiplicity: Optional[str] = None

@dataclass
class UMLEnum:
    name: str
    values: list

@dataclass
class UMLNote:
    target: str
    text: str