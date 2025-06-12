import re
import xml.etree.ElementTree as ET

def extract_xml(response: str) -> str | None:
    import re
    # Najpierw spróbuj wyciągnąć blok markdown
    match = re.search(r"```xml\n(.*?)\n```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Potem spróbuj wyciągnąć XML bezpośrednio
    match = re.search(r"<\?xml.*?\?>.*?</[a-zA-Z0-9:_\-]+>", response, re.DOTALL)
    if match:
        return match.group(0).strip()
    # Ostatecznie spróbuj znaleźć pierwszy tag XML
    match = re.search(r"<[a-zA-Z0-9:_\-]+.*?>.*?</[a-zA-Z0-9:_\-]+>", response, re.DOTALL)
    if match:
        return match.group(0).strip()
    return None

def extract_plantuml(response: str) -> str | None:
    """Wyciąga blok PlantUML z odpowiedzi modelu."""
    match = re.search(r"```plantuml\n(.*?)\n```", response, re.DOTALL)
    return match.group(1).strip() if match else None

def extract_plantuml_blocks(response: str) -> list[str]:
    """
    Zwraca listę wszystkich bloków PlantUML z odpowiedzi modelu.
    """
    return re.findall(r"```plantuml\n(.*?)\n```", response, re.DOTALL)

def is_valid_xml(xml_str: str) -> bool:
    try:
        ET.fromstring(xml_str)
        return True
    except Exception:
        return False