// static/js/auth.js

const AuthUtils = {
    isAuthenticated: function() {
        return !!localStorage.getItem('access_token');
    },

    getUserRole: function() {
        return localStorage.getItem('user_role');
    },

    logout: function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_role');
        window.location.href = '/accounts/login/';
    },

    setupAjaxHeaders: function() {
        // Get CSRF token
        function getCsrfToken() {
            // Try to get from form
            const tokenInputs = document.querySelectorAll('[name=csrfmiddlewaretoken]');
            if (tokenInputs && tokenInputs.length > 0) {
                return tokenInputs[0].value;
            }
            
            // Fallback to cookie
            return AuthUtils.getCookie('csrftoken');
        }

        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                // Add CSRF token if needed
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    const csrfToken = getCsrfToken();
                    if (csrfToken) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken);
                    }
                }
                // Add Authorization if token exists
                const token = localStorage.getItem('access_token');
                if (token) {
                    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                }
            }
        });
    },

    getCookie: function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    handleUnauthorized: function() {
        $(document).ajaxError(function(event, jqXHR, settings, thrownError) {
            if (jqXHR.status === 401) {
                const refreshToken = localStorage.getItem('refresh_token');
                if (refreshToken) {
                    $.ajax({
                        url: '/api/auth/token/refresh/',
                        method: 'POST',
                        data: { refresh: refreshToken },
                        success: function(response) {
                            localStorage.setItem('access_token', response.access);
                            // Retry the original request that failed
                            settings.headers = {
                                ...settings.headers,
                                'Authorization': `Bearer ${response.access}`
                            };
                            $.ajax(settings);
                        },
                        error: function() {
                            // If refresh fails, clear all tokens and redirect to login
                            AuthUtils.logout();
                        }
                    });
                } else {
                    // No refresh token available, redirect to login
                    AuthUtils.logout();
                }
            }
        });
    },

    redirectToDashboard: function() {
        const role = this.getUserRole();
        const token = localStorage.getItem('access_token');
        
        if (!role || !token) {
            this.logout();
            return;
        }

        let url = '/';
        switch(role) {
            case 'ADMIN':
                url = '/dashboard/admin/';
                break;
            case 'MINER':
                url = '/dashboard/miner/';
                break;
            case 'TECHNICAL':
                url = '/dashboard/technical/';
                break;
        }

        window.location.href = url;
    },

    checkAuthAndRedirect: function() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            this.logout();
            return;
        }

        $.ajax({
            url: '/api/users/me/',
            method: 'GET',
            success: (response) => {
                localStorage.setItem('user_role', response.role);
                this.redirectToDashboard();
            },
            error: () => {
                this.logout();
            }
        });
    }
};

// Initialize authentication utilities
$(document).ready(function() {
    try {
        // Setup AJAX headers - Modified to handle missing CSRF token gracefully
        AuthUtils.setupAjaxHeaders = function() {
            // Get CSRF token from various sources
            const csrfToken = 
                document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                AuthUtils.getCookie('csrftoken');

            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    // Add CSRF token if needed
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        if (csrfToken) {
                            xhr.setRequestHeader("X-CSRFToken", csrfToken);
                        }
                    }
                    // Add Authorization token if exists
                    const token = localStorage.getItem('access_token');
                    if (token) {
                        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                    }
                }
            });
        };

        // Initialize headers
        AuthUtils.setupAjaxHeaders();
        
        // Handle unauthorized access
        AuthUtils.handleUnauthorized();

        // Handle logout button if it exists
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function(e) {
                e.preventDefault();
                AuthUtils.logout();
            });
        }

        // Show/hide role-specific elements
        const userRole = AuthUtils.getUserRole();
        if (userRole) {
            $('.role-specific').hide();
            $(`.role-${userRole.toLowerCase()}`).show();
        }
    } catch (error) {
        console.error('Auth initialization error:', error);
    }
});