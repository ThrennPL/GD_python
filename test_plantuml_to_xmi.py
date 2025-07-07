from plantuml_to_ea import PlantUMLToEAConverter
from datetime import datetime
import unittest
import os

class TestPlantUMLToXMI(unittest.TestCase):
    def test_convert_file(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        #input_file = 'Proces bankowy.puml'
        input_file = 'Proces e-commerce.puml'
        #input_file = 'Proces szkoleniowy.puml'
        output_file = f'test_output_{timestamp}.xmi'
        
        
        #odczytaj plik input_file i zapisz go do zmiennej plantuml_code
        with open(input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
        
        # Convert the PlantUML file to XMI
        PlantUMLToEAConverter().convert_file(input_file, output_file)
        
        # Check if the output file was created and is not empty
        self.assertTrue(os.path.exists(output_file))
        self.assertGreater(os.path.getsize(output_file), 0)

# jak uruchomić testy

if __name__ == "__main__":
    unittest.main() 