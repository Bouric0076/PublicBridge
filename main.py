import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables from environment
USER = os.getenv("DB_USER") 
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT", "5432")
DBNAME = os.getenv("DB_NAME", "postgres")

# Connect to the database
try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        sslmode='require'
    )
    print("Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Example query
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print("Current Time:", result)
    
    # Test database tables
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;")
    tables = cursor.fetchall()
    print("Sample tables:", tables)

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Connection closed.")

except Exception as e:
    print(f"Failed to connect: {e}")
    print(f"Connection details: user={USER}, host={HOST}, port={PORT}, dbname={DBNAME}")