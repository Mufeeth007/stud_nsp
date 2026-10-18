"""
Database Module for Student Records Management System
Handles PostgreSQL connection and automatic table creation using psycopg2.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_db_connection():
    """
    Creates and returns a connection to the PostgreSQL database.
    Reads configuration from environment variables.
    """
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "student_db")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    database_url = os.getenv("DATABASE_URL")

    # If DATABASE_URL is provided and DB_PASSWORD is default or empty, use DATABASE_URL
    if database_url and (not db_password or db_password == "your_password"):
        return psycopg2.connect(database_url)

    # Standard connection using individual environment variables
    return psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )


def init_db():
    """
    Initializes the database by creating the 'students' table if it doesn't already exist.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        register_number VARCHAR(50) UNIQUE NOT NULL,
        department VARCHAR(100) NOT NULL,
        email VARCHAR(120) NOT NULL,
        academic_year VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
        conn.commit()
        print("Database initialized successfully: 'students' table is ready.")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Warning/Error during database initialization: {e}")
        # Note: Do not crash immediately so helpful instructions can be displayed to user
        raise e
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # Test connection and table creation when run directly
    try:
        print("Testing database connection and initializing table...")
        init_db()
        print("Success!")
    except Exception as err:
        print(f"Initialization failed: {err}")
