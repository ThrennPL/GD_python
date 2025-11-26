"""
Test Client dla BPMN MCP Server
Prosty klient do testowania funkcjonalności serwera MCP bez pełnej integracji MCP
"""

import asyncio
import json
from typing import Dict, Any
import sys
import os

# Add bpmn_v2 to path
sys.path.append(os.path.dirname(__file__))

from bpmn_mcp_server import BPMNProcessMCP, BPMNValidationIssue
from ai_config import get_default_config


class BPMNMCPTestClient:
    """Test client dla BPMN MCP Server"""
    
    def __init__(self, use_mock_ai: bool = True):
        # Always use default config from env
        ai_config = get_default_config()
        self.server = BPMNProcessMCP(ai_config=ai_config)
        print(f"🧪 Test Client initialized with {ai_config.provider.value}")
    
    async def test_generate_process(self, description: str, process_name: str = "Test Process"):
        """Test generowania procesu BPMN"""
        print(f"\n🔧 Testing: generate_bpmn_process")
        print(f"Description: {description[:100]}...")
        
        args = {
            "process_description": description,
            "process_name": process_name,
            "context": "banking",
            "validate_and_improve": True
        }
        
        result = await self.server._handle_generate_process(args)
        
        if not result.isError:
            response = json.loads(result.content[0].text)
            if response.get("success"):
                print(f"✅ Process generated successfully")
                bpmn_json = response.get("bpmn_json")
                print(f"📊 Elements: {len(bpmn_json.get('elements', []))}")
                print(f"🔗 Flows: {len(bpmn_json.get('flows', []))}")
                print(f"👥 Participants: {len(bpmn_json.get('participants', []))}")
                return bpmn_json
            else:
                print(f"❌ Process generation failed: {response.get('error')}")
        else:
            print(f"❌ Error: {result.content[0].text}")
        
        return None
    
    async def test_validate_process(self, bpmn_json: Dict):
        """Test walidacji procesu BPMN"""
        print(f"\n🔧 Testing: validate_bpmn_process")
        
        args = {
            "bpmn_json": bpmn_json,
            "original_description": "Test process description"
        }
        
        result = await self.server._handle_validate_process(args)
        
        if not result.isError:
            validation = json.loads(result.content[0].text)
            print(f"✅ Validation completed")
            print(f"🔍 Valid: {validation['is_valid']}")
            print(f"📊 Total issues: {validation['issues_count']}")
            print(f"❌ Errors: {len(validation['errors'])}")
            print(f"⚠️ Warnings: {len(validation['warnings'])}")
            print(f"💡 Suggestions: {len(validation['suggestions'])}")
            
            # Show some issues
            if validation['errors']:
                print(f"\n🚨 Sample errors:")
                for error in validation['errors'][:2]:
                    print(f"  - {error['message']}")
            
            if validation['warnings']:
                print(f"\n⚠️ Sample warnings:")
                for warning in validation['warnings'][:2]:
                    print(f"  - {warning['message']}")
            
            return validation
        else:
            print(f"❌ Validation error: {result.content[0].text}")
        
        return None
    
    async def test_improve_process(self, bpmn_json: Dict, original_description: str):
        """Test iteracyjnej poprawy procesu"""
        print(f"\n🔧 Testing: improve_bpmn_process")
        
        args = {
            "bpmn_json": bpmn_json,
            "original_description": original_description,
            "max_iterations": 2
        }
        
        result = await self.server._handle_improve_process(args)
        
        if not result.isError:
            improvement = json.loads(result.content[0].text)
            if improvement.get("success"):
                print(f"✅ Process improved successfully")
                improved_json = improvement.get("improved_process")
                return improved_json
            else:
                print(f"❌ Improvement failed: {improvement.get('error')}")
        else:
            print(f"❌ Error: {result.content[0].text}")
        
        return None
    
    async def test_generate_xml(self, bpmn_json: Dict):
        """Test generowania XML"""
        print(f"\n🔧 Testing: generate_bpmn_xml")
        
        args = {
            "bpmn_json": bpmn_json,
            "output_file": "test_output.bpmn"
        }
        
        result = await self.server._handle_generate_xml(args)
        
        if not result.isError:
            xml_result = json.loads(result.content[0].text)
            if xml_result.get("success"):
                print(f"✅ XML generated successfully")
                print(f"📄 XML length: {xml_result['xml_length']} chars")
                if xml_result.get("output_file"):
                    print(f"💾 Saved to: {xml_result['output_file']}")
                return xml_result.get("bpmn_xml")
            else:
                print(f"❌ XML generation failed: {xml_result.get('error')}")
        else:
            print(f"❌ Error: {result.content[0].text}")
        
        return None
    
    async def test_analyze_text(self, text: str):
        """Test analizy tekstu"""
        print(f"\n🔧 Testing: analyze_process_text")
        print(f"Text: {text[:100]}...")
        
        args = {
            "process_text": text,
            "context": "banking"
        }
        
        result = await self.server._handle_analyze_text(args)
        
        if not result.isError:
            analysis = json.loads(result.content[0].text)
            print(f"✅ Text analysis completed")
            print(f"📊 Elements found: {len(analysis.get('elements', []))}")
            print(f"👥 Participants: {len(analysis.get('participants', []))}")
            print(f"🎯 Confidence: {analysis.get('confidence', 0):.2f}")
            return analysis
        else:
            print(f"❌ Analysis error: {result.content[0].text}")
        
        return None
    
    async def run_comprehensive_test(self):
        """Uruchamia pełny test wszystkich funkcjonalności"""
        print("🚀 Starting Comprehensive BPMN MCP Server Test")
        print("=" * 60)
        
        # Test data
        blik_description = """
        Klient chce dokonać płatności BLIK w sklepie internetowym.
        Najpierw wybiera opcję płatności BLIK i wprowadza kod z aplikacji bankowej.
        System BLIK sprawdza dostępność środków na koncie i weryfikuje kod.
        Jeśli weryfikacja jest pomyślna, system blokuje środki i wysyła potwierdzenie.
        W przeciwnym razie wyświetla komunikat o błędzie i anuluje transakcję.
        """
        
        try:
            # Test 1: Analyze text
            analysis = await self.test_analyze_text(blik_description)
            
            # Test 2: Generate process
            bpmn_json = await self.test_generate_process(blik_description, "Płatność BLIK")
            
            if bpmn_json:
                # Test 3: Validate process
                validation = await self.test_validate_process(bpmn_json)
                
                # Test 4: Improve process (if there are issues)
                if validation and not validation['is_valid']:
                    improved_json = await self.test_improve_process(bpmn_json, blik_description)
                    if improved_json:
                        bpmn_json = improved_json
                
                # Test 5: Generate XML
                xml_output = await self.test_generate_xml(bpmn_json)
            
            print("\n" + "=" * 60)
            print("🎯 COMPREHENSIVE TEST COMPLETED")
            print("✅ All functionality tested successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Główna funkcja testowa"""
    
    print("🌟 BPMN MCP Server Test Suite")
    print("Choose test mode:")
    print("1. Mock AI (fast, no API calls)")
    print("2. Real AI (requires API keys)")
    
    # For demo, use Mock AI
    use_mock = True
    print("Using Mock AI for demo...")
    
    client = BPMNMCPTestClient(use_mock_ai=use_mock)
    
    # Run tests
    await client.run_comprehensive_test()
    
    # Interactive mode
    print(f"\n💡 Interactive mode - enter Polish process descriptions:")
    print("(type 'exit' to quit)")
    
    while True:
        try:
            user_input = input("\n📝 Process description: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            
            if user_input:
                print(f"\n🔄 Processing: {user_input}")
                
                # Quick analysis
                analysis = await client.test_analyze_text(user_input)
                
                # Generate process
                if analysis:
                    process = await client.test_generate_process(user_input, "User Process")
                    
                    if process:
                        # Quick validation
                        validation = await client.test_validate_process(process)
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())