document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('statusModal');
    if (modalEl) {
        const statusModal = new bootstrap.Modal(modalEl);
        // Add a tiny delay (300ms) to ensure everything is rendered smoothly
        setTimeout(() => {
            statusModal.show();
        }, 300);
    }
});