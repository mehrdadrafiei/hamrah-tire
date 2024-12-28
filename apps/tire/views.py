from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Tire, Warranty, RepairRequest, TechnicalReport
from .serializers import (
    TireSerializer, WarrantySerializer,
    RepairRequestSerializer, TechnicalReportSerializer
)

class TireViewSet(viewsets.ModelViewSet):
    serializer_class = TireSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Tire.objects.all()
        elif user.role == 'MINER':
            return Tire.objects.filter(owner=user)
        elif user.role == 'TECHNICAL':
            return Tire.objects.all()
        return Tire.objects.none()

    @action(detail=True, methods=['post'])
    def activate_warranty(self, request, pk=None):
        tire = self.get_object()
        warranty = tire.warranty
        
        if warranty and not warranty.is_active:
            warranty.is_active = True
            warranty.activation_date = timezone.now()
            warranty.save()
            return Response({'status': 'warranty activated'})
        return Response(
            {'error': 'warranty already active or not found'},
            status=status.HTTP_400_BAD_REQUEST
        )

class RepairRequestViewSet(viewsets.ModelViewSet):
    serializer_class = RepairRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RepairRequest.objects.all()
        return RepairRequest.objects.filter(requested_by=user)

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

class TechnicalReportViewSet(viewsets.ModelViewSet):
    queryset = TechnicalReport.objects.all()
    serializer_class = TechnicalReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != 'TECHNICAL':
            return TechnicalReport.objects.none()
        return TechnicalReport.objects.all()