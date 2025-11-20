#!/usr/bin/env python3
"""
Debug: Szczegóły wywołania modelu AI w PDF Analysis
Pokazuje dokładnie jakie adresy i parametry są używane
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer
import json

def show_current_configuration():
    """Pokazuje aktualną konfigurację z .env"""
    print("🔧 AKTUALNA KONFIGURACJA Z .ENV")
    print("=" * 50)
    
    config_vars = [
        ("PDF_ANALYSIS_MODE", "Tryb analizy"),
        ("PDF_ANALYSIS_MODEL", "Model AI dla PDF"),
        ("PDF_ANALYSIS_PROMPT_LANG", "Język promptów"),
        ("CHAT_URL", "URL do API chat"),
        ("API_KEY", "Klucz API"),
        ("MODEL_PROVIDER", "Dostawca modelu"),
        ("API_DEFAULT_MODEL", "Domyślny model")
    ]
    
    for var, description in config_vars:
        value = os.getenv(var, "BRAK")
        # Maskuj API key dla bezpieczeństwa
        if "API_KEY" in var and value != "BRAK":
            masked_value = value[:8] + "*" * (len(value) - 8) if len(value) > 8 else "***masked***"
            print(f"  {var:25} = {masked_value:<30} # {description}")
        else:
            print(f"  {var:25} = {value:<30} # {description}")

def show_ai_analyzer_config():
    """Pokazuje konfigurację AI Analyzera"""
    print("\n📱 KONFIGURACJA AI PDF ANALYZER")
    print("=" * 50)
    
    try:
        analyzer = AIPDFAnalyzer()
        
        print(f"  Analysis Mode    = {analyzer.analysis_mode}")
        print(f"  Model           = {analyzer.model}")
        print(f"  Model Provider  = {analyzer.model_provider}")
        print(f"  Prompt Language = {analyzer.prompt_language}")
        print(f"  Chat URL        = {analyzer.chat_url}")
        
        # Maskuj API key
        if analyzer.api_key:
            masked_key = analyzer.api_key[:8] + "*" * (len(analyzer.api_key) - 8) if len(analyzer.api_key) > 8 else "***masked***"
            print(f"  API Key         = {masked_key}")
        else:
            print(f"  API Key         = BRAK")
            
        return analyzer
    except Exception as e:
        print(f"❌ Błąd inicjalizacji: {e}")
        return None

def show_request_details(analyzer):
    """Pokazuje szczegóły żądania HTTP"""
    if not analyzer:
        return
    
    print(f"\n🌐 SZCZEGÓŁY WYWOŁANIA API")
    print("=" * 50)
    
    if analyzer.model_provider == "gemini":
        print("🔧 GEMINI - Używa Google Generative AI SDK")
        print("  Metoda: google.generativeai SDK")
        print("  URL: Wewnętrzne SDK (nie REST)")
        print("  Autoryzacja: API key przez SDK")
        print("  Config:")
        print("    • temperature: 0.1")
        print("    • max_output_tokens: 2048")
        print("    • top_k: 40")
        print("    • top_p: 0.95")
        
    elif analyzer.model_provider == "openai":
        print("🔧 OPENAI - REST API")
        print(f"  URL: {analyzer.chat_url}")
        print("  Metoda: HTTP POST")
        print("  Headers:")
        print("    • Content-Type: application/json")
        print("    • Authorization: Bearer ***MASKED***")
        print("  Config:")
        print("    • temperature: 0.1")
        print("    • max_tokens: 2048")
        
    else:  # local
        print("🔧 LOCAL MODEL - REST API")
        print(f"  URL: {analyzer.chat_url}")
        print("  Metoda: HTTP POST")
        print("  Headers:")
        print("    • Content-Type: application/json")
        print("  Config:")
        print("    • temperature: 0.1")
        print("    • max_tokens: 2048")
    
    print(f"\nTimeout: 60 sekund")
    print(f"Model: {analyzer.model}")

def show_payload_structure(analyzer):
    """Pokazuje strukturę payload dla różnych providerów"""
    if not analyzer:
        return
    
    print(f"\n📄 STRUKTURA WYWOŁANIA")
    print("=" * 50)
    
    sample_prompt = "Przykładowy tekst do analizy..."
    
    if analyzer.model_provider == "gemini":
        print("GEMINI SDK Format:")
        print(f"""
