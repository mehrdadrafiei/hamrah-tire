from rest_framework import permissions

class IsAdminOrSelf(permissions.BasePermission):
    """
    Custom permission to only allow:
    1. Admin users to access any profile
    2. Regular users to access their own profile
    """
    
    def has_permission(self, request, view):
        # Authenticated users can see their own profile
        # Admin users can see all profiles
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin users can access any profile
        if request.user.role == 'ADMIN':
            return True
            
        # Regular users can only access their own profile
        return obj.id == request.user.id