# Student Records System using PostgreSQL

A modern, responsive, full-stack Student Records System designed specifically to test and validate the **PostgreSQL database engine provided by Project Nostromo (Android)**.

Built with **pure Vanilla HTML, CSS, JavaScript** on the frontend, a **Python Flask REST API** on the backend, and **PostgreSQL** via `psycopg2-binary`.

---

## Table of Contents

- [Overview & Architecture](#overview--architecture)
- [Technology Stack](#technology-stack)
- [Student Record Schema](#student-record-schema)
- [Project Structure](#project-structure)
- [Nostromo Integration Guide](#nostromo-integration-guide)
  - [Where to Paste the Nostromo URI](#where-to-paste-the-nostromo-uri)
  - [Connection Mode 1: Local Wi-Fi](#connection-mode-1-local-wi-fi-recommended)
  - [Connection Mode 2: USB Cable via ADB](#connection-mode-2-usb-cable-via-adb)
- [Step-by-Step Setup (Windows PowerShell)](#step-by-step-setup-windows-powershell)
- [API Reference](#api-reference)
- [Testing & Verification Guide](#testing--verification-guide)
  - [Sample Test Data](#sample-test-data)
  - [Test Scenarios & Expected Results](#test-scenarios--expected-results)
  - [Automated Verification Suite](#automated-verification-suite)
- [Troubleshooting Nostromo Connection Failures](#troubleshooting-nostromo-connection-failures)

---

## Overview & Architecture

Project **Nostromo** provides a native PostgreSQL database engine hosted directly on an Android device. This application acts as a test harness to verify:

1. **Remote connectivity** to Nostromo's PostgreSQL engine over Wi-Fi or USB ADB.
2. **DDL Execution**: Automatic schema creation (`CREATE TABLE IF NOT EXISTS students`).
3. **DML / CRUD Operations**: Creating, querying, modifying, and deleting student records.
4. **Data Integrity & Constraints**: Primary key auto-generation, unique register number constraint, and field validations.
5. **Data Persistence**: Ensuring records survive application and server restarts.
6. **Graceful Error Handling**: Masked credentials, diagnostic terminal logging, and UI status alerts.

> **Important**: This project connects strictly to PostgreSQL using the connection URI provided by Nostromo. It **never** falls back to SQLite or any mock database.

---

## Technology Stack

- **Frontend**: Plain HTML5, CSS3 (Modern custom variables, responsive grid, toast notifications, dialog modals), and Vanilla JavaScript (ES6+ `fetch` API). Zero external dependencies (No React, No Tailwind).
- **Backend**: Python 3 (Flask RESTful API, `python-dotenv`).
- **Database Driver**: `psycopg2-binary` using parameterized queries (`%s`) for SQL injection protection.
- **Database Engine**: PostgreSQL running inside the Nostromo Android project.

---

## Student Record Schema

Each student record is stored in PostgreSQL under the `students` table:

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Auto-generated sequential ID |
| `name` | `VARCHAR(150)` | `NOT NULL` | Full student name |
| `register_number` | `VARCHAR(50)` | `NOT NULL UNIQUE` | Unique student registration number |
| `department` | `VARCHAR(100)` | `NOT NULL` | Department / major |
| `email` | `VARCHAR(255)` | `NOT NULL` | Validated email address |
| `academic_year` | `VARCHAR(50)` | `NOT NULL` | Academic year (e.g. 1st Year, 2nd Year) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | `DEFAULT CURRENT_TIMESTAMP` | Record creation timestamp |

---

## Project Structure

```
stud_nsp/
│
├── app.py              # Flask server and REST API endpoints
├── db.py               # PostgreSQL connection management, schema init & CRUD operations
├── requirements.txt    # Python dependencies (Flask, python-dotenv, psycopg2-binary)
├── .env.example        # Environment variable template for DATABASE_URL
├── .gitignore          # Keeps .env, cache, and virtual environment out of Git
├── test_system.py      # Automated test suite to validate Flask routes & Nostromo DB
├── README.md           # Complete setup, testing, and troubleshooting documentation
│
├── templates/
│   └── index.html      # Responsive single-page dashboard with modals and forms
│
└── static/
    ├── style.css       # Clean, modern styling with variables and mobile responsiveness
    └── script.js       # Client-side API integration, live search, and validation
```

---

## Nostromo Integration Guide

### Where to Paste the Nostromo URI

1. In the Nostromo Android application, start the PostgreSQL server engine.
2. The app will display a connection URI in this format:
   ```text
   postgresql://<username>:<password>@<host>:<port>/<database_name>
   ```
3. Copy the URI from Nostromo.
4. In this project folder, create a `.env` file (by copying `.env.example`):
   ```powershell
   Copy-Item .env.example .env
   ```
5. Open `.env` and paste your copied URI on the `DATABASE_URL=` line:
   ```env
   DATABASE_URL=postgresql://postgres:secretpassword@192.168.1.105:5432/nostromodb
   ```
6. Save the file. The Flask backend automatically reloads the variable without requiring Python code changes.

---

### Connection Mode 1: Local Wi-Fi (Recommended)

When your Android device and PC are on the same Wi-Fi network:

1. Connect both your PC and Android phone running Nostromo to the same Wi-Fi router.
2. Note the Wi-Fi IP address shown in Nostromo (e.g. `192.168.1.105`).
3. Set your `.env`:
   ```env
   DATABASE_URL=postgresql://postgres:yourpassword@192.168.1.105:5432/nostromodb
   ```
4. *Tip*: Ensure "AP Isolation" or "Guest Network Isolation" is disabled in your Wi-Fi router settings so devices can communicate.

---

### Connection Mode 2: USB Cable via ADB

If you connect your Android device to your PC with a USB cable:

1. Enable **Developer Options** and **USB Debugging** on your Android device.
2. Run Android Debug Bridge (ADB) port forwarding in PowerShell:
   ```powershell
   adb forward tcp:5432 tcp:5432
   ```
   *(If Nostromo uses a custom port like 5433, use `adb forward tcp:5432 tcp:5433`)*
3. Set your `.env` to point to localhost (forwarded through ADB):
   ```env
   DATABASE_URL=postgresql://postgres:yourpassword@127.0.0.1:5432/nostromodb
   ```

---

## Step-by-Step Setup (Windows PowerShell)

Open **Windows PowerShell** in the project folder `d:\Projects\stud_nsp`:

### 1. Create and Activate Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1
```

> *Note*: If PowerShell displays a script execution policy error, enable local script execution for the current session:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\venv\Scripts\Activate.ps1
> ```

### 2. Install Required Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure the `.env` File

```powershell
# Copy template to .env
Copy-Item .env.example .env

# Edit .env in Notepad
notepad .env
```
Paste your PostgreSQL URI from Nostromo after `DATABASE_URL=` and save.

### 4. Run the Automated Verification Suite

Before starting the web server, run the automated test script to check connectivity and route logic:

```powershell
python test_system.py
```

### 5. Start the Flask Server

```powershell
python app.py
```

You will see terminal output similar to:
```text
======================================================================
  Student Records System - Nostromo PostgreSQL Test Harness
======================================================================
  Configured Database URI: postgresql://postgres:****@192.168.1.105:5432/nostromodb
  Attempting initial schema verification...
  [SUCCESS] PostgreSQL schema initialized successfully.
======================================================================
  Starting Flask Web Server on http://127.0.0.1:5000 ...
======================================================================
```

### 6. Open the Application in a Web Browser

Navigate to:
```text
http://127.0.0.1:5000
```

---

## API Reference

All API routes return JSON and appropriate HTTP status codes.

### 1. Health Check
- **Endpoint**: `GET /api/health`
- **Purpose**: Verifies PostgreSQL connection, reports server version and record counts.
- **Success Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "database_url": "postgresql://postgres:****@192.168.1.105:5432/nostromodb",
    "engine": "PostgreSQL (Project Nostromo)",
    "postgresql_version": "PostgreSQL 16.2 on aarch64-linux-android...",
    "total_students": 5
  }
  ```
- **Error Response (503 Service Unavailable)**:
  ```json
  {
    "status": "unhealthy",
    "database": "disconnected",
    "error": "Could not connect to PostgreSQL database provided by Nostromo...",
    "troubleshooting": ["..."]
  }
  ```

---

### 2. List All Students / Search
- **Endpoint**: `GET /api/students`
- **Optional Query**: `GET /api/students?search=alex`
- **Success Response (200 OK)**:
  ```json
  {
    "count": 1,
    "search_query": "alex",
    "students": [
      {
        "id": 1,
        "name": "Alex Johnson",
        "register_number": "REG-2024-001",
        "department": "Computer Science & Engineering",
        "email": "alex.j@university.edu",
        "academic_year": "2nd Year (2024-2028)",
        "created_at": "2026-10-17T18:00:00+00:00"
      }
    ]
  }
  ```

---

### 3. Get Student by ID
- **Endpoint**: `GET /api/students/<id>`
- **Response**: `200 OK` with student object or `404 Not Found`.

---

### 4. Create Student
- **Endpoint**: `POST /api/students`
- **Request Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "name": "Alex Johnson",
    "register_number": "REG-2024-001",
    "department": "Computer Science & Engineering",
    "email": "alex.j@university.edu",
    "academic_year": "2nd Year (2024-2028)"
  }
  ```
- **Responses**:
  - `201 Created`: Student added successfully.
  - `400 Bad Request`: Field missing or invalid email format.
  - `409 Conflict`: Register number already exists in database.
  - `503 Service Unavailable`: PostgreSQL connection error.

---

### 5. Update Student
- **Endpoint**: `PUT /api/students/<id>`
- **Request Body**: Same schema as Create.
- **Responses**: `200 OK`, `400 Bad Request`, `404 Not Found`, or `409 Conflict`.

---

### 6. Delete Student
- **Endpoint**: `DELETE /api/students/<id>`
- **Responses**: `200 OK` on deletion or `404 Not Found`.

---

## Testing & Verification Guide

### Sample Test Data

Use these sample records to test CRUD operations in the dashboard or via curl/PowerShell:

| Student Name | Register Number | Department | Email Address | Academic Year |
| :--- | :--- | :--- | :--- | :--- |
| **Alex Johnson** | `REG-2024-001` | Computer Science & Engineering | `alex.j@university.edu` | 2nd Year (2024-2028) |
| **Samantha Reed** | `REG-2024-002` | Data Science & AI | `samantha.r@university.edu` | 1st Year (2025-2029) |
| **Michael Chen** | `REG-2023-089` | Electronics & Communication | `mchen@tech.org` | 3rd Year (2023-2027) |
| **Elena Rostova** | `REG-2022-045` | Mechanical Engineering | `elena.r@mech.edu` | 4th Year (2022-2026) |

---

### Test Scenarios & Expected Results

#### Test 1: Automatic Table Creation
- **Action**: Start Flask (`python app.py`).
- **Expected Result**: Terminal displays `[SUCCESS] PostgreSQL schema initialized successfully.` The `students` table is automatically created with primary key and unique constraints.

#### Test 2: Add Student (Create)
- **Action**: Fill out the registration form in the browser and click **Save Student**.
- **Expected Result**: Green toast notification appears: `"Student 'Alex Johnson' added successfully!"`. The table updates instantly and the Total Students counter increments to `1`.

#### Test 3: Duplicate Register Number Validation
- **Action**: Attempt to add a second student with the exact same Register Number (`REG-2024-001`).
- **Expected Result**: Request is rejected with `HTTP 409 Conflict`. A red toast alert informs you: `"A student with register number 'REG-2024-001' already exists."` The register number field is outlined in red.

#### Test 4: Email Format Validation
- **Action**: Enter `invalid-email-format` in the email input and submit.
- **Expected Result**: Rejected with `HTTP 400 Bad Request`. An inline validation message explains: `"Please enter a valid email format (e.g. user@domain.com)."`.

#### Test 5: Live Search & Filtering
- **Action**: Type `Alex` or `REG-2024-001` into the search box.
- **Expected Result**: Table immediately filters matching records with debounce. The counter displays `"Showing 1 student"`. Clearing the search restores the full list.

#### Test 6: Edit Student (Update)
- **Action**: Click the **Edit** button next to a student, change Department to `Information Technology`, and click **Save Changes**.
- **Expected Result**: Modal closes, green toast notification displays `"Student record updated successfully"`, and the department pill updates in the table.

#### Test 7: Delete with Confirmation
- **Action**: Click **Delete**, inspect the warning dialog, and click **Confirm Delete**.
- **Expected Result**: Modal closes, record is removed from PostgreSQL, and a confirmation toast appears. When all records are deleted, the clean empty state message is shown.

#### Test 8: Data Persistence Across Server Restart
- **Action**:
  1. Add 2 students.
  2. In PowerShell, stop the Flask server with `Ctrl + C`.
  3. Restart the server with `python app.py`.
  4. Refresh `http://127.0.0.1:5000` in your browser.
- **Expected Result**: Both student records remain completely intact, proving permanent storage in Nostromo's PostgreSQL engine.

#### Test 9: Connection Failure & Error Handling
- **Action**: In `.env`, change the port or stop the PostgreSQL server in the Nostromo Android app, then click **Check Health** in the header.
- **Expected Result**:
  - The status dot turns red with text `"Database Disconnected"`.
  - An alert banner opens with specific troubleshooting steps.
  - The terminal outputs detailed diagnostic guidance with masked credentials.
  - The server continues running smoothly without crashing.

---

### Automated Verification Suite

Run the included automated verification script at any time:

```powershell
python test_system.py
```

The script runs a 4-stage test battery:
1. Environment & configuration sanity check.
2. API routing and validation checks.
3. Live Nostromo PostgreSQL schema, CRUD, duplicate constraint, and search verification.
4. Summary status report.

---

## Troubleshooting Nostromo Connection Failures

If the application cannot connect to the Nostromo PostgreSQL engine, check the following:

| Problem | Root Cause | Solution |
| :--- | :--- | :--- |
| **`Connection refused (10061)`** | Nostromo PostgreSQL engine is not running, or wrong port | 1. Open the Nostromo Android app and verify PostgreSQL is started.<br>2. Confirm the port in your URI matches Nostromo. |
| **`Connection timed out`** | Devices cannot reach each other over Wi-Fi | 1. Ensure PC and Android phone are on the exact same Wi-Fi SSID.<br>2. Disable "AP Isolation" or "Guest Mode" on your router.<br>3. Check Windows Firewall rules for outgoing port 5432. |
| **`password authentication failed`** | Incorrect username or password in URI | Re-copy the exact connection URI generated by Nostromo into `.env`. |
| **`database "..." does not exist`** | Database name is misspelled | Verify the database name suffix in your Nostromo connection URI. |
| **Connecting via USB cable fails** | ADB port forwarding not active | Run `adb forward tcp:5432 tcp:5432` in PowerShell and set `DATABASE_URL=postgresql://...:5432/...` pointing to `127.0.0.1`. |
