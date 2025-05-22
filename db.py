import mysql.connector
from mysql.connector import Error
import time

def connect_db(max_retries=3, retry_delay=1):
    
  retries = 0
    
    while retries < max_retries:
        try:
            connection = mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                password="marione123",
                database="calendar_of_events"
            )
            if connection.is_connected():
                print(f"Connected to the database (attempt {retries + 1})")
                return connection
        except Error as e:
            print(f"Error connecting to MySQL database (attempt {retries + 1}): {e}")
            retries += 1
            
            if retries < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    print("Failed to connect to database after multiple attempts")
    return None

def execute_query(query, params=None):
    
  connection = None
    cursor = None
    result = None
    
    try:
        connection = connect_db()
        if connection is None:
            return None
            
        cursor = connection.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        # Check if query is SELECT
        if query.strip().upper().startswith("SELECT"):
            result = cursor.fetchall()
        else:
            connection.commit()
            result = cursor.rowcount
            
    except Error as e:
        print(f"Error executing query: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            
    return result
