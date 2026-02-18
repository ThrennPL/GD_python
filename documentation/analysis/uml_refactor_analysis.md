# 1. Struktura Katalogów (Nowy Moduł)
Zgodnie z założeniem "osobnego modułu domenowego", sugeruję utworzenie nowej przestrzeni w src, która będzie sąsiadować z istniejącą logiką BPMN, ale pozostanie od niej całkowicie niezależna.

    └── uml_refactor/
        ├── __init__.py
        ├── service.py          # UMLImageRefactorService (Orkiestracja)
        ├── vision.py           # VisionExtractor (Interfejs do multimodalnych modeli)
        ├── engine.py           # RefactorEngine (Logika modyfikacji kodu PlantUML)
        └── validator.py        # PlantUMLValidator (Weryfikacja składni przed renderowaniem)

# 2. Logika Przepływu (Sequence Diagram)
Wprowadzenie 2-etapowego pipeline'u wewnątrz modułu zapewni najwyższą precyzję. Zamiast liczyć na to, że model "zgadnie" wszystko na raz, dzielimy proces na ekstrakcję i transformację.
- **VisionExtractor**: Wysyła obraz do modelu multimodalnego (np. GPT-4o) z promptem: *"Zmień ten obraz na kod PlantUML. Zwróć tylko kod."*
- **"RefactorEngine**: Bierze uzyskany kod tekstowy oraz instrukcję użytkownika i wykonuje drugie uderzenie do modelu (może być tańszy model tekstowy): *"Oto kod PlantUML: [KOD]. Zmodyfikuj go tak: [INSTRUKCJA]."*
- **"Validator**: Sprawdza, czy wynik zawiera @startuml i @enduml oraz czy nie ma krytycznych błędów składniowych.

Właściwy tekst promptów zostanie doprecyzowany podczas dewelopmentu.

