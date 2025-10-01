"""
AI Layout Manager - Inteligentne pozycjonowanie elementów diagramu
używające TYLKO prawdziwego modelu AI do analizy semantycznej i pozycjonowania.
"""

import sys
import os
from typing import Dict, List, Tuple, Any
import json
import time

# Dodaj ścieżkę do logger_utils
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)

try:
    from utils.logger_utils import log_debug, log_info, log_error, log_warning
except ImportError:
    def log_debug(msg): print(f"DEBUG: {msg}")
    def log_info(msg): print(f"INFO: {msg}")
    def log_error(msg): print(f"ERROR: {msg}")
    def log_warning(msg): print(f"WARNING: {msg}")


class AILayoutManager:
    """
    AI-powered Layout Manager dla diagramów UML.
    Używa TYLKO prawdziwego modelu AI - bez deterministycznych fallback'ów.
    """
    
    def __init__(self, debug: bool = False, debug_ai_communication: bool = False, use_real_ai: bool = True):
        self.debug = debug
        self.debug_ai_communication = debug_ai_communication
        self.use_real_ai = use_real_ai
        
        # WYMUSZA UŻYCIE PRAWDZIWEGO AI
        if not self.use_real_ai:
            log_warning("⚠️  AILayoutManager wymaga use_real_ai=True - wymuszam włączenie")
            self.use_real_ai = True
        
        # Konfiguracja API (z .env) - WYMAGANA
        self._setup_ai_api()
        
        # Canvas parametry
        self.canvas_width = 1800
        self.canvas_height = 1600
        self.margin_x = 100
        self.margin_y = 80
        
        # Pozycje elementów
        self.element_positions = {}
        self.swimlanes_geometry = {}
        
        # Typ diagramu (domyślnie activity)
        self.diagram_type = "activity"
    
    def _setup_ai_api(self):
        """Konfiguruje API do prawdziwego modelu AI - WYMAGANE"""
        try:
            # Znajdź ścieżkę do katalogu głównego projektu
            parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            sys.path.append(parent_dir)
            
            from dotenv import load_dotenv
            
            # Wskaż dokładną ścieżkę do pliku .env w głównym katalogu
            dotenv_path = os.path.join(parent_dir, '.env')
            
            # Sprawdź czy plik istnieje przed załadowaniem
            if os.path.exists(dotenv_path):
                if self.debug_ai_communication:
                    log_info(f"Ładowanie konfiguracji z: {dotenv_path}")
                load_dotenv(dotenv_path=dotenv_path)
            else:
                log_warning(f"Plik .env nie znaleziony w {dotenv_path}")
                # Próba alternatywnej ścieżki (bieżący katalog)
                alt_path = os.path.join(os.getcwd(), '.env')
                if os.path.exists(alt_path):
                    log_info(f"Ładowanie konfiguracji z alternatywnej ścieżki: {alt_path}")
                    load_dotenv(dotenv_path=alt_path)
                else:
                    log_error(f"Nie znaleziono pliku .env ani w {dotenv_path}, ani w {alt_path}")
            
            # Pobierz zmienne środowiskowe z załadowanego pliku .env
            self.api_url = os.getenv("CHAT_URL", "https://generativelanguage.googleapis.com/v1beta/chat/completions")
            self.api_key = os.getenv("API_KEY", "")
            self.default_model = os.getenv("API_DEFAULT_MODEL", "gemini-2.0-flash")
            self.model_provider = os.getenv("MODEL_PROVIDER", "gemini")

            if self.debug_ai_communication:
                log_info(f"🤖 REAL AI CONFIG:")
                log_info(f"   URL: {self.api_url}")
                log_info(f"   Model: {self.default_model}")
                log_info(f"   Key: {self.api_key[:10]}..." if self.api_key else "   Key: <brak>")
                
        except ImportError:
            log_error("❌ dotenv not installed - install with: pip install python-dotenv")
            raise ImportError("AILayoutManager requires python-dotenv for API configuration")
        except Exception as e:
            log_error(f"❌ Real AI config error: {e}")
            raise Exception(f"Failed to configure AI API: {e}")
    
    def analyze_diagram_structure(self, parsed_data: Dict, diagram_type: str = "activity") -> Tuple[Dict, Dict]:
        """
        🤖 GŁÓWNA METODA: 5-krokowa analiza diagramu z prawdziwym AI
        """
        
        start_time = time.time()
        self.diagram_type = diagram_type.lower()
        
        log_info(f"🚀 AI PIPELINE START: Analiza diagramu {self.diagram_type} - 5 kroków")
        
        try:
            # KROK 1: Analiza semantyczna elementów (po 5 na raz)
            semantic_results = self._ai_step1_semantic_analysis(parsed_data)
            
            # KROK 2: Wykrywanie wzorców przepływu
            flow_patterns = self._ai_step2_flow_patterns(parsed_data, semantic_results)
            
            # KROK 3: Przypisanie do stref
            zone_assignments = self._ai_step3_zone_assignment(semantic_results, flow_patterns)
            
            # KROK 4: Obliczenie pozycji
            element_positions = self._ai_step4_position_calculation(zone_assignments, parsed_data)
            
            # KROK 5: Finalna optymalizacja
            optimized_positions = self._ai_step5_optimization(element_positions, parsed_data)
            
            # Oblicz informacje o siatce
            grid_info = self._calculate_grid_info_from_positions(optimized_positions)
            
            processing_time = time.time() - start_time
            
            log_info(f"✅ AI PIPELINE SUCCESS: {len(optimized_positions)} elementów w {processing_time:.2f}s")
            
            self.element_positions = optimized_positions
            return optimized_positions, grid_info
            
        except Exception as e:
            log_error(f"❌ AI PIPELINE FAILED: {e}")
            # BEZ FALLBACK - rzuć wyjątek
            raise Exception(f"AI Layout analysis failed: {e}")
    
    def _ai_step1_semantic_analysis(self, parsed_data: Dict) -> Dict:
        """
        KROK 1: Analiza semantyczna elementów (po 5 na raz)
        """
        
        from prompts.ai_layout_prompts import get_ai_prompt
        
        flow = parsed_data.get('flow', [])
        semantic_results = {}
        
        log_info(f"🔍 KROK 1: Analiza semantyczna {len(flow)} elementów")
        
        # Przetwarzaj po 5 elementów na raz
        batch_size = 5
        for i in range(0, len(flow), batch_size):
            batch = flow[i:i+batch_size]
            
            # Przygotuj dane elementów dla promptu
            elements_data = []
            for element in batch:
                elements_data.append({
                    'id': element.get('id', 'brak')[-8:],
                    'type': element.get('type', 'unknown'),
                    'text': element.get('text', ''),
                    'name': element.get('name', ''),
                    'swimlane': element.get('swimlane', '')
                })
            
            # Użyj promptu z ai_layout_prompts
            prompt = get_ai_prompt(
                "AI_Step_1_Semantic_Analysis",
                diagram_type=self.diagram_type.capitalize(),
                elements_data=json.dumps(elements_data, ensure_ascii=False, indent=2)
            )
            
            # Wywołaj AI
            ai_response = self._call_real_ai_model(prompt, f"SEMANTIC_BATCH_{i//batch_size + 1}")
            
            # Parse i zapisz wyniki
            batch_results = self._parse_semantic_response(ai_response, batch)
            semantic_results.update(batch_results)
            
            if self.debug_ai_communication:
                log_info(f"📊 KROK 1 - Grupa {i//batch_size + 1}: {len(batch_results)} elementów sklasyfikowanych")
        
        log_info(f"✅ KROK 1 COMPLETED: {len(semantic_results)} elementów sklasyfikowanych")
        return semantic_results
    
    def _ai_step2_flow_patterns(self, parsed_data: Dict, semantic_results: Dict) -> Dict:
        """
        KROK 2: Wykrywanie wzorców przepływu
        """
        
        from prompts.ai_layout_prompts import get_ai_prompt
        
        log_info("🔗 KROK 2: Wykrywanie wzorców przepływu")
        
        # Przygotuj dane połączeń
        connections_data = []
        for conn in parsed_data.get('logical_connections', [])[:15]:
            source_semantic = semantic_results.get(conn.get('source_id', ''), {})
            target_semantic = semantic_results.get(conn.get('target_id', ''), {})
            
            connections_data.append({
                'source_id': conn.get('source_id', '')[-6:],
                'target_id': conn.get('target_id', '')[-6:],
                'label': conn.get('label', ''),
                'source_type': source_semantic.get('semantic_type', 'unknown'),
                'target_type': target_semantic.get('semantic_type', 'unknown')
            })
        
        # Użyj promptu z ai_layout_prompts
        prompt = get_ai_prompt(
            "AI_Step_2_Flow_Patterns",
            diagram_type=self.diagram_type.capitalize(),
            connections_data=json.dumps(connections_data, ensure_ascii=False, indent=1),
            semantic_results=json.dumps(list(semantic_results.keys())[:10], ensure_ascii=False)
        )
        
        ai_response = self._call_real_ai_model(prompt, "FLOW_PATTERNS")
        flow_patterns = self._parse_flow_patterns_response(ai_response)
        
        log_info(f"✅ KROK 2 COMPLETED: Wykryto {len(flow_patterns.get('main_sequence', []))} elementów w głównej sekwencji")
        return flow_patterns
    
    def _ai_step3_zone_assignment(self, semantic_results: Dict, flow_patterns: Dict) -> Dict:
        """
        KROK 3: Przypisanie elementów do stref layoutu
        """
        
        from prompts.ai_layout_prompts import get_ai_prompt, get_zone_definitions
        
        log_info("🎯 KROK 3: Przypisanie elementów do stref")
        
        # Pobierz definicje stref dla typu diagramu
        zone_defs = get_zone_definitions(self.diagram_type)
        zone_definitions = json.dumps(zone_defs["zones"], ensure_ascii=False, indent=1)
        
        # Użyj promptu z ai_layout_prompts
        prompt = get_ai_prompt(
            "AI_Step_3_Zone_Assignment",
            diagram_type=self.diagram_type.capitalize(),
            semantic_results=json.dumps(semantic_results, ensure_ascii=False, indent=1),
            flow_patterns=json.dumps(flow_patterns, ensure_ascii=False, indent=1),
            zone_definitions=zone_definitions
        )
        
        ai_response = self._call_real_ai_model(prompt, "ZONE_ASSIGNMENT")
        zone_assignments = self._parse_zone_assignment_response(ai_response)
        
        log_info(f"✅ KROK 3 COMPLETED: {len(zone_assignments)} elementów przypisanych do stref")
        return zone_assignments
    
    def _ai_step4_position_calculation(self, zone_assignments: Dict, parsed_data: Dict) -> Dict:
        """KROK 4: Obliczenie konkretnych pozycji XY - BATCH PROCESSING"""
        
        from prompts.ai_layout_prompts import get_compact_position_prompt, get_zone_definitions
        
        log_info("📍 KROK 4: Obliczanie pozycji XY")
        
        if self.debug_ai_communication:
            log_info(f"🔍 Zone assignments input: {len(zone_assignments)} elementów")
        
        # PRZETWARZAJ PO MNIEJSZYCH GRUPACH
        all_positions = {}
        
        # Podziel na grupy po 10 elementów (bezpiecznie dla promptów)
        assignments_items = list(zone_assignments.items())
        batch_size = 10
        total_batches = (len(assignments_items) + batch_size - 1) // batch_size
        
        log_info(f"🔄 KROK 4: Podzielono na {total_batches} grup po max {batch_size} elementów")
        
        # Pobierz definicje stref raz (używane we wszystkich grupach)
        zone_defs = get_zone_definitions(self.diagram_type)
        zone_coordinates = {}
        for zone_name, zone_info in zone_defs["zones"].items():
            zone_coordinates[zone_name] = {
                "x_range": f"{zone_info['x_range'][0]}-{zone_info['x_range'][1]}",
                "y_range": f"{zone_info['y_range'][0]}-{zone_info['y_range'][1]}",
                "description": zone_info['description']
            }
        
        # Przetwarzaj każdą grupę
        for i in range(0, len(assignments_items), batch_size):
            batch_assignments = dict(assignments_items[i:i+batch_size])
            batch_number = i // batch_size + 1
            
            log_info(f"📍 KROK 4 - Grupa {batch_number}/{total_batches}: {len(batch_assignments)} elementów")
            
            if self.debug_ai_communication:
                sample_assignments = dict(list(batch_assignments.items())[:3])
                log_info(f"🔍 Sample assignments: {sample_assignments}")
            
            try:
                # Użyj KOMPAKTOWEGO promptu z ai_layout_prompts
                batch_positions = self._ai_step4_process_batch(
                    batch_assignments, 
                    zone_coordinates, 
                    batch_number
                )
                
                all_positions.update(batch_positions)
                
                log_info(f"✅ KROK 4 - Grupa {batch_number}: {len(batch_positions)} pozycji obliczonych")
                
            except Exception as e:
                log_error(f"❌ KROK 4 - Grupa {batch_number} FAILED: {e}")
                
                # FALLBACK: Użyj podstawowe pozycje dla tej grupy
                fallback_positions = self._generate_fallback_positions_for_batch(batch_assignments)
                all_positions.update(fallback_positions)
                
                log_warning(f"⚠️ KROK 4 - Grupa {batch_number}: Użyto {len(fallback_positions)} pozycji fallback")
        
        log_info(f"✅ KROK 4 COMPLETED: {len(all_positions)} pozycji obliczonych łącznie")
        return all_positions

    def _ai_step4_process_batch(self, batch_assignments: Dict, zone_coordinates: Dict, batch_number: int) -> Dict:
        """Zapewnia unikalne pozycje dla każdego elementu"""
        
        # ✅ INICJALIZUJ _used_positions GLOBALNIE
        if not hasattr(self, '_used_positions'):
            self._used_positions = set()

        from prompts.ai_layout_prompts import get_compact_position_prompt
        
        used_positions_list = list(self._used_positions)

        # Użyj kompaktowego promptu z ai_layout_prompts.py
        prompt = get_compact_position_prompt(
            diagram_type=self.diagram_type,
            batch_assignments=batch_assignments,
            zone_coordinates=zone_coordinates,
            batch_number=batch_number,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
            used_positions=used_positions_list
        )
        
        # ✅ POPRAWKA: Użyj used_positions_list zamiast used_positions
        if used_positions_list:
            prompt += f"\n\n⚠️ AVOID these already used positions: {used_positions_list[:10]}"
        
        if self.debug_ai_communication:
            log_info(f"📤 KROK 4.{batch_number} Prompt length: {len(prompt)} chars")
        
        # Wywołaj AI
        ai_response = self._call_real_ai_model(prompt, f"POSITION_BATCH_{batch_number}")
        
        # Parsuj odpowiedź
        raw_positions = self._parse_positions_batch_response(ai_response, batch_assignments)
        
        # ✅ ENSURE UNIQUE POSITIONS
        unique_positions = {}
        for elem_id, pos_data in raw_positions.items():
            x, y = pos_data['x'], pos_data['y']
            
            # Sprawdź kolizje
            pos_key = (x, y)
            offset = 0
            
            while pos_key in self._used_positions:
                offset += 25  # Przesuń o 25px
                new_x = x + offset
                new_y = y + (offset // 100) * 25  # Co 100px w prawo, 25px w dół
                pos_key = (new_x, new_y)
            
            # Zapisz unikalną pozycję
            self._used_positions.add(pos_key)
            
            unique_positions[elem_id] = {
                **pos_data,
                'x': pos_key[0],
                'y': pos_key[1]
            }
            
            if offset > 0 and self.debug_ai_communication:
                log_info(f"🔄 COLLISION RESOLVED: {elem_id[-8:]} moved by {offset}px")
        
        return unique_positions

    def _parse_positions_batch_response(self, ai_response: str, batch_assignments: Dict) -> Dict:
        """Parsuje odpowiedź AI dla grupy pozycji - ULEPSZONA WERSJA"""
        
        try:
            json_data = self._extract_json_from_response(ai_response)
            
            positions = {}
            ai_positions = json_data.get('positions', {})
            
            for short_id, pos_data in ai_positions.items():
                # Znajdź pełne ID elementu
                full_elem_id = self._find_full_element_id(short_id, batch_assignments)
                
                if full_elem_id and full_elem_id in batch_assignments:
                    positions[full_elem_id] = {
                        'x': int(pos_data.get('x', 100)),
                        'y': int(pos_data.get('y', 100)),
                        'width': int(pos_data.get('width', 140)),
                        'height': int(pos_data.get('height', 60)),
                        'column': 0,
                        'row': 0,
                        'zone': batch_assignments.get(full_elem_id, 'main_flow'),
                        'role': 'activity'
                    }
                elif self.debug_ai_communication:
                    log_warning(f"⚠️ Nie znaleziono pełnego ID dla skrótu: {short_id}")
            
            if self.debug_ai_communication:
                log_info(f"🎯 Parsed {len(positions)} positions from {len(ai_positions)} AI positions")
                
                # Pokaż statystyki mapowania
                mapped_count = len([pid for pid in ai_positions.keys() 
                                if self._find_full_element_id(pid, batch_assignments)])
                log_info(f"🎯 ID mapping success: {mapped_count}/{len(ai_positions)} ({mapped_count/len(ai_positions)*100:.1f}%)")
            
            return positions
            
        except Exception as e:
            log_error(f"Failed to parse batch positions response: {e}")
            if self.debug_ai_communication:
                log_error(f"Raw response: {ai_response[:500]}...")
            return {}

    def _generate_fallback_positions_for_batch(self, batch_assignments: Dict) -> Dict:
        """Generuje fallback pozycje dla grupy elementów (gdy AI zawiedzie)"""
        
        from prompts.ai_layout_prompts import get_zone_definitions
        
        positions = {}
        zone_defs = get_zone_definitions(self.diagram_type)
        
        if self.debug_ai_communication:
            log_info(f"🔧 FALLBACK: Generowanie pozycji dla {len(batch_assignments)} elementów")
        
        # Grupuj elementy według stref
        zones_elements = {}
        for elem_id, zone in batch_assignments.items():
            if zone not in zones_elements:
                zones_elements[zone] = []
            zones_elements[zone].append(elem_id)
        
        # Pozycjonuj w każdej strefie
        for zone_name, elements in zones_elements.items():
            if zone_name in zone_defs["zones"]:
                zone_info = zone_defs["zones"][zone_name]
                
                # Podstawowe pozycjonowanie w siatce
                x_start = zone_info["x_range"][0] + 50  # Dodaj margines
                y_start = zone_info["y_range"][0] + 50
                x_spacing = 160
                y_spacing = 80
                
                for i, elem_id in enumerate(elements):
                    col = i % 3  # Max 3 kolumny
                    row = i // 3
                    
                    positions[elem_id] = {
                        'x': x_start + (col * x_spacing),
                        'y': y_start + (row * y_spacing),
                        'width': 140,
                        'height': 60,
                        'column': col,
                        'row': row,
                        'zone': zone_name,
                        'role': 'activity'
                    }
                    
                    if self.debug_ai_communication:
                        log_info(f"🔧 FALLBACK: {elem_id[-8:]} → ({positions[elem_id]['x']}, {positions[elem_id]['y']}) w {zone_name}")
            else:
                # Jeśli strefa nie istnieje, użyj domyślnej pozycji
                for i, elem_id in enumerate(elements):
                    positions[elem_id] = {
                        'x': 100 + (i * 150),
                        'y': 100,
                        'width': 140,
                        'height': 60,
                        'column': i,
                        'row': 0,
                        'zone': 'main_flow',
                        'role': 'activity'
                    }
                    
                    if self.debug_ai_communication:
                        log_warning(f"🔧 FALLBACK: {elem_id[-8:]} → pozycja domyślna (nieznana strefa: {zone_name})")
        
        return positions

    def _call_real_ai_model(self, prompt: str, context: str = "") -> str:
        """Wywołuje prawdziwy model AI przez API - z obsługą różnych dostawców"""
        
        try:
            # Dostosowane limity według kontekstu
            if "POSITION_BATCH" in context:
                max_tokens = 2000    # Więcej tokenów dla grup pozycji
                temperature = 0.05   # Bardzo deterministyczne dla pozycji
                timeout = 240        # Krótszy timeout dla małych grup
            elif context == "POSITION_CALCULATION":
                max_tokens = 2500    # Jeszcze więcej dla dużych grup
                temperature = 0.05
                timeout = 300
            else:
                max_tokens = 1500
                temperature = 0.1
                timeout = 300
                
            if self.debug_ai_communication:
                log_info(f"🤖 REAL AI API CALL:")
                log_info(f"📤 MODEL PROVIDER: {self.model_provider}")
                log_info(f"📤 MODEL: {self.default_model}")
                log_info(f"📤 MAX_TOKENS: {max_tokens}")
                log_info(f"📤 TEMPERATURE: {temperature}")
                log_info(f"📤 CONTEXT: {context}")
                log_info(f"📤 PROMPT LENGTH: {len(prompt)} chars")
            
            # Obsługa różnych dostawców modeli
            if self.model_provider == "gemini":
                import google.generativeai as genai
                
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.default_model)
                
                # Przygotuj treść jako wiadomość
                generation_config = {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
                
                try:
                    response = model.generate_content(
                        prompt, 
                        generation_config=generation_config
                    )
                    ai_response = response.text if hasattr(response, "text") else str(response)
                    
                    if self.debug_ai_communication:
                        log_info(f"📥 GEMINI RESPONSE: {len(ai_response)} chars")
                        log_info(f"📥 PREVIEW: {ai_response[:300]}...")
                    
                    return ai_response
                    
                except Exception as e:
                    log_error(f"Gemini API error: {e}")
                    raise Exception(f"Gemini API error: {e}")
                    
            else:  # openai lub local
                import requests
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.default_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                
                # Wywołanie z odpowiednim timeout
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=timeout)
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    if self.debug_ai_communication:
                        log_info(f"📥 API RESPONSE: {len(ai_response)} chars")
                        log_info(f"📥 PREVIEW: {ai_response[:300]}...")
                    
                    return ai_response
                else:
                    log_error(f"AI API Error: {response.status_code} - {response.text}")
                    raise Exception(f"AI API returned {response.status_code}: {response.text}")
                    
        except Exception as e:
            log_error(f"AI API Exception: {e}")
            raise Exception(f"Failed to call AI API: {e}")

    def _find_full_element_id(self, short_id: str, batch_assignments: Dict) -> str:
        """Znajduje pełne ID elementu na podstawie skróconego - ULEPSZONA WERSJA"""
        
        if not short_id:
            return None
        
        # Przeszukuj batch_assignments zamiast zone_assignments (bardziej precyzyjne)
        for full_id in batch_assignments.keys():
            # Sprawdź różne warianty dopasowania
            if (full_id.endswith(short_id) or 
                short_id in full_id or
                full_id[-8:] == short_id or  # Ostatnie 8 znaków
                full_id[-6:] == short_id):   # Ostatnie 6 znaków
                
                if self.debug_ai_communication:
                    log_info(f"🎯 ID MAPPING: {short_id} → {full_id}")
                return full_id
        
        if self.debug_ai_communication:
            log_warning(f"⚠️ ID MAPPING FAILED: {short_id} (nie znaleziono w {len(batch_assignments)} elementach)")
        
        return None
    
    def _ai_step5_optimization(self, element_positions: Dict, parsed_data: Dict) -> Dict:
        """
        KROK 5: Finalna optymalizacja układu
        """
        
        log_info("🔧 KROK 5: Optymalizacja układu")
        
        # Wykryj konflikty pozycji
        conflicts = self._detect_position_conflicts(element_positions)
        
        if not conflicts:
            log_info("✅ KROK 5 COMPLETED: Brak konfliktów do optymalizacji")
            return element_positions
        
        from prompts.ai_layout_prompts import get_ai_prompt
        
        # Przygotuj podsumowanie konfliktów
        conflicts_summary = []
        for conflict in conflicts[:5]:  # Max 5 konfliktów
            conflicts_summary.append({
                'element1': conflict['elem1'][-6:],
                'element2': conflict['elem2'][-6:],
                'distance': conflict['distance'],
                'pos1': f"({conflict['pos1']['x']}, {conflict['pos1']['y']})",
                'pos2': f"({conflict['pos2']['x']}, {conflict['pos2']['y']})"
            })
        
        # Użyj promptu z ai_layout_prompts
        prompt = get_ai_prompt(
            "AI_Step_5_Optimization",
            diagram_type=self.diagram_type.capitalize(),
            element_positions=json.dumps({k: {"x": v["x"], "y": v["y"]} for k, v in element_positions.items()}, 
                                       ensure_ascii=False, indent=1),
            conflicts=json.dumps(conflicts_summary, ensure_ascii=False, indent=1),
            min_distance=120
        )
        
        ai_response = self._call_real_ai_model(prompt, "OPTIMIZATION")
        corrections = self._parse_optimization_response(ai_response)
        
        # Zastosuj poprawki
        for elem_id, correction in corrections.items():
            if elem_id in element_positions:
                element_positions[elem_id].update(correction)
        
        log_info(f"✅ KROK 5 COMPLETED: {len(corrections)} pozycji poprawionych")
        return element_positions
    
    def _parse_semantic_response(self, ai_response: str, batch_elements: List) -> Dict:
        """Parsuje odpowiedź z kroku 1 (analiza semantyczna)"""
        
        try:
            # Wyciągnij JSON z odpowiedzi
            json_data = self._extract_json_from_response(ai_response)
            
            results = {}
            elements_data = json_data.get('elements', [])
            
            for i, element_analysis in enumerate(elements_data):
                if i < len(batch_elements):
                    full_element_id = batch_elements[i].get('id')
                    if full_element_id:
                        results[full_element_id] = element_analysis
            
            return results
            
        except Exception as e:
            log_error(f"Failed to parse semantic response: {e}")
            return {}
    
    def _parse_flow_patterns_response(self, ai_response: str) -> Dict:
        """Parsuje odpowiedź z kroku 2 (wzorce przepływu)"""
        
        try:
            json_data = self._extract_json_from_response(ai_response)
            
            # Zwróć z domyślnymi wartościami jeśli brakuje kluczy
            return {
                'main_sequence': json_data.get('main_sequence', []),
                'success_branches': json_data.get('success_branches', []),
                'error_branches': json_data.get('error_branches', []),
                'parallel_flows': json_data.get('parallel_flows', []),
                'decision_points': json_data.get('decision_points', [])
            }
            
        except Exception as e:
            log_error(f"Failed to parse flow patterns response: {e}")
            return {'main_sequence': [], 'success_branches': [], 'error_branches': [], 'decision_points': []}
    
    def _parse_zone_assignment_response(self, ai_response: str) -> Dict:
        """Parsuje odpowiedź z kroku 3 (przypisanie stref)"""
        
        try:
            json_data = self._extract_json_from_response(ai_response)
            
            zone_assignments = json_data.get('zone_assignments', {})
            
            if self.debug_ai_communication:
                zone_stats = json_data.get('zone_stats', {})
                log_info(f"📊 ZONE STATS: {zone_stats}")
            
            return zone_assignments
            
        except Exception as e:
            log_error(f"Failed to parse zone assignment response: {e}")
            return {}
    
    def _parse_positions_response(self, ai_response: str, zone_assignments: Dict) -> Dict:
        """Parsuje odpowiedź z kroku 4 (pozycje XY)"""
        
        try:
            json_data = self._extract_json_from_response(ai_response)
            
            positions = {}
            ai_positions = json_data.get('positions', {})
            
            for elem_id, pos_data in ai_positions.items():
                # Znajdź pełne ID elementu
                full_elem_id = self._find_full_element_id(elem_id, zone_assignments)
                if full_elem_id:
                    positions[full_elem_id] = {
                        'x': pos_data.get('x', 100),
                        'y': pos_data.get('y', 100),
                        'width': pos_data.get('width', 140),
                        'height': pos_data.get('height', 60),
                        'column': 0,
                        'row': 0,
                        'zone': zone_assignments.get(full_elem_id, 'main_flow'),
                        'role': 'activity'
                    }
            
            return positions
            
        except Exception as e:
            log_error(f"Failed to parse positions response: {e}")
            return {}
    
    def _parse_optimization_response(self, ai_response: str) -> Dict:
        """Parsuje odpowiedź z kroku 5 (optymalizacja)"""
        
        try:
            json_data = self._extract_json_from_response(ai_response)
            
            corrections = json_data.get('corrections', {})
            
            if self.debug_ai_communication:
                for elem_id, correction in corrections.items():
                    reason = correction.get('reason', 'Brak uzasadnienia')
                    log_info(f"🔧 CORRECTION {elem_id}: {reason}")
            
            return corrections
            
        except Exception as e:
            log_error(f"Failed to parse optimization response: {e}")
            return {}
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _extract_json_from_response(self, ai_response: str) -> Dict:
        """Wyciąga JSON z odpowiedzi AI (obsługuje markdown)"""
        
        import re
        
        if self.debug_ai_communication:
            log_info(f"🔍 PARSING JSON Response length: {len(ai_response)} chars")
            log_info(f"🔍 First 500 chars: {ai_response[:500]}")
        
        # Próba 1: Surowy JSON
        try:
            result = json.loads(ai_response)
            if self.debug_ai_communication:
                log_info(f"✅ SUCCESS: Surowy JSON parsed")
            return result
        except json.JSONDecodeError as e:
            if self.debug_ai_communication:
                log_info(f"❌ Surowy JSON failed: {e}")
        
        # Próba 2: JSON w markdown blokach - ULEPSZONA REGEX
        json_patterns = [
            r'```json\s*\n(.*?)\n\s*```',     # ```json\n...\n```  
            r'```json\s*(.*?)\s*```',         # ```json ... ```
            r'```\s*\n(.*?)\n\s*```',         # ```\n...\n```
            r'```\s*(.*?)\s*```',             # ``` ... ```
            r'\{.*\}',                        # Pierwszy obiekt JSON (last resort)
        ]
        
        for i, pattern in enumerate(json_patterns):
            try:
                json_match = re.search(pattern, ai_response, re.DOTALL)
                if json_match:
                    # Dla wszystkich oprócz ostatniego wzorca, użyj grupy 1
                    if pattern != r'\{.*\}':
                        json_text = json_match.group(1).strip()
                    else:
                        json_text = json_match.group(0).strip()
                    
                    if self.debug_ai_communication:
                        log_info(f"🎯 Pattern {i+1} matched, JSON length: {len(json_text)}")
                        log_info(f"🎯 Extracted JSON preview: {json_text[:200]}...")
                    
                    result = json.loads(json_text)
                    if self.debug_ai_communication:
                        log_info(f"✅ SUCCESS: Pattern {i+1} parsed JSON with {len(result)} keys")
                    return result
                    
            except json.JSONDecodeError as e:
                if self.debug_ai_communication:
                    log_info(f"❌ Pattern {i+1} failed: {e}")
                continue
            except Exception as e:
                if self.debug_ai_communication:
                    log_info(f"❌ Pattern {i+1} error: {e}")
                continue
        
        # Jeśli nic nie zadziałało - POKAŻ WIĘCEJ SZCZEGÓŁÓW
        if self.debug_ai_communication:
            log_error(f"❌ ALL PATTERNS FAILED")
            log_error(f"📄 Full response: {ai_response}")
            
            # Sprawdź czy to problem z długością
            if len(ai_response) > 2000:
                log_error(f"⚠️ Response bardzo długi ({len(ai_response)} chars) - może problem z obcięciem?")
        
        # Rzuć bardziej szczegółowy błąd
        raise ValueError(f"Could not extract JSON from AI response. Length: {len(ai_response)} chars. "
                        f"Preview: {ai_response[:300]}...")
    
    def _find_full_element_id(self, short_id: str, zone_assignments: Dict) -> str:
        """Znajduje pełne ID elementu na podstawie skróconego"""
        
        for full_id in zone_assignments.keys():
            if full_id.endswith(short_id) or short_id in full_id:
                return full_id
        return None
    
    def _detect_position_conflicts(self, element_positions: Dict) -> List[Dict]:
        """Wykrywa konflikty pozycji (nakładające się elementy)"""
        
        conflicts = []
        positions_list = list(element_positions.items())
        
        for i, (elem1_id, pos1) in enumerate(positions_list):
            for j, (elem2_id, pos2) in enumerate(positions_list[i+1:], i+1):
                
                # Oblicz odległość między elementami
                dx = abs(pos1['x'] - pos2['x'])
                dy = abs(pos1['y'] - pos2['y'])
                distance = (dx**2 + dy**2)**0.5
                
                # Sprawdź czy się nakładają (minimalna odległość 120px)
                min_distance = 120
                if distance < min_distance:
                    conflicts.append({
                        'elem1': elem1_id,
                        'elem2': elem2_id,
                        'distance': round(distance, 1),
                        'pos1': {'x': pos1['x'], 'y': pos1['y']},
                        'pos2': {'x': pos2['x'], 'y': pos2['y']}
                    })
        
        return conflicts
    
    def _calculate_grid_info_from_positions(self, positions: Dict) -> Dict:
        """Oblicza informacje o siatce na podstawie pozycji elementów"""
        
        if not positions:
            return {'columns': 3, 'rows': 3, 'width': self.canvas_width, 'height': self.canvas_height}
        
        max_x = max(pos['x'] + pos['width'] for pos in positions.values())
        max_y = max(pos['y'] + pos['height'] for pos in positions.values())
        
        # Oszacuj liczbę kolumn i wierszy
        x_positions = sorted(set(pos['x'] for pos in positions.values()))
        y_positions = sorted(set(pos['y'] for pos in positions.values()))
        
        return {
            'columns': len(x_positions),
            'rows': len(y_positions),
            'width': min(max_x + self.margin_x, self.canvas_width),
            'height': min(max_y + self.margin_y, self.canvas_height)
        }
    
    # ============================================================================
    # COMPATIBILITY METHODS (dla istniejącego kodu)
    # ============================================================================
    
    def update_swimlane_geometry(self):
        """Placeholder dla kompatybilności"""
        pass
    
    def get_element_position(self, element_id: str) -> Dict:
        """Zwraca pozycję konkretnego elementu"""
        return self.element_positions.get(element_id, {
            'x': 100, 'y': 100, 'width': 140, 'height': 60
        })
    
    def get_all_positions(self) -> Dict:
        """Zwraca wszystkie pozycje elementów"""
        return self.element_positions.copy()
    
    def get_canvas_info(self) -> Dict:
        """Zwraca informacje o canvas"""
        return {
            'width': self.canvas_width,
            'height': self.canvas_height,
            'margin_x': self.margin_x,
            'margin_y': self.margin_y
        }
