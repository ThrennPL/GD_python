"""
BPMN v2 - JSON Prompt Template
Szablon promptu dla AI z strukturalnym wyjściem JSON

Ten moduł zawiera:
1. JSON Schema dla odpowiedzi AI
2. Template promptu z przykładami  
3. Walidację odpowiedzi AI
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import jsonschema

from structure_definition import ElementType, TaskType, GatewayType
from polish_dictionary import ContextType


class ResponseFormat(Enum):
    """Formaty odpowiedzi AI"""
    JSON_STRUCTURED = "json_structured"
    JSON_SIMPLE = "json_simple"
    TEXT_WITH_JSON = "text_with_json"


@dataclass
class AIPromptTemplate:
    """Szablon promptu dla AI"""
    context_type: ContextType = ContextType.GENERIC
    response_format: ResponseFormat = ResponseFormat.JSON_STRUCTURED
    include_examples: bool = True
    include_banking_context: bool = False


class BPMNJSONSchema:
    """JSON Schema dla odpowiedzi BPMN"""
    
    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Zwraca pełen JSON Schema dla odpowiedzi BPMN"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": "BPMN Process Definition",
            "description": "Strukturalna definicja procesu BPMN w JSON",
            "required": ["process_name", "participants", "elements", "flows"],
            "properties": {
                "process_name": {
                    "type": "string",
                    "description": "Nazwa procesu",
                    "minLength": 3,
                    "maxLength": 100
                },
                "description": {
                    "type": "string", 
                    "description": "Opis procesu (opcjonalne)"
                },
                "participants": {
                    "type": "array",
                    "description": "Uczestnicy procesu (pools)",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["id", "name"],
                        "properties": {
                            "id": {"type": "string", "pattern": "^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ][a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ0-9_]*$"},
                            "name": {"type": "string", "minLength": 2},
                            "type": {"type": "string", "enum": ["human", "system", "organization"]},
                            "lanes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id", "name"],
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                },
                "elements": {
                    "type": "array",
                    "description": "Elementy procesu",
                    "minItems": 3,  # Minimum: start, 1 activity, end
                    "items": {
                        "type": "object",
                        "required": ["id", "name", "type", "participant"],
                        "properties": {
                            "id": {"type": "string", "pattern": "^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ][a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ0-9_]*$"},
                            "name": {"type": "string", "minLength": 2},
                            "type": {
                                "type": "string", 
                                "enum": ["startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent", 
                                        "userTask", "serviceTask", "exclusiveGateway", "parallelGateway", "boundaryEvent"]
                            },
                            "participant": {"type": "string"},
                            "lane": {"type": "string"},
                            "task_type": {"type": "string", "enum": ["user", "service", "send", "receive"]},
                            "gateway_type": {"type": "string", "enum": ["exclusive", "parallel", "inclusive"]},
                            "assignee": {"type": "string"},
                            "implementation": {"type": "string"}
                        }
                    }
                },
                "flows": {
                    "type": "array",
                    "description": "Przepływy między elementami",
                    "minItems": 2,  # Minimum: start->activity, activity->end
                    "items": {
                        "type": "object",
                        "required": ["id", "source", "target"],
                        "properties": {
                            "id": {"type": "string"},
                            "source": {"type": "string"},
                            "target": {"type": "string"},
                            "name": {"type": "string"},
                            "condition": {"type": "string"},
                            "type": {"type": "string", "enum": ["sequence", "message"], "default": "sequence"}
                        }
                    }
                },
                "gateways": {
                    "type": "array",
                    "description": "Definicje bramek z warunkami",
                    "items": {
                        "type": "object",
                        "required": ["id", "conditions"],
                        "properties": {
                            "id": {"type": "string"},
                            "conditions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["target", "condition"],
                                    "properties": {
                                        "target": {"type": "string"},
                                        "condition": {"type": "string"},
                                        "is_default": {"type": "boolean", "default": False}
                                    }
                                }
                            }
                        }
                    }
                },
                "metadata": {
                    "type": "object",
                    "description": "Metadane procesu",
                    "properties": {
                        "context": {"type": "string"},
                        "industry": {"type": "string"},
                        "complexity": {"type": "string", "enum": ["simple", "medium", "complex", "very complex"]},
                        "compliance_requirements": {"type": "array", "items": {"type": "string"}},
                        "estimated_duration": {"type": "string"}
                    }
                }
            }
        }


class PromptGenerator:
    """Generator promptów dla AI z JSON Schema"""
    
    def __init__(self, template: AIPromptTemplate):
        self.template = template
        self.schema = BPMNJSONSchema.get_schema()
    
    def generate_prompt(self, process_description: str) -> str:
        """
        Generuje kompletny prompt dla AI
        
        Args:
            process_description: Opis procesu biznesowego
            
        Returns:
            Gotowy prompt dla AI
        """
        # Podstawowa część promptu
        base_prompt = self._get_base_prompt()
        
        # Kontekst biznesowy
        context_section = self._get_context_section()
        
        # JSON Schema
        schema_section = self._get_schema_section()
        
        # Przykłady
        examples_section = self._get_examples_section() if self.template.include_examples else ""
        
        # Instrukcje walidacji
        validation_section = self._get_validation_section()
        
        # Opis procesu
        process_section = f"""
