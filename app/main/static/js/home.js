/**
 * Health Vault - CLINICAL DASHBOARD (HOME.JS)
 * State-managed Admission & Triage (Structured 2026)
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. DOM ELEMENTS ---
    const elements = {
        // Dashboard Triage
        mainInput: document.getElementById('main-input'),
        analyzeBtn: document.getElementById('start-analysis-btn'),
        
        // Modal & Form
        admissionModalEl: document.getElementById('admissionModal'),
        admissionForm: document.getElementById('admission-init-form'),
        submitBtn: document.getElementById('btn-submit-admission'),
        
        // Identity Verification
        btnVerify: document.getElementById('btn-verify-identity'),
        emailInput: document.getElementById('patient-email-probe'),
        btnCodeSubmit: document.getElementById('btn-submit-code'),
        verificationCode: document.getElementById('verificationCode'),
        codeSection: document.getElementById('codeSection'),
        feedback: document.getElementById('probe-feedback'),
        
        // Dynamic UI Sections
        dynamicFields: document.getElementById('dynamic-admission-fields'),
        regFields: document.getElementById('registration-fields'),
        unitSelector: document.getElementById('unit-selector'),
        subjectSelector: document.getElementById('subject-selector'),

        // File Upload / Dropzone
        fileInput: document.getElementById('admission-file-input'),
        filePreview: document.getElementById('file-preview-container'),
        selectedFilename: document.getElementById('selected-filename'),
        fileStatus: document.getElementById('file-status-text'),
        dropzone: document.getElementById('admission-drop-zone'),

        // New Patient Inputs
        regInputs: [
            document.getElementById('reg-full-name'),
            document.getElementById('reg-mrn')
        ]
    };

    // --- 2. FILE UPLOAD & DROPZONE LOGIC ---
    
    const isSupportedImage = (file) => {
        return Boolean(file && file.type.startsWith('image/'));
    };

    const showFileError = (message) => {
        if (elements.fileInput) elements.fileInput.value = '';
        elements.filePreview?.classList.add('d-none');
        if (elements.fileStatus) {
            elements.fileStatus.textContent = message;
            elements.fileStatus.classList.add('text-danger');
        }
    };

    const updateFilePreview = (files) => {
        const file = files[0];
        if (!file) return showFileError('A diagnostic image is required.');
        if (Array.from(files).some(file => !isSupportedImage(file))) {
            return showFileError('Unsupported file. Upload diagnostic images only; PDF and other formats are blocked.');
        }

        elements.fileStatus?.classList.remove('text-danger');
        if (elements.fileStatus) elements.fileStatus.textContent = `${files.length} diagnostic image${files.length === 1 ? '' : 's'} selected`;
        if (elements.selectedFilename) {
            elements.selectedFilename.textContent = Array.from(files).map(file => file.name).join(', ');
        }
        elements.filePreview?.classList.remove('d-none');
    };

    elements.fileInput?.addEventListener('change', function() {
        updateFilePreview(this.files);
    });

    elements.dropzone?.addEventListener('click', (event) => {
        if (event.target !== elements.fileInput) elements.fileInput?.click();
    });

    // Handle Drag & Drop Events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        elements.dropzone?.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        elements.dropzone?.addEventListener(eventName, () => {
            elements.dropzone.classList.add('border-primary', 'bg-primary-subtle');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        elements.dropzone?.addEventListener(eventName, () => {
            elements.dropzone.classList.remove('border-primary', 'bg-primary-subtle');
        }, false);
    });

    elements.dropzone?.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (elements.fileInput) {
            if (files.length > 0 && Array.from(files).every(isSupportedImage)) {
                elements.fileInput.files = files;
                updateFilePreview(files);
            } else {
                showFileError('Unsupported file. Upload diagnostic images only; PDF and other formats are blocked.');
            }
        }
    }, false);

    // --- 3. QUICK TRIAGE LOGIC ---
    const handleTriageQuery = () => {
        const query = elements.mainInput?.value.trim();
        
        // If query is empty, focus the search bar but don't open modal
        if (!query) {
            elements.mainInput?.classList.add('is-invalid');
            elements.mainInput?.focus();
            return;
        }

        if (elements.admissionModalEl) {
            const sessionNameInput = document.getElementById('session-name-input');
            if (sessionNameInput) sessionNameInput.value = query;

            const modal = bootstrap.Modal.getOrCreateInstance(elements.admissionModalEl);
            modal.show();
        }
    };

    elements.analyzeBtn?.addEventListener('click', handleTriageQuery);
    elements.mainInput?.addEventListener('keypress', (e) => { 
        if (e.key === 'Enter') { e.preventDefault(); handleTriageQuery(); }
        elements.mainInput?.classList.remove('is-invalid');
    });

    // --- 4. DYNAMIC CURRICULUM SELECTORS ---
    // Note: Ensure your HTML contains the ID 'unit-selector' inside the modal
    elements.unitSelector?.addEventListener('change', async function() {
        if (!elements.subjectSelector) return;

        const unitId = this.value;
        elements.subjectSelector.disabled = true;
        elements.subjectSelector.innerHTML = '<option value="" disabled selected>Loading...</option>';

        try {
            const response = await fetch(`/api/units/${unitId}/subjects`);
            const subjects = await response.json();

            elements.subjectSelector.innerHTML = '<option value="" disabled selected>Select Topic...</option>';
            subjects.forEach(sub => {
                const option = document.createElement('option');
                option.value = sub.id;
                option.textContent = sub.name;
                elements.subjectSelector.appendChild(option);
            });
            elements.subjectSelector.disabled = false;
        } catch (error) {
            console.error("Topic load error:", error);
            elements.subjectSelector.innerHTML = '<option value="" disabled selected>Error loading</option>';
        }
    });

    // --- 5. IDENTITY VERIFICATION FLOW ---

    elements.btnVerify?.addEventListener('click', async () => {
        const email = elements.emailInput?.value.trim();
        if (!email || !email.includes('@')) {
            elements.emailInput?.classList.add('is-invalid');
            return;
        }

        elements.btnVerify.disabled = true;
        elements.btnVerify.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

        try {
            const response = await fetch(`/api/check-patient?email=${encodeURIComponent(email)}`);
            const data = await response.json();

            if (data.status === 'success') {
                elements.codeSection?.classList.remove('d-none');
                if (elements.feedback) elements.feedback.innerHTML = `<span class="text-primary small fw-bold">Code sent to ${email}</span>`;
                elements.emailInput.readOnly = true;
                elements.btnVerify.classList.add('d-none');
            }
        } catch (error) {
            if (elements.feedback) elements.feedback.innerHTML = `<span class="text-danger small">Verification service offline.</span>`;
            elements.btnVerify.disabled = false;
            elements.btnVerify.innerHTML = 'Verify';
        }
    });

    elements.btnCodeSubmit?.addEventListener('click', async () => {
        const code = elements.verificationCode?.value;
        const email = elements.emailInput?.value.trim();
        if (!code) return;

        elements.btnCodeSubmit.disabled = true;
        elements.btnCodeSubmit.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

        try {
            const response = await fetch('/api/clinical/patient/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `email=${encodeURIComponent(email)}&code=${encodeURIComponent(code)}`
            });
            const data = await response.json();

            if (data.status !== 'error') {
                elements.dynamicFields?.classList.remove('d-none');
                elements.submitBtn?.classList.remove('d-none');
                elements.codeSection?.classList.add('d-none');
                
                if (data.exists) {
                    if (elements.feedback) elements.feedback.innerHTML = `<div class="alert alert-success py-2 small mb-0 border-0 bg-success-subtle">Verified Patient: <strong>${data.full_name}</strong></div>`;
                    elements.regFields?.classList.add('d-none');
                    setRequired(false);
                } else {
                    if (elements.feedback) elements.feedback.innerHTML = `<div class="alert alert-warning py-2 small mb-0 border-0 bg-warning-subtle">No record found. Please register:</div>`;
                    elements.regFields?.classList.remove('d-none');
                    setRequired(true);
                }
            } else {
                if (elements.feedback) elements.feedback.innerHTML = `<span class="text-danger small">Invalid Code. Please check your email.</span>`;
                elements.btnCodeSubmit.disabled = false;
                elements.btnCodeSubmit.innerHTML = 'Verify';
            }
        } catch (e) { 
            console.error("Auth Failure", e); 
            elements.btnCodeSubmit.disabled = false;
        }
    });

    const setRequired = (val) => {
        elements.regInputs.forEach(el => { if (el) el.required = val; });
    };

    // --- 6. FINAL ADMISSION SUBMISSION ---
    elements.admissionForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const selectedFile = elements.fileInput?.files[0];
        if (!elements.fileInput?.files.length || Array.from(elements.fileInput.files).some(file => !isSupportedImage(file))) {
            showFileError('Upload at least one diagnostic image before initializing the session.');
            return;
        }
        const formData = new FormData(elements.admissionForm);
        
        elements.submitBtn.disabled = true;
        elements.submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

        try {
            const response = await fetch('/api/clinical/admission', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (result.status === 'success') {
                window.location.href = result.redirect_url; 
            } else {
                alert("Admission Failed: " + result.message);
                elements.submitBtn.disabled = false;
                elements.submitBtn.innerHTML = 'Initialize Session';
            }
        } catch (error) {
            console.error("Admission Error:", error);
            elements.submitBtn.disabled = false;
            elements.submitBtn.innerHTML = 'Initialize Session';
        }
    });

    // --- 7. MODAL RESET LOGIC ---
    elements.admissionModalEl?.addEventListener('hidden.bs.modal', () => {
        elements.admissionForm?.reset();
        elements.dynamicFields?.classList.add('d-none');
        elements.submitBtn?.classList.add('d-none');
        elements.codeSection?.classList.add('d-none');
        if (elements.feedback) elements.feedback.innerHTML = '';
        elements.filePreview?.classList.add('d-none');
        if (elements.selectedFilename) elements.selectedFilename.textContent = '';
        if (elements.fileStatus) {
            elements.fileStatus.textContent = 'Drop scan here or click to upload';
            elements.fileStatus.classList.remove('text-danger');
        }
        
        elements.btnVerify.disabled = false;
        elements.btnVerify.innerHTML = 'Verify';
        elements.btnVerify.classList.remove('d-none');
        elements.emailInput.readOnly = false;
        elements.btnCodeSubmit.disabled = false;
        elements.btnCodeSubmit.innerHTML = 'Verify';
    });
});