# 3. Integracja z AIProviders
Aby nie łamać zasady DRY (Don't Repeat Yourself) i uniknąć silnego powiązania, moduł powinien przyjmować instancję adaptera AI w konstruktorze.

*Przykład w src/uml_refactor/vision.py*

	class VisionExtractor:
        def __init__(self, ai_provider):
            self.ai_provider = ai_provider
        def extract_from_image(self, image_path: str) -> str:
            # Logika konwersji obrazu na base64 i wywołanie generate()
            # wykorzystując istniejący interfejs w AIProviders
            pass


# 4. Alternatywne źródło PlantUML
W CoreApp (Orchestrator) musisz zdefiniować moment, w którym system decyduje o wyborze źródła. Możesz wprowadzić prostą fabrykę lub strategię:

| Źródło (Input) | Przetwarzanie | Cel (Output) |
| ---| ---| ---|
| Plik .bpmn | BPMNAdapter| PlantUML Code |
| Obraz .png/.jpg | UMLImageRefactor | PlantUML Code |
| Tekst (Prompt) | ImprovementEngine | PlantUML Code| 

Wszystkie te drogi schodzą się w jednym punkcie: PlantUMLTooling, który zajmuje się renderowaniem końcowym. Dzięki temu reszta systemu nie musi wiedzieć, czy diagram powstał z pliku XML, czy z rysunku odręcznego na serwetce.

# 5. Rekomendacja dot. "Model Repository"
Skoro chcemy mieć repozytorium modeli, warto w konfiguracji modułu UMLImageRefactor umożliwić definiowanie różnych modeli dla różnych etapów:
- vision_model: gpt-4o (najlepszy OCR i rozumienie schematów)
- refactor_model: gpt-4o-mini lub Claude Haiku (szybka i tania transformacja tekstu)

# 6. Konfiguracja i Hybrydowość (.env)
Rozszerzenie pliku .env o dedykowane parametry dla tego modułu. Pozwoli to na elastyczne mieszanie zasobów – na przykład użycie potężnego modelu chmurowego (Gemini/OpenAI) do trudnej analizy obrazu (Vision) i taniego lub lokalnego modelu do końcowej edycji tekstu (Refactor).
- **Zmienne sterujące**: Powinny definiować identyfikatory modeli dla obu etapów (Vision i Refactor).
- **Flagi dostawcy**: Określenie, czy dany etap ma uderzać do lokalnego endpointu LM Studio, czy do zewnętrznego API.
- **Parametry jakościowe**: Np. temperature dla modelu wizyjnego (zwykle niższa dla lepszej precyzji OCR).

# 7. Architektura serwisu UMLImageRefactorService
Serwis ten pełni rolę orkiestratora. Nie wykonuje on bezpośrednio zapytań HTTP, lecz deleguje zadania do podległych mu komponentów, korzystając z wstrzykniętego AIProvider.

Sekcje wewnątrz serwisu:
- **Inicjalizacja (Constructor)**:
    
    Tutaj następuje wstrzyknięcie zależności: AIProvider, LoggingService oraz Metrics. W tym miejscu tworzone są też instancje wewnętrznych "silników": VisionExtractor oraz RefactorEngine.

- **Metoda główna (Process Refactor)**:
    
    Przyjmuje ścieżkę do obrazu oraz tekstową instrukcję zmiany. Odpowiada za sekwencyjne wywołanie etapów: najpierw ekstrakcji, potem modyfikacji. Zarządza przepływem danych między nimi.

- **Etap 1: VisionExtractor (Analiza obrazu)**:

    **Opis działania**: Komponent ten odpowiada za przygotowanie obrazu (np. konwersję do Base64) i sformułowanie promptu systemowego dla modelu multimodalnego. Jego zadaniem jest "przepisanie" tego, co widzi na obrazku, na surowy kod PlantUML. Musi on obsłużyć błąd, jeśli model lokalny (np. w LM Studio) nie posiada zdolności wizyjnych.

- **Etap 2: RefactorEngine (Transformacja kodu)**:

    **Opis działania**: Przyjmuje kod wygenerowany w poprzednim kroku oraz instrukcję użytkownika. Wysyła zapytanie do modelu tekstowego. To tutaj dzieje się "magia" modyfikacji architektury (np. zamiana klas, dodawanie relacji).

- **Etap 3: PlantUMLValidator (Weryfikacja)**:

    **Opis działania**: Pasywny komponent, który sprawdza, czy wynik końcowy zawiera poprawne tagi @startuml / @enduml i czy struktura kodu nie została uszkodzona podczas generowania.

- **Obsługa błędów i Metryki**:

    Każdy etap jest logowany. W przypadku niepowodzenia na etapie wizji (np. nieczytelny diagram), system przerywa proces przed wysłaniem zapytania do edytora, co optymalizuje koszty i czas.

# 8. Integracja z istniejącym systemem
Dzięki takiemu podejściu, CoreApp traktuje UMLImageRefactorService jako kolejne źródło danych wejściowych.

- **AIProviders**: Nie wymagają zmian w logice – muszą jedynie obsługiwać opcjonalny parametr z danymi obrazu w metodzie generującej odpowiedź.

- **PlantUMLTooling**: Otrzymuje gotowy, poprawiony kod tekstowy, dokładnie tak samo, jakby pochodził on z adaptera BPMN. Jest to całkowicie przezroczyste dla procesu renderowania i eksportu.

## Uzupełnienie: Kontrakt AIProvider (multimodal)
Cel: rozszerzyć istniejący kontrakt AIProvider tak, by obsługiwał wejście obrazowe bez utraty polimorfizmu.

Zakładamy, że metoda generująca odpowiedź akceptuje opcjonalny argument obrazu, a konkretne adaptery (OpenAI/Gemini/LM Studio) same odpowiadają za pakowanie danych do JSON. Kontrakt powinien wspierać listę content blocks (tekst + obraz) jako standardowy format multimodalny.

Checklist do dopisania w kontrakcie:
- Opcjonalny parametr obrazu (np. image_data) w metodzie generujacej odpowiedz.
- Akceptacja base64 lub sciezki do pliku jako danych wejsciowych.
- Content blocks jako standard (tekst i obraz jako oddzielne bloki).
- Brak zmiany istniejacych wywolan tekstowych (backward compatibility).

## Uzupełnienie: VisionExtractor
Cel: zdefiniować komponent, ktory przygotowuje obraz i wywoluje AIProvider bez znajomosci HTTP.

VisionExtractor powinien walidowac plik (typ, rozmiar), konwertowac obraz do base64 i budowac system prompt ukierunkowany na UML/PlantUML. Zwraca surowy kod PlantUML jako tekst, bez dodatkowego przetwarzania.

Checklist:
- Walidacja formatu obrazu (png, jpg) i rozmiaru pliku.
- Konwersja do base64 oraz przygotowanie payloadu dla AIProvider.
- System prompt skoncentrowany na strukturze UML (klasy, relacje, kierunki strzalek, typy zaleznosci).
- Wywolanie AIProvider.generate() z obrazem i zwrot raw content.

## Uzupełnienie: AIResponse (multimodal)
Cel: ujednolicic odpowiedz z modelu wizji z istniejacym kontraktem AIResponse.

AIResponse powinien zawierac surowy kod PlantUML, nazwe modelu oraz metadane (np. confidence, flagi wykrycia obrazu), gdy provider je zwraca. Format pozostaje zgodny z obecnymi wywolaniami tekstowymi.

Checklist:
- Pole content: raw PlantUML.
- Pole model: nazwa modelu, ktory wykonal ekstrakcje.
- Pole metadata: opcjonalne informacje o pewnosci/wykryciu obrazu.
- Zgodnosc wsteczna z odpowiedziami tekstowymi.

## Uzupełnienie: Konfiguracja (.env) i hybryda
Cel: doprecyzowac zmienne srodowiskowe i zasady fallbacku dla trybu wizji i refactoru.

Wprowadzamy osobne zmienne dla modeli i dostawcow, z jasnym priorytetem nad globalnymi ustawieniami. Adaptery powinny wspierac tryb lokalny (LM Studio) i chmurowy (OpenAI/Gemini) oraz fail-fast, gdy brak wsparcia wizji.

Checklist:
- Zmienne: UML_VISION_MODEL, UML_REFACTOR_MODEL.
- Zmienne: UML_VISION_PROVIDER, UML_REFACTOR_PROVIDER.
- Zmienne: UML_VISION_TEMPERATURE, UML_REFACTOR_TEMPERATURE.
- Priorytety: gdy ustawione, nadpisuja MODEL_PROVIDER, API_KEY, CHAT_URL.
- Fallback: jasne komunikaty bledu, gdy provider lub model nie wspiera obrazow.

## Uzupełnienie: LM Studio /v1/responses (wizja)
Cel: opisac praktyczny sposob wywolania modelu multimodalnego w LM Studio oraz ograniczenia kompatybilnosci.

Zakladamy, ze LM Studio udostepnia endpoint /v1/responses i ze model wspiera format zgodny z OpenAI (content blocks). Jesli model nie jest multimodalny, adapter powinien przerwac wykonanie z czytelnym bledem.

Przyklad requestu (bazowy, bez obrazu):

        curl http://localhost:1234/v1/responses \
            -H "Content-Type: application/json" \
            -d '{
                "model": "qwen3-vl-8b-instruct",
                "input": "What is the weather like in Boston today?",
                "tool_choice": "auto"
            }'

