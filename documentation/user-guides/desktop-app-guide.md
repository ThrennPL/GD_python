# Przewodnik Użytkownika - Aplikacja Desktop

## 🖥️ Rozpoczynanie Pracy

### Uruchomienie Aplikacji

#### Windows
```bash
# Metoda 1: Podwójne kliknięcie
main.py

# Metoda 2: Terminal/PowerShell
python main.py

# Metoda 3: Virtual Environment
.\venv\Scripts\activate
python main.py
```

#### macOS/Linux
```bash
# Terminal
python3 main.py

# Lub z virtual environment
source venv/bin/activate
python main.py
```

### Pierwsze Uruchomienie

Po uruchomieniu aplikacji zobaczysz główne okno z:

1. **Pole tekstowe** - wprowadzanie opisu procesu
2. **Przyciski wyboru** - PlantUML lub BPMN
3. **Menu konfiguracji** - ustawienia AI providera
4. **Panel wyników** - wyświetlanie wygenerowanych diagramów

## 🔧 Konfiguracja Wstępna

### 1. Ustawienia AI Provider

**Krok 1:** Otwórz menu `Ustawienia > Konfiguracja AI`

**Krok 2:** Wybierz preferowanego providera:
- **OpenAI GPT-4**: Najwyższa jakość, wymaga płatnego API key
- **Google Gemini**: Dobre wyniki, darmowy tier dostępny
- **Claude**: Wysoka jakość analizy tekstu
- **Ollama**: Lokalne przetwarzanie, bez kosztów API

**Krok 3:** Wprowadź API key (jeśli wymagany):

```
OpenAI: sk-proj-xxxxxxxxxxxxxxxxxxxxxxx
Gemini: AIzaSyxxxxxxxxxxxxxxxxxxxxxxx
Claude: sk-ant-apixxxxxxxxxxxxxxxxxxxxxxx
```

**Krok 4:** Testuj połączenie przyciskiem `Test Connection`

### 2. Ustawienia Językowe

**Lokalizacja:** `Ustawienia > Język`

**Dostępne opcje:**
- 🇵🇱 Polski (domyślny)
- 🇬🇧 English

**Wpływ na:**
- Interfejs aplikacji
- Szablony promptów
- Komunikaty błędów
- Etykiety diagramów

### 3. Ustawienia PlantUML

**Lokalizacja:** `Ustawienia > PlantUML`

**Opcje renderowania:**
- **Local**: Używa lokalnego PlantUML.jar (szybsze, offline)
- **Online**: Używa serwera plantuml.com (nie wymaga instalacji)

