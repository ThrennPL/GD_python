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
    code = plantuml_code.lower()
    if 'state' in code or '-->' in code and 'state' in code:
        return tr("diagram_type_state_diagram", LANG=LANG)
    if 'actor' in code and ('->' in code or '->>' in code or '->|' in code) and ('component' not in code or 'deployment' not in code):
        return tr("diagram_type_sequence_diagram", LANG=LANG)
    if 'class' in code or 'interface' in code or '--|' in code or '<|--' in code:
        return tr("diagram_type_class_diagram", LANG=LANG)
    if ('usecase' in code or 'use case' in code) and ('actor' in code or '->' in code or '->>' in code):
        return tr("diagram_type_usecase_diagram", LANG=LANG)
    if 'component' in code or 'node' in code or 'package' in code or 'container' in code:
        return tr("diagram_type_component_diagram", LANG=LANG)
    if 'activity' in code or 'start' in code or 'end' in code:
        return tr("diagram_type_activity_diagram", LANG=LANG)
    if 'object' in code or 'note' in code:
        return tr("diagram_type_object_diagram", LANG=LANG)  
    if 'deployment' in code or 'artifact' in code:
        return tr("diagram_type_deployment_diagram", LANG=LANG)
    if 'flow' in code or 'data' in code or 'process' in code:
        return tr("diagram_type_flow_diagram", LANG=LANG)     
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
        log_error(f"Nie udało się pobrać SVG: {response.status_code}, Error: {error_msg}")
        return response.content, error_msg
    else:
        error_msg = tr("msg_error_downloading_SVG", LANG=LANG).format(
            status_code=response.status_code,
            error_text=response.text
        )
        raise Exception(error_msg)
    
def fetch_plantuml_svg_local(plantuml_code: str, plantuml_jar_path: str = "plantuml.jar", LANG="pl") -> str:
    """
    Generates SVG from PlantUML code using local plantuml.jar and returns the path to the SVG file.
    The temporary file is not deleted automatically – remove it when no longer needed.
    """

    tmpdir = tempfile.mkdtemp()
    puml_path = os.path.join(tmpdir, "diagram.puml")
    svg_path = os.path.join(tmpdir, "diagram.svg")
    # Save PlantUML code to a temporary file
    with open(puml_path, "w", encoding="utf-8") as f:
        f.write(plantuml_code)
    # Generate SVG using plantuml.jar
    result = subprocess.run([
        "java", "-jar", plantuml_jar_path, "-stdrpt:2", "-tsvg", puml_path,"-charset","UTF-8"
    ], capture_output=True)
    stdout_jar = result.stdout.decode("utf-8")

    error_msg = ''
    if ":" in stdout_jar:
        error_msg = stdout_jar.split(":", 1)[1].strip()
        log_error(f"Extracted error message: {error_msg}")
    else:
        error_msg= stdout_jar

    log_info(f"PlantUML stdout: {error_msg}")
    return svg_path, error_msg

