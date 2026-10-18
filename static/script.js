/**
 * Student Records Management System - Frontend JavaScript
 * Handles REST API interactions, form validation, table rendering, search, and UI state.
 */

// Application State
let studentsList = [];
let deleteTargetId = null;
let isEditMode = false;

// DOM Elements
const studentForm = document.getElementById('studentForm');
const formTitle = document.getElementById('formTitle');
const formSubtitle = document.getElementById('formSubtitle');
const formBadge = document.getElementById('formBadge');
const submitBtnText = document.getElementById('submitBtnText');
const cancelBtn = document.getElementById('cancelBtn');
const cancelBtnText = document.getElementById('cancelBtnText');

// Form Input Elements
const studentIdInput = document.getElementById('studentId');
const studentNameInput = document.getElementById('studentName');
const registerNumberInput = document.getElementById('registerNumber');
const departmentSelect = document.getElementById('department');
const emailInput = document.getElementById('email');
const academicYearSelect = document.getElementById('academicYear');

// Field Error Elements
const nameError = document.getElementById('nameError');
const registerNumberError = document.getElementById('registerNumberError');
const departmentError = document.getElementById('departmentError');
const emailError = document.getElementById('emailError');
const academicYearError = document.getElementById('academicYearError');

// Table & UI Elements
const studentsTableBody = document.getElementById('studentsTableBody');
const tableLoading = document.getElementById('tableLoading');
const emptyState = document.getElementById('emptyState');
const emptyStateTitle = document.getElementById('emptyStateTitle');
const emptyStateDesc = document.getElementById('emptyStateDesc');
const totalStudentsCount = document.getElementById('totalStudentsCount');
const showingCountText = document.getElementById('showingCountText');

// Search & Controls
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearchBtn');
const refreshBtn = document.getElementById('refreshBtn');

// Delete Modal Elements
const deleteModal = document.getElementById('deleteModal');
const deleteTargetDetails = document.getElementById('deleteTargetDetails');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

// Toast Container
const toastContainer = document.getElementById('toastContainer');

// ============================================================================
// Initialization & Event Listeners
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch of all students
    fetchStudents();

    // Form submission
    studentForm.addEventListener('submit', handleFormSubmit);

    // Cancel / Reset button
    cancelBtn.addEventListener('click', handleCancelEdit);

    // Search input (live filtering)
    searchInput.addEventListener('input', handleSearch);

    // Clear search
    clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearSearchBtn.style.display = 'none';
        renderTable(studentsList);
        searchInput.focus();
    });

    // Refresh table button
    refreshBtn.addEventListener('click', () => {
        showNotification('Refreshing student records...', 'info');
        fetchStudents(searchInput.value.trim());
    });

    // Delete modal cancel & confirm
    cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    confirmDeleteBtn.addEventListener('click', handleConfirmDelete);

    // Close modal on click outside
    deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) {
            closeDeleteModal();
        }
    });

    // Keyboard ESC to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && deleteModal.style.display !== 'none') {
            closeDeleteModal();
        }
    });

    // Input blur validations for real-time feedback
    studentNameInput.addEventListener('input', () => clearFieldError(studentNameInput, nameError));
    registerNumberInput.addEventListener('input', () => clearFieldError(registerNumberInput, registerNumberError));
    departmentSelect.addEventListener('change', () => clearFieldError(departmentSelect, departmentError));
    emailInput.addEventListener('input', () => clearFieldError(emailInput, emailError));
    academicYearSelect.addEventListener('change', () => clearFieldError(academicYearSelect, academicYearError));
});

// ============================================================================
// API Calls: Fetch, Add, Update, Delete
// ============================================================================

/**
 * Fetch all students from backend REST API (GET /api/students)
 */
