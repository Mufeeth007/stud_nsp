"""
Database Module for Student Records Management System
Handles PostgreSQL connection and automatic table creation using psycopg2.
Supports both DATABASE_URL (Nostromo / Cloud) and individual environment variables.
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
    Supports DATABASE_URL (Nostromo / production environments)
    as well as individual DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.
    """
    database_url = os.getenv("DATABASE_URL")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "student_db")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")

    # Priority 1: DATABASE_URL (provided by Nostromo or cloud hosting)
    if database_url:
        try:
            return psycopg2.connect(database_url)
        except Exception as e:
            # If DATABASE_URL fails, attempt fallback to individual variables
            if db_password and db_password != "your_password":
                return psycopg2.connect(
                    host=db_host,
                    port=db_port,
                    dbname=db_name,
                    user=db_user,
                    password=db_password
                )
            raise e

    # Priority 2: Individual connection settings
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
