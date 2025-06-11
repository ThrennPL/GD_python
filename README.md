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

## Wymagania

- Python 3.8+
- PyQt5
- requests

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
- `Prompty_bankowe.txt` – przykładowe opisy procesów do testów

## Przykładowe użycie

1. Wprowadź opis procesu w polu tekstowym.
2. Wybierz typ szablonu (PlantUML/XML) i szablon promptu.
3. Wybierz typ diagramu.
4. Kliknij "Wyślij" – model AI wygeneruje kod diagramu.
5. Diagram zostanie wyświetlony jako SVG (lub XML).
6. W przypadku błędów kod PlantUML zostanie automatycznie zweryfikowany przez AI.
7. Możesz także sprawdzić poprawność opisu procesu przez AI.

## Przykładowe prompty

Zobacz plik [`Prompty_bankowe.txt`](Prompty_bankowe.txt) – znajdziesz tam przykłady opisów procesów dla różnych typów diagramów UML/BPMN.

## Zrzuty ekranu

![GD 2025-06-11 Sprawdzanie poprownosci opisu procesu](https://github.com/user-attachments/assets/f2ea75e1-32a6-44b6-936e-8d4298231215)
![GD 2025-06-11 Diagram komponentów](https://github.com/user-attachments/assets/4f11ba4c-cf2e-42fc-9f5e-2af3ef2b0d99)

## Autor

Grzegorz Majewski / ThrennPL
[https://www.linkedin.com/in/grzegorz-majewski-421306151/]

## Licencja

MIT
