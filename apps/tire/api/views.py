# apps/tire/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Count, Avg
from rest_framework.permissions import IsAuthenticated
from ..models import Tire, Warranty, RepairRequest, TechnicalReport
from .serializers import (
    TireDetailSerializer, 
    TireListSerializer,
    WarrantySerializer,
    RepairRequestSerializer, 
    TechnicalReportSerializer
)
from ..filters import TireFilter
from .permissions import TirePermission, RepairRequestPermission, TechnicalReportPermission
from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@extend_schema(tags=['Tires'])
class TireViewSet(viewsets.ModelViewSet):
    filterset_class = TireFilter
    search_fields = ['brand', 'serial_number', 'model', 'manufacturer']
    ordering_fields = ['purchase_date', 'working_hours', 'tread_depth']
    ordering = ['-purchase_date']
    permission_classes = [IsAuthenticated, TirePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return TireListSerializer
        return TireDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Tire.objects.select_related('owner', 'category')
        
        if user.role == 'ADMIN':
            queryset = queryset.all()
        elif user.role == 'MINER':
            queryset = queryset.filter(owner=user)
        elif user.role == 'TECHNICAL':
            queryset = queryset.all()
        else:
            queryset = Tire.objects.none()
            
        return queryset.order_by('-purchase_date')

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(f"Error in list view: {str(e)}")
            return Response(
                {"error": "An error occurred while fetching the data."},
                status=500
            )
        
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @extend_schema(
        summary="Activate tire warranty",
        description="Activate the warranty for a specific tire. Only available for tires with inactive warranties.",
        responses={
            200: None,
            400: None,
            404: None
        }
    )
    @action(detail=True, methods=['post'])
    def activate_warranty(self, request, pk=None):
        tire = self.get_object()
        warranty = getattr(tire, 'warranty', None)
        
        if not warranty:
            return Response(
                {'error': 'No warranty found for this tire'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if warranty.is_active:
            return Response(
                {'error': 'Warranty is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        warranty.is_active = True
        warranty.activated_by = request.user
        warranty.save()
        return Response({'status': 'warranty activated'})

    @extend_schema(
        summary="Get tire statistics",
        description="Get statistics about tires including counts, averages, and status distribution.",
        responses={200: None}
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        stats = {
            'total_tires': queryset.count(),
            'status_distribution': dict(
                queryset.values_list('status')
                .annotate(count=Count('id'))
            ),
            'avg_working_hours': queryset.aggregate(
                Avg('working_hours')
            )['working_hours__avg'],
            'avg_tread_depth': queryset.aggregate(
                Avg('tread_depth')
            )['tread_depth__avg']
        }
        return Response(stats)


@extend_schema(tags=['Repairs'])
class RepairRequestViewSet(viewsets.ModelViewSet):
    serializer_class = RepairRequestSerializer
    permission_classes = [IsAuthenticated, RepairRequestPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['tire__serial_number', 'description']
    ordering_fields = ['request_date', 'status']
    ordering = ['-request_date']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RepairRequest.objects.all()
        return RepairRequest.objects.filter(requested_by=user)

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)


@extend_schema(tags=['Technical'])
class TechnicalReportViewSet(viewsets.ModelViewSet):
    serializer_class = TechnicalReportSerializer
    permission_classes = [IsAuthenticated, TechnicalReportPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['tire__serial_number', 'notes']
    ordering_fields = ['inspection_date', 'condition_rating']
    ordering = ['-inspection_date']

    def get_queryset(self):
        user = self.request.user
        if user.role != 'TECHNICAL':
            return TechnicalReport.objects.none()
        return TechnicalReport.objects.all()

    def perform_create(self, serializer):
        serializer.save(expert=self.request.user)

    # Add the resolve action here
    @extend_schema(
        summary="Mark technical report as resolved",
        description="Mark a technical report as resolved.",
        responses={200: None}
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        report = self.get_object()
        report.resolved = True
        report.save()
        return Response({'status': 'report resolved'})