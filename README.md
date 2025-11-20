# Generator i Weryfikator Diagramów UML/BPMN z AI

**Status projektu**: ✅ **REORGANIZACJA ZAKOŃCZONA** (2025-11-20) - Nowa profesjonalna struktura + Smart PDF Analysis System

Aplikacja do generowania, wizualizacji i weryfikacji diagramów UML (PlantUML) oraz BPMN (XML) na podstawie opisu procesu, z wykorzystaniem modeli AI (np. LLM). Projekt oferuje zarówno wersję desktopową (PyQt5), jak i webową (Streamlit), umożliwiając wybór szablonu promptu, typu diagramu, walidację opisu procesu oraz automatyczną weryfikację kodu PlantUML. 

**🆕 Najnowsze funkcje:**
- **🧠 Smart PDF Analysis System** - inteligentne wykrywanie możliwości modelu i automatyczny wybór metody analizy
- **📁 Zreorganizowana struktura** - profesjonalna organizacja kodu (src/, tests/, tools/, config/)
- **⚡ Real-time progress tracking** - informacje o postępie w czasie rzeczywistym
- **🔄 Graceful fallback** - automatyczne przełączanie metod przy błędach

---

## Szybki start (dla nowych użytkowników)

1. **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/ThrennPL/GD_python
    cd GD_python
    ```
2. **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Pobierz `plantuml.jar`**  
   Pobierz plik ze strony [PlantUML Download](https://plantuml.com/download) i umieść go w katalogu projektu.
4. **Sprawdź Java:**  
   Upewnij się, że masz zainstalowaną Javę (polecenie w terminalu):
    ```bash
    java -version
    ```
5. **Utwórz plik `.env`:**  
   Skopiuj poniższą konfigurację do pliku `.env` w katalogu głównym projektu i uzupełnij wymagane pola (np. `API_KEY` dla Gemini/OpenAI, dane bazy jeśli chcesz zapisywać historię):
    ```
    PLANTUML_JAR_PATH=plantuml.jar
    PLANTUML_GENERATOR_TYPE=local
    API_URL=http://localhost:1234/v1/models
    #API_URL=https://api.openai.com/v1/models
    #API_URL=https://generativelanguage.googleapis.com/v1beta/models
    API_DEFAULT_MODEL=
    CHAT_URL=http://localhost:1234/v1/chat/completions
    #CHAT_URL=https://api.openai.com/v1/chat/completions
    #CHAT_URL=https://generativelanguage.googleapis.com/v1v1beta/chat/completions
    API_KEY=
    MODEL_PROVIDER=local
    #MODEL_PROVIDER=openai
    #MODEL_PROVIDER=gemini
    DB_PROVIDER=
    DB_HOST=
    DB_PORT=
    DB_NAME=
    DB_USER=
    DB_PASSWORD=
    ```
6. **Uruchom lokalny serwer AI (np. LM Studio):**  
   Jeśli korzystasz z lokalnego modelu, uruchom LM Studio i sprawdź, czy jest dostępny pod `http://localhost:1234`.
7. **Uruchom aplikację:**
   - **Streamlit:**  
     ```bash
     streamlit run src/streamlit_app.py
     # lub
     scripts/run_streamlit.bat
     ```
   - **PyQt5:**  
     ```bash
     python main.py
     ```

---

## Funkcje

  * Generowanie kodu PlantUML lub XML BPMN na podstawie opisu procesu
  * **🆕 Integracja z plikami PDF** - wzbogacanie kontekstu diagramów o dane z dokumentów PDF
  * Wybór szablonu promptu i typu diagramu (sekwencja, aktywność, klasa, komponent, stan, przypadek użycia itp.)
  * Wizualizacja diagramów PlantUML (SVG)
  * **🆕 Edycja kodu PlantUML** - możliwość edycji wygenerowanego kodu bezpośrednio w aplikacji
  * Automatyczna weryfikacja kodu PlantUML w przypadku błędów generowania SVG
  * **🆕 Ulepszona weryfikacja błędów** - bardziej dokładne wykrywanie błędów składni PlantUML
  * **🆕 Wybór języka z GUI** - dynamiczna zmiana języka interfejsu w trakcie pracy
  * Walidacja opisów procesów przez AI
  * Historia konwersacji z modelem AI
  * Obsługa wielu modeli AI (lokalnych lub poprzez API, np. OpenAI, Gemini)
  * Pobieranie wygenerowanych diagramów w formatach: PlantUML, SVG, XMI
  * Specjalne opcje dla diagramów BPMN (poziom złożoności, reguła walidacji, format wyjściowy, domena)
  * Zapis zapytań i odpowiedzi z modelu do bazy danych (mySQL, PostgreSQL)
  * **Dwie wersje językowe interfejsu i promptów (angielska i polska)**
  * Przykładowe prompty testowe dla branży bankowej

