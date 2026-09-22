/**
 * STITCH AI - CLINICAL SETTINGS ENGINE (2026)
 * Synchronizes AI inference modes, UI scaling, and reporting standards.
 */

document.addEventListener('DOMContentLoaded', () => {
    const settingsForm = document.getElementById('settings-form');
    const saveBtn = document.getElementById('save-settings-btn');
    const fontSizeRange = document.getElementById('fontSizeRange');
    const fontSizeVal = document.getElementById('fontSizeVal');
    const syncStatusText = document.getElementById('sync-status-text');

    // --- 1. LIVE UI FEEDBACK (PRESERVED) ---
    fontSizeRange?.addEventListener('input', (e) => {
        if (fontSizeVal) fontSizeVal.textContent = e.target.value;
        document.body.style.fontSize = `${e.target.value}px`; // Live Scaling
    });

    // --- 2. ADDED REACTIVE TRIGGER (FOR SETTINGSDATA TABLE) ---
    const autoSaveField = async (payload) => {
        try {
            const response = await fetch('/settings/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (response.ok && syncStatusText) {
                const originalText = syncStatusText.innerHTML;
                syncStatusText.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Changes Synced';
                setTimeout(() => { syncStatusText.innerHTML = originalText; }, 2000);
            }
        } catch (err) { console.error("Field sync failed:", err); }
    };

    document.querySelectorAll('.reactive-setting').forEach(el => {
        el.addEventListener('change', (e) => {
            const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
            autoSaveField({ [e.target.name]: val });
        });
    });

    // --- 3. RESET TRIGGER (FOR PYTHON RESET ROUTE) ---
    document.getElementById('reset-settings-btn')?.addEventListener('click', async () => {
        if (!confirm("Reset to default system state?")) return;
        const resp = await fetch('/settings/reset', { method: 'POST' });
        if (resp.ok) window.location.reload();
    });

    // --- 4. REGISTRY SYNCHRONIZATION (ORIGINAL LOGIC) ---
    settingsForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const originalHTML = saveBtn.innerHTML;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Deploying Updates...';
        saveBtn.disabled = true;

        const formData = new FormData(settingsForm);
        const payload = {
            intelligence_mode: formData.get('intelligence_mode'),
            language: formData.get('language'),
            font_style: formData.get('font_style'),
            font_size: formData.get('font_size'),
            header_style: formData.get('header_style'),
            show_digital_stamp: document.getElementById('showStamp')?.checked ?? false
        };

        try {
            const response = await fetch('/settings/update', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (response.ok && result.status === 'success') {
                saveBtn.innerHTML = '<i class="bi bi-check-lg me-2"></i>System Synchronized';
                saveBtn.classList.replace('btn-primary', 'btn-success');
                setTimeout(() => {
                    saveBtn.classList.replace('btn-success', 'btn-primary');
                    saveBtn.innerHTML = originalHTML;
                    saveBtn.disabled = false;
                }, 2000);
            } else { throw new Error(result.message); }
        } catch (error) {
            saveBtn.innerHTML = 'Sync Error';
            saveBtn.classList.replace('btn-primary', 'btn-danger');
            setTimeout(() => {
                saveBtn.classList.replace('btn-danger', 'btn-primary');
                saveBtn.innerHTML = originalHTML;
                saveBtn.disabled = false;
            }, 3000);
        }
    });

    // --- 5. COMPLIANCE & REVOCATION (ORIGINAL LOGIC) ---
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    confirmDeleteBtn?.addEventListener('click', async () => {
        if (!confirm("CRITICAL: Purge all clinical records?")) return;
        confirmDeleteBtn.disabled = true;
        confirmDeleteBtn.innerHTML = 'Revoking Access...';
        try {
            const response = await fetch('/delete_account', { method: 'DELETE' });
            if (response.ok) window.location.href = '/auth/logout?reason=decommissioned';
        } catch (err) { confirmDeleteBtn.disabled = false; }
    });

    // --- 6. PRACTITIONER SUPPORT (ORIGINAL LOGIC) ---
    const submitTicketBtn = document.getElementById('submitTicketBtn');
    submitTicketBtn?.addEventListener('click', async () => {
        const issueType = document.getElementById('issue_type').value;
        const details = document.getElementById('supportDetails').value.trim();
        if (!details) return alert("Details required.");

        submitTicketBtn.disabled = true;
        const formData = new FormData();
        formData.append('issue', issueType);
        formData.append('details', details);

        try {
            const response = await fetch('/review-support', { method: 'POST', body: formData });
            if (response.ok) {
                submitTicketBtn.classList.replace('btn-primary', 'btn-success');
                submitTicketBtn.innerHTML = 'Reported';
                setTimeout(() => { 
                    bootstrap.Modal.getInstance(document.getElementById('supportModal')).hide();
                }, 1000);
            }
        } catch (err) { submitTicketBtn.disabled = false; }
    });
});