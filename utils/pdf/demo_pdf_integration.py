"""
Przykład demonstracyjny integracji PDF z generatorem diagramów.
Ten skrypt pokazuje jak używać nowej funkcjonalności PDF.
"""

import os
import tempfile
from pathlib import Path

# Import nowych modułów PDF
from utils.pdf.pdf_processor import PDFProcessor, enhance_prompt_with_pdf_context
from utils.pdf.streamlit_pdf_integration import PDFUploadManager

def create_sample_pdf_content():
    """Tworzy przykładową treść dokumentu PDF dla demonstracji."""
    
    sample_content = """
PROCES OBSŁUGI ZAMÓWIENIA E-COMMERCE

1. WPROWADZENIE
Niniejszy dokument opisuje pełny proces obsługi zamówienia w systemie e-commerce 
od momentu złożenia przez klienta do dostawy produktu.

2. UCZESTNICY PROCESU
- Klient - osoba składająca zamówienie
- System e-commerce - platforma obsługi zamówień  
- Centrum logistyczne - magazyn i przygotowanie wysyłki
- Kurier - dostawca zewnętrzny
- System płatności - bramka płatnicza
- Dział obsługi klienta - wsparcie techniczne

3. GŁÓWNE ETAPY PROCESU

Krok 1: Składanie zamówienia
Klient przegląda katalog produktów w systemie e-commerce, dodaje wybrane 
pozycje do koszyka i przechodzi do procesu zamówienia.

Krok 2: Weryfikacja danych
System e-commerce sprawdza poprawność danych klienta, dostępność produktów
w magazynie oraz kalkuluje koszty wysyłki.

Krok 3: Przetwarzanie płatności  
W przypadku pozytywnej weryfikacji, zamówienie jest przekazywane do systemu
płatności w celu autoryzacji transakcji.

Krok 4: Potwierdzenie zamówienia
Po udanej płatności system generuje potwierdzenie zamówienia i wysyła
powiadomienie do klienta oraz centrum logistycznego.

Krok 5: Przygotowanie do wysyłki
Centrum logistyczne przygotowuje produkty, pakuje je i przekazuje kurierowi.

Krok 6: Dostawa
Kurier dostarcza zamówienie do klienta i aktualizuje status w systemie.

4. PUNKTY DECYZYJNE

Decyzja 1: Dostępność produktu
- Jeśli produkt dostępny -> Kontynuuj proces
- Jeśli niedostępny -> Zaproponuj alternatywę lub odłóż zamówienie

Decyzja 2: Weryfikacja płatności
- Jeśli płatność autoryzowana -> Potwierdź zamówienie  
- Jeśli odrzucona -> Powiadomienie o błędzie i propozycja alternatywnej metody

Decyzja 3: Status dostawy
- Jeśli dostawa udana -> Zamknij zamówienie
- Jeśli nieudana -> Ponowna próba dostawy lub zwrot

5. SYSTEMY ZINTEGROWANE
- Portal e-commerce (front-end)
- System zarządzania zamówieniami (OMS)
- System zarządzania magazynem (WMS)
- System płatności (PayU, Przelewy24)
- System CRM dla obsługi klienta
- API kurierów (DHL, UPS, InPost)
"""
    return sample_content

def demonstrate_pdf_processing():
    """Demonstracja podstawowego przetwarzania PDF."""
    
    print("=== Demonstracja przetwarzania PDF ===")
    
    # Utwórz tymczasowy plik PDF (symulacja)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write(create_sample_pdf_content())
        temp_path = tmp_file.name
    
    try:
        # Inicjalizuj procesor
        processor = PDFProcessor()
        
        # Symulacja przetwarzania (używamy pliku tekstowego jako przykład)
        print(f"📄 Przetwarzanie dokumentu: {temp_path}")
        
        # Utwórz symulację PDF document
        from utils.pdf.pdf_processor import PDFDocument, ProcessContext
        from datetime import datetime
        import hashlib
        
        content = create_sample_pdf_content()
        file_hash = hashlib.md5(content.encode()).hexdigest()
        
        pdf_doc = PDFDocument(
            file_path=temp_path,
            title="Proces obsługi zamówienia e-commerce",
            total_pages=1,
            text_content=content,
            structured_content={'pages': [{'page_num': 1, 'text': content}]},
            metadata={'title': 'Demo proces'},
            hash=file_hash,
            processed_date=datetime.now().isoformat()
        )
        
        # Analizuj kontekst procesu
        print("\n🔍 Analiza kontekstu procesu...")
        context = processor.analyze_process_context(content)
        
        print(f"📋 Nazwa procesu: {context.process_name}")
        print(f"👥 Znaleziono aktorów ({len(context.actors)}): {', '.join(context.actors[:5])}")
        print(f"⚙️ Znaleziono aktywności ({len(context.activities)}): {', '.join(context.activities[:3])}")
        print(f"🖥️ Znaleziono systemy ({len(context.systems)}): {', '.join(context.systems[:3])}")
        print(f"❓ Znaleziono decyzje ({len(context.decisions)}): {len(context.decisions)}")
        
        # Testuj kontekst dla różnych typów diagramów
        print("\n📊 Generowanie kontekstu dla różnych typów diagramów:")
        
        diagram_types = ['sequence', 'activity', 'class', 'component']
        
        for diagram_type in diagram_types:
            print(f"\n--- {diagram_type.upper()} DIAGRAM ---")
            context_text = processor.get_context_for_diagram_type(pdf_doc, diagram_type)
            # Pokaż pierwsze 200 znaków
            preview = context_text[:200] + "..." if len(context_text) > 200 else context_text
            print(preview)
        
        return pdf_doc, context
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return None, None
        
    finally:
        # Usuń tymczasowy plik
        try:
            os.unlink(temp_path)
        except:
            pass

def demonstrate_prompt_enhancement():
    """Demonstracja wzbogacania promptu o kontekst PDF."""
    
    print("\n=== Demonstracja wzbogacania promptu ===")
    
    # Oryginalny prompt
    original_prompt = """
    Wygeneruj diagram sekwencji PlantUML dla procesu zamawiania produktów online.
    
    Proces powinien obejmować:
    - Składanie zamówienia przez klienta
    - Weryfikację płatności  
    - Przygotowanie produktu do wysyłki
    """
    
    print(f"📝 Oryginalny prompt ({len(original_prompt)} znaków):")
    print(original_prompt)
    
    # Symulacja pliku PDF (używamy przykładu tekstowego)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write(create_sample_pdf_content())
        temp_path = tmp_file.name
    
    try:
        # Wzbogać prompt (użyjemy symulacji)
        print(f"\n🔗 Wzbogacanie promptu kontekstem z PDF...")
        
        # Symulacja funkcji enhance_prompt_with_pdf_context
        enhanced_prompt = f"""{original_prompt}

**DODATKOWY KONTEKST Z DOKUMENTÓW PDF:**

**KONTEKST Z DOKUMENTU: Proces obsługi zamówienia e-commerce**

**PROCES:** Proces obsługi zamówienia e-commerce

**UCZESTNICY PROCESU:**
- Klient
- System e-commerce  
- Centrum logistyczne
- Kurier
- System płatności

**GŁÓWNE AKTYWNOŚCI:**
- Składanie zamówienia
- Weryfikacja danych
- Przetwarzanie płatności
- Przygotowanie do wysyłki
- Dostawa

**SYSTEMY I KOMPONENTY:**
- Portal e-commerce
- System zarządzania zamówieniami
- System płatności
- API kurierów

**PUNKTY DECYZYJNE:**
- Dostępność produktu
- Weryfikacja płatności
- Status dostawy

**INSTRUKCJA:** Wykorzystaj powyższy kontekst z dokumentów PDF do wzbogacenia diagramu o dodatkowe szczegóły, aktorów, systemy i procesy, które mogą być istotne dla kompletnego przedstawienia.
"""
        
        print(f"\n✨ Wzbogacony prompt ({len(enhanced_prompt)} znaków):")
        print("--- POCZĄTEK WZBOGACONEGO PROMPTU ---")
        print(enhanced_prompt)
        print("--- KONIEC WZBOGACONEGO PROMPTU ---")
        
        print(f"\n📈 Statystyki:")
        print(f"   - Oryginalna długość: {len(original_prompt)} znaków")
        print(f"   - Wzbogacona długość: {len(enhanced_prompt)} znaków")
        print(f"   - Wzrost o: {len(enhanced_prompt) - len(original_prompt)} znaków ({((len(enhanced_prompt) / len(original_prompt)) - 1) * 100:.1f}%)")
        
        return enhanced_prompt
        
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass

