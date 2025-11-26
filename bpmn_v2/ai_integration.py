"""
BPMN v2 - AI Integration
Integracja z rzeczywistymi API AI (OpenAI, Claude, Ollama)

Ten moduł zawiera:
1. Abstract AI Client interface
2. OpenAI client implementation  
3. Claude client implementation
4. Local Ollama client implementation
5. Response parsing and error handling
"""

import json
import os
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests

# Try to import aiohttp (optional for async operations)
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None

# Try to import OpenAI (optional dependency)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    openai = None

# Try to import Anthropic (optional dependency)
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    anthropic = None


class AIProvider(Enum):
    """Dostępni dostawcy AI"""
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    LOCAL = "local"  # LLM Studio


@dataclass
class AIConfig:
    """Konfiguracja AI"""
    provider: AIProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # For Ollama or custom endpoints
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 30
    
    @classmethod
    def from_main_app_env(cls, api_key: str, model_provider: str, chat_url: Optional[str] = None, 
                         default_model: Optional[str] = None) -> 'AIConfig':
        """Tworzy konfigurację z parametrów głównej aplikacji"""
        
        # Import fresh to avoid stale references  
        from bpmn_v2.ai_integration import AIProvider as FreshAIProvider
        
        provider_map = {
            "openai": FreshAIProvider.OPENAI,
            "claude": FreshAIProvider.CLAUDE,
            "ollama": FreshAIProvider.OLLAMA,
            "gemini": FreshAIProvider.GEMINI,
            "local": FreshAIProvider.LOCAL
        }
        
        provider = provider_map.get(model_provider.lower(), FreshAIProvider.GEMINI)
        
        # Use default model if provided, otherwise use provider defaults
        if default_model:
            model = default_model
        elif provider == FreshAIProvider.OPENAI:
            model = "gpt-4"
        elif provider == FreshAIProvider.CLAUDE:
            model = "claude-3-sonnet-20240229"
        elif provider == FreshAIProvider.OLLAMA:
            model = "llama2"
        elif provider == FreshAIProvider.GEMINI:
            model = "models/gemini-2.0-flash"
        elif provider == FreshAIProvider.LOCAL:
            model = "google/gemma-3-4b"  # Default local model
        else:
            model = "models/gemini-2.0-flash"  # fallback
            
        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=chat_url,
            temperature=0.7,
            max_tokens=4000,
            timeout=30
        )


@dataclass 
class AIResponse:
    """Odpowiedź od AI"""
    content: str
    model: str
    provider: AIProvider
    usage: Optional[Dict] = None
    metadata: Optional[Dict] = None
    success: bool = True
    error: Optional[str] = None


class AIClientInterface(ABC):
    """Abstract interface dla klientów AI"""
    
    @abstractmethod
    def __init__(self, config: AIConfig):
        pass
    
    @abstractmethod
    def generate_response(self, prompt: str) -> AIResponse:
        """Generuje odpowiedź synchronicznie"""
        pass
    
    @abstractmethod
    async def generate_response_async(self, prompt: str) -> AIResponse:
        """Generuje odpowiedź asynchronicznie"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Testuje połączenie z API"""
        pass


class OpenAIClient(AIClientInterface):
    """Klient OpenAI (obsługuje też lokalne modele z kompatybilnym API)"""
    
    def __init__(self, config: AIConfig):
        if not HAS_OPENAI:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        self.config = config
        
        # Determine if this is local or OpenAI based on config
        if config.provider == AIProvider.LOCAL:
            # Local LLM Studio - no API key needed, use base_url
            self.client = openai.OpenAI(
                api_key="local-model",  # Dummy key for local
                base_url=config.base_url or "http://localhost:1234/v1"
            )
            self.is_local = True
        else:
            # OpenAI proper
            self.client = openai.OpenAI(
                api_key=config.api_key or os.getenv('OPENAI_API_KEY'),
                base_url=config.base_url
            )
            self.is_local = False
        
        self.model = config.model or ("google/gemma-3-4b" if self.is_local else "gpt-4")
        
        provider_name = "Local LLM" if self.is_local else "OpenAI"
        print(f"🤖 {provider_name} Client initialized (model: {self.model})")
    
    def generate_response(self, prompt: str) -> AIResponse:
        """Generuje odpowiedź od OpenAI lub lokalnego modelu"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem od procesów biznesowych BPMN. Odpowiadaj zgodnie z podanym JSON Schema."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            content = response.choices[0].message.content
            
            # Usage info may not be available for local models
            usage = {}
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                }
            
            return AIResponse(
                content=content,
                model=self.model,
                provider=self.config.provider,  # Will be OPENAI or LOCAL
                usage=usage,
                success=True
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model=self.model,
                provider=self.config.provider,
                success=False,
                error=str(e)
            )
    
    async def generate_response_async(self, prompt: str) -> AIResponse:
        """Asynchroniczna wersja (używa sync client w thread pool)"""
        import concurrent.futures
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.generate_response, prompt)
    
    def test_connection(self) -> bool:
        """Testuje połączenie z OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"❌ OpenAI connection test failed: {e}")
            return False


