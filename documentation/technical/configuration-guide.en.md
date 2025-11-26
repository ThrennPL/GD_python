# Configuration Guide - GD System

## 📋 Configuration Overview

The GD system offers flexible configuration through environment variables, enabling adaptation to different environments and requirements. Configuration includes AI providers, BPMN quality settings, PDF analysis parameters, and environment options.

## 🔧 Basic Configuration

### 1. Environment file `.env`

Create an `.env` file in the project root directory:

```env
# AI Provider Configuration
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=your-google-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
CLAUDE_API_KEY=your-claude-api-key-here
OLLAMA_BASE_URL=http://localhost:11434

# Application Settings
LANGUAGE=en
API_DEFAULT_MODEL=models/gemini-2.0-flash
CHAT_URL=https://generativelanguage.googleapis.com/v1beta/models

# BPMN Quality Settings
BPMN_QUALITY_THRESHOLD=0.8
BPMN_MAX_ITERATIONS=10
BPMN_TIMEOUT_MINUTES=5

# PDF Analysis Settings
PDF_ANALYSIS_MODE=ai
PDF_ANALYSIS_MODEL=models/gemini-2.0-flash
PDF_ANALYSIS_PROMPT_LANG=en
PDF_DIRECT_THRESHOLD_MB=2.0
PDF_MAX_PAGES_TEXT=50
PDF_CHUNK_SIZE=4000

# Performance Settings
API_REQUEST_TIMEOUT=60
MAX_CONCURRENT_REQUESTS=5

# PlantUML Configuration
PLANTUML_JAR_PATH=plantuml.jar
PLANTUML_GENERATOR_TYPE=local

# Database Configuration (optional)
DB_PROVIDER=sqlite
DB_PATH=data/diagrams.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

---

## 🤖 AI Provider Configuration

### Google Gemini (Recommended)

**Best support for BPMN v2 and PDF analysis**

```env
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=AIzaSyC_example_key_here
API_DEFAULT_MODEL=models/gemini-2.0-flash
CHAT_URL=https://generativelanguage.googleapis.com/v1beta/models
```

**Available models:**
- `models/gemini-2.0-flash` - Latest, most efficient (recommended)
- `models/gemini-1.5-pro` - Advanced model with large context
- `models/gemini-1.5-flash` - Fast model for basic tasks

**Getting API key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in to Google account
3. Click "Create API Key"
4. Copy the generated key to `GOOGLE_API_KEY`

### OpenAI (GPT)

**High-quality generation with PDF limitations**

```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-example_key_here
API_DEFAULT_MODEL=gpt-4-turbo
CHAT_URL=https://api.openai.com/v1/chat/completions
```

**Available models:**
- `gpt-4-turbo` - Latest GPT-4 (recommended)
- `gpt-4` - Standard GPT-4
- `gpt-3.5-turbo` - Economical model

**Getting API key:**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in to OpenAI account
3. Click "Create new secret key"
4. Copy key to `OPENAI_API_KEY`

### Anthropic Claude

**Advanced reasoning and context analysis**

```env
MODEL_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-example_key_here
API_DEFAULT_MODEL=claude-3-5-sonnet-20241022
CHAT_URL=https://api.anthropic.com/v1/messages
```

**Available models:**
- `claude-3-5-sonnet-20241022` - Latest Sonnet (recommended)
- `claude-3-5-haiku-20241022` - Fast model
- `claude-3-opus-20240229` - Most advanced model

### Ollama (Local models)

**On-premise solution without API costs**

```env
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
API_DEFAULT_MODEL=llama3.1:8b
```

**Installing Ollama:**
1. Download from [https://ollama.ai/](https://ollama.ai/)
2. Install and run server
3. Download model: `ollama pull llama3.1:8b`

**Available models:**
- `llama3.1:8b` - Basic model (recommended for start)
- `llama3.1:70b` - Advanced model (requires more RAM)
- `codellama:7b` - Specialized in code

---

## ⚙️ BPMN v2 Configuration

### Quality parameters

```env
# Quality threshold (0.0-1.0)
BPMN_QUALITY_THRESHOLD=0.8

# Maximum optimization iterations
BPMN_MAX_ITERATIONS=10

# Process timeout (minutes)
BPMN_TIMEOUT_MINUTES=5

# Automatic validation
BPMN_AUTO_VALIDATE=true

# Automatic improvement
BPMN_AUTO_IMPROVE=true

# Save iteration history
BPMN_SAVE_ITERATIONS=true
```

### Quality levels - recommendations

| Quality threshold | Application | Time | Iterations |
|------------------|-------------|------|------------|
| **0.6**          | Prototypes, sketches | ~30s | 2-4 |
| **0.7**          | Working documentation | ~45s | 3-5 |
| **0.8**          | Standard production | ~65s | 4-7 |
| **0.9**          | Critical processes | ~85s | 6-10 |

### Process types

```env
# Default process type
BPMN_DEFAULT_PROCESS_TYPE=business

