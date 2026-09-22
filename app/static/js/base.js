document.addEventListener('DOMContentLoaded', function() {
    // --- Global Selectors ---
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const themeToggle = document.getElementById('theme-toggle');
    const htmlEl = document.documentElement;
    const menuToggle = document.getElementById('menu-toggle');
    const menuClose = document.getElementById('menu-close');

    /**
     * 1. SIDEBAR & LAYOUT LOGIC
     * Optimized for rapid navigation between clinical units.
     */
    function toggleSidebar() {
        // Toggle the sidebar classes
        sidebar.classList.toggle('sidebar-hidden');
        sidebar.classList.toggle('sidebar-visible');
        
        // Toggle the overlay visibility
        // Using d-none (Bootstrap) and your custom overlay-active
        overlay.classList.toggle('d-none');
        overlay.classList.toggle('overlay-active');
        
        // Toggle the hamburger icon visibility
        const icon = menuToggle.querySelector('i');
        if (icon) {
            icon.classList.toggle('opacity-0'); // Better than d-none to keep layout stable
        }
    }

    [menuToggle, menuClose, overlay].forEach(el => {
        el?.addEventListener('click', toggleSidebar);
    });

    // Close sidebar when clicking a mobile navigation link
    document.querySelectorAll('.close-sidebar-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (window.innerWidth < 992) toggleSidebar();
        });
    });

    /**
     * 2. DARK MODE (Clinical Eye-Strain Reduction)
     */
    const currentTheme = htmlEl.getAttribute('data-bs-theme');
    syncThemeIcon(currentTheme);
    
    themeToggle?.addEventListener('click', (e) => {
        e.preventDefault();
        const activeTheme = htmlEl.getAttribute('data-bs-theme');
        const newTheme = activeTheme === 'light' ? 'dark' : 'light';
        
        // Apply to DOM
        htmlEl.setAttribute('data-bs-theme', newTheme);
        // Save for next page load
        localStorage.setItem('theme', newTheme);
        // Update Icon
        syncThemeIcon(newTheme);
    });

    function syncThemeIcon(theme) {
        const icon = themeToggle?.querySelector('i');
        if (!icon) return;

        if (theme === 'dark') {
            icon.classList.replace('bi-moon-stars', 'bi-sun-fill');
            // Add a subtle glow for the clinical dark mode
            icon.style.color = '#ffc107'; 
        } else {
            icon.classList.replace('bi-sun-fill', 'bi-moon-stars');
            icon.style.color = '';
        }
    }

    /**
     * 3. DIAGNOSTIC LITERACY NAVIGATION
     * Logic to handle the 5-subject curriculum (Pulmonology, Radiology, etc.)
     */
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link, .sidebar-session-link').forEach(link => {
        const href = link.getAttribute('href');
        // Check if current path matches the link or is a sub-path of the link
        if (href && href !== '#' && (currentPath === href || currentPath.startsWith(href))) {
            link.classList.add('active', 'bg-primary-subtle', 'text-primary', 'fw-bold');
            
            // Auto-expand the specific Medical Subject accordion
            const collapse = link.closest('.collapse');
            if (collapse) {
                const bsCollapse = new bootstrap.Collapse(collapse, { toggle: false });
                bsCollapse.show();
                // Rotate the chevron icon if present
                const trigger = document.querySelector(`[data-bs-target="#${collapse.id}"] .bi-chevron-right`);
                if (trigger) trigger.style.transform = "rotate(90deg)";
            }
        }
    });

    /**
     * 4. NEW PATIENT ADMISSION (MODAL LOGIC)
     * Switches routes based on whether we are adding to a unit or creating a new one.
     */
    const projectSelector = document.getElementById('project-selector');
    projectSelector?.addEventListener('change', function() {
        const inputGroup = document.getElementById('new-project-input-group');
        const form = document.getElementById('research-init-form');
        const newNameInput = document.getElementById('new_project_name');

        if (this.value === "NEW_PROJECT") {
            inputGroup.classList.remove('d-none');
            newNameInput.required = true;
            form.action = '/api/clinical/new-unit';
        } else {
            inputGroup.classList.add('d-none');
            newNameInput.required = false;
            form.action = '/api/clinical/add-admission';
        }
    });

    /**
     * 5. PROFILE & AVATAR (AJAX)
     */
    document.getElementById('avatar-upload')?.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file || !file.type.startsWith('image/')) return;

        const formData = new FormData();
        formData.append('avatar', file);

        try {
            const response = await fetch('/update-user-avatar', { method: 'POST', body: formData });
            if (response.ok) location.reload();
        } catch (err) {
            console.error("Avatar upload failed");
        }
    });

    // Logout handling
    document.getElementById('logout-link')?.addEventListener('click', async (e) => {
        e.preventDefault();
        
        try {
            const response = await fetch("/logout", { 
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' } 
            });

            // Robust check for JSON content
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const data = await response.json();
                if (data.redirect) window.location.href = data.redirect;
            } else {
                // If we got HTML (likely already redirected), just manually go to login
                window.location.href = "/auth/login";
            }
        } catch (err) {
            // Fallback for network issues
            window.location.href = "/auth/login";
        }
    });
});