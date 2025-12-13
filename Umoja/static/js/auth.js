/**
 * Umoja Farmer Connect - Authentication JavaScript
 * Handles login, registration, and authentication
 */

// Check if user is logged in on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    initializeAuthForms();
});

/**
 * Check authentication status
 */
function checkAuthStatus() {
    const user = localStorage.getItem('ufc_user');
    const token = localStorage.getItem('ufc_token');
    
    if (user && token) {
        updateUIForLoggedInUser(JSON.parse(user));
    }
}

/**
 * Initialize authentication forms
 */
function initializeAuthForms() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Registration form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Logout buttons
    const logoutButtons = document.querySelectorAll('.logout-btn');
    logoutButtons.forEach(btn => {
        btn.addEventListener('click', handleLogout);
    });
}

/**
 * Handle login form submission
 */
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const rememberMe = document.getElementById('rememberMe')?.checked;
    
    // Validation
    if (!window.UmojaFC.validateEmail(email)) {
        window.UmojaFC.showToast('Please enter a valid email address', 'danger');
        return;
    }
    
    if (password.length < 6) {
        window.UmojaFC.showToast('Password must be at least 6 characters', 'danger');
        return;
    }
    
    window.UmojaFC.showLoader();
    
    try {
        // Simulate API call (replace with actual API endpoint)
        await simulateAPICall();
        
        // Mock successful login
        const userData = {
            id: 1,
            name: 'John Farmer',
            email: email,
            type: 'farmer',
            phone: '+254712345678',
            location: 'Nairobi, Kenya'
        };
        
        const token = 'mock_jwt_token_' + Date.now();
        
        // Store user data
        localStorage.setItem('ufc_user', JSON.stringify(userData));
        localStorage.setItem('ufc_token', token);
        
        if (rememberMe) {
            localStorage.setItem('ufc_remember', 'true');
        }
        
        window.UmojaFC.showToast('Login successful!', 'success');
        
        // Redirect based on user type
        setTimeout(() => {
            if (userData.type === 'farmer') {
                window.location.href = '/pages/farmer/dashboard.html';
            } else {
                window.location.href = '/pages/broker/dashboard.html';
            }
        }, 1000);
        
    } catch (error) {
        window.UmojaFC.showToast('Login failed. Please try again.', 'danger');
        console.error('Login error:', error);
    } finally {
        window.UmojaFC.hideLoader();
    }
}

/**
 * Handle registration form submission
 */
async function handleRegister(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('registerName').value,
        email: document.getElementById('registerEmail').value,
        phone: document.getElementById('registerPhone').value,
        password: document.getElementById('registerPassword').value,
        confirmPassword: document.getElementById('confirmPassword').value,
        userType: document.getElementById('userType').value,
        location: document.getElementById('registerLocation').value,
        terms: document.getElementById('termsCheck').checked
    };
    
    // Validation
    if (!formData.name || formData.name.length < 3) {
        window.UmojaFC.showToast('Please enter a valid name', 'danger');
        return;
    }
    
    if (!window.UmojaFC.validateEmail(formData.email)) {
        window.UmojaFC.showToast('Please enter a valid email address', 'danger');
        return;
    }
    
    if (!window.UmojaFC.validatePhone(formData.phone)) {
        window.UmojaFC.showToast('Please enter a valid Kenyan phone number', 'danger');
        return;
    }
    
    if (formData.password.length < 8) {
        window.UmojaFC.showToast('Password must be at least 8 characters', 'danger');
        return;
    }
    
    if (formData.password !== formData.confirmPassword) {
        window.UmojaFC.showToast('Passwords do not match', 'danger');
        return;
    }
    
    if (!formData.terms) {
        window.UmojaFC.showToast('Please accept the terms and conditions', 'danger');
        return;
    }
    
    window.UmojaFC.showLoader();
    
    try {
        // Simulate API call
        await simulateAPICall();
        
        window.UmojaFC.showToast('Registration successful! Please login.', 'success');
        
        setTimeout(() => {
            window.location.href = '/pages/auth/login.html';
        }, 1500);
        
    } catch (error) {
        window.UmojaFC.showToast('Registration failed. Please try again.', 'danger');
        console.error('Registration error:', error);
    } finally {
        window.UmojaFC.hideLoader();
    }
}

/**
 * Handle logout
 */
function handleLogout(e) {
    e.preventDefault();
    
    // Clear local storage
    localStorage.removeItem('ufc_user');
    localStorage.removeItem('ufc_token');
    localStorage.removeItem('ufc_remember');
    
    window.UmojaFC.showToast('Logged out successfully', 'info');
    
    setTimeout(() => {
        window.location.href = '/index.html';
    }, 1000);
}

/**
 * Update UI for logged in user
 */
function updateUIForLoggedInUser(user) {
    const navbarNav = document.querySelector('.navbar-nav');
    if (navbarNav) {
        const loginBtn = navbarNav.querySelector('a[href*="login"]')?.parentElement;
        const registerBtn = navbarNav.querySelector('a[href*="register"]')?.parentElement;
        
        if (loginBtn) loginBtn.style.display = 'none';
        if (registerBtn) registerBtn.style.display = 'none';
        
        // Add user menu
        const userMenu = document.createElement('li');
        userMenu.className = 'nav-item dropdown';
        userMenu.innerHTML = `
            <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                <i class="bi bi-person-circle me-1"></i>${user.name}
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
                <li><a class="dropdown-item" href="/pages/${user.type}/dashboard.html">
                    <i class="bi bi-speedometer2 me-2"></i>Dashboard
                </a></li>
                <li><a class="dropdown-item" href="/pages/${user.type}/profile.html">
                    <i class="bi bi-person me-2"></i>Profile
                </a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item logout-btn" href="#">
                    <i class="bi bi-box-arrow-right me-2"></i>Logout
                </a></li>
            </ul>
        `;
        navbarNav.appendChild(userMenu);
        
        // Re-initialize logout button
        userMenu.querySelector('.logout-btn').addEventListener('click', handleLogout);
    }
}

/**
 * Get current user
 */
function getCurrentUser() {
    const user = localStorage.getItem('ufc_user');
    return user ? JSON.parse(user) : null;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!localStorage.getItem('ufc_token');
}

/**
 * Require authentication
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/pages/auth/login.html';
    }
}

/**
 * Simulate API call (for development)
 */
function simulateAPICall() {
    return new Promise((resolve) => {
        setTimeout(() => resolve(), 1500);
    });
}

// Export functions
window.UmojaAuth = {
    getCurrentUser,
    isAuthenticated,
    requireAuth,
    handleLogout
};