# Available types:
# - business: Business processes
# - technical: Technical processes
# - workflow: Work flows
# - integration: Integration processes
```

---

## 📄 PDF Analysis Configuration

### Analysis modes

```env
# PDF analysis mode
PDF_ANALYSIS_MODE=ai  # ai|local|hybrid

# Analysis model (if ai)
PDF_ANALYSIS_MODEL=models/gemini-2.0-flash

# Analysis prompt language
PDF_ANALYSIS_PROMPT_LANG=en  # pl|en
```

### Processing parameters

```env
# Size threshold for direct PDF processing (MB)
PDF_DIRECT_THRESHOLD_MB=2.0

# Maximum number of pages for text analysis
PDF_MAX_PAGES_TEXT=50

# Text chunk size
PDF_CHUNK_SIZE=4000

# Maximum PDF file size (MB)
PDF_MAX_FILE_SIZE_MB=50

# PDF analysis timeout (seconds)
PDF_ANALYSIS_TIMEOUT=120
```

### Models supporting direct PDF

| Provider | Model | Direct PDF | Text Fallback |
|----------|-------|------------|---------------|
| **Gemini** | gemini-2.0-flash | ✅ | ✅ |
| **Gemini** | gemini-1.5-pro | ✅ | ✅ |
| **Gemini** | gemini-1.5-flash | ✅ | ✅ |
| **OpenAI** | gpt-4* | ❌ | ✅ |
| **Claude** | claude-3* | ❌ | ✅ |
| **Ollama** | All models | ❌ | ✅ |

---

## 🌐 Application Configuration

### Language settings

```env
# Main interface language
LANGUAGE=en  # pl|en

# AI prompt language
PROMPT_LANGUAGE=en  # pl|en

# BPMN validation language
BPMN_VALIDATION_LANG=en  # pl|en
```

### PlantUML settings

```env
# Path to PlantUML JAR
PLANTUML_JAR_PATH=plantuml.jar

# PlantUML generator type
PLANTUML_GENERATOR_TYPE=local  # local|server

# PlantUML server URL (if server)
PLANTUML_SERVER_URL=http://localhost:8080/plantuml

# Rendering timeout (seconds)
PLANTUML_RENDER_TIMEOUT=30
```

### Performance settings

```env
# API request timeout (seconds)
API_REQUEST_TIMEOUT=60

# Maximum concurrent requests
MAX_CONCURRENT_REQUESTS=5

# Retry for failed requests
API_MAX_RETRIES=3

# Delay between retries (seconds)
API_RETRY_DELAY=2
```

---

## 🔧 Environment Configuration

### Development Configuration

```env
# Development settings
ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Mocks for testing
USE_MOCK_AI=false
MOCK_AI_DELAY=1

# Local paths
TEMP_DIR=temp/
LOGS_DIR=logs/
CACHE_DIR=cache/
```

### Production Configuration

```env
# Production settings
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Security
SECURE_COOKIES=true
SESSION_TIMEOUT=3600

# Performance
ENABLE_CACHING=true
CACHE_TTL=300
COMPRESS_RESPONSES=true

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Testing Configuration

```env
# Testing environment
ENV=testing
USE_MOCK_AI=true
MOCK_AI_DELAY=0.1

# Test databases
DB_PROVIDER=memory
TEST_DATA_DIR=test_files/

# Reduced timeouts for faster tests
API_REQUEST_TIMEOUT=10
BPMN_TIMEOUT_MINUTES=1
```

---

## 🖥️ Desktop vs Web Configuration

### Desktop Application (PyQt5)

```env
# Desktop specific
DESKTOP_THEME=dark  # dark|light|auto
DESKTOP_FONT_SIZE=12
DESKTOP_WINDOW_SIZE=1200x800

# File dialogs
DEFAULT_SAVE_DIR=output/
DEFAULT_LOAD_DIR=input/

# Editor settings
CODE_EDITOR_FONT=Consolas
CODE_EDITOR_THEME=monokai
```

### Web Application (Streamlit)

```env
# Streamlit specific
STREAMLIT_PORT=8501
STREAMLIT_HOST=localhost
STREAMLIT_THEME=dark

# Upload limits
MAX_UPLOAD_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf,txt,md

# Session management
SESSION_STATE_TTL=1800
MAX_SESSIONS=100
```

---

## 📊 Database Configuration

### SQLite (Default)

```env
DB_PROVIDER=sqlite
DB_PATH=data/diagrams.db
DB_BACKUP_DIR=backups/
DB_BACKUP_INTERVAL=24h
```

### PostgreSQL

```env
DB_PROVIDER=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gd_python
DB_USER=gd_user
DB_PASSWORD=secure_password
DB_SSL_MODE=require
```

### MySQL

