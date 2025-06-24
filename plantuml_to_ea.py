from plantuml_parser import PlantUMLParser
from xmi_generator import EAXMIGenerator
import re

class PlantUMLToEAConverter:
    """Główny konwerter PlantUML do Enterprise Architect"""
    
    def __init__(self):
        self.parser = PlantUMLParser()
        self.xmi_generator = EAXMIGenerator()
    
    def convert(self, plantuml_code: str) -> str:
        """Konwertuje kod PlantUML na XMI dla EA"""
        # Parsuj PlantUML
        self.parser.parse(plantuml_code)
        
        # Generuj XMI
        xmi_content = self.xmi_generator.generate_xmi(
            self.parser.classes, 
            self.parser.relations,
            self.parser.enums,
            self.parser.notes 
        )
        
        return xmi_content
    
    def convert_file(self, input_file: str, output_file: str):
        """Konwertuje plik PlantUML na plik XMI"""
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        xmi_content = self.convert(plantuml_code)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xmi_content)
        
        print(f"Konwersja zakończona: {input_file} -> {output_file}")

# Przykład użycia
if __name__ == "__main__":
    # Przykładowy kod PlantUML
    sample_plantuml = """
    @startuml
    class Person {
        -name: String
        -age: int
        +getName(): String
        +setName(name: String): void
    }
    
    class Employee {
        -employeeId: String
        -salary: double
        +getEmployeeId(): String
    }
    
    Person <|-- Employee
    @enduml
    """
    
    # Konwertuj
    
    converter = PlantUMLToEAConverter()
    xmi_result = converter.convert(sample_plantuml)
    
    print("Wygenerowany XMI:")
    print(xmi_result[:500] + "...")  # Pokaż pierwsze 500 znaków

def plantuml_to_xmi(plantuml_code: str) -> str:
    """
    Funkcja pomocnicza do użycia w GUI – konwertuje kod PlantUML na XMI.
    """
    converter = PlantUMLToEAConverter()
    return converter.convert(plantuml_code)