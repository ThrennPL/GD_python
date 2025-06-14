# Generator i Weryfikator Diagramów UML/BPMN z AI

Aplikacja desktopowa (PyQt5) do generowania, wizualizacji i weryfikacji diagramów UML (PlantUML) oraz BPMN (XML) na podstawie opisu procesu, z wykorzystaniem modeli AI (np. LLM). Pozwala na wybór szablonu promptu, typu diagramu, walidację opisu procesu oraz automatyczną weryfikację kodu PlantUML.

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

## Uruchomienie

```bash
python main.py
```

## Struktura projektu

- `main.py` – główny plik aplikacji (GUI, logika)
- `prompt_templates.py` – szablony promptów do AI
- `plantuml_utils.py` – funkcje pomocnicze do PlantUML (kodowanie, pobieranie SVG, rozpoznawanie typu diagramu)
- `input_validator.py` – funkcja do walidacji opisu procesu przez AI
- `plantuml_convert_to_xmi.py` – funkcje konwersji formatu PlantUML na XMI do EA
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

Diagram przypadków użycia:
![Diagram przypadków użycia](https://github.com/user-attachments/assets/bcac902f-0fe5-48b9-8088-968c597ffb62)


## Przykładowe prompty

Zobacz plik [`Prompty_bankowe.txt`](Prompty_bankowe.txt) – znajdziesz tam przykłady opisów procesów dla różnych typów diagramów UML/BPMN.
Zpbacz plik [`Szablony_promptow.txt`] (Szablony_promptów.txt) - zapoznaj się z opisem działania poszczególnych szablonów promptów dedykowanych dla typów diagramów

## Zrzuty ekranu

![GD 2025-06-11 Sprawdzanie poprownosci opisu procesu](https://github.com/user-attachments/assets/f2ea75e1-32a6-44b6-936e-8d4298231215)
![GD 2025-06-13 Diagram Klas](https://github.com/user-attachments/assets/621eaac8-10d0-47c1-a4e3-628eeccb80a9)
![GD 2025-06-13 Diagram komponentów](https://github.com/user-attachments/assets/30794976-68b5-49bd-9e8c-413e41fa5d14)
![GD 2025-06-13 Diagram komponentów C4](https://github.com/user-attachments/assets/5c65f1a2-a8b8-44ab-8ced-4a9a917b82f4)



## Autor

Grzegorz Majewski / ThrennPL
[https://www.linkedin.com/in/grzegorz-majewski-421306151/]

## Licencja

MIT
