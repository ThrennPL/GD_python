

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
                    "Jako doświadczony koder PlantUML i architekt systemowy wygeneruj diagram komponentów C4 w PlantUML dla:\n{process_description}\n"
                    "z następującymi wymaganiami:\n\n"
        
                    "**WYMAGANIA TECHNICZNE C4 COMPONENT:**\n"
                    "1. **INCLUDES:** Użyj WYŁĄCZNIE:\n"
                    "   - `!include <C4/C4_Component>`\n"
                    "   - Opcjonalnie `!include <C4/C4_Container>` jeśli pokazujesz kontekst kontenerów\n\n"
        
                    "2. **DOSTĘPNE MAKRA:**\n"
                    "   - `Component(alias, \"Nazwa\", \"Technologia\", \"Opis funkcjonalności\")`\n"
                    "   - `ComponentDb(alias, \"Nazwa DB\", \"Typ DB\", \"Opis danych\")`\n"
                    "   - `ComponentQueue(alias, \"Nazwa Queue\", \"Technologia\", \"Opis kolejki\")`\n"
                    "   - `Container()` - TYLKO dla kontekstu, nie jako główne elementy\n\n"
        
                    "3. **STRUKTURA DIAGRAMU:**\n"
                    "   - Rozpocznij: `@startuml`\n"
                    "   - Include: `!include <C4/C4_Component>`\n"
                    "   - Tytuł: `title [System] - Diagram Komponentów (C4 Level 3)`\n"
                    "   - Opcjonalnie kontekst kontenera: `Container_Boundary(container, \"Kontener\")`\n"
                    "   - Definicje wszystkich komponentów\n"
                    "   - Relacje między komponentami\n"
                    "   - Zakończ: `@enduml`\n\n"
        
                    "4. **POZIOM SZCZEGÓŁOWOŚCI:**\n"
                    "   - Pokazuj komponenty WEWNĄTRZ jednego kontenera/systemu\n"
                    "   - Każdy komponent = konkretna odpowiedzialność biznesowa\n"
                    "   - NIE mieszaj poziomów abstrakcji (System vs Component)\n"
                    "   - Skupij się na przepływie danych i wywołaniach między komponentami\n\n"
        
                    "5. **RELACJE:**\n"
                    "   - `Rel(źródło, cel, \"Etykieta\", \"Protokół/Technologia\")`\n"
                    "   - `Rel_Back()`, `Rel_Neighbor()` dla lepszego layoutu\n"
                    "   - Zawsze opisuj CZYM jest komunikacja (API call, event, data flow)\n\n"
        
                    "6. **NAZEWNICTWO:**\n"
                    "   - Konsekwentny język (polski LUB angielski)\n"
                    "   - Nazwy komponentów = rzeczowniki opisujące funkcję\n"
                    "   - Aliasy = krótkie, bez spacji, snake_case lub camelCase\n\n"
        
                    "7. **PRZYKŁAD POPRAWNEJ STRUKTURY:**\n"
                    "```plantuml\n"
                    "@startuml\n"
                    "!include <C4/C4_Component>\n"
                    "title System Zamówień - Komponenty (C4 Level 3)\n\n"
        
                    "Container_Boundary(api_container, \"API Container\") {{\n"
                    "    Component(order_controller, \"Order Controller\", \"Spring MVC\", \"Obsługuje żądania HTTP dla zamówień\")\n"
                    "    Component(order_service, \"Order Service\", \"Spring Bean\", \"Logika biznesowa zamówień\")\n"
                    "    Component(payment_service, \"Payment Service\", \"Spring Bean\", \"Obsługa płatności\")\n"
                    "    Component(notification_service, \"Notification Service\", \"Spring Bean\", \"Wysyłanie powiadomień\")\n"
                    "    ComponentDb(order_db, \"Orders Database\", \"PostgreSQL\", \"Przechowuje dane zamówień\")\n"
                    "    ComponentQueue(order_queue, \"Order Events\", \"RabbitMQ\", \"Kolejka zdarzeń zamówień\")\n"
                    "}}\n\n"
        
                    "Rel(order_controller, order_service, \"Wywołuje\", \"Method call\")\n"
                    "Rel(order_service, payment_service, \"Przetwarza płatność\", \"Method call\")\n"
                    "Rel(order_service, order_db, \"Zapisuje zamówienie\", \"SQL\")\n"
                    "Rel(order_service, order_queue, \"Publikuje zdarzenie\", \"AMQP\")\n"
                    "Rel(notification_service, order_queue, \"Nasłuchuje zdarzeń\", \"AMQP\")\n"
                    "@enduml\n"
                    "```\n\n"
        
                    "8. **ZABRONIONE PRAKTYKI:**\n"
                    "   - ❌ Mieszanie makr z różnych poziomów C4\n"
                    "   - ❌ Używanie `System()` w diagramie komponentów\n"
                    "   - ❌ Pokazywanie komponentów z różnych kontenerów bez kontekstu\n"
                    "   - ❌ Niejasne nazwy typu \"Service1\", \"Database\"\n"
                    "   - ❌ Relacje bez opisów technologii komunikacji\n\n"
        
                    "**REZULTAT:** Wygeneruj kompletny, działający kod PlantUML przedstawiający komponenty wewnątrz systemu/kontenera zgodnie z poziomem 3 modelu C4."
                ),
                "allowed_diagram_types": ["component"],
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
                    "**Weryfikacja opisu procesu dla diagramu typu: {diagram_type}**\n\n"
                    "**Opis procesu do weryfikacji:**\n"
                    "{process_description}\n\n"
                    "**Przeprowadź szczegółową analizę zgodnie z wymaganiami dla diagramu {diagram_type}:**\n\n"
        
                    # Wymagania ogólne
                    "**1. ANALIZA OGÓLNA:**\n"
                    "- Czy proces ma jasno określony punkt początkowy i końcowy?\n"
                    "- Czy wszystkie kroki są logicznie powiązane?\n"
                    "- Czy brakuje jakichś kluczowych elementów procesu?\n"
                    "- Czy opis jest jednoznaczny i zrozumiały?\n\n"
        
                    # Wymagania specyficzne dla typu diagramu
                    "**2. WYMAGANIA SPECYFICZNE DLA {diagram_type}:**\n"
                    "{diagram_specific_requirements}\n\n"
        
                    "**3. WERYFIKACJA KOMPLETNOŚCI:**\n"
                    "- Sprawdź czy wszystkie niezbędne role/aktorzy są zidentyfikowani\n"
                    "- Zweryfikuj czy wszystkie decyzje i punkty rozgałęzienia są opisane\n"
                    "- Upewnij się czy wszystkie wyjątki i ścieżki alternatywne są uwzględnione\n\n"
        
                    "**4. REZULTAT WERYFIKACJI:**\n"
                    "Podaj wynik w następującym formacie:\n"
                    "- **STATUS:** [POPRAWNY/WYMAGA_POPRAWEK/NIEPEŁNY]\n"
                    "- **GŁÓWNE PROBLEMY:** [lista głównych problemów lub 'Brak']\n"
                    "- **SUGEROWANE POPRAWKI:** [konkretne sugestie lub 'Brak']\n"
                    "- **BRAKUJĄCE ELEMENTY:** [lista brakujących elementów lub 'Brak']\n"
                    "- **REKOMENDACJE:** [dodatkowe zalecenia dla poprawy diagramu]\n\n"

                    "**5. PROPOZYCJA:**\n"
                    "[przygotuj jak powinien wyglądać poprawiony opis tak by można było go wysłać do modelu]\n\n"    
        
                    "Jeśli opis jest w pełni poprawny i kompletny, napisz: '✅ OPIS JEST POPRAWNY I KOMPLETNY DLA DIAGRAMU {diagram_type}'"
    ),
                "allowed_diagram_types": "all",
                "type": "Validation"
    }
}

