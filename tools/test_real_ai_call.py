#!/usr/bin/env python3
"""
Test rzeczywistego wywołania AI PDF Analysis
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer

def test_real_ai_call():
    """Test rzeczywistego wywołania modelu AI."""
    print("🤖 TEST RZECZYWISTEGO WYWOŁANIA AI")
    print("=" * 50)
    
    try:
        analyzer = AIPDFAnalyzer()
        print(f"✅ AI Analyzer zainicjalizowany")
        print(f"   Mode: {analyzer.analysis_mode}")
        print(f"   Model: {analyzer.model}")
        print(f"   Provider: {analyzer.model_provider}")
        
        if analyzer.analysis_mode != "ai":
            print("⚠️  Tryb nie jest ustawiony na 'ai' - przełączam")
            return False
        
        # Prosty test prompt
        test_prompt = """
        Przeanalizuj następujący proces biznesowy:
        
        Proces składania podania o urlop:
        1. Pracownik wypełnia formularz urlopowy
        2. Przełożony sprawdza dostępność terminów
        3. HR weryfikuje saldo dni urlopowych
        4. Jeśli wszystko w porządku - zatwierdza
        5. Jeśli nie - zwraca do poprawy
        6. Pracownik otrzymuje powiadomienie
        
        Zidentyfikuj aktorów, aktywności i punkty decyzyjne.
        """
        
        print(f"\n📝 Wysyłam test prompt...")
        print(f"Długość promptu: {len(test_prompt)} znaków")
        
        # Wywołanie AI
        response, metadata = analyzer.call_ai_model(test_prompt)
        
        if metadata["success"]:
            print(f"✅ SUKCES!")
            print(f"   Czas przetwarzania: {metadata['processing_time']:.2f}s")
            print(f"   Tokeny: {metadata['tokens_used']}")
            print(f"   Model: {metadata['model_used']}")
            print(f"   Metoda: {metadata.get('method', 'unknown')}")
            
            print(f"\n📄 ODPOWIEDŹ AI ({len(response)} znaków):")
            print("-" * 50)
            # Pokaż pierwszą część odpowiedzi
            preview = response[:500] + "..." if len(response) > 500 else response
            print(preview)
            print("-" * 50)
            
            return True
        else:
            print(f"❌ BŁĄD:")
            print(f"   Error: {metadata.get('error', 'Unknown error')}")
            print(f"   Czas: {metadata['processing_time']:.2f}s")
            return False
            
    except Exception as e:
        print(f"❌ Wyjątek: {e}")
        return False

def main():
    print("🧪 TEST INTEGRATION AI PDF ANALYSIS")
    print("=" * 60)
    
    success = test_real_ai_call()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test AI zakończony sukcesem!")
        print("   System gotowy do wzbogacania analizy PDF")
    else:
        print("❌ Test AI nie powiódł się")
        print("   Sprawdź konfigurację API key i połączenie")
        print("   Lub ustaw PDF_ANALYSIS_MODE=local")

if __name__ == "__main__":
    main()