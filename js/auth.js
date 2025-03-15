function checkAuth() {
    const token = localStorage.getItem('userToken');
    if (!token) {
        return false;
    }
    
    // Check if token is expired
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

function logout() {
    localStorage.removeItem('userToken');
    localStorage.removeItem('userEmail');
    window.location.href = 'login.html';
}

// Add auth headers to all API requests
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