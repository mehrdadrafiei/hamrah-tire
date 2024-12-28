# config/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.accounts.views import UserViewSet
from apps.tire.views import TireViewSet, RepairRequestViewSet, TechnicalReportViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tires', TireViewSet, basename='tire')
router.register(r'repair-requests', RepairRequestViewSet, basename='repair-request')
router.register(r'technical-reports', TechnicalReportViewSet, basename='technical-report')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]