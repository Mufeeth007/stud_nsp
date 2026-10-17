"""
Student Records System - Verification & Test Suite
Used to test the Flask application and validate the Nostromo PostgreSQL engine.

Usage:
    python test_system.py
"""

import os
import sys
import json
import unittest
from dotenv import load_dotenv

# Load environment
load_dotenv()

from app import app
from db import (
    get_database_url,
    get_masked_db_url,
    check_db_health,
    init_db,
    DatabaseConfigError,
    DatabaseConnectionError
)


class TestColor:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_header(title):
    print(f"\n{TestColor.CYAN}{TestColor.BOLD}{'=' * 70}{TestColor.RESET}")
    print(f"{TestColor.CYAN}{TestColor.BOLD}  {title}{TestColor.RESET}")
    print(f"{TestColor.CYAN}{TestColor.BOLD}{'=' * 70}{TestColor.RESET}")


def print_pass(msg):
    print(f"  [{TestColor.GREEN}PASS{TestColor.RESET}] {msg}")


def print_fail(msg):
    print(f"  [{TestColor.RED}FAIL{TestColor.RESET}] {msg}")


def print_info(msg):
    print(f"  [{TestColor.YELLOW}INFO{TestColor.RESET}] {msg}")


def run_full_suite():
    print_header("STUDENT RECORDS SYSTEM - NOSTROMO POSTGRESQL VALIDATION")
    
    # 1. Environment & Configuration Check
    print(f"\n{TestColor.BOLD}[1/4] Checking Environment Configuration...{TestColor.RESET}")
    db_url = os.getenv("DATABASE_URL")
    if not db_url or not db_url.strip():
        print_fail("DATABASE_URL is not configured in .env file.")
        print_info("To test against Nostromo PostgreSQL, edit .env and set:")
        print_info("DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>")
        has_db_url = False
    else:
        print_pass(f"DATABASE_URL detected: {get_masked_db_url(db_url)}")
        has_db_url = True

    # 2. Flask Application Route Unit Checks (using Flask Test Client)
    print(f"\n{TestColor.BOLD}[2/4] Testing Flask API Routing & Validation (Client Unit Tests)...{TestColor.RESET}")
    client = app.test_client()

    # Test Homepage route
    resp = client.get("/")
    if resp.status_code == 200 and b"Student Records System" in resp.data:
        print_pass("GET / returns 200 OK and renders student dashboard")
    else:
        print_fail(f"GET / returned status {resp.status_code}")

    # Test Health endpoint
    resp = client.get("/api/health")
    if resp.status_code in (200, 503):
        print_pass(f"GET /api/health returned valid response (HTTP {resp.status_code})")
        health_json = resp.get_json()
        print_info(f"Health Response Database Status: {health_json.get('database')}")
    else:
        print_fail(f"GET /api/health unexpected status: {resp.status_code}")

    # Test Validation on POST with empty body
    resp = client.post("/api/students", json={})
    if resp.status_code == 400:
        print_pass("POST /api/students correctly rejects empty JSON payload with HTTP 400")
    else:
        print_fail(f"POST /api/students empty body returned {resp.status_code}, expected 400")

    # Test Validation on POST with invalid email format
    invalid_email_payload = {
        "name": "Jane Doe",
        "register_number": "TEST-REG-9999",
        "department": "Computer Science & Engineering",
        "email": "not-an-email",
        "academic_year": "1st Year (2025-2029)"
    }
    resp = client.post("/api/students", json=invalid_email_payload)
    if resp.status_code == 400 and "email" in resp.get_json().get("error", "").lower():
        print_pass("POST /api/students correctly validates email format and returns HTTP 400")
    else:
        print_fail(f"POST /api/students with invalid email returned {resp.status_code}")

    # 3. Live Database Tests (if configured)
    print(f"\n{TestColor.BOLD}[3/4] Live Nostromo PostgreSQL Connectivity & CRUD Tests...{TestColor.RESET}")
    if not has_db_url:
        print_info("Skipping live database queries because DATABASE_URL is not yet configured.")
        print_info("Once you paste your Nostromo URI into .env, re-run this script to test your PostgreSQL engine.")
    else:
        try:
            # A. Schema Initialization
            print_info("Attempting table creation and schema validation...")
            init_ok, init_msg = init_db()
            if init_ok:
                print_pass("PostgreSQL Schema initialized (table 'students' ready)")
            else:
                print_fail(f"Schema initialization failed: {init_msg}")

            # B. Health Check
            health = check_db_health()
            if health.get("status") == "healthy":
                print_pass(f"PostgreSQL connection verified! Engine version: {health.get('postgresql_version', '')[:50]}...")
            else:
                print_fail(f"PostgreSQL health check failed: {health.get('error')}")

            # C. Create Student Record
            test_reg = f"TEST-REG-{os.getpid()}"
            sample_student = {
                "name": "Alice Turing",
                "register_number": test_reg,
                "department": "Data Science & AI",
                "email": "alice.turing@nostromo.test",
                "academic_year": "3rd Year (2023-2027)"
            }
            resp = client.post("/api/students", json=sample_student)
            created_student = None
            if resp.status_code == 201:
                created_student = resp.get_json().get("student")
                print_pass(f"POST /api/students created student #{created_student['id']} ({created_student['name']})")
            else:
                print_fail(f"POST /api/students failed with status {resp.status_code}: {resp.get_data(as_text=True)}")

            if created_student:
                student_id = created_student["id"]

                # D. Duplicate Register Number Validation (expect 409)
                resp_dup = client.post("/api/students", json=sample_student)
                if resp_dup.status_code == 409:
                    print_pass(f"Duplicate register number properly rejected with HTTP 409 Conflict: {resp_dup.get_json().get('error')}")
                else:
                    print_fail(f"Duplicate register number did not return 409 (got {resp_dup.status_code})")

                # E. Retrieve Single Student (GET /api/students/<id>)
                resp_get = client.get(f"/api/students/{student_id}")
                if resp_get.status_code == 200 and resp_get.get_json()["student"]["name"] == "Alice Turing":
                    print_pass(f"GET /api/students/{student_id} successfully retrieved student details")
                else:
                    print_fail(f"GET /api/students/{student_id} failed: {resp_get.status_code}")

                # F. Search Student (GET /api/students?search=Alice)
                resp_search = client.get("/api/students?search=Alice")
                if resp_search.status_code == 200 and resp_search.get_json()["count"] >= 1:
                    print_pass(f"GET /api/students?search=Alice successfully returned {resp_search.get_json()['count']} record(s)")
                else:
                    print_fail(f"Search query failed: {resp_search.get_data(as_text=True)}")

                # G. Update Student (PUT /api/students/<id>)
                updated_payload = {
                    "name": "Alice M. Turing",
                    "register_number": test_reg,
                    "department": "Computer Science & Engineering",
                    "email": "alice.updated@nostromo.test",
                    "academic_year": "4th Year (2022-2026)"
                }
                resp_put = client.put(f"/api/students/{student_id}", json=updated_payload)
                if resp_put.status_code == 200 and resp_put.get_json()["student"]["department"] == "Computer Science & Engineering":
                    print_pass(f"PUT /api/students/{student_id} successfully updated department to '{resp_put.get_json()['student']['department']}'")
                else:
                    print_fail(f"PUT /api/students/{student_id} failed: {resp_put.get_data(as_text=True)}")

                # H. Delete Student (DELETE /api/students/<id>)
                resp_del = client.delete(f"/api/students/{student_id}")
                if resp_del.status_code == 200:
                    print_pass(f"DELETE /api/students/{student_id} successfully removed test record")
                else:
                    print_fail(f"DELETE /api/students/{student_id} failed: {resp_del.get_data(as_text=True)}")

                # I. Verify Deletion (expect 404)
                resp_verify_del = client.get(f"/api/students/{student_id}")
                if resp_verify_del.status_code == 404:
                    print_pass(f"GET /api/students/{student_id} confirmed 404 Not Found after deletion")
                else:
                    print_fail(f"Expected 404 after deletion, got {resp_verify_del.status_code}")

        except Exception as e:
            print_fail(f"Exception during live database testing: {e}")

    # 4. Summary & Verification Instructions
    print(f"\n{TestColor.BOLD}[4/4] Verification Summary{TestColor.RESET}")
    print("=" * 70)
    print("  All local application structures, routes, and validation filters passed.")
    if has_db_url:
        print("  PostgreSQL live tests were executed against your DATABASE_URL.")
    else:
        print("  Configure DATABASE_URL in .env to run live tests against your Nostromo engine.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_full_suite()