Przyklad requestu (z obrazem, format content blocks - do doprecyzowania w implementacji adaptera):

        curl http://localhost:1234/v1/responses \
            -H "Content-Type: application/json" \
            -d '{
                "model": "qwen3-vl-8b-instruct",
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Zmien ten obraz UML na kod PlantUML. Zwracaj tylko kod."},
                            {"type": "image_url", "image_url": {"url": "data:image/png;base64,BASE64_DATA"}}
                        ]
                    }
                ]
            }'

Uwagi:
- Format z obrazem zalezy od wsparcia modelu w LM Studio; adapter powinien walidowac kompatybilnosc.
- W pierwszej iteracji wystarczy obsluga base64 w polu image_url; sciezka do pliku moze byc mapowana do base64 w VisionExtractor.

## Uzupełnienie: Capability check (Vision)
Cel: jasno okreslic, jak system sprawdza wsparcie wejscia obrazowego u dostawcy oraz jak komunikuje brak kompatybilnosci.

Reguly sprawdzania:
- Provider chmurowy: sprawdz wsparcie multimodalne na podstawie znanego modelu (whitelist) lub flag w konfiguracji.
- LM Studio: sprawdz, czy model jest multimodalny (nazwa/konfiguracja) oraz czy endpoint akceptuje content blocks z image_url.
- Jesli brak wsparcia, zwroc blad przed wywolaniem API (fail-fast).

