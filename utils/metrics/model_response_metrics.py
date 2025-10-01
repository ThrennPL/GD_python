import time
import functools
from datetime import datetime
import json
import os
from utils.logger_utils import log_info, log_error

def measure_response_time(func=None, measure_result=True, model_arg_position=None):
    """Dekorator do pomiaru czasu odpowiedzi modelu AI
    
    Działa zarówno z nawiasami jak i bez:
    @measure_response_time
    def func(): pass
    
    LUB
    
    @measure_response_time(measure_result=False)
    def func(): pass
    
    Args:
        func: Funkcja do udekorowania (automatycznie gdy używany bez nawiasów)
        measure_result (bool): Czy mierzyć i zapisywać wynik tej funkcji
        model_arg_position (int): Pozycja argumentu z nazwą modelu (None = auto)
    """
    # Przypadek gdy używany bez nawiasów @measure_response_time
    if callable(func):
        @functools.wraps(func)
        def direct_wrapper(*args, **kwargs):
            # Początek pomiaru
            start_time = time.time()
            start_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            function_name = func.__name__
            
            # Identyfikacja modelu
            model_name = "unknown"
            
            # Rozpoznaj model na podstawie funkcji
            if function_name == "handle_api_response" and len(args) > 1:
                model_name = args[1]  # args[0]=self, args[1]=model_name
            elif function_name == "start_api_thread" and len(args) > 1:
                # args[0]=self, args[1]=prompt, args[2]=model_name (opcjonalnie)
                if len(args) > 2 and args[2]:
                    model_name = args[2]
                else:
                    model_name = kwargs.get('model_name', "unknown")
            elif function_name == "run" and hasattr(args[0], 'model_name'):
                # Dla APICallThread.run()
                model_name = args[0].model_name
            # Pobierz z kwargs
            elif 'model_name' in kwargs:
                model_name = kwargs['model_name']
            elif 'model' in kwargs:
                model_name = kwargs['model']
            
            # Uprość nazwę modelu
            if isinstance(model_name, str) and '/' in model_name:
                model_name = model_name.split('/')[-1]
            
            # Wykonaj oryginalną funkcję
            result = None
            error = None
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                error = e
                raise
            finally:
                # Oblicz czas
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                # Określ rozmiar odpowiedzi
                response_size = 0
                
                # Z wyniku funkcji
                if result is not None:
                    if isinstance(result, str):
                        response_size = len(result)
                    elif isinstance(result, dict) and 'content' in result:
                        response_size = len(str(result['content']))
                    elif hasattr(result, 'text'):
                        response_size = len(result.text)
                
                # Z argumentów dla handle_api_response
                if function_name == "handle_api_response" and len(args) > 2:
                    if isinstance(args[2], str):
                        response_size = len(args[2])
                
                # Z atrybutów dla APICallThread.run
                if function_name == "run" and hasattr(args[0], 'response_content') and args[0].response_content:
                    response_size = len(args[0].response_content)
                
                # Status i zapis
                status = "SUCCESS" if error is None else f"ERROR: {type(error).__name__}"
                log_info(f"📊 MODEL RESPONSE TIME | {start_dt} | {model_name} | {status} | {elapsed_ms}ms | {response_size} bytes")
                
                # Zapis do metryk
                ModelResponseMetrics.record(
                    timestamp=start_dt,
                    model=model_name,
                    function=function_name,
                    status=status,
                    elapsed_ms=elapsed_ms,
                    response_size=response_size
                )
            
            return result
            
        return direct_wrapper
    
    # Przypadek gdy używany z nawiasami @measure_response_time()
    def decorator(inner_func):
        @functools.wraps(inner_func)
        def wrapper(*args, **kwargs):
            # Pomiń pomiar jeśli wyłączony
            if not measure_result:
                return inner_func(*args, **kwargs)
                
            # Początek pomiaru
            start_time = time.time()
            start_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            function_name = inner_func.__name__
            
            # Identyfikacja modelu
            model_name = "unknown"
            
            # Pobierz z określonej pozycji jeśli podano
            if model_arg_position is not None and len(args) > model_arg_position:
                model_name = args[model_arg_position]
            # Rozpoznaj na podstawie funkcji
            elif function_name == "handle_api_response" and len(args) > 1:
                model_name = args[1]  # args[0]=self, args[1]=model_name
            elif function_name == "start_api_thread" and len(args) > 1:
                # args[0]=self, args[1]=prompt, args[2]=model_name (opcjonalnie)
                if len(args) > 2 and args[2]:
                    model_name = args[2]
                else:
                    model_name = kwargs.get('model_name', "unknown")
            elif function_name == "run" and hasattr(args[0], 'model_name'):
                # Dla APICallThread.run()
                model_name = args[0].model_name
            # Pobierz z kwargs
            elif 'model_name' in kwargs:
                model_name = kwargs['model_name']
            elif 'model' in kwargs:
                model_name = kwargs['model']
            
            # Uprość nazwę modelu
            if isinstance(model_name, str) and '/' in model_name:
                model_name = model_name.split('/')[-1]
            
            # Wykonaj oryginalną funkcję
            result = None
            error = None
            try:
                result = inner_func(*args, **kwargs)
            except Exception as e:
                error = e
                raise
            finally:
                # Oblicz czas
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                # Określ rozmiar odpowiedzi
                response_size = 0
                
                # Z wyniku funkcji
                if result is not None:
                    if isinstance(result, str):
                        response_size = len(result)
                    elif isinstance(result, dict) and 'content' in result:
                        response_size = len(str(result['content']))
                    elif hasattr(result, 'text'):
                        response_size = len(result.text)
                
                # Z argumentów dla handle_api_response
                if function_name == "handle_api_response" and len(args) > 2:
                    if isinstance(args[2], str):
                        response_size = len(args[2])
                
                # Z atrybutów dla APICallThread.run
                if function_name == "run" and hasattr(args[0], 'response_content') and args[0].response_content:
                    response_size = len(args[0].response_content)
                
                # Status i zapis
                status = "SUCCESS" if error is None else f"ERROR: {type(error).__name__}"
                log_info(f"📊 MODEL RESPONSE TIME | {start_dt} | {model_name} | {status} | {elapsed_ms}ms | {response_size} bytes")
                
                # Zapis do metryk
                ModelResponseMetrics.record(
                    timestamp=start_dt,
                    model=model_name,
                    function=function_name,
                    status=status,
                    elapsed_ms=elapsed_ms,
                    response_size=response_size
                )
            
            return result
            
        return wrapper
    return decorator

