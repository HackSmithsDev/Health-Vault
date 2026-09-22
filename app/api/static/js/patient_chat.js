/**
 * PATIENT LIAISON CHAT ENGINE
 * Logic for private patient-AI interactions.
 */

// 1. Keep this GLOBAL so it's accessible everywhere
function appendSupportMessage(sender, text) {
    const chatContainer = document.getElementById('supportChatContainer');
    if (!chatContainer) return;

    const html = `
        <div class="message-group mb-4 ${sender}-message d-flex flex-column align-items-${sender === 'patient' ? 'end' : 'start'}">
            <div class="message-bubble p-3 rounded-4 shadow-sm border ${sender === 'patient' ? 'bg-primary text-white' : 'bg-white text-dark'}" style="max-width: 85%;">
                ${text}
            </div>
            <small class="text-muted mt-1 px-2" style="font-size: 0.7rem;">Just now</small>
        </div>`;
    
    chatContainer.insertAdjacentHTML('beforeend', html);
    
    // Smooth scroll to the new message
    chatContainer.scrollTo({ 
        top: chatContainer.scrollHeight, 
        behavior: 'smooth' 
    });
}

// 2. Wrap initialization in DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('supportChatContainer');
    const chatForm = document.getElementById('supportChatForm');
    const patientInput = document.getElementById('patientInput');

    // Initial scroll to bottom (handles page refreshes)
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    if (chatForm) {
        chatForm.onsubmit = async (e) => {
            e.preventDefault();
            const text = patientInput.value.trim();
            if (!text) return;

            // Step 1: UI Update
            appendSupportMessage('patient', text);
            patientInput.value = '';

            // Step 2: API Call to the Liaison Route
            try {
                // We use the dynamic session ID injected by Jinja in the template
                const response = await fetch(`/api/support/${window.currentSessionId}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });

                if (!response.ok) throw new Error('Network response was not ok');

                const data = await response.json();
                appendSupportMessage('ai', data.reply);
                
            } catch (err) {
                console.error("Support Chat Error:", err);
                // Optional: Show a small error toast/message to the patient
            }
        };
    }
});