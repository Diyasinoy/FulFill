function logout() {
    localStorage.removeItem('userToken');
    localStorage.removeItem('userEmail');
    window.location.href = '/login';
}

function checkAuth() {
    const token = localStorage.getItem('userToken');
    if (!token) {
        window.location.href = '/login';
        return false;
    }
    
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.exp < Date.now() / 1000) {
            logout();
            return false;
        }
    } catch (e) {
        logout();
        return false;
    }
    
    return true;
}

function getAuthHeaders() {
    const token = localStorage.getItem('userToken');
    if (!token) {
        logout();
        return {};
    }
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// In your login success handler
if (response.ok) {
    localStorage.setItem('userToken', data.token);
    if (remember) {
        localStorage.setItem('userEmail', email);
    }
    window.location.href = '/home';  // Changed from index to home
}

// Add this function to your existing auth.js
function isAuthenticated() {
    const token = localStorage.getItem('userToken');
    if (!token) {
        return false;
    }
    
    try {
        // Check if token is expired
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.exp < Date.now() / 1000) {
            logout();
            return false;
        }
        return true;
    } catch (e) {
        logout();
        return false;
    }
} 