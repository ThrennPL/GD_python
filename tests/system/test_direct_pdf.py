#!/usr/bin/env python3
"""
Test bezpośredniego przesyłania PDF do Gemini 2.0 Flash
Porównuje jakość analizy: tekst vs bezpośredni PDF
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
from pathlib import Path
import time

def test_direct_pdf_upload():
    """Test bezpośredniego uploadu PDF."""
    print("🚀 TEST BEZPOŚREDNIEGO PDF UPLOAD")
    print("=" * 50)
    
    # Konfiguracja
    api_key = os.getenv("API_KEY")
    model_name = os.getenv("PDF_ANALYSIS_MODEL", "models/gemini-2.0-flash")
    
    if not api_key:
        print("❌ Brak API_KEY")
        return None, None
    
    # Plik do testu
    pdf_path = Path("test_documents/wyklad01sp.pdf")
    if not pdf_path.exists():
        print(f"❌ Nie znaleziono pliku: {pdf_path}")
        return None, None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        print(f"✅ Model: {model_name}")
        print(f"📄 PDF: {pdf_path.name} ({pdf_path.stat().st_size / 1024:.1f} KB)")
        
        # Upload PDF
        print("📤 Uploading PDF...")
        start_time = time.time()
        
        uploaded_file = genai.upload_file(
            path=str(pdf_path),
            display_name="Test Business Process PDF"
        )
        
        upload_time = time.time() - start_time
        print(f"✅ Upload zakończony: {upload_time:.2f}s")
        print(f"   File URI: {uploaded_file.name}")
        print(f"   Display name: {uploaded_file.display_name}")
        print(f"   MIME type: {uploaded_file.mime_type}")
        
        # Przygotuj prompt do analizy
        analysis_prompt = """
Przeanalizuj ten dokument PDF i wyciągnij następujące informacje:

1. AKTORZY - jakie role/osoby są wymienione w dokumencie
2. AKTYWNOŚCI - jakie procesy, operacje, działania są opisane
3. SYSTEMY - jakie systemy, aplikacje, narzędzia są wymienione
4. DECYZJE - jakie punkty decyzyjne, warunki, reguły biznesowe
5. PRZEPŁYW - jaka jest sekwencja działań

Odpowiedź przedstaw w strukturalnym formacie z jasno oznaczonymi sekcjami.
Skup się na elementach, które mogłyby być użyte do generowania diagramów biznesowych.
"""
        
        # Analiza przez AI
        print("🤖 Analiza przez AI...")
        analysis_start = time.time()
        
        response = model.generate_content([
            analysis_prompt,
            uploaded_file
        ])
        
        analysis_time = time.time() - analysis_start
        print(f"✅ Analiza zakończona: {analysis_time:.2f}s")
        
        # Cleanup
        print("🧹 Cleanup...")
        genai.delete_file(uploaded_file.name)
        
        return response.text, {
            "upload_time": upload_time,
            "analysis_time": analysis_time,
            "total_time": upload_time + analysis_time,
            "file_size": pdf_path.stat().st_size,
            "method": "direct_pdf"
        }
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return None, None

def test_text_extraction_method():
    """Test obecnej metody (ekstraktowanie tekstu)."""
    print("\n📝 TEST OBECNEJ METODY (TEKST)")
    print("=" * 50)
    
    try:
        # Import naszego systemu
        from utils.pdf.pdf_processor import PDFProcessor
        from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer
        
        pdf_path = Path("test_documents/wyklad01sp.pdf")
        
        print(f"📄 PDF: {pdf_path.name}")
        
        start_time = time.time()
        
        # Przetwórz PDF
        processor = PDFProcessor()
        pdf_doc = processor.process_pdf(str(pdf_path))
        
        # Analiza AI
        analyzer = AIPDFAnalyzer()
        
        # Przygotuj prompt
        analysis_prompt = f"""
Przeanalizuj ten tekst z dokumentu PDF i wyciągnij następujące informacje:

{pdf_doc.text_content[:3000]}...

1. AKTORZY - jakie role/osoby są wymienione
2. AKTYWNOŚCI - jakie procesy, operacje, działania są opisane  
3. SYSTEMY - jakie systemy, aplikacje, narzędzia są wymienione
4. DECYZJE - jakie punkty decyzyjne, warunki, reguły biznesowe
5. PRZEPŁYW - jaka jest sekwencja działań

