import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

EXTERNAL_DATABASE_URL = os.environ["EXTERNAL_DATABASE_URL"]

try:
    # Establish the connection
    conn = psycopg2.connect(EXTERNAL_DATABASE_URL)
except psycopg2.Error as e:
    print(f"Error connecting to TimescaleDB: {e}")
    exit(1)

cursor = conn.cursor()

query = input()
while query != "exit":
    try:
        cursor.execute(query)
        print(cursor.fetchall())
    except Exception as e:
        print(e)
    query = input()
