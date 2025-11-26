"""
Configuration file for BPMN MCP Server
Konfiguracja serwera MCP dla BPMN z różnymi trybami działania
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from bpmn_v2.ai_config import AIConfig, AIProvider, get_default_config


@dataclass
class MCPServerConfig:
    """Konfiguracja serwera MCP"""
    
    # Server settings
    name: str = "bpmn-process-mcp"
    version: str = "2.0.0"
    port: int = 8000
    host: str = "localhost"
    
    # AI configuration
    ai_config: Optional[AIConfig] = None
    
    # Validation settings
    enable_validation: bool = True
    enable_auto_improvement: bool = True
    max_improvement_iterations: int = 3
    
    # Process settings
    default_context: str = "banking"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Performance
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 60


# Predefiniowane konfiguracje
DEVELOPMENT_CONFIG = MCPServerConfig(
    name="bpmn-dev-mcp",
    ai_config=None,  # Użyje get_default_config()
    enable_validation=True,
    enable_auto_improvement=True,
    max_improvement_iterations=2,
    log_level="DEBUG",
    max_concurrent_requests=5
)

PRODUCTION_CONFIG = MCPServerConfig(
    name="bpmn-prod-mcp", 
    ai_config=None,  # Będzie ustawione z env vars
    enable_validation=True,
    enable_auto_improvement=True,
    max_improvement_iterations=3,
    log_level="INFO",
    log_file="bpmn_mcp.log",
    max_concurrent_requests=20,
    request_timeout_seconds=120
)

TESTING_CONFIG = MCPServerConfig(
    name="bpmn-test-mcp",
    ai_config=AIConfig(
        provider=AIProvider.GEMINI,
        model="mock-bpmn-expert"
    ),
    enable_validation=True,
    enable_auto_improvement=False,  # Skip for faster tests
    max_improvement_iterations=1,
    log_level="DEBUG",
    cache_enabled=False,  # Fresh results for each test
    max_concurrent_requests=1
)

# Quick access configs
CONFIGS = {
    "development": DEVELOPMENT_CONFIG,
    "production": PRODUCTION_CONFIG, 
    "testing": TESTING_CONFIG
}


def get_config(environment: str = "development") -> MCPServerConfig:
    """
    Zwraca konfigurację dla danego środowiska
    
    Args:
        environment: "development", "production", "testing"
    """
    
    config = CONFIGS.get(environment)
    if not config:
        raise ValueError(f"Unknown environment: {environment}. Available: {list(CONFIGS.keys())}")
    
    # Set AI config if not specified
    if config.ai_config is None:
        config.ai_config = get_default_config()
    
    return config


def get_config_from_env() -> MCPServerConfig:
    """
    Tworzy konfigurację na podstawie zmiennych środowiskowych
    """
    
    # Base configuration
    config = MCPServerConfig()
    
    # Override from environment
    config.port = int(os.getenv("BPMN_MCP_PORT", "8000"))
    config.host = os.getenv("BPMN_MCP_HOST", "localhost")
    config.log_level = os.getenv("BPMN_MCP_LOG_LEVEL", "INFO")
    config.log_file = os.getenv("BPMN_MCP_LOG_FILE")
    
    # AI configuration from env
    ai_provider = os.getenv("BPMN_MCP_AI_PROVIDER", "").lower()
    ai_model = os.getenv("BPMN_MCP_AI_MODEL")
    ai_key = os.getenv("BPMN_MCP_AI_API_KEY")
    
    if ai_provider and ai_model:
        try:
            provider = AIProvider(ai_provider)
            config.ai_config = AIConfig(
                provider=provider,
                model=ai_model,
                api_key=ai_key
            )
        except ValueError:
            print(f"⚠️ Unknown AI provider: {ai_provider}, using default")
            config.ai_config = get_default_config()
    else:
        config.ai_config = get_default_config()
    
    # Feature flags
    config.enable_validation = os.getenv("BPMN_MCP_ENABLE_VALIDATION", "true").lower() == "true"
    config.enable_auto_improvement = os.getenv("BPMN_MCP_ENABLE_AUTO_IMPROVEMENT", "true").lower() == "true"
    config.max_improvement_iterations = int(os.getenv("BPMN_MCP_MAX_ITERATIONS", "10"))
    
    # Performance settings
    config.max_concurrent_requests = int(os.getenv("BPMN_MCP_MAX_CONCURRENT", "10"))
    config.request_timeout_seconds = int(os.getenv("BPMN_MCP_TIMEOUT", "60"))
    
    # Cache settings
    config.cache_enabled = os.getenv("BPMN_MCP_CACHE_ENABLED", "true").lower() == "true"
    config.cache_ttl_seconds = int(os.getenv("BPMN_MCP_CACHE_TTL", "3600"))
    
    return config


def print_config_summary(config: MCPServerConfig):
    """Wyświetla podsumowanie konfiguracji"""
    
    print(f"\n📋 BPMN MCP Server Configuration")
    print(f"{'='*50}")
    print(f"🏷️  Name: {config.name}")
    print(f"🔢 Version: {config.version}")
    print(f"🌐 Address: {config.host}:{config.port}")
    print(f"🤖 AI Provider: {config.ai_config.provider.value if config.ai_config else 'None'}")
    print(f"🤖 AI Model: {config.ai_config.model if config.ai_config else 'None'}")
    print(f"✅ Validation: {'Enabled' if config.enable_validation else 'Disabled'}")
    print(f"🔄 Auto-improve: {'Enabled' if config.enable_auto_improvement else 'Disabled'}")
    print(f"🔁 Max iterations: {config.max_improvement_iterations}")
    print(f"💾 Cache: {'Enabled' if config.cache_enabled else 'Disabled'}")
    print(f"🔊 Log level: {config.log_level}")
    print(f"⚡ Max concurrent: {config.max_concurrent_requests}")
    print(f"{'='*50}")


def validate_config(config: MCPServerConfig) -> bool:
    """
    Waliduje konfigurację serwera
    
    Returns:
        True jeśli konfiguracja jest poprawna
    """
    
    issues = []
    
    # Check AI config
    if not config.ai_config:
        issues.append("❌ AI configuration is missing")
    else:
        # Validate AI config
        from ai_config import validate_config
        if not validate_config(config.ai_config):
            issues.append(f"❌ AI configuration invalid: {config.ai_config.provider.value}")
    
    # Check port
    if not (1024 <= config.port <= 65535):
        issues.append(f"❌ Invalid port: {config.port} (should be 1024-65535)")
    
    # Check iterations
    if config.max_improvement_iterations < 0 or config.max_improvement_iterations > 10:
        issues.append(f"❌ Invalid max iterations: {config.max_improvement_iterations} (should be 0-10)")
    
    # Check concurrent requests
    if config.max_concurrent_requests < 1 or config.max_concurrent_requests > 100:
        issues.append(f"❌ Invalid max concurrent: {config.max_concurrent_requests} (should be 1-100)")
    
    # Check timeout
    if config.request_timeout_seconds < 10 or config.request_timeout_seconds > 300:
        issues.append(f"❌ Invalid timeout: {config.request_timeout_seconds}s (should be 10-300s)")
    
    if issues:
        print(f"\n🚨 Configuration validation failed:")
        for issue in issues:
            print(f"  {issue}")
        return False
    
    print(f"✅ Configuration validation passed")
    return True


# Environment variable template
ENV_TEMPLATE = """
# BPMN MCP Server Environment Variables

