import unittest
from plantuml_activity_parser import PlantUMLActivityParser

class TestPlantUMLActivityParser(unittest.TestCase):
    """Testy jednostkowe dla parsera PlantUML."""
    
    def test_basic_flow(self):
        """Test podstawowego przepływu start -> activity -> stop."""
        code = """
        @startuml
        start
        :Wykonaj zadanie;
        stop
        @enduml
        """
        parser = PlantUMLActivityParser(code)
        result = parser.parse()
        
        # Weryfikacja
        self.assertEqual(len(result['flow']), 3)
        self.assertEqual(result['flow'][0]['type'], 'control')
        self.assertEqual(result['flow'][1]['type'], 'activity')
        self.assertEqual(result['flow'][2]['type'], 'control')
    
    def test_decision_flow(self):
        """Test przepływu z decyzją."""
        code = """
        @startuml
        start
        if (Warunek spełniony?) then (tak)
          :Wykonaj zadanie A;
        else (nie)
          :Wykonaj zadanie B;
        endif
        stop
        @enduml
        """
        parser = PlantUMLActivityParser(code)
        result = parser.parse()
        
        # Weryfikacja struktury decyzji
        decision_elements = [e for e in result['flow'] if e['type'] == 'decision_start']
        self.assertEqual(len(decision_elements), 1)
        
        # Sprawdź czy mamy obie gałęzie
        else_elements = [e for e in result['flow'] if e['type'] == 'decision_else']
        self.assertEqual(len(else_elements), 1)
        
        # Sprawdź czy mamy połączenia dla obu gałęzi
        yes_connections = [c for c in result['logical_connections'] 
                           if c['source_id'] == decision_elements[0]['id'] and c['label'] == 'tak']
        no_connections = [c for c in result['logical_connections'] 
                          if c['source_id'] == decision_elements[0]['id'] and c['label'] == 'nie']
        self.assertEqual(len(yes_connections), 1)
        self.assertEqual(len(no_connections), 1)
    
    def test_repeat_while_loop(self):
        """Test pętli repeat-while."""
        code = """
        @startuml
        start
        repeat
          :Wykonaj zadanie;
        repeat while (Warunek spełniony?)
        stop
        @enduml
        """
        parser = PlantUMLActivityParser(code)
        result = parser.parse()
        
        # Weryfikacja pętli repeat-while
        repeat_start = [e for e in result['flow'] if e['type'] == 'repeat_start']
        repeat_end = [e for e in result['flow'] if e['type'] == 'repeat_end']
        self.assertEqual(len(repeat_start), 1)
        self.assertEqual(len(repeat_end), 1)
        
        # Sprawdź czy jest połączenie zwrotne
        loop_connections = [c for c in result['logical_connections'] 
                           if c['source_id'] == repeat_end[0]['id'] and 
                              c['target_id'] == repeat_start[0]['id']]
        self.assertEqual(len(loop_connections), 1)
    
    def test_loop_endloop(self):
        """Test pętli loop-endloop."""
        code = """
        @startuml
        start
        loop Iteruj przez elementy
          :Wykonaj zadanie;
        endloop
        stop
        @enduml
        """
        parser = PlantUMLActivityParser(code)
        result = parser.parse()
        
        # Weryfikacja pętli loop-endloop
        loop_start = [e for e in result['flow'] if e['type'] == 'loop_start']
        loop_end = [e for e in result['flow'] if e['type'] == 'loop_end']
        self.assertEqual(len(loop_start), 1)
        self.assertEqual(len(loop_end), 1)
        self.assertEqual(loop_start[0]['label'], 'Iteruj przez elementy')
        
        # Sprawdź czy jest połączenie zwrotne
        loop_connections = [c for c in result['logical_connections'] 
                           if c['source_id'] == loop_end[0]['id'] and 
                              c['target_id'] == loop_start[0]['id']]
        self.assertEqual(len(loop_connections), 1)
    
    def test_parallel_branches(self):
        """Test równoległych gałęzi (parallel)."""
        code = """
        @startuml
        start
        parallel
          :Zadanie równoległe 1;
        parallel again
          :Zadanie równoległe 2;
        end parallel
        stop
        @enduml
        """
        parser = PlantUMLActivityParser(code)
        result = parser.parse()
        
        # Weryfikacja rozgałęzienia równoległego
        parallel_start = [e for e in result['flow'] if e['type'] == 'parallel_start']
        parallel_again = [e for e in result['flow'] if e['type'] == 'parallel_again']
        parallel_end = [e for e in result['flow'] if e['type'] == 'parallel_end']
        self.assertEqual(len(parallel_start), 1)
        self.assertEqual(len(parallel_again), 1)
        self.assertEqual(len(parallel_end), 1)
        
        # Sprawdź czy są połączenia do obu gałęzi
        branch_connections = [c for c in result['logical_connections'] 
                             if c['source_id'] == parallel_start[0]['id']]
        self.assertTrue(len(branch_connections) > 0)
    
    def test_complex_nested_structures(self):
        """Test złożonych zagnieżdżonych struktur."""
        code = """
        @startuml
        start
        if (Warunek A?) then (tak)
          loop Iteruj przez elementy
            :Zadanie w pętli;
            if (Warunek B?) then (tak)
              :Zagnieżdżone zadanie;
            endif
          endloop
        else (nie)
          parallel
            :Zadanie równoległe 1;
          parallel again
            repeat
              :Zadanie w repeat;
            repeat while (Warunek C?)
          end parallel
        endif
        stop
        @enduml
        """
        parser = PlantUMLActivityParser(code)
        result = parser.parse()
        
        # Weryfikacja złożonej struktury
        decision_elements = [e for e in result['flow'] if e['type'] == 'decision_start']
        loop_elements = [e for e in result['flow'] if e['type'] == 'loop_start']
        repeat_elements = [e for e in result['flow'] if e['type'] == 'repeat_start']
        parallel_elements = [e for e in result['flow'] if e['type'] == 'parallel_start']
        
        # Sprawdź czy wszystkie struktury kontrolne zostały rozpoznane
        self.assertTrue(len(decision_elements) >= 2)  # Co najmniej 2 decyzje
        self.assertEqual(len(loop_elements), 1)      # 1 pętla loop
        self.assertEqual(len(repeat_elements), 1)    # 1 pętla repeat
        self.assertEqual(len(parallel_elements), 1)  # 1 rozgałęzienie parallel
    
    def test_island_detection(self):
        """Test wykrywania niepołączonych części diagramu."""
        code = """
        @startuml
        start
        :Zadanie 1;
        stop
        
        ' Niepołączona wyspa
        :Zadanie 2;
        :Zadanie 3;
        @enduml
        """
        parser = PlantUMLActivityParser(code)
        result = parser.parse()
        
        # Sprawdź czy mamy elementy oznaczone jako nieosiągalne
        unreachable = [e for e in result['flow'] if e.get('unreachable', False)]
        self.assertEqual(len(unreachable), 2)  # Zadania 2 i 3 powinny być nieosiągalne

if __name__ == '__main__':
    unittest.main()