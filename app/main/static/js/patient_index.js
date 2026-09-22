/* ==========================================================================
   PATIENT PORTAL INTERACTIVE ENGINE
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Real-time Health Record Filter
    const searchInput = document.querySelector('#recordSearch');
    const records = document.querySelectorAll('.health-record-item');

    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const term = e.target.value.toLowerCase();
            
            records.forEach(record => {
                const title = record.querySelector('.fw-bold').textContent.toLowerCase();
                const unit = record.querySelector('.badge').textContent.toLowerCase();
                
                if (title.includes(term) || unit.includes(term)) {
                    record.style.display = 'block';
                    record.classList.add('animate-in');
                } else {
                    record.style.display = 'none';
                }
            });
        });
    }

    // 2. Metric Counter Animation
    const counters = document.querySelectorAll('.metric-value');
    counters.forEach(counter => {
        const target = +counter.getAttribute('data-target');
        const count = +counter.innerText;
        const speed = 200; // Lower is faster

        const updateCount = () => {
            const inc = target / speed;
            if (count < target) {
                counter.innerText = Math.ceil(count + inc);
                setTimeout(updateCount, 1);
            } else {
                counter.innerText = target;
            }
        };
        updateCount();
    });

    // 3. Insight Card Interactivity
    const insightCard = document.querySelector('.insight-card');
    if (insightCard) {
        insightCard.addEventListener('mouseenter', () => {
            insightCard.style.cursor = 'pointer';
        });
        
        // Example: Copy insight to clipboard
        insightCard.addEventListener('click', () => {
            const text = insightCard.querySelector('p').innerText;
            navigator.clipboard.writeText(text).then(() => {
                showToast("Insight copied to clipboard!");
            });
        });
    }
});

// Helper for UI Feedback
function showToast(message) {
    // Check if a toast container exists, or create a simple alert
    console.log("Portal Notice:", message);
    // You could trigger a Bootstrap Toast here
}