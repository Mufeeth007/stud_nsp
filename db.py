import os
import re
import sys
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("nostromo_db")

# Regex pattern for validating email addresses
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


# ------------------------------------------------------------------------------
# Custom Exceptions
# ------------------------------------------------------------------------------
class DatabaseConfigError(Exception):
    """Raised when DATABASE_URL is not set or improperly formatted in .env."""
    pass


class DatabaseConnectionError(Exception):
    """Raised when connecting to PostgreSQL fails."""
    pass


class DuplicateRecordError(Exception):
    """Raised when a unique constraint is violated (e.g., duplicate register_number)."""
    pass


class RecordNotFoundError(Exception):
    """Raised when a requested record is not found."""
    pass


class ValidationError(Exception):
    """Raised when input data validation fails."""
    pass


# ------------------------------------------------------------------------------
# Utility Helpers
# ------------------------------------------------------------------------------
def get_database_url() -> str:
    """
    Retrieve and validate the PostgreSQL database URI from the environment.
    Does NOT assume localhost or fallback to SQLite.
    """
    url = os.getenv("DATABASE_URL")
    if not url or not url.strip():
        raise DatabaseConfigError(
            "DATABASE_URL is not configured in your .env file.\n"
            "Please copy the PostgreSQL connection URI from your Nostromo Android app "
            "and set DATABASE_URL=<your-uri> in the .env file."
        )
    return url.strip()


def get_masked_db_url(raw_url: str = None) -> str:
    """
    Returns a masked version of the connection URI for safe display/logging.
    Never exposes passwords.
    """
    try:
        if not raw_url:
            raw_url = os.getenv("DATABASE_URL", "")
        if not raw_url:
            return "NOT CONFIGURED"
        
        parsed = urlparse(raw_url)
        netloc = ""
        if parsed.username:
            netloc += parsed.username
            if parsed.password:
                netloc += ":****"
            netloc += "@"
        if parsed.hostname:
            netloc += parsed.hostname
        if parsed.port:
            netloc += f":{parsed.port}"
        
        masked = f"{parsed.scheme}://{netloc}{parsed.path}"
        if parsed.query:
            masked += f"?{parsed.query}"
        return masked
    except Exception:
        return "postgresql://***:****@***:***/***"


def get_troubleshooting_guidance(error_msg: str, raw_url: str = None) -> list:
    """
    Generate helpful troubleshooting steps based on the connection failure.
    Tailored specifically for testing PostgreSQL on Nostromo (Android).
    """
    masked_url = get_masked_db_url(raw_url)
    steps = [
        f"Configured URI: {masked_url}",
        "Verify Nostromo Android App: Ensure the PostgreSQL service is active and running inside Nostromo.",
        "Check Network Connectivity: If connecting via Wi-Fi, ensure your PC and Android phone are on the exact same Wi-Fi network and AP isolation is disabled on your router.",
        "Check USB / ADB Port Forwarding: If using 127.0.0.1 or localhost over USB cable, verify that ADB forward was executed: `adb forward tcp:5432 tcp:5432` (adjust port if Nostromo uses a custom port).",
        "Check Firewall: Ensure Windows Defender Firewall or any security software allows inbound/outbound TCP traffic on the PostgreSQL port.",
        "Verify Credentials: Check if the username, password, and database name in the Nostromo URI match the running PostgreSQL instance.",
        f"Raw PostgreSQL Error: {error_msg}"
    ]
    return steps


# ------------------------------------------------------------------------------
# Connection & Table Initialization
# ------------------------------------------------------------------------------
def get_db_connection():
    """
    Establish a connection to the PostgreSQL database using DATABASE_URL.
    Raises DatabaseConfigError or DatabaseConnectionError with actionable details.
    """
    db_url = get_database_url()
    try:
        # Connect with psycopg2
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.OperationalError as e:
        error_msg = str(e).strip()
        logger.error("=" * 70)
        logger.error("[NOSTROMO DB ERROR] Failed to connect to PostgreSQL engine!")
        for step in get_troubleshooting_guidance(error_msg, db_url):
            logger.error(f"  -> {step}")
        logger.error("=" * 70)
        raise DatabaseConnectionError(
            f"Could not connect to PostgreSQL database provided by Nostromo: {error_msg}"
        ) from e
    except Exception as e:
        logger.error(f"[NOSTROMO DB ERROR] Unexpected connection error: {e}")
        raise DatabaseConnectionError(f"Unexpected connection error: {e}") from e


def init_db():
    """
    Automatically creates the 'students' table and required indexes if they do not exist.
    Called on server startup.
    """
    logger.info("Initializing PostgreSQL database schema...")
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        name VARCHAR(150) NOT NULL,
        register_number VARCHAR(50) NOT NULL UNIQUE,
        department VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL,
        academic_year VARCHAR(50) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_students_reg_num ON students(register_number);
    CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
            conn.commit()
        logger.info("[NOSTROMO DB] Table 'students' and indexes verified successfully.")
        return True, "Table 'students' is ready."
    except (DatabaseConfigError, DatabaseConnectionError) as e:
        logger.warning(f"[NOSTROMO DB] Schema initialization deferred: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"[NOSTROMO DB] Failed to create table: {e}")
        return False, str(e)


def check_db_health() -> dict:
    """
    Check the current health of the database connection.
    Returns status dict with PostgreSQL version and student count if reachable.
    """
    try:
        db_url = get_database_url()
        masked_url = get_masked_db_url(db_url)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                pg_version_row = cur.fetchone()
                pg_version = pg_version_row['version'] if pg_version_row else "Unknown"

                cur.execute("SELECT COUNT(*) AS total FROM students;")
                count_row = cur.fetchone()
                total_students = count_row['total'] if count_row else 0

        return {
            "status": "healthy",
            "database": "connected",
            "database_url": masked_url,
            "engine": "PostgreSQL (Project Nostromo)",
            "postgresql_version": pg_version,
            "total_students": total_students
        }
    except DatabaseConfigError as e:
        return {
            "status": "unconfigured",
            "database": "disconnected",
            "error": str(e),
            "troubleshooting": [
                "Copy your PostgreSQL URI from Nostromo into .env file:",
                "DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>"
            ]
        }
    except DatabaseConnectionError as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "troubleshooting": get_troubleshooting_guidance(str(e))
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "troubleshooting": get_troubleshooting_guidance(str(e))
        }


