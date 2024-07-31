import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

HOST = "localhost"
PORT = "5432"
DB = "stocksdb"
USER = "postgres"
PASSWORD = os.environ["POSTGRES_PASSWORD"]

try:
    # Establish the connection
    conn = psycopg2.connect(
        host=HOST, port=PORT, database=DB, user=USER, password=PASSWORD
    )
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
