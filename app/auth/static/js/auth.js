document.addEventListener('DOMContentLoaded', () => {
    console.log("⚡ Health Vault: Vanilla Clinical Auth Engine Active");

    // Selectors
    const authSubtitle = document.getElementById('auth-subtitle');
    const signupEmail = document.getElementById('signup-email');
    const signupPass = document.getElementById('signup-password');

    // Password Recovery State
    let recoveryEmail = '';
    let verifiedOtp = '';
    let recoveryStage = 'request'; // 'request' | 'verify'

    /**
     * 1. CORE VIEW CONTROLLER
     */
    function switchAuthBox(targetId) {
        const targetBox = document.getElementById(targetId);
        if (!targetBox) {
            console.error(`Clinical Auth Error: Box #${targetId} not found.`);
            return;
        }

        // Hide all boxes
        document.querySelectorAll('.auth-box').forEach(box => {
            box.classList.add('d-none');
            box.style.opacity = "0";
        });

        // Show target and trigger smooth fade-in
        targetBox.classList.remove('d-none');
        setTimeout(() => { targetBox.style.opacity = "1"; }, 10);

        const defaults = {
            'signin-box': 'Secure Practitioner Login',
            'signup-box-1': 'Establish Clinical Credentials',
            'signup-box-2': 'Institutional & Registry Details',
            'forgot-box': 'Account Recovery Protocol',
            'verify-box': 'MFA: Identity Verification',
            'reset-box': 'Update System Credentials'
        };

        if (authSubtitle) {
            authSubtitle.innerText = defaults[targetId] || 'Health Vault Clinical Portal';
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
            
            // Reset recovery form state if user navigates away
            if (target === 'forgot-box') {
                resetForgotState();
            }
            switchAuthBox(target);
        }
    });

    function resetForgotState() {
        recoveryStage = 'request';
        recoveryEmail = '';
        verifiedOtp = '';
        const otpSection = document.getElementById('otp-expand-section');
        const emailInput = document.getElementById('forgot-email');
        const actionBtn = document.getElementById('btn-forgot-action');
        const desc = document.getElementById('forgot-desc');

        if (otpSection) otpSection.classList.add('d-none');
        if (emailInput) {
            emailInput.disabled = false;
            emailInput.value = '';
        }
        if (actionBtn) actionBtn.innerText = 'Request Token';
        if (desc) desc.innerText = 'Enter your hospital email to receive a secure recovery token.';
    }

    /**
     * 3. MULTI-STEP REGISTRY LOGIC
     */
    document.getElementById('btn-signup-next')?.addEventListener('click', async () => {
        const email = signupEmail.value.trim();
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

    document.getElementById('form-signup-final')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const signupData = Object.fromEntries(formData.entries());
        
        signupData.email = signupEmail.value.trim();
        signupData.password = signupPass.value;
        signupData.experience = parseInt(signupData.experience, 10) || 0;

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
                alert("Registration Error: " + (result.message || "Failed"));
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
            email: document.getElementById('signin-email').value.trim(),
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

    /**
     * 5. EXPANDABLE PASSWORD RECOVERY PIPELINE
     */
    document.getElementById('form-forgot')?.addEventListener('submit', async function(e) {
        e.preventDefault();

        const emailInput = document.getElementById('forgot-email');
        const otpSection = document.getElementById('otp-expand-section');
        const otpInput = document.getElementById('recovery-otp');
        const actionBtn = document.getElementById('btn-forgot-action');
        const desc = document.getElementById('forgot-desc');

        // STAGE 1: Check Email & Dispatch Token
        if (recoveryStage === 'request') {
            recoveryEmail = emailInput.value.trim();
            if (!recoveryEmail) return;

            actionBtn.disabled = true;
            actionBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Validating...';

            try {
                const res = await fetch('/auth/forget_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: recoveryEmail })
                });
                const data = await res.json();

                if (res.ok && data.status === 'success') {
                    // Lock email input, expand the OTP section
                    emailInput.disabled = true;
                    otpSection.classList.remove('d-none');
                    if (otpInput) otpInput.required = true;
                    
                    actionBtn.innerText = 'Verify Token';
                    desc.innerText = `Token dispatched to ${recoveryEmail}. Enter it below:`;
                    recoveryStage = 'verify';
                    
                    setTimeout(() => otpInput?.focus(), 100);
                } else {
                    alert(data.message || 'Email not found in our records.');
                }
            } catch (err) {
                alert('Network failure. Could not connect to verification service.');
            } finally {
                actionBtn.disabled = false;
                if (recoveryStage === 'request') actionBtn.innerText = 'Request Token';
            }
            return;
        }

        // STAGE 2: Verify Token & Redirect to Reset Box
        if (recoveryStage === 'verify') {
            const enteredOtp = otpInput.value.trim();
            if (enteredOtp.length !== 6) {
                alert('Please enter a valid 6-digit verification code.');
                return;
            }

            actionBtn.disabled = true;
            actionBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Verifying...';

            try {
                const res = await fetch('/auth/verify_otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: recoveryEmail,
                        otp: enteredOtp
                    })
                });
                const data = await res.json();

                if (res.ok && data.status === 'success') {
                    verifiedOtp = enteredOtp;
                    // Transition to Reset Box
                    switchAuthBox('reset-box');
                } else {
                    alert(data.message || 'Invalid or expired token.');
                }
            } catch (err) {
                alert('Failed to verify token with server.');
            } finally {
                actionBtn.disabled = false;
                actionBtn.innerText = 'Verify Token';
            }
        }
    });

    /**
     * 6. FINAL RESET PASSWORD SUBMISSION
     */
    document.getElementById('form-reset-password')?.addEventListener('submit', async function(e) {
        e.preventDefault();

        const newPass = document.getElementById('reset-new-password').value;
        const confirmPass = document.getElementById('reset-confirm-password').value;

        if (newPass !== confirmPass) {
            alert('Passwords do not match.');
            return;
        }

        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;

        try {
            const res = await fetch('/auth/reset_password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: recoveryEmail,
                    otp: verifiedOtp,
                    password: newPass
                })
            });
            const data = await res.json();

            if (res.ok && data.status === 'success') {
                alert('Password reset successfully. Please log in.');
                resetForgotState();
                switchAuthBox('signin-box');
            } else {
                alert('Error: ' + (data.message || 'Failed to update password.'));
            }
        } catch (err) {
            alert('System offline. Could not complete password reset.');
        } finally {
            submitBtn.disabled = false;
        }
    });
});