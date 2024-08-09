import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

try:
    # Establish the connection
    conn = psycopg2.connect(DATABASE_URL)
except psycopg2.Error as e:
    print(f"Error connecting to TimescaleDB: {e}")
    exit(1)

cursor = conn.cursor()

query = input()
while query != "exit":
    try:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        print([dict(zip(columns, row)) for row in cursor.fetchall()])
        # print(cursor.fetchall())
    except Exception as e:
        print(e)
    query = input()