**OPIS PROCESU DO ANALIZY:**
{process_description}

"""
        
        # Instrukcja wyjścia
        output_instruction = self._get_output_instruction()
        
        return f"""{base_prompt}

{context_section}

{schema_section}

{examples_section}

{validation_section}

{process_section}

{output_instruction}"""
    
    def _get_base_prompt(self) -> str:
        """Podstawowa część promptu"""
        if self.template.context_type == ContextType.BANKING:
            expert_role = "architekt procesów bankowych z 15-letnim doświadczeniem w systemach core banking"
        else:
            expert_role = "analityk procesów biznesowych z 10-letnim doświadczeniem w notacji BPMN 2.0"
        
        return f"""**Jako {expert_role}, Twoim zadaniem jest przeanalizowanie opisu procesu biznesowego i zwrócenie strukturalnej definicji w formacie JSON zgodnym z BPMN 2.0.**

**CELE ANALIZY:**
1. Zidentyfikuj wszystkich uczestników procesu (participants/pools)
2. Wyodrębnij sekwencję działań i zadań
3. Znajdź punkty decyzyjne i bramki (gateways)
4. Określ przepływy między elementami
5. Przypisz odpowiednie typy BPMN do każdego elementu"""
    
    def _get_context_section(self) -> str:
        """Sekcja kontekstu biznesowego"""
        if self.template.context_type == ContextType.BANKING:
            return """
**KONTEKST BANKOWY:**
- Uwzględnij wymagania regulacyjne (KYC, AML, PSD2)
- Rozróżnij zadania użytkownika od automatyzacji systemowej
- Identyfikuj procesy autoryzacji i weryfikacji
- Zadbaj o ślady audytowe i compliance
- Standardowi uczestnicy: Klient, Bank, Systemy zewnętrzne"""
        elif self.template.context_type == ContextType.INSURANCE:
            return """
**KONTEKST UBEZPIECZENIOWY:**
- Uwzględnij procesy oceny ryzyka
- Identyfikuj procesy likwidacji szkód
- Zadbaj o zgodność z przepisami ubezpieczeniowymi"""
        else:
            return """
**KONTEKST OGÓLNY:**
- Stosuj standardowe wzorce BPMN 2.0
- Rozróżnij zadania ręczne od automatycznych
- Identyfikuj wszystkie strony procesu"""
    
    def _get_schema_section(self) -> str:
        """Sekcja z JSON Schema"""
        return f"""
**WYMAGANY FORMAT ODPOWIEDZI - JSON SCHEMA:**

Twoja odpowiedź MUSI być poprawnym JSON zgodnym z poniższym schema:

