# Przewodnik Konfiguracji - System GD_python

## 📋 Przegląd Konfiguracji

System GD_python oferuje elastyczną konfigurację przez zmienne środowiskowe, umożliwiając adaptację do różnych środowisk i wymagań. Konfiguracja obejmuje providerów AI, ustawienia jakości BPMN, parametry analizy PDF oraz opcje środowiska.

## 🔧 Konfiguracja Podstawowa

### 1. Plik środowiskowy `.env`

Utwórz plik `.env` w katalogu głównym projektu:

```env
# AI Provider Configuration
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=your-google-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
CLAUDE_API_KEY=your-claude-api-key-here
OLLAMA_BASE_URL=http://localhost:11434

# Application Settings
LANGUAGE=pl
API_DEFAULT_MODEL=models/gemini-2.0-flash
CHAT_URL=https://generativelanguage.googleapis.com/v1beta/models

# BPMN Quality Settings
BPMN_QUALITY_THRESHOLD=0.8
BPMN_MAX_ITERATIONS=10
BPMN_TIMEOUT_MINUTES=5

# PDF Analysis Settings
PDF_ANALYSIS_MODE=ai
PDF_ANALYSIS_MODEL=models/gemini-2.0-flash
PDF_ANALYSIS_PROMPT_LANG=pl
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

## 🤖 Konfiguracja Providerów AI

### Google Gemini (Zalecany)

**Najlepsze wsparcie dla BPMN v2 i analizy PDF**

```env
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=AIzaSyC_example_key_here
API_DEFAULT_MODEL=models/gemini-2.0-flash
CHAT_URL=https://generativelanguage.googleapis.com/v1beta/models
```

**Dostępne modele:**
- `models/gemini-2.0-flash` - Najnowszy, najwydajniejszy (zalecany)
- `models/gemini-1.5-pro` - Zaawansowany model z dużym kontekstem
- `models/gemini-1.5-flash` - Szybki model do podstawowych zadań

**Uzyskiwanie klucza API:**
1. Przejdź do [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Zaloguj się na konto Google
3. Kliknij "Create API Key"
4. Skopiuj wygenerowany klucz do `GOOGLE_API_KEY`

### OpenAI (GPT)

**Wysokiej jakości generowanie z ograniczeniami PDF**

```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-example_key_here
API_DEFAULT_MODEL=gpt-4-turbo
CHAT_URL=https://api.openai.com/v1/chat/completions
```

**Dostępne modele:**
- `gpt-4-turbo` - Najnowszy GPT-4 (zalecany)
- `gpt-4` - Standard GPT-4
- `gpt-3.5-turbo` - Ekonomiczny model

**Uzyskiwanie klucza API:**
1. Przejdź do [OpenAI Platform](https://platform.openai.com/api-keys)
2. Zaloguj się na konto OpenAI
3. Kliknij "Create new secret key"
4. Skopiuj klucz do `OPENAI_API_KEY`

### Anthropic Claude

**Zaawansowane rozumowanie i analiza kontekstu**

```env
MODEL_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-example_key_here
API_DEFAULT_MODEL=claude-3-5-sonnet-20241022
CHAT_URL=https://api.anthropic.com/v1/messages
```

**Dostępne modele:**
- `claude-3-5-sonnet-20241022` - Najnowszy Sonnet (zalecany)
- `claude-3-5-haiku-20241022` - Szybki model
- `claude-3-opus-20240229` - Najzaawansowany model

### Ollama (Lokalne modele)

**Rozwiązanie on-premise bez kosztów API**

```env
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
API_DEFAULT_MODEL=llama3.1:8b
```

**Instalacja Ollama:**
1. Pobierz z [https://ollama.ai/](https://ollama.ai/)
2. Zainstaluj i uruchom serwer
3. Pobierz model: `ollama pull llama3.1:8b`

**Dostępne modele:**
- `llama3.1:8b` - Podstawowy model (zalecany dla start)
- `llama3.1:70b` - Zaawansowany model (wymaga więcej RAM)
- `codellama:7b` - Specjalizowany w kodzie

---

## ⚙️ Konfiguracja BPMN v2

### Parametry jakości

```env
# Próg jakości (0.0-1.0)
BPMN_QUALITY_THRESHOLD=0.8

