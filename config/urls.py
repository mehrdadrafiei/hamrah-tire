from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from apps.accounts.api.views import (
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
from apps.accounts import views as account_views
from apps.tire import views as tire_views

# API Routers
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tires', TireViewSet, basename='tire')
router.register(r'repair-requests', RepairRequestViewSet, basename='repair-request')
router.register(r'technical-reports', TechnicalReportViewSet, basename='technical-report')

# Authentication URLs (API)
auth_patterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    path('verify-email/resend/', EmailVerificationView.as_view(), name='resend_verification'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
]

# API URL patterns with namespace
api_patterns = [
    path('', include(router.urls)),
    path('auth/', include((auth_patterns, 'auth'), namespace='auth')),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Frontend URL patterns
urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints (with namespace)
    path('api/', include((api_patterns, 'api'), namespace='api')),
    
    # Frontend/Authentication routes
    path('', account_views.dashboard_view, name='dashboard'),
    path('accounts/login/', account_views.login_view, name='login'),
    path('accounts/logout/', account_views.logout_view, name='logout'),
    path('accounts/profile/', account_views.profile_view, name='profile'),
    path('accounts/password/change/', account_views.change_password_view, name='change_password'),
    path('accounts/users/', account_views.user_list_view, name='user_list'),
    path('accounts/profile/', account_views.profile_view, name='profile'),
    path('accounts/notifications/', account_views.notifications_view, name='notifications'),
    path('accounts/messages/', account_views.messages_view, name='messages'),
    
    # Password Reset Routes
    path('accounts/password-reset/', account_views.password_reset_view, name='password_reset'),
    path('accounts/password-reset/sent/', account_views.password_reset_done_view, name='password_reset_done'),
    path('accounts/password-reset/<str:token>/', account_views.password_reset_confirm_view, name='password_reset_confirm'),
    path('accounts/password-reset/complete/', account_views.password_reset_complete_view, name='password_reset_complete'),
    
    # Tire Management
    path('tires/', account_views.tire_list_view, name='tire_list'),
    path('tires/<int:pk>/', account_views.tire_detail_view, name='tire_detail'),

    #path('repairs/', account_views.repair_list, name='repair_list'),

    # Role-specific Dashboards
    path('dashboard/admin/', account_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/miner/', account_views.miner_dashboard, name='miner_dashboard'),
    path('dashboard/technical/', account_views.technical_dashboard, name='technical_dashboard'),
    path('dashboard/', account_views.dashboard_view, name='dashboard')
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)