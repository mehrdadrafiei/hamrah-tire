from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from rest_framework.authentication import SessionAuthentication
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except Exception:
            return None

class EmailVerifiedAuthentication(JWTAuthentication):
    def authenticate(self, request):
        auth_response = super().authenticate(request)
        if auth_response is None:
            return None

        user, token = auth_response
        if not user.email_verified:
            return None

        return user, token

class CustomSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        # Skip CSRF validation for APIs
        return

class CustomUserRateThrottle(UserRateThrottle):
    rate = '100/hour'

class CustomAnonRateThrottle(AnonRateThrottle):
    rate = '20/hour'