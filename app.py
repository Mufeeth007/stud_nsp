"""
Student Records Management System - Flask Backend
REST API endpoints for managing student records with PostgreSQL.
"""

import os
import re
from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.errors import UniqueViolation

from db import get_db_connection, init_db

app = Flask(__name__)

# Basic email regex validation pattern
EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


def validate_student_data(data, is_update=False):
    """
    Validates student payload fields.
    Returns (is_valid, error_message, cleaned_data).
    """
    if not isinstance(data, dict):
        return False, "Invalid request payload. Expected JSON object.", None

    name = str(data.get("name", "")).strip()
    register_number = str(data.get("register_number", "")).strip()
    department = str(data.get("department", "")).strip()
    email = str(data.get("email", "")).strip()
    academic_year = str(data.get("academic_year", "")).strip()

    # Validate required fields
    if not name:
        return False, "Student Name is required.", None
    if len(name) > 100:
        return False, "Student Name cannot exceed 100 characters.", None

    if not register_number:
        return False, "Register Number is required.", None
    if len(register_number) > 50:
        return False, "Register Number cannot exceed 50 characters.", None

    if not department:
        return False, "Department is required.", None
    if len(department) > 100:
        return False, "Department cannot exceed 100 characters.", None

    if not email:
        return False, "Email Address is required.", None
    if not re.match(EMAIL_REGEX, email):
        return False, "Please enter a valid email address (e.g., student@example.com).", None
    if len(email) > 120:
        return False, "Email Address cannot exceed 120 characters.", None

    if not academic_year:
        return False, "Academic Year is required.", None
    if len(academic_year) > 50:
        return False, "Academic Year cannot exceed 50 characters.", None

    cleaned_data = {
        "name": name,
        "register_number": register_number,
        "department": department,
        "email": email,
        "academic_year": academic_year
    }

    return True, None, cleaned_data



_db_initialized = False


def ensure_db_initialized():
    """Ensures database tables exist without crashing if connection is temporarily unavailable."""
    global _db_initialized
    if not _db_initialized:
        try:
            init_db()
            _db_initialized = True
        except Exception as e:
            print(f"[Notice] Database initialization will be retried on next request: {e}")


@app.before_request
def before_request_check():
    """Verifies database is initialized before handling incoming request."""
    ensure_db_initialized()


# ---------------------------------------------------------
# Web Routes
# ---------------------------------------------------------
@app.route("/")
def index():
    """Serves the main single-page application dashboard."""
    return render_template("index.html")



# ---------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------