class ModelResponseMetrics:
    _metrics_file = "model_metrics.jsonl"
    _metrics = []
    _is_initialized = False
    
    @classmethod
    def initialize(cls, metrics_file=None):
        """Inicjalizuje system metryk"""
        if metrics_file:
            cls._metrics_file = metrics_file
            
        # Utwórz katalog dla pliku metryk jeśli nie istnieje
        metrics_dir = os.path.dirname(cls._metrics_file)
        if metrics_dir and not os.path.exists(metrics_dir):
            os.makedirs(metrics_dir, exist_ok=True)
            
        cls._is_initialized = True
    
    @classmethod
    def record(cls, timestamp, model, function, status, elapsed_ms, response_size):
        """Zapisuje pojedynczą metrykę"""
        metric = {
            "timestamp": timestamp,
            "model": model,
            "function": function,
            "status": "SUCCESS" if "ERROR" not in status else "ERROR",
            "elapsed_ms": elapsed_ms,
            "response_size": response_size
        }
        
        # Dodaj do pamięci
        cls._metrics.append(metric)
        
        # Zapisz do pliku
        try:
            with open(cls._metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metric) + "\n")
        except Exception as e:
            log_error(f"Error saving metric: {str(e)}")
    
    @classmethod
    def get_statistics(cls):
        """Zwraca podstawowe statystyki"""
        if not cls._metrics:
            return {"count": 0}
            
        by_model = {}
        by_function = {}
        
        for m in cls._metrics:
            # Statystyki według modelu
            model = m["model"]
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(m["elapsed_ms"])
            
            # Statystyki według funkcji
            function = m["function"]
            if function not in by_function:
                by_function[function] = []
            by_function[function].append(m["elapsed_ms"])
        
        stats = {
            "count": len(cls._metrics), 
            "by_model": {},
            "by_function": {}
        }
        
        # Statystyki według modelu
        for model, times in by_model.items():
            stats["by_model"][model] = {
                "count": len(times),
                "avg_ms": sum(times) / len(times),
                "min_ms": min(times),
                "max_ms": max(times)
            }
        
        # Statystyki według funkcji
        for function, times in by_function.items():
            stats["by_function"][function] = {
                "count": len(times),
                "avg_ms": sum(times) / len(times),
                "min_ms": min(times),
                "max_ms": max(times)
            }
        
        return stats