---

## 🆕 Smart PDF Analysis System

**Zaawansowany system analizy PDF z AI, który automatycznie wykrywa możliwości modelu i inteligentnie wybiera metodę analizy.**

### 🎯 Kluczowe funkcje:
- **Automatyczne wykrywanie możliwości modelu** - system sprawdza czy model obsługuje bezpośrednie przesyłanie PDF
- **Inteligentny wybór metody** - na podstawie rozmiaru pliku i możliwości modelu
- **Real-time progress tracking** - informacje o postępie analizy w czasie rzeczywistym
- **Hierarchiczny fallback** - automatyczne przełączanie między metodami przy błędach
- **Smart method selection** - małe pliki (Direct PDF, wysoka jakość), duże pliki (Text Extraction, szybciej)

### 📊 Performance Metrics:
| Metoda | Czas/MB | Jakość | Elementy Biznesowe |
|--------|---------|--------|---------|
| Direct PDF | 11.5s | Wysoka | 75% accuracy |
| Text Extraction | 3.6s | Średnia | Podstawowa |

### ⚙️ Konfiguracja:
```env
# Smart PDF Analysis
PDF_ANALYSIS_MODEL=models/gemini-2.0-flash
PDF_ANALYSIS_MODE=ai
PDF_DIRECT_THRESHOLD_MB=2.0
PDF_MAX_PAGES_TEXT=50
PDF_CHUNK_SIZE=4000
```

### 🚀 Wykorzystanie:
1. **Automatyczne wykrywanie** - system sprawdza możliwości modelu
2. **Smart selection** - wybiera optymalną metodę (Direct PDF ≤2MB, Text Extraction >2MB)
3. **Progress tracking** - real-time feedback o postępie
4. **Graceful fallback** - automatyczne przełączanie przy błędach
5. **Enhanced context** - wzbogacony kontekst biznesowy w promptach

### 🎯 Modele obsługujące Direct PDF:
- ✅ Gemini 2.0 Flash
- ✅ Gemini 1.5 Pro/Flash
- ❌ OpenAI models (fallback do text extraction)
- ❌ Local models (fallback do text extraction)

---

## 🆕 Edycja kodu PlantUML

**Nowa funkcjonalność umożliwiająca bezpośrednią edycję wygenerowanego kodu PlantUML.**

### Możliwości:
- **Edycja kodu** bezpośrednio w aplikacji przez przycisk "Kod PlantUML"
- **Podgląd w czasie rzeczywistym** - natychmiastowe aktualizacje diagramu
- **Zapisywanie zmian** - możliwość aktualizacji diagramu po edycji
- **Intuitive UI** - wygodny edytor z podświetlaniem składni

### Jak używać:
1. **Wygeneruj diagram** używając AI
2. **Kliknij "Kod PlantUML"** aby otworzyć edytor
3. **Edytuj kod** bezpośrednio w oknie dialogowym
4. **Kliknij "Aktualizuj diagram"** aby zastosować zmiany
5. **Diagram zostanie automatycznie zaktualizowany**

### Korzyści:
- **Szybkie poprawki** bez regenerowania przez AI
- **Fine-tuning** szczegółów diagramu
- **Nauka składni PlantUML** przez praktykę
- **Kontrola nad końcowym rezultatem**

---

## Eksport XMI