import google.generativeai as genai
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("{analyzer.model}")

generation_config = genai.types.GenerationConfig(
    temperature=0.1,
    max_output_tokens=2048,
    top_k=40,
    top_p=0.95
)

response = model.generate_content(prompt, generation_config=generation_config)
""")
        
    elif analyzer.model_provider == "openai":
        payload = {
            "model": analyzer.model,
            "messages": [
                {"role": "user", "content": sample_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }
        print("OPENAI REST API Format:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
    else:  # local
        payload = {
            "model": analyzer.model,
            "messages": [
                {"role": "user", "content": sample_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }
        print("LOCAL API Format:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

def show_response_parsing(analyzer):
    """Pokazuje jak parsowana jest odpowiedź"""
    if not analyzer:
        return
    
    print(f"\n🔍 PARSOWANIE ODPOWIEDZI")
    print("=" * 50)
    
    if analyzer.model_provider == "gemini":
        print("GEMINI SDK - Parsowanie odpowiedzi:")
        print("  if hasattr(response, 'text'):")
        print("      content = response.text")
        print("  elif hasattr(response, 'candidates'):")
        print("      content = response.candidates[0].content.parts[0].text")
        print("  else:")
        print("      content = str(response)")
        print("\n  tokens = aproksymacja (len(prompt) + len(response))")
        
    elif analyzer.model_provider == "openai":
        print("OPENAI REST API - Parsowanie odpowiedzi:")
        print('  response["choices"][0]["message"]["content"]')
        print('  tokens = response["usage"]["total_tokens"]')
        
    else:
        print("LOCAL API - Parsowanie odpowiedzi:")
        print('  response["choices"][0]["message"]["content"]')
        print('  tokens = response["usage"]["total_tokens"]')

def show_url_breakdown():
    """Rozbija URL na komponenty"""
    print(f"\n🔗 ANALIZA URL")
    print("=" * 50)
    
    chat_url = os.getenv("CHAT_URL", "")
    if not chat_url:
        print("❌ BRAK CHAT_URL w .env")
        return
    
    print(f"Pełny URL: {chat_url}")
    
    # Rozbij URL
    if "generativelanguage.googleapis.com" in chat_url:
        print("\n📍 GOOGLE GEMINI API:")
        print("  Domena: generativelanguage.googleapis.com")
        print("  Ścieżka: /v1beta/chat/completions") 
        print("  Protokół: HTTPS")
        print("  Port: 443 (domyślny HTTPS)")
        print("  Autoryzacja: x-goog-api-key header")
        
    elif "api.openai.com" in chat_url:
        print("\n📍 OPENAI API:")
        print("  Domena: api.openai.com")
        print("  Ścieżka: /v1/chat/completions")
        print("  Protokół: HTTPS") 
        print("  Port: 443 (domyślny HTTPS)")
        print("  Autoryzacja: Bearer token")
        
    elif "localhost" in chat_url:
        print("\n📍 LOCAL MODEL:")
        print("  Domena: localhost")
        print("  Ścieżka: /v1/chat/completions")
        print("  Protokół: HTTP")
        print("  Port: (z URL)")
        print("  Autoryzacja: Brak lub custom")

def main():
    """Główna funkcja debug"""
    print("🔍 DEBUG: Wywołanie modelu AI w PDF Analysis")
    print("=" * 60)
    
    show_current_configuration()
    analyzer = show_ai_analyzer_config()
    show_url_breakdown()
    show_request_details(analyzer)
    show_payload_structure(analyzer)
    show_response_parsing(analyzer)
    
    print("\n" + "=" * 60)
    print("💡 PODSUMOWANIE WYWOŁANIA:")
    print("1. System odczytuje konfigurację z .env")
    print("2. Konstruuje żądanie HTTP POST na CHAT_URL")
    print("3. Dodaje odpowiednie headers (API key)")
    print("4. Wysyła payload z modelem i promptem")
    print("5. Parsuje odpowiedź JSON")
    print("6. Zwraca tekst + metadane")

if __name__ == "__main__":
    main()