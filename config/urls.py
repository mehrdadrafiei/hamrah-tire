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
from apps.tire.api.views import (
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
from apps.dashboard import views as dashboard_views

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
    path('', dashboard_views.dashboard_view, name='dashboard'),
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
    path('accounts/password-reset/confirm/<str:token>/', account_views.password_reset_confirm_view, name='password_reset_confirm'),
    path('accounts/password-reset/complete/', account_views.password_reset_complete_view, name='password_reset_complete'),

    # Tire Management
    # path('tires/', tire_views.tire_list_view, name='tire_list'),
    # path('tires/add/', tire_views.tire_add_view, name='tire_add'),
    #path('tires/<int:pk>/edit/', tire_views.tire_edit_view, name='tire_edit'),
    # path('tires/<int:pk>/delete/', tire_views.tire_delete_view, name='tire_delete'),
    path('tires/<int:pk>/edit/', tire_views.tire_edit, name='tire_edit'),

    # Tire Model URLs (Catalog)
    path('models/', tire_views.tire_model_list, name='model_list'),
    path('models/create/', tire_views.tire_model_create, name='model_create'),
    path('models/<int:pk>/edit/', tire_views.tire_model_edit, name='model_edit'),
    
    # Tire Order URLs
    path('orders/', tire_views.order_list, name='order_list'),
    path('orders/create/', tire_views.order_create, name='order_create'),
    path('orders/<int:pk>/', tire_views.order_detail, name='order_detail'),
    path('orders/<int:pk>/serial-numbers/', tire_views.order_serial_numbers, name='order_serial_numbers'),
    path('orders/<int:pk>/mark-ready/', tire_views.order_mark_ready, name='order_mark_ready'),
    
    # Individual Tire URLs
    path('tires/', tire_views.tire_list, name='tire_list'),
    path('tires/dashboard/', tire_views.tire_dashboard, name='tire_dashboard'),
    path('tires/<int:pk>/', tire_views.tire_detail, name='tire_detail'),
    path('tires/status-update/', tire_views.tire_status_update, name='tire_status_update'),
    path('tires/export/', tire_views.export_tire_data, name='export_tire_data'),

    # Tire Category URLs
    path('tires/categories/', tire_views.tire_categories_view, name='tire_categories'),
    path('tires/categories/<int:pk>/delete/', tire_views.category_delete_view, name='delete_category'),
    path('reports/', tire_views.report_list_view, name='report_list'),

    
    #path('repairs/', account_views.repair_list, name='repair_list'),

    # Role-specific Dashboards
    path('dashboard/admin/', dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/miner/', dashboard_views.miner_dashboard, name='miner_dashboard'),
    path('dashboard/technical/', dashboard_views.technical_dashboard, name='technical_dashboard'),
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),

    path('accounts/users/', account_views.user_list_view, name='user_list'),
    path('accounts/users/add/', account_views.user_add_view, name='user_add'),
    path('accounts/users/<int:user_id>/edit/', account_views.user_edit_view, name='user_edit'),
    path('accounts/users/<int:user_id>/activate/', account_views.user_activate_view, name='user_activate'),
    path('accounts/users/<int:user_id>/deactivate/', account_views.user_deactivate_view, name='user_deactivate'),
    #path('accounts/users/<int:user_id>/resend-verification/', account_views.resend_verification_email_view, name='resend_verification'),
    path('accounts/verify-email/<str:token>/', account_views.verify_email_view, name='verify_email'),

    # Training URLs
    path('training/', tire_views.training_list_view, name='training_list'),
    path('training/add/', tire_views.training_add_view, name='training_add'),
    path('training/<int:pk>/edit/', tire_views.training_edit_view, name='training_edit'),
    path('training/<int:pk>/delete/', tire_views.training_delete_view, name='training_delete'),

    # Training Category URLs
    path('training/categories/', tire_views.training_category_list_view, name='training_category_list'),
    path('training/categories/<int:pk>/edit/', tire_views.training_category_edit_view, name='training_category_edit'),
    path('training/categories/<int:pk>/delete/', tire_views.training_category_delete_view, name='training_category_delete'),

    # Training Request URLs
    path('training/requests/', tire_views.training_request_list_view, name='training_request_list'),
    path('training/requests/<int:pk>/update/', tire_views.training_request_update_view, name='training_request_update'),

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)