```json
{json.dumps(self.schema, indent=2, ensure_ascii=False)}
```"""
    
    def _get_examples_section(self) -> str:
        """Sekcja z przykładami"""
        if self.template.context_type == ContextType.BANKING:
            return self._get_banking_example()
        else:
            return self._get_generic_example()
    
    def _get_banking_example(self) -> str:
        """Przykład bankowy"""
        example = {
            "process_name": "Przelew internetowy",
            "description": "Proces wykonania przelewu przez klienta w bankowości elektronicznej",
            "participants": [
                {"id": "klient", "name": "Klient", "type": "human"},
                {"id": "system_bankowy", "name": "System Bankowy", "type": "system"}
            ],
            "elements": [
                {"id": "start1", "name": "Klient chce wykonać przelew", "type": "startEvent", "participant": "klient"},
                {"id": "task1", "name": "Logowanie do systemu", "type": "userTask", "participant": "klient", "task_type": "user"},
                {"id": "task2", "name": "Wypełnienie formularza przelewu", "type": "userTask", "participant": "klient", "task_type": "user"},
                {"id": "task3", "name": "Weryfikacja danych", "type": "serviceTask", "participant": "system_bankowy", "task_type": "service"},
                {"id": "gateway1", "name": "Czy dane są poprawne?", "type": "exclusiveGateway", "participant": "system_bankowy", "gateway_type": "exclusive"},
                {"id": "task4", "name": "Wykonanie przelewu", "type": "serviceTask", "participant": "system_bankowy", "task_type": "service"},
                {"id": "end1", "name": "Przelew wykonany", "type": "endEvent", "participant": "system_bankowy"}
            ],
            "flows": [
                {"id": "flow1", "source": "start1", "target": "task1"},
                {"id": "flow2", "source": "task1", "target": "task2"},
                {"id": "flow3", "source": "task2", "target": "task3"},
                {"id": "flow4", "source": "task3", "target": "gateway1"},
                {"id": "flow5", "source": "gateway1", "target": "task4", "name": "tak", "condition": "dane_poprawne"},
                {"id": "flow6", "source": "gateway1", "target": "task2", "name": "nie", "condition": "dane_niepoprawne"},
                {"id": "flow7", "source": "task4", "target": "end1"}
            ],
            "gateways": [
                {
                    "id": "gateway1",
                    "conditions": [
                        {"target": "task4", "condition": "dane_poprawne", "is_default": False},
                        {"target": "task2", "condition": "dane_niepoprawne", "is_default": True}
                    ]
                }
            ],
            "metadata": {
                "context": "banking",
                "industry": "financial_services", 
                "complexity": "medium",
                "compliance_requirements": ["PSD2", "RODO"]
            }
        }
        
        return f"""
**PRZYKŁAD ODPOWIEDZI (proces bankowy):**

```json
{json.dumps(example, indent=2, ensure_ascii=False)}
```"""
    
    def _get_generic_example(self) -> str:
        """Przykład ogólny"""
        example = {
            "process_name": "Obsługa zamówienia",
            "participants": [
                {"id": "klient", "name": "Klient", "type": "human"},
                {"id": "sklep", "name": "Sklep", "type": "organization"}
            ],
            "elements": [
                {"id": "start1", "name": "Klient składa zamówienie", "type": "startEvent", "participant": "klient"},
                {"id": "task1", "name": "Przetwarzanie zamówienia", "type": "serviceTask", "participant": "sklep"},
                {"id": "end1", "name": "Zamówienie zrealizowane", "type": "endEvent", "participant": "sklep"}
            ],
            "flows": [
                {"id": "flow1", "source": "start1", "target": "task1"},
                {"id": "flow2", "source": "task1", "target": "end1"}
            ]
        }
        
        return f"""
**PRZYKŁAD ODPOWIEDZI:**

```json
{json.dumps(example, indent=2, ensure_ascii=False)}
```"""
    
    def _get_validation_section(self) -> str:
        """Sekcja z zasadami walidacji"""
        return """
🚨🚨🚨 UWAGA: PARTICIPANT VALIDATION 🚨🚨🚨
KAŻDY ELEMENT MUSI MIEĆ PARTICIPANT Z LISTY PARTICIPANTS!
SPRAWDŹ KAŻDY ELEMENT DWUKROTNIE PRZED ZAPISEM!

**KRYTYCZNE ZASADY WALIDACJI:**