class ClaudeClient(AIClientInterface):
    """Klient Anthropic Claude"""
    
    def __init__(self, config: AIConfig):
        if not HAS_ANTHROPIC:
            raise ImportError("Anthropic library not installed. Run: pip install anthropic")
        
        self.config = config
        self.client = anthropic.Anthropic(
            api_key=config.api_key or os.getenv('ANTHROPIC_API_KEY')
        )
        
        # Default models for Claude
        self.model = config.model or "claude-3-sonnet-20240229"
        
        print(f"🤖 Claude Client initialized (model: {self.model})")
    
    def generate_response(self, prompt: str) -> AIResponse:
        """Generuje odpowiedź od Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system="Jesteś ekspertem od procesów biznesowych BPMN. Odpowiadaj zgodnie z podanym JSON Schema.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            return AIResponse(
                content=content,
                model=self.model,
                provider=AIProvider.CLAUDE,
                usage=usage,
                success=True
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model=self.model,
                provider=AIProvider.CLAUDE,
                success=False,
                error=str(e)
            )
    
    async def generate_response_async(self, prompt: str) -> AIResponse:
        """Asynchroniczna wersja"""
        import concurrent.futures
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.generate_response, prompt)
    
    def test_connection(self) -> bool:
        """Testuje połączenie z Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}]
            )
            return True
        except Exception as e:
            print(f"❌ Claude connection test failed: {e}")
            return False


class OllamaClient(AIClientInterface):
    """Klient dla lokalnego Ollama"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"
        self.model = config.model or "llama2"
        
        print(f"🤖 Ollama Client initialized (model: {self.model}, url: {self.base_url})")
    
    def generate_response(self, prompt: str) -> AIResponse:
        """Generuje odpowiedź od Ollama"""
        try:
            url = f"{self.base_url}/api/generate"
            
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            }
            
            response = requests.post(
                url, 
                json=data, 
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("response", "")
            
            return AIResponse(
                content=content,
                model=self.model,
                provider=AIProvider.OLLAMA,
                metadata={"eval_count": result.get("eval_count")},
                success=True
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model=self.model,
                provider=AIProvider.OLLAMA,
                success=False,
                error=str(e)
            )
    
    async def generate_response_async(self, prompt: str) -> AIResponse:
        """Asynchroniczna wersja dla Ollama"""
        if not HAS_AIOHTTP:
            # Fallback to sync version in thread pool
            import concurrent.futures
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return await loop.run_in_executor(executor, self.generate_response, prompt)
        
        try:
            url = f"{self.base_url}/api/generate"
            
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    json=data, 
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    content = result.get("response", "")
                    
                    return AIResponse(
                        content=content,
                        model=self.model,
                        provider=AIProvider.OLLAMA,
                        metadata={"eval_count": result.get("eval_count")},
                        success=True
                    )
                    
        except Exception as e:
            return AIResponse(
                content="",
                model=self.model,
                provider=AIProvider.OLLAMA,
                success=False,
                error=str(e)
            )
    
    def test_connection(self) -> bool:
        """Testuje połączenie z Ollama"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            if self.model in model_names:
                print(f"✅ Ollama model '{self.model}' found")
                return True
            else:
                print(f"⚠️ Model '{self.model}' not found. Available: {model_names}")
                return False
                
        except Exception as e:
            print(f"❌ Ollama connection test failed: {e}")
            return False


