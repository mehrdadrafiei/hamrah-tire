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
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                // Add CSRF token for non-GET requests
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", $('meta[name="csrf-token"]').attr('content'));
                }
                // Add Authorization header if token exists
                const token = localStorage.getItem('access_token');
                if (token) {
                    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                }
            }
        });
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
    // This is causing problems - remove it
    // if (!AuthUtils.isAuthenticated() && window.location.pathname !== '/accounts/login/') {
    //     window.location.href = '/accounts/login/';
    //     return;
    // }

    // Keep this part
    $('#logoutBtn').click(function(e) {
        e.preventDefault();
        AuthUtils.logout();
    });

    const userRole = AuthUtils.getUserRole();
    if (userRole) {
        $('.role-specific').hide();
        $(`.role-${userRole.toLowerCase()}`).show();
    }
});