Checklist:
- Zdefiniowac sposob wykrywania wsparcia multimodalnego dla providera.
- Zdefiniowac komunikat bledu dla UI (czytelny, bez wchodzenia w technikalia).
- W przypadku braku wsparcia, nie wykonywac zadnego wywolania do API.

## Uzupełnienie: Walidacja PlantUML
Cel: potwierdzic wybor mechanizmu walidacji wynikowego kodu PlantUML.

Decyzja: walidacja powinna odbywac sie przez render (jar/www), bo to referencyjne narzedzie tworcow PlantUML i najlepiej wychwytuje bledy skladniowe oraz interpretacyjne.

Minimalne reguly walidacji:
- Sprawdz obecność @startuml i @enduml przed wyslaniem do rendera.
- Przy renderze traktuj bledy parsera jako twarde bledy walidacji.
- W przypadku bledow rendera zwroc czytelny komunikat oraz fragment diagnostyczny.

## Uzupełnienie: Integracja z UI (Streamlit/PyQt)
Cel: zdefiniowac proste sterowanie trybem obrazu i powiazanie z pipeline oraz promptami.

Zalozenia UI:
- Checkbox: decyzja, czy uzywamy obrazu jako zrodla wejscia.
- Przycisk/selector pliku: wskazanie obrazu (png/jpg).
- Po wskazaniu: wyswietlenie linku do pliku z pelna lokalizacja.

Zasady przeplywu:
- Checkbox wymusza uruchomienie sekwencji VisionExtractor -> RefactorEngine -> Validator.
- Zawsze zachowujemy typ diagramu i szablon wybrany przez uzytkownika (prompt i walidacja musza je respektowac).
- Gdy checkbox nieaktywny, pipeline dziala jak dotychczas (bez trybu obrazu).

Session state (Streamlit):
- uml_image_enabled: bool (czy tryb obrazu aktywny)
- uml_image_path: str (pelna sciezka do pliku)
- uml_image_name: str (nazwa pliku do wyswietlenia)
- uml_image_last_error: str (ostatni blad walidacji obrazu/promptu)

## Uzupełnienie: Mapowanie typow diagramow i promptow
Cel: zdefiniowac spojnosc miedzy identyfikacja typu diagramu (PlantUMLDiagramIdentifier) a wyborem szablonow promptow.

Podstawy:
- PlantUMLDiagramIdentifier zwraca nazwy typu w jezyku polskim (np. Diagram klas, Diagram sekwencji).
- Szablony promptow w prompts/prompt_templates_pl.py maja zdefiniowane klucze tematyczne i allowed_diagram_types.
- Ostateczny wybor szablonu powinien zawsze respektowac preferencje uzytkownika, a mapowanie sluzy jako fallback.

Mapa domyslna (fallback) na podstawie prompt_templates_pl.py:
- Diagram sekwencji -> "Diagram sekwencji" (allowed_diagram_types: ["sequence"]).
- Diagram aktywnosci -> "Diagram aktywnosci" (allowed_diagram_types: ["activity"]).
- Diagram przypadkow uzycia -> "Diagram przypadkow uzycia" (allowed_diagram_types: ["usecase"]).
- Diagram klas -> "Diagram klas" (allowed_diagram_types: ["class"]).
- Diagram komponentow -> "Diagram komponentow - Podstawowa notacja" lub "Diagram komponentow - Notacja C4" (wybor przez uzytkownika).
- Diagram przeplywow -> "Diagram przeplywow" (allowed_diagram_types: ["flowchart"]).
- Diagram stanow / Diagram obiektow -> "Standardowy" (brak dedykowanego szablonu).
- Diagram ogolny -> "Standardowy".

