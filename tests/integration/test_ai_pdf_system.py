#!/usr/bin/env python3
"""
Test AI-Enhanced PDF Analysis System
Testuje nowy system analizy PDF z wykorzystaniem AI
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf.pdf_processor import PDFProcessor, enhance_prompt_with_pdf_context
from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer
import tempfile
from pathlib import Path

def create_test_env():
    """Ustawia środowisko testowe."""
    test_env = {
        "PDF_ANALYSIS_MODE": "ai",
        "PDF_ANALYSIS_MODEL": "gemini",
        "PDF_ANALYSIS_PROMPT_LANG": "pl",
        "GEMINI_API_KEY": "test_key_placeholder",
    }
    
    # Stwórz tymczasowy .env dla testów
    env_content = "\n".join([f"{key}={value}" for key, value in test_env.items()])
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        return f.name

def test_ai_analyzer_initialization():
    """Test inicjalizacji AI analyzera."""
    print("=== Test inicjalizacji AI PDF Analyzer ===")
    
    try:
        analyzer = AIPDFAnalyzer()
        print(f"✅ AI Analyzer zainicjalizowany")
        print(f"   - Mode: {analyzer.analysis_mode}")
        print(f"   - Model: {analyzer.model}")
        print(f"   - Language: {analyzer.prompt_language}")
        return True
    except Exception as e:
        print(f"❌ Błąd inicjalizacji: {e}")
        return False

def test_pdf_processor_mode_selection():
    """Test wyboru trybu w PDF procesorze."""
    print("\n=== Test wyboru trybu analizy ===")
    
    try:
        # Import lokalny aby uniknąć problemów
        from utils.pdf.pdf_processor import PDFProcessor
        
        # Test trybu AI
        os.environ["PDF_ANALYSIS_MODE"] = "ai"
        processor_ai = PDFProcessor()
        print(f"✅ PDFProcessor w trybie AI: {processor_ai.analysis_mode}")
        
        # Test trybu local
        os.environ["PDF_ANALYSIS_MODE"] = "local"
        processor_local = PDFProcessor()
        print(f"✅ PDFProcessor w trybie local: {processor_local.analysis_mode}")
        
        return True
    except Exception as e:
        print(f"❌ Błąd testu trybu: {e}")
        return False

def test_prompt_templates():
    """Test szablonów promptów dla różnych typów diagramów."""
    print("\n=== Test szablonów promptów ===")
    
    try:
        analyzer = AIPDFAnalyzer()
        
        # Test różnych typów diagramów
        diagram_types = ['activity', 'sequence', 'class', 'component']
        
        for diagram_type in diagram_types:
            prompt = analyzer.get_analysis_prompt("Test content", diagram_type)
            if prompt and len(prompt) > 100:
                print(f"✅ Prompt dla {diagram_type}: {len(prompt)} znaków")
            else:
                print(f"❌ Brak promptu dla {diagram_type}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Błąd testowania promptów: {e}")
        return False

def test_context_formatting():
    """Test formatowania kontekstu dla różnych typów diagramów."""
    print("\n=== Test formatowania kontekstu ===")
    
    try:
        analyzer = AIPDFAnalyzer()
        
        # Symulacja wyników AI
        mock_ai_response = {
            'actors': ['Użytkownik', 'Administrator', 'System'],
            'activities': ['Logowanie', 'Walidacja', 'Zapis danych'],
            'decisions': ['Sprawdzenie uprawnień', 'Weryfikacja danych'],
            'systems': ['Baza danych', 'API'],
            'confidence': 0.85
        }
        
        # Test formatowania dla różnych typów
        diagram_types = ['activity', 'sequence', 'class', 'component']
        
        for diagram_type in diagram_types:
            formatted = analyzer.format_context_for_diagram(mock_ai_response, diagram_type)
            if formatted and len(formatted) > 50:
                print(f"✅ Format dla {diagram_type}: {len(formatted)} znaków")
            else:
                print(f"❌ Błędne formatowanie dla {diagram_type}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Błąd testowania formatowania: {e}")
        return False

def test_enhanced_prompt_integration():
    """Test integracji z enhance_prompt_with_pdf_context."""
    print("\n=== Test integracji z główną funkcją ===")
    
    try:
        # Import lokalny
        from utils.pdf.pdf_processor import enhance_prompt_with_pdf_context
        
        # Ustawienie trybu local dla testu (żeby nie potrzebować prawdziwego API)
        os.environ["PDF_ANALYSIS_MODE"] = "local"
        
        original_prompt = "Wygeneruj diagram aktywności dla procesu logowania"
        
        # Test z pustą listą plików
        enhanced_empty = enhance_prompt_with_pdf_context(original_prompt, [], "activity")
        
        if enhanced_empty == original_prompt:
            print("✅ Pusta lista plików - zwrócono oryginalny prompt")
        else:
            print("❌ Błąd dla pustej listy plików")
            return False
        
        # Test z nieistniejącymi plikami (nie powinno powodować crashu)
        enhanced_missing = enhance_prompt_with_pdf_context(
            original_prompt, 
            ["nonexistent.pdf"], 
            "activity"
        )
        
        if enhanced_missing == original_prompt:
            print("✅ Nieistniejący plik - zwrócono oryginalny prompt")
        else:
            print("❌ Błąd dla nieistniejącego pliku")
        
        return True
    except Exception as e:
        print(f"❌ Błąd testowania integracji: {e}")
        return False

def test_configuration_loading():
    """Test ładowania konfiguracji z .env."""
    print("\n=== Test ładowania konfiguracji ===")
    
    try:
        # Zapisz oryginalne zmienne
        original_mode = os.environ.get("PDF_ANALYSIS_MODE")
        original_model = os.environ.get("PDF_ANALYSIS_MODEL")
        
        # Test różnych konfiguracji
        test_configs = [
            ("ai", "gemini"),
            ("ai", "openai"),
            ("local", "none")
        ]
        
        for mode, model in test_configs:
            os.environ["PDF_ANALYSIS_MODE"] = mode
            os.environ["PDF_ANALYSIS_MODEL"] = model
            
            analyzer = AIPDFAnalyzer()
            
            if analyzer.analysis_mode == mode and analyzer.model == model:
                print(f"✅ Konfiguracja {mode}/{model}: OK")
            else:
                print(f"❌ Błąd konfiguracji {mode}/{model}")
                return False
        
        # Przywróć oryginalne
        if original_mode:
            os.environ["PDF_ANALYSIS_MODE"] = original_mode
        if original_model:
            os.environ["PDF_ANALYSIS_MODEL"] = original_model
        
        return True
    except Exception as e:
        print(f"❌ Błąd testowania konfiguracji: {e}")
        return False

def main():
    """Uruchomienie wszystkich testów."""
    print("🚀 AI-Enhanced PDF Analysis System - Testy funkcjonalne")
    print("=" * 60)
    
    tests = [
        test_ai_analyzer_initialization,
        test_pdf_processor_mode_selection,
        test_prompt_templates,
        test_context_formatting,
        test_enhanced_prompt_integration,
        test_configuration_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ Test {test_func.__name__} FAILED")
        except Exception as e:
            print(f"❌ Test {test_func.__name__} CRASHED: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 WYNIKI TESTÓW: {passed}/{total} przeszło pomyślnie")
    
    if passed == total:
        print("🎉 Wszystkie testy przeszły pomyślnie!")
        print("\n📋 System AI PDF Analysis gotowy do użycia:")
        print("   • Konfiguracja przez .env (PDF_ANALYSIS_MODE, PDF_ANALYSIS_MODEL)")
        print("   • Automatyczne przełączanie między trybem AI i lokalnym")
        print("   • Obsługa wszystkich typów diagramów")
        print("   • Integracja z istniejącym workflow PDF")
    else:
        print("⚠️  Niektóre testy nie przeszły - sprawdź logi powyżej")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)