# Server settings
BPMN_MCP_PORT=8000
BPMN_MCP_HOST=localhost
BPMN_MCP_LOG_LEVEL=INFO
# BPMN_MCP_LOG_FILE=bpmn_mcp.log

# AI Configuration (choose one provider)
# For OpenAI:
# BPMN_MCP_AI_PROVIDER=openai
# BPMN_MCP_AI_MODEL=gpt-4
# BPMN_MCP_AI_API_KEY=your-openai-key

# For Claude:
# BPMN_MCP_AI_PROVIDER=claude
# BPMN_MCP_AI_MODEL=claude-3-sonnet-20240229
# BPMN_MCP_AI_API_KEY=your-claude-key

# For Ollama (local):
# BPMN_MCP_AI_PROVIDER=ollama
# BPMN_MCP_AI_MODEL=llama2

# Feature flags
BPMN_MCP_ENABLE_VALIDATION=true
BPMN_MCP_ENABLE_AUTO_IMPROVEMENT=true
BPMN_MCP_MAX_ITERATIONS=10

# Performance
BPMN_MCP_MAX_CONCURRENT=10
BPMN_MCP_TIMEOUT=60

# Cache
BPMN_MCP_CACHE_ENABLED=true
BPMN_MCP_CACHE_TTL=3600
"""


if __name__ == "__main__":
    print("🧪 Testing BPMN MCP Server Configurations")
    
    # Test all predefined configs
    for env_name, config in CONFIGS.items():
        print(f"\n🔧 Testing {env_name} configuration:")
        print_config_summary(config)
        is_valid = validate_config(config)
        print(f"✅ Valid: {is_valid}")
    
    # Test environment config
    print(f"\n🌍 Environment-based configuration:")
    env_config = get_config_from_env()
    print_config_summary(env_config)
    validate_config(env_config)
    
    # Show environment template
    print(f"\n📄 Environment variables template:")
    print(ENV_TEMPLATE)