⚠️ **ABSOLUTNIE ZAKAZANE:**
- NIGDY nie dodawaj nowych uczestników (participants) poza tymi w opisie procesu
- NIGDY nie twórz elementów z nieistniejącymi participant ID  
- KAŻDY element MUSI używać TYLKO participant ID z listy participants
- ZAKAZANE participant ID: autoryzacja_platnosci, boundary_timer, payment_gateway, notification_service

✅ **WYMAGANE:**
1. **ID Elementów:** Wszystkie ID muszą być unikalne i składać się z liter, cyfr i podkreśleń
2. **Uczestnicy:** Każdy element musi być przypisany do istniejącego participant - SPRAWDŹ DWA RAZY!
3. **Przepływy:** Każdy flow musi łączyć istniejące elementy (source i target)
4. **Struktura procesu:** Minimum 1 startEvent, 1 aktywność, 1 endEvent
5. **Bramki:** Każda bramka musi mieć zdefiniowane warunki dla wszystkich wychodzących ścieżek
6. **Typy zadań:** Rozróżnij userTask (człowiek) od serviceTask (system)

🔥 **PARTICIPANT VALIDATION - KRYTYCZNE WYMAGANIE:**
- KAŻDY element MUSI używać TYLKO participant ID z listy participants
- SPRAWDŹ LISTĘ PARTICIPANTS PRZED KAŻDYM ELEMENTEM!
- NIGDY nie twórz elementów z participant jak: "autoryzacja_platnosci", "boundary_timer", "payment_system"
- UŻYJ TYLKO: klient, sprzedawca, aplikacja_mobilna, system_blik, clearing_blik, system_core_banking

❌ **PRZYKŁADY BŁĘDNYCH PARTICIPANT:**
- "autoryzacja_platnosci" → użyj "aplikacja_mobilna"  
- "boundary_timer" → użyj "system_blik"
- "payment_gateway" → użyj "system_blik"
- "notification_service" → użyj "aplikacja_mobilna"

✅ **POPRAWNY PRZYKŁAD:**
```json
{
  "participants": [{"id": "klient", "name": "Klient"}],
  "elements": [{"id": "task1", "participant": "klient"}]  ✓ POPRAWNE
}
```

❌ **BŁĘDNY PRZYKŁAD:**
```json
{
  "participants": [{"id": "klient", "name": "Klient"}], 
  "elements": [{"id": "task1", "participant": "bank_system"}]  ✗ BŁĄD!
}
```

🚨 **ABSOLUTNE ZAKAZY:**
- NIGDY nie wymyślaj nowych participant ID
- NIGDY nie dodawaj uczestników których nie ma w opisie procesu
- KAŻDY participant w elements MUSI istnieć w participants"""
    
    def _get_output_instruction(self) -> str:
        """Instrukcja formatu wyjścia"""
        return """
**INSTRUKCJA WYJŚCIA:**

