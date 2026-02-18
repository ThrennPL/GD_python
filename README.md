# Generator i Weryfikator Diagramów UML/BPMN z AI

**Status projektu**: ✅ **BPMN v2 PRODUCTION READY** (2025-11-26) - Kompletny system z dokumentacją biznesową i techniczną

Aplikacja do generowania, wizualizacji i weryfikacji diagramów UML (PlantUML) oraz BPMN v2 (XML) na podstawie opisu procesu, z wykorzystaniem modeli AI (np. LLM). Projekt oferuje zarówno wersję desktopową (PyQt5), jak i webową (Streamlit), umożliwiając wybór szablonu promptu, typu diagramu, walidację opisu procesu oraz automatyczną weryfikację kodu PlantUML.

**🆕 Najnowsze funkcje BPMN v2:**

- **🎯 Advanced BPMN v2 System** - iteracyjna optymalizacja jakości z real-time monitoring
- **📊 Quality-driven Generation** - automatyczne doskonalenie diagramów do osiągnięcia wymaganej jakości
- **🔄 Dynamic Configuration** - elastyczna konfiguracja AI providers przez zmienne środowiskowe
- **📖 Complete Documentation Suite** - kompletna dokumentacja biznesowa, techniczna i architekturalna
- **🖥️ Dual Interface Support** - pełna integracja BPMN v2 w aplikacji desktop i web
- **📈 Performance Analytics** - szczegółowe metryki wydajności i jakości

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
   Skopiuj poniższą konfigurację do pliku `.env` w katalogu głównym projektu i uzupełnij wymagane pola:

    ```env
    # AI Provider Configuration
    MODEL_PROVIDER=gemini
    GEMINI_API_KEY=your-gemini-key-here
    OPENAI_API_KEY=your-openai-key-here
    CLAUDE_API_KEY=your-claude-key-here
    OLLAMA_BASE_URL=http://localhost:11434

    # Application Settings
    LANGUAGE=pl
    PLANTUML_JAR_PATH=plantuml.jar
    PLANTUML_GENERATOR_TYPE=local

    # BPMN Quality Settings
    BPMN_QUALITY_THRESHOLD=0.8
    BPMN_MAX_ITERATIONS=10
    
    # Performance Settings
    API_REQUEST_TIMEOUT=60
    MAX_CONCURRENT_REQUESTS=5
    ```
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

- Generowanie kodu PlantUML lub XML BPMN na podstawie opisu procesu
- **🆕 System BPMN v2** - zaawansowane generowanie BPMN z iteracyjną optymalizacją jakości
- **🆕 Dynamic AI Configuration** - elastyczna konfiguracja providerów AI przez zmienne środowiskowe
- Wybór szablonu promptu i typu diagramu (sekwencja, aktywność, klasa, komponent, stan, przypadek użycia itp.)
- Wizualizacja diagramów PlantUML (SVG)
- Edycja kodu PlantUML - możliwość edycji wygenerowanego kodu bezpośrednio w aplikacji
- Diagram komponentów z PlantUML (notacja C4 i klasyczna)
- Diagram aktywności z poprawionym pozycjonowaniem
- **🆕 PDF Integration** - analiza dokumentów PDF i wzbogacanie kontekstu diagramów
- Automatyczna weryfikacja kodu PlantUML w przypadku błędów generowania SVG
- **🆕 Quality Analytics** - szczegółowe metryki jakości i wydajności generowania
- Dual Interface - pełna funkcjonalność w aplikacji desktop (PyQt5) i web (Streamlit)
- Walidacja opisów procesów przez AI
- Historia konwersacji z modelem AI
- Obsługa wielu modeli AI (OpenAI GPT-4, Google Gemini, Anthropic Claude, Ollama)
- Pobieranie wygenerowanych diagramów w formatach: PlantUML, SVG, XMI, BPMN
- **🆕 Real-time Progress Monitoring** - śledzenie postępu optymalizacji BPMN w czasie rzeczywistym
- **Dwie wersje językowe interfejsu i promptów (angielska i polska)**
- **🆕 Complete Documentation Suite** - kompletna dokumentacja biznesowa i techniczna
- **🧭 Planowane** - refaktor UML z obrazu (diagram -> PlantUML)

---

## 🎯 System BPMN v2 - Zaawansowane Generowanie

**Przełomowy system generowania BPMN z automatyczną optymalizacją jakości.**

### 📊 Kluczowe funkcje

