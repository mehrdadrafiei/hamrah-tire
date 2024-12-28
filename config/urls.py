from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.accounts.views import UserViewSet
from apps.tire.views import TireViewSet, RepairRequestViewSet, TechnicalReportViewSet
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Authentication'])
class CustomTokenObtainPairView(TokenObtainPairView):
    pass

@extend_schema(tags=['Authentication'])
class CustomTokenRefreshView(TokenRefreshView):
    pass

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tires', TireViewSet, basename='tire')
router.register(r'repair-requests', RepairRequestViewSet, basename='repair-request')
router.register(r'technical-reports', TechnicalReportViewSet, basename='technical-report')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    # JWT endpoints
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    # OpenAPI endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
