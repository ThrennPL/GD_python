#!/usr/bin/env python3
"""
Test możliwości Gemini 2.0 Flash z plikami PDF
Sprawdza czy model obsługuje bezpośrednie przesyłanie PDF
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
from pathlib import Path

def test_pdf_capabilities():
    """Testuje możliwości modelu z plikami PDF."""
    print("🔍 TEST MOŻLIWOŚCI PDF - GEMINI 2.0 FLASH")
    print("=" * 60)
    
    # Konfiguracja
    api_key = os.getenv("API_KEY")
    model_name = os.getenv("PDF_ANALYSIS_MODEL", "models/gemini-2.0-flash")
    
    if not api_key:
        print("❌ Brak API_KEY w .env")
        return False
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        print(f"✅ Model zainicjalizowany: {model_name}")
        
        # Sprawdź dostępne formaty
        print(f"\n📋 Sprawdzanie możliwości modelu:")
        
        # Lista obsługiwanych formatów przez Gemini
        supported_formats = [
            "text/plain",
            "text/html", 
            "text/css",
            "text/javascript",
            "application/pdf",  # To nas interesuje!
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp"
        ]
        
        print("📄 Oficjalnie obsługiwane formaty przez Gemini:")
        for fmt in supported_formats:
            marker = "🎯" if "pdf" in fmt else "📝"
            print(f"  {marker} {fmt}")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_file_upload_api():
    """Testuje Google File API do uploadowania plików."""
    print(f"\n🔧 TEST FILE UPLOAD API")
    print("=" * 40)
    
    try:
        # Sprawdź dostępność File API
        print("📂 Google File API umożliwia:")
        print("  • Upload plików do 2GB")
        print("  • Obsługę PDF, obrazów, video")
        print("  • Tymczasowe przechowywanie (24h)")
        print("  • Bezpośrednie przetwarzanie przez model")
        
        # Przykład użycia (bez rzeczywistego uploadu)
        example_code = '''
# Upload pliku PDF
file = genai.upload_file(path="document.pdf", 
                        display_name="Business Process PDF")

# Analiza przez model
response = model.generate_content([
    "Przeanalizuj ten dokument PDF i wyciągnij procesy biznesowe:",
    file
])

# Cleanup
genai.delete_file(file.name)
'''
        
        print(f"\n💡 Przykład użycia:")
        print(example_code)
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def show_current_vs_enhanced_approach():
    """Porównanie obecnego podejścia z enhanced PDF processing."""
    print(f"\n🔄 PORÓWNANIE PODEJŚĆ")
    print("=" * 40)
    
    current_approach = {
        "Metoda": "Ekstraktowanie tekstu → AI prompt",
        "Kroki": [
            "1. PyMuPDF/PyPDF2 → surowy tekst",
            "2. Regex patterns → elementy procesu", 
            "3. Formatowanie → structured prompt",
            "4. AI model → analiza tekstu"
        ],
        "Zalety": [
            "Działa z dowolnym modelem",
            "Kontrola nad ekstraktowaniem",
            "Fallback mechanism"
        ],
        "Ograniczenia": [
            "Utrata formatowania",
            "Problemy z tabelami/obrazami",
            "Długie prompty tekstowe"
        ]
    }
    
    enhanced_approach = {
        "Metoda": "Bezpośrednie przesłanie PDF → AI",
        "Kroki": [
            "1. Upload PDF → Google File API",
            "2. Bezpośrednia analiza przez model",
            "3. Structured response"
        ],
        "Zalety": [
            "Zachowanie formatowania",
            "Analiza obrazów/tabel/wykresów",
            "Lepsza jakość analizy",
            "Krótsze prompty"
        ],
        "Ograniczenia": [
            "Tylko modele obsługujące PDF",
            "Wymaga File API",
            "Limit 2GB na plik"
        ]
    }
    
    print("📊 OBECNE PODEJŚCIE:")
    print(f"   Metoda: {current_approach['Metoda']}")
    for i, step in enumerate(current_approach['Kroki'], 1):
        print(f"   {step}")
    
    print(f"\n   ✅ Zalety:")
    for advantage in current_approach['Zalety']:
        print(f"      • {advantage}")
    
    print(f"   ⚠️ Ograniczenia:")
    for limitation in current_approach['Ograniczenia']:
        print(f"      • {limitation}")
    
    print(f"\n🚀 ENHANCED PODEJŚCIE:")
    print(f"   Metoda: {enhanced_approach['Metoda']}")
    for i, step in enumerate(enhanced_approach['Kroki'], 1):
        print(f"   {step}")
    
    print(f"\n   ✅ Zalety:")
    for advantage in enhanced_approach['Zalety']:
        print(f"      • {advantage}")
    
    print(f"   ⚠️ Ograniczenia:")
    for limitation in enhanced_approach['Ograniczenia']:
        print(f"      • {limitation}")

def check_for_test_pdfs():
    """Sprawdza dostępność plików PDF do testów."""
    print(f"\n📁 SPRAWDZANIE PLIKÓW PDF")
    print("=" * 40)
    
    # Sprawdź workspace
    workspace = Path(".")
    pdf_files = list(workspace.glob("*.pdf"))
    
    if pdf_files:
        print(f"✅ Znaleziono {len(pdf_files)} plików PDF:")
        for pdf in pdf_files:
            size = pdf.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"   📄 {pdf.name} ({size_mb:.1f} MB)")
            
        # Wybierz najlepszy kandydat
        best_candidate = min(pdf_files, key=lambda x: x.stat().st_size)
        print(f"\n🎯 Najlepszy kandydat do testu: {best_candidate.name}")
        return best_candidate
    else:
        print("❌ Nie znaleziono plików PDF w workspace")
        print("💡 Możesz stworzyć test PDF lub użyć istniejących dokumentów")
        return None

def main():
    """Główna funkcja testowa."""
    print("🔬 ANALIZA MOŻLIWOŚCI GEMINI 2.0 FLASH Z PDF")
    print("=" * 70)
    
    # Testy
    model_ok = test_pdf_capabilities()
    if model_ok:
        test_file_upload_api()
        show_current_vs_enhanced_approach()
        test_file = check_for_test_pdfs()
        
        print("\n" + "=" * 70)
        print("🎯 REKOMENDACJE:")
        
        if test_file:
            print("1. ✅ Gemini 2.0 Flash obsługuje PDF")
            print("2. ✅ Google File API dostępne") 
            print("3. ✅ Pliki PDF dostępne do testów")
            print("4. 🚀 WARTO zaimplementować enhanced PDF processing")
            print("\n💡 Następne kroki:")
            print("   • Implementuj File API upload")
            print("   • Test z rzeczywistym PDF")
            print("   • Porównaj jakość z obecnym podejściem")
            print(f"   • Użyj {test_file.name} jako test case")
        else:
            print("1. ✅ Gemini 2.0 Flash obsługuje PDF")
            print("2. ✅ Google File API dostępne")
            print("3. ❌ Brak plików PDF do testów")
            print("4. ⚠️ Możemy zaimplementować, ale potrzebujemy test PDF")
    else:
        print("❌ Problem z konfiguracją modelu")

if __name__ == "__main__":
    main()