```env
DB_PROVIDER=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gd_python
DB_USER=gd_user
DB_PASSWORD=secure_password
DB_CHARSET=utf8mb4
```

---

## 🚀 Configuration Profiles

### Profile: Rapid Prototyping

**Fast prototyping with low quality**

```env
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=your_key
API_DEFAULT_MODEL=models/gemini-1.5-flash

BPMN_QUALITY_THRESHOLD=0.6
BPMN_MAX_ITERATIONS=3
BPMN_TIMEOUT_MINUTES=2

PDF_ANALYSIS_MODE=local
```

### Profile: Production Standard

**Standard production with balanced quality**

```env
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=your_key
API_DEFAULT_MODEL=models/gemini-2.0-flash

BPMN_QUALITY_THRESHOLD=0.8
BPMN_MAX_ITERATIONS=10
BPMN_TIMEOUT_MINUTES=5

PDF_ANALYSIS_MODE=ai
ENABLE_CACHING=true
```

### Profile: High Quality

**High quality for critical processes**

```env
MODEL_PROVIDER=claude
CLAUDE_API_KEY=your_key
API_DEFAULT_MODEL=claude-3-5-sonnet-20241022

BPMN_QUALITY_THRESHOLD=0.9
BPMN_MAX_ITERATIONS=15
BPMN_TIMEOUT_MINUTES=10

PDF_ANALYSIS_MODE=ai
API_REQUEST_TIMEOUT=120
```

### Profile: On-Premise

**Local solution without external APIs**

```env
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
API_DEFAULT_MODEL=llama3.1:8b

BPMN_QUALITY_THRESHOLD=0.7
PDF_ANALYSIS_MODE=local
PLANTUML_GENERATOR_TYPE=local
```

---

## 🔍 Configuration Validation

### Checking configuration

Run the checking script:

```bash
python -m bpmn_v2.test_env_config
```

**Checked elements:**
- ✅ API key availability
- ✅ AI provider connection
- ✅ Model correctness
- ✅ PlantUML availability
- ✅ Directory permissions
- ✅ Python dependencies

### Problem diagnostics

**Problem: No AI response**
```bash
# Check API keys
echo $GOOGLE_API_KEY
echo $OPENAI_API_KEY

# Test connection
python -m tools.test_real_ai_call
```

**Problem: BPMN errors**
```bash
# Check BPMN configuration
python -c "from bpmn_v2.ai_config import create_bpmn_config; print(create_bpmn_config())"
```

**Problem: PDF errors**
```bash
# Test PDF analysis
python -m tools.analyze_pdf_quality
```

---

## 🔐 Configuration Security

### API key protection

1. **Never commit .env to repository**
```bash
echo ".env" >> .gitignore
```

2. **Use environment variables in production**
```bash
export GOOGLE_API_KEY="your_key_here"
```

3. **Key rotation**
- Change API keys regularly
- Use different keys for different environments
- Monitor key usage

### Sensitive data encryption

```env
# Optional local data encryption
ENCRYPT_LOCAL_DATA=true
ENCRYPTION_KEY=your_encryption_key

# Secure file permissions
FILE_PERMISSIONS=600
DIR_PERMISSIONS=700
```

---

## 🧪 Configuration Testing

### Configuration test suite

```bash
# Test all components
python -m tests.test_configuration

# Test specific provider
python -m tests.test_ai_providers --provider gemini

# Test BPMN pipeline
python -m tests.test_bpmn_pipeline

# Test PDF analysis
python -m tests.test_pdf_analysis
```

### Configuration metrics

```bash
# Performance analysis
python -m tools.benchmark_configuration

# API cost report
python -m tools.api_cost_analysis
```

---

## 📚 Configuration Examples

### Configuration for development team

```env
# Team Development Configuration
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=shared_dev_key
API_DEFAULT_MODEL=models/gemini-1.5-flash

# Moderate quality for speed
BPMN_QUALITY_THRESHOLD=0.7
BPMN_MAX_ITERATIONS=7

# Shared resources
PDF_ANALYSIS_MODE=ai
PLANTUML_GENERATOR_TYPE=server
PLANTUML_SERVER_URL=http://dev-plantuml:8080

# Development aids
DEBUG=true
LOG_LEVEL=DEBUG
USE_MOCK_AI=false
```

### Configuration for demonstrations

```env
# Demo Configuration
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=demo_key
API_DEFAULT_MODEL=models/gemini-2.0-flash

# High quality for impressive results
BPMN_QUALITY_THRESHOLD=0.85
BPMN_MAX_ITERATIONS=8

# Visual settings
DESKTOP_THEME=light
STREAMLIT_THEME=light
LANGUAGE=en

# Optimized for demos
API_REQUEST_TIMEOUT=90
ENABLE_CACHING=true
```

This guide covers all configuration aspects of the GD system. For specific use cases, consult the API Reference documentation or contact the development team.