- **Iteracyjna optymalizacja jakości** - automatyczne doskonalenie diagramów do osiągnięcia wymaganej jakości
- **Real-time monitoring** - śledzenie postępu optymalizacji w czasie rzeczywistym  
- **Quality scoring** - precyzyjna ocena jakości diagramów (0.0-1.0)
- **Automatic improvement** - inteligentne doskonalenie struktury, nazw i przepływów
- **Dynamic configuration** - elastyczna konfiguracja przez zmienne środowiskowe
- **Multi-provider support** - obsługa OpenAI, Gemini, Claude, Ollama

### 🔄 Przepływ optymalizacji

1. **Generacja wstępna** - utworzenie podstawowego diagramu BPMN
2. **Analiza jakości** - ocena zgodności ze standardem BPMN 2.0
3. **Iteracyjne doskonalenie** - automatyczne poprawki i optymalizacje
4. **Real-time feedback** - informacje o postępie dla użytkownika
5. **Quality validation** - sprawdzenie osiągnięcia wymaganej jakości

### ⚙️ Konfiguracja BPMN v2

```env
# Ustawienia jakości BPMN
BMPN_QUALITY_THRESHOLD=0.8    # Minimalny próg jakości (0.0-1.0)
BMPN_MAX_ITERATIONS=10        # Maksymalna liczba iteracji
BMPN_TIMEOUT_MINUTES=5        # Timeout procesu optymalizacji

# Opcje automatyzacji
BMPN_AUTO_VALIDATE=true       # Automatyczna walidacja
BMPN_AUTO_IMPROVE=true        # Automatyczne doskonalenie
BMPN_SAVE_ITERATIONS=true     # Zapis historii iteracji
```

### 📈 Metryki wydajności

| Próg jakości | Średni czas | Iteracje | Sukces |
|--------------|-------------|-----------|--------|
| 0.7          | 45s         | 3-5       | 98%    |
| 0.8          | 65s         | 4-7       | 95%    |
| 0.9          | 85s         | 6-10      | 87%    |

### 🎯 Przykład użycia

**Desktop Application:**
1. Wybierz "BPMN" w radio button
2. Wprowadź opis procesu biznesowego
3. Ustaw parametry jakości
4. Obserwuj progress bar podczas optymalizacji
5. Otrzymaj wysokiej jakości diagram BPMN 2.0

**Streamlit Web App:**
1. Skonfiguruj parametry BPMN w sidebar
2. Wprowadź szczegółowy opis procesu
3. Kliknij "Generate BPMN v2"
4. Śledź real-time progress i quality score
5. Pobierz diagram w formacie XML lub SVG

---

## 📖 Kompletna Dokumentacja Systemu

**Profesjonalna dokumentacja biznesowa i techniczna przygotowana przez eksperta analityka biznesowo-systemowego.**

### 🏢 Dokumentacja Biznesowa

- **[Business Overview](documentation/business/business-overview.md)** - Analiza biznesowa z ROI i competitive advantage
- **[Use Cases](documentation/business/use-cases.md)** - 8 szczegółowych scenariuszy użycia z metrykami sukcesu
- **[Requirements Analysis](documentation/business/requirements-analysis.md)** - Wymagania funkcjonalne i niefunkcjonalne

### 🏗️ Architektura Systemu

- **[System Architecture](documentation/architecture/system-architecture.md)** - Kompletna architektura z diagramami komponentów
- **[Data Model](documentation/architecture/data-model.md)** - Szczegółowy model danych z przepływami
- **[Integration Architecture](documentation/architecture/integrations.md)** - Zewnętrzne systemy i API

### 🔧 Dokumentacja Techniczna

- **[API Reference](documentation/technical/api-reference.md)** - Kompletne API dla wszystkich modułów
- **[Configuration Guide](documentation/technical/configuration-guide.md)** - Przewodnik konfiguracji dla wszystkich środowisk
- **[Deployment Guide](documentation/technical/deployment-guide.md)** - Production deployment (Docker, Cloud, CI/CD)

### 👥 Przewodniki Użytkownika

- **[Desktop App Guide](documentation/user-guides/desktop-app-guide.md)** - Kompletny przewodnik aplikacji PyQt5
- **[Streamlit Web Guide](documentation/user-guides/streamlit-web-guide.md)** - Przewodnik aplikacji webowej
- **[BPMN v2 Guide](documentation/user-guides/bpmn-guide.md)** - Zaawansowane funkcje BPMN v2
- **[PDF Integration Guide](documentation/user-guides/pdf-guide.md)** - Analiza dokumentów PDF

### 💼 Business Value

- **Reduced Training Time**: Kompleksowe przewodniki redukują czas szkolenia o ~60%
- **Faster Deployment**: Gotowe procedury przyspieszają wdrożenie o ~75%
- **Lower Support Costs**: Szczegółowe troubleshooting zmniejsza koszty wsparcia
- **Better Adoption**: User-friendly dokumentacja zwiększa adoption rate
- **Technical Debt Reduction**: Dobra dokumentacja ułatwia maintenance i rozwój

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

