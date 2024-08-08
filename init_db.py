import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

# Database connection details
EXTERNAL_DATABASE_URL = os.environ["EXTERNAL_DATABASE_URL"]


# Function to read SQL file
def read_sql_file(file_path):
    with open(file_path, "r") as file:
        return file.read()


# Function to execute SQL commands
def execute_sql(conn, sql_command):
    with conn.cursor() as cur:
        cur.execute(sql_command)
    conn.commit()


# Main function to initialize the database
def initialize_database():
    try:
        # Connect to the database
        conn = psycopg2.connect(EXTERNAL_DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        print("Successfully connected to the database.")

        # Read the init.sql file
        sql_commands = read_sql_file("init.sql")

        # Split the SQL commands
        commands = sql_commands.split(";")

        # Execute each command
        for command in commands:
            if command.strip() != "":
                execute_sql(conn, command)
                print(
                    f"Executed: {command[:50]}..."
                )  # Print first 50 chars of each command

        print("Database initialization completed successfully.")
        if conn:
            conn.close()
            print("Database connection closed.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL or executing SQL: {error}")


initialize_database()