# ------------------------------------------------------------------------------
# Data Validation
# ------------------------------------------------------------------------------
def validate_student_payload(data: dict) -> dict:
    """
    Validates and cleans input data for student creation and updates.
    Ensures required fields are present, trimmed, and email is correctly formatted.
    """
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a valid JSON object.")

    required_fields = ["name", "register_number", "department", "email", "academic_year"]
    cleaned = {}

    for field in required_fields:
        val = data.get(field)
        if val is None or not str(val).strip():
            field_display = field.replace("_", " ").title()
            raise ValidationError(f"'{field_display}' is required and cannot be empty.")
        cleaned[field] = str(val).strip()

    # Validate email format
    if not EMAIL_REGEX.match(cleaned["email"]):
        raise ValidationError(f"'{cleaned['email']}' is not a valid email address.")

    # Sanity checks on length
    if len(cleaned["name"]) > 150:
        raise ValidationError("Student name must not exceed 150 characters.")
    if len(cleaned["register_number"]) > 50:
        raise ValidationError("Register number must not exceed 50 characters.")
    if len(cleaned["department"]) > 100:
        raise ValidationError("Department must not exceed 100 characters.")
    if len(cleaned["email"]) > 255:
        raise ValidationError("Email address must not exceed 255 characters.")
    if len(cleaned["academic_year"]) > 50:
        raise ValidationError("Academic year must not exceed 50 characters.")

    return cleaned


# ------------------------------------------------------------------------------
# CRUD Operations
# ------------------------------------------------------------------------------
def get_all_students(search_query: str = None) -> list:
    """
    Retrieve all students, optionally filtered by name or register number.
    Ordered by ID descending.
    """
    query = """
        SELECT id, name, register_number, department, email, academic_year, created_at
        FROM students
    """
    params = []

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        query += " WHERE name ILIKE %s OR register_number ILIKE %s OR department ILIKE %s"
        params.extend([term, term, term])

    query += " ORDER BY id DESC;"

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def get_student_by_id(student_id: int) -> dict:
    """
    Retrieve a single student by primary key ID.
    Raises RecordNotFoundError if record does not exist.
    """
    query = """
        SELECT id, name, register_number, department, email, academic_year, created_at
        FROM students
        WHERE id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (student_id,))
            row = cur.fetchone()
            if not row:
                raise RecordNotFoundError(f"Student with ID {student_id} not found.")
            return dict(row)


def create_student(data: dict) -> dict:
    """
    Insert a new student into PostgreSQL using parameterized query.
    Handles duplicate register numbers via UniqueViolation.
    """
    cleaned = validate_student_payload(data)

    insert_sql = """
        INSERT INTO students (name, register_number, department, email, academic_year)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name, register_number, department, email, academic_year, created_at;
    """
    params = (
        cleaned["name"],
        cleaned["register_number"],
        cleaned["department"],
        cleaned["email"],
        cleaned["academic_year"],
    )

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(insert_sql, params)
                new_student = cur.fetchone()
            conn.commit()
            return dict(new_student)
    except psycopg2.IntegrityError as e:
        # Check for unique constraint violation (PostgreSQL pgcode 23505)
        if getattr(e, 'pgcode', None) == '23505' or "duplicate key" in str(e).lower():
            raise DuplicateRecordError(
                f"A student with register number '{cleaned['register_number']}' already exists."
            ) from e
        raise


def update_student(student_id: int, data: dict) -> dict:
    """
    Update an existing student record.
    Raises RecordNotFoundError if ID is missing, or DuplicateRecordError on register number collision.
    """
    cleaned = validate_student_payload(data)

    # Check if student exists
    get_student_by_id(student_id)

    update_sql = """
        UPDATE students
        SET name = %s,
            register_number = %s,
            department = %s,
            email = %s,
            academic_year = %s
        WHERE id = %s
        RETURNING id, name, register_number, department, email, academic_year, created_at;
    """
    params = (
        cleaned["name"],
        cleaned["register_number"],
        cleaned["department"],
        cleaned["email"],
        cleaned["academic_year"],
        student_id,
    )

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(update_sql, params)
                updated_row = cur.fetchone()
            conn.commit()
            if not updated_row:
                raise RecordNotFoundError(f"Student with ID {student_id} not found.")
            return dict(updated_row)
    except psycopg2.IntegrityError as e:
        if getattr(e, 'pgcode', None) == '23505' or "duplicate key" in str(e).lower():
            raise DuplicateRecordError(
                f"Another student with register number '{cleaned['register_number']}' already exists."
            ) from e
        raise


def delete_student(student_id: int) -> dict:
    """
    Delete a student record by ID.
    Raises RecordNotFoundError if record does not exist.
    """
    # Verify existence first
    existing = get_student_by_id(student_id)

    delete_sql = "DELETE FROM students WHERE id = %s RETURNING id;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(delete_sql, (student_id,))
            deleted = cur.fetchone()
        conn.commit()
        if not deleted:
            raise RecordNotFoundError(f"Student with ID {student_id} not found.")
        return existing
