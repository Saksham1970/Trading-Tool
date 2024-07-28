import psycopg2

from utils.config import HOST, PORT, DB, USER, PASSWORD
from psycopg2.extras import execute_values


try:
    # Establish the connection
    conn = psycopg2.connect(
        host=HOST, port=PORT, database=DB, user=USER, password=PASSWORD
    )
    cursor = conn.cursor()

except psycopg2.Error as e:
    print(f"Error connecting to TimescaleDB: {e}")
    exit(1)


def get_data(table, __dictionary=False, **kwargs):
    # Query to get data from a table
    where_clause = " AND ".join([f"{key} = %s" for key in kwargs.keys()])
    query = f"SELECT * FROM {table}"
    if where_clause:
        query += f" WHERE {where_clause}"

    if __dictionary:
        cursor.execute(query, tuple(kwargs.values()))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.execute(query, tuple(kwargs.values()))
    return cursor.fetchall()


def get_data_query(query, __dictionary=False):
    if __dictionary:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.execute(query)
    return cursor.fetchall()


def insert_data(table, **kwargs):
    # Query to insert data into a table
    keys = ", ".join(kwargs.keys())
    placeholders = ", ".join(["%s" for _ in kwargs])
    query = (
        f"INSERT INTO {table} ({keys}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
    )
    try:
        cursor.execute(query, tuple(kwargs.values()))
        cursor.connection.commit()
        return True
    except Exception as e:
        print(f"Error inserting data: {e}")
        return False


def is_present(table, **kwargs):
    data = get_data(table, **kwargs)
    return len(data) > 0


def bulk_insert_data(table, data):
    if data is None or data.empty:
        return True  # No data to insert

    # Get column names
    columns = list(data.columns)
    # Prepare the query
    query = (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s ON CONFLICT DO NOTHING"
    )

    try:
        # Convert DataFrame to a list of tuples
        values = [tuple(x) for x in data.to_numpy()]

        # Execute the query
        execute_values(cursor, query, values)

        cursor.connection.commit()
        return True
    except Exception as e:
        print(f"Error bulk inserting data: {e}")
        return False


def delete_data(table, **kwargs):
    # Query to delete data from a table
    where_clause = " AND ".join([f"{key} = %s" for key in kwargs.keys()])
    query = f"DELETE FROM {table} WHERE {where_clause}"
    try:
        cursor.execute(query, tuple(kwargs.values()))
        cursor.connection.commit()
        return True
    except Exception as e:
        print(f"Error deleting data: {e}")
        return False
