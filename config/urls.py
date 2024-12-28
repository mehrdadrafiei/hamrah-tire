from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from apps.accounts.views import (
    UserViewSet,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    EmailVerificationView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView
)
from apps.tire.views import (
    TireViewSet,
    RepairRequestViewSet,
    TechnicalReportViewSet
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

# API Routers
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tires', TireViewSet, basename='tire')
router.register(r'repair-requests', RepairRequestViewSet, basename='repair-request')
router.register(r'technical-reports', TechnicalReportViewSet, basename='technical-report')

# Authentication URLs
auth_patterns = [
    # JWT Token endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # Email verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    path('verify-email/resend/', EmailVerificationView.as_view(), name='resend_verification'),
    
    # Password management
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
]

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/auth/', include(auth_patterns)),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)