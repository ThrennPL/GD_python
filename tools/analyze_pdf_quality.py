#!/usr/bin/env python3
"""
Pokazuje pełne wyniki porównania Direct PDF vs Text Extraction
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
from pathlib import Path
from utils.pdf.pdf_processor import PDFProcessor
from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer

def show_full_comparison():
    """Pokazuje pełne wyniki obu metod side-by-side."""
    print("📋 PEŁNE PORÓWNANIE JAKOŚCI ANALIZY")
    print("=" * 70)
    
    # Quick test obu metod
    pdf_path = Path("test_documents/wyklad01sp.pdf")
    
    # Method 1: Direct PDF
    print("🚀 METODA 1: DIRECT PDF")
    print("-" * 30)
    
    try:
        genai.configure(api_key=os.getenv("API_KEY"))
        model = genai.GenerativeModel(os.getenv("PDF_ANALYSIS_MODEL"))
        
        uploaded_file = genai.upload_file(
            path=str(pdf_path),
            display_name="Analysis Test"
        )
        
        prompt = """Wyciągnij z tego dokumentu:
1. AKTORZY (konkretne role/osoby)
2. AKTYWNOŚCI (procesy, operacje) 
3. SYSTEMY (narzędzia, aplikacje)
Bądź konkretny i szczegółowy."""
        
        response = model.generate_content([prompt, uploaded_file])
        pdf_result = response.text
        
        genai.delete_file(uploaded_file.name)
        
        print(f"Wynik ({len(pdf_result)} znaków):")
        print(pdf_result)
        
    except Exception as e:
        print(f"❌ Błąd Direct PDF: {e}")
        pdf_result = None
    
    print("\n" + "=" * 70)
    
    # Method 2: Text extraction
    print("📝 METODA 2: TEXT EXTRACTION")
    print("-" * 30)
    
    try:
        processor = PDFProcessor()
        pdf_doc = processor.process_pdf(str(pdf_path))
        
        analyzer = AIPDFAnalyzer()
        
        prompt = f"""Wyciągnij z tego tekstu:
1. AKTORZY (konkretne role/osoby)
2. AKTYWNOŚCI (procesy, operacje)
3. SYSTEMY (narzędzia, aplikacje)
Bądź konkretny i szczegółowy.

TEKST:
{pdf_doc.text_content[:2000]}..."""
        
        response_text, metadata = analyzer.call_ai_model(prompt)
        
        if metadata["success"]:
            print(f"Wynik ({len(response_text)} znaków):")
            print(response_text)
            text_result = response_text
        else:
            print(f"❌ Błąd: {metadata.get('error', 'Unknown')}")
            text_result = None
            
    except Exception as e:
        print(f"❌ Błąd Text Extraction: {e}")
        text_result = None
    
    # Analiza różnic
    print("\n" + "=" * 70)
    print("🔍 ANALIZA RÓŻNIC")
    print("-" * 20)
    
    if pdf_result and text_result:
        # Sprawdź konkretne elementy
        pdf_mentions = {
            "student": "student" in pdf_result.lower(),
            "bos": "bos" in pdf_result.lower() or "biuro obsługi" in pdf_result.lower(),
            "podanie": "podanie" in pdf_result.lower(),
            "dziekanat": "dziekanat" in pdf_result.lower()
        }
        
        text_mentions = {
            "student": "student" in text_result.lower(),
            "bos": "bos" in text_result.lower() or "biuro obsługi" in text_result.lower(),
            "podanie": "podanie" in text_result.lower(),
            "dziekanat": "dziekanat" in text_result.lower()
        }
        
        print("Elementy biznesowe znalezione:")
        for element, found_pdf in pdf_mentions.items():
            found_text = text_mentions[element]
            pdf_icon = "✅" if found_pdf else "❌"
            text_icon = "✅" if found_text else "❌"
            print(f"  {element.upper():12} | Direct PDF: {pdf_icon} | Text Extraction: {text_icon}")
        
        # Podsumowanie
        pdf_score = sum(pdf_mentions.values())
        text_score = sum(text_mentions.values())
        
        print(f"\nWynik: Direct PDF: {pdf_score}/4, Text Extraction: {text_score}/4")
        
        if pdf_score > text_score:
            print("🏆 Direct PDF znajduje więcej szczegółów biznesowych!")
        elif text_score > pdf_score:
            print("🏆 Text Extraction znajduje więcej szczegółów biznesowych!")
        else:
            print("🤝 Obie metody równie skuteczne")

def main():
    show_full_comparison()

if __name__ == "__main__":
    main()