async function fetchStudents(searchQuery = '') {
    showLoading(true);
    emptyState.style.display = 'none';

    try {
        const url = searchQuery 
            ? `/api/students?search=${encodeURIComponent(searchQuery)}`
            : '/api/students';

        const response = await fetch(url);
        const data = await response.json();

        if (response.ok && data.success) {
            studentsList = data.students || [];
            
            // If no search filter is active, update the total count card
            if (!searchQuery) {
                totalStudentsCount.textContent = data.total ?? studentsList.length;
            }

            renderTable(studentsList, searchQuery);
        } else {
            const errorMsg = data.error || 'Failed to load student records.';
            showNotification(errorMsg, 'error');
            renderTable([], searchQuery);
        }
    } catch (err) {
        console.error('Fetch error:', err);
        showNotification('Could not connect to the server. Please check if Flask and PostgreSQL are running.', 'error');
        renderTable([], searchQuery);
    } finally {
        showLoading(false);
    }
}

/**
 * Handle form submission for both Add (POST) and Edit (PUT)
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    // Perform full form validation
    if (!validateForm()) {
        showNotification('Please correct the highlighted form errors.', 'error');
        return;
    }

    const payload = {
        name: studentNameInput.value.trim(),
        register_number: registerNumberInput.value.trim(),
        department: departmentSelect.value,
        email: emailInput.value.trim(),
        academic_year: academicYearSelect.value
    };

    const isUpdate = Boolean(studentIdInput.value);
    const url = isUpdate ? `/api/students/${studentIdInput.value}` : '/api/students';
    const method = isUpdate ? 'PUT' : 'POST';

    // Disable submit button while request is pending
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    const originalText = submitBtnText.textContent;
    submitBtnText.textContent = isUpdate ? 'Updating...' : 'Saving...';

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showNotification(result.message || (isUpdate ? 'Student updated!' : 'Student added!'), 'success');
            resetFormState();
            await fetchStudents(searchInput.value.trim());
        } else {
            // Handle duplicate register number or validation error from server
            const errorMsg = result.error || 'Operation failed. Please try again.';
            showNotification(errorMsg, 'error');

            if (errorMsg.toLowerCase().includes('register number')) {
                setFieldError(registerNumberInput, registerNumberError, errorMsg);
                registerNumberInput.focus();
            } else if (errorMsg.toLowerCase().includes('email')) {
                setFieldError(emailInput, emailError, errorMsg);
                emailInput.focus();
            }
        }
    } catch (err) {
        console.error('Submit error:', err);
        showNotification('Network error occurred while saving student record.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtnText.textContent = originalText;
    }
}

/**
 * Populate form with student details for editing (GET /api/students/<id>)
 */
async function editStudent(id) {
    try {
        const response = await fetch(`/api/students/${id}`);
        const data = await response.json();

        if (response.ok && data.success && data.student) {
            const student = data.student;

            // Switch form to Edit Mode
            isEditMode = true;
            studentIdInput.value = student.id;
            studentNameInput.value = student.name;
            registerNumberInput.value = student.register_number;
            departmentSelect.value = student.department;
            emailInput.value = student.email;
            academicYearSelect.value = student.academic_year;

            // Clear any previous validation errors
            clearAllFieldErrors();

            // Update UI headers and buttons
            formTitle.textContent = 'Edit Student Details';
            formSubtitle.textContent = `Modifying record for ${student.name} (ID #${student.id})`;
            formBadge.textContent = `Editing #${student.id}`;
            formBadge.className = 'mode-badge badge-edit';
            submitBtnText.textContent = 'Update Student';
            cancelBtnText.textContent = 'Cancel Edit';

            // Smoothly scroll to the form
            studentForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
            studentNameInput.focus();
        } else {
            showNotification(data.error || 'Could not fetch student details for editing.', 'error');
        }
    } catch (err) {
        console.error('Error fetching student for edit:', err);
        showNotification('Failed to load student record details.', 'error');
    }
}

/**
 * Open confirmation modal before deleting a student
 */
function confirmDelete(id, name, registerNumber) {
    deleteTargetId = id;
    deleteTargetDetails.innerHTML = `
        <strong>Name:</strong> ${escapeHtml(name)}<br>
        <strong>Register No:</strong> ${escapeHtml(registerNumber)}<br>
        <strong>Student ID:</strong> #${escapeHtml(String(id))}
    `;
    deleteModal.style.display = 'flex';
}

/**
 * Close the delete confirmation modal
 */
function closeDeleteModal() {
    deleteModal.style.display = 'none';
    deleteTargetId = null;
}