c4_component_requirements = (
    "- Czy używa prawidłowych includes dla poziomu komponentów?\n"
    "- Czy wszystkie komponenty należą do tego samego kontenera/systemu?\n"
    "- Czy każdy komponent ma jasno określoną odpowiedzialność?\n"
    "- Czy relacje opisują konkretne typy komunikacji?\n"
    "- Czy diagram nie miesza poziomów abstrakcji C4?\n"
    "- Czy nazwy komponentów są funkcjonalne (nie techniczne)?\n"
)

usecase_requirements = (
    "- Czy wszystkie aktorzy (główni i pomocniczy) są zidentyfikowani?\n"
    "- Czy przypadki użycia są atomowe i skupione na jednym celu?\n"
    "- Czy relacje extend i include są poprawnie opisane?\n"
    "- Czy warunki wstępne i końcowe są określone?\n"
    "- Czy scenariusze alternatywne są uwzględnione?\n"
)

sequence_requirements = (
    "- Czy wszystkie obiekty/aktorzy uczestniczący w procesie są zidentyfikowani?\n"
    "- Czy kolejność interakcji jest logiczna i kompletna?\n"
    "- Czy wszystkie komunikaty między obiektami są opisane?\n"
    "- Czy okresy życia obiektów są jasno określone?\n"
    "- Czy uwzględniono wszystkie warunki i pętle?\n"
)

