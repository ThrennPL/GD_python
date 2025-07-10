import psycopg2
from psycopg2 import sql
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def log_ai_interaction(request: str, response: str, model_name: str = None,
                       user_id: str = None, status_code: int = None,
                       latency_ms: int = None):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 5432)),  # domyślny port PostgreSQL to 5432",
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        cursor = conn.cursor()

        insert_query = sql.SQL("""
            INSERT INTO ai_logs (request, response, model_name, user_id, status_code, latency_ms)
            VALUES (%s, %s, %s, %s, %s, %s)
        """)

        cursor.execute(insert_query, (request, response, model_name, user_id, status_code, latency_ms))
        conn.commit()

    except Exception as e:
        print("Błąd podczas zapisu do bazy:", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    import sys
    request = sys.argv[1]
    response = sys.argv[2]
    model_name = sys.argv[3]
    log_ai_interaction(request, response, model_name)
    #test_db_connection()

'''CREATE TABLE ai_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    request TEXT NOT NULL,
    response TEXT NOT NULL,
    model_name VARCHAR(255),
    user_id VARCHAR(255),  -- jeśli potrzebujesz info o użytkowniku
    status_code INTEGER,    -- np. 200, 400, 500
    latency_ms INTEGER      -- czas odpowiedzi w milisekundach
);'''

'''DB_PROVIDER=mysql
DB_PROVIDER=postgresql
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD='''