**Konfiguracja Local PlantUML:**
1. Pobierz `plantuml.jar` z [oficjalnej strony](https://plantuml.com/download)
2. Umieść w folderze aplikacji
3. Ustaw ścieżkę w `Ustawienia > PlantUML > Ścieżka JAR`

## 📝 Generowanie Diagramów PlantUML

### Podstawowy Przepływ Pracy

#### 1. Wprowadzenie Opisu

**Dobry opis zawiera:**
- Jasno zdefiniowany cel procesu
- Listę głównych kroków
- Uczestników (aktorów)
- Warunki i decyzje

**Przykład dobrego opisu:**
```
Proces obsługi zamówienia klienta w sklepie internetowym:

1. Klient przegląda produkty i dodaje do koszyka
2. Klient przechodzi do płatności
3. System weryfikuje dostępność produktów
4. System przetwarza płatność
5. Jeśli płatność udana - generuje zamówienie
6. Magazyn przygotowuje przesyłkę
7. Klient otrzymuje potwierdzenie i tracking
8. Kurier dostarcza przesyłkę

Aktorzy: Klient, System, Magazyn, Kurier
```

#### 2. Wybór Typu Diagramu

**Activity Diagram** (zalecany dla procesów biznesowych):
- Przepływ aktywności
- Punkty decyzyjne
- Równoległe ścieżki
- Start i końcowe stany

**Sequence Diagram** (dla interakcji systemowych):
- Komunikacja między objektami
- Chronologia wywołań
- Odpowiedzi i komunikaty

**Class Diagram** (dla modelowania danych):
- Struktura klas
- Relacje między objektami
- Atrybuty i metody

#### 3. Generowanie

1. **Kliknij** przycisk `Generuj PlantUML`
2. **Czekaj** na przetworzenie (5-30 sekund)
3. **Sprawdź** wynik w panelu podglądu

### Zaawansowane Funkcje PlantUML

#### 1. Użycie Szablonów

**Dostęp:** `Menu > Szablony > PlantUML`

**Dostępne szablony:**
- **Proces Biznesowy**: Optymalizowany dla przepływów biznesowych
- **Analiza Systemu**: Dla diagramów technicznych
- **User Stories**: Dla przypadków użycia
- **Data Flow**: Dla przepływu danych

**Zastosowanie szablonu:**
1. Wybierz szablon z listy rozwijanej
2. Wprowadź opis procesu
3. Szablon zostanie automatycznie zastosowany

#### 2. Personalizacja Wyników

**Dostępne opcje:**
- **Styl diagramu**: UML, Business, Technical
- **Poziom szczegółowości**: Podstawowy, Rozszerzony, Pełny
- **Format kolorów**: Domyślny, Monochroniczny, Kolorowy

#### 3. Edycja Ręczna

**Funkcjonalność:**
- Edycja wygenerowanego kodu PlantUML
- Podgląd na żywo podczas edycji
- Syntax highlighting
- Automatyczne uzupełnianie

**Dostęp:**
1. Po generacji kliknij `Edytuj kod`
2. Modyfikuj kod w edytorze
3. Kliknij `Renderuj` aby zobaczyć zmiany

## 🔄 Generowanie Diagramów BPMN

### Proces BPMN v2

#### 1. Przygotowanie Opisu

**BPMN wymaga bardziej szczegółowego opisu:**
```
Tytuł: Proces rekrutacji nowego pracownika

Opis procesu:
- HR otrzymuje zgłoszenie o potrzebie rekrutacyjnej
- HR publikuje ogłoszenie o pracę
- Kandydaci składają aplikacje
- HR przeprowadza wstępną selekcję CV
- Wybrani kandydaci zapraszani na rozmowę
- Przeprowadzane są rozmowy kwalifikacyjne
- Podejmowana jest decyzja o zatrudnieniu
- Wybrany kandydat otrzymuje ofertę pracy
- Po akceptacji - proces onboardingu

Pule odpowiedzialności:
- HR (Human Resources)
- Menedżer ds. rekrutacji
- Kandydat
- Przełożony bezpośredni

Systemy:
- ATS (Applicant Tracking System)
- System HR
- Email
```

#### 2. Konfiguracja BPMN

**Parametry jakości:**
- **Próg jakości**: 0.8 (zalecane dla produkcji)
- **Maksymalne iteracje**: 10
- **Typ procesu**: Business/Technical/Workflow
- **Obszar poprawy**: Structure/Naming/Flow/All

#### 3. Proces Generowania z Optymalizacją

**Etapy automatycznej optymalizacji:**

1. **Generacja wstępna** (20%)
   - Tworzenie podstawowej struktury
   - Identyfikacja głównych aktywności

2. **Analiza jakości** (40%)
   - Sprawdzanie poprawności składniowej
   - Walidacja zgodności ze standardem BPMN 2.0

3. **Optymalizacja** (60-90%)
   - Poprawa nazw aktywności
   - Optymalizacja przepływu
   - Dodanie bramek decyzyjnych

4. **Finalizacja** (100%)
   - Końcowa walidacja
   - Generowanie wynikowego XML

### Monitorowanie Procesu BPMN

**Progress Bar pokazuje:**
- Aktualny etap przetwarzania
- Procentowy postęp
- Liczbę wykonanych iteracji
- Aktualny wynik jakości

**Możliwe akcje podczas przetwarzania:**
- **Anuluj**: Przerywa proces optymalizacji
- **Pomiń optymalizację**: Używa bieżącego wyniku

## 💾 Zarządzanie Plikami

### Eksport Wyników

#### 1. Opcje Eksportu

**Format PlantUML:**
- `.puml` - kod źródłowy PlantUML
- `.svg` - grafika wektorowa (zalecana)
- `.png` - grafika rastrowa
- `.pdf` - dokument PDF

**Format BPMN:**
- `.bpmn` - kod XML BPMN 2.0
- `.svg` - wizualizacja graficzna
- `.xmi` - do importu w Enterprise Architect

#### 2. Eksport Pojedynczy

1. **Wygeneruj** diagram
2. **Kliknij prawym** na rezultat
3. **Wybierz** `Eksportuj jako...`
4. **Określ** lokalizację i format
5. **Potwierdź** zapisanie

#### 3. Eksport Zbiorczy

**Funkcjonalność:**
- Eksport wszystkich wygenerowanych diagramów
- Wybór formatów do eksportu
- Automatyczna organizacja w foldery
- Opcja kompresji ZIP

**Dostęp:**
`Menu > Plik > Eksportuj wszystkie`

### Import PDF

#### 1. Dodawanie Plików PDF

**Metody dodawania:**
- **Przeciągnij i upuść** pliki do aplikacji
- **Menu > Plik > Importuj PDF**
- **Przycisk** `Dodaj PDF` w głównym oknie

**Obsługiwane formaty:**
- PDF (główny)
- TXT (dodatkowy tekst)
- DOC/DOCX (przez konwersję)

#### 2. Przetwarzanie PDF

**Automatyczne funkcje:**
- Ekstraktacja tekstu z całego dokumentu
- Identyfikacja tabel i struktur
- Rozpoznawanie procesów biznesowych
- Wyodrębnienie kluczowych informacji

**Opcje konfiguracji:**
- **Maksymalna liczba stron**: domyślnie 50
- **Ekstraktacja tabel**: włączona/wyłączona
- **Tryb analizy**: AI/Basic

#### 3. Wykorzystanie Kontekstu PDF

**Wzbogacenie opisu:**
Po przetworzeniu PDF, aplikacja automatycznie:
- Dodaje znalezione procesy do opisu
- Identyfikuje uczestników i role
- Rozpoznaje systemy i narzędzia
- Sugeruje strukturę diagramu

**Przykład wykorzystania:**
1. Załaduj PDF z dokumentacją procesu
2. Aplikacja wyekstraktuje kluczowe informacje
3. Wprowadź podstawowy opis procesu
4. PDF context zostanie automatycznie połączony
5. Generuj wzbogacony diagram

## ⚙️ Ustawienia Zaawansowane

### Optymalizacja Wydajności

#### 1. Ustawienia Pamięci

**Lokalizacja:** `Ustawienia > Wydajność > Pamięć`

**Konfiguracja:**
- **Maksymalne użycie pamięci**: 2048 MB (domyślnie)
- **Cache dla obrazów**: 256 MB
- **Automatyczne czyszczenie**: co 50 operacji

#### 2. Ustawienia Sieci

**Timeouts:**
- **Połączenie z AI**: 60 sekund
- **Pobieranie wyników**: 120 sekund
- **Retry attempts**: 3 próby

**Proxy (jeśli wymagany):**
```
HTTP Proxy: http://proxy.company.com:8080
HTTPS Proxy: https://proxy.company.com:8080
Username: your_username
Password: your_password
```

### Backup i Restore

#### 1. Automatyczny Backup

**Konfiguracja:**
- **Włącz auto-backup**: Tak/Nie
- **Częstotliwość**: Dziennie/Tygodniowo
- **Lokalizacja**: `./backups/` (domyślna)
- **Zachowaj kopie**: 30 dni

**Co jest backupowane:**
- Ustawienia aplikacji
- Zapisane diagramy
- Cache templates
- Logi operacji

#### 2. Manual Backup

**Dostęp:** `Menu > Plik > Backup`

**Opcje:**
- **Kompletny backup**: Wszystkie dane
- **Tylko ustawienia**: Konfiguracja
- **Tylko wyniki**: Wygenerowane diagramy

#### 3. Restore

**Procedura:**
1. `Menu > Plik > Restore`
2. Wybierz plik backup (.zip)
3. Określ co przywrócić
4. Restart aplikacji (jeśli wymagany)

## 🔍 Rozwiązywanie Problemów

### Częste Problemy

#### 1. "Błąd połączenia z AI"

**Przyczyny:**
- Nieprawidłowy API key
- Przekroczony limit requests
- Problemy z internetem
- Provider API niedostępny

**Rozwiązanie:**
1. Sprawdź API key w `Ustawienia > AI Provider`
2. Test Connection
3. Sprawdź stan konta u providera
4. Zmień providera (jeśli dostępny)

#### 2. "PlantUML rendering error"

**Przyczyny:**
- Nieprawidłowy kod PlantUML
- Brak połączenia z internetem (tryb online)
- Uszkodzony plantuml.jar (tryb local)

**Rozwiązanie:**
1. Sprawdź kod w edytorze online: http://plantuml.com/plantuml
2. Przełącz między local/online rendering
3. Pobierz najnowszy plantuml.jar

#### 3. "Niska jakość BPMN"

**Przyczyny:**
- Zbyt ogólny opis procesu
- Brak szczegółów o uczestnikach
- Niewystarczający kontekst

**Rozwiązanie:**
1. Dodaj więcej szczegółów do opisu
2. Określ jasno role i odpowiedzialności
3. Zwiększ liczbę maksymalnych iteracji
4. Obniż próg jakości tymczasowo

#### 4. "PDF nie został przetworzony"

**Przyczyny:**
- Plik uszkodzony
- PDF tylko z obrazami (bez tekstu)
- Przekroczenie limitu stron
- Brak uprawnień do pliku

**Rozwiązanie:**
1. Sprawdź czy PDF otwiera się w innych aplikacjach
2. Użyj PDF z tekstem (nie skanów)
3. Zwiększ limit stron w ustawieniach
4. Sprawdź uprawnienia do pliku

### Diagnostyka

#### 1. Logi Aplikacji

**Lokalizacja:** `Menu > Pomoc > Otwórz logi`

**Typy logów:**
- `application.log` - główne operacje
- `ai_requests.log` - komunikacja z AI
- `errors.log` - błędy i wyjątki
- `performance.log` - metryki wydajności

#### 2. Test Systemu

**Dostęp:** `Menu > Pomoc > Diagnostyka`

**Sprawdza:**
- Połączenia z AI providers
- Stan PlantUML renderer
- Dostępność pamięci
- Uprawnienia do plików
- Wersje dependencies

#### 3. Debug Mode

**Aktywacja:**
1. `Ustawienia > Zaawansowane > Debug Mode`
2. Restart aplikacji

**Dodatkowe funkcje w debug:**
- Szczegółowe logi
- Zapisywanie intermediate files
- Performance monitoring
- Stack traces dla błędów

## 📚 Skróty Klawiszowe

### Nawigacja
- `Ctrl + N`: Nowy projekt
- `Ctrl + O`: Otwórz plik
- `Ctrl + S`: Zapisz wyniki
- `Ctrl + E`: Eksportuj
- `Ctrl + Q`: Zamknij aplikację

### Generowanie
- `F5`: Generuj PlantUML
- `F6`: Generuj BPMN  
- `F9`: Toggle preview
- `Esc`: Anuluj operację

### Edycja
- `Ctrl + Z`: Cofnij
- `Ctrl + Y`: Ponów
- `Ctrl + A`: Zaznacz wszystko
- `Ctrl + C`: Kopiuj
- `Ctrl + V`: Wklej

### Widok
- `F11`: Pełny ekran
- `Ctrl + +`: Powiększ diagram
- `Ctrl + -`: Pomniejsz diagram
- `Ctrl + 0`: Resetuj zoom

---

*Przewodnik użytkownika jest regularnie aktualizowany. Sprawdzaj `Menu > Pomoc > Sprawdź aktualizacje` dla najnowszej wersji.*