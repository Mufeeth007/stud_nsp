# Student Records Management System

A simple, complete, and beginner-friendly **Student Records Management System** built with **HTML, CSS, JavaScript, Python Flask, and PostgreSQL**.

Designed as a clean, college mini project that demonstrates full CRUD (Create, Read, Update, Delete) database operations, parameterized SQL queries, responsive design, and input validation without complex frameworks.

---

## 📋 Features

- **Add New Students**: Easily register students with their details.
- **View All Records**: Clean, responsive table showing all enrolled students.
- **Edit Existing Records**: Click "Edit" on any row to load and update student details.
- **Delete Student with Confirmation**: Safe deletion prompt showing the student's name and register number.
- **Real-Time Search**: Search instantly by **student name** or **register number**.
- **Field & Email Validation**: Ensures no empty fields and validates standard email formats.
- **Duplicate Prevention**: Rejects duplicate register numbers with friendly alerts.
- **Toast Notifications**: Modern floating success and error alerts.
- **Total Students Counter**: Live dashboard card displaying student count.
- **Persistent Storage**: All data is saved directly in PostgreSQL and persists across server restarts.

---

## 🗂️ Student Details Fields

Each student record includes:
1. **Student ID**: Auto-incrementing primary key (`id SERIAL PRIMARY KEY`).
2. **Student Name**: Full name of the student.
3. **Register Number**: Unique institutional registration number.
4. **Department**: Academic department / engineering branch.
5. **Email Address**: Validated email address.
6. **Academic Year**: Current year of study (1st, 2nd, 3rd, 4th, or Final Year).

---

## 📁 Project Structure

```text
student-records-system/
│
├── app.py              # Flask server and REST API endpoints
├── db.py               # PostgreSQL connection & automatic table creation
├── requirements.txt    # Python dependencies list
├── .env                # Environment variables (DB credentials)
├── .gitignore          # Files to exclude from Git version control
├── README.md           # Project documentation and step-by-step setup
│
├── templates/
│   └── index.html      # Frontend HTML dashboard
│
└── static/
    ├── style.css       # Clean, modern, responsive CSS styling
    └── script.js       # Vanilla JavaScript for API interaction and UI
```

---

## 🛠️ Prerequisites

Before getting started, make sure you have the following installed on your Windows PC:

1. **Python 3.10 or higher**: [Download Python for Windows](https://www.python.org/downloads/)
   - *Important:* During installation, check the box **"Add Python to PATH"**.
2. **PostgreSQL 15, 16, or 17**: [Download PostgreSQL for Windows](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
   - During PostgreSQL installation, remember the password you set for the default `postgres` user.
3. **Visual Studio Code**: [Download VS Code](https://code.visualstudio.com/)

---

## 🚀 Step-by-Step Setup Instructions (Windows PowerShell)

Follow these exact steps in **Windows PowerShell** to set up and run the application.

### Step 1: Open the Project in VS Code

1. Launch **Visual Studio Code**.
2. Click **File** > **Open Folder...** (or press `Ctrl + K, Ctrl + O`).
3. Select your project folder (e.g., `D:\Projects\stud_nsp` or `student-records-system`).
4. Open the integrated terminal by pressing `Ctrl + ` ` ` (backtick) or selecting **Terminal** > **New Terminal**.

---

### Step 2: Create and Activate a Python Virtual Environment

In the VS Code PowerShell terminal, run:

```powershell
# 1. Create the virtual environment named 'venv'
python -m venv venv

# 2. Activate the virtual environment
.\venv\Scripts\Activate.ps1
```

> **Tip:** If you see an execution policy error such as *`cannot be loaded because running scripts is disabled on this system`*, run this command once and try activating again:
> ```powershell
> Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
> .\venv\Scripts\Activate.ps1
> ```
> You will see `(venv)` at the beginning of your terminal prompt when activated.

---

### Step 3: Install Required Packages

Install the required dependencies using `pip`:

```powershell
pip install -r requirements.txt
```

This installs:
- **Flask**: Web framework for building REST API endpoints.
- **psycopg2-binary**: PostgreSQL adapter for Python.
- **python-dotenv**: Loads database credentials securely from `.env`.

---

### Step 4: Create the PostgreSQL Database (`student_db`)

You can create the database using either **psql** command line or **pgAdmin 4**.

#### Option A: Using `psql` (Recommended & Fast)

Run the following command in PowerShell:

```powershell
# Connect to PostgreSQL as user 'postgres'
psql -U postgres
```
*(Enter your PostgreSQL password when prompted)*

Once inside the PostgreSQL shell (`postgres=#`), create the database:

```sql
CREATE DATABASE student_db;
\q
```

#### Option B: Using pgAdmin 4 (GUI)

1. Open **pgAdmin 4** from your Windows Start menu.
2. Enter your master password to unlock pgAdmin.
3. In the left sidebar, expand **Servers** > **PostgreSQL 17** (or your version).
4. Right-click on **Databases** > **Create** > **Database...**.
5. In the **Database** field, type `student_db`.
6. Click **Save**.

---

### Step 5: Configure the `.env` File

Open the `.env` file in the project root and configure it with your local PostgreSQL settings:

```env
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=student_db
DB_USER=postgres
DB_PASSWORD=your_actual_password_here

# Application Port
PORT=5000
```

> **Important:** Replace `your_actual_password_here` with the password you chose when you installed PostgreSQL.

---

### Step 6: Test Database Initialization

You can verify that PostgreSQL connects properly and creates the `students` table by running:

```powershell
python db.py
```

If successful, you will see:
```text
Testing database connection and initializing table...
Database initialized successfully: 'students' table is ready.
Success!
```

---

### Step 7: Run the Flask Application

Start the Flask development server:

```powershell
python app.py
```

You will see output similar to:
```text
Database initialized successfully: 'students' table is ready.
Starting Student Records Management System on http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

### Step 8: Open the Website in Your Browser

1. Open any web browser (Google Chrome, Microsoft Edge, Firefox, Brave).
2. Visit the URL:
   ```text
   http://127.0.0.1:5000
   ```
   *(or `http://localhost:5000`)*
3. You can now:
   - Add new student records.
   - Search by name or register number in real-time.
   - Click **Edit** to update existing details.
   - Click **Delete** to remove a record with a confirmation dialog.

---

## 📡 REST API Reference

| HTTP Method | Endpoint | Description | Request Body | Status Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Serves dashboard UI (`index.html`) | None | `200 OK` |
| `GET` | `/api/students` | Retrieve all student records | None (optional `?search=...`) | `200 OK` |
| `GET` | `/api/students/<id>` | Retrieve a single student by ID | None | `200 OK` / `404 Not Found` |
| `POST` | `/api/students` | Add a new student record | JSON: `name`, `register_number`, `department`, `email`, `academic_year` | `201 Created` / `400` / `409` |
| `PUT` | `/api/students/<id>` | Update an existing student | JSON: `name`, `register_number`, `department`, `email`, `academic_year` | `200 OK` / `404` / `409` |
| `DELETE` | `/api/students/<id>` | Delete a student record | None | `200 OK` / `404 Not Found` |

---

## 🛡️ Security & Best Practices

- **SQL Injection Prevention**: All queries in `app.py` and `db.py` use parameterized placeholders (`%s`), never raw string formatting.
- **Environment Separation**: Sensitive database credentials reside exclusively in `.env`, which is excluded from Git via `.gitignore`.
- **Duplicate Prevention**: Database enforces `UNIQUE(register_number)` and Flask returns a clear `409 Conflict` error if a duplicate is attempted.
- **XSS Protection**: Frontend escapes dynamic text values before injecting them into HTML DOM nodes.

---

## ❓ Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `FATAL: password authentication failed for user "postgres"` | Incorrect password in `.env` | Update `DB_PASSWORD` in `.env` to match your PostgreSQL password. |
| `FATAL: database "student_db" does not exist` | Database not created yet | Run `CREATE DATABASE student_db;` in `psql` or pgAdmin. |
| `connection to server ... failed: Connection refused` | PostgreSQL service is not running | Open Windows Services (`services.msc`), find **postgresql-x64-XX**, and click **Start**. |
| `running scripts is disabled on this system` | Windows PowerShell Execution Policy | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell. |

---

## 📜 License
This project is open-source and free to use for educational and learning purposes.