class AIClientFactory:
    """Factory do tworzenia klientów AI"""
    
    @staticmethod
    def create_client(config: AIConfig) -> AIClientInterface:
        """Tworzy odpowiedni klient AI"""
        
        # Use global AIProvider 
        if config.provider == AIProvider.OPENAI:
            return OpenAIClient(config)
        elif config.provider == AIProvider.LOCAL:
            return OpenAIClient(config)  # Same client, different config
        elif config.provider == AIProvider.CLAUDE:
            return ClaudeClient(config)
        elif config.provider == AIProvider.OLLAMA:
            return OllamaClient(config)
        elif config.provider == AIProvider.GEMINI:
            return GeminiClient(config)
        else:
            # Force Gemini if no valid provider
            print(f"⚠️ Unsupported provider {config.provider}, forcing Gemini...")
            gemini_config = AIConfig(
                provider=AIProvider.GEMINI,
                model="models/gemini-2.0-flash",
                api_key=config.api_key or os.getenv('GOOGLE_API_KEY'),
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout
            )
            return GeminiClient(gemini_config)
    
    @staticmethod
    def get_available_providers() -> List[AIProvider]:
        """Zwraca listę dostępnych dostawców"""
        providers = [AIProvider.OLLAMA, AIProvider.LOCAL]  # Always available
        
        if HAS_OPENAI:
            providers.append(AIProvider.OPENAI)
        if HAS_ANTHROPIC:
            providers.append(AIProvider.CLAUDE)
        if HAS_GEMINI:
            providers.append(AIProvider.GEMINI)
        
        return providers


# Try to import Gemini (optional dependency)
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    genai = None


class GeminiClient(AIClientInterface):
    """Klient Google Gemini"""
    
    def __init__(self, config: AIConfig):
        if not HAS_GEMINI:
            raise ImportError("Google GenerativeAI library not installed. Run: pip install google-generativeai")
        
        self.config = config
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(config.model)
    
    def generate_response(self, prompt: str) -> AIResponse:
        """Generuje odpowiedź synchronicznie"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens,
                )
            )
            
            content = response.text if hasattr(response, 'text') and response.text else str(response)
            
            return AIResponse(
                content=content,
                model=self.config.model,
                provider=AIProvider.GEMINI,
                usage={"input_tokens": 0, "output_tokens": len(content.split())},  # Approximate
                metadata={"response_object": response},
                success=True
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model=self.config.model,
                provider=AIProvider.GEMINI,
                success=False,
                error=str(e)
            )
    
    async def generate_response_async(self, prompt: str) -> AIResponse:
        """Generuje odpowiedź asynchronicznie"""
        # For now, just wrap sync call
        # TODO: Implement true async when Gemini SDK supports it
        return self.generate_response(prompt)
    
    def test_connection(self) -> bool:
        """Testuje połączenie z API"""
        try:
            test_response = self.generate_response("Test connection")
            return test_response.success
        except:
            return False


class ResponseParser:
    """Parser odpowiedzi AI do formatu JSON"""
    
    @staticmethod
    def extract_json(ai_response: AIResponse) -> Tuple[bool, Optional[Dict], List[str]]:
        """
        Wyciąga JSON z odpowiedzi AI
        
        Returns:
            Tuple (success, json_data, errors)
        """
        if not ai_response.success:
            return False, None, [f"AI Error: {ai_response.error}"]
        
        content = ai_response.content.strip()
        errors = []
        
        try:
            # Try direct JSON parsing first
            json_data = json.loads(content)
            return True, json_data, []
        
        except json.JSONDecodeError:
            # Try to extract JSON from markdown or text
            json_blocks = ResponseParser._extract_json_blocks(content)
            
            for block in json_blocks:
                try:
                    json_data = json.loads(block)
                    return True, json_data, []
                except json.JSONDecodeError:
                    continue
            
            # No valid JSON found
            errors.append("No valid JSON found in AI response")
            errors.append(f"Response content: {content[:200]}...")
            
            return False, None, errors
    
    @staticmethod
    def _extract_json_blocks(text: str) -> List[str]:
        """Wyciąga bloki JSON z tekstu"""
        import re
        
        # Look for JSON in code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return matches
        
        # Look for standalone JSON objects
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        return matches


if __name__ == "__main__":
    """Test AI integration"""
    print("🧪 Testing AI Integration")
    
    # Test available providers
    print(f"\n📋 Available providers: {[p.value for p in AIClientFactory.get_available_providers()]}")
    
    # Test default client from env
    print(f"\n🤖 Testing Default Client (from env):")
    from ai_config import get_default_config
    
    default_config = get_default_config()
    client = AIClientFactory.create_client(default_config)
    print(f"Provider: {default_config.provider.value}")
    print(f"Model: {default_config.model}")
    print(f"Connection test: {client.test_connection()}")
    print(f"Response length: {len(response.content)} chars")
    
    # Test JSON parsing
    success, json_data, errors = ResponseParser.extract_json(response)
    print(f"JSON parsing success: {success}")
    if success:
        print(f"Process name: {json_data.get('process_name')}")
        print(f"Elements count: {len(json_data.get('elements', []))}")
    else:
        print(f"Parse errors: {errors}")
    
    print(f"\n✅ AI Integration test completed")