from logger_utils import log_info, log_error
import re
import requests
import os
from PyQt5.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv

load_dotenv()

class APICallThread(QThread):
    response_received = pyqtSignal(str, str)  # Sygnalizuje odebranie odpowiedzi (model, treść)
    error_occurred = pyqtSignal(str)         # Sygnalizuje błąd

    def __init__(self, url, headers, payload, model_name, provider):
        super().__init__()
        self.url = url
        self.headers = headers
        self.payload = payload
        self.model_name = model_name
        self.provider = provider

    def run(self):
        """Wysyła żądanie API i emituje odpowiedź."""
        # zapisz w logu treść wysyłanego promptu
        log_info(f"Wysyłam do API: {self.url} żądanie do modelu: {self.model_name} z treścią: {self.payload.get('messages', [{}])[0].get('content', 'No content')}")   
        try:
            if self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("API_KEY", ""))
                model = genai.GenerativeModel(self.model_name)
                try:
                    response = model.generate_content(self.payload["messages"][0]["content"])
                    response_content = response.text if hasattr(response, "text") else str(response)
                    self.response_received.emit(self.model_name, response_content)
                    log_info(f"Odpowiedź API: {response.text[:5000]}")
                except Exception as e:
                    error_msg = f"Gemini error: {e}"
                    self.error_occurred.emit(error_msg)
                    log_error(f"Błąd API Gemini: {error_msg}")
            else:
                response = requests.post(self.url, headers=self.headers, json=self.payload)
                if response.status_code == 200:
                    response_content = response.json().get("choices")[0].get("message").get("content", "No response")
                    self.response_received.emit(self.model_name, response_content)
                    log_info(f"Odpowiedź API: {response.text[:5000]}") # Logujemy tylko pierwsze 2000 znaków
                else:
                    error_msg = f"Error: {response.status_code} - {response.text}"
                    self.error_occurred.emit(error_msg)
                    log_error(f"Błąd API: {error_msg}")
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {e}")
            log_error(f"Błąd połaczenia: {e}")    