Eksport XMI jest obecnie dostępny **tylko dla diagramu klas, sekwencji, aktywnmości i komponentów (Class Diagram, Sequence Diagram, Activity Diagram, Component Diagram),**. Przycisk „Zapisz XMI” (również menu kontekstowe) jest aktywny wyłącznie, gdy aktywna zakładka zawiera diagram klas, diagram sekwencji lub diagram aktywności. Dla innych typów diagramów (np. przypadków użycia, komponentów) eksport XMI nie jest jeszcze obsługiwany. Po imporcie do EA elementy mogą wymagać ręcznego uporządkowania.

---

## Obsługa Zakładek (dla wersji desktopowej)

Aplikacja desktopowa umożliwia pracę z wieloma diagramami w zakładkach. Po przełączeniu zakładki aplikacja automatycznie sprawdza typ diagramu i aktywuje/dezaktywuje przycisk eksportu XMI.

---

## Generowanie Diagramów SVG

Diagramy SVG mogą być generowane na dwa sposoby, zależnie od ustawienia parametru `plantuml_generator_type`:

  * **`plantuml_generator_type = local`**: Diagramy SVG są generowane lokalnie przy użyciu `plantuml.jar` i Javy. Upewnij się, że oba są dostępne w Twoim systemie.
  * **`plantuml_generator_type = www`**: Diagramy SVG są generowane z wykorzystaniem strony [www.plantuml.com](https://plantuml.com/).

---

## Wymagania

  * Python 3.7+ (dla Streamlit) lub Python 3.8+ (dla PyQt5)
  * Lokalny serwer AI (np. LM Studio) uruchomiony na porcie `http://localhost:1234` (jeśli korzystasz z lokalnego modelu)
  * Zależności z pliku `config/requirements.txt`
  * **🆕 Smart PDF Analysis:** 
    * PyPDF2, PyMuPDF (automatycznie instalowane)
    * Google Generative AI SDK (dla Direct PDF upload)
    * Automatyczne wykrywanie możliwości modelu
  * Java (dla lokalnego renderowania PlantUML)
  * `plantuml.jar` (w katalogu `config/plantuml.jar`)
  * PyQt5 (tylko dla wersji desktopowej)
  * Plik `.env` z konfiguracją (kopia w głównym katalogu + `config/.env`)

---

## FAQ / Najczęstsze problemy

- **Brak Javy lub plantuml.jar:**  
  Upewnij się, że Java jest zainstalowana (`java -version`) i plik `plantuml.jar` znajduje się w katalogu projektu.
- **Brak połączenia z serwerem AI:**  
  Sprawdź, czy LM Studio lub inny serwer jest uruchomiony i dostępny pod wskazanym adresem.
- **Brak API_KEY:**  
  W przypadku Gemini/OpenAI musisz podać własny klucz API w pliku `.env`.
- **Problemy z bazą danych:**  
  Jeśli chcesz zapisywać historię do bazy, skonfiguruj odpowiednie parametry w `.env` i upewnij się, że baza jest dostępna. Szczegóły jakie sa potrzeben tabeme dla danej bazy w dedykowanym konektorze mysql_connector.py i PostgreSQL_connector.py.

---

## Użytkowanie

1.  **Wybierz model AI**: Z listy dostępnych modeli na serwerze.
2.  **🆕 Dodaj kontekst PDF**: (Opcjonalnie) Prześlij plik PDF aby wzbogacić kontekst.
3.  **Skonfiguruj szablon**: Wybierz typ szablonu (PlantUML/XML) i konkretny szablon.
4.  **Wybierz typ diagramu**: Sekwencja, aktywność, klasa itp.
5.  **Wprowadź opis procesu**: W polu tekstowym wpisz szczegółowy opis procesu, który chcesz zwizualizować.
6.  **Generowanie/Walidacja**: Kliknij przycisk „Wyślij zapytanie" lub „Waliduj opis".
7.  **Wyświetlanie Diagramu**: Wygenerowany diagram PlantUML (SVG) lub kod XML BPMN pojawi się w odpowiednich zakładkach.
8.  **🆕 Edytuj kod**: Kliknij "Kod PlantUML" aby edytować wygenerowany kod bezpośrednio w aplikacji.

---

## 📁 Nowa struktura projektu

```
GD_python/
├── 📁 src/                     # Główny kod aplikacji
│   ├── main.py                 # Aplikacja PyQt5
│   ├── streamlit_app.py        # Aplikacja Streamlit
│   ├── api_thread.py           # Komunikacja API
│   └── input_validator.py      # Walidacja danych
├── 📁 tests/                   # Wszystkie testy
│   ├── unit/                   # Testy jednostkowe
│   ├── integration/            # Testy integracyjne
│   ├── system/                 # Testy systemowe
│   └── fixtures/               # Dane testowe
├── 📁 tools/                   # Narzędzia developerskie
├── 📁 examples/                # Przykładowe diagramy
│   ├── activity/, class/, sequence/
│   └── generated/              # Wygenerowane pliki
├── 📁 config/                  # Konfiguracja
│   ├── .env, requirements.txt
│   └── plantuml.jar
├── 📁 scripts/                 # Skrypty uruchomieniowe
│   ├── run_streamlit.bat
│   └── run_tests.py
├── 📁 utils/                   # Moduły pomocnicze
│   └── pdf/                    # **🆕 Smart PDF Analysis**
│       ├── ai_pdf_analyzer.py  # AI analysis engine
│       ├── pdf_processor.py    # Enhanced PDF processor
│       └── streamlit_pdf_integration.py
├── 📁 language/                # Tłumaczenia
├── 📁 prompts/                 # Szablony promptów
├── 📁 docs/                    # Dokumentacja
├── main.py                     # Entry point PyQt5
└── streamlit_app.py            # Entry point Streamlit
```

---

## 📈 Historia Wersji

### v3.0.0 - Reorganizacja Projektu (2025-11-20)
- ✅ **Kompletna reorganizacja struktury** - profesjonalna organizacja w src/, tests/, tools/, config/
- ✅ **Smart PDF Analysis System** - inteligentne wykrywanie możliwości modeli i automatyczny wybór metody
- ✅ **Real-time progress tracking** - informowanie użytkownika o postępie operacji
- ✅ **Hierarchical fallback** - graceful degradation przy błędach
- ✅ **Enhanced testing** - pełna struktura testów (unit/integration/system)
- ✅ **Performance optimization** - analiza 75% vs 0% accuracy (Direct PDF vs Text Extraction)

### v2.x - Funkcje Legacy
- PDF Integration
- PlantUML Code Editing  
- GUI Language Selection
- Enhanced Error Verification

### Następne planowane funkcje (v3.1+):
- Cache system dla wyników analizy PDF
- Batch processing wielu plików
- User interface progress bars w GUI
- Model auto-selection

---

## 🔗 Przydatne Linki

- **📚 Dokumentacja Smart PDF System**: [`docs/SMART_PDF_SYSTEM_README.md`](docs/SMART_PDF_SYSTEM_README.md)
- **📁 Dokumentacja reorganizacji**: [`REORGANIZATION_README.md`](REORGANIZATION_README.md)
- **🧪 Test runner**: `python scripts/run_tests.py`
- **🛠️ Development tools**: `tools/` directory

---

## 🤝 Współpraca

Projekt jest otwarty na współpracę! Jeśli masz pomysły na ulepszenia lub znalazłeś błędy:

1. **Fork repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Run tests** (`python scripts/run_tests.py`)
4. **Commit changes** (`git commit -m 'Add amazing feature'`)
5. **Push to branch** (`git push origin feature/amazing-feature`)
6. **Open Pull Request**

---

## 📄 Licencja

Ten projekt jest licencjonowany na mocy **Creative Commons Uznanie autorstwa-Użycie niekomercyjne-Na tych samych warunkach 4.0 Międzynarodowa (CC BY-NC-SA 4.0)**.

Możesz zobaczyć skrót licencji (w języku polskim) tutaj:
[https://creativecommons.org/licenses/by-nc-sa/4.0/deed.pl](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.pl)

---

### Co to oznacza:

Licencja ta zezwala na używanie, udostępnianie i tworzenie utworów zależnych (bazujących na tym kodzie), ale z następującymi kluczowymi ograniczeniami:

* **Uznanie autorstwa (BY)**: Musisz odpowiednio oznaczyć autora oryginału (mnie) oraz podać link do tej licencji.
* **Użycie niekomercyjne (NC)**: **Nie możesz używać tego materiału do celów komercyjnych.** Jest to kluczowy warunek tej licencji.
* **Na tych samych warunkach (SA)**: Jeśli remiksujesz, przekształcasz lub tworzysz na podstawie tego materiału, musisz rozpowszechniać swoje dzieło na **tej samej licencji** (CC BY-NC-SA 4.0), co oryginał.

---

## 🧪 Testowanie

### Uruchamianie wszystkich testów:
```bash
python scripts/run_tests.py
```

### Testy według kategorii:
```bash
# Testy jednostkowe
python scripts/run_tests.py unit

# Testy integracyjne  
python scripts/run_tests.py integration

# Testy systemowe
python scripts/run_tests.py system
```

### Konkretny test:
```bash
# Test Smart PDF System
python tests/system/test_smart_pdf_system.py

# Test inteligentnej selekcji
python tests/system/test_smart_selection.py

# Analiza jakości PDF
python tools/analyze_pdf_quality.py
```

### 📊 Status testów:
- ✅ **Smart PDF Analysis** - Comprehensive system tests
- ✅ **Model Capability Detection** - Auto PDF support detection
- ✅ **Progress Tracking** - Real-time user feedback
- ✅ **Fallback Mechanisms** - Graceful error handling
- ✅ **Performance Analysis** - Direct PDF vs Text Extraction

---

## TODO (rozwojowe)

  * Praca nad szablonami promptów, szczególnie w zakresie sprawdzania poprawności procesu (rozważyć krokowość).
  * Eksport XMI dla innych typów diagramów będzie dostępny w przyszłych wersjach.
  * Opracowanie agenta wspierającego użytkownika przy tworzeniu kompleksowej dokumentacji.

---

## Przykładowe prompty

Zobacz plik `prompts/Prompty_bankowe.txt` – znajdziesz tam przykłady opisów procesów dla różnych typów diagramów UML/BPMN.
Zapoznaj się z plikiem `prompts/Szablony_promptow.txt` - zawiera opis działania poszczególnych szablonów promptów dedykowanych dla typów diagramów.

Plik testowy: `tests/fixtures/test_documents/Prompty.txt` - przykład procesu biznesowego gotowy do testowania.

---

## Zrzuty ekranu

  * [GD 2025-11-15 Sprawdzanie poprawności opisu procesu](https://github.com/user-attachments/assets/5016fd0b-d3fd-48e9-ae34-6285e4ab57bd)
  * [GD 2025-11-15 Diagram Klas](https://github.com/user-attachments/assets/87dd2e69-c36e-4e53-8a3f-a5ed2c14e398)
  * [GD 2025-06-14 Diagram komponentów](https://github.com/user-attachments/assets/eb99c9a0-834b-4a84-9037-c2a32af755da)
  * [GD 2025-11-15 Diagram komponentów C4](https://github.com/user-attachments/assets/c7ff4a33-aede-45cd-b168-3012db42cf89)

---

**Status**: ✅ **PRODUCTION READY v3.0.0** - Reorganizacja zakończona + Smart PDF Analysis System  
**Ostatnia aktualizacja**: 2025-11-20  
**Następne kroki**: GUI progress bars, cache system, batch processing

## Zrzuty ekranu

  * [GD 2025-11-15 Sprawdzanie poprawności opisu procesu](https://github.com/user-attachments/assets/5016fd0b-d3fd-48e9-ae34-6285e4ab57bd)
  * [GD 2025-11-15 Diagram Klas](https://github.com/user-attachments/assets/87dd2e69-c36e-4e53-8a3f-a5ed2c14e398)
  * [GD 2025-06-14 Diagram komponentów](https://github.com/user-attachments/assets/eb99c9a0-834b-4a84-9037-c2a32af755da)
  * [GD 2025-11-15 Diagram komponentów C4](https://github.com/user-attachments/assets/c7ff4a33-aede-45cd-b168-3012db42cf89)

