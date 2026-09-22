document.addEventListener('DOMContentLoaded', () => {
    const inputField = document.getElementById('chat-input-field');
    const sendBtn = document.getElementById('send-btn');
    const voiceBtn = document.getElementById('voice-input-btn');
    const fileInput = document.getElementById('hidden-file-input');
    const preview = document.getElementById('attachment-preview');
    const chatContainer = document.getElementById('chat-container');


    // --- AUTO-POLLING FOR BACKGROUND INTAKE ---
    const pollIntakeStatus = async () => {
        try {
            const response = await fetch(`/api/session/${CURRENT_SESSION_ID}/status`);
            const data = await response.json();

            if (data.status === 'Completed') {
                // Success! The AI has categorized the 1 of 5 subjects.
                // Refresh to show the new messages and the Diagnostic Report.
                window.location.reload(); 
            } else if (data.status === 'Error') {
                alert("Clinical intake failed: " + data.error_message);
            } else {
                // Still processing, check again in 3 seconds
                setTimeout(pollIntakeStatus, 3000);
            }
        } catch (e) {
            console.error("Polling error:", e);
        }
    };

    // Start polling only if the session is currently processing
    if (document.getElementById('session-badge').innerText.trim() === 'Processing') {
        pollIntakeStatus();
    }

    // --- FIX 1: ATTACHMENT LOGIC ---
    // This links the dropdown buttons to the hidden file input
    document.querySelectorAll('.attach-option').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const type = btn.getAttribute('data-type');
            if (type === 'img') fileInput.accept = "image/*";
            else if (type === 'doc') fileInput.accept = ".pdf";
            fileInput.click(); // Open the file picker
        });
    });

    fileInput.addEventListener('change', function() {
        preview.innerHTML = '';
        Array.from(this.files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = e => {
                    preview.insertAdjacentHTML('beforeend', `
                        <div class="position-relative">
                            <img src="${e.target.result}" class="preview-item rounded border">
                            <span class="badge bg-danger position-absolute top-0 start-100 translate-middle p-1" style="cursor:pointer" onclick="this.parentElement.remove()">×</span>
                        </div>`);
                };
                reader.readAsDataURL(file);
            } else {
                preview.insertAdjacentHTML('beforeend', `<div class="preview-item d-flex align-items-center justify-content-center bg-light border small">PDF</div>`);
            }
        });
        toggleButtons();
    });

    // --- FIX 2: VOICE DICTATION ---
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (Recognition) {
        const recognition = new Recognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        voiceBtn.addEventListener('click', () => {
            recognition.start();
            voiceBtn.classList.replace('btn-primary', 'btn-danger'); // Visual feedback
            inputField.placeholder = "Listening to clinical notes...";
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            inputField.value = transcript;
            toggleButtons(); 
            
            // Instead of immediate send, highlight the field so they can check it
            inputField.classList.add('is-valid');
            setTimeout(() => inputField.classList.remove('is-valid'), 2000);
            
            // If you still want auto-send, keep this:
            if (transcript.trim().length > 0) sendBtn.click(); 
        };
        recognition.onend = () => {
            voiceBtn.classList.replace('btn-danger', 'btn-primary');
            inputField.placeholder = "Enter clinical observations...";
        };
    }

    // --- BUTTON TOGGLING & ENTER KEY ---
    function toggleButtons() {
        const hasInput = inputField.value.trim().length > 0 || fileInput.files.length > 0;
        sendBtn.classList.toggle('d-none', !hasInput);
        voiceBtn.classList.toggle('d-none', hasInput);
    }

    inputField.addEventListener('input', toggleButtons);
    
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !sendBtn.classList.contains('d-none')) {
            e.preventDefault();
            sendBtn.click();
        }
    });

    let currentAction = 'chat'; // Default mode

    // --- 1. CHIP SELECTION ---
    document.querySelectorAll('.chip-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.chip-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentAction = btn.getAttribute('data-action');
        });
    });

    // --- 2. ORCHESTRATOR (Send Logic) ---
    sendBtn.addEventListener('click', async () => {
        const message = inputField.value.trim();
        const file = fileInput.files[0];
        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // A. PDF Gatekeeper
        if (file && file.type === 'application/pdf') {
            showFeatureNotice("PDF Clinical Records", "Clinical validation in progress. PDF support available soon.");
            return resetInputs();
        }

        // B. UI Update (User Side)
        let filePreviewUrl = (file && file.type.startsWith('image/')) ? URL.createObjectURL(file) : null;
        appendMessage('user', message || (file ? "Analyzing new scan..." : "Processing..."), now, null, filePreviewUrl, false);

        // C. Logic Branching
        if (file) {
            // Handle a new image analysis mid-session
            await handleMidSessionAnalysis(file, message, now);
        } else {
            // Handle command-based chat/differential/reporting
            await handleClinicalCommand(message, currentAction, now);
        }

        resetInputs();
        if (filePreviewUrl) setTimeout(() => URL.revokeObjectURL(filePreviewUrl), 10000);
    });

    // --- 3. MID-SESSION ANALYSIS (The "Analyze" Route) ---
    async function handleMidSessionAnalysis(file, message, timestamp) {
        const formData = new FormData();
        formData.append('file', file);
        if (message) formData.append('message', message);

        const thinkingId = showThinkingState("Vision Engine is processing new scan...");

        try {
            const response = await fetch(`/api/session/${CURRENT_SESSION_ID}/analyze`, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            removeThinkingState(thinkingId);

            if (data.status === 'success') {
                appendMessage('ai', data.ai_message, timestamp, data.report_data);
            }
        } catch (err) {
            handleErrorState(thinkingId, "Vision Engine Timeout.");
        }
    }

    // --- 4. CLINICAL COMMAND GATEWAY (The "Command" Route) ---
    async function handleClinicalCommand(query, action, timestamp) {
        const thinkingId = showThinkingState(`Specialist is preparing ${action.replace('_', ' ')}...`);

        try {
            const response = await fetch(`/api/session/${CURRENT_SESSION_ID}/ai/command`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, action: action })
            });
            const data = await response.json();
            removeThinkingState(thinkingId);

            if (data.status === 'success') {
                appendMessage('ai', data.ai_message, timestamp, { report_id: data.report_id });
                
                // Auto-reset to 'chat' if report was generated
                if (action === 'generate_report') {
                    document.querySelector('[data-action="chat"]').click();
                }
            }
        } catch (err) {
            handleErrorState(thinkingId, "Consultation Gateway Error.");
        }
    }

    // --- 5. UI UTILITIES ---

    function showThinkingState(text) {
        const id = 'thinking-' + Date.now();
        chatContainer.insertAdjacentHTML('beforeend', `
            <div id="${id}" class="message-group mb-4 ai-message d-flex flex-column align-items-start animate__animated animate__fadeIn">
                <div class="ai-thinking small ms-5 text-primary">
                    <i class="bi bi-cpu-fill me-2 spin"></i>${text}
                </div>
            </div>
        `);
        scrollToBottom();
        return id;
    }

    function removeThinkingState(id) {
        document.getElementById(id)?.remove();
    }

    function handleErrorState(id, text) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = `<div class="text-danger small ms-5">${text}</div>`;
    }

    function resetInputs() {
        inputField.value = '';
        preview.innerHTML = '';
        fileInput.value = '';
        toggleButtons();
    }

    function showFeatureNotice(featureName, text) {
        const noticeHtml = `
            <div class="alert alert-info border-primary shadow-sm mt-3 animate__animated animate__shakeX">
                <div class="d-flex align-items-center">
                    <i class="bi bi-info-circle-fill fs-5 me-3 text-primary"></i>
                    <div>
                        <h6 class="mb-0 fw-bold small">${featureName}</h6>
                        <p class="mb-0 smaller">${text}</p>
                    </div>
                </div>
            </div>
        `;
        chatContainer.insertAdjacentHTML('beforeend', noticeHtml);
        scrollToBottom();
    }

    function appendMessage(sender, text, time, reportData = null, fileUrl = null, isPdf = false) {
        let reportHtml = '';
        let fileHtml = '';

        // 1. Generate HTML for Files (Matched to your Jinja template)
        if (fileUrl) {
            if (isPdf) {
                fileHtml = `
                    <div class="mb-2 p-3 bg-light border rounded-3 d-flex align-items-center text-dark" 
                        style="cursor: pointer;" onclick="window.open('${fileUrl}', '_blank')">
                        <i class="bi bi-file-earmark-pdf-fill text-danger fs-3 me-3"></i>
                        <div class="d-flex flex-column overflow-hidden">
                            <span class="small fw-bold text-truncate">Clinical_Record.pdf</span>
                            <span class="smaller text-muted">Portable Document Format</span>
                        </div>
                    </div>`;
            } else {
                fileHtml = `
                    <div class="mb-2">
                        <img src="${fileUrl}" class="rounded-3 shadow-sm img-fluid border" 
                            style="max-height: 280px; width: 100%; object-fit: contain; cursor: zoom-in; background: #000;" 
                            onclick="window.open(this.src, '_blank')">
                    </div>`;
            }
        }

        // 2. Report Card logic (Upgraded with Confidence Progress Bar & Export Button)

        if (reportData && reportData.report_id) { // Added specific check for report_id
            const conf = reportData.confidence_score ? Math.round(reportData.confidence_score) : 0;
            const reportId = reportData.report_id;

            reportHtml = `
                <div class="diagnostic-card mt-3 p-3 border rounded-3 bg-white shadow-sm border-primary-subtle">
                    <div class="d-flex align-items-center justify-content-between border-bottom pb-2 mb-2">
                        <h6 class="m-0 small fw-bold text-uppercase text-primary">
                            <i class="bi bi-shield-check me-2"></i>Verified Analysis
                        </h6>
                        <button onclick="exportReport('${reportId}')" 
                                class="btn btn-sm btn-outline-primary py-0 px-2" 
                                title="Export PDF Report" style="font-size: 0.7rem;">
                            <i class="bi bi-file-earmark-pdf me-1"></i>Export
                        </button>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="text-secondary smaller">Impression:</span>
                        <span class="badge bg-primary text-white px-2 py-1" style="font-size: 0.75rem;">
                            ${reportData.prediction_label || 'Analysis Complete'}
                        </span>
                    </div>
                    <div class="progress" style="height: 6px;">
                        <div class="progress-bar bg-primary" style="width: ${conf}%"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-1">
                        <span class="smaller text-muted">AI Confidence</span>
                        <span class="smaller fw-bold text-primary">${conf}%</span>
                    </div>
                </div>`;
        } else {
            reportHtml = ''; // Explicitly clear it if no report_id exists
        }

        // 3. Formatting Text
        const formattedText = text ? `<div class="message-body text-break">${text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</div>` : '';

        const html = `
            <div class="message-group mb-4 ${sender}-message d-flex flex-column align-items-${sender === 'user' ? 'end' : 'start'}">
                ${sender === 'ai' ? `
                    <div class="d-flex align-items-center mb-1 ms-2">
                        <div class="bg-primary rounded-circle d-flex align-items-center justify-content-center me-2" style="width: 24px; height: 24px;">
                            <i class="bi bi-robot text-white" style="font-size: 0.8rem;"></i>
                        </div>
                        <span class="fw-bold small text-primary">Stitch AI Specialist</span>
                    </div>` : ''}
                <div class="message-bubble rounded-4 shadow-sm border ${sender === 'ai' ? 'border-start border-primary border-4' : ''}">
                    ${fileHtml}
                    ${formattedText}
                    ${reportHtml}
                </div>
                <small class="text-muted mt-1 px-2" style="font-size: 0.7rem;">${time}</small>
            </div>`;
        
        chatContainer.insertAdjacentHTML('beforeend', html);
        scrollToBottom();
    }

    function scrollToBottom() {
        setTimeout(() => {
            window.requestAnimationFrame(() => {
                chatContainer.scrollTo({
                    top: chatContainer.scrollHeight,
                    behavior: 'smooth'
                });
            });
        }, 50);
    }
    scrollToBottom();
});



function exportReport(reportId) {
    if (!reportId) {
        console.error("Report ID is missing");
        return;
    }
    // Opens the export route in a new tab/hidden download stream
    window.open(`/api/report/${reportId}/export`, '_blank');
}