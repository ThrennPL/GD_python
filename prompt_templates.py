

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
                    "Na podstawie opisu procesu biznesowego: {process_description}\n\n"
        
                    "**KROK 1: ANALIZA PROCESU BIZNESOWEGO**\n"
                    "Przeanalizuj opisany proces i zidentyfikuj:\n"
                    "- Kto uczestniczy w procesie (aktorzy, role)?\n"
                    "- Jakie dane są przetwarzane, przechowywane, przekazywane?\n"
                    "- Jakie decyzje są podejmowane i na podstawie czego?\n"
                    "- Jakie systemy zewnętrzne są wymagane?\n"
                    "- Jakie powiadomienia/komunikacja jest potrzebna?\n"
                    "- Jakie dokumenty/raporty są generowane?\n\n"

                    "**KROK 2: IDENTYFIKACJA KOMPONENTÓW SYSTEMU**\n"
                    "Na podstawie analizy określ jakie komponenty informatyczne są potrzebne:\n\n"
        
                    "**A) WARSTWA INTERFEJSU UŻYTKOWNIKA:**\n"
                    "- Czy potrzebna jest aplikacja webowa?\n"
                    "- Czy potrzebne jest API dla innych systemów?\n"
                    "- Czy potrzebny jest panel administracyjny?\n"
                    "- Czy potrzebne są mobilne interfejsy?\n\n"
        
                    "**B) WARSTWA LOGIKI BIZNESOWEJ:**\n"
                    "- Jakie serwisy biznesowe obsługują główne funkcje procesu?\n"
                    "- Czy potrzebne są komponenty do walidacji danych?\n"
                    "- Czy potrzebne są komponenty do obliczeń/algorytmów?\n"
                    "- Czy potrzebne są komponenty do orkiestracji przepływu?\n\n"
        
                    "**C) WARSTWA DOSTĘPU DO DANYCH:**\n"
                    "- Jakie bazy danych są potrzebne (transakcyjne, analityczne)?\n"
                    "- Czy potrzebne są repozytoria/DAO?\n"
                    "- Czy potrzebna jest cache/pamięć podręczna?\n"
                    "- Czy potrzebne są komponenty ETL?\n\n"
        
                    "**D) KOMPONENTY INTEGRACYJNE:**\n"
                    "- Z jakimi systemami zewnętrznymi trzeba się integrować?\n"
                    "- Czy potrzebne są kolejki/brokery komunikatów?\n"
                    "- Czy potrzebne są komponenty do synchronizacji danych?\n"
                    "- Czy potrzebne są adaptery/connectors?\n\n"
        
                    "**E) KOMPONENTY POMOCNICZE:**\n"
                    "- Czy potrzebne są komponenty do powiadomień (email, SMS)?\n"
                    "- Czy potrzebne są komponenty do generowania raportów?\n"
                    "- Czy potrzebne są komponenty do logowania/audytu?\n"
                    "- Czy potrzebne są komponenty do zarządzania plikami?\n\n"
        
                    "**KROK 3: GENEROWANIE DIAGRAMU PlantUML**\n"
                    "Wygeneruj kompletny kod PlantUML w podstawowej notacji z następującymi wymaganiami:\n\n"
        
                    "**STRUKTURA TECHNICZNA:**\n"
                    "1. **Rozpocznij:** `@startuml`\n"
                    "2. **Tytuł:** `title [Nazwa Procesu] - Architektura Systemu`\n"
                    "3. **Tema:** `!theme blueprint` (opcjonalnie)\n"
                    "4. **Definicje wszystkich elementów przed relacjami**\n"
                    "5. **Zakończ:** `@enduml`\n\n"
        
                    "**ELEMENTY DO UŻYCIA:**\n"
                    "- `actor \"Nazwa\" as alias` - użytkownicy/role\n"
                    "- `component \"Nazwa\" <<stereotype>> as alias` - komponenty biznesowe\n"
                    "- `database \"Nazwa\" as alias` - bazy danych\n"
                    "- `queue \"Nazwa\" as alias` - kolejki/brokery\n"
                    "- `file \"Nazwa\" as alias` - storage/pliki\n"
                    "- `cloud \"Nazwa\" as alias` - systemy zewnętrzne\n"
                    "- `interface \"Nazwa\" as alias` - interfejsy\n\n"
        
                    "**GRUPOWANIE:**\n"
                    "- `package \"UI Layer\" {{ }}` - warstwa interfejsu\n"
                    "- `package \"Business Layer\" {{ }}` - logika biznesowa\n"
                    "- `package \"Data Layer\" {{ }}` - dostęp do danych\n"
                    "- `package \"Integration Layer\" {{ }}` - integracje\n"
                    "- `frame \"[Nazwa Systemu]\" {{ }}` - granice systemu\n\n"
        
                    "**STEREOTYPY:**\n"
                    "- `<<controller>>` - kontrolery Web/API\n"
                    "- `<<service>>` - serwisy biznesowe\n"
                    "- `<<repository>>` - dostęp do danych\n"
                    "- `<<facade>>` - fasady integracyjne\n"
                    "- `<<utility>>` - komponenty pomocnicze\n"
                    "- `<<gateway>>` - bramy API\n\n"
        
                    "**RELACJE Z OPISAMI:**\n"
                    "- `-->` z etykietami typu: \"HTTP API\", \"SQL Query\", \"Message\", \"File Access\"\n"
                    "- Zawsze opisuj protokół/technologię komunikacji\n"
                    "- Grupuj podobne relacje dla czytelności\n\n"
        
                    "**PRZYKŁAD STRUKTURY:**\n"
                    "```plantuml\n"
                    "@startuml\n"
                    "!theme blueprint\n"
                    "title [Nazwa Procesu] - Architektura Systemu\n\n"
        
                    "' Aktorzy z procesu biznesowego\n"
                    "actor \"[Rola1]\" as actor1\n"
                    "actor \"[Rola2]\" as actor2\n\n"
        
                    "' Systemy zewnętrzne zidentyfikowane w procesie\n"
                    "cloud \"[System Zewnętrzny]\" as ext_system\n\n"
        
                    "frame \"System [Nazwa Procesu]\" {{\n"
                    "    package \"UI Layer\" {{\n"
                    "        component \"[Process] Web App\" <<controller>> as web_app\n"
                    "        component \"[Process] API\" <<gateway>> as api\n"
                    "    }}\n\n"
        
                    "    package \"Business Layer\" {{\n"
                    "        component \"[Process] Service\" <<service>> as main_service\n"
                    "        component \"[Function] Service\" <<service>> as func_service\n"
                    "        interface \"I[Process]Service\" as iservice\n"
                    "    }}\n\n"
        
                    "    package \"Data Layer\" {{\n"
                    "        component \"[Entity] Repository\" <<repository>> as repo\n"
                    "        database \"[Process] Database\" as db\n"
                    "    }}\n\n"
        
                    "    package \"Integration Layer\" {{\n"
                    "        component \"[External] Adapter\" <<facade>> as adapter\n"
                    "        queue \"[Process] Events\" as queue\n"
                    "    }}\n"
                    "}}\n\n"
        
                    "' Relacje wyprowadzone z przepływu procesu\n"
                    "actor1 --> web_app : \"Inicjuje proces\"\n"
                    "web_app --> iservice : \"Wywołuje logikę\"\n"
                    "main_service ..|> iservice : \"implements\"\n"
                    "main_service --> repo : \"Pobiera/zapisuje dane\"\n"
                    "repo --> db : \"SQL\"\n"
                    "main_service --> adapter : \"Integracja zewnętrzna\"\n"
                    "adapter --> ext_system : \"API call\"\n"
                    "@enduml\n"
                    "```\n\n"
        
                    "**ZASADY NAZEWNICTWA:**\n"
                    "- Nazwy komponentów powinny odzwierciedlać funkcje z procesu biznesowego\n"
                    "- Używaj nazw funkcjonalnych, nie technicznych (\"Order Service\" zamiast \"Service1\")\n"
                    "- Aliasy krótkie, bez spacji (order_service, payment_api)\n"
                    "- Konsekwentny język (polski lub angielski)\n\n"
        
                    "**KOŃCOWY REZULTAT:**\n"
                    "Dostarcz kompletny, działający kod PlantUML który:\n"
                    "1. Odzwierciedla wszystkie aspekty procesu biznesowego w formie komponentów IT\n"
                    "2. Pokazuje logiczną architekturę systemu potrzebnego do obsługi procesu\n"
                    "3. Zawiera wszystkie niezbędne integracje i przepływy danych\n"
                    "4. Jest gotowy do użycia bez modyfikacji\n"
                    "5. Zawiera komentarze wyjaśniające mapowanie proces→komponenty"
                ),
                "allowed_diagram_types": ["component"],
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