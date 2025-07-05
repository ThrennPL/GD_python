# Generator i Weryfikator Diagramów UML/BPMN z AI

Aplikacja do generowania, wizualizacji i weryfikacji diagramów UML (PlantUML) oraz BPMN (XML) na podstawie opisu procesu, z wykorzystaniem modeli AI (np. LLM). Projekt oferuje zarówno wersję desktopową (PyQt5) , jak i webową (Streamlit) , umożliwiając wybór szablonu promptu, typu diagramu, walidację opisu procesu oraz automatyczną weryfikację kodu PlantUML . Aplikacja obsługuje **dwie wersje językowe (angielską i polską)**, z dedykowanymi szablonami promptów dla każdej z nich, co zapewnia lepsze rezultaty generowania w wybranym języku.

## Funkcje

  * Generowanie kodu PlantUML lub XML BPMN na podstawie opisu procesu
  * Wybór szablonu promptu i typu diagramu (sekwencja, aktywność, klasa, komponent, stan, przypadek użycia itp.)
  * Wizualizacja diagramów PlantUML (SVG)
  * Automatyczna weryfikacja kodu PlantUML w przypadku błędów generowania SVG
  * Walidacja opisów procesów przez AI
  * Historia konwersacji z modelem AI
  * Obsługa wielu modeli AI (lokalnych lub poprzez API, np. OpenAI, Gemini)
  * Pobieranie wygenerowanych diagramów w formatach: PlantUML, SVG, XMI
  * Specjalne opcje dla diagramów BPMN (poziom złożoności, reguła walidacji, format wyjściowy, domena)
  * **Dwie wersje językowe interfejsu i promptów (angielska i polska)**
  * Przykładowe prompty testowe dla branży bankowej

## Eksport XMI

Eksport XMI jest obecnie dostępny **tylko dla diagramu klas (Class Diagram)**. Przycisk „Zapisz XMI” jest aktywny wyłącznie, gdy aktywna zakładka zawiera diagram klas. Dla innych typów diagramów (np. sekwencji, aktywności) eksport XMI nie jest jeszcze obsługiwany . Należy pamiętać, że po wczytaniu do Enterprise Architect mogą pojawić się tylko elementy, ale nie sam diagram .

## Obsługa Zakładek (dla wersji desktopowej)

Aplikacja desktopowa umożliwia pracę z wieloma diagramami w zakładkach. Po przełączeniu zakładki aplikacja automatycznie sprawdza typ diagramu i aktywuje/dezaktywuje przycisk eksportu XMI .

## Generowanie Diagramów SVG

