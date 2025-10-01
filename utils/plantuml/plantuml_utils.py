import base64
import string
import zlib
from zlib import compress
import re
import requests
import subprocess
import tempfile
import os
import tempfile
from typing import List, Dict, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv 
import sys
import re 
import os


parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)
try: 
    from utils.logger_utils import setup_logger, log_info, log_error, log_exception
except ImportError as e:
    MODULES_LOADED = False
    print(f"Import error: {e}")
    sys.exit(1)

load_dotenv()

plantuml_jar_path = os.getenv("PLANTUML_JAR_PATH", "utils/plantuml/plantuml.jar")
plantuml_generator_type = os.getenv("PLANTUML_GENERATOR_TYPE", "local")
plantuml_url = os.getenv("PLANTUML_URL", "https://www.plantuml.com/plantuml")

plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet   = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = bytes.maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))

def plantuml_encode(plantuml_text):
    """Kompresuje i koduje tekst PlantUML do formatu URL zgodnego z plantuml.com."""
    zlibbed_str = compress(plantuml_text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(b64_to_plantuml).decode('utf-8')

@dataclass
class DiagramCandidate:
    """Kandydat na typ diagramu z punktacją"""
    type_key: str
    score: float
    evidence: List[str]
    
    def __str__(self):
        return f"{self.type_key} (score: {self.score:.2f})"

class PlantUMLDiagramIdentifier:
    """Klasa do etapowej identyfikacji typów diagramów PlantUML"""
    
    def __init__(self):
        # Definicje wzorców dla każdego typu diagramu
        self.patterns = {
            'class_diagram': {
                'explicit': [r'@startclass'],
                'strong': [
                    r'\bclass\s+\w+',
                    r'\binterface\s+\w+', 
                    r'\benum\s+\w+',
                    r'\babstract\s+class',
                ],
                'moderate': [
                    r'extends\b',
                    r'implements\b',
                    r'<\|--',
                    r'--\|>',
                    r'\*--',
                    r'--\*',
                    r'o--',
                    r'--o',
                    r'\+\s*\w+\s*:',  # +field:
                    r'-\s*\w+\s*:',   # -field:
                    r'#\s*\w+\s*:',   # #field:
                    r'\.\.>',
                    r'<\.\.', 
                ],
                'weak': [
                    r'\w+\s*:\s*\w+',  # field: type
                    r'\{\s*\w+.*\}',   # {fields}
                ]
            },
            
            'sequence_diagram': {
                'explicit': [r'@startsequence'],
                'strong': [
                    r'\bparticipant\b',
                    r'\bactor\b',
                    r'\w+\s*-[->]+\s*\w+\s*:',  # A -> B: message
                ],
                'moderate': [
                    r'activate\b',
                    r'deactivate\b',
                    r'note\s+(over|left|right)',
                    r'->>', r'-->', r'->x', r'--x', r'->>',
                    r'alt\b', r'else\b', r'opt\b', r'loop\b',
                    r'<<-', r'<--',
                ],
                'weak': [
                    r'->', r'<-',
                ]
            },
            
            'activity_diagram': {
                'explicit': [r'@startactivity'],
                'strong': [
                    r'\bstart\b.*\bstop\b',
                    r'\bpartition\b',
                    r'\bswimlane\b',
                    r'\bfork\b.*\bend\s+fork\b',
                ],
                'moderate': [
                    r'\bif\b.*\bthen\b',
                    r'\belse\b.*\bendif\b',
                    r'\brepeat\b.*\bwhile\b',
                    r':[^:]+;',  # :activity;
                    r'\bdetach\b',
                ],
                'weak': [
                    r'\bstart\b', r'\bstop\b', r'\bend\b',
                ]
            },
            
            'state_diagram': {
                'explicit': [r'@startstate'],
                'strong': [
                    r'\[\*\]',  # [*]
                    r'\bstate\s+\w+',
                ],
                'moderate': [
                    r'-down->', r'-up->', r'-left->', r'-right->',
                    r'\w+\s*-->\s*\w+',
                ],
                'weak': [
                    r'\bstate\b',
                ]
            },
            
            'usecase_diagram': {
                'explicit': [r'@startuse\s*case'],
                'strong': [
                    r'\busecase\b',
                    r'\buse\s+case\b',
                ],
                'moderate': [
                    r'\bactor\b(?!.*->)',  # actor bez strzałek (nie sequence)
                    r'\(\w+\)',  # (UseCase)
                ],
                'weak': []
            },
            
            'component_diagram': {
                'explicit': [r'@startcomponent'],
                'strong': [
                    r'!include\s+<c4/',
                    r'\bcomponent\s+.*<<.*>>',  # Komponent ze stereotypem - silny wzorzec!
                    r'\bcomponent\(',
                    r'\bperson\(',
                    r'\bsystem\(',
                    r'\bcontainer\(',
                    r'\benterprise\(',
                    r'\bcomponentdb\(',
                    r'\bsystemdb\(',
                    r'\bcontainerdb\(',
                    r'package\s+".*"\s+{.*component', # Pakiet zawierający komponenty
                    r'package\s+.*{.*component',      # Dowolny pakiet z komponentami
                    r'frame\s+.*{.*component',        # Frame z komponentami
                    r'\bdatabase\s+.*',               # Definicja bazy danych
                    r'\bqueue\s+.*',                  # Definicja kolejki
                    r'\binterface\s+".*"',            # Definicja interfejsu w cudzysłowach
                ],
                'moderate': [
                    r'\bcomponent\s+.*',             # Dowolny komponent
                    r'\[component\]',
                    r'\(\)<>',
                ],
                'weak': []
            },
            
            'object_diagram': {
                'explicit': [r'@startobject'],
                'strong': [
                    r'\bobject\s+\w+',
                ],
                'moderate': [
                    r'\w+\s*:\s*\w+\s*{',  # object: Class {
                ],
                'weak': []
            }
        }
        
        # Wzorce wykluczające (anty-wzorce)
        self.exclusion_patterns = {
            'activity_diagram': [
                r'\bparticipant\b',
                r'\bclass\s+\w+',
                r'\binterface\s+\w+',
                r'<\|--', r'--\|>',
                r'\w+\s*->\s*\w+\s*:',  # A -> B: message pattern
            ],
            'sequence_diagram': [
                r'\bclass\s+\w+',
                r'\binterface\s+\w+',
                r'extends\b',
                r'implements\b',
                r'<\|--', r'--\|>',
                r'package\s+.*{\s*.*component',  # Wykluczenie gdy są pakiety z komponentami
                r'component\s+.*<<.*>>',         # Wykluczenie gdy są komponenty ze stereotypami
                r'frame\s+.*{.*component',       # Wykluczenie gdy są ramki z komponentami

            ],
            'class_diagram': [
                r'\bparticipant\b',
                r'\bactor\b.*->',
                r'activate\b',
                r'deactivate\b',
            ]
        }

    def preprocess_code(self, plantuml_code: str) -> str:
        """Preprocessing kodu - usunięcie komentarzy i normalizacja"""
        lines = plantuml_code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Usuń komentarze ale zachowaj resztę linii
            if "'" in line:
                comment_pos = line.find("'")
                line = line[:comment_pos]
            cleaned_lines.append(line.strip())
        
        return '\n'.join(cleaned_lines).lower()

    def check_explicit_declarations(self, code: str) -> str:
        """Etap 1: Sprawdź jawne deklaracje @start*"""
        special_types = {
            r'@startsalt': 'wireframe',
            r'@startmindmap': 'mindmap_diagram',
            r'@startgantt': 'gantt_chart',
            r'@startwbs': 'work_breakdown',
            r'@starterdiagram': 'erd_diagram',
        }
        
        for pattern, diagram_type in special_types.items():
            if re.search(pattern, code):
                return diagram_type
                
        # Sprawdź główne typy
        for diagram_type, patterns in self.patterns.items():
            for pattern in patterns['explicit']:
                if re.search(pattern, code):
                    return diagram_type.replace('_diagram', '')
                    
        return None

    def score_candidates(self, code: str) -> List[DiagramCandidate]:
        """Etap 2: Punktowanie kandydatów"""
        candidates = []
        
        for diagram_type, patterns in self.patterns.items():
            score = 0.0
            evidence = []
            
            # Punkty za różne poziomy dopasowania
            for pattern in patterns['strong']:
                matches = len(re.findall(pattern, code))
                if matches > 0:
                    score += matches * 3.0
                    evidence.append(f"Strong: {pattern} ({matches}x)")
                    
            for pattern in patterns['moderate']:
                matches = len(re.findall(pattern, code))
                if matches > 0:
                    score += matches * 1.5
                    evidence.append(f"Moderate: {pattern} ({matches}x)")
                    
            for pattern in patterns['weak']:
                matches = len(re.findall(pattern, code))
                if matches > 0:
                    score += matches * 0.5
                    evidence.append(f"Weak: {pattern} ({matches}x)")
            
            # Zastosuj kary za wzorce wykluczające
            if diagram_type in self.exclusion_patterns:
                for exclusion_pattern in self.exclusion_patterns[diagram_type]:
                    exclusion_matches = len(re.findall(exclusion_pattern, code))
                    if exclusion_matches > 0:
                        penalty = exclusion_matches * 2.0
                        score -= penalty
                        evidence.append(f"Penalty: {exclusion_pattern} (-{penalty})")
            
            if score > 0:
                candidates.append(DiagramCandidate(
                    type_key=diagram_type,
                    score=score,
                    evidence=evidence
                ))
        
        return sorted(candidates, key=lambda x: x.score, reverse=True)

    def resolve_conflicts(self, candidates: List[DiagramCandidate], code: str) -> DiagramCandidate:
        """Etap 3: Rozwiązywanie konfliktów między podobnymi kandydatami"""
        if len(candidates) <= 1:
            return candidates[0] if candidates else None
            
        top_candidates = [c for c in candidates if c.score >= candidates[0].score * 0.7]
        
        # Specjalne reguły rozwiązywania konfliktów
        candidate_types = {c.type_key for c in top_candidates}
        
        # Konflikt: class vs sequence
        if {'class_diagram', 'sequence_diagram'}.issubset(candidate_types):
            # Jeśli jest participant/actor + strzałki komunikatów -> sequence
            if re.search(r'(participant|actor).*->\s*\w+\s*:', code):
                return next(c for c in top_candidates if c.type_key == 'sequence_diagram')
            # Jeśli są definicje klas -> class
            elif re.search(r'(class|interface|enum)\s+\w+', code):
                return next(c for c in top_candidates if c.type_key == 'class_diagram')
        
        # Konflikt: activity vs class/sequence
        if 'activity_diagram' in candidate_types:
            if {'class_diagram', 'sequence_diagram'} & candidate_types:
                # Jeśli są wyraźne wskaźniki class/sequence, usuń activity
                if re.search(r'(participant|class\s+\w+|interface\s+\w+)', code):
                    top_candidates = [c for c in top_candidates if c.type_key != 'activity_diagram']
        
        # Konflikt: component vs class
        if {'component_diagram', 'class_diagram'}.issubset(candidate_types):
            # C4 ma priorytet
            if re.search(r'(!include\s+<c4/|component\(|person\()', code):
                return next(c for c in top_candidates if c.type_key == 'component_diagram')
        if {'component_diagram', 'sequence_diagram'}.issubset(candidate_types):
            # Jeśli są pakiety z komponentami wewnątrz, to jest to diagram komponentów
            if re.search(r'package\s+.*\{\s*.*component', code):
                return next(c for c in top_candidates if c.type_key == 'component_diagram')
            # Jeśli są komponenty ze stereotypami, to jest to diagram komponentów
            elif re.search(r'component\s+.*<<.*>>', code):
                return next(c for c in top_candidates if c.type_key == 'component_diagram')
            # Jeśli w pliku jest jawne określenie, że to diagram komponentów
            elif re.search(r'diagram\s*komponent(ów|ow)', code, re.IGNORECASE):
                return next(c for c in top_candidates if c.type_key == 'component_diagram')
            # Jeśli nazwa pliku wskazuje na diagram komponentów
            elif hasattr(self, 'filename') and re.search(r'komponent', getattr(self, 'filename', ''), re.IGNORECASE):
                return next(c for c in top_candidates if c.type_key == 'component_diagram')   

        
        # Zwróć kandydata z najwyższym wynikiem
        return top_candidates[0] if top_candidates else candidates[0]

def identify_plantuml_diagram_type(plantuml_code: str, LANG="pl", debug=False, filename=None) -> str:
    """
    Rozpoznaje typ diagramu PlantUML na podstawie kodu źródłowego.
    Zwraca polską nazwę typu diagramu do wyświetlenia w interfejsie.
    
    Args:
        plantuml_code: Kod PlantUML do analizy
        LANG: Kod języka dla tłumaczeń (domyślnie 'pl')
        debug: Czy wyświetlić informacje debugowe (opcjonalny)
        filename: Nazwa pliku z kodem (opcjonalny)
        
    Returns:
        str: Przetłumaczona nazwa typu diagramu
    """
    identifier = PlantUMLDiagramIdentifier()
    if filename:
        identifier.filename = filename
    code = identifier.preprocess_code(plantuml_code)
    
    if debug:
        print("=== ETAP 1: Sprawdzanie jawnych deklaracji ===")
    
    # Etap 1: Jawne deklaracje
    explicit_type = identifier.check_explicit_declarations(code)
    if explicit_type:
        if debug:
            print(f"Znaleziono jawną deklarację: {explicit_type}")
        # Tłumaczenie specjalnych typów diagramów
        translations = {
            'wireframe': 'Diagram interfejsu',
            'mindmap_diagram': 'Mapa myśli',
            'mindmap': 'Mapa myśli',
            'gantt_chart': 'Wykres Gantta',
            'gantt': 'Wykres Gantta',
            'work_breakdown': 'Diagram WBS',
            'erd_diagram': 'Diagram ERD',
            'erd': 'Diagram ERD'
        }
        return translations.get(explicit_type, f"Diagram {explicit_type}")
    
    if debug:
        print("Brak jawnych deklaracji, przechodząc do punktowania...")
        print("\n=== ETAP 2: Punktowanie kandydatów ===")
    
    # Etap 2: Punktowanie kandydatów  
    candidates = identifier.score_candidates(code)
    
    if debug:
        print("Kandydaci:")
        for i, candidate in enumerate(candidates[:5], 1):
            print(f"{i}. {candidate}")
            for evidence in candidate.evidence:
                print(f"   - {evidence}")
    
    if not candidates:
        if debug:
            print("Brak kandydatów, zwracam typ ogólny")
        return "Diagram ogólny"
    
    if debug:
        print(f"\n=== ETAP 3: Rozwiązywanie konfliktów ===")
    
    # Etap 3: Rozwiązywanie konfliktów
    final_candidate = identifier.resolve_conflicts(candidates, code)
    
    if debug:
        print(f"Wybrany kandydat: {final_candidate}")
    
    diagram_type = final_candidate.type_key.replace('_diagram', '')
    
    # Mapa tłumaczeń typów diagramów na język polski
    pl_diagram_types = {
        'class': 'Diagram klas',
        'sequence': 'Diagram sekwencji',
        'activity': 'Diagram aktywności',
        'state': 'Diagram stanów',
        'usecase': 'Diagram przypadków użycia',
        'component': 'Diagram komponentów',
        'object': 'Diagram obiektów',
    }
    
    # Zwróć polską nazwę typu diagramu lub ogólną jeśli brak tłumaczenia
    return pl_diagram_types.get(diagram_type, "Diagram ogólny")

def fetch_plantuml_svg_www(plantuml_code: str, LANG="pl") -> bytes:
    #Pobiera diagram PlantUML jako SVG z serwisu plantuml.com.
    encoded = plantuml_encode(plantuml_code)
    url = f"{plantuml_url}/svg/{encoded}"
    response = requests.get(url)
    log_info(f"Pobieranie SVG z serwisu plantuml.com: {url}")
    
    error_headers = {
        'line': response.headers.get('X-PlantUML-Diagram-Error-Line', ''),
        'error': response.headers.get('X-PlantUML-Diagram-Error', ''),
        'description': response.headers.get('X-PlantUML-Diagram-Description', '')
    }
    
    error_msg = ''
    if error_headers['line'].isdigit():
        error_msg = f"{int(error_headers['line'])+1}: {error_headers['error']} : {error_headers['description']}" 
  
    if response.status_code == 200:
        log_error(f"Błąd powbierania SVG (kod: {response.status_code}):\n {error_msg}") 
        return response.content, error_msg
    else:
        error_msg = f"Błąd powbierania SVG (kod: {response.status_code}):\n {response.text}"
        log_error(f"{error_msg}")
        raise Exception(error_msg)
    
def fetch_plantuml_svg_local(plantuml_code: str, plantuml_jar_path: str = "plantuml.jar", LANG="pl") -> str:
    tmpdir = tempfile.mkdtemp()
    puml_path = os.path.join(tmpdir, "diagram.puml")
    svg_path = os.path.join(tmpdir, "diagram.svg")
    with open(puml_path, "w", encoding="utf-8") as f:
        f.write(plantuml_code)
    result = subprocess.run(
        [
            "java", "-jar", plantuml_jar_path, "-stdrpt:2", "-tsvg",
            puml_path, "-charset", "UTF-8"
        ],
        capture_output=True
    )
    stdout_jar = result.stdout.decode("utf-8")
    stderr_jar = result.stderr.decode("utf-8")
    error_msg = None

    if result.returncode != 0 or stderr_jar:
        # Priorytetowo zwracamy stderr, bo tam PlantUML wywala błędy Java
        error_msg = stderr_jar.strip() or stdout_jar.strip()
        log_error(f"PlantUML error: {error_msg}")
    else:
        # Dodatkowo można sprawdzać stderr na obecność "Error" lub typowych fragmentów
        error_msg = ""
        log_info(f"Plik SVG został pomyślnie wygenerowany i zapisany jako: {svg_path}")
        if stdout_jar.strip() != "":
            log_info(f"PlantUML stdout: {stdout_jar.strip()}")

    return svg_path, error_msg

# Przykład użycia funkcji
if __name__ == "__main__":
    import sys
    import argparse
    from datetime import datetime


    # Konfiguracja parsera argumentów
    parser = argparse.ArgumentParser(description="Narzędzie do obsługi diagramów PlantUML")
    parser.add_argument('input_file', nargs='?', default='Diagram_aktywnosci_test2.puml',
                    help='Ścieżka do pliku z kodem PlantUML (domyślnie: diagram.puml)')
    
    # Grupa wzajemnie wykluczających się operacji
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--identify', '-i', action='store_true', 
                      help='Identyfikuj typ diagramu')
    group.add_argument('--generate-local', '-gl', action='store_true', 
                      help='Generuj SVG lokalnie')
    group.add_argument('--generate-www', '-gw', action='store_true', 
                      help='Generuj SVG przez serwis www.plantuml.com')
    
    # Opcje dodatkowe
    parser.add_argument('--output', '-o', 
                      help='Ścieżka pliku wyjściowego (dla generowania)')
    parser.add_argument('--debug', '-d', action='store_true', 
                      help='Włącz tryb debugowania')
    parser.add_argument('--jar', 
                      help=f'Ścieżka do pliku JAR PlantUML (domyślnie: {plantuml_jar_path})')
    
    # Parsowanie argumentów
    args = parser.parse_args()
    
    # Konfiguracja logowania
    setup_logger('plantuml_utils.log')
    
    try:
        # Wczytaj plik PlantUML
        log_info(f"Wczytywanie pliku: {args.input_file}")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Identyfikacja typu diagramu
        if args.identify:
            diagram_type = identify_plantuml_diagram_type(plantuml_code, debug=args.debug, filename=args.input_file)            
            log_info(f"Zidentyfikowany typ diagramu: {diagram_type}")
            print(f"\nZidentyfikowany typ diagramu: {diagram_type}\n")
            
            # Wypisz szczegóły jeśli włączono debugowanie
            if args.debug:
                print("\nSzczegółowa analiza diagramu:")
                identifier = PlantUMLDiagramIdentifier()
                code = identifier.preprocess_code(plantuml_code)
                candidates = identifier.score_candidates(code)
                
                if candidates:
                    print("\nWszystkie znalezione typy diagramów (według punktacji):")
                    for i, candidate in enumerate(candidates, 1):
                        print(f"{i}. {candidate.type_key} - {candidate.score:.2f} punktów")
        
        # 2. Generowanie SVG lokalnie
        elif args.generate_local:
            jar_path = args.jar or plantuml_jar_path
            output_path = args.output or f"diagram_local_{timestamp}.svg"
            
            print(f"Generowanie SVG lokalnie przy użyciu {jar_path}...")
            svg_path, error_msg = fetch_plantuml_svg_local(plantuml_code, jar_path)
            
            if not error_msg:
                # Kopiowanie do wskazanego miejsca docelowego
                import shutil
                shutil.copy(svg_path, output_path)
                log_info(f"SVG wygenerowano pomyślnie i zapisano jako: {output_path}")
                print(f"\nSVG wygenerowano pomyślnie i zapisano jako: {output_path}")
                
                if args.debug:
                    # Identyfikuj diagram dla celów informacyjnych
                    diagram_type = identify_plantuml_diagram_type(plantuml_code)
                    print(f"Typ diagramu: {diagram_type}")
            else:
                log_error(f"Błąd generowania SVG: {error_msg}")
                print(f"\nBłąd generowania SVG: {error_msg}")
                sys.exit(1)
        
        # 3. Generowanie SVG przez serwis WWW
        elif args.generate_www:
            output_path = args.output or f"diagram_www_{timestamp}.svg"
            
            print("Generowanie SVG przez serwis www.plantuml.com...")
            try:
                svg_content, error_msg = fetch_plantuml_svg_www(plantuml_code)
                
                if not error_msg:
                    # Zapisz SVG do pliku
                    with open(output_path, 'wb') as f:
                        f.write(svg_content)
                    log_info(f"SVG wygenerowano pomyślnie i zapisano jako: {output_path}")
                    print(f"\nSVG wygenerowano pomyślnie i zapisano jako: {output_path}")
                    
                    if args.debug:
                        # Identyfikuj diagram dla celów informacyjnych
                        diagram_type = identify_plantuml_diagram_type(plantuml_code)
                        print(f"Typ diagramu: {diagram_type}")
                else:
                    log_error(f"Ostrzeżenie generowania SVG: {error_msg}")
                    print(f"\nOstrzeżenie generowania SVG: {error_msg}")
                    
                    # Zapisz SVG do pliku mimo ostrzeżenia
                    with open(output_path, 'wb') as f:
                        f.write(svg_content)
                    print(f"SVG zapisano jako: {output_path} (z ostrzeżeniami)")
            except Exception as e:
                log_error(f"Błąd generowania SVG przez WWW: {e}")
                print(f"\nBłąd generowania SVG przez WWW: {e}")
                sys.exit(1)
    
    except FileNotFoundError:
        log_error(f"Nie znaleziono pliku: {args.input_file}")
        print(f"\nNie znaleziono pliku: {args.input_file}")
        print(f"Użycie: python {sys.argv[0]} <ścieżka_do_pliku_puml> [opcje]")
        sys.exit(1)
    except Exception as e:
        log_error(f"Wystąpił błąd: {e}")
        print(f"\nWystąpił błąd: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
