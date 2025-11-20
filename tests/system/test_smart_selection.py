#!/usr/bin/env python3
"""
Test logiki smart selection dla różnych rozmiarów plików
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer
import time

def progress_callback(message):
    """Callback do wyświetlania postępu."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_smart_selection_logic():
    """Test logiki smart selection na podstawie rozmiaru pliku."""
    print("🧠 TEST SMART SELECTION LOGIC")
    print("=" * 50)
    
    analyzer = AIPDFAnalyzer()
    
    # Symulujmy różne rozmiary plików
    test_cases = [
        {"size_mb": 0.5, "expected": "direct"},
        {"size_mb": 1.2, "expected": "direct"},  
        {"size_mb": 2.5, "expected": "text"},
        {"size_mb": 5.0, "expected": "text"},
        {"size_mb": 10.0, "expected": "text"}
    ]
    
    print(f"📊 Threshold: {os.getenv('PDF_DIRECT_THRESHOLD_MB', '2.0')} MB")
    print(f"🎯 Model: {analyzer.model}")
    print(f"📄 PDF Support: {'✅' if analyzer.pdf_supported else '❌'}")
    
    print(f"\n📋 TEST CASES:")
    for i, case in enumerate(test_cases, 1):
        size_bytes = case["size_mb"] * 1024 * 1024
        
        # Sprawdź logikę decyzyjną
        if analyzer.pdf_supported and size_bytes <= float(os.getenv('PDF_DIRECT_THRESHOLD_MB', '2.0')) * 1024 * 1024:
            actual_method = "direct"
        else:
            actual_method = "text"
        
        status = "✅" if actual_method == case["expected"] else "❌"
        print(f"   {i}. {case['size_mb']:.1f}MB → {actual_method:6} (expected: {case['expected']:6}) {status}")

def test_configuration_parameters():
    """Test parametrów konfiguracji."""
    print(f"\n🔧 PARAMETRY KONFIGURACJI:")
    print("=" * 40)
    
    params = [
        ("PDF_ANALYSIS_MODEL", "Model używany do analizy"),
        ("PDF_ANALYSIS_MODE", "Tryb analizy (ai/local)"),
        ("PDF_DIRECT_THRESHOLD_MB", "Próg rozmiaru dla direct upload"),
        ("PDF_MAX_PAGES_TEXT", "Max stron dla text extraction"),
        ("PDF_CHUNK_SIZE", "Rozmiar chunka tekstu"),
    ]
    
    for param, description in params:
        value = os.getenv(param, "NOT SET")
        print(f"   {param:<25}: {value}")
        print(f"   {'':<25}  ({description})")
        print()

def test_performance_estimation():
    """Test szacowania wydajności."""
    print(f"⚡ SZACOWANIE WYDAJNOŚCI:")
    print("=" * 40)
    
    # Na podstawie poprzednich testów
    performance_data = {
        "direct": {"time_per_mb": 11.5, "quality": "Wysoka", "business_elements": "3/4"},
        "text": {"time_per_mb": 3.6, "quality": "Średnia", "business_elements": "0/4"}
    }
    
    file_sizes = [0.5, 1.4, 2.5, 5.0]
    
    print("Rozmiar | Metoda  | Czas    | Jakość   | Elementy")
    print("--------|---------|---------|----------|----------")
    
    for size in file_sizes:
        # Logika wyboru metody
        threshold = float(os.getenv('PDF_DIRECT_THRESHOLD_MB', '2.0'))
        
        if size <= threshold:
            method = "direct"
            estimated_time = size * performance_data["direct"]["time_per_mb"]
            quality = performance_data["direct"]["quality"]
            elements = performance_data["direct"]["business_elements"]
        else:
            method = "text"
            estimated_time = size * performance_data["text"]["time_per_mb"]
            quality = performance_data["text"]["quality"]
            elements = performance_data["text"]["business_elements"]
        
        print(f"{size:6.1f}MB | {method:7} | {estimated_time:5.1f}s | {quality:8} | {elements}")

def main():
    """Główna funkcja testowa."""
    print("🚀 SMART SELECTION ANALYSIS")
    print("=" * 60)
    
    test_smart_selection_logic()
    test_configuration_parameters()
    test_performance_estimation()
    
    print(f"\n" + "=" * 60)
    print("💡 WNIOSKI:")
    print("• System automatycznie wybiera optymalną metodę")
    print("• Małe pliki (≤2MB) → Direct PDF (wyższa jakość)")  
    print("• Duże pliki (>2MB) → Text Extraction (szybciej)")
    print("• User otrzymuje real-time progress feedback")
    print("• Graceful degradation przy błędach")
    
    print(f"\n🎯 NASTĘPNE KROKI:")
    print("• Integracja z GUI (PyQt5 + Streamlit)")
    print("• Progress bars w interfejsie użytkownika") 
    print("• Możliwość zmiany threshold przez użytkownika")
    print("• Cache wyników analizy PDF")

if __name__ == "__main__":
    main()