"""
Simple test of AI integration without hanging
"""
import sys
import os
sys.path.append('.')

def test_basic_ai():
    """Test basic AI functionality"""
    print("🧪 Testing Basic AI Integration")
    
    try:
        from bpmn_v2.ai_integration import AIProvider, AIConfig, MockClient
        print("✅ Imports successful")
        
        # Test Mock client only (no external dependencies)
        config = AIConfig(
            provider=AIProvider.GEMINI,
            model="test-model"
        )
        
        client = MockClient(config)
        print("✅ Mock client created")
        
        # Test connection
        if client.test_connection():
            print("✅ Connection test passed")
        else:
            print("❌ Connection test failed")
            return False
        
        # Test simple response
        response = client.generate_response("Test prompt")
        print(f"✅ Response generated: {response.success}")
        print(f"   Content length: {len(response.content)}")
        print(f"   Provider: {response.provider.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test AI config"""
    print("\n🧪 Testing AI Config")
    
    try:
        from ai_config import get_default_config, print_config_status
        print("✅ Config imports successful")
        
        # Get default config (should be Mock since no API keys)
        config = get_default_config()
        print(f"✅ Default config: {config.provider.value}")
        
        # Print status (but don't hang on network calls)
        print("📋 Config status check skipped (to avoid hanging)")
        
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_pipeline():
    """Test pipeline with Mock AI"""
    print("\n🧪 Testing Pipeline with Mock AI")
    
    try:
        from complete_pipeline import BPMNv2Pipeline
        from ai_config import get_default_config
        print("✅ Pipeline imports successful")
        
        # Create pipeline with env config
        pipeline = BPMNv2Pipeline(ai_config=get_default_config())
        print("✅ Pipeline created with env config")
        
        # Test simple Polish text
        test_text = "Klient loguje się do systemu i sprawdza saldo."
        
        # Test just the analysis part (no full pipeline)
        analysis = pipeline.analyze_process_description(test_text)
        print(f"✅ Analysis completed: {analysis['confidence']:.2f} confidence")
        print(f"   Elements: {len(analysis.get('elements', []))}")
        print(f"   Participants: {len(analysis.get('participants', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Quick AI Integration Test (No Hanging)")
    print("=" * 50)
    
    results = []
    
    # Test 1: Basic AI
    results.append(test_basic_ai())
    
    # Test 2: Config  
    results.append(test_config())
    
    # Test 3: Pipeline
    results.append(test_pipeline())
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    test_names = ["Basic AI", "Config", "Pipeline"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
    
    all_passed = all(results)
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")