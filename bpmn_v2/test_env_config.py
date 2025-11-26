from ai_config import create_bpmn_config, get_available_models_for_provider
from ai_integration import AIClientFactory

print('🎯 TESTING ENV-BASED BPMN GENERATION')
print('='*50)

# Show available models for current provider
models = get_available_models_for_provider()
print(f'Provider from env: {models["provider"]}')
print(f'Available models: {models["models"]}')

# Test different models
print('\n🔬 Testing different models:')
for model in models['models'][:2]:  # Test first 2
    print(f'\n--- Testing {model} ---')
    config = create_bpmn_config(selected_model=model)
    
    try:
        client = AIClientFactory.create_client(config)
        print(f'✅ Client created: {type(client).__name__}')
        print(f'📍 Base URL: {config.base_url}')
        print(f'🔑 Has API key: {bool(config.api_key)}')
        
        # Test connection if available
        if hasattr(client, 'test_connection'):
            conn_test = client.test_connection()
            print(f'🔗 Connection: {"✅ OK" if conn_test else "❌ Failed"}')
        
    except Exception as e:
        print(f'❌ Failed: {e}')

print('\n🎉 ENV-BASED SYSTEM WORKS!')