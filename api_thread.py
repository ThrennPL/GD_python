import re
import requests
from PyQt5.QtCore import QThread, pyqtSignal

class APICallThread(QThread):
    response_received = pyqtSignal(str, str)  # Sygnalizuje odebranie odpowiedzi (model, treść)
    error_occurred = pyqtSignal(str)         # Sygnalizuje błąd

    def __init__(self, url, headers, payload, model_name):
        super().__init__()
        self.url = url
        self.headers = headers
        self.payload = payload
        self.model_name = model_name

    def run(self):
        """Wysyła żądanie API i emituje odpowiedź."""
        try:
            response = requests.post(self.url, headers=self.headers, json=self.payload)
            if response.status_code == 200:
                response_content = response.json().get("choices")[0].get("message").get("content", "No response")
                self.response_received.emit(self.model_name, response_content)
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                self.error_occurred.emit(error_msg)
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {e}")