Odpowiedź przedstaw w strukturalnym formacie z jasno oznaczonymi sekcjami.
"""
        
        response_text, metadata = analyzer.call_ai_model(analysis_prompt)
        
        total_time = time.time() - start_time
        
        if metadata["success"]:
            print(f"✅ Analiza zakończona: {total_time:.2f}s")
            return response_text, {
                "total_time": total_time,
                "processing_time": metadata["processing_time"],
                "tokens_used": metadata["tokens_used"],
                "method": "text_extraction",
                "text_length": len(pdf_doc.text_content)
            }
        else:
            print(f"❌ Błąd: {metadata.get('error', 'Unknown')}")
            return None, None
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return None, None

def compare_results(pdf_result, pdf_metadata, text_result, text_metadata):
    """Porównanie wyników obu metod."""
    print("\n🔬 PORÓWNANIE WYNIKÓW")
    print("=" * 60)
    
    if not pdf_result or not text_result:
        print("❌ Brak wyników do porównania")
        return
    
    # Metryki
    print("⏱️ WYDAJNOŚĆ:")
    print(f"  Direct PDF:     {pdf_metadata['total_time']:.2f}s")
    print(f"  Text extract:   {text_metadata['total_time']:.2f}s")
    
    if pdf_metadata['total_time'] < text_metadata['total_time']:
        print("  🏆 Zwycięzca: Direct PDF (szybciej)")
    else:
        print("  🏆 Zwycięzca: Text extraction (szybciej)")
    
    # Długość odpowiedzi
    print(f"\n📏 DŁUGOŚĆ ODPOWIEDZI:")
    print(f"  Direct PDF:     {len(pdf_result)} znaków")
    print(f"  Text extract:   {len(text_result)} znaków")
    
    # Jakość (próbka)
    print(f"\n📄 JAKOŚĆ ANALIZY:")
    print(f"  Direct PDF - pierwsze 300 znaków:")
    print(f"    {pdf_result[:300]}...")
    print(f"\n  Text extract - pierwsze 300 znaków:")
    print(f"    {text_result[:300]}...")
    
    # Szczegółowe porównanie
    pdf_has_structure = any(keyword in pdf_result.lower() for keyword in 
                           ["aktorzy", "aktywności", "systemy", "decyzje", "przepływ"])
    text_has_structure = any(keyword in text_result.lower() for keyword in 
                            ["aktorzy", "aktywności", "systemy", "decyzje", "przepływ"])
    
    print(f"\n🎯 STRUKTURA ODPOWIEDZI:")
    print(f"  Direct PDF zawiera strukturę:   {'✅' if pdf_has_structure else '❌'}")
    print(f"  Text extract zawiera strukturę: {'✅' if text_has_structure else '❌'}")

def main():
    """Główna funkcja testowa."""
    print("⚡ PORÓWNANIE: Direct PDF vs Text Extraction")
    print("=" * 70)
    
    # Test 1: Direct PDF upload
    pdf_result, pdf_metadata = test_direct_pdf_upload()
    
    # Test 2: Text extraction method
    text_result, text_metadata = test_text_extraction_method()
    
    # Porównanie
    if pdf_result and text_result:
        compare_results(pdf_result, pdf_metadata, text_result, text_metadata)
        
        print("\n" + "=" * 70)
        print("🏁 WNIOSKI:")
        
        if pdf_metadata['total_time'] < text_metadata['total_time']:
            print("1. 🚀 Direct PDF jest szybszy")
        else:
            print("1. 🐌 Direct PDF jest wolniejszy")
            
        print("2. 🎯 Direct PDF ma dostęp do formatowania")
        print("3. 📊 Direct PDF może analizować obrazy/tabele")
        print("4. 🔧 Text extraction działa z wszystkimi modelami")
        
        print("\n💡 REKOMENDACJA:")
        if pdf_metadata['total_time'] < text_metadata['total_time'] * 1.5:
            print("   ✅ Warto zaimplementować Direct PDF jako primary method")
            print("   ✅ Text extraction jako fallback")
        else:
            print("   ⚠️ Direct PDF może być za wolny")
            print("   ✅ Text extraction pozostaje primary method")
    else:
        print("\n❌ Nie udało się przeprowadzić pełnego porównania")

if __name__ == "__main__":
    main()