import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

def log_ai_interaction(request: str, response: str, model_name: str = None,
                       user_id: str = None, status_code: int = None,
                       latency_ms: int = None):
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        if conn.is_connected():
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO ai_logs (request, response, model_name, user_id, status_code, latency_ms)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(insert_query, (request, response, model_name, user_id, status_code, latency_ms))
            conn.commit()

    except Error as e:
        print("Błąd podczas zapisu do bazy:", e)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

def test_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        if conn.is_connected():
            print("✅ Połączenie z bazą danych działa.")
            cursor = conn.cursor()
            cursor.execute("SELECT NOW()")  # przykładowe zapytanie testowe
            result = cursor.fetchone()
            print(f"🕒 Baza zwróciła aktualny czas: {result[0]}")
        else:
            print("❌ Nie udało się połączyć z bazą danych.")

    except Error as e:
        print(f"❌ Błąd połączenia z bazą danych: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    
    log_ai_interaction(
                            request="Test_tekstu_pytania",
                            response="Test_tekstu_odpowiedzi",
                            model_name="Model_testowy",
                            user_id=None,
                            status_code=None,
                            latency_ms=None
                        )
    print("Zapisano do bazy przeszedł")
    test_db_connection()


'''CREATE TABLE ai_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    request TEXT NOT NULL,
    response TEXT NOT NULL,
    model_name VARCHAR(255),
    user_id VARCHAR(255),
    status_code INT,
    latency_ms INT
);'''