@app.route("/api/students", methods=["GET"])
def get_students():
    """
    GET /api/students
    Retrieve all students from the database.
    Supports optional search filter: /api/students?search=keyword
    """
    search_query = request.args.get("search", "").strip()
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if search_query:
                # Search by student name OR register number (case-insensitive)
                query = """
                SELECT id, name, register_number, department, email, academic_year,
                       to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
                FROM students
                WHERE name ILIKE %s OR register_number ILIKE %s
                ORDER BY id ASC;
                """
                search_param = f"%{search_query}%"
                cur.execute(query, (search_param, search_param))
            else:
                query = """
                SELECT id, name, register_number, department, email, academic_year,
                       to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
                FROM students
                ORDER BY id ASC;
                """
                cur.execute(query)

            students = cur.fetchall()

        return jsonify({
            "success": True,
            "students": students,
            "total": len(students)
        }), 200

    except psycopg2.OperationalError as e:
        return jsonify({
            "success": False,
            "error": "Database connection error. Please make sure PostgreSQL is running and .env is configured correctly."
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An error occurred while fetching students: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    """
    GET /api/students/<id>
    Retrieve a single student record by primary key ID.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
            SELECT id, name, register_number, department, email, academic_year,
                   to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
            FROM students
            WHERE id = %s;
            """
            cur.execute(query, (student_id,))
            student = cur.fetchone()

        if not student:
            return jsonify({
                "success": False,
                "error": f"Student with ID {student_id} not found."
            }), 404

        return jsonify({
            "success": True,
            "student": student
        }), 200

    except psycopg2.OperationalError:
        return jsonify({
            "success": False,
            "error": "Database connection error. Please make sure PostgreSQL is running."
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An error occurred while fetching student details: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/students", methods=["POST"])
def add_student():
    """
    POST /api/students
    Add a new student record to the database.
    """
    data = request.get_json(silent=True) or request.form.to_dict()
    is_valid, error_msg, cleaned = validate_student_data(data)
    if not is_valid:
        return jsonify({"success": False, "error": error_msg}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check for duplicate register number
            check_sql = "SELECT id FROM students WHERE register_number = %s;"
            cur.execute(check_sql, (cleaned["register_number"],))
            existing = cur.fetchone()
            if existing:
                return jsonify({
                    "success": False,
                    "error": f"A student with Register Number '{cleaned['register_number']}' already exists."
                }), 409

            # Insert new student record
            insert_sql = """
            INSERT INTO students (name, register_number, department, email, academic_year)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, register_number, department, email, academic_year,
                      to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at;
            """
            cur.execute(insert_sql, (
                cleaned["name"],
                cleaned["register_number"],
                cleaned["department"],
                cleaned["email"],
                cleaned["academic_year"]
            ))
            new_student = cur.fetchone()

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student record added successfully!",
            "student": new_student
        }), 201

    except UniqueViolation:
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "error": f"A student with Register Number '{cleaned['register_number']}' already exists."
        }), 409
    except psycopg2.OperationalError:
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "error": "Database connection error. Please make sure PostgreSQL is running."
        }), 500
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "error": f"Failed to add student: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """
    PUT /api/students/<id>
    Update an existing student record by primary key ID.
    """
    data = request.get_json(silent=True) or request.form.to_dict()
    is_valid, error_msg, cleaned = validate_student_data(data, is_update=True)
    if not is_valid:
        return jsonify({"success": False, "error": error_msg}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify student exists
            cur.execute("SELECT id FROM students WHERE id = %s;", (student_id,))
            student_exists = cur.fetchone()
            if not student_exists:
                return jsonify({
                    "success": False,
                    "error": f"Student with ID {student_id} not found."
                }), 404

            # Check if updated register number belongs to another student
            check_sql = "SELECT id FROM students WHERE register_number = %s AND id != %s;"
            cur.execute(check_sql, (cleaned["register_number"], student_id))
            duplicate = cur.fetchone()
            if duplicate:
                return jsonify({
                    "success": False,
                    "error": f"A different student already has Register Number '{cleaned['register_number']}'."
                }), 409

            # Update record
            update_sql = """
            UPDATE students
            SET name = %s,
                register_number = %s,
                department = %s,
                email = %s,
                academic_year = %s
            WHERE id = %s
            RETURNING id, name, register_number, department, email, academic_year,
                      to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at;
            """
            cur.execute(update_sql, (
                cleaned["name"],
                cleaned["register_number"],
                cleaned["department"],
                cleaned["email"],
                cleaned["academic_year"],
                student_id
            ))
            updated_student = cur.fetchone()

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student record updated successfully!",
            "student": updated_student
        }), 200

    except UniqueViolation:
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "error": f"A student with Register Number '{cleaned['register_number']}' already exists."
        }), 409
    except psycopg2.OperationalError:
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "error": "Database connection error. Please make sure PostgreSQL is running."
        }), 500
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "error": f"Failed to update student: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    """
    DELETE /api/students/<id>
    Delete a student record by primary key ID.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE id = %s RETURNING id;", (student_id,))
            deleted = cur.fetchone()

        if not deleted:
            return jsonify({
                "success": False,
                "error": f"Student with ID {student_id} not found."
            }), 404

        conn.commit()

        return jsonify({
            "success": True,
            "message": f"Student record #{student_id} was successfully deleted."
        }), 200

    except psycopg2.OperationalError:
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "error": "Database connection error. Please make sure PostgreSQL is running."
        }), 500
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "error": f"Failed to delete student: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------
# Application Startup
# ---------------------------------------------------------
if __name__ == "__main__":
    # Attempt automatic database & table initialization
    try:
        init_db()
    except Exception as err:
        print("\n" + "=" * 60)
        print("NOTE: Database initialization could not be completed.")
        print(f"Detail: {err}")
        print("Please ensure PostgreSQL is installed, running, and student_db is created.")
        print("Update your .env file with your PostgreSQL password.")
        print("=" * 60 + "\n")

    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Student Records Management System on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
