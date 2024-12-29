# apps/accounts/decorators.py
from functools import wraps
from pyexpat.errors import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

User = get_user_model()

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # First check if user is authenticated
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Then check JWT token if it exists
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                jwt_auth = JWTAuthentication()
                try:
                    jwt_auth_result = jwt_auth.authenticate(request)
                    if jwt_auth_result:
                        user, token = jwt_auth_result
                        request.user = user
                except:
                    pass

            # Check if user has required role
            if request.user.role not in allowed_roles:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator