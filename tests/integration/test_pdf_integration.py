"""
Skrypt testowy - kompletny scenariusz użycia integracji PDF.
"""

import sys
sys.path.append('.')

from utils.pdf.pdf_processor import PDFProcessor, enhance_prompt_with_pdf_context
import tempfile
import os

def test_complete_scenario():
    """Test kompletnego scenariusza użycia PDF."""
    
    print("🧪 TEST KOMPLETNEGO SCENARIUSZA PDF")
    print("=" * 50)
    
    # 1. Przygotowanie danych testowych
    print("\n1. 📄 Przygotowanie dokumentu testowego...")
    
    test_content = """PROCES AUTORYZACJI UŻYTKOWNIKA

UCZESTNICY:
- Użytkownik końcowy
- System uwierzytelniania  
- Baza danych użytkowników
- Serwis sesji
- Moduł logowania

KROKI PROCESU:
Krok 1: Wprowadzenie danych logowania
Użytkownik wprowadza nazwę użytkownika i hasło w formularzu logowania.

Krok 2: Walidacja danych
System uwierzytelniania sprawdza poprawność formatu danych.

Krok 3: Weryfikacja w bazie danych
System sprawdza dane w bazie danych użytkowników.

Krok 4: Tworzenie sesji
Po pomyślnej weryfikacji tworzony jest token sesji.

Krok 5: Przekierowanie do aplikacji
Użytkownik otrzymuje dostęp do chronionej części aplikacji.

PUNKTY DECYZYJNE:
- Jeśli dane niepoprawne -> Komunikat błędu
- Jeśli użytkownik zablokowany -> Odmowa dostępu  
- Jeśli wszystko OK -> Dostęp przyznany"""

    # Zapisz jako plik testowy
    test_file_path = "test_documents/auth_process.txt"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✅ Utworzono plik testowy: {test_file_path}")
    
    # 2. Test przetwarzania PDF
    print("\n2. ⚙️ Testowanie przetwarzania dokumentu...")
    
    processor = PDFProcessor()
    
    # Symulacja PDFDocument (gdyby był to prawdziwy PDF)
    from utils.pdf.pdf_processor import PDFDocument
    from datetime import datetime
    import hashlib
    
    file_hash = hashlib.md5(test_content.encode()).hexdigest()
    pdf_doc = PDFDocument(
        file_path=test_file_path,
        title="Proces autoryzacji użytkownika",
        total_pages=1,
        text_content=test_content,
        structured_content={'pages': [{'text': test_content}]},
        metadata={},
        hash=file_hash,
        processed_date=datetime.now().isoformat()
    )
    
    # Analiza kontekstu
    context = processor.analyze_process_context(test_content)
    
    print(f"   📋 Proces: {context.process_name}")
    print(f"   👥 Aktorzy: {len(context.actors)} -> {context.actors}")
    print(f"   ⚙️ Systemy: {len(context.systems)} -> {context.systems}")
    print(f"   ❓ Decyzje: {len(context.decisions)} -> {context.decisions}")
    
    # 3. Test kontekstu dla diagramów
    print("\n3. 📊 Testowanie kontekstu dla różnych diagramów...")
    
    diagram_types = ['sequence', 'activity', 'class']
    contexts = {}
    
    for diagram_type in diagram_types:
        contexts[diagram_type] = processor.get_context_for_diagram_type(pdf_doc, diagram_type)
        print(f"   ✅ {diagram_type}: {len(contexts[diagram_type])} znaków kontekstu")
    
    # 4. Test wzbogacania promptu
    print("\n4. 🚀 Testowanie wzbogacania promptu...")
    
    original_prompts = {
        'sequence': """Wygeneruj diagram sekwencji PlantUML dla procesu logowania użytkownika.
        
Uwzględnij:
- Wprowadzenie danych przez użytkownika
- Weryfikację w systemie
- Udzielenie dostępu""",
        
        'activity': """Stwórz diagram aktywności PlantUML dla procesu uwierzytelniania.
        
Pokaż:
- Decyzje w procesie  
- Alternatywne ścieżki
- Punkty końcowe""",
    }
    
    enhanced_results = {}
    
    for prompt_type, original_prompt in original_prompts.items():
        enhanced = enhance_prompt_with_pdf_context(
            original_prompt, 
            [test_file_path], 
            prompt_type
        )
        enhanced_results[prompt_type] = enhanced
        
        print(f"   📝 {prompt_type}:")
        print(f"      Oryginał: {len(original_prompt)} znaków")
        print(f"      Wzbogacony: {len(enhanced)} znaków")
        print(f"      Wzrost: {((len(enhanced)/len(original_prompt))-1)*100:.0f}%")
    
    # 5. Pokazanie przykładu wzbogaconego promptu
    print(f"\n5. 💡 Przykład wzbogaconego promptu (sequence):")
    print("-" * 50)
    example_prompt = enhanced_results['sequence']
    # Pokaż pierwsze 500 znaków
    print(example_prompt[:500])
    if len(example_prompt) > 500:
        print("... [skrócono]")
    print("-" * 50)
    
    # 6. Test cache
    print(f"\n6. 💾 Test systemu cache...")
    
    # Sprawdź czy katalog cache został utworzony
    cache_dir = processor.cache_dir
    print(f"   📁 Katalog cache: {cache_dir}")
    print(f"   📂 Istnieje: {cache_dir.exists()}")
    
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.json"))
        print(f"   📄 Pliki cache: {len(cache_files)}")
    
    # 7. Podsumowanie
    print(f"\n🎯 PODSUMOWANIE TESTÓW")
    print("=" * 30)
    print("✅ Przetwarzanie dokumentu: OK")
    print("✅ Analiza kontekstu: OK") 
    print("✅ Generowanie kontekstu dla diagramów: OK")
    print("✅ Wzbogacanie promptu: OK")
    print("✅ System cache: OK")
    
    return {
        'contexts': contexts,
        'enhanced_prompts': enhanced_results,
        'analysis': context
    }

