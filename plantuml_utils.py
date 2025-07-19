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
from logger_utils import setup_logger, log_info, log_error, log_exception
from translations_pl import TRANSLATIONS as PL
from translations_en import TRANSLATIONS as EN

load_dotenv()

plantuml_jar_path = os.getenv("PLANTUML_JAR_PATH", "plantuml.jar")
plantuml_generator_type = os.getenv("PLANTUML_GENERATOR_TYPE", "local")
plantuml_url = os.getenv("PLANTUML_URL", "https://www.plantuml.com/plantuml")

plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet   = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = bytes.maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))

LANG = os.getenv("LANG", "pl")

def tr(key, LANG="pl"):
        return EN[key] if LANG == "en" else PL[key]

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
                    r'\bcomponent\(',
                    r'\bperson\(',
                    r'\bsystem\(',
                    r'\bcontainer\(',
                    r'\benterprise\(',
                    r'\bcomponentdb\(',
                    r'\bsystemdb\(',
                    r'\bcontainerdb\(',
                ],
                'moderate': [
                    r'\bcomponent\s+\w+',
                    r'\[component\]',
                    r'\(\)<>',
                    r'\bdatabase\b',
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
        
        # Zwróć kandydata z najwyższym wynikiem
        return top_candidates[0] if top_candidates else candidates[0]

def identify_plantuml_diagram_type(plantuml_code: str, LANG="pl", debug=False) -> str:
    """
    Rozpoznaje typ diagramu PlantUML na podstawie kodu źródłowego.
    Funkcja kompatybilna z oryginalnym interfejsem plantuml_utils.py
    
    Args:
        plantuml_code: Kod PlantUML do analizy
        LANG: Kod języka dla tłumaczeń
        debug: Czy wyświetlić informacje debugowe (opcjonalny)
        
    Returns:
        str: Przetłumaczona nazwa typu diagramu
    """
    identifier = PlantUMLDiagramIdentifier()
    code = identifier.preprocess_code(plantuml_code)
    
    if debug:
        print("=== ETAP 1: Sprawdzanie jawnych deklaracji ===")
    
    # Etap 1: Jawne deklaracje
    explicit_type = identifier.check_explicit_declarations(code)
    if explicit_type:
        if debug:
            print(f"Znaleziono jawną deklarację: {explicit_type}")
        return tr(f"diagram_type_{explicit_type}", LANG=LANG)
    
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
        return tr("diagram_type_general", LANG=LANG)
    
    if debug:
        print(f"\n=== ETAP 3: Rozwiązywanie konfliktów ===")
    
    # Etap 3: Rozwiązywanie konfliktów
    final_candidate = identifier.resolve_conflicts(candidates, code)
    
    if debug:
        print(f"Wybrany kandydat: {final_candidate}")
    
    diagram_type = final_candidate.type_key.replace('_diagram', '')
    return tr(f"diagram_type_{diagram_type}_diagram", LANG=LANG)

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
        log_error(tr("msg_error_downloading_SVG", LANG=LANG).format(status_code=response.status_code, error_text=error_msg)) 
        return response.content, error_msg
    else:
        error_msg = tr("msg_error_downloading_SVG", LANG=LANG).format(
            status_code=response.status_code,
            error_text=response.text
        )
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
        log_info(tr("msg_info_success_generating_SVG", LANG=LANG).format(svg_path=svg_path))
        log_info(f"PlantUML stdout: {stdout_jar.strip()}")

    return svg_path, error_msg

# Dodaj na końcu pliku plantuml_utils.py
if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    # Obsługa argumentów wiersza poleceń lub użycie wartości domyślnych
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'diagram_sekwencji_PlantUML.puml'
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #output_file = f"diagram_klas_{timestamp}.xmi"
    
    try:
        # Wczytaj plik PlantUML
        log_info(tr("msg_info_reading_file", LANG="pl").format(input_file=input_file))
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        # Najpierw zidentyfikuj typ diagramu - teraz z możliwością debugowania
        diagram_type = identify_plantuml_diagram_type(plantuml_code, debug=True)
        log_info(tr("msg_info_diagram_type", LANG="pl").format(diagram_type=diagram_type)) 
        print(f"Zidentyfikowany typ diagramu: {diagram_type}")
        
    except FileNotFoundError:
        log_error(tr("msg_error_file_not_found", LANG="pl").format(input_file=input_file)) 
        log_info(tr("msg_info_usage", LANG="pl").format(script_name=sys.argv[0])) 
    except Exception as e:
        log_error(tr("msg_error_reading_file", LANG="pl").format(input_file=input_file, error=e)) 
        import traceback
        traceback.print_exc()