# Maksymalna liczba iteracji optymalizacji
BPMN_MAX_ITERATIONS=10

# Timeout procesu (minuty)
BPMN_TIMEOUT_MINUTES=5

# Automatyczna walidacja
BPMN_AUTO_VALIDATE=true

# Automatyczne doskonalenie
BPMN_AUTO_IMPROVE=true

# Zapis historii iteracji
BPMN_SAVE_ITERATIONS=true
```

### Poziomy jakości - zalecenia

| Próg jakości | Zastosowanie | Czas | Iteracje |
|--------------|--------------|------|----------|
| **0.6**      | Prototypy, szkice | ~30s | 2-4 |
| **0.7**      | Dokumentacja robocza | ~45s | 3-5 |
| **0.8**      | Standardowa produkcja | ~65s | 4-7 |
| **0.9**      | Krytyczne procesy | ~85s | 6-10 |

### Typy procesów

```env
# Domyślny typ procesu
BPMN_DEFAULT_PROCESS_TYPE=business

# Dostępne typy:
# - business: Procesy biznesowe
# - technical: Procesy techniczne
# - workflow: Przepływy pracy
# - integration: Procesy integracji
```

---

## 📄 Konfiguracja Analizy PDF

### Tryby analizy

```env
# Tryb analizy PDF
PDF_ANALYSIS_MODE=ai  # ai|local|hybrid

# Model do analizy (jeśli ai)
PDF_ANALYSIS_MODEL=models/gemini-2.0-flash

# Język promptów analizy
PDF_ANALYSIS_PROMPT_LANG=pl  # pl|en
```

### Parametry przetwarzania

```env
# Próg rozmiaru dla direct PDF processing (MB)
PDF_DIRECT_THRESHOLD_MB=2.0

# Maksymalna liczba stron do analizy tekstu
PDF_MAX_PAGES_TEXT=50

# Rozmiar fragmentu tekstu
PDF_CHUNK_SIZE=4000

# Maksymalny rozmiar pliku PDF (MB)
PDF_MAX_FILE_SIZE_MB=50

# Timeout analizy PDF (sekundy)
PDF_ANALYSIS_TIMEOUT=120
```

### Modele wspierające direct PDF

| Provider | Model | Direct PDF | Text Fallback |
|----------|-------|------------|---------------|
| **Gemini** | gemini-2.0-flash | ✅ | ✅ |
| **Gemini** | gemini-1.5-pro | ✅ | ✅ |
| **Gemini** | gemini-1.5-flash | ✅ | ✅ |
| **OpenAI** | gpt-4* | ❌ | ✅ |
| **Claude** | claude-3* | ❌ | ✅ |
| **Ollama** | All models | ❌ | ✅ |

---

## 🌐 Konfiguracja Aplikacji

### Ustawienia językowe

```env
# Główny język interfejsu
LANGUAGE=pl  # pl|en

# Język promptów AI
PROMPT_LANGUAGE=pl  # pl|en

# Język walidacji BPMN
BPMN_VALIDATION_LANG=pl  # pl|en
```

### Ustawienia PlantUML

```env
# Ścieżka do PlantUML JAR
PLANTUML_JAR_PATH=plantuml.jar

# Typ generatora PlantUML
PLANTUML_GENERATOR_TYPE=local  # local|server

# URL serwera PlantUML (jeśli server)
PLANTUML_SERVER_URL=http://localhost:8080/plantuml

# Timeout renderowania (sekundy)
PLANTUML_RENDER_TIMEOUT=30
```

### Ustawienia wydajności

```env
# Timeout żądań API (sekundy)
API_REQUEST_TIMEOUT=60

# Maksymalna liczba równoczesnych żądań
MAX_CONCURRENT_REQUESTS=5

# Retry dla nieudanych żądań
API_MAX_RETRIES=3

# Opóźnienie między retry (sekundy)
API_RETRY_DELAY=2
```

---

## 🔧 Konfiguracja Środowiskowa

### Konfiguracja Development

```env
# Development settings
ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Mocki dla testowania
USE_MOCK_AI=false
MOCK_AI_DELAY=1

