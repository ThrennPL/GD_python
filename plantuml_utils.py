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

def tr(key, LANG="pl"):
        return EN[key] if LANG == "en" else PL[key]

def plantuml_encode(plantuml_text):
    """Kompresuje i koduje tekst PlantUML do formatu URL zgodnego z plantuml.com."""
    zlibbed_str = compress(plantuml_text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(b64_to_plantuml).decode('utf-8')

def identify_plantuml_diagram_type(plantuml_code: str, LANG="pl") -> str:
    """
    Rozpoznaje typ diagramu PlantUML na podstawie kodu źródłowego.
    
    Args:
        plantuml_code: Kod PlantUML do analizy
        LANG: Kod języka dla tłumaczeń
        
    Returns:
        str: Przetłumaczona nazwa typu diagramu
    """
    # Usuń komentarze i znormalizuj kod do małych liter
    code = re.sub(r"'.*$", "", plantuml_code, flags=re.MULTILINE).lower()
    
    # Sprawdź czy to diagram C4 - ma najwyższy priorytet
    c4_indicators = ['!include <c4/', 'component(', 'person(', 'system(', 'container(', 
                    'enterprise(', 'componentdb(', 'systemdb(', 'containerdb(']
    if any(indicator in code for indicator in c4_indicators):
        return tr("diagram_type_component_diagram", LANG=LANG)
    
    # Sprawdź jawne deklaracje typu diagramu
    if re.search(r'@startsalt', code):
        return tr("diagram_type_wireframe", LANG=LANG)
    if re.search(r'@startmindmap', code):
        return tr("diagram_type_mindmap_diagram", LANG=LANG)
    if re.search(r'@startgantt', code):
        return tr("diagram_type_gantt_chart", LANG=LANG)
    if re.search(r'@startwbs', code):
        return tr("diagram_type_work_breakdown", LANG=LANG)
    if re.search(r'@starterdiagram', code):
        return tr("diagram_type_erd_diagram", LANG=LANG)
    if re.search(r'@startstate', code):
        return tr("diagram_type_state_diagram", LANG=LANG)
    if re.search(r'@startactivity', code):
        return tr("diagram_type_activity_diagram", LANG=LANG)
    if re.search(r'@startcomponent', code):
        return tr("diagram_type_component_diagram", LANG=LANG)
    if re.search(r'@startclass', code):
        return tr("diagram_type_class_diagram", LANG=LANG)
    if re.search(r'@startobject', code):
        return tr("diagram_type_object_diagram", LANG=LANG)
    if re.search(r'@startsequence', code):
        return tr("diagram_type_sequence_diagram", LANG=LANG)
    if re.search(r'@startuse\s*case', code):
        return tr("diagram_type_usecase_diagram", LANG=LANG)
    
    # Standardowy diagram komponentów (bez C4)
    component_indicators = ['component ', '[component]', '()<>']
    if any(indicator in code for indicator in component_indicators):
        return tr("diagram_type_component_diagram", LANG=LANG)
    
    # Wykrywanie na podstawie zawartości - w kolejności od najbardziej specyficznych

    # Diagram aktywności
    activity_indicators = ['start', 'stop', ':' in code and ';' in code]
    activity_control_flow = ['if', 'then', 'else', 'endif', 'repeat', 'while', 'fork', 'fork again']
    if ('start' in code and any(indicator in code for indicator in activity_control_flow)) or \
    (re.search(r':[^;]+;', code) and any(indicator in code for indicator in activity_indicators)):
        return tr("diagram_type_activity_diagram", LANG=LANG)
    
    # Diagram klas - wyższy priorytet niż diagram sekwencji!
    class_indicators = ['class ', 'interface ', 'enum ', 'abstract class', 'extends', 'implements']
    if any(indicator in code for indicator in class_indicators):
        return tr("diagram_type_class_diagram", LANG=LANG)
    
    # Sprawdź symbole relacji typowe dla diagramów klas
    class_relationships = ['<|--', '--|>', '*--', '--*', 'o--', '--o', '<--*', '*-->']
    if any(rel in code for rel in class_relationships):
        return tr("diagram_type_class_diagram", LANG=LANG)
    
    # Diagram sekwencji
    if (('actor' in code or 'participant' in code) and 
        any(arrow in code for arrow in ['->>', '->x', '-->', '->', '<-', '<--'])):
        return tr("diagram_type_sequence_diagram", LANG=LANG)
    
    # Diagram stanu
    state_indicators = ['state', '[*]', '-down->', '-up->', '-left->', '-right->']
    if any(indicator in code for indicator in state_indicators):
        return tr("diagram_type_state_diagram", LANG=LANG)
    
    # Diagram przypadków użycia
    if ('usecase' in code or 'use case' in code) or ('actor' in code and not '->' in code):
        return tr("diagram_type_usecase_diagram", LANG=LANG)
    
    # Jeśli mamy @startuml ale nie dopasowaliśmy do innych typów,
    # sprawdź jeszcze raz zawartość aby rozróżnić diagram klas od sekwencji
    if '{' in code and '}' in code and '--' in code:
        return tr("diagram_type_class_diagram", LANG=LANG)
    
    # Domyślny typ
    return tr("diagram_type_general", LANG=LANG)

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
        log_info(tr("msg_info_success_generating_SVG", LANG=LANG)).format(svg_path=svg_path)
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
        input_file = 'Diagram_aktywnosci.puml'
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #output_file = f"diagram_klas_{timestamp}.xmi"
    
    try:
        # Wczytaj plik PlantUML
        log_info(tr("msg_info_reading_file", LANG="pl").format(input_file=input_file))
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        # Najpierw zidentyfikuj typ diagramu
        diagram_type = identify_plantuml_diagram_type(plantuml_code)
        log_info(tr("msg_info_diagram_type", LANG="pl").format(diagram_type=diagram_type)) 
        
    except FileNotFoundError:
        log_error(tr("msg_error_file_not_found", LANG="pl").format(input_file=input_file)) 
        log_info(tr("msg_info_usage", LANG="pl").format(script_name=sys.argv[0])) 
    except Exception as e:
        log_error(tr("msg_error_reading_file", LANG="pl").format(input_file=input_file, error=e)) 
        import traceback
        traceback.print_exc()