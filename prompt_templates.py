

prompt_templates = {
            "Standardowy": {
                "template": (
                    "**Jako analityk z 10 letnim stażem i doświadczeniem w notacji PlantUML przygotuj diagram {diagram_type} w notacji PlantUML dla procesu:**\n\n"
                    "{process_description}\n\n"
                    "**Wymagania:**\n"
                    "- Format: Kompletny kod PlantUML (@startuml ... @enduml)\n"
                    "- Uwzględnij wszystkich uczestników procesu\n"
                    "- Zachowaj logiczną sekwencję kroków\n\n"
                    "**Output:** Gotowy kod PlantUML"
                ),
                "allowed_diagram_types": "all",  # lub lista np. ["sequence", "activity", ...]
                "type": "PlantUML"
            },
            "Z checklistą": {
                "template": (
                    "**ZADANIE:** Jako analityk z 10 letnim stażem i doświadczeniem w notacji PlantUML stwórz diagram PlantUML dla procesu:\n\n"
                    "{process_description}\n\n"
                    "**CHECKLIST do sprawdzenia:**\n"
                    "- [ ] Kod zaczyna się od @startuml\n"
                    "- [ ] Kod kończy się na @enduml\n"
                    "- [ ] Wszyscy aktorzy są zdefiniowani\n"
                    "- [ ] Sekwencja jest logiczna\n"
                    "- [ ] Typ diagramu: {diagram_type}\n\n"
                    "**DOSTARCZ:** Kompletny, działający kod PlantUML"
                ),
                "allowed_diagram_types": "all",  # lub lista np. ["sequence", "activity", ...]
                "type": "PlantUML"
            },
            "Diagram klas": {
                "template": (
                    "Jako analityk z 10 letnim stażem i doświadczeniem w notacji PlantUML przeanalizuj poniższy proces biznesowy i przedstaw go jako diagram klas w PlantUML:\n\n"
                    "{process_description}\n\n"
                    "Oczekiwany format odpowiedzi:\n\n"
                    "```plantuml\n"
                    "@startuml\n"
                    "class ClassName {{\n"
                    "    +attribute1: Type\n"
                    "    -attribute2: Type\n"
                    "    +method1(): ReturnType\n"
                    "}}\n"
                    "@enduml\n"
                    "```\n\n"
                    "Upewnij się, że diagram zawiera:\n"
                    "- Poprawną składnię PlantUML\n"
                    "- Klasy z atrybutami i metodami\n"
                    "- Relacje między klasami (np. dziedziczenie, asocjacje)\n"
                    "- Komentarze opisujące klasy i ich relacje\n"
                    "- Klasy, enumy i interfejsy, jeśli są istotne mają poprawną składnię jak w przykładzie dla klasy\n\n"
                    "Zwróć uwagę na poprawność składni PlantUML."
                    ),
                "allowed_diagram_types": ["class"],  # Tylko diagramy klas
                "type": "PlantUML"
            },
            "Diagram komponentów - Notacja C4": {
                "template": (
                    "Jako doświadczony kodel PlantUML i analityk systemowy wygeneruj diagram komponentów w PlantUML dla:\n {process_description}\n z następującymi wymaganiami:\n\n"
                    "**WYMAGANIA TECHNICZNE:**\n"
                    "1. Użyj WYŁĄCZNIE w notacji C4: użyj `!include <C4/C4_Context>` i makr Person(), System(), Container(), ContainerDb()\n"              
                    "2. **STRUKTURA KODU:**\n"
                    "   - Rozpocznij od @startuml\n"
                    "   - Dodaj tytuł: `title [Nazwa Systemu] - Diagram Komponentów`\n"
                    "   - Dodaj odpowiednie include na początku\n"
                    "   - Zakończ @enduml\n"
                    "3. **DEFINICJE KOMPONENTÓW:**\n"
                    "   - Zdefiniuj WSZYSTKIE komponenty przed użyciem w relacjach\n"
                    "   - Każdy komponent musi mieć unikalną nazwę i opis\n"
                    "   - Użyj spójnego nazewnictwa (tylko polski LUB tylko angielski)\n"
                    "   - Grupuj powiązane komponenty w package/System_Boundary\n"
                    "4. **RELACJE:**\n"
                    "   - Użyj jasnych etykiet dla połączeń\n"
                    "   - Określ kierunek relacji (-->, <--, <-->)\n"
                    "   - Dodaj opis typu komunikacji (HTTP, SQL, HTTPS, etc.)\n"
                    "5. **ZABRONIONE PRAKTYKI:**\n"
                    "   - NIE używaj mieszanej notacji C4 i podstawowej składni PlantUML\n"
                    "   - NIE używaj niezdefiniowanych komponentów w relacjach\n"
                    "   - NIE pozostawiaj pustych lub niejasnych nazw komponentów\n"
                    "   - NIE duplikuj nazw baz danych bez rozróżnienia\n"
                    "6. **PRZYKŁAD DOBREJ STRUKTURY (C4):**\n"
                    "@startuml\n"
                    "!include <C4/C4_Context>\n"
                    "title System X - Diagram Komponentów\n\n"
                    "Person(user, \"Użytkownik\", \"Opis użytkownika\")\n\n"
                    "System_Boundary(system, \"System X\") {{\n"
                    "    Container(api, \"API Gateway\", \"Tech\", \"Opis\")\n"
                    "    Container(service, \"Serwis\", \"Tech\", \"Opis\")\n"
                    "    ContainerDb(db, \"Baza\", \"Tech\", \"Opis\")\n"
                    "}}\n\n"
                    "Rel(user, api, \"Używa\", \"HTTPS\")\n"
                    "Rel(api, service, \"Przekazuje\", \"HTTP\")\n"
                    "Rel(service, db, \"Zapisuje\", \"SQL\")\n"
                    "@enduml\n"
                    "\n\n"
                ),
                "allowed_diagram_types": ["component"],  # Tylko diagramy komponentów
                "type": "PlantUML"
            },
            "Diagram komponentów - Podstawowa notacja": {
                "template": (
                    "Jako doświadczony kodel PlantUML i analityk systemowy wygeneruj diagram komponentów w PlantUML dla:\n {process_description}\n z następującymi wymaganiami:\n\n"
                    "**WYMAGANIA TECHNICZNE:**\n"
                    "1. Użyj WYŁĄCZNIE podstawowej notacją PlantUML: użyj `component`, `database`, `actor` bez include C4:\n"
                    "2. **STRUKTURA KODU:**\n"
                    "   - Rozpocznij od @startuml\n"
                    "   - Dodaj tytuł: `title [Nazwa Systemu] - Diagram Komponentów`\n"
                    "   - Zakończ @enduml\n"
                    "3. **DEFINICJE KOMPONENTÓW:**\n"
                    "   - Zdefiniuj WSZYSTKIE komponenty przed użyciem w relacjach\n"
                    "   - Każdy komponent musi mieć unikalną nazwę i opis\n"
                    "   - Użyj spójnego nazewnictwa (tylko polski LUB tylko angielski)\n"
                    "   - Grupuj powiązane komponenty w package/System_Boundary\n"
                    "4. **RELACJE:**\n"
                    "   - Użyj jasnych etykiet dla połączeń\n"
                    "   - Określ kierunek relacji (-->, <--, <-->)\n"
                    "   - Dodaj opis typu komunikacji (HTTP, SQL, HTTPS, etc.)\n"
                    "5. **ZABRONIONE PRAKTYKI:**\n"
                    "   - NIE używaj mieszanej notacji C4 i podstawowej składni PlantUML\n"
                    "   - NIE używaj niezdefiniowanych komponentów w relacjach\n"
                    "   - NIE pozostawiaj pustych lub niejasnych nazw komponentów\n"
                    "   - NIE duplikuj nazw baz danych bez rozróżnienia\n"
                    "6. **PRZYKŁAD DOBREJ STRUKTURY (Podstawowa):**\n"
                    "@startuml\n"
                    "title System X - Diagram Komponentów\n"
                    "actor \"Użytkownik\" as User"
                    "package \"System X\" {{\n"
                    "    component \"API Gateway\" as API\n"
                    "    component \"Serwis\" as Service\n"
                    "    database \"Baza Danych\" as DB\n"
                    "}}\n\n"
                    "User --> API : \"HTTPS\"\n"
                    "API --> Service : \"HTTP\"\n"
                    "Service --> DB : \"SQL\"\n"
                    "@enduml\n\n"
                ),
                "allowed_diagram_types": ["component"],  # Tylko diagramy komponentów
                "type": "PlantUML"
            },
            "XML": {
                "template": (
                    "**Jako analityk z 10 letnim stażem i doświadczeniem w notacji BPMN przygotuj proces biznesowy zgodnie z:**\n\n"
                    "{process_description}\n\n"
                    "**Wymagania:**\n"
                    "- Format: Kompletny, poprawny kod XML BPMN 2.0 gotowy do importu w Camunda Modeler\n"
                    "- Uwzględnij wszystkie elementy wymagane przez Camunda (włącznie z diagramem DI)\n"
                    "- Użyj Pool i Lane dla różnych uczestników procesu\n"
                    "- Zastosuj odpowiednie typy zadań (User Task, Service Task, Send Task, Receive Task)\n"
                    "- Dodaj Message Flow między różnymi uczestnikami\n\n"
                    "**Definiuj uczestników procesu jak:**\n"
                    "1. Klient (Pool: \"Klient\")\n"
                    "2. Sprzedawca/Terminal (Pool: \"Sprzedawca\")\n"
                    "3. System BLIK (Pool: \"System BLIK\")\n"
                    "4. Bank (Pool: \"Bank Klienta\")\n"
                    "**DODATKOWE WYMAGANIA:**\n"
                    "- Dodaj bramki decyzyjne tam gdzie proces może się rozgałęzić\n"
                    "- Uwzględnij scenariusze błędów (brak środków, nieprawidłowy kod, timeout)\n"
                    "- Użyj odpowiednich typów zdarzeń (Start Event, End Event, Message Events)\n"
                    "- Wszystkie elementy muszą mieć prawidłowe ID i nazwy w języku polskim\n"
                    "- Kod musi być kompletny i gotowy do uruchomienia bez dodatkowych modyfikacji\n"
                    "- Pamiętaj o takich sekcjach jak `<definitions>`, `<process>`, `<bpmn:collaboration>`, `<bpmn:participant>`, `<bpmn:laneSet>`, `<bpmn:lane>`, '<bpmndi:BPMNDiagram>'\n"
                    "- Użyj poprawnej struktury XML z odpowiednimi przestrzeniami nazw (xmlns)\n"
                    "- Upewnij się, że wszystkie elementy są poprawnie zagnieżdżone i zamknięte\n"
                    "- Użyj poprawnych atrybutów dla każdego elementu BPMN (np. `id`, `name`, `type`, `messageRef`)\n"
                    "- Upewnij się, że wszystkie elementy mają unikalne ID i są poprawnie zdefiniowane\n"
                    "**Kluczowe elementy sekcji BPMNDiagram:**\n"  
                    "- `<bpmndi:BPMNPlane>`: zawiera elementy diagramu\n"
                    "- `<bpmndi:BPMNShape>`: definiuje kształty elementów na diagramie\n"
                    "- `<bpmndi:BPMNEdge>`: definiuje krawędzie między elementami\n"   
                    "- `<bpmndi:BPMNLabel>`: definiuje etykiety dla elementów\n"
                    "- `<bpmndi:BPMNLabelStyle>`: definiuje styl etykiet\n"
                    "- `<bpmndi:BPMNDiagram>`: główny element diagramu BPMN\n"
                    "- Wszystkie te elementy muszą być poprawnie zagnieżdżone w `<bpmndi:BPMNDiagram>`\n\n"
                    "**DOSTARCZ:** Kompletny, działający kod XML BPMN 2.0 gotowy do importu w Camunda Modeler"
                ),
                "allowed_diagram_types": ["BPMN"],  # Tylko diagram procesu biznesowego
                "type": "XML"
            },
            "Weryfikacja kodu PlantUML": {
                "template": (
                    "**Sprawdź poniższy kod PlantUML pod kątem poprawności składni oraz brakujących lub błędnych elementów.**\n"
                    "Uwzględnij że powinien to być kod PlantUML dla diagramu o typie: {diagram_type}\n"
                    "Kod do weryfikacji:\n"
                    "```plantuml\n"
                    "{plantuml_code}\n"
                    "```\n\n"
                    "**Wymagania:**\n"
                    "- Wskaż dokładnie, które linie lub fragmenty są niepoprawne lub niezgodne z notacją PlantUML\n"
                    "- Zasugeruj poprawki lub uzupełnienia\n"
                    "- Jeśli kod jest poprawny, napisz: 'Kod jest poprawny i kompletny.'"
                ),
                "allowed_diagram_types": "all",
                "type": "Verification"  # szablon do weryfikacji kodu PlantUML
            },
            "Weryfikacja opisu procesu": {
               "template": (
                    "**Sprawdź poniższy opis procesu pod kątem kompletności i poprawności biznesowej.**\n\n"
                    "{process_description}\n\n"
                    "**Wymagania:**\n"
                    "- Wskaż, czy opis zawiera wszystkie kluczowe kroki procesu\n"
                    "- Zasugeruj ewentualne poprawki lub uzupełnienia\n"
                    "- Jeśli opis jest poprawny, napisz: 'Opis jest poprawny i kompletny.'"
                ),
                "allowed_diagram_types": "all",
                "type": "Validation"
    }
}