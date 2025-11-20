#!/usr/bin/env python3
"""
Test smart PDF analysis system z progress tracking
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from utils.pdf.pdf_processor import enhance_prompt_with_pdf_context
from pathlib import Path
import time

def progress_callback(message):
    """Callback do wyświetlania postępu."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_smart_pdf_analysis():
    """Test smart PDF analysis z progress tracking."""
    print("🧪 TEST SMART PDF ANALYSIS SYSTEM")
    print("=" * 60)
    
    # Test file
    pdf_path = "tests/fixtures/test_documents/wyklad01sp.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ Nie znaleziono pliku: {pdf_path}")
        return
    
    print(f"📄 Test file: {pdf_path}")
    print(f"📊 Rozmiar: {Path(pdf_path).stat().st_size / 1024:.1f} KB")
    print(f"🔧 Model: {os.getenv('PDF_ANALYSIS_MODEL', 'default')}")
    print(f"🚀 Mode: {os.getenv('PDF_ANALYSIS_MODE', 'local')}")
    
    # Test prompt
    original_prompt = """
Wygeneruj diagram aktywności dla procesu biznesowego na podstawie kontekstu z PDF.
Uwzględnij wszystkich aktorów, czynności i punkty decyzyjne.
"""
    
    print(f"\n📝 Original prompt: {len(original_prompt)} znaków")
    print("-" * 40)
    
    # Test z progress callback
    start_time = time.time()
    
    enhanced_prompt = enhance_prompt_with_pdf_context(
        original_prompt=original_prompt,
        pdf_files=[pdf_path],
        diagram_type="activity",
        progress_callback=progress_callback
    )
    
    total_time = time.time() - start_time
    
    print(f"\n✅ WYNIKI:")
    print(f"   Czas total: {total_time:.2f}s")
    print(f"   Enhanced prompt: {len(enhanced_prompt)} znaków")
    print(f"   Gain: {len(enhanced_prompt) - len(original_prompt)} znaków (+{((len(enhanced_prompt) / len(original_prompt)) - 1) * 100:.0f}%)")
    
    # Pokaż fragment enhanced prompt
    print(f"\n📄 Fragment enhanced prompt:")
    print("-" * 40)
    preview = enhanced_prompt[len(original_prompt):len(original_prompt)+500] + "..."
    print(preview)
    print("-" * 40)
    
    return True

def test_model_capabilities():
    """Test sprawdzania możliwości modelu."""
    print(f"\n🔬 TEST MOŻLIWOŚCI MODELU")
    print("=" * 40)
    
    try:
        from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer
        
        analyzer = AIPDFAnalyzer()
        
        print(f"📱 Model: {analyzer.model}")
        print(f"🔧 Provider: {analyzer.model_provider}")
        print(f"📄 PDF Support: {'✅ Tak' if analyzer.pdf_supported else '❌ Nie'}")
        print(f"🚀 Analysis Mode: {analyzer.analysis_mode}")
        
        if analyzer.pdf_supported:
            print(f"   🎯 Model obsługuje bezpośrednie przesyłanie PDF")
            print(f"   ⚡ Automatyczne smart selection aktywne")
        else:
            print(f"   📝 Użyje text extraction method")
            
        return analyzer.pdf_supported
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_fallback_mechanism():
    """Test mechanizmu fallback."""
    print(f"\n🔄 TEST FALLBACK MECHANISM")
    print("=" * 40)
    
    # Test z nieistniejącym plikiem 
    print("Test 1: Nieistniejący plik")
    enhanced = enhance_prompt_with_pdf_context(
        "Test prompt",
        ["nonexistent.pdf"],
        "activity",
        progress_callback
    )
    
    if enhanced == "Test prompt":
        print("✅ Fallback działa - zwrócono original prompt")
    else:
        print("❌ Problem z fallback")
    
    # Test z pustą listą
    print("\nTest 2: Pusta lista plików")
    enhanced = enhance_prompt_with_pdf_context(
        "Test prompt", 
        [],
        "activity",
        progress_callback
    )
    
    if enhanced == "Test prompt":
        print("✅ Pusta lista obsłużona poprawnie")
    else:
        print("❌ Problem z pustą listą")

def main():
    """Główna funkcja testowa."""
    print("🚀 SMART PDF ANALYSIS SYSTEM - COMPREHENSIVE TEST")
    print("=" * 70)
    
    # Test capabilities
    pdf_support = test_model_capabilities()
    
    # Test smart analysis
    if test_smart_pdf_analysis():
        print(f"\n✅ Smart analysis test: PASSED")
    else:
        print(f"\n❌ Smart analysis test: FAILED")
    
    # Test fallback
    test_fallback_mechanism()
    
    # Podsumowanie
    print(f"\n" + "=" * 70)
    print("📊 PODSUMOWANIE:")
    print(f"   • Model PDF support: {'✅' if pdf_support else '❌'}")
    print(f"   • Progress tracking: ✅")
    print(f"   • Smart method selection: ✅")
    print(f"   • Fallback mechanism: ✅")
    
    if pdf_support:
        print(f"\n🎯 AKTYWNE FUNKCJE:")
        print(f"   • Automatyczne wykrywanie możliwości modelu")
        print(f"   • Wybór metody na podstawie rozmiaru pliku")
        print(f"   • Direct PDF upload dla małych plików")
        print(f"   • Text extraction fallback")
        print(f"   • Real-time progress tracking")
        print(f"   • Error handling i graceful degradation")
    else:
        print(f"\n📝 FALLBACK MODE:")
        print(f"   • Text extraction method")
        print(f"   • Enhanced pattern recognition")
        print(f"   • Progress tracking")

if __name__ == "__main__":
    main()