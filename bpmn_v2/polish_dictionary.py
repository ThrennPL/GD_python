"""
BPMN v2 - Słownik terminologii polskiej
Mapowanie polskich terminów na elementy BPMN

Ten moduł zawiera:
1. Słownik mapowania polskich słów na typy BPMN
2. Funkcje rozpoznawania kontekstu
3. Inteligentne dopasowywanie terminów
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from structure_definition import (
    ElementType, TaskType, GatewayType, 
    Task, Gateway, StartEvent, EndEvent, SequenceFlow
)


class ContextType(Enum):
    """Typy kontekstu procesu"""
    BANKING = "banking"
    INSURANCE = "insurance"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    GENERIC = "generic"


@dataclass
class TermMapping:
    """Mapowanie terminu na element BPMN"""
    polish_terms: List[str]
    bpmn_element: ElementType
    task_type: Optional[TaskType] = None
    gateway_type: Optional[GatewayType] = None
    confidence: float = 1.0
    context: ContextType = ContextType.GENERIC
    description: str = ""


class PolishToBPMNDictionary:
    """Słownik mapowania polskich terminów na elementy BPMN"""
    
    def __init__(self):
        self.mappings = self._build_mappings()
        self.banking_terms = self._build_banking_terms()
        self.action_patterns = self._build_action_patterns()
        self.condition_patterns = self._build_condition_patterns()
    
    def _build_mappings(self) -> List[TermMapping]:
        """Buduje podstawowe mapowania terminów"""
        return [
            # === ZDARZENIA POCZĄTKOWE ===
            TermMapping(
                polish_terms=["start", "początek", "rozpoczęcie", "rozpocznij", "zaczyna", "inicjuje", 
                             "uruchamia", "startuje", "wystartuj", "zainicjuj"],
                bpmn_element=ElementType.START_EVENT,
                description="Zdarzenie rozpoczynające proces"
            ),
            
            # === ZDARZENIA KOŃCOWE ===
            TermMapping(
                polish_terms=["koniec", "zakończenie", "end", "stop", "zakończ", "skończ",
                             "kończy", "zamyka", "finalizuje", "kompletuje"],
                bpmn_element=ElementType.END_EVENT,
                description="Zdarzenie kończące proces"
            ),
            
            # === ZADANIA UŻYTKOWNIKA ===
            TermMapping(
                polish_terms=["wprowadź", "wpisz", "wypełnij", "podaj", "wybierz", "zaznacz",
                             "autoryzuj", "zatwierdź", "podpisz", "weryfikuj ręcznie", "sprawdź ręcznie",
                             "wprowadza", "wybiera", "zatwierdza", "autoryzuje"],
                bpmn_element=ElementType.USER_TASK,
                task_type=TaskType.USER,
                description="Zadanie wymagające interwencji użytkownika"
            ),
            
            # === ZADANIA SYSTEMU ===
            TermMapping(
                polish_terms=["oblicz", "przelicz", "generuj", "utwórz", "wyślij", "przekaż",
                             "zapisz", "zachowaj", "aktualizuj", "synchronizuj", "integruj",
                             "sprawdza", "weryfikuje", "kontroluje", "monitoruje"],
                bpmn_element=ElementType.SERVICE_TASK,
                task_type=TaskType.SERVICE,
                description="Zadanie automatyczne systemu"
            ),
            
            # === BRAMKI EXCLUSIVE (XOR) ===
            TermMapping(
                polish_terms=["jeśli", "czy", "sprawdza", "weryfikuje", "kontroluje",
                             "decyduje", "czy", "lub", "albo"],
                bpmn_element=ElementType.EXCLUSIVE_GATEWAY,
                gateway_type=GatewayType.EXCLUSIVE,
                description="Bramka ekskluzywna - jedna ścieżka"
            ),
            
            # === BRAMKI PARALLEL (AND) ===
            TermMapping(
                polish_terms=["równolegle", "jednocześnie", "paralelnie", "w tym samym czasie",
                             "wszystkie", "oraz"],
                bpmn_element=ElementType.PARALLEL_GATEWAY,
                gateway_type=GatewayType.PARALLEL,
                description="Bramka równoległa - wszystkie ścieżki"
            ),
            
            # === WARUNKI ===
            TermMapping(
                polish_terms=["tak", "yes", "pozytywnie", "zgoda", "akceptacja", "tak"],
                bpmn_element=ElementType.SEQUENCE_FLOW,
                description="Pozytywny warunek przepływu"
            ),
            
            TermMapping(
                polish_terms=["nie", "no", "negatywnie", "odrzucenie", "brak", "odmowa"],
                bpmn_element=ElementType.SEQUENCE_FLOW,
                description="Negatywny warunek przepływu"
            )
        ]
    
    def _build_banking_terms(self) -> Dict[str, TermMapping]:
        """Specjalistyczne terminy bankowe"""
        return {
            # Procesy bankowe
            "przelew": TermMapping(
                ["przelew", "transfer", "przekazywanie środków"],
                ElementType.SERVICE_TASK, TaskType.SERVICE,
                context=ContextType.BANKING,
                description="Transfer środków pieniężnych"
            ),
            
            "autoryzacja": TermMapping(
                ["autoryzacja", "uwierzytelnienie", "weryfikacja tożsamości"],
                ElementType.USER_TASK, TaskType.USER,
                context=ContextType.BANKING,
                description="Proces potwierdzania tożsamości"
            ),
            
            "sprawdzenie_salda": TermMapping(
                ["sprawdzenie salda", "sprawdza saldo", "weryfikacja środków"],
                ElementType.SERVICE_TASK, TaskType.SERVICE,
                context=ContextType.BANKING,
                description="Automatyczne sprawdzenie dostępnych środków"
            ),
            
            "blokada_środków": TermMapping(
                ["blokada środków", "zablokuj środki", "rezerwacja kwoty"],
                ElementType.SERVICE_TASK, TaskType.SERVICE,
                context=ContextType.BANKING,
                description="Tymczasowa blokada środków na koncie"
            ),
            
            # Bramki bankowe
            "dostępność_środków": TermMapping(
                ["dostępność środków", "czy środki dostępne", "sprawdza limit"],
                ElementType.EXCLUSIVE_GATEWAY, gateway_type=GatewayType.EXCLUSIVE,
                context=ContextType.BANKING,
                description="Decyzja o dostępności środków"
            )
        }
    
    def _build_action_patterns(self) -> Dict[str, TaskType]:
        """Wzorce czasowników wskazujących na typ zadania"""
        return {
            # Zadania użytkownika (czynności interaktywne)
            'user_patterns': [
                r'\b(wprowadz|wprowadza|wprowadzić)\b',
                r'\b(wypełnij|wypełnia|wypełnić)\b',
                r'\b(wybierz|wybiera|wybrać)\b',
                r'\b(zatwierdz|zatwierdza|zatwierdzić)\b',
                r'\b(autoryzuj|autoryzuje|autoryzować)\b',
                r'\b(podpisz|podpisuje|podpisać)\b',
                r'\b(sprawdź|sprawdza|sprawdzić)\b',  # gdy dotyczy użytkownika
                r'\b(weryfikuj|weryfikuje|weryfikować)\b'  # gdy dotyczy użytkownika
            ],
            
            # Zadania systemu (czynności automatyczne)
            'service_patterns': [
                r'\b(oblicz|oblicza|obliczyć)\b',
                r'\b(generuj|generuje|generować)\b',
                r'\b(wyślij|wysyła|wysłać)\b',
                r'\b(zapisz|zapisuje|zapisać)\b',
                r'\b(aktualizuj|aktualizuje|aktualizować)\b',
                r'\b(synchronizuj|synchronizuje|synchronizować)\b',
                r'\b(przetwarz|przetwarza|przetwarzać)\b',
                r'\b(integruj|integruje|integrować)\b',
                r'\b(monitoruj|monitoruje|monitorować)\b'
            ]
        }
    
    def _build_condition_patterns(self) -> List[str]:
        """Wzorce wskazujące na warunki/bramki"""
        return [
            r'\bjeśli\b',
            r'\bczy\b.*\?',
            r'\bw przypadku gdy\b',
            r'\bgdy\b.*\btedy\b',
            r'\bjeżeli\b',
            r'\bw zależności od\b',
            r'\bsprawdza czy\b',
            r'\bweryfikuje czy\b'
        ]
    
    def recognize_element_type(self, text: str, context: ContextType = ContextType.GENERIC) -> Optional[Tuple[ElementType, Dict]]:
        """
        Rozpoznaje typ elementu BPMN na podstawie polskiego tekstu
        
        Args:
            text: Polski tekst opisujący element
            context: Kontekst biznesowy
            
        Returns:
            Tuple (ElementType, metadata) lub None
        """
        text_lower = text.lower()
        
        # 1. Sprawdź bezpośrednie mapowania
        for mapping in self.mappings:
            if mapping.context == context or mapping.context == ContextType.GENERIC:
                for term in mapping.polish_terms:
                    if term in text_lower:
                        metadata = {
                            'task_type': mapping.task_type,
                            'gateway_type': mapping.gateway_type,
                            'confidence': mapping.confidence,
                            'source_term': term,
                            'description': mapping.description
                        }
                        return mapping.bpmn_element, metadata
        
        # 2. Sprawdź specjalistyczne terminy (np. bankowe)
        if context == ContextType.BANKING:
            for term, mapping in self.banking_terms.items():
                for polish_term in mapping.polish_terms:
                    if polish_term in text_lower:
                        metadata = {
                            'task_type': mapping.task_type,
                            'gateway_type': mapping.gateway_type,
                            'confidence': 0.9,
                            'source_term': polish_term,
                            'description': mapping.description
                        }
                        return mapping.bpmn_element, metadata
        
        # 3. Analiza wzorców czasowników
        task_type = self._analyze_action_patterns(text_lower)
        if task_type:
            element_type = ElementType.USER_TASK if task_type == TaskType.USER else ElementType.SERVICE_TASK
            metadata = {
                'task_type': task_type,
                'confidence': 0.7,
                'source_term': 'pattern_match',
                'description': f'Rozpoznano na podstawie wzorca czasownika'
            }
            return element_type, metadata
        
        # 4. Sprawdź wzorce warunków/bramek
        if self._has_condition_patterns(text_lower):
            metadata = {
                'gateway_type': GatewayType.EXCLUSIVE,
                'confidence': 0.8,
                'source_term': 'condition_pattern',
                'description': 'Rozpoznano wzorzec warunku decyzyjnego'
            }
            return ElementType.EXCLUSIVE_GATEWAY, metadata
        
        # 5. Domyślnie zwróć TASK
        return ElementType.TASK, {
            'task_type': TaskType.GENERIC,
            'confidence': 0.3,
            'source_term': 'default',
            'description': 'Domyślne zadanie ogólne'
        }
    
    def _analyze_action_patterns(self, text: str) -> Optional[TaskType]:
        """Analizuje wzorce czasowników"""
        action_patterns = self._build_action_patterns()
        
        # Sprawdź wzorce zadań użytkownika
        for pattern in action_patterns['user_patterns']:
            if re.search(pattern, text, re.IGNORECASE):
                return TaskType.USER
        
        # Sprawdź wzorce zadań systemu
        for pattern in action_patterns['service_patterns']:
            if re.search(pattern, text, re.IGNORECASE):
                return TaskType.SERVICE
        
        return None
    
    def _has_condition_patterns(self, text: str) -> bool:
        """Sprawdza czy tekst zawiera wzorce warunków"""
        condition_patterns = self._build_condition_patterns()
        
        for pattern in condition_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def extract_process_elements(self, process_description: str, context: ContextType = ContextType.GENERIC) -> List[Dict]:
        """
        Wyodrębnia elementy procesu z polskiego opisu
        
        Args:
            process_description: Opis procesu po polsku
            context: Kontekst biznesowy
            
        Returns:
            Lista elementów z metadanymi
        """
        elements = []
        
        # Podziel na zdania
        sentences = re.split(r'[.!?]+', process_description)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Rozpoznaj typ elementu
            element_type, metadata = self.recognize_element_type(sentence, context) or (ElementType.TASK, {})
            
            element_info = {
                'sequence': i,
                'text': sentence,
                'bpmn_type': element_type,
                'metadata': metadata,
                'suggested_name': self._suggest_element_name(sentence, element_type)
            }
            
            elements.append(element_info)
        
        return elements
    
    def _suggest_element_name(self, text: str, element_type: ElementType) -> str:
        """Sugeruje nazwę elementu na podstawie tekstu"""
        # Usuń niepotrzebne słowa
        text_clean = re.sub(r'\b(następnie|potem|później|wtedy|gdy|jeśli)\b', '', text, flags=re.IGNORECASE)
        text_clean = text_clean.strip()
        
        # Skróć do sensownej długości
        if len(text_clean) > 50:
            words = text_clean.split()
            text_clean = ' '.join(words[:6]) + '...' if len(words) > 6 else text_clean
        
        # Dodaj prefix w zależności od typu
        if element_type == ElementType.START_EVENT:
            return f"Start: {text_clean}"
        elif element_type == ElementType.END_EVENT:
            return f"Koniec: {text_clean}"
        elif element_type in [ElementType.EXCLUSIVE_GATEWAY, ElementType.PARALLEL_GATEWAY]:
            return f"Decyzja: {text_clean}"
        else:
            return text_clean


class ProcessAnalyzer:
    """Analizator procesów biznesowych w języku polskim"""
    
    def __init__(self, context: ContextType = ContextType.GENERIC):
        self.dictionary = PolishToBPMNDictionary()
        self.context = context
    
    def analyze_process_description(self, description: str) -> Dict:
        """
        Analizuje opis procesu i zwraca strukturę BPMN
        
        Args:
            description: Polski opis procesu
            
        Returns:
            Słownik ze strukturą procesu
        """
        # Wyodrębnij elementy
        elements = self.dictionary.extract_process_elements(description, self.context)
        
        # Znajdź uczestników (pools)
        participants = self._extract_participants(description)
        
        # Znajdź przepływy
        flows = self._extract_flows(elements, description)
        
        # Znajdź warunki
        conditions = self._extract_conditions(description)
        
        return {
            'process_name': self._extract_process_name(description),
            'description': description,
            'elements': elements,
            'participants': participants,
            'flows': flows,
            'conditions': conditions,
            'context': self.context.value,
            'confidence': self._calculate_overall_confidence(elements)
        }
    
    def _extract_participants(self, description: str) -> List[str]:
        """Wyodrębnia uczestników procesu"""
        participants = set()
        
        # Wzorce uczestników
        participant_patterns = [
            r'\b(klient|customer|użytkownik|user)\b',
            r'\b(bank|system|aplikacja|serwis)\b',
            r'\b(sprzedawca|merchant|sklep)\b',
            r'\b(doradca|konsultant|analityk)\b',
            r'\b(administrator|admin|zarządca)\b'
        ]
        
        for pattern in participant_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            participants.update([match.lower() for match in matches])
        
        return list(participants)
    
    def _extract_flows(self, elements: List[Dict], description: str) -> List[Dict]:
        """Wyodrębnia przepływy między elementami"""
        flows = []
        
        # Proste połączenia sekwencyjne
        for i in range(len(elements) - 1):
            current = elements[i]
            next_elem = elements[i + 1]
            
            flows.append({
                'source': current['sequence'],
                'target': next_elem['sequence'],
                'type': 'sequence',
                'condition': None
            })
        
        return flows
    
    def _extract_conditions(self, description: str) -> List[Dict]:
        """Wyodrębnia warunki decyzyjne"""
        conditions = []
        
        # Wzorce warunków
        condition_patterns = [
            r'jeśli\s+(.+?)\s+to',
            r'w przypadku\s+(.+?)\s+',
            r'gdy\s+(.+?)\s+wtedy'
        ]
        
        for pattern in condition_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                condition_text = match.group(1).strip()
                conditions.append({
                    'condition': condition_text,
                    'position': match.start(),
                    'type': 'exclusive'
                })
        
        return conditions
    
    def _extract_process_name(self, description: str) -> str:
        """Wyodrębnia nazwę procesu z opisu"""
        # Pierwsze zdanie jako nazwa
        first_sentence = description.split('.')[0]
        return first_sentence[:50] + '...' if len(first_sentence) > 50 else first_sentence
    
    def _calculate_overall_confidence(self, elements: List[Dict]) -> float:
        """Oblicza ogólną pewność analizy"""
        if not elements:
            return 0.0
        
        confidences = [elem['metadata'].get('confidence', 0.5) for elem in elements]
        return sum(confidences) / len(confidences)


if __name__ == "__main__":
    # Test słownika
    print("=== BPMN v2 Dictionary Test ===")
    
    analyzer = ProcessAnalyzer(ContextType.BANKING)
    
    # Test bankowy proces BLIK
    blik_process = """
    Klient wybiera płatność BLIK w sklepie. 
    Sprzedawca generuje 6-cyfrowy kod. 
    Klient wprowadza kod w aplikacji banku. 
    System sprawdza dostępność środków na koncie. 
    Jeśli środki są dostępne to system blokuje kwotę. 
    System wysyła potwierdzenie do sprzedawcy. 
    Proces kończy się pomyślnie.
    """
    
    result = analyzer.analyze_process_description(blik_process)
    
    print(f"Proces: {result['process_name']}")
    print(f"Kontekst: {result['context']}")
    print(f"Pewność: {result['confidence']:.2f}")
    print(f"\nElementy ({len(result['elements'])}):")
    
    for elem in result['elements']:
        print(f"  {elem['sequence']}: {elem['bpmn_type'].value} - {elem['suggested_name']}")
        print(f"     Źródło: {elem['metadata'].get('source_term', 'N/A')}")
    
    print(f"\nUczestnicy: {', '.join(result['participants'])}")
    print(f"Warunki: {len(result['conditions'])}")
    print(f"Przepływy: {len(result['flows'])}")