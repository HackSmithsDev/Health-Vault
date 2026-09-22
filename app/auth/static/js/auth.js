document.addEventListener('DOMContentLoaded', () => {
    console.log("⚡ Stitch AI: Vanilla Clinical Auth Engine Active");

    // Selectors
    const authSubtitle = document.getElementById('auth-subtitle');
    const signupEmail = document.getElementById('signup-email');
    const signupPass = document.getElementById('signup-password');

    /**
     * 1. CORE VIEW CONTROLLER
     */
    function switchAuthBox(targetId) {
        const targetBox = document.getElementById(targetId);
        if (!targetBox) {
            console.error(`Clinical Auth Error: Box #${targetId} not found.`);
            return;
        }

        // Hide all boxes using Bootstrap's d-none
        document.querySelectorAll('.auth-box').forEach(box => {
            box.classList.add('d-none');
            box.style.opacity = "0";
        });

        // Show target and trigger a simple fade-in
        targetBox.classList.remove('d-none');
        setTimeout(() => { targetBox.style.opacity = "1"; }, 10);

        const defaults = {
            'signin-box': 'Secure Practitioner Login',
            'signup-box-1': 'Establish Clinical Credentials',
            'signup-box-2': 'Institutional & Registry Details',
            'forgot-box': 'Request Secure Recovery Token',
            'verify-box': 'MFA: Identity Verification',
            'reset-box': 'Update System Credentials'
        };

        if (authSubtitle) {
            authSubtitle.innerText = defaults[targetId] || 'Stitch AI Clinical Portal';
        }
    }

    /**
     * 2. EVENT DELEGATION (Handles all .switch-box clicks)
     */
    document.addEventListener('click', (e) => {
        const switcher = e.target.closest('.switch-box');
        if (switcher) {
            e.preventDefault();
            const target = switcher.getAttribute('data-target');
            switchAuthBox(target);
        }
    });

    /**
     * 3. MULTI-STEP REGISTRY LOGIC
     */
    
    // Step 1 -> Step 2
    document.getElementById('btn-signup-next')?.addEventListener('click', async () => {
        const email = signupEmail.value;
        const pass = signupPass.value;
        const confirm = document.getElementById('signup-password-confirm').value;

        if (!email || !pass || pass !== confirm) {
            alert("Ensure hospital email is valid and passwords match.");
            return;
        }

        try {
            const response = await fetch(`/auth/check-email?email=${encodeURIComponent(email)}`);
            const data = await response.json();
            
            if (data.exists) {
                alert("This practitioner email is already registered.");
            } else {
                switchAuthBox('signup-box-2');
            }
        } catch (error) {
            alert("Registry Connection Failed. Check hospital network.");
        }
    });

    document.getElementById('btn-signup-back')?.addEventListener('click', () => switchAuthBox('signup-box-1'));

    // Final Submission
    document.getElementById('form-signup-final')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const signupData = Object.fromEntries(formData.entries());
        
        // Inject credentials from Step 1
        signupData.email = signupEmail.value;
        signupData.password = signupPass.value;
        signupData.experience = parseInt(signupData.experience);

        try {
            const response = await fetch('/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(signupData)
            });
            const result = await response.json();
            
            if (result.status === "success") {
                window.location.href = result.redirect;
            } else {
                alert("Registration Error: " + result.message);
            }
        } catch (err) {
            alert("Clinical Registry Error. Try again later.");
        }
    });

    /**
     * 4. MFA & LOGIN
     */
    document.getElementById('form-signin')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const loginData = {
            email: document.getElementById('signin-email').value,
            password: document.getElementById('signin-password').value
        };

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(loginData)
            });
            const result = await response.json();
            if (result.status === "success") window.location.href = result.redirect;
            else alert("Access Denied: Invalid credentials.");
        } catch (err) {
            alert("Login System Offline.");
        }
    });
});