Zwróć WYŁĄCZNIE poprawny JSON zgodny z podanym schema. 
Nie dodawaj żadnych komentarzy, objaśnień ani dodatkowego tekstu.
JSON musi być kompletny i gotowy do parsowania."""


class ResponseValidator:
    """Walidator odpowiedzi AI"""
    
    def __init__(self):
        self.schema = BPMNJSONSchema.get_schema()
    
    def validate_response(self, response: str) -> Tuple[bool, Optional[Dict], List[str]]:
        """
        Waliduje odpowiedź AI
        
        Args:
            response: Surowa odpowiedź AI
            
        Returns:
            Tuple (is_valid, parsed_json, errors)
        """
        errors = []
        parsed_json = None
        
        # 1. Spróbuj wyodrębnić JSON
        json_content = self._extract_json(response)
        if not json_content:
            errors.append("Nie znaleziono poprawnego JSON w odpowiedzi")
            return False, None, errors
        
        # 2. Spróbuj sparsować JSON
        try:
            parsed_json = json.loads(json_content)
        except json.JSONDecodeError as e:
            errors.append(f"Błąd parsowania JSON: {e}")
            return False, None, errors
        
        # 3. Waliduj względem schema
        try:
            jsonschema.validate(parsed_json, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Błąd walidacji schema: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Błąd w schema: {e}")
        
        # 4. Waliduj logikę biznesową
        business_errors = self._validate_business_logic(parsed_json)
        errors.extend(business_errors)
        
        is_valid = len(errors) == 0
        return is_valid, parsed_json, errors
    
    def _extract_json(self, response: str) -> Optional[str]:
        """Wyodrębnia JSON z odpowiedzi AI"""
        # Spróbuj znaleźć JSON w bloku kodu
        json_pattern = r'```(?:json)?\s*(.*?)```'
        match = re.search(json_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Spróbuj znaleźć JSON jako całą odpowiedź
        response_stripped = response.strip()
        if response_stripped.startswith('{') and response_stripped.endswith('}'):
            return response_stripped
        
        return None
    
    def _validate_business_logic(self, data: Dict) -> List[str]:
        """Waliduje logikę biznesową"""
        errors = []
        
        # Sprawdź czy wszystkie flow'y łączą istniejące elementy
        element_ids = {elem['id'] for elem in data.get('elements', [])}
        for flow in data.get('flows', []):
            if flow['source'] not in element_ids:
                errors.append(f"Flow {flow['id']}: nieznane źródło {flow['source']}")
            if flow['target'] not in element_ids:
                errors.append(f"Flow {flow['id']}: nieznany cel {flow['target']}")
        
        # Sprawdź czy są zdarzenia start i end
        element_types = [elem['type'] for elem in data.get('elements', [])]
        if 'startEvent' not in element_types:
            errors.append("Brak zdarzenia początkowego (startEvent)")
        if 'endEvent' not in element_types:
            errors.append("Brak zdarzenia końcowego (endEvent)")
        
        # Sprawdź czy wszyscy uczestnicy w elements istnieją w participants
        participant_ids = {p['id'] for p in data.get('participants', [])}
        for elem in data.get('elements', []):
            if elem['participant'] not in participant_ids:
                errors.append(f"Element {elem['id']}: nieznany participant {elem['participant']}")
        
        return errors


if __name__ == "__main__":
    # Test prompt template
    print("=== BPMN v2 JSON Prompt Template Test ===")
    
    # Utwórz template dla bankowości
    template = AIPromptTemplate(
        context_type=ContextType.BANKING,
        response_format=ResponseFormat.JSON_STRUCTURED,
        include_examples=True
    )
    
    generator = PromptGenerator(template)
    
    # Wygeneruj prompt dla procesu BLIK
    blik_description = """
    Klient w sklepie wybiera płatność BLIK i otrzymuje 6-cyfrowy kod od sprzedawcy. 
    Wprowadza kod w aplikacji mobilnej banku i autoryzuje płatność kodem PIN. 
    System BLIK banku sprawdza dostępność środków na koncie. 
    Jeśli środki są wystarczające, system blokuje środki i wysyła potwierdzenie. 
    Clearing BLIK przekazuje potwierdzenie do terminala sprzedawcy.
    """
    
    prompt = generator.generate_prompt(blik_description)
    
    print("✅ Prompt wygenerowany")
    print(f"Długość promptu: {len(prompt)} znaków")
    print(f"Sekcje: base, context, schema, examples, validation, process, output")
    
    # Test walidatora z przykładową odpowiedzią
    validator = ResponseValidator()
    
    test_response = """
    ```json
    {
        "process_name": "Płatność BLIK",
        "participants": [
            {"id": "klient", "name": "Klient", "type": "human"},
            {"id": "system_blik", "name": "System BLIK", "type": "system"}
        ],
        "elements": [
            {"id": "start1", "name": "Klient wybiera BLIK", "type": "startEvent", "participant": "klient"}
        ],
        "flows": []
    }
    ```
    """
    
    is_valid, parsed, errors = validator.validate_response(test_response)
    print(f"\nTest walidacji: {'✅ Valid' if is_valid else '❌ Invalid'}")
    if errors:
        print("Błędy:", errors)
    
    # Zapisz przykładowy prompt do pliku
    with open('bpmn_v2/example_prompt.txt', 'w', encoding='utf-8') as f:
        f.write(prompt)
    print("\n📁 Przykładowy prompt zapisany do: bpmn_v2/example_prompt.txt")