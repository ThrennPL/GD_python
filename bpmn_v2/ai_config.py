"""
AI Configuration Settings
Konfiguracja różnych dostawców AI dla BPMN v2
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from parent directory .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    print(f"🔧 Loaded env from: {env_path}")
except ImportError:
    print("⚠️ python-dotenv not installed, using system env variables only")

from ai_integration import AIProvider, AIConfig

# =============================================================================
# KONFIGURACJA DYNAMICZNA BAZUJĄCA NA .ENV
# =============================================================================

def _get_provider_from_env() -> AIProvider:
    """Mapuje MODEL_PROVIDER z env na AIProvider enum"""
    provider_map = {
        'gemini': AIProvider.GEMINI,
        'openai': AIProvider.OPENAI,
        'local': AIProvider.OLLAMA,  # local = Ollama
        'claude': AIProvider.CLAUDE,
        'ollama': AIProvider.OLLAMA
    }
    
    model_provider = os.getenv('MODEL_PROVIDER', 'gemini').lower()
    return provider_map.get(model_provider, AIProvider.GEMINI)

def create_bpmn_config(selected_model: str = None) -> AIConfig:
    """Tworzy konfigurację BPMN na podstawie parametrów env i wybranego modelu"""
    provider = _get_provider_from_env()
    
    # Model: z GUI selection lub z env jako fallback
    model = selected_model or os.getenv('API_DEFAULT_MODEL', 'models/gemini-2.0-flash')
    
    # API key w zależności od providera
    if provider == AIProvider.GEMINI:
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('API_KEY')
    elif provider == AIProvider.OPENAI:
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('API_KEY')
    elif provider == AIProvider.CLAUDE:
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('API_KEY')
    else:
        api_key = os.getenv('API_KEY')
    
    # Base URL z env
    base_url = os.getenv('CHAT_URL')
    
    # Temperature dla BPMN (niższa dla bardziej strukturalnych wyników)
    temperature = 0.3
    if provider == AIProvider.GEMINI:
        temperature = 0.7  # Gemini lubi wyższą temperature
    
    return AIConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=4000,
        timeout=30
    )

def create_pdf_config() -> AIConfig:
    """Oddzielna konfiguracja dla analizy PDF"""
    # PDF używa własnych parametrów z env
    pdf_mode = os.getenv('PDF_ANALYSIS_MODE', 'ai')
    
    if pdf_mode == 'ai':
        model = os.getenv('PDF_ANALYSIS_MODEL', 'models/gemini-2.0-flash')
        
        # Dla PDF zawsze używamy Gemini (najlepsze OCR)
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('API_KEY')
        
        return AIConfig(
            provider=AIProvider.GEMINI,
            model=model,
            api_key=api_key,
            base_url=os.getenv('CHAT_URL'),
            temperature=0.4,  # Średnia temperature dla OCR
            max_tokens=4000,
            timeout=30
        )
    else:
        # Local PDF analysis - używamy lokalny model
        return AIConfig(
            provider=AIProvider.OLLAMA,
            model='llama2',
            base_url='http://localhost:11434',
            temperature=0.4,
            max_tokens=4000,
            timeout=60
        )



# =============================================================================
# KONFIGURACJA DOMYŚLNA
# =============================================================================

def get_default_config() -> AIConfig:
    """
    Zwraca domyślną konfigurację BPMN na podstawie parametrów env
    """
    config = create_bpmn_config()
    print(f"🤖 Using {config.provider.value} provider from env (MODEL_PROVIDER)")
    print(f"🔗 Base URL: {config.base_url}")
    print(f"📱 Model: {config.model}")
    return config


def get_available_models_for_provider() -> dict:
    """Zwraca dostępne modele dla aktualnego providera z env"""
    provider = _get_provider_from_env()
    
    model_options = {
        AIProvider.GEMINI: [
            'models/gemini-2.0-flash',
            'models/gemini-1.5-pro',
            'models/gemini-1.5-flash'
        ],
        AIProvider.OPENAI: [
            'gpt-4',
            'gpt-4-turbo-preview', 
            'gpt-3.5-turbo'
        ],
        AIProvider.CLAUDE: [
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307'
        ],
        AIProvider.OLLAMA: [
            'llama2',
            'mistral',
            'codellama'
        ]
    }
    
    return {
        'provider': provider.value,
        'models': model_options.get(provider, [])
    }


def validate_config(config: AIConfig) -> bool:
    """
    Waliduje konfigurację AI
    """
    if config.provider == AIProvider.OPENAI:
        return config.api_key is not None or os.getenv('OPENAI_API_KEY') is not None
    
    elif config.provider == AIProvider.CLAUDE:
        return config.api_key is not None or os.getenv('ANTHROPIC_API_KEY') is not None
    
    elif config.provider == AIProvider.GEMINI:
        return config.api_key is not None or os.getenv('GOOGLE_API_KEY') is not None
    
    elif config.provider == AIProvider.OLLAMA:
        # Check if Ollama is running
        try:
            import requests
            url = config.base_url or "http://localhost:11434"
            response = requests.get(f"{url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    return False


# =============================================================================
# ENVIRONMENT SETUP HELPERS  
# =============================================================================

def setup_openai_env(api_key: str):
    """Ustawia zmienną środowiskową dla OpenAI"""
    os.environ['OPENAI_API_KEY'] = api_key
    print("✅ OpenAI API key set")


def setup_claude_env(api_key: str):
    """Ustawia zmienną środowiskową dla Claude"""
    os.environ['ANTHROPIC_API_KEY'] = api_key
    print("✅ Claude API key set")


def print_config_status():
    """Wyświetla status aktualnej konfiguracji z env"""
    print("\n📋 AI Configuration Status (from .env):")
    print("-" * 50)
    
    # Pokaż env variables
    print(f"MODEL_PROVIDER: {os.getenv('MODEL_PROVIDER', 'not set')}")
    print(f"CHAT_URL: {os.getenv('CHAT_URL', 'not set')}")
    print(f"API_DEFAULT_MODEL: {os.getenv('API_DEFAULT_MODEL', 'not set')}")
    
    print("\n🔧 Current Configuration:")
    try:
        bpmn_config = create_bpmn_config()
        pdf_config = create_pdf_config()
        
        print(f"BPMN: {bpmn_config.provider.value} - {bpmn_config.model}")
        print(f"PDF:  {pdf_config.provider.value} - {pdf_config.model}")
        
        # Test validation
        bpmn_valid = validate_config(bpmn_config)
        pdf_valid = validate_config(pdf_config)
        
        print(f"\nValidation:")
        print(f"BPMN Config: {'✅ Valid' if bpmn_valid else '❌ Invalid'}")
        print(f"PDF Config:  {'✅ Valid' if pdf_valid else '❌ Invalid'}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    print("-" * 50)


if __name__ == "__main__":
    print_config_status()