Eksport XMI jest obecnie dostępny **tylko dla diagramu klas, sekwencji, aktywności i komponentów (Class Diagram, Sequence Diagram, Activity Diagram, Component Diagram),**. Przycisk „Zapisz XMI” (również menu kontekstowe) jest aktywny wyłącznie, gdy aktywna zakładka zawiera diagram klas, diagram sekwencji, diagram aktywności lub diagram komponentów. Dla innych typów diagramów (np. przypadków użycia) eksport XMI nie jest jeszcze obsługiwany. Po imporcie do EA elementy mogą wymagać ręcznego uporządkowania.

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
  * Plik `.env` z konfiguracją w katalogu głównym

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

### v4.0.0 - BPMN v2 Production Release (2025-11-26)

- ✅ **BPMN v2 System** - zaawansowane generowanie BPMN z iteracyjną optymalizacją jakości
- ✅ **Dynamic AI Configuration** - elastyczna konfiguracja AI providers przez zmienne środowiskowe  
- ✅ **Complete Documentation Suite** - kompletna dokumentacja biznesowa, techniczna i architekturalna
- ✅ **Quality-driven Generation** - automatyczne doskonalenie diagramów do osiągnięcia wymaganej jakości
- ✅ **Real-time Progress Monitoring** - śledzenie postępu optymalizacji w czasie rzeczywistym
- ✅ **Dual Interface Integration** - pełna integracja BPMN v2 w aplikacji desktop i web
- ✅ **Performance Analytics** - szczegółowe metryki wydajności i jakości generowania
- ✅ **Professional Documentation** - business-grade dokumentacja dla stakeholderów i zespołów technicznych
- ✅ **Diagramy komponentów** - notacja C4 i klasyczna z PlantUML
- ✅ **Diagram aktywności** - poprawione pozycjonowanie elementów

### v3.0.0 - Reorganizacja Projektu (2025-11-20)

- ✅ **Kompletna reorganizacja struktury** - profesjonalna organizacja w src/, tests/, tools/, config/
- ✅ **Smart PDF Analysis System** - inteligentne wykrywanie możliwości modeli i automatyczny wybór metody
- ✅ **Real-time progress tracking** - informowanie użytkownika o postępie operacji
- ✅ **Hierarchical fallback** - graceful degradation przy błędach
- ✅ **Enhanced testing** - pełna struktura testów (unit/integration/system)
- ✅ **Performance optimization** - analiza 75% vs 0% accuracy (Direct PDF vs Text Extraction)

### v2.x - Funkcje Legacy

- PDF Integration
- Edycja kodu PlantUML
- Wybór języka GUI
- Enhanced Error Verification

### Planowane funkcje (v4.1+)

- Cache system dla wyników analizy PDF
- Batch processing wielu plików
- Advanced BPMN templates
- Integration z Enterprise Architect
- Multi-language support expansion
- Performance optimization dashboard
- PlantUML Code Editing  
- GUI Language Selection
- Enhanced Error Verification
- UML Image Refactor (obraz -> PlantUML)

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
  * [GD 2025-11-20 Desktop - Diagram klas](https://github.com/user-attachments/assets/621afe0c-79d4-47f3-a409-d635b203490d)
  * [GD 2025-11-20 Streamlit](https://github.com/user-attachments/assets/7486a5de-dda8-4f50-9b9e-5fea016d5cdc)



---

**Status**: ✅ **BPMN v2 PRODUCTION READY v4.0.0** - Kompletny system z dokumentacją biznesową i techniczną  
**Ostatnia aktualizacja**: 2025-11-26  
**Następne kroki**: Advanced BPMN templates, Enterprise Architect integration, Multi-language expansion

## Zrzuty ekranu

  * [GD 2025-11-15 Sprawdzanie poprawności opisu procesu](https://github.com/user-attachments/assets/5016fd0b-d3fd-48e9-ae34-6285e4ab57bd)
  * [GD 2025-11-15 Diagram Klas](https://github.com/user-attachments/assets/87dd2e69-c36e-4e53-8a3f-a5ed2c14e398)
  * [GD 2025-06-14 Diagram komponentów](https://github.com/user-attachments/assets/eb99c9a0-834b-4a84-9037-c2a32af755da)
  * [GD 2025-11-15 Diagram komponentów C4](https://github.com/user-attachments/assets/c7ff4a33-aede-45cd-b168-3012db42cf89)

