"""
BPMN v2 - Complete Pipeline Integration
Kompletny pipeline: Polish Text → AI → JSON → BPMN XML

Ten moduł integruje wszystkie komponenty v2:
1. Polish Dictionary (terminologia)
2. JSON Prompt Template (szablon dla AI)
3. JSON to BPMN Generator (XML output)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Import all v2 components
from structure_definition import BPMNDiagram, Process, ElementType, TaskType
from polish_dictionary import PolishToBPMNDictionary, ProcessAnalyzer, ContextType
from json_prompt_template import BPMNJSONSchema, PromptGenerator, ResponseValidator, AIPromptTemplate
from json_to_bpmn_generator import BPMNJSONConverter
from ai_integration import AIClientFactory, ResponseParser, AIResponse
from ai_config import get_default_config, AIConfig
from ai_integration import AIProvider  # Import AIProvider z primary source


class BPMNv2Pipeline:
    """Kompletny pipeline BPMN v2"""
    
    def __init__(self, ai_config: Optional[AIConfig] = None):
        self.polish_dict = PolishToBPMNDictionary()
        self.process_analyzer = ProcessAnalyzer()  # używa domyślnego kontekstu
        self.json_schema = BPMNJSONSchema()
        self.prompt_template = AIPromptTemplate(context_type=ContextType.BANKING, include_banking_context=True)
        self.prompt_generator = PromptGenerator(self.prompt_template)
        self.response_validator = ResponseValidator()
        self.bpmn_converter = BPMNJSONConverter()
        
        # AI Integration
        self.ai_config = ai_config or get_default_config()
        self.ai_client = AIClientFactory.create_client(self.ai_config)
        self.response_parser = ResponseParser()
        
        print("🚀 BPMN v2 Pipeline zainicjalizowany")
        print("📚 Słownik PL→BPMN: ✅")
        print("📋 Generator promptów: ✅")
        print("🔄 JSON→BPMN konwerter: ✅")
        print(f"🤖 AI Client: {self.ai_config.provider.value} ({self.ai_config.model})")
        
        # Test AI connection
        if self.ai_client.test_connection():
            print("✅ AI connection test passed")
        else:
            print("⚠️ AI connection test failed - pipeline może nie działać poprawnie")
    
    def analyze_process_description(self, polish_text: str) -> Dict[str, Any]:
        """
        Analizuje polski opis procesu
        
        Args:
            polish_text: Opis procesu po polsku
            
        Returns:
            Analiza procesu z mapowaniem terminów
        """
        print(f"\n📝 Analizuję opis procesu ({len(polish_text)} znaków)")
        
        analysis = self.process_analyzer.analyze_process_description(polish_text)
        
        print(f"🎯 Znalezione elementy: {len(analysis.get('elements', []))}")
        print(f"🏢 Wykryci uczestnicy: {len(analysis.get('participants', []))}")
        print(f"📊 Confidence score: {analysis.get('confidence', 0):.2f}")
        
        return analysis
    
    def generate_ai_prompt(self, polish_text: str, context: str = "banking") -> str:
        """
        Generuje prompt dla AI na podstawie polskiego tekstu
        
        Args:
            polish_text: Opis procesu po polsku
            context: Kontekst biznesowy (default: banking)
            
        Returns:
            Kompletny prompt dla AI z JSON Schema
        """
        print(f"\n🤖 Generuję prompt AI (kontekst: {context})")
        
        # Analyze Polish text first
        analysis = self.analyze_process_description(polish_text)
        
        # Generate context-aware prompt
        prompt = self.prompt_generator.generate_prompt(
            process_description=polish_text
        )
        
        print(f"📄 Wygenerowany prompt ({len(prompt)} znaków)")
        
        return prompt
    
    def validate_ai_response(self, ai_response_json: Dict) -> Dict[str, Any]:
        """
        Waliduje odpowiedź AI względem JSON Schema
        
        Args:
            ai_response_json: Odpowiedź AI w JSON
            
        Returns:
            Wynik walidacji z błędami/ostrzeżeniami
        """
        print(f"\n🔍 Walidacja odpowiedzi AI")
        
        validation = self.response_validator.validate_response(ai_response_json)
        
        if validation['is_valid']:
            print(f"✅ Walidacja przeszła pomyślnie")
        else:
            print(f"❌ Błędy walidacji: {len(validation['errors'])}")
            for error in validation['errors']:
                print(f"   ⚠️ {error}")
        
        if validation['warnings']:
            print(f"⚠️ Ostrzeżenia: {len(validation['warnings'])}")
            for warning in validation['warnings']:
                print(f"   ⚠️ {warning}")
        
        return validation
    
    def convert_json_to_bpmn(self, process_json: Dict) -> str:
        """
        Konwertuje JSON procesu na BPMN XML
        
        Args:
            process_json: Dane procesu w JSON (zwalidowane)
            
        Returns:
            Kompletny BPMN XML
        """
        print(f"\n🔄 Konwersja JSON → BPMN XML")
        
        bpmn_xml = self.bpmn_converter.convert_json_to_bpmn(process_json)
        
        print(f"📄 BPMN XML wygenerowany ({len(bpmn_xml)} znaków)")
        print(f"🔧 Elementy: {len(process_json.get('elements', []))}")
        print(f"🔗 Przepływy: {len(process_json.get('flows', []))}")
        print(f"👥 Uczestnicy: {len(process_json.get('participants', []))}")
        
        return bpmn_xml
    
    def save_pipeline_outputs(self, process_name: str, polish_text: str, 
                             ai_prompt: str, ai_response: Dict, bpmn_xml: str) -> Dict[str, str]:
        """
        Zapisuje wszystkie artefakty pipeline'u
        
        Args:
            process_name: Nazwa procesu
            polish_text: Oryginalny tekst polski
            ai_prompt: Wygenerowany prompt
            ai_response: Odpowiedź AI w JSON
            bpmn_xml: Wygenerowany BPMN XML
            
        Returns:
            Dictionary z ścieżkami zapisanych plików
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = "".join(c for c in process_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        files = {}
        
        # 1. Original Polish text
        polish_file = f"{safe_name}_{timestamp}_input.txt"
        with open(polish_file, 'w', encoding='utf-8') as f:
            f.write(f"# {process_name}\n# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(polish_text)
        files['polish_input'] = polish_file
        
        # 2. AI Prompt
        prompt_file = f"{safe_name}_{timestamp}_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(ai_prompt)
        files['ai_prompt'] = prompt_file
        
        # 3. AI Response JSON
        json_file = f"{safe_name}_{timestamp}_response.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(ai_response, f, indent=2, ensure_ascii=False)
        files['ai_response'] = json_file
        
        # 4. BPMN XML
        bpmn_file = f"{safe_name}_{timestamp}.bpmn"
        with open(bpmn_file, 'w', encoding='utf-8') as f:
            f.write(bpmn_xml)
        files['bpmn_output'] = bpmn_file
        
        print(f"\n📁 Zapisano artefakty pipeline'u:")
        for artifact_type, filepath in files.items():
            print(f"   {artifact_type}: {filepath}")
        
        return files
    
    def run_complete_pipeline(self, polish_text: str, process_name: str = "Process", 
                            context: str = "banking", save_artifacts: bool = True) -> Dict[str, Any]:
        """
        Uruchamia kompletny pipeline BPMN v2
        
        Args:
            polish_text: Opis procesu po polsku
            process_name: Nazwa procesu
            context: Kontekst biznesowy
            save_artifacts: Czy zapisywać artefakty
            
        Returns:
            Kompletny wynik pipeline'u
        """
        print(f"\n{'='*60}")
        print(f"🚀 URUCHAMIANIE COMPLETE PIPELINE BPMN v2")
        print(f"📋 Proces: {process_name}")
        print(f"🏢 Kontekst: {context}")
        print(f"🔧 DEBUG: Polish text input length: {len(polish_text)}")
        print(f"🔧 DEBUG: Polish text preview: {polish_text[:200]}...")
        print(f"{'='*60}")
        
        result = {
            'success': False,
            'process_name': process_name,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'files': {}
        }
        
        try:
            # Step 1: Analyze Polish text
            print(f"\n📍 KROK 1: Analiza polskiego tekstu")
            analysis = self.analyze_process_description(polish_text)
            result['analysis'] = analysis
            
            # Step 2: Generate AI prompt
            print(f"\n📍 KROK 2: Generowanie promptu AI")
            ai_prompt = self.generate_ai_prompt(polish_text, context)
            result['ai_prompt'] = ai_prompt
            
            # Step 3: Get AI response
            print(f"\n📍 KROK 3: Wywołanie AI ({self.ai_config.provider.value})")
            print(f"🤖 Model: {self.ai_config.model}")
            print(f"📊 Prompt size: {len(ai_prompt)} znaków")
            
            ai_response = self.ai_client.generate_response(ai_prompt)
            
            if not ai_response.success:
                raise ValueError(f"AI API error: {ai_response.error}")
            
            print(f"✅ AI response received ({len(ai_response.content)} znaków)")
            if ai_response.usage:
                print(f"💰 Token usage: {ai_response.usage}")
            
            # Step 4: Parse AI response to JSON
            print(f"\n📍 KROK 4: Parsing odpowiedzi AI do JSON")
            json_success, parsed_json, parse_errors = self.response_parser.extract_json(ai_response)
            
            if not json_success:
                raise ValueError(f"JSON parsing failed: {parse_errors}")
            
            print(f"✅ JSON parsed successfully")
            result['ai_response'] = parsed_json
            
            # Step 5: Validate AI response
            print(f"\n📍 KROK 5: Walidacja JSON względem schema")
            json_string = json.dumps(parsed_json, ensure_ascii=False)
            validation_result = self.response_validator.validate_response(json_string)
            is_valid, validated_json, validation_errors = validation_result
            
            validation = {
                'is_valid': is_valid,
                'parsed_json': validated_json,
                'errors': validation_errors,
                'warnings': []
            }
            result['validation'] = validation
            
            if not validation['is_valid']:
                raise ValueError(f"AI response validation failed: {validation['errors']}")
            
            # Step 6: Generate BPMN XML
            print(f"\n📍 KROK 6: Generowanie BPMN XML")
            bpmn_xml = self.convert_json_to_bpmn(parsed_json)
            result['bpmn_xml'] = bpmn_xml
            
            # Step 7: Save artifacts
            if save_artifacts:
                print(f"\n📍 KROK 7: Zapisywanie artefaktów")
                files = self.save_pipeline_outputs(
                    process_name, polish_text, ai_prompt, parsed_json, bpmn_xml
                )
                result['files'] = files
            
            result['success'] = True
            
            print(f"\n{'='*60}")
            print(f"✅ PIPELINE ZAKOŃCZONY SUKCESEM!")
            print(f"📊 Analiza: {analysis['confidence']:.2f} confidence")
            print(f"🤖 AI: {self.ai_config.provider.value} - {self.ai_config.model}")
            if ai_response.usage:
                print(f"💰 Tokens: {ai_response.usage}")
            print(f"📄 BPMN XML: {len(bpmn_xml)} znaków")
            if save_artifacts:
                print(f"📁 Pliki: {len(result['files'])} artefaktów")
            print(f"{'='*60}")
        
        except Exception as e:
            print(f"\n❌ BŁĄD PIPELINE: {e}")
            result['error'] = str(e)
            result['traceback'] = traceback.format_exc()
        
        return result
    
    def _create_simulated_ai_response(self, analysis: Dict, polish_text: str) -> Dict:
        """Tworzy symulowaną odpowiedź AI na podstawie analizy"""
        
        # Extract elements from analysis
        participants = analysis.get('participants', ['klient', 'system'])
        elements = analysis.get('elements', [])
        
        # Build participants list FIRST
        participant_list = []
        unique_participants = list(set(participants[:3]))  # Max 3 unique participants
        for i, p in enumerate(unique_participants):
            participant_list.append({
                "id": p.lower(),  # use lowercase as ID
                "name": p.capitalize(),
                "type": "human" if i == 0 else "system"
            })
        
        # Build simulated process
        simulated_elements = []
        flows = []
        
        # Start event
        start_participant = participant_list[0]['id'] if participant_list else "klient"
        simulated_elements.append({
            "id": "start_1",
            "name": "Rozpoczęcie procesu",
            "type": "startEvent",
            "participant": start_participant
        })
        
        # Add tasks from analyzed elements or create default ones
        task_counter = 1
        if elements and len(elements) > 2:  # We have meaningful elements
            for i, element in enumerate(elements):
                if element.get('type') in ['userTask', 'serviceTask', 'task']:
                    # Ensure participant exists
                    participant_idx = i % len(participant_list)
                    participant = participant_list[participant_idx]['id'] if participant_list else "klient"
                    
                    simulated_elements.append({
                        "id": f"task_{task_counter}",
                        "name": element.get('name', f"Task {task_counter}"),
                        "type": element.get('type', 'task'),
                        "participant": participant
                    })
                    task_counter += 1
        
        # Ensure we have at least one task between start and end
        if len(simulated_elements) == 1:  # Only start event
            # Add a default task
            participant = participant_list[0]['id'] if participant_list else "klient"
            simulated_elements.append({
                "id": f"task_{task_counter}",
                "name": "Główne zadanie procesu",
                "type": "userTask",
                "participant": participant
            })
        
        # End event
        end_participant = participant_list[-1]['id'] if participant_list else "system"
        simulated_elements.append({
            "id": "end_1", 
            "name": "Zakończenie procesu",
            "type": "endEvent",
            "participant": end_participant
        })
        
        # Create flows - ensure we have enough flows
        for i in range(len(simulated_elements) - 1):
            flows.append({
                "id": f"flow_{i+1}",
                "source": simulated_elements[i]['id'],
                "target": simulated_elements[i+1]['id'],
                "type": "sequence"
            })
        
        return {
            "process_name": "Proces zautomatyzowany",
            "description": polish_text[:200] + "..." if len(polish_text) > 200 else polish_text,
            "participants": participant_list,
            "elements": simulated_elements,
            "flows": flows
        }


def main():
    """Demonstracja kompletnego pipeline BPMN v2 z rzeczywistym AI"""
    print("🌟 BPMN v2 Complete Pipeline Demo - with Real AI Integration")
    
    # Test available AI providers first
    from ai_config import print_config_status, create_bpmn_config
    print_config_status()
    
    # Use Mock client for demo (change to real AI config as needed)
    print(f"\n🤖 Using Mock Client for demo...")
    print("💡 To use real AI, set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
    
    # Initialize pipeline with Mock AI
    pipeline = BPMNv2Pipeline(ai_config=MOCK_CLIENT)
    
    # Example 1: BLIK payment process
    blik_text = """
    Klient chce dokonać płatności BLIK w sklepie internetowym.
    Najpierw wybiera opcję płatności BLIK i wprowadza kod z aplikacji bankowej.
    System BLIK sprawdza dostępność środków na koncie i weryfikuje kod.
    Jeśli weryfikacja jest pomyślna, system blokuje środki i wysyła potwierdzenie do klienta.
    W przeciwnym razie wyświetla komunikat o błędzie.
    """
    
    result1 = pipeline.run_complete_pipeline(
        polish_text=blik_text,
        process_name="Płatność BLIK",
        context="banking"
    )
    
    # Example 2: Loan application
    loan_text = """
    Klient składa wniosek o kredyt hipoteczny w banku.
    Bank weryfikuje dokumenty i sprawdza historię kredytową.
    Następnie ocenia zdolność kredytową i podejmuje decyzję.
    Jeśli wniosek zostanie zaakceptowany, przygotowuje umowę kredytową.
    """
    
    result2 = pipeline.run_complete_pipeline(
        polish_text=loan_text,
        process_name="Wniosek o kredyt hipoteczny", 
        context="banking"
    )
    
    # Summary
    print(f"\n🎯 PODSUMOWANIE DEMO:")
    print(f"✅ Proces 1 (BLIK): {'SUKCES' if result1['success'] else 'BŁĄD'}")
    print(f"✅ Proces 2 (Kredyt): {'SUKCES' if result2['success'] else 'BŁĄD'}")
    
    if result1['success'] and result2['success']:
        print(f"\n🚀 Pipeline BPMN v2 z AI Integration działa poprawnie!")
        print(f"📁 Wygenerowane artefakty:")
        for name, files in [("BLIK", result1.get('files', {})), ("Kredyt", result2.get('files', {}))]:
            print(f"   {name}:")
            for artifact_type, filepath in files.items():
                print(f"     - {artifact_type}: {filepath}")
        
        print(f"\n💡 Aby użyć rzeczywistego AI:")
        print(f"   export OPENAI_API_KEY='your-key'")
        print(f"   # lub")
        print(f"   export ANTHROPIC_API_KEY='your-key'")
        print(f"   # i uruchom ponownie")


if __name__ == "__main__":
    main()