/**
 * Execute student deletion (DELETE /api/students/<id>)
 */
async function handleConfirmDelete() {
    if (!deleteTargetId) return;

    confirmDeleteBtn.disabled = true;
    confirmDeleteBtn.textContent = 'Deleting...';

    try {
        const response = await fetch(`/api/students/${deleteTargetId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showNotification(result.message || 'Student record deleted successfully.', 'success');
            
            // If deleting the record currently in the edit form, reset the form
            if (studentIdInput.value == deleteTargetId) {
                resetFormState();
            }

            closeDeleteModal();
            await fetchStudents(searchInput.value.trim());
        } else {
            showNotification(result.error || 'Failed to delete student.', 'error');
        }
    } catch (err) {
        console.error('Delete error:', err);
        showNotification('Network error occurred while deleting student.', 'error');
    } finally {
        confirmDeleteBtn.disabled = false;
        confirmDeleteBtn.textContent = 'Yes, Delete Student';
    }
}

// ============================================================================
// Form Validation Logic
// ============================================================================

const EMAIL_PATTERN = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

function validateForm() {
    let isValid = true;
    clearAllFieldErrors();

    // 1. Student Name
    const nameVal = studentNameInput.value.trim();
    if (!nameVal) {
        setFieldError(studentNameInput, nameError, 'Student name is required.');
        isValid = false;
    } else if (nameVal.length > 100) {
        setFieldError(studentNameInput, nameError, 'Name cannot exceed 100 characters.');
        isValid = false;
    }

    // 2. Register Number
    const regVal = registerNumberInput.value.trim();
    if (!regVal) {
        setFieldError(registerNumberInput, registerNumberError, 'Register number is required.');
        isValid = false;
    } else if (regVal.length > 50) {
        setFieldError(registerNumberInput, registerNumberError, 'Register number cannot exceed 50 characters.');
        isValid = false;
    }

    // 3. Department
    if (!departmentSelect.value) {
        setFieldError(departmentSelect, departmentError, 'Please select a department.');
        isValid = false;
    }

    // 4. Email Address
    const emailVal = emailInput.value.trim();
    if (!emailVal) {
        setFieldError(emailInput, emailError, 'Email address is required.');
        isValid = false;
    } else if (!EMAIL_PATTERN.test(emailVal)) {
        setFieldError(emailInput, emailError, 'Enter a valid email format (e.g., student@example.com).');
        isValid = false;
    } else if (emailVal.length > 120) {
        setFieldError(emailInput, emailError, 'Email cannot exceed 120 characters.');
        isValid = false;
    }

    // 5. Academic Year
    if (!academicYearSelect.value) {
        setFieldError(academicYearSelect, academicYearError, 'Please select an academic year.');
        isValid = false;
    }

    return isValid;
}

function setFieldError(inputElem, errorElem, message) {
    inputElem.classList.add('input-error');
    errorElem.textContent = message;
}

function clearFieldError(inputElem, errorElem) {
    inputElem.classList.remove('input-error');
    errorElem.textContent = '';
}

function clearAllFieldErrors() {
    clearFieldError(studentNameInput, nameError);
    clearFieldError(registerNumberInput, registerNumberError);
    clearFieldError(departmentSelect, departmentError);
    clearFieldError(emailInput, emailError);
    clearFieldError(academicYearSelect, academicYearError);
}

function handleCancelEdit() {
    resetFormState();
    showNotification('Form cleared.', 'info');
}

function resetFormState() {
    studentForm.reset();
    studentIdInput.value = '';
    isEditMode = false;
    clearAllFieldErrors();

    // Reset UI headers and buttons
    formTitle.textContent = 'Add New Student';
    formSubtitle.textContent = 'Fill in the student details below to save to PostgreSQL';
    formBadge.textContent = 'New Entry';
    formBadge.className = 'mode-badge badge-add';
    submitBtnText.textContent = 'Add Student';
    cancelBtnText.textContent = 'Clear Form';
}

// ============================================================================
// Table Rendering & Search Filter
// ============================================================================

/**
 * Render the list of students into the HTML table
 */
function renderTable(students, currentQuery = '') {
    studentsTableBody.innerHTML = '';

    if (!students || students.length === 0) {
        emptyState.style.display = 'flex';
        if (currentQuery) {
            emptyStateTitle.textContent = 'No Matching Records';
            emptyStateDesc.textContent = `No students found matching "${escapeHtml(currentQuery)}". Try another search term.`;
        } else {
            emptyStateTitle.textContent = 'No Students Found';
            emptyStateDesc.textContent = 'No student records exist yet. Use the form on the left to add one!';
        }
        showingCountText.textContent = 'Showing 0 students';
        return;
    }

    emptyState.style.display = 'none';
    showingCountText.textContent = `Showing ${students.length} student${students.length === 1 ? '' : 's'}`;

    students.forEach((student) => {
        const row = document.createElement('tr');
        row.setAttribute('data-id', student.id);

        row.innerHTML = `
            <td><strong>#${student.id}</strong></td>
            <td><strong>${escapeHtml(student.name)}</strong></td>
            <td><span class="reg-no-text">${escapeHtml(student.register_number)}</span></td>
            <td><span class="badge-dept">${escapeHtml(student.department)}</span></td>
            <td><a href="mailto:${escapeHtml(student.email)}" style="color: var(--primary); text-decoration: none;">${escapeHtml(student.email)}</a></td>
            <td><span class="badge-year">${escapeHtml(student.academic_year)}</span></td>
            <td class="text-center actions-cell">
                <button 
                    type="button" 
                    class="btn btn-sm btn-action-edit" 
                    onclick="editStudent(${student.id})"
                    title="Edit Student Details"
                >
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    Edit
                </button>
                <button 
                    type="button" 
                    class="btn btn-sm btn-action-delete" 
                    onclick="confirmDelete(${student.id}, '${escapeJsString(student.name)}', '${escapeJsString(student.register_number)}')"
                    title="Delete Student Record"
                >
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                    Delete
                </button>
            </td>
        `;

        studentsTableBody.appendChild(row);
    });
}

/**
 * Handle live search filtering on user keystroke
 */
function handleSearch(e) {
    const query = e.target.value.trim().toLowerCase();

    if (query) {
        clearSearchBtn.style.display = 'block';
    } else {
        clearSearchBtn.style.display = 'none';
    }

    // Client-side instant filter of loaded students
    const filtered = studentsList.filter((student) => {
        const nameMatch = student.name && student.name.toLowerCase().includes(query);
        const regMatch = student.register_number && student.register_number.toLowerCase().includes(query);
        return nameMatch || regMatch;
    });

    renderTable(filtered, query);
}

// ============================================================================
// UI Helpers: Loading, Toast Notifications, HTML Escaping
// ============================================================================

function showLoading(isLoading) {
    tableLoading.style.display = isLoading ? 'flex' : 'none';
}

/**
 * Display modern floating toast notifications
 * @param {string} message - Message to display
 * @param {'success'|'error'|'info'} type - Alert type
 */
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let iconSvg = '';
    let titleText = 'Notice';

    if (type === 'success') {
        titleText = 'Success';
        iconSvg = `
            <svg class="toast-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
        `;
    } else if (type === 'error') {
        titleText = 'Error';
        iconSvg = `
            <svg class="toast-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
        `;
    } else {
        iconSvg = `
            <svg class="toast-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
        `;
    }

    toast.innerHTML = `
        ${iconSvg}
        <div class="toast-content">
            <div class="toast-title">${titleText}</div>
            <div class="toast-message">${escapeHtml(message)}</div>
        </div>
        <button class="toast-close" aria-label="Close notification">&times;</button>
    `;

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        dismissToast(toast);
    });

    toastContainer.appendChild(toast);

    // Auto dismiss after 4 seconds
    setTimeout(() => {
        dismissToast(toast);
    }, 4000);
}

function dismissToast(toast) {
    if (!toast || toast.dataset.dismissed) return;
    toast.dataset.dismissed = 'true';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(50px)';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 250);
}

/**
 * Escape HTML to protect against XSS injection
 */
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Escape strings for inline JavaScript parameters
 */
function escapeJsString(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r');
}
