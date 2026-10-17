import os
import sys
import logging
from flask import Flask, request, jsonify, render_template
from db import (
    init_db,
    check_db_health,
    get_all_students,
    get_student_by_id,
    create_student,
    update_student,
    delete_student,
    DatabaseConfigError,
    DatabaseConnectionError,
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
    get_masked_db_url
)

# Initialize Flask application
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("student_app")


def serialize_student(student: dict) -> dict:
    """Format student dictionary for JSON serialization."""
    if not student:
        return {}
    res = dict(student)
    if res.get("created_at") and hasattr(res["created_at"], "isoformat"):
        res["created_at"] = res["created_at"].isoformat()
    return res


# ------------------------------------------------------------------------------
# Frontend Page
# ------------------------------------------------------------------------------
@app.route("/")
def index():
    """Serves the main single-page application dashboard."""
    return render_template("index.html")


# ------------------------------------------------------------------------------
# Health Check Endpoint
# ------------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Check application and PostgreSQL database connectivity.
    Reports connection status, PostgreSQL version, and total records.
    """
    health = check_db_health()
    if health.get("status") == "healthy":
        return jsonify(health), 200
    elif health.get("status") == "unconfigured":
        return jsonify(health), 503
    else:
        return jsonify(health), 503


# ------------------------------------------------------------------------------
# Student Records API Endpoints
# ------------------------------------------------------------------------------
@app.route("/api/students", methods=["GET"])
def list_students():
    """
    Retrieve all students.
    Supports optional search parameter: /api/students?search=<term>
    Searches across name, register_number, and department.
    """
    search_query = request.args.get("search", default=None, type=str)
    try:
        students = get_all_students(search_query)
        serialized = [serialize_student(s) for s in students]
        return jsonify({
            "count": len(serialized),
            "students": serialized,
            "search_query": search_query
        }), 200
    except (DatabaseConfigError, DatabaseConnectionError) as e:
        logger.error(f"Database error in list_students: {e}")
        return jsonify({
            "error": "Database connection error",
            "details": str(e)
        }), 503
    except Exception as e:
        logger.error(f"Unexpected error in list_students: {e}")
        return jsonify({
            "error": "Failed to retrieve student records",
            "details": str(e)
        }), 500


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id: int):
    """Retrieve details of a single student by ID."""
    try:
        student = get_student_by_id(student_id)
        return jsonify({
            "student": serialize_student(student)
        }), 200
    except RecordNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except (DatabaseConfigError, DatabaseConnectionError) as e:
        return jsonify({
            "error": "Database connection error",
            "details": str(e)
        }), 503
    except Exception as e:
        logger.error(f"Unexpected error in get_student: {e}")
        return jsonify({
            "error": "Failed to fetch student record",
            "details": str(e)
        }), 500


@app.route("/api/students", methods=["POST"])
def add_student():
    """
    Create a new student record.
    Expects JSON: {name, register_number, department, email, academic_year}
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "error": "Invalid request body. Expected JSON object with student details."
        }), 400

    try:
        new_student = create_student(data)
        return jsonify({
            "message": "Student record created successfully.",
            "student": serialize_student(new_student)
        }), 201
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except DuplicateRecordError as e:
        return jsonify({"error": str(e)}), 409
    except (DatabaseConfigError, DatabaseConnectionError) as e:
        return jsonify({
            "error": "Database connection error",
            "details": str(e)
        }), 503
    except Exception as e:
        logger.error(f"Unexpected error in add_student: {e}")
        return jsonify({
            "error": "Failed to create student record",
            "details": str(e)
        }), 500


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def edit_student(student_id: int):
    """
    Update an existing student record by ID.
    Expects JSON: {name, register_number, department, email, academic_year}
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "error": "Invalid request body. Expected JSON object with updated details."
        }), 400

    try:
        updated = update_student(student_id, data)
        return jsonify({
            "message": "Student record updated successfully.",
            "student": serialize_student(updated)
        }), 200
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except RecordNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except DuplicateRecordError as e:
        return jsonify({"error": str(e)}), 409
    except (DatabaseConfigError, DatabaseConnectionError) as e:
        return jsonify({
            "error": "Database connection error",
            "details": str(e)
        }), 503
    except Exception as e:
        logger.error(f"Unexpected error in edit_student: {e}")
        return jsonify({
            "error": "Failed to update student record",
            "details": str(e)
        }), 500


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def remove_student(student_id: int):
    """Delete a student record by ID."""
    try:
        deleted = delete_student(student_id)
        return jsonify({
            "message": f"Student '{deleted['name']}' (Register No: {deleted['register_number']}) was successfully deleted.",
            "deleted_id": student_id
        }), 200
    except RecordNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except (DatabaseConfigError, DatabaseConnectionError) as e:
        return jsonify({
            "error": "Database connection error",
            "details": str(e)
        }), 503
    except Exception as e:
        logger.error(f"Unexpected error in remove_student: {e}")
        return jsonify({
            "error": "Failed to delete student record",
            "details": str(e)
        }), 500


# ------------------------------------------------------------------------------
# Generic Error Handlers
# ------------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Resource or endpoint not found"}), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------------------
# Server Startup
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("  Student Records System - Nostromo PostgreSQL Test Harness")
    print("=" * 70)
    print(f"  Configured Database URI: {get_masked_db_url()}")
    print("  Attempting initial schema verification...")
    
    # Attempt to initialize schema
    success, msg = init_db()
    if success:
        print("  [SUCCESS] PostgreSQL schema initialized successfully.")
    else:
        print(f"  [NOTICE] Schema verification pending: {msg}")
        print("  You can update your .env file at any time without changing code.")
    print("=" * 70)
    print("  Starting Flask Web Server on http://127.0.0.1:5000 ...")
    print("=" * 70)
    
    # Run development server
    app.run(host="0.0.0.0", port=5000, debug=True)
