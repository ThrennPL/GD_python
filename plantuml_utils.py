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

plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet   = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = bytes.maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))

def plantuml_encode(plantuml_text):
    """Kompresuje i koduje tekst PlantUML do formatu URL zgodnego z plantuml.com."""
    zlibbed_str = compress(plantuml_text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(b64_to_plantuml).decode('utf-8')

def identify_plantuml_diagram_type(plantuml_code: str) -> str:
    code = plantuml_code.lower()
    if 'state' in code or '-->' in code and 'state' in code:
        return "Diagram stanów"
    if 'actor' in code and ('->' in code or '->>' in code or '->|' in code) and 'component' not in code:
        return "Diagram sekwencji"
    if 'class' in code or 'interface' in code or '--|' in code or '<|--' in code:
        return "Diagram klas"
    if 'usecase' in code:
        return "Diagram przypadków użycia"
    if 'component' in code or 'node' in code or 'package' in code or 'container' in code:
        return "Diagram komponentów"
    if 'activity' in code or 'start' in code or 'end' in code:
        return "Diagram aktywności"
    if 'object' in code or 'note' in code:
        return "Diagram obiektów"   
    if 'deployment' in code or 'artifact' in code:
        return "Diagram wdrożenia"
    return "Diagram ogólny (typ nieokreślony)"

def fetch_plantuml_svg_www(plantuml_code: str) -> bytes:
    #Pobiera diagram PlantUML jako SVG z serwisu plantuml.com.
    encoded = plantuml_encode(plantuml_code)
    url = f"https://www.plantuml.com/plantuml/svg/{encoded}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Nie udało się pobrać SVG: {response.status_code}")
    
def fetch_plantuml_svg_local(plantuml_code: str, plantuml_jar_path: str = "plantuml.jar") -> str:
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
    subprocess.run([
        "java", "-jar", plantuml_jar_path, "-tsvg", puml_path
    ], check=True)
    # Return the path to the generated SVG file
    return svg_path
    