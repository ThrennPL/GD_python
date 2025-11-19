"""
Skrypt do tworzenia przykładowego PDF dla testowania integracji.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import tempfile
import os

def create_test_pdf():
    """Tworzy przykładowy plik PDF do testowania."""
    
    try:
        # Spróbuj użyć reportlab jeśli dostępny
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        test_pdf_path = "test_documents/test_process_document.pdf"
        os.makedirs("test_documents", exist_ok=True)
        
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        width, height = letter
        
        # Tytuł
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "PROCES OBSŁUGI ZAMÓWIENIA E-COMMERCE")
        
        # Treść
        content = [
            "",
            "1. WPROWADZENIE",
            "Niniejszy dokument opisuje pełny proces obsługi zamówienia",
            "w systemie e-commerce od momentu złożenia przez klienta do dostawy produktu.",
            "",
            "2. UCZESTNICY PROCESU",
            "- Klient - osoba składająca zamówienie", 
            "- System e-commerce - platforma obsługi zamówień",
            "- Centrum logistyczne - magazyn i przygotowanie wysyłki",
            "- Kurier - dostawca zewnętrzny",
            "- System płatności - bramka płatnicza",
            "- Dział obsługi klienta - wsparcie techniczne",
            "",
            "3. GŁÓWNE ETAPY PROCESU",
            "",
            "Krok 1: Składanie zamówienia",
            "Klient przegląda katalog produktów w systemie e-commerce,",
            "dodaje wybrane pozycje do koszyka i przechodzi do procesu zamówienia.",
            "",
            "Krok 2: Weryfikacja danych",
            "System e-commerce sprawdza poprawność danych klienta,",
            "dostępność produktów w magazynie oraz kalkuluje koszty wysyłki.",
            "",
            "Krok 3: Przetwarzanie płatności",
            "W przypadku pozytywnej weryfikacji, zamówienie jest przekazywane",
            "do systemu płatności w celu autoryzacji transakcji.",
            "",
            "Krok 4: Potwierdzenie zamówienia",
            "Po udanej płatności system generuje potwierdzenie zamówienia",
            "i wysyła powiadomienie do klienta oraz centrum logistycznego.",
            "",
            "Krok 5: Przygotowanie do wysyłki",
            "Centrum logistyczne przygotowuje produkty, pakuje je",
            "i przekazuje kurierowi.",
            "",
            "Krok 6: Dostawa",
            "Kurier dostarcza zamówienie do klienta i aktualizuje status w systemie."
        ]
        
        y_position = height - 100
        c.setFont("Helvetica", 10)
        
        for line in content:
            if y_position < 50:
                c.showPage()
                y_position = height - 50
                c.setFont("Helvetica", 10)
            
            if line.startswith(("1.", "2.", "3.")):
                c.setFont("Helvetica-Bold", 12)
            elif line.startswith("Krok"):
                c.setFont("Helvetica-Bold", 10)
            else:
                c.setFont("Helvetica", 10)
            
            c.drawString(50, y_position, line)
            y_position -= 15
        
        c.save()
        print(f"✅ Utworzono plik testowy: {test_pdf_path}")
        return test_pdf_path
        
    except ImportError:
        # Fallback - utwórz prosty plik tekstowy jako symulację PDF
        test_txt_path = "test_documents/test_process_document.txt"
        os.makedirs("test_documents", exist_ok=True)
        
        content = """PROCES OBSŁUGI ZAMÓWIENIA E-COMMERCE

1. WPROWADZENIE
Niniejszy dokument opisuje pełny proces obsługi zamówienia w systemie e-commerce od momentu złożenia przez klienta do dostawy produktu.

2. UCZESTNICY PROCESU
- Klient - osoba składająca zamówienie
- System e-commerce - platforma obsługi zamówień  
- Centrum logistyczne - magazyn i przygotowanie wysyłki
- Kurier - dostawca zewnętrzny
- System płatności - bramka płatnicza
- Dział obsługi klienta - wsparcie techniczne

3. GŁÓWNE ETAPY PROCESU

Krok 1: Składanie zamówienia
Klient przegląda katalog produktów w systemie e-commerce, dodaje wybrane pozycje do koszyka i przechodzi do procesu zamówienia.

Krok 2: Weryfikacja danych
System e-commerce sprawdza poprawność danych klienta, dostępność produktów w magazynie oraz kalkuluje koszty wysyłki.

Krok 3: Przetwarzanie płatności  
W przypadku pozytywnej weryfikacji, zamówienie jest przekazywane do systemu płatności w celu autoryzacji transakcji.

Krok 4: Potwierdzenie zamówienia
Po udanej płatności system generuje potwierdzenie zamówienia i wysyła powiadomienie do klienta oraz centrum logistycznego.

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
- API kurierów (DHL, UPS, InPost)"""
        
        with open(test_txt_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"⚠️  ReportLab niedostępny, utworzono plik tekstowy: {test_txt_path}")
        print("💡 Możesz używać tego pliku do testów lub zainstalować reportlab: pip install reportlab")
        return test_txt_path

if __name__ == "__main__":
    create_test_pdf()