/**
 * Student Records System - Pure Vanilla JavaScript Frontend
 * Handles CRUD operations, PostgreSQL health checks, search filtering,
 * modal dialogs, real-time validations, and toast notifications.
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------------------
    // DOM Elements
    // -------------------------------------------------------------------------
    // Health and Status
    const dbStatusBadge = document.getElementById("db-status-badge");
    const dbStatusText = document.getElementById("db-status-text");
    const btnRefreshHealth = document.getElementById("btn-refresh-health");
    const statTotalStudents = document.getElementById("stat-total-students");
    const statTotalDepts = document.getElementById("stat-total-depts");
    const statDbEngine = document.getElementById("stat-db-engine");
    const connectionBanner = document.getElementById("connection-banner");
    const bannerTitle = document.getElementById("banner-title");
    const bannerMessage = document.getElementById("banner-message");
    const bannerClose = document.getElementById("banner-close");

    // Add Student Form
    const studentForm = document.getElementById("student-form");
    const inputName = document.getElementById("student-name");
    const inputReg = document.getElementById("student-reg");
    const selectDept = document.getElementById("student-dept");
    const inputEmail = document.getElementById("student-email");
    const selectYear = document.getElementById("student-year");
    const btnResetForm = document.getElementById("btn-reset-form");
    const btnSubmitForm = document.getElementById("btn-submit-form");

    // Errors for Add Form
    const errorName = document.getElementById("error-name");
    const errorReg = document.getElementById("error-reg");
    const errorDept = document.getElementById("error-dept");
    const errorEmail = document.getElementById("error-email");
    const errorYear = document.getElementById("error-year");

    // Table & Search
    const searchInput = document.getElementById("search-input");
    const btnClearSearch = document.getElementById("btn-clear-search");
    const btnRefreshTable = document.getElementById("btn-refresh-table");
    const recordsCounter = document.getElementById("records-counter");
    const activeSearchLabel = document.getElementById("active-search-label");
    const studentsTable = document.getElementById("students-table");
    const studentsTbody = document.getElementById("students-tbody");
    const tableLoading = document.getElementById("table-loading");
    const tableEmpty = document.getElementById("table-empty");
    const tableSearchEmpty = document.getElementById("table-search-empty");
    const btnResetSearchState = document.getElementById("btn-reset-search-state");

    // Edit Modal Elements
    const editModal = document.getElementById("edit-modal");
    const editForm = document.getElementById("edit-student-form");
    const editId = document.getElementById("edit-student-id");
    const editName = document.getElementById("edit-student-name");
    const editReg = document.getElementById("edit-student-reg");
    const editDept = document.getElementById("edit-student-dept");
    const editEmail = document.getElementById("edit-student-email");
    const editYear = document.getElementById("edit-student-year");
    const btnCloseEditModal = document.getElementById("btn-close-edit-modal");
    const btnCancelEdit = document.getElementById("btn-cancel-edit");
    const editErrorName = document.getElementById("edit-error-name");
    const editErrorReg = document.getElementById("edit-error-reg");
    const editErrorDept = document.getElementById("edit-error-dept");
    const editErrorEmail = document.getElementById("edit-error-email");
    const editErrorYear = document.getElementById("edit-error-year");

    // Delete Modal Elements
    const deleteModal = document.getElementById("delete-modal");
    const btnCloseDeleteModal = document.getElementById("btn-close-delete-modal");
    const btnCancelDelete = document.getElementById("btn-cancel-delete");
    const btnConfirmDelete = document.getElementById("btn-confirm-delete");
    const deleteConfirmMsg = document.getElementById("delete-confirm-message");
    const deleteRecordPreview = document.getElementById("delete-record-preview");

    // Toast Container
    const toastContainer = document.getElementById("toast-container");

    // -------------------------------------------------------------------------
    // Application State
    // -------------------------------------------------------------------------
    let currentStudents = [];
    let pendingDeleteStudent = null;
    let searchDebounceTimer = null;
    const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

    // -------------------------------------------------------------------------
    // Toast Notification System
    // -------------------------------------------------------------------------
    function showToast(title, message, type = "info", duration = 4000) {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;

        const icons = {
            success: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
            error: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
            warning: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
            info: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-body">
                <div class="toast-title">${escapeHtml(title)}</div>
                <div class="toast-message">${escapeHtml(message)}</div>
            </div>
            <button class="toast-close" aria-label="Close notification">&times;</button>
        `;

        const closeBtn = toast.querySelector(".toast-close");
        const removeToast = () => {
            toast.classList.add("toast-hiding");
            setTimeout(() => toast.remove(), 300);
        };

        closeBtn.addEventListener("click", removeToast);
        setTimeout(removeToast, duration);
        toastContainer.appendChild(toast);
    }

    // -------------------------------------------------------------------------
    // Health Check & Database Status
    // -------------------------------------------------------------------------
    async function checkHealth(notifyOnSuccess = false) {
        dbStatusBadge.className = "status-badge status-checking";
        dbStatusText.textContent = "Checking Database...";
        statDbEngine.textContent = "Connecting...";

        try {
            const res = await fetch("/api/health");
            const data = await res.json();

            if (res.ok && data.status === "healthy") {
                dbStatusBadge.className = "status-badge status-connected";
                dbStatusText.textContent = "Nostromo DB Connected";
                statDbEngine.textContent = "PostgreSQL (Active)";
                statDbEngine.title = data.postgresql_version || "PostgreSQL";
                connectionBanner.classList.add("hidden");

                if (notifyOnSuccess) {
                    showToast("Database Connected", "PostgreSQL engine on Nostromo is active and healthy.", "success");
                }
                return true;
            } else {
                handleConnectionFailure(data);
                return false;
            }
        } catch (err) {
            handleConnectionFailure({
                error: "Flask backend could not be reached or network request failed.",
                details: err.message
            });
            return false;
        }
    }

    function handleConnectionFailure(data) {
        dbStatusBadge.className = "status-badge status-disconnected";
        dbStatusText.textContent = "Database Disconnected";
        statDbEngine.textContent = "Disconnected";

        connectionBanner.classList.remove("hidden");
        if (data.status === "unconfigured") {
            bannerTitle.textContent = "PostgreSQL Configuration Missing (.env)";
            bannerMessage.innerHTML = "Please set <code>DATABASE_URL=...</code> in your <code>.env</code> file with the URI provided by Nostromo.";
        } else {
            bannerTitle.textContent = "PostgreSQL Connection Error";
            bannerMessage.textContent = data.error || "Could not connect to Nostromo PostgreSQL. Check server terminal for diagnostic details.";
        }
    }

    // -------------------------------------------------------------------------
    // Load & Render Students
    // -------------------------------------------------------------------------
    async function fetchStudents(searchQuery = "") {
        setTableLoading(true);

        const url = searchQuery
            ? `/api/students?search=${encodeURIComponent(searchQuery)}`
            : "/api/students";

        try {
            const res = await fetch(url);
            const data = await res.json();

            if (res.ok) {
                currentStudents = data.students || [];
                renderTable(currentStudents, searchQuery);
                updateStats(currentStudents);
            } else {
                showToast("Data Load Error", data.details || data.error || "Failed to load students.", "error");
                renderTable([], searchQuery);
            }
        } catch (err) {
            showToast("Network Error", "Unable to contact server to fetch student records.", "error");
            renderTable([], searchQuery);
        } finally {
            setTableLoading(false);
        }
    }

    function renderTable(students, searchQuery = "") {
        studentsTbody.innerHTML = "";

        // Reset visibility
        tableEmpty.classList.add("hidden");
        tableSearchEmpty.classList.add("hidden");
        studentsTable.classList.remove("hidden");

        const count = students.length;
        recordsCounter.textContent = `Showing ${count} student${count === 1 ? "" : "s"}`;

        if (searchQuery) {
            activeSearchLabel.classList.remove("hidden");
            activeSearchLabel.textContent = `Filtered by: "${searchQuery}"`;
            btnClearSearch.classList.remove("hidden");
        } else {
            activeSearchLabel.classList.add("hidden");
            btnClearSearch.classList.add("hidden");
        }

        if (count === 0) {
            studentsTable.classList.add("hidden");
            if (searchQuery) {
                tableSearchEmpty.classList.remove("hidden");
                document.getElementById("search-empty-text").textContent =
                    `No student records matched "${searchQuery}".`;
            } else {
                tableEmpty.classList.remove("hidden");
            }
            return;
        }

        // Populate rows
        students.forEach((student) => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td><strong>#${student.id}</strong></td>
                <td>
                    <div style="font-weight: 600; color: #1e293b;">${escapeHtml(student.name)}</div>
                </td>
                <td>
                    <span class="student-reg-badge">${escapeHtml(student.register_number)}</span>
                </td>
                <td>
                    <span class="dept-pill">${escapeHtml(student.department)}</span>
                </td>
                <td>
                    <a href="mailto:${escapeHtml(student.email)}" style="color: #4f46e5; text-decoration: none;">
                        ${escapeHtml(student.email)}
                    </a>
                </td>
                <td>${escapeHtml(student.academic_year)}</td>
                <td style="text-align: center;">
                    <div class="table-actions">
                        <button class="action-btn action-btn-edit" data-id="${student.id}" title="Edit Student">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                            Edit
                        </button>
                        <button class="action-btn action-btn-delete" data-id="${student.id}" title="Delete Student">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                            Delete
                        </button>
                    </div>
                </td>
            `;

            // Attach event listeners
            tr.querySelector(".action-btn-edit").addEventListener("click", () => openEditModal(student));
            tr.querySelector(".action-btn-delete").addEventListener("click", () => openDeleteModal(student));

            studentsTbody.appendChild(tr);
        });
    }

    function setTableLoading(loading) {
        if (loading) {
            tableLoading.classList.remove("hidden");
            studentsTable.classList.add("hidden");
            tableEmpty.classList.add("hidden");
            tableSearchEmpty.classList.add("hidden");
        } else {
            tableLoading.classList.add("hidden");
        }
    }

    function updateStats(students) {
        statTotalStudents.textContent = students.length;
        const uniqueDepts = new Set(students.map((s) => s.department));
        statTotalDepts.textContent = uniqueDepts.size;
    }

    // -------------------------------------------------------------------------
    // Form Validation Helpers
    // -------------------------------------------------------------------------
    function clearFormErrors() {
        [inputName, inputReg, selectDept, inputEmail, selectYear].forEach((el) => {
            el.classList.remove("input-error");
        });
        [errorName, errorReg, errorDept, errorEmail, errorYear].forEach((el) => {
            el.textContent = "";
        });
    }

    function validateField(input, errorEl, message) {
        input.classList.add("input-error");
        errorEl.textContent = message;
    }

    function validateAddForm() {
        clearFormErrors();
        let isValid = true;

        const name = inputName.value.trim();
        const reg = inputReg.value.trim();
        const dept = selectDept.value;
        const email = inputEmail.value.trim();
        const year = selectYear.value;

        if (!name) {
            validateField(inputName, errorName, "Student Name is required.");
            isValid = false;
        }

        if (!reg) {
            validateField(inputReg, errorReg, "Register Number is required.");
            isValid = false;
        }

        if (!dept) {
            validateField(selectDept, errorDept, "Please select a department.");
            isValid = false;
        }

        if (!email) {
            validateField(inputEmail, errorEmail, "Email address is required.");
            isValid = false;
        } else if (!EMAIL_REGEX.test(email)) {
            validateField(inputEmail, errorEmail, "Please enter a valid email format (e.g. user@domain.com).");
            isValid = false;
        }

        if (!year) {
            validateField(selectYear, errorYear, "Please select an academic year.");
            isValid = false;
        }

        return isValid ? { name, register_number: reg, department: dept, email, academic_year: year } : null;
    }

    // Real-time error clearance on typing
    [inputName, inputReg, selectDept, inputEmail, selectYear].forEach((input) => {
        input.addEventListener("input", () => {
            input.classList.remove("input-error");
            const err = input.parentElement.querySelector(".field-error");
            if (err) err.textContent = "";
        });
    });

    // -------------------------------------------------------------------------
    // Add Student Submit
    // -------------------------------------------------------------------------
    studentForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = validateAddForm();
        if (!payload) return;

        btnSubmitForm.disabled = true;
        btnSubmitForm.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...`;

        try {
            const res = await fetch("/api/students", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.status === 201) {
                showToast("Success", `Student '${payload.name}' added successfully!`, "success");
                studentForm.reset();
                clearFormErrors();
                fetchStudents(searchInput.value.trim());
            } else if (res.status === 409) {
                validateField(inputReg, errorReg, data.error || "Register number already exists.");
                showToast("Duplicate Record", data.error, "error");
            } else if (res.status === 400) {
                showToast("Validation Error", data.error, "warning");
            } else if (res.status === 503) {
                showToast("Database Error", data.details || data.error, "error");
                checkHealth();
            } else {
                showToast("Error", data.details || data.error || "Failed to create student.", "error");
            }
        } catch (err) {
            showToast("Network Error", "Could not submit student data: " + err.message, "error");
        } finally {
            btnSubmitForm.disabled = false;
            btnSubmitForm.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Save Student
            `;
        }
    });

    btnResetForm.addEventListener("click", () => {
        studentForm.reset();
        clearFormErrors();
    });

    // -------------------------------------------------------------------------
    // Edit Modal Logic
    // -------------------------------------------------------------------------
    function clearEditErrors() {
        [editName, editReg, editDept, editEmail, editYear].forEach((el) => el.classList.remove("input-error"));
        [editErrorName, editErrorReg, editErrorDept, editErrorEmail, editErrorYear].forEach((el) => el.textContent = "");
    }

    function openEditModal(student) {
        clearEditErrors();
        editId.value = student.id;
        editName.value = student.name;
        editReg.value = student.register_number;
        editDept.value = student.department;
        editEmail.value = student.email;
        editYear.value = student.academic_year;

        editModal.classList.remove("hidden");
        editName.focus();
    }

    function closeEditModal() {
        editModal.classList.add("hidden");
        clearEditErrors();
    }

    [btnCloseEditModal, btnCancelEdit].forEach((btn) => {
        btn.addEventListener("click", closeEditModal);
    });

    editModal.addEventListener("click", (e) => {
        if (e.target === editModal) closeEditModal();
    });

    editForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearEditErrors();

        const id = editId.value;
        const name = editName.value.trim();
        const reg = editReg.value.trim();
        const dept = editDept.value;
        const email = editEmail.value.trim();
        const year = editYear.value;

        let valid = true;
        if (!name) { validateField(editName, editErrorName, "Student Name is required."); valid = false; }
        if (!reg) { validateField(editReg, editErrorReg, "Register Number is required."); valid = false; }
        if (!dept) { validateField(editDept, editErrorDept, "Please select a department."); valid = false; }
        if (!email) {
            validateField(editEmail, editErrorEmail, "Email address is required.");
            valid = false;
        } else if (!EMAIL_REGEX.test(email)) {
            validateField(editEmail, editErrorEmail, "Please enter a valid email format.");
            valid = false;
        }
        if (!year) { validateField(editYear, editErrorYear, "Please select an academic year."); valid = false; }

        if (!valid) return;

        const payload = { name, register_number: reg, department: dept, email, academic_year: year };

        try {
            const res = await fetch(`/api/students/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok) {
                showToast("Updated", `Student record updated successfully.`, "success");
                closeEditModal();
                fetchStudents(searchInput.value.trim());
            } else if (res.status === 409) {
                validateField(editReg, editErrorReg, data.error);
                showToast("Duplicate Register Number", data.error, "error");
            } else {
                showToast("Update Failed", data.error || data.details || "Could not update record.", "error");
            }
        } catch (err) {
            showToast("Network Error", "Could not connect to update record: " + err.message, "error");
        }
    });

    // -------------------------------------------------------------------------
    // Delete Confirmation Modal Logic
    // -------------------------------------------------------------------------
    function openDeleteModal(student) {
        pendingDeleteStudent = student;
        deleteConfirmMsg.textContent = `Are you sure you want to permanently delete this student record from PostgreSQL?`;
        deleteRecordPreview.innerHTML = `
            <div><strong>Name:</strong> ${escapeHtml(student.name)}</div>
            <div><strong>Register No:</strong> <span class="student-reg-badge">${escapeHtml(student.register_number)}</span></div>
            <div><strong>Department:</strong> ${escapeHtml(student.department)}</div>
        `;
        deleteModal.classList.remove("hidden");
        btnConfirmDelete.focus();
    }

    function closeDeleteModal() {
        deleteModal.classList.add("hidden");
        pendingDeleteStudent = null;
    }

    [btnCloseDeleteModal, btnCancelDelete].forEach((btn) => {
        btn.addEventListener("click", closeDeleteModal);
    });

    deleteModal.addEventListener("click", (e) => {
        if (e.target === deleteModal) closeDeleteModal();
    });

    btnConfirmDelete.addEventListener("click", async () => {
        if (!pendingDeleteStudent) return;
        const id = pendingDeleteStudent.id;
        const studentName = pendingDeleteStudent.name;

        btnConfirmDelete.disabled = true;
        btnConfirmDelete.textContent = "Deleting...";

        try {
            const res = await fetch(`/api/students/${id}`, { method: "DELETE" });
            const data = await res.json();

            if (res.ok) {
                showToast("Deleted", data.message || `Student '${studentName}' was deleted.`, "success");
                closeDeleteModal();
                fetchStudents(searchInput.value.trim());
            } else {
                showToast("Delete Failed", data.details || data.error || "Failed to delete student.", "error");
            }
        } catch (err) {
            showToast("Network Error", "Could not delete student: " + err.message, "error");
        } finally {
            btnConfirmDelete.disabled = false;
            btnConfirmDelete.innerHTML = `
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
                Confirm Delete
            `;
        }
    });

    // -------------------------------------------------------------------------
    // Search & Filter (Debounced)
    // -------------------------------------------------------------------------
    searchInput.addEventListener("input", () => {
        clearTimeout(searchDebounceTimer);
        const query = searchInput.value.trim();

        if (query) {
            btnClearSearch.classList.remove("hidden");
        } else {
            btnClearSearch.classList.add("hidden");
        }

        searchDebounceTimer = setTimeout(() => {
            fetchStudents(query);
        }, 250);
    });

    btnClearSearch.addEventListener("click", () => {
        searchInput.value = "";
        btnClearSearch.classList.add("hidden");
        fetchStudents("");
        searchInput.focus();
    });

    btnResetSearchState.addEventListener("click", () => {
        searchInput.value = "";
        btnClearSearch.classList.add("hidden");
        fetchStudents("");
    });

    // -------------------------------------------------------------------------
    // Refresh Buttons & Keyboard Shortcuts
    // -------------------------------------------------------------------------
    btnRefreshTable.addEventListener("click", () => {
        fetchStudents(searchInput.value.trim());
        showToast("Refreshed", "Student records reloaded from PostgreSQL.", "info", 2000);
    });

    btnRefreshHealth.addEventListener("click", () => {
        checkHealth(true);
    });

    bannerClose.addEventListener("click", () => {
        connectionBanner.classList.add("hidden");
    });

    // Close modals on Escape key
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (!editModal.classList.contains("hidden")) closeEditModal();
            if (!deleteModal.classList.contains("hidden")) closeDeleteModal();
        }
    });

    // Utility: HTML Escaper to prevent XSS
    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // -------------------------------------------------------------------------
    // Initial Application Bootstrap
    // -------------------------------------------------------------------------
    checkHealth();
    fetchStudents();
});
