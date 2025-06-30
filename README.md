# Generator i Weryfikator Diagramów UML/BPMN z AI

Aplikacja desktopowa (PyQt5) oraz online (Streamlit) do generowania, wizualizacji i weryfikacji diagramów UML (PlantUML) oraz BPMN (XML) na podstawie opisu procesu, z wykorzystaniem modeli AI (np. LLM). Pozwala na wybór szablonu promptu, typu diagramu, walidację opisu procesu oraz automatyczną weryfikację kodu PlantUML.

## Funkcje

- Generowanie kodu PlantUML lub XML BPMN na podstawie opisu procesu
- Wybór szablonu promptu i typu diagramu (sequence, activity, class, component, state, use case, itd.)
- Wizualizacja diagramów PlantUML (SVG) w zakładkach
- Automatyczna weryfikacja kodu PlantUML w przypadku błędów generowania SVG
- Walidacja opisu procesu przez AI
- Historia rozmowy z modelem
- Obsługa wielu modeli AI (np. lokalnych lub OpenAI API)
- Przykładowe prompty testowe dla branży bankowej
- Eksport XMI dla PlantUML

## Eksport XMI

- Eksport XMI jest obecnie dostępny **tylko dla diagramu klas (Class Diagram)**.
- Przycisk „Zapisz XMI” jest aktywny wyłącznie, gdy aktywna zakładka zawiera diagram klas.
- Dla innych typów diagramów (np. sekwencji, aktywności) eksport XMI nie jest jeszcze obsługiwany.

## Obsługa zakładek

- Aplikacja umożliwia pracę z wieloma diagramami w zakładkach.
- Po przełączeniu zakładki aplikacja automatycznie sprawdza typ diagramu i aktywuje/dezaktywuje przycisk eksportu XMI.

## Generowanie diagramów SVG
- Zależnie od ustawionej wartości parametru:
- **plantuml_generator_type = local** - Diagramy SVG są generowane lokalnie przy użyciu plantuml.jar i Java. Upewnij się, że oba są dostępne w twoim systemie.
- **plantuml_generator_type = www** - Diagramy SVG są generowane z wykorzystaniem strony [www.plantuml.com](https://plantuml.com/).

## TODO

- Praca nad szablonami promptów w szczególności przy sprawdzaniu poprawności proceu - do rozważenia krokowość w tym zakresie.
- Eksport XMI działa tylkopołownicznie - po wczytaniu do Enterprice Architect nie ma diagramu ale są pozostałe elementy.
- Eksport XMI dla innych typów diagramów będzie dostępny w przyszłych wersjach.

## Wymagania

- Python 3.8+
- PyQt5
- requests- Java (for local PlantUML rendering)
- plantuml.jar (download from https://plantuml.com/download)

## Instalacja

```bash
git clone https://github.com/ThrennPL/GD_python
cd twoj-projekt
pip install -r requirements.txt
```

## Konfiguracja .env
PLANTUML_JAR_PATH=plantuml.jar
PLANTUML_GENERATOR_TYPE=local
API_URL=https://api.openai.com/v1/models
API_DEFAULT_MODEL=gpt-4o
CHAT_URL=https://api.openai.com/v1/chat/completions
API_KEY=<...>

## Uruchomienie

```bash
python main.py
lub
streamlit run streamlit_app.py
```

## Struktura projektu

- `main.py` – główny plik aplikacji (GUI, logika) - PyQt5
- `streamlit_app.py` – główny plik aplikacji (GUI, logika) - Streamlit
- `prompt_templates.py` – szablony promptów do AI
- `plantuml_utils.py` – funkcje pomocnicze do PlantUML (kodowanie, pobieranie SVG, rozpoznawanie typu diagramu)
- `input_validator.py` – funkcja do walidacji opisu procesu przez AI
- `plantuml_model.py`, `plantuml_parser.py`, `plantuml_to_ea.py`, `xmi_generator.py` – funkcje konwersji formatu PlantUML na XMI do EA
- `Prompty_bankowe.txt` – przykładowe opisy procesów do testów
- `Szablony_promptow.txt` - lista zdefiniowanych szablonów promptów oraz opis ich działania

## Przykładowe użycie

1. Wprowadź opis procesu w polu tekstowym.
2. Wybierz typ szablonu (PlantUML/XML) i szablon promptu.
3. Wybierz typ diagramu.
4. Kliknij "Wyślij" – model AI wygeneruje kod diagramu.
5. Diagram zostanie wyświetlony jako SVG (lub XML).
6. W przypadku błędów kod PlantUML zostanie automatycznie zweryfikowany przez AI.
7. Możesz także sprawdzić poprawność opisu procesu przez AI.

Diagram przypadków użycia (PyQt5):
![GD 2025-06-14 Przypadków użycia](https://github.com/user-attachments/assets/d8df84b4-f519-441e-856f-9ad1f7470d05)

## Przykładowe prompty

Zobacz plik [`Prompty_bankowe.txt`](Prompty_bankowe.txt) – znajdziesz tam przykłady opisów procesów dla różnych typów diagramów UML/BPMN.
Zpbacz plik [`Szablony_promptow.txt`](Szablony_promptów.txt) - zapoznaj się z opisem działania poszczególnych szablonów promptów dedykowanych dla typów diagramów

## Zrzuty ekranu
![GD 2025-06-14 Sprawdzanie poprownosci opisu procesu](https://github.com/user-attachments/assets/6bafbbb4-c6e7-4f62-b145-51623c20026e)
![GD 2025-06-14 Diagram Klas](https://github.com/user-attachments/assets/a3082146-64d2-466b-b1d7-de33567c51eb)
![GD 2025-06-14 Diagram komponentów](https://github.com/user-attachments/assets/eb99c9a0-834b-4a84-9037-c2a32af755da)
![GD 2025-06-14 Diagram komponentów C4](https://github.com/user-attachments/assets/168735ab-e2d8-4fcb-97d0-1cf7ec078327)
![Diagram komponentów C4 wersja Streamlit 2025-06-28 014118](https://github.com/user-attachments/assets/edede5c5-39a4-4e07-b9bd-b21639141dde)
![Diagram sekwencji wersja Streamlit 2025-06-28 014118](https://github.com/user-attachments/assets/d0a1d0af-3c92-4dbe-9807-16da583293c2)
![Weryfikacja opisu diagramu wersja Streamlit 2025-06-28 014118](https://github.com/user-attachments/assets/df116ea5-c29b-49b1-a2b9-7bb20f16c950)


## Autor

- Grzegorz Majewski / ThrennPL
[https://www.linkedin.com/in/grzegorz-majewski-421306151/]
gmajka1@wp.pl

- Jacek Dymek / jacdym
[https://www.linkedin.com/in/jacek-dymek-6b08ba5/]
jjdymek@interia.pl



