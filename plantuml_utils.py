import base64
import string
import zlib
from zlib import compress
import re
import requests

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
    if 'actor' in code and '->' in code:
        return "Diagram sekwencji"
    if 'class' in code or 'interface' in code or '--|' in code or '<|--' in code:
        return "Diagram klas"
    if 'usecase' in code:
        return "Diagram przypadków użycia"
    if 'component' in code or 'node' in code:
        return "Diagram komponentów"
    return "Diagram ogólny (typ nieokreślony)"

def fetch_plantuml_svg(plantuml_code: str) -> bytes:
    """Pobiera diagram PlantUML jako SVG z serwisu plantuml.com."""
    encoded = plantuml_encode(plantuml_code)
    url = f"https://www.plantuml.com/plantuml/svg/{encoded}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Nie udało się pobrać SVG: {response.status_code}")