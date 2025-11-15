# Generator i Weryfikator Diagramów UML/BPMN z AI

Aplikacja do generowania, wizualizacji i weryfikacji diagramów UML (PlantUML) oraz BPMN (XML) na podstawie opisu procesu, z wykorzystaniem modeli AI (np. LLM). Projekt oferuje zarówno wersję desktopową (PyQt5), jak i webową (Streamlit), umożliwiając wybór szablonu promptu, typu diagramu, walidację opisu procesu oraz automatyczną weryfikację kodu PlantUML. Aplikacja obsługuje **dwie wersje językowe (angielską i polską)**, z dedykowanymi szablonami promptów dla każdej z nich, co zapewnia lepsze rezultaty generowania w wybranym języku.

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
     streamlit run streamlit_app.py
     ```
   - **PyQt5:**  
     ```bash
     python main.py
     ```

---

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
  * Zapis zapytań i odpowiedzi z modelu do bazy danych (mySQL, PostgreSQL)
  * **Dwie wersje językowe interfejsu i promptów (angielska i polska)**
  * Przykładowe prompty testowe dla branży bankowej

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
  * Zależności z pliku `requirements.txt`
  * Java (dla lokalnego renderowania PlantUML)
  * `plantuml.jar` (do pobrania ze strony PlantUML)
  * PyQt5 (tylko dla wersji desktopowej)
  * Plik `.env` z konfiguracją (patrz wyżej)

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
2.  **Skonfiguruj szablon**: Wybierz typ szablonu (PlantUML/XML) i konkretny szablon.
3.  **Wybierz typ diagramu**: Sekwencja, aktywność, klasa itp.
4.  **Wprowadź opis procesu**: W polu tekstowym wpisz szczegółowy opis procesu, który chcesz zwizualizować.
5.  **Generowanie/Walidacja**: Kliknij przycisk „Wyślij zapytanie” lub „Waliduj opis”.
6.  **Wyświetlanie Diagramu**: Wygenerowany diagram PlantUML (SVG) lub kod XML BPMN pojawi się w odpowiednich zakładkach.

---

## Struktura plików

  * `streamlit_app.py` - główna aplikacja Streamlit
  * `main.py` - oryginalna aplikacja PyQt5
  * `run_streamlit.bat` - skrypt uruchamiający (Windows) dla wersji Streamlit
  * Pozostałe pliki Python - moduły pomocnicze
      * `translations_pl.py`, `translations_en.py` - pliki z tłumaczeniami interfejsu
      * `prompt_templates_pl.py`, `prompt_templates_en.py` - pliki z szablonami promptów dla języka polskiego i angielskiego

---
## Licencja

Ten projekt jest udostępniony na licencji Creative Commons BY-NC-SA 4.0. Oznacza to, że możesz go dowolnie używać i modyfikować w celach niekomercyjnych, pod warunkiem uznania autorstwa i udostępniania pochodnych na tej samej licencji. Użycie komercyjne jest zabronione.

---

## TODO (rozwojowe)

  * Praca nad szablonami promptów, szczególnie w zakresie sprawdzania poprawności procesu (rozważyć krokowość).
  * Eksport XMI dla innych typów diagramów będzie dostępny w przyszłych wersjach.
  * Opracowanie agenta wspierającego użytkownika przy tworzeniu kompleksowej dokumentacji.

---

## Przykładowe prompty

Zobacz plik `Prompty_bankowe.txt` – znajdziesz tam przykłady opisów procesów dla różnych typów diagramów UML/BPMN.
Zapoznaj się z plikiem `Szablony_promptow.txt` - zawiera opis działania poszczególnych szablonów promptów dedykowanych dla typów diagramów.

---

## Zrzuty ekranu

  * [GD 2025-06-14 Sprawdzanie poprawności opisu procesu](https://github.com/user-attachments/assets/6bafbbb4-c6e7-4f62-b145-51623c20026e)
  * [GD 2025-06-14 Diagram Klas](https://github.com/user-attachments/assets/a3082146-64d2-466b-b1d7-de33567c51eb)
  * [GD 2025-06-14 Diagram komponentów](https://github.com/user-attachments/assets/eb99c9a0-834b-4a84-9037-c2a32af755da)
  * [GD 2025-06-14 Diagram komponentów C4](https://github.com/user-attachments/assets/168735ab-e2d8-4fcb-97d83f2a5b6c)