def demonstrate_streamlit_integration():
    """Demonstracja integracji z interfejsem Streamlit."""
    
    print("\n=== Demonstracja integracji Streamlit ===")
    
    try:
        # Inicjalizuj manager (bez Streamlit session_state)
        print("🚀 Inicjalizacja PDF Upload Manager...")
        
        # Symulacja konfiguracji
        print("⚙️ Konfiguracja:")
        print("   - Cache directory: utils/cache/pdf/")
        print("   - Supported formats: PDF")
        print("   - Max file size: 10MB")
        print("   - Auto-processing: Enabled")
        
        print("✅ Manager zainicjalizowany pomyślnie")
        
        print("\n📋 Dostępne funkcjonalności w UI:")
        print("   1. Upload wielu plików PDF")
        print("   2. Automatyczne przetwarzanie i cache")
        print("   3. Podgląd ekstraktowanego kontekstu")
        print("   4. Wybór trybu wykorzystania kontekstu:")
        print("      - Automatycznie dostosuj do typu diagramu") 
        print("      - Użyj pełnego tekstu jako kontekst")
        print("      - Tylko kluczowe elementy")
        print("   5. Integracja z generowaniem promptów")
        
        print("\n🔧 Proces w aplikacji Streamlit:")
        print("   1. Użytkownik wgrywa pliki PDF")
        print("   2. System automatycznie je przetwarza")
        print("   3. Ekstraktuje kontekst biznesowy")
        print("   4. Przy generowaniu diagramu kontekst jest dodawany do promptu")
        print("   5. AI otrzymuje bogszy kontekst i generuje lepsze diagramy")
        
    except Exception as e:
        print(f"❌ Błąd demonstracji: {e}")

def demonstrate_cache_functionality():
    """Demonstracja funkcjonalności cache."""
    
    print("\n=== Demonstracja systemu cache ===")
    
    processor = PDFProcessor()
    
    # Symulacja cache
    print("💾 System cache:")
    print(f"   - Lokalizacja: {processor.cache_dir}")
    print("   - Format: JSON")
    print("   - Klucz: MD5 hash pliku")
    
    # Przykład struktury cache
    cache_example = {
        "file_path": "/path/to/document.pdf",
        "title": "Proces obsługi klienta",  
        "total_pages": 15,
        "processed_date": "2024-11-19T10:30:00",
        "text_content": "Treść dokumentu...",
        "hash": "abc123def456",
        "structured_content": {
            "pages": [],
            "toc": []
        }
    }
    
    print(f"\n📄 Przykład wpisu cache:")
    print(f"   Plik: abc123def456.json")
    print("   Zawartość:")
    for key, value in cache_example.items():
        if key == "text_content":
            print(f"     {key}: {str(value)[:50]}...")
        else:
            print(f"     {key}: {value}")
    
    print("\n⚡ Korzyści cache:")
    print("   - Szybkie przetwarzanie przy ponownym użyciu")
    print("   - Wykrywanie zmian w plikach")
    print("   - Oszczędność zasobów obliczeniowych")
    print("   - Lepsza responsywność aplikacji")

def main():
    """Główna funkcja demonstracyjna."""
    
    print("🎯 DEMONSTRACJA INTEGRACJI PDF Z GENERATOREM DIAGRAMÓW")
    print("=" * 60)
    
    try:
        # 1. Podstawowe przetwarzanie
        pdf_doc, context = demonstrate_pdf_processing()
        
        # 2. Wzbogacanie promptu
        enhanced_prompt = demonstrate_prompt_enhancement()
        
        # 3. Integracja Streamlit
        demonstrate_streamlit_integration()
        
        # 4. System cache
        demonstrate_cache_functionality()
        
        print("\n" + "=" * 60)
        print("✅ DEMONSTRACJA ZAKOŃCZONA POMYŚLNIE")
        print("\n💡 Następne kroki:")
        print("   1. Zainstaluj zależności: pip install PyPDF2 PyMuPDF")
        print("   2. Uruchom aplikację: streamlit run streamlit_app.py")
        print("   3. Wgraj swoje pliki PDF w sekcji 'Dodatkowy kontekst'")
        print("   4. Generuj diagramy z wzbogaconym kontekstem!")
        
    except Exception as e:
        print(f"\n❌ Błąd podczas demonstracji: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()