# Lokalne ścieżki
TEMP_DIR=temp/
LOGS_DIR=logs/
CACHE_DIR=cache/
```

### Konfiguracja Production

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

### Konfiguracja Testing

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

## 🖥️ Konfiguracja Desktop vs Web

### Aplikacja Desktop (PyQt5)

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

### Aplikacja Web (Streamlit)

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

## 📊 Konfiguracja Baz Danych

### SQLite (Domyślna)

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

## 🚀 Profile Konfiguracyjne

### Profil: Rapid Prototyping

**Szybkie prototypowanie z niską jakością**

```env
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=your_key
API_DEFAULT_MODEL=models/gemini-1.5-flash

BPMN_QUALITY_THRESHOLD=0.6
BPMN_MAX_ITERATIONS=3
BPMN_TIMEOUT_MINUTES=2

PDF_ANALYSIS_MODE=local
```

### Profil: Production Standard

**Standardowa produkcja z zrównoważoną jakością**

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

### Profil: High Quality

**Wysokiej jakości dla krytycznych procesów**

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

### Profil: On-Premise

**Rozwiązanie lokalne bez zewnętrznych API**

```env
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
API_DEFAULT_MODEL=llama3.1:8b

BPMN_QUALITY_THRESHOLD=0.7
PDF_ANALYSIS_MODE=local
PLANTUML_GENERATOR_TYPE=local
```

---

## 🔍 Walidacja Konfiguracji

### Sprawdzanie konfiguracji

Uruchom skrypt sprawdzający:

```bash
python -m bpmn_v2.test_env_config
```

**Sprawdzane elementy:**
- ✅ Dostępność kluczy API
- ✅ Połączenie z providerami AI
- ✅ Prawidłowość modeli
- ✅ Dostępność PlantUML
- ✅ Uprawnienia do katalogów
- ✅ Zależności Python

### Diagnostyka problemów

**Problem: Brak odpowiedzi AI**
```bash
# Sprawdź klucze API
echo $GOOGLE_API_KEY
echo $OPENAI_API_KEY

# Test połączenia
python -m tools.test_real_ai_call
```

**Problem: Błędy BPMN**
```bash
# Sprawdź konfigurację BPMN
python -c "from bpmn_v2.ai_config import create_bpmn_config; print(create_bpmn_config())"
```

**Problem: Błędy PDF**
```bash
# Test analizy PDF
python -m tools.analyze_pdf_quality
```

---

## 🔐 Bezpieczeństwo Konfiguracji

### Ochrona kluczy API

1. **Nigdy nie commituj .env do repozytorium**
```bash
echo ".env" >> .gitignore
```

2. **Użyj zmiennych środowiskowych w produkcji**
```bash
export GOOGLE_API_KEY="your_key_here"
```

3. **Rotacja kluczy**
- Zmieniaj klucze API regularnie
- Używaj różnych kluczy dla różnych środowisk
- Monitoruj użycie kluczy

### Szyfrowanie wrażliwych danych

```env
# Opcjonalne szyfrowanie lokalnych danych
ENCRYPT_LOCAL_DATA=true
ENCRYPTION_KEY=your_encryption_key

# Secure file permissions
FILE_PERMISSIONS=600
DIR_PERMISSIONS=700
```

---

## 🧪 Testowanie Konfiguracji

### Test suite konfiguracji

```bash
# Test wszystkich komponentów
python -m tests.test_configuration

# Test konkretnego providera
python -m tests.test_ai_providers --provider gemini

# Test BPMN pipeline
python -m tests.test_bpmn_pipeline

# Test analizy PDF
python -m tests.test_pdf_analysis
```

### Metryki konfiguracji

```bash
# Analiza wydajności
python -m tools.benchmark_configuration

# Raport kosztów API
python -m tools.api_cost_analysis
```

---

## 📚 Przykłady Konfiguracji

### Konfiguracja dla zespołu developerskiego

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

### Konfiguracja dla demonstracji

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
LANGUAGE=pl

# Optimized for demos
API_REQUEST_TIMEOUT=90
ENABLE_CACHING=true
```

Ten przewodnik pokrywa wszystkie aspekty konfiguracji systemu GD_python. Dla specificznych przypadków użycia, skonsultuj się z dokumentacją API Reference lub skontaktuj się z zespołem rozwoju.