bpmn_requirements = (
    "- Czy określone są wszystkie pule (pools) i ścieżki (lanes)?\n"
    "- Czy zdarzenia początkowe i końcowe są jasno zdefiniowane?\n"
    "- Czy wszystkie bramki (gateways) mają określone warunki?\n"
    "- Czy procesy międzyorganizacyjne są poprawnie opisane?\n"
    "- Czy wszystkie zadania mają przypisanych wykonawców?\n"
)

flowchart_requirements = (
    "- Czy wszystkie punkty decyzyjne mają jasno określone warunki (tak/nie)?\n"
    "- Czy wszystkie ścieżki prowadzą do logicznego zakończenia?\n"
    "- Czy procesy równoległe są jasno oznaczone?\n"
    "- Czy wszystkie pętle i iteracje są opisane z warunkami zakończenia?\n"
)

class_requirements = (
    "- Czy wszystkie klasy mają jasno określone atrybuty i metody?\n"
    "- Czy relacje między klasami (dziedziczenie, asocjacje) są poprawnie zdefiniowane?\n"
    "- Czy diagram zawiera wszystkie istotne klasy i interfejsy?\n"
    "- Czy nazwy klas są spójne i jednoznaczne?\n"
)

component_requirements = (
    "- Czy wszystkie komponenty są jasno zdefiniowane i mają unikalne nazwy?\n"
    "- Czy relacje między komponentami są poprawnie opisane?\n"
    "- Czy diagram zawiera wszystkie istotne komponenty systemu?\n"
    "- Czy użyto spójnej notacji dla komponentów i interfejsów?\n"
)

activity_requirements = (
    "- Czy wszystkie działania (activities) są jasno zdefiniowane?\n"
    "- Czy diagram zawiera wszystkie istotne działania i decyzje?\n"
    "- Czy ścieżki alternatywne i warunki zakończenia są poprawnie opisane?\n"
    "- Czy diagram jest czytelny i logicznie uporządkowany?\n"
)

deployment_requirements = (
    "- Czy wszystkie elementy wdrożenia (np. serwery, bazy danych) są jasno zdefiniowane?\n"
    "- Czy relacje między elementami wdrożenia są poprawnie opisane?\n"
    "- Czy diagram zawiera wszystkie istotne elementy infrastruktury?\n"
    "- Czy użyto spójnej notacji dla elementów wdrożenia i artefaktów?\n"
)

object_requirements = (
    "- Czy wszystkie obiekty są jasno zdefiniowane i mają unikalne nazwy?\n"
    "- Czy relacje między obiektami są poprawnie opisane?\n"
    "- Czy diagram zawiera wszystkie istotne obiekty i ich atrybuty?\n"
    "- Czy użyto spójnej notacji dla obiektów i ich relacji?\n"
)

state_requirements = (
    "- Czy wszystkie stany są jasno zdefiniowane?\n"
    "- Czy przejścia między stanami są poprawnie opisane?\n"
    "- Czy diagram zawiera wszystkie istotne stany i ich relacje?\n"
    "- Czy użyto spójnej notacji dla stanów i przejść?\n"
)

def get_diagram_specific_requirements(diagram_type):
    requirements_map = {
        "flowchart": flowchart_requirements,
        "bpmn": bpmn_requirements,
        "sequence": sequence_requirements,
        "usecase": usecase_requirements,
        "class": class_requirements,
        "component": component_requirements,
        "activity": activity_requirements,
        "deployment": deployment_requirements,
        "object": object_requirements,  
        "state": state_requirements,
        # dodaj więcej typów według potrzeb
    }