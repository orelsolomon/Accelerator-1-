import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',  # e.g., 'localhost' or the IP address
            user='isorelsu_user123',  # e.g., 'root'
            password='Rotem123456789!',
            database='isorelsu_SmartSip'
        )

        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def get_result_from_query(connection, query_string, *args):
    cursor = connection.cursor()
    cursor.execute(query_string, args)
    record = cursor.fetchone()
    if record:
        return record
    return None

def get_single_result_from_query(connection, query_string, *args):
    result = get_result_from_query(connection, query_string, *args)
    if result:
        return result[0]
    return None
