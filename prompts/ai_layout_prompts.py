"""
AI Layout Manager - Prompty do inteligentnego pozycjonowania elementów diagramów.
Używane przez AILayoutManager dla różnych typów diagramów UML i nie tylko.
"""

ai_layout_prompts = {
    
    # ============================================================================
    # AI LAYOUT - PROMPTY KROKOWE (UNIWERSALNE)
    # ============================================================================
    
    "AI_Step_1_Semantic_Analysis": {
        "template": (
            "**ANALIZA SEMANTYCZNA ELEMENTÓW DIAGRAMU {diagram_type}**\n\n"
            
            "**GRUPA ELEMENTÓW DO ANALIZY:**\n"
            "{elements_data}\n\n"
            
            "**ZADANIE:** Przeanalizuj każdy element i sklasyfikuj go semantycznie według typu diagramu\n\n"
            
            "**KLASYFIKACJA SEMANTYCZNA:**\n"
            "- `process_start` - elementy inicjujące (start, rozpoczęcie)\n"
            "- `process_end` - elementy kończące (end, stop, zakończenie)\n"
            "- `business_decision` - węzły decyzyjne wymagające wyboru\n"
            "- `success_activity` - działania sukcesu (aktywacja, zatwierdzenie)\n"
            "- `error_handling` - obsługa błędów (blokada, odrzucenie)\n"
            "- `critical_business` - kluczowe procesy (weryfikacja, autoryzacja)\n"
            "- `retry_alternative` - alternatywne ścieżki i ponowne próby\n"
            "- `standard_activity` - standardowe działania biznesowe\n"
            "- `data_node` - węzły danych (bazy, storage, dokumenty)\n"
            "- `control_node` - węzły kontrolne (synchronizacja, rozgałęzienia)\n\n"
            
            "**WAŻNOŚĆ BIZNESOWA (1-10):**\n"
            "- 10: Krytyczne elementy kontrolne (start/end)\n"
            "- 9: Kluczowe decyzje biznesowe\n"
            "- 8: Elementy sukcesu i weryfikacji\n"
            "- 7: Obsługa błędów\n"
            "- 6: Alternatywne ścieżki\n"
            "- 5: Standardowe aktywności\n\n"
            
            "**POZYCJA W PRZEPŁYWIE:**\n"
            "- `control_start` - punkt początkowy\n"
            "- `control_end` - punkt końcowy\n"
            "- `main` - główna ścieżka procesu\n"
            "- `success` - ścieżki sukcesu\n"
            "- `error` - ścieżki błędów\n"
            "- `alternative` - ścieżki alternatywne\n"
            "- `data` - elementy danych\n\n"
            
            "**WYMAGANY FORMAT JSON:**\n"
            "```json\n"
            "{{\n"
            "  \"elements\": [\n"
            "    {{\n"
            "      \"element_id\": \"id_skrócone\",\n"
            "      \"semantic_type\": \"success_activity\",\n"
            "      \"importance\": 8,\n"
            "      \"business_category\": \"success_path\",\n"
            "      \"reasoning\": \"Element zawiera 'aktywacja' - wskazuje na sukces\"\n"
            "    }}\n"
            "  ]\n"
            "}}\n"
            "```\n\n"
            
            "**UWAGI:**\n"
            "- Analizuj polskie słowa kluczowe w tekstach\n"
            "- Uwzględniaj kontekst biznesowy, nie tylko techniczny\n"
            "- Dodaj krótkie uzasadnienie dla każdej klasyfikacji"
        ),
        "allowed_diagram_types": ["activity", "sequence", "usecase", "component", "class"],
        "type": "AI_Step",
        "parameters": ["diagram_type", "elements_data"]
    },
    
    "AI_Step_2_Flow_Patterns": {
        "template": (
            "**WYKRYWANIE WZORCÓW PRZEPŁYWU W DIAGRAMIE {diagram_type}**\n\n"
            
            "**POŁĄCZENIA DO ANALIZY:**\n"
            "{connections_data}\n\n"
            
            "**WYNIKI ANALIZY SEMANTYCZNEJ:**\n"
            "{semantic_results}\n\n"
            
            "**ZADANIE:** Znajdź wzorce przepływu specyficzne dla diagramu {diagram_type}\n\n"
            
            "**WZORCE DO WYKRYCIA:**\n"
            "1. **Główna sekwencja** - ścieżka od start do end\n"
            "2. **Gałęzie sukcesu** - decyzje 'tak' → elementy pozytywne\n"
            "3. **Gałęzie błędów** - decyzje 'nie' → elementy negatywne\n"
            "4. **Punkty decyzyjne** - węzły z wieloma wyjściami\n"
            "5. **Alternatywne ścieżki** - pętle i obejścia\n"
            "6. **Przepływy równoległe** - wykonywanie współbieżne\n"
            "7. **Punkty synchronizacji** - scalanie przepływów\n\n"
            
            "**WYMAGANY FORMAT JSON:**\n"
            "```json\n"
            "{{\n"
            "  \"main_sequence\": [\"id1\", \"id2\", \"id3\"],\n"
            "  \"success_branches\": [\n"
            "    {{\n"
            "      \"decision\": \"id_dec\",\n"
            "      \"condition\": \"tak\",\n"
            "      \"targets\": [\"id_success1\"]\n"
            "    }}\n"
            "  ],\n"
            "  \"error_branches\": [\n"
            "    {{\n"
            "      \"decision\": \"id_dec\",\n"
            "      \"condition\": \"nie\",\n"
            "      \"targets\": [\"id_error1\"]\n"
            "    }}\n"
            "  ],\n"
            "  \"parallel_flows\": [\n"
            "    {{\n"
            "      \"fork_point\": \"id_fork\",\n"
            "      \"branches\": [\"id_branch1\", \"id_branch2\"],\n"
            "      \"join_point\": \"id_join\"\n"
            "    }}\n"
            "  ],\n"
            "  \"decision_points\": [\"id_dec1\", \"id_dec2\"]\n"
            "}}\n"
            "```\n\n"
            
            "**UWAGI:**\n"
            "- Szukaj etykiet 'tak'/'nie' w połączeniach\n"
            "- Uwzględniaj typy semantyczne elementów\n"
            "- Identyfikuj logiczne grupy powiązanych elementów\n"
            "- Uwzględnij specyfikę diagramu {diagram_type}"
        ),
        "allowed_diagram_types": ["activity", "sequence", "usecase", "component"],
        "type": "AI_Step",
        "parameters": ["diagram_type", "connections_data", "semantic_results"]
    },
    
    "AI_Step_3_Zone_Assignment": {
        "template": (
            "**PRZYPISANIE ELEMENTÓW DO STREF LAYOUTU - {diagram_type}**\n\n"
            
            "**ELEMENTY Z ANALIZĄ SEMANTYCZNĄ:**\n"
            "{semantic_results}\n\n"
            
            "**WZORCE PRZEPŁYWU:**\n"
            "{flow_patterns}\n\n"
            
            "**ZADANIE:** Przypisz każdy element do odpowiedniej strefy układu dla {diagram_type}\n\n"
            
            "**DOSTĘPNE STREFY WEDŁUG TYPU DIAGRAMU:**\n"
            "{zone_definitions}\n\n"
            
            "**ZASADY PRZYPISANIA:**\n"
            "- `process_start` → `control_start`\n"
            "- `process_end` → `control_end`\n"
            "- `business_decision` → `decision_zone`\n"
            "- `success_activity` → `success_zone`\n"
            "- `error_handling` → `error_zone`\n"
            "- `data_node` → `data_zone`\n"
            "- elementy z `main_sequence` → `main_flow` (jeśli nie mają specjalnej strefy)\n\n"
            
            "**WYMAGANY FORMAT JSON:**\n"
            "```json\n"
            "{{\n"
            "  \"zone_assignments\": {{\n"
            "    \"elem_id\": \"main_flow\",\n"
            "    \"elem_id2\": \"success_zone\"\n"
            "  }},\n"
            "  \"zone_stats\": {{\n"
            "    \"main_flow\": 15,\n"
            "    \"success_zone\": 5,\n"
            "    \"error_zone\": 2,\n"
            "    \"decision_zone\": 3\n"
            "  }}\n"
            "}}\n"
            "```\n\n"
            
            "**UWAGI:**\n"
            "- Groupuj logicznie powiązane elementy\n"
            "- Preferuj strefy według ważności biznesowej\n"
            "- Uwzględnij konwencje diagramu {diagram_type}"
        ),
        "allowed_diagram_types": ["activity", "sequence", "usecase", "component", "class"],
        "type": "AI_Step", 
        "parameters": ["diagram_type", "semantic_results", "flow_patterns", "zone_definitions"]
    },
    
    "AI_Step_4_Position_Calculation": {
        "template": (
            "**OBLICZENIE KONKRETNYCH POZYCJI XY - {diagram_type}**\n\n"
            
            "**PRZYPISANIA STREF:**\n"
            "{zone_assignments}\n\n"
            
            "**ZADANIE:** Oblicz precyzyjne współrzędne dla każdego elementu\n\n"
            
            "**PARAMETRY CANVAS:**\n"
            "- Szerokość: {canvas_width}px\n"
            "- Wysokość: {canvas_height}px\n"
            "- Margines: {margin}px z każdej strony\n\n"
            
            "**WSPÓŁRZĘDNE STREF:**\n"
            "{zone_coordinates}\n\n"
            
            "**ODSTĘPY:**\n"
            "- Poziomo: {h_spacing}px między elementami\n"
            "- Pionowo: {v_spacing}px między elementami\n\n"
            
            "**WYMAGANY FORMAT JSON:**\n"
            "```json\n"
            "{{\n"
            "  \"positions\": {{\n"
            "    \"elem_id\": {{\n"
            "      \"x\": 900,\n"
            "      \"y\": 100,\n"
            "      \"width\": 140,\n"
            "      \"height\": 60\n"
            "    }},\n"
            "    \"elem_id2\": {{\n"
            "      \"x\": 750,\n"
            "      \"y\": 250,\n"
            "      \"width\": 180,\n"
            "      \"height\": 70\n"
            "    }}\n"
            "  }}\n"
            "}}\n"
            "```\n\n"
            
            "**UWAGI:**\n"
            "- Zachowaj logiczną kolejność w strefach\n"
            "- Dostosuj wymiary do długości tekstu\n"
            "- Unikaj nakładających się elementów\n"
            "- Uwzględnij konwencje układu dla {diagram_type}"
        ),
        "allowed_diagram_types": ["activity", "sequence", "usecase", "component", "class"],
        "type": "AI_Step",
        "parameters": ["diagram_type", "zone_assignments", "canvas_width", "canvas_height", "margin", "zone_coordinates", "h_spacing", "v_spacing"]
    },
    
    "AI_Step_5_Optimization": {
        "template": (
            "**FINALNA OPTYMALIZACJA UKŁADU - {diagram_type}**\n\n"
            
            "**AKTUALNE POZYCJE:**\n"
            "{element_positions}\n\n"
            
            "**WYKRYTE KONFLIKTY:**\n"
            "{conflicts}\n\n"
            
            "**ZADANIE:** Popraw pozycje elementów w konflikcie uwzględniając specyfikę {diagram_type}\n\n"
            
            "**ZASADY OPTYMALIZACJI:**\n"
            "- Minimalna odległość: {min_distance}px między elementami\n"
            "- Zachowaj logikę stref\n"
            "- Minimalizuj przesunięcia\n"
            "- Preferuj przesunięcia zgodne z konwencjami {diagram_type}\n\n"
            
            "**WYMAGANY FORMAT JSON:**\n"
            "```json\n"
            "{{\n"
            "  \"corrections\": {{\n"
            "    \"elem_id\": {{\n"
            "      \"x\": 950,\n"
            "      \"y\": 150,\n"
            "      \"reason\": \"przesunięte prawo o 100px - konflikt z elem_id2\"\n"
            "    }}\n"
            "  }}\n"
            "}}\n"
            "```\n\n"
            
            "**UWAGI:**\n"
            "- Poprawiaj tylko elementy w rzeczywistych konfliktach\n"
            "- Podaj uzasadnienie dla każdej korekty\n"
            "- Zachowaj czytelność całego układu\n"
            "- Uwzględnij best practices dla {diagram_type}"
        ),
        "allowed_diagram_types": ["activity", "sequence", "usecase", "component", "class"],
        "type": "AI_Step",
        "parameters": ["diagram_type", "element_positions", "conflicts", "min_distance"]
    },
    
    # ============================================================================
    # AI LAYOUT - DEFINICJE STREF DLA RÓŻNYCH TYPÓW DIAGRAMÓW
    # ============================================================================
    
    "Zone_Definitions_Activity": {
        "zones": {
            "control_start": {"x_range": [800, 1000], "y_range": [50, 120], "description": "elementy startowe (góra-środek)"},
            "control_end": {"x_range": [800, 1000], "y_range": [1300, 1500], "description": "elementy końcowe (dół-środek)"},
            "main_flow": {"x_range": [700, 1100], "y_range": [200, 1200], "description": "główny przepływ (środek pionowy)"},
            "decision_zone": {"x_range": [650, 1150], "y_range": [150, 800], "description": "decyzje (środek-góra)"},
            "success_zone": {"x_range": [1200, 1600], "y_range": [200, 600], "description": "sukcesy (prawo-góra)"},
            "error_zone": {"x_range": [1200, 1600], "y_range": [700, 1200], "description": "błędy (prawo-dół)"},
            "alternative_flow": {"x_range": [200, 600], "y_range": [300, 1000], "description": "alternatywy (lewa strona)"}
        }
    },
    
    "Zone_Definitions_Sequence": {
        "zones": {
            "actors_zone": {"x_range": [100, 300], "y_range": [100, 1400], "description": "aktorzy (lewa strona)"},
            "systems_zone": {"x_range": [400, 1600], "y_range": [100, 1400], "description": "systemy/obiekty (środek-prawo)"},
            "interaction_zone": {"x_range": [350, 1650], "y_range": [200, 1300], "description": "interakcje (między obiektami)"},
            "note_zone": {"x_range": [50, 1700], "y_range": [150, 1350], "description": "notatki (wszędzie)"}
        }
    },
    
    "Zone_Definitions_Component": {
        "zones": {
            "ui_layer": {"x_range": [200, 1600], "y_range": [100, 300], "description": "warstwa prezentacji (góra)"},
            "business_layer": {"x_range": [200, 1600], "y_range": [350, 700], "description": "logika biznesowa (środek)"},
            "data_layer": {"x_range": [200, 1600], "y_range": [750, 1100], "description": "dostęp do danych (dół)"},
            "external_systems": {"x_range": [50, 150], "y_range": [100, 1100], "description": "systemy zewnętrzne (lewa)"},
            "infrastructure": {"x_range": [1650, 1750], "y_range": [100, 1100], "description": "infrastruktura (prawa)"}
        }
    },
    
    "Zone_Definitions_UseCase": {
        "zones": {
            "actors_left": {"x_range": [50, 200], "y_range": [100, 1400], "description": "aktorzy główni (lewa)"},
            "actors_right": {"x_range": [1600, 1750], "y_range": [100, 1400], "description": "systemy zewnętrzne (prawa)"},
            "main_cases": {"x_range": [300, 1500], "y_range": [200, 600], "description": "główne przypadki (środek-góra)"},
            "supporting_cases": {"x_range": [300, 1500], "y_range": [650, 1000], "description": "funkcje wspierające (środek-dół)"},
            "admin_cases": {"x_range": [300, 1500], "y_range": [1050, 1300], "description": "administracja (dół)"}
        }
    },
    
    "Zone_Definitions_Class": {
        "zones": {
            "entities": {"x_range": [200, 600], "y_range": [200, 1200], "description": "klasy główne/encje (lewa)"},
            "services": {"x_range": [700, 1100], "y_range": [200, 1200], "description": "serwisy/kontrolery (środek)"},
            "interfaces": {"x_range": [1200, 1600], "y_range": [100, 500], "description": "interfejsy (prawo-góra)"},
            "utilities": {"x_range": [1200, 1600], "y_range": [600, 1000], "description": "narzędzia/helpers (prawo-dół)"},
            "value_objects": {"x_range": [200, 1600], "y_range": [1300, 1500], "description": "obiekty wartości (dół)"}
        }
    },
    
    # ============================================================================
    # AI LAYOUT - MINI PROMPTY (dla pojedynczych elementów/małych grup)
    # ============================================================================
    
    "AI_Mini_Element_Classification": {
        "template": (
            "**SZYBKA KLASYFIKACJA ELEMENTU {diagram_type}**\n\n"
            
            "**ELEMENT:**\n"
            "- ID: {element_id}\n"
            "- Typ: {element_type}\n"
            "- Tekst: \"{element_text}\"\n"
            "- Nazwa: \"{element_name}\"\n\n"
            
            "**ZADANIE:** Sklasyfikuj semantycznie ten jeden element dla diagramu {diagram_type}\n\n"
            
            "**OPCJE KLASYFIKACJI:**\n"
            "1. `process_start` - start, rozpoczęcie\n"
            "2. `process_end` - end, stop, zakończenie\n"
            "3. `business_decision` - decyzje, wybory\n"
            "4. `success_activity` - aktywacja, zatwierdzenie, sukces\n"
            "5. `error_handling` - blokada, odrzucenie, błędy\n"
            "6. `critical_business` - weryfikacja, autoryzacja\n"
            "7. `standard_activity` - standardowe działania\n"
            "8. `data_node` - bazy danych, storage, dokumenty\n"
            "9. `control_node` - synchronizacja, rozgałęzienia\n\n"
            
            "**FORMAT ODPOWIEDZI:**\n"
            "```json\n"
            "{{\n"
            "  \"semantic_type\": \"success_activity\",\n"
            "  \"importance\": 8,\n"
            "  \"business_category\": \"success_path\",\n"
            "  \"reasoning\": \"Zawiera słowo 'aktywacja' - wskazuje na pozytywny rezultat\"\n"
            "}}\n"
            "```"
        ),
        "allowed_diagram_types": ["activity", "sequence", "usecase", "component", "class"],
        "type": "AI_Mini",
        "parameters": ["diagram_type", "element_id", "element_type", "element_text", "element_name"]
    },
    
    "AI_Mini_Zone_Positioning": {
        "template": (
            "**SZYBKIE OBLICZENIE POZYCJI W STREFIE - {diagram_type}**\n\n"
            
            "**STREFA:** {zone_name}\n"
            "**ELEMENTY DO POZYCJONOWANIA:** {element_count}\n"
            "**LISTA ELEMENTÓW:** {elements_list}\n\n"
            
            "**PARAMETRY STREFY:**\n"
            "- Obszar X: {zone_x_range}\n"
            "- Obszar Y: {zone_y_range}\n"
            "- Odstęp poziomy: {h_spacing}px\n"
            "- Odstęp pionowy: {v_spacing}px\n\n"
            
            "**ZADANIE:** Rozmieść elementy równomiernie w strefie zgodnie z konwencjami {diagram_type}\n\n"
            
            "**FORMAT JSON:**\n"
            "```json\n"
            "{{\n"
            "  \"positions\": {{\n"
            "    \"elem1\": {{\"x\": 800, \"y\": 200}},\n"
            "    \"elem2\": {{\"x\": 950, \"y\": 200}}\n"
            "  }}\n"
            "}}\n"
            "```"
        ),
        "allowed_diagram_types": ["activity", "sequence", "usecase", "component", "class"],
        "type": "AI_Mini",
        "parameters": ["diagram_type", "zone_name", "element_count", "elements_list", "zone_x_range", "zone_y_range", "h_spacing", "v_spacing"]
    },

    # ============================================================================
    # AI LAYOUT - KOMPAKTOWE PROMPTY (dla batch processing)
    # ============================================================================
    
    "AI_Compact_Position_Batch": {
        "template": (
            "**POZYCJONOWANIE ELEMENTÓW DIAGRAMU {diagram_type} - GRUPA {batch_number}**\n\n"
            
            "**ELEMENTY DO POZYCJONOWANIA:**\n"
            "{elements_assignments}\n\n"
            
            "**STREFY:**\n"
            "{zones_compact}\n\n"
            
            "**CANVAS:** {canvas_width}x{canvas_height}px\n\n"
            
            "**ZADANIE:** Oblicz pozycje XY dla każdego elementu w odpowiedniej strefie.\n\n"
            
            "**ODPOWIEDŹ (TYLKO JSON):**\n"
            "```json\n"
            "{{\n"
            "  \"positions\": {{\n"
            "    \"short_id\": {{\"x\": 800, \"y\": 150, \"width\": 140, \"height\": 60}}\n"
            "  }}\n"
            "}}\n"
            "```"
        ),
        "allowed_diagram_types": ["activity", "sequence", "usecase", "component", "class"],
        "type": "AI_Compact",
        "parameters": ["diagram_type", "batch_number", "elements_assignments", "zones_compact", "canvas_width", "canvas_height"]
    },
    
    "AI_Compact_Zone_Summary": {
        "template": (
            "**STREFY DLA {diagram_type}:**\n"
            "{zone_list}\n\n"
            
            "**ELEMENTY ({element_count}):**\n"
            "{elements_summary}"
        ),
        "allowed_diagram_types": ["activity", "sequence", "usecase", "component", "class"],
        "type": "AI_Compact",
        "parameters": ["diagram_type", "zone_list", "element_count", "elements_summary"]
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_zone_definitions(diagram_type):
    """Pobiera definicje stref dla określonego typu diagramu"""
    zone_key = f"Zone_Definitions_{diagram_type.capitalize()}"
    return ai_layout_prompts.get(zone_key, ai_layout_prompts["Zone_Definitions_Activity"])

def get_ai_prompt(prompt_name, **kwargs):
    """Pobiera i formatuje prompt AI z parametrami"""
    if prompt_name not in ai_layout_prompts:
        raise ValueError(f"Prompt '{prompt_name}' not found in ai_layout_prompts")
    
    template = ai_layout_prompts[prompt_name]["template"]
    return template.format(**kwargs)

def is_prompt_allowed_for_diagram(prompt_name, diagram_type):
    """Sprawdza czy prompt jest dozwolony dla danego typu diagramu"""
    if prompt_name not in ai_layout_prompts:
        return False
    
    allowed_types = ai_layout_prompts[prompt_name].get("allowed_diagram_types", [])
    return diagram_type in allowed_types or "all" in allowed_types

def get_compact_position_prompt(diagram_type, batch_assignments, zone_coordinates, batch_number, canvas_width, canvas_height, used_positions=None):
    """Tworzy kompaktowy prompt dla grupy pozycji - ULEPSZONA WERSJA"""
    
    # ULTRA-SKRÓCONY FORMAT ELEMENTÓW (z lepszym ID mapping)
    elements_list = []
    for elem_id, zone in batch_assignments.items():
        # Użyj ostatnich 8 znaków jako short_id (bardziej unique)
        short_id = elem_id[-8:] if len(elem_id) > 8 else elem_id
        elements_list.append(f'"{short_id}": "{zone}"')
    
    elements_assignments = ", ".join(elements_list)
    
    # SKRÓCONE STREFY (tylko nazwa i zakresy)
    zones_compact = []
    for zone, coords in zone_coordinates.items():
        zones_compact.append(f'"{zone}": X{coords["x_range"]}, Y{coords["y_range"]}')
    
    zones_compact_str = ", ".join(zones_compact)
    

    # Używamy istniejącego promptu AI_Compact_Position_Batch
    return get_ai_prompt(
        "AI_Compact_Position_Batch",
        diagram_type=diagram_type.upper(),
        batch_number=batch_number,
        elements_assignments=elements_assignments,
        zones_compact=zones_compact_str,
        canvas_width=canvas_width,
        canvas_height=canvas_height
    )