Diagramy SVG mogą być generowane na dwa sposoby, zależnie od ustawienia parametru `plantuml_generator_type`:

  * **`plantuml_generator_type = local`**: Diagramy SVG są generowane lokalnie przy użyciu `plantuml.jar` i Javy. Upewnij się, że oba są dostępne w Twoim systemie .
  * **`plantuml_generator_type = www`**: Diagramy SVG są generowane z wykorzystaniem strony [www.plantuml.com](https://plantuml.com/) .

## Wymagania

  * Python 3.7+ (dla Streamlit) lub Python 3.8+ (dla PyQt5)
  * Lokalny serwer AI (np. LM Studio) uruchomiony na porcie `http://localhost:1234`
  * Zależności z pliku `requirements.txt`
  * Java (dla lokalnego renderowania PlantUML)
  * `plantuml.jar` (do pobrania ze strony PlantUML)
  * PyQt5 (tylko dla wersji desktopowej)
  * `requests`

## Instalacja

1.  Sklonuj repozytorium:
    ```bash
    git clone https://github.com/ThrennPL/GD_python
    cd twoj-projekt
    ```
2.  Zainstaluj zależności:
    ```bash
    pip install -r requirements.txt
    ```
3.  Upewnij się, że lokalny serwer AI jest uruchomiony na `http://localhost:1234` .

## Konfiguracja (`.env`)

Przykładowa konfiguracja w pliku `.env`:

```
PLANTUML_JAR_PATH=plantuml.jar
PLANTUML_GENERATOR_TYPE=local
#API_URL=https://api.openai.com/v1/models
#API_URL=http://localhost:1234/v1/models
API_URL=https://generativelanguage.googleapis.com/v1beta/models
API_DEFAULT_MODEL=models/gemini-2.0-flash
#API_DEFAULT_MODEL=google/gemma-3-4b
#CHAT_URL=https://api.openai.com/v1/chat/completions
#CHAT_URL=http://localhost:1234/v1/chat/completions
CHAT_URL=https://generativelanguage.googleapis.com/v1v1beta/chat/completions
API_KEY=
MODEL_PROVIDER =gemini
#MODEL_PROVIDER =local
#MODEL_PROVIDER =openai
```

Dla Gemini i OpenAI trzeba użyć własnych API_KEY

## Uruchomienie

### Wersja Streamlit

  * **Metoda 1: Bezpośrednio**
    ```bash
    streamlit run streamlit_app.py
    ```
  * **Metoda 2: Skrypt batch (Windows)**
    ```bash
    run_streamlit.bat
    ```

### Wersja PyQt5

```bash
python main.py
```

## Użytkowanie

1.  **Wybierz model AI**: Z listy dostępnych modeli na serwerze .
2.  **Skonfiguruj szablon**: Wybierz typ szablonu (PlantUML/XML) i konkretny szablon .
3.  **Wybierz typ diagramu**: Sekwencja, aktywność, klasa itp.
4.  **Wprowadź opis procesu**: W polu tekstowym wpisz szczegółowy opis procesu, który chcesz zwizualizować .
5.  **Generowanie/Walidacja**: Kliknij przycisk „Wyślij zapytanie” lub „Waliduj opis” .
6.  **Wyświetlanie Diagramu**: Wygenerowany diagram PlantUML (SVG) lub kod XML BPMN pojawi się w odpowiednich zakładkach .

## Struktura plików

  * `streamlit_app.py` - główna aplikacja Streamlit
  * `main.py` - oryginalna aplikacja PyQt5
  * `run_streamlit.bat` - skrypt uruchamiający (Windows) dla wersji Streamlit
  * Pozostałe pliki Python - moduły pomocnicze (bez zmian)
      * `translations_pl.py`, `translations_en.py` - pliki z tłumaczeniami interfejsu
      * `prompt_templates_pl.py`, `prompt_templates_en.py` - pliki z szablonami promptów dla języka polskiego i angielskiego

## TODO (rozwojowe)

  * Praca nad szablonami promptów, szczególnie w zakresie sprawdzania poprawności procesu (rozważyć krokowość) .
  * Eksport XMI dla innych typów diagramów będzie dostępny w przyszłych wersjach .

## Przykładowe prompty

Zobacz plik `Prompty_bankowe.txt` – znajdziesz tam przykłady opisów procesów dla różnych typów diagramów UML/BPMN .
Zapoznaj się z plikiem `Szablony_promptow.txt` - zawiera opis działania poszczególnych szablonów promptów dedykowanych dla typów diagramów .

## Zrzuty ekranu

  * [GD 2025-06-14 Sprawdzanie poprawności opisu procesu](https://github.com/user-attachments/assets/6bafbbb4-c6e7-4f62-b145-51623c20026e)
  * [GD 2025-06-14 Diagram Klas](https://github.com/user-attachments/assets/a3082146-64d2-466b-b1d7-de33567c51eb)
  * [GD 2025-06-14 Diagram komponentów](https://github.com/user-attachments/assets/eb99c9a0-834b-4a84-9037-c2a32af755da)
  * [GD 2025-06-14 Diagram komponentów C4](https://github.com/user-attachments/assets/168735ab-e2d8-4fcb-97d83f2a5b6c)
