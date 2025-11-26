"""
BPMN v2 - Complete Demo
Demonstracja wszystkich funkcji systemu BPMN v2 z AI i MCP

Pokazuje:
1. Podstawowy pipeline (Polish → AI → BPMN)
2. Integrację z rzeczywistym AI
3. Weryfikację i poprawki przez MCP server  
4. Iteracyjne doskonalenie procesu
5. Eksport do różnych formatów
"""

import os
import json
from datetime import datetime
from typing import Dict, List

# Import all BPMN v2 modules
from complete_pipeline import BPMNv2Pipeline
from iterative_pipeline import IterativeImprovementPipeline
from mcp_server_simple import SimpleMCPServer
from ai_config import (
    get_default_config, print_config_status, 
    create_bpmn_config, get_available_models_for_provider
)


class BPMNv2Demo:
    """Kompletne demo systemu BPMN v2"""
    
    def __init__(self):
        self.basic_pipeline = None
        self.iterative_pipeline = None
        self.mcp_server = None
        
    def run_complete_demo(self):
        """Uruchamia kompletne demo wszystkich funkcji"""
        print("🌟" * 30)
        print("🚀 BPMN v2 COMPLETE SYSTEM DEMO")
        print("🌟" * 30)
        
        # 1. Show AI configuration status
        self.demo_ai_configuration()
        
        # 2. Basic pipeline demo
        self.demo_basic_pipeline()
        
        # 3. MCP server demo
        self.demo_mcp_server()
        
        # 4. Iterative improvement demo  
        self.demo_iterative_improvement()
        
        # 5. Real AI demo (if available)
        self.demo_real_ai()
        
        # 6. Summary
        self.demo_summary()
    
    def demo_ai_configuration(self):
        """Demonstracja konfiguracji AI"""
        print(f"\n{'='*60}")
        print("1️⃣ AI CONFIGURATION DEMO")
        print(f"{'='*60}")
        
        print_config_status()
        
        default_config = get_default_config()
        print(f"\n🎯 Selected AI: {default_config.provider.value} - {default_config.model}")
        
        # Show available configs
        print(f"\n📋 Available configurations:")
        
        # Get available configs based on env
        available = get_available_models_for_provider()
        
        configs = {
            f"{available['provider']} (from env)": get_default_config(),
        }
        
        # Add model variations if available
        for model in available['models'][:3]:  # Limit to 3 options
            config = create_bpmn_config(selected_model=model)
            configs[f"{config.provider.value} - {model}"] = config
        
        for name, config in configs.items():
            available = "🟢" if self._is_config_available(config) else "🔴"
            print(f"   {available} {name}: {config.model}")
        
        print(f"\n💡 Tip: Set OPENAI_API_KEY or ANTHROPIC_API_KEY to use real AI")
    
    def demo_basic_pipeline(self):
        """Demonstracja podstawowego pipeline"""
        print(f"\n{'='*60}")
        print("2️⃣ BASIC PIPELINE DEMO")  
        print(f"{'='*60}")
        
        # Initialize with best available AI
        ai_config = get_default_config()
        self.basic_pipeline = BPMNv2Pipeline(ai_config=ai_config)
        
        # Demo process
        demo_text = """
        Klient chce otworzyć nowe konto bankowe.
        Najpierw wypełnia wniosek online i przesyła dokumenty.
        Bank weryfikuje tożsamość klienta i sprawdza jego historię kredytową.
        Jeśli weryfikacja jest pozytywna, bank aktywuje konto i wysyła karty.
        Klient otrzymuje dane dostępowe do bankowości elektronicznej.
        """
        
        print(f"📝 Proces do analizy:")
        print(f"   {demo_text.strip()}")
        
        result = self.basic_pipeline.run_complete_pipeline(
            polish_text=demo_text,
            process_name="Otwarcie konta bankowego",
            context="banking",
            save_artifacts=True
        )
        
        if result['success']:
            print(f"\n✅ Basic Pipeline - SUCCESS!")
            print(f"   📊 Quality: {result.get('final_quality', 'N/A')}")
            print(f"   📁 Files: {len(result.get('files', {}))}")
            for file_type, path in result.get('files', {}).items():
                print(f"      - {file_type}: {path}")
        else:
            print(f"\n❌ Basic Pipeline - FAILED: {result.get('error')}")
    
    def demo_mcp_server(self):
        """Demonstracja MCP server"""
        print(f"\n{'='*60}")
        print("3️⃣ MCP SERVER DEMO")
        print(f"{'='*60}")
        
        self.mcp_server = SimpleMCPServer()
        
        # Test process with quality issues
        test_process = {
            "process_name": "Prosty proces",
            "description": "",
            "participants": [
                {"id": "user", "name": "U", "type": "human"}
            ],
            "elements": [
                {"id": "start", "name": "", "type": "startEvent", "participant": "user"},
                {"id": "end", "name": "", "type": "endEvent", "participant": "user"}
            ],
            "flows": []
        }
        
        print(f"🔍 Testing process with quality issues...")
        verification = self.mcp_server.verify_bpmn_process(test_process)
        
        print(f"\n📊 Verification Results:")
        print(f"   Valid: {verification['is_valid']}")
        print(f"   Quality: {verification['overall_quality']:.2f}")
        print(f"   Missing elements: {len(verification['missing_elements'])}")
        
        if verification['missing_elements']:
            print(f"\n❌ Issues found:")
            for issue in verification['missing_elements'][:3]:
                print(f"      - {issue}")
        
        if verification['improvement_suggestions']:
            print(f"\n💡 Suggestions:")
            for suggestion in verification['improvement_suggestions'][:3]:
                print(f"      - {suggestion}")
        
        # Auto-improve
        print(f"\n🔧 Applying automatic improvements...")
        improvement = self.mcp_server.improve_bpmn_process(test_process)
        
        print(f"   Changes made: {len(improvement['changes_made'])}")
        for change in improvement['changes_made']:
            print(f"      - {change}")
        
        # Re-verify improved version
        new_verification = self.mcp_server.verify_bpmn_process(improvement['improved_process'])
        print(f"   New quality: {new_verification['overall_quality']:.2f}")
        
        print(f"\n✅ MCP Server demo completed")
    
    def demo_iterative_improvement(self):
        """Demonstracja iteracyjnej poprawy"""
        print(f"\n{'='*60}")
        print("4️⃣ ITERATIVE IMPROVEMENT DEMO")
        print(f"{'='*60}")
        
        # Initialize iterative pipeline
        ai_config = get_default_config()
        self.iterative_pipeline = IterativeImprovementPipeline(
            ai_config=ai_config,
            max_iterations=10,
            target_quality=0.8
        )
        
        # Complex process that might need improvements
        complex_text = """
        Firma przeprowadza rekrutację nowego pracownika.
        HR publikuje ogłoszenie i otrzymuje CV.
        Menedżer przegląda aplikacje i wybiera kandydatów.
        Przeprowadzane są rozmowy kwalifikacyjne.
        Sprawdzane są referencje wybranych kandydatów.
        Podejmowana jest decyzja o zatrudnieniu.
        Nowy pracownik jest wprowadzany do firmy.
        """
        
        print(f"📝 Complex process for iterative improvement:")
        print(f"   {complex_text.strip()}")
        
        result = self.iterative_pipeline.generate_and_improve_process(
            polish_text=complex_text,
            process_name="Proces rekrutacji",
            context="generic"
        )
        
        if result['success']:
            # Generate and show report
            report = self.iterative_pipeline.generate_improvement_report(result)
            print(report)
        else:
            print(f"\n❌ Iterative improvement failed: {result.get('error')}")
    
    def demo_real_ai(self):
        """Demonstracja z prawdziwym AI (jeśli dostępne)"""
        print(f"\n{'='*60}")
        print("5️⃣ REAL AI DEMO")
        print(f"{'='*60}")
        
        # Check if real AI is available
        openai_available = os.getenv('OPENAI_API_KEY') is not None
        claude_available = os.getenv('ANTHROPIC_API_KEY') is not None
        
        if not (openai_available or claude_available):
            print(f"⚠️ Real AI not available (no API keys)")
            print(f"💡 To test with real AI:")
            print(f"   export OPENAI_API_KEY='your-openai-key'")
            print(f"   # or")
            print(f"   export ANTHROPIC_API_KEY='your-claude-key'")
            print(f"   # then run demo again")
            return
        
        print(f"🎉 Real AI available! Testing...")
        
        # Use real AI config
        real_config = OPENAI_GPT4 if openai_available else CLAUDE_SONNET
        real_pipeline = BPMNv2Pipeline(ai_config=real_config)
        
        # Simple test
        simple_text = "Klient loguje się i sprawdza swoje transakcje."
        
        try:
            result = real_pipeline.run_complete_pipeline(
                polish_text=simple_text,
                process_name="Test z prawdziwym AI",
                context="banking",
                save_artifacts=False
            )
            
            if result['success']:
                print(f"✅ Real AI test successful!")
                print(f"   Provider: {real_config.provider.value}")
                print(f"   Model: {real_config.model}")
                if result.get('ai_response'):
                    process_name = result['ai_response'].get('process_name', 'N/A')
                    elements_count = len(result['ai_response'].get('elements', []))
                    print(f"   Generated process: {process_name}")
                    print(f"   Elements: {elements_count}")
            else:
                print(f"❌ Real AI test failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Real AI error: {e}")
    
    def demo_summary(self):
        """Podsumowanie demo"""
        print(f"\n{'='*60}")
        print("6️⃣ DEMO SUMMARY")
        print(f"{'='*60}")
        
        print(f"""
🎯 BPMN v2 System Features Demonstrated:

✅ Basic Pipeline:
   - Polish text analysis
   - AI prompt generation  
   - JSON → BPMN conversion
   - XML output with layout

✅ MCP Server:
   - Process quality verification
   - Issue identification
   - Automatic improvements
   - Iterative enhancement

✅ AI Integration:
   - Multiple AI providers (OpenAI, Claude, Ollama)
   - Mock AI for testing
   - Error handling and fallbacks
   - Token usage tracking

✅ Quality Assurance:
   - JSON Schema validation
   - BPMN completeness checking
   - Missing element detection
   - Improvement suggestions

🚀 Ready for production use!
💡 Add real AI API keys for full functionality
""")
        
        # Show generated files
        print(f"\n📁 Generated files in bpmn_v2/:")
        import glob
        bpmn_files = glob.glob("*.bpmn")
        json_files = glob.glob("*_response.json")
        
        if bpmn_files:
            print(f"   BPMN files: {len(bpmn_files)}")
            for f in bpmn_files[-3:]:  # Show last 3
                print(f"      - {f}")
        
        if json_files:
            print(f"   JSON files: {len(json_files)}")
            for f in json_files[-3:]:  # Show last 3
                print(f"      - {f}")
        
        print(f"\n🎉 Demo completed successfully!")
    
    def _is_config_available(self, config) -> bool:
        """Sprawdza czy konfiguracja jest dostępna"""
        from ai_config import validate_config
        try:
            return validate_config(config)
        except:
            return False


def main():
    """Main demo function"""
    demo = BPMNv2Demo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()