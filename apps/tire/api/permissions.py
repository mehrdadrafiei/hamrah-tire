from rest_framework.permissions import BasePermission, SAFE_METHODS

class TirePermission(BasePermission):
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user.is_authenticated:
            return False
            
        # ADMIN can do everything
        if request.user.role == 'ADMIN':
            return True
            
        # TECHNICAL can only view
        if request.user.role == 'TECHNICAL':
            return request.method in SAFE_METHODS
            
        # MINER can view their own tires and create repair requests
        if request.user.role == 'MINER':
            if request.method in SAFE_METHODS:
                return True
            # Allow creating repair requests
            if view.action == 'create_repair_request':
                return True
        
        return False

    def has_object_permission(self, request, view, obj):
        # ADMIN can do everything
        if request.user.role == 'ADMIN':
            return True
            
        # TECHNICAL can view all
        if request.user.role == 'TECHNICAL':
            return request.method in SAFE_METHODS
            
        # MINER can only view/modify their own tires
        if request.user.role == 'MINER':
            return obj.owner == request.user

        return False

class RepairRequestPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        if request.user.role == 'ADMIN':
            return True
            
        if request.user.role == 'MINER':
            if request.method == 'POST':  # Can create requests
                return True
            return request.method in SAFE_METHODS
            
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        return obj.requested_by == request.user

class TechnicalReportPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        if request.user.role == 'ADMIN':
            return True
            
        if request.user.role == 'TECHNICAL':
            return True
            
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        if request.user.role == 'TECHNICAL':
            return True
        return request.method in SAFE_METHODS