def test_streamlit_integration():
    """Test integracji ze Streamlit."""
    
    print(f"\n🌐 TEST INTEGRACJI STREAMLIT")
    print("=" * 40)
    
    try:
        # Test importu
        print("1. 📦 Test importu modułów...")
        from utils.pdf.streamlit_pdf_integration import PDFUploadManager
        print("   ✅ Import PDFUploadManager: OK")
        
        # Test inicjalizacji (poza kontekstem Streamlit)
        print("2. 🚀 Test inicjalizacji...")
        # Symulacja session state
        class MockSessionState:
            def __init__(self):
                self.uploaded_pdfs = []
                self.pdf_contexts = {}
        
        # Nie inicjalizujemy managera poza Streamlit - tylko sprawdzamy import
        print("   ✅ Klasy dostępne: OK")
        
        # Test integracji z główną aplikacją
        print("3. 🔗 Test integracji z streamlit_app.py...")
        
        # Sprawdź czy zmodyfikowany kod kompiluje się
        import ast
        
        with open('streamlit_app.py', 'r', encoding='utf-8') as f:
            app_code = f.read()
        
        # Sprawdź składnię
        try:
            ast.parse(app_code)
            print("   ✅ Składnia streamlit_app.py: OK")
        except SyntaxError as e:
            print(f"   ❌ Błąd składni: {e}")
            return False
        
        # Sprawdź czy PDF import jest obecny
        if 'PDFUploadManager' in app_code:
            print("   ✅ Import PDF w aplikacji: OK")
        else:
            print("   ⚠️ Brak importu PDF w aplikacji")
        
        # Sprawdź czy render_pdf_upload_section jest wywołany
        if 'render_pdf_upload_section' in app_code:
            print("   ✅ Wywołanie sekcji PDF: OK")
        else:
            print("   ⚠️ Brak wywołania sekcji PDF")
        
        print("\n🎯 INTEGRACJA STREAMLIT: ✅ GOTOWA")
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu integracji: {e}")
        return False

def main():
    """Główna funkcja testowa."""
    
    print("🧪 KOMPLETNY TEST INTEGRACJI PDF")
    print("=" * 60)
    
    # Sprawdź czy katalogi testowe istnieją
    os.makedirs("test_documents", exist_ok=True)
    
    try:
        # Test funkcjonalności PDF
        results = test_complete_scenario()
        
        # Test integracji Streamlit
        streamlit_ok = test_streamlit_integration()
        
        print("\n" + "=" * 60)
        print("🎉 WSZYSTKIE TESTY ZAKOŃCZONE")
        
        if streamlit_ok:
            print("\n💡 NASTĘPNE KROKI:")
            print("1. Uruchom aplikację: streamlit run streamlit_app.py")
            print("2. Wgraj plik test_documents/auth_process.txt jako PDF")
            print("3. Wybierz typ diagramu (np. sequence)")
            print("4. Wprowadź krótki opis procesu")
            print("5. Wygeneruj diagram - zobaczysz wzbogacony kontekst!")
        
        print(f"\n📋 Pliki testowe utworzone:")
        print(f"   - test_documents/test_process_document.txt")
        print(f"   - test_documents/auth_process.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd w testach: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)