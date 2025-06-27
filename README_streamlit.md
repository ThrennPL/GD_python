# AI Diagram Generator - Streamlit Version

Aplikacja do generowania diagramów PlantUML i XML przy użyciu modeli AI, przekonwertowana z PyQt5 na Streamlit.

## Funkcje

- 🤖 Integracja z lokalnymi modelami AI (przez API)
- 📊 Generowanie diagramów PlantUML różnych typów
- 🎯 Szablony zapytań dla różnych rodzajów diagramów
- 💾 Pobieranie wygenerowanych diagramów w formatach: PlantUML, SVG, XMI
- 🔍 Walidacja opisów procesów
- 💬 Historia konwersacji z modelem AI
- 🏗️ Specjalne opcje dla diagramów BPMN

## Wymagania

- Python 3.7+
- Lokalny serwer AI (np. LM Studio) uruchomiony na porcie 1234
- Zależności z pliku `requirements.txt`

## Instalacja

1. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

2. Upewnij się, że lokalny serwer AI jest uruchomiony na `http://localhost:1234`

## Uruchomienie

### Metoda 1: Bezpośrednio
```bash
streamlit run streamlit_app.py
```

### Metoda 2: Skrypt batch (Windows)
```bash
run_streamlit.bat
```

## Użytkowanie

1. **Wybierz model AI** - z listy dostępnych modeli na serwerze
2. **Skonfiguruj szablon** - wybierz typ szablonu (PlantUML/XML) i konkretny szablon
3. **Wybierz typ diagramu** - sequence, activity, class, itp.
4. **Wprowadź opis procesu** - opisz proces, który chcesz przekształcić w diagram
5. **Wyślij zapytanie** - model AI wygeneruje odpowiedź
6. **Pobierz wyniki** - pobierz wygenerowane diagramy w różnych formatach

## Różnice względem wersji PyQt5

### Co zostało przeniesione:
- ✅ Wszystkie główne funkcje generowania diagramów
- ✅ Szablony zapytań i konfiguracja
- ✅ Integracja z API modelu AI
- ✅ Pobieranie różnych formatów plików
- ✅ Walidacja i obsługa błędów
- ✅ Historia konwersacji

### Co zostało zmienione:
- 🔄 Interfejs użytkownika na webowy (Streamlit)
- 🔄 Zarządzanie stanem przez `st.session_state`
- 🔄 Pobieranie plików przez `st.download_button`
- 🔄 Wyświetlanie diagramów SVG przez `st.components.v1.html`

### Co może wymagać dostosowania:
- ⚠️ Zakładki z diagramami - zastąpione przez `st.tabs`
- ⚠️ Async API calls - zastąpione przez synchroniczne wywołania
- ⚠️ Wielokrotna weryfikacja kodu - może wymagać dodatkowej implementacji

## Struktura plików

- `streamlit_app.py` - główna aplikacja Streamlit
- `main.py` - oryginalna aplikacja PyQt5
- `run_streamlit.bat` - skrypt uruchamiający (Windows)
- Pozostałe pliki Python - moduły pomocnicze (bez zmian)

## Konfiguracja

### Ustawienia API:
```python
API_URL = "http://localhost:1234/v1/models"
CHAT_URL = "http://localhost:1234/v1/chat/completions"
```

### Ustawienia PlantUML:
```python
plantuml_generator_type = "www"  # lub "local"
plantuml_jar_path = "plantuml.jar"
```

## Rozwiązywanie problemów

1. **Brak modeli AI**: Sprawdź czy serwer AI jest uruchomiony na porcie 1234
2. **Błędy PlantUML**: Sprawdź połączenie internetowe (dla trybu "www")
3. **Błędy importów**: Zainstaluj wszystkie zależności z `requirements.txt`

## Wsparcie

Jeśli napotkasz problemy, sprawdź logi w terminalu lub skonsultuj się z dokumentacją Streamlit.