## Uzupełnienie: Polityka plikow i prywatnosci
Cel: okreslic, jak przechowujemy obrazy oraz kiedy je usuwamy, aby ograniczyc ryzyko ujawnienia danych.

Zasady przechowywania:
- Obrazy trafiaja do katalogu tymczasowego (np. temp/uml_refactor lub systemowy tmp).
- Pliki sa usuwane po zakonczeniu procesu (sukces lub blad), chyba ze uzytkownik zaznaczy opcje zachowania.
- W logach nie zapisujemy pelnych obrazow ani ich base64; dopuszczalny jest hash (np. sha256).

## Uzupełnienie: Limity i pre-processing obrazow
Cel: ograniczyc koszty i poprawic jakosc ekstrakcji UML przed wyslaniem do modelu.

Limity i skalowanie:
- Maksymalny rozmiar pliku: 10 MB (konfigurowalny w .env).
- Maksymalne wymiary: np. 2048x2048 px, obraz powyzej limitu jest skalowany.
- Akceptowane formaty: PNG, JPG.

Pre-processing:
- Skala do max wymiaru z zachowaniem proporcji.
- Opcjonalne wyostrzenie/kontrast tylko jesli wykryto zbyt niska czytelnosc.
- Zachowaj kolor, gdy diagram zawiera rozroznienia kolorystyczne.
- Jesli format jest niestandardowy (np. webp, bmp), automatycznie konwertuj do PNG przed wysylka do API.

## Uzupełnienie: Testy (unit + integration)
Cel: zapewnic minimalne pokrycie kluczowych elementow pipeline'u obrazu i walidacji PlantUML.

Zakres testow jednostkowych:
- VisionExtractor: walidacja formatu, rozmiaru i konwersji do base64.
- RefactorEngine: budowanie promptu z zachowaniem typu diagramu i szablonu.
- Validator: wykrycie brakujacych tagow @startuml/@enduml.

Zakres testow integracyjnych:
- Obraz -> VisionExtractor -> RefactorEngine -> Validator -> render (mock AI).
- Wariant negatywny: obraz niepoprawny lub brak wsparcia wizji (fail-fast).
- Wariant UI: checkbox wlaczony/wylaczony i zachowanie przeplywu.

## Nowe watpliwosci po przegladzie
- Brakuje polityki przechowywania i czyszczenia plikow obrazow (tmp/cache) oraz zasad prywatnosci.
- Nie zdefiniowano limitow rozmiaru obrazow i strategii skalowania (resize) przed wysylka do modelu.
- Nie ma doprecyzowania, jak logujemy artefakty (obraz, prompty) i czy sa maskowane w logach. Logowanie zostanie rozwiazane w osobnym module, a na tym etapie bazujemy na istniejacej funkcjonalnosci.

# 9. Nowy plan uzupełnień (po przegladzie)
Poniższy plan odnosi sie do nowych brakow wykrytych po przegladzie kompletnej analizy.
Status: plan zrealizowany z wyjatkiem logow (osobny modul).

- [x] Krok 1: Polityka plikow i prywatnosci (czesciowo)
    - [x] Okreslic, gdzie przechowywane sa obrazy (tmp/cache) i kiedy sa usuwane.
    - [ ] Zdefiniowac zasady anonimizacji/maskowania w logach (pomijamy na razie).

- [x] Krok 2: Limity i pre-processing obrazow
    - [x] Zdefiniowac maksymalny rozmiar pliku i dopuszczalne wymiary.
    - [x] Opisac strategie skalowania/kompresji przed wysylka do modelu.

- [x] Krok 3: Mapowanie typu diagramu i szablonu na prompty
    - [x] Okreslic, jak typ diagramu i szablon wplywaja na prompt Vision/Refactor.
    - [x] Zdefiniowac fallback, gdy typ nie jest rozpoznany.

## Poza zakresem obecnej analizy (osobny modul)
- Logowanie artefaktow i metryk (prompt, model, czas, status) oraz polityka logowania obrazu (np. hash).