from django_filters import rest_framework as filters
from .models import TireModel
from .models import RepairRequest, TechnicalReport


class TireModelFilter(filters.FilterSet):
    brand = filters.CharFilter(lookup_expr='icontains')
    category = filters.NumberFilter(field_name='category__id')
    # min_working_hours = filters.NumberFilter(field_name="working_hours", lookup_expr='gte')
    # max_working_hours = filters.NumberFilter(field_name="working_hours", lookup_expr='lte')
    # min_tread_depth = filters.NumberFilter(field_name="tread_depth", lookup_expr='gte')
    # max_tread_depth = filters.NumberFilter(field_name="tread_depth", lookup_expr='lte')
    # purchase_date_after = filters.DateFilter(field_name="purchase_date", lookup_expr='gte')
    # purchase_date_before = filters.DateFilter(field_name="purchase_date", lookup_expr='lte')

    class Meta:
        model = TireModel
        fields = {
            'model': ['exact', 'icontains'],
            'size': ['exact', 'icontains'],
            # 'manufacturer': ['exact', 'icontains'],
            # 'status': ['exact', 'in'],
            # 'owner': ['exact'],
            'brand': ['exact', 'icontains'],
            'category': ['exact'],
        }


class RepairRequestFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="request_date", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="request_date", lookup_expr='lte')
    
    class Meta:
        model = RepairRequest
        fields = {
            'tire__serial_number': ['exact', 'icontains'],
            'status': ['exact', 'in'],
            'requested_by': ['exact'],
            'approved_by': ['exact'],
        }

class TechnicalReportFilter(filters.FilterSet):
    min_tread_depth = filters.NumberFilter(field_name="tread_depth", lookup_expr='gte')
    max_tread_depth = filters.NumberFilter(field_name="tread_depth", lookup_expr='lte')
    inspection_date_after = filters.DateFilter(field_name="inspection_date", lookup_expr='gte')
    inspection_date_before = filters.DateFilter(field_name="inspection_date", lookup_expr='lte')
    
    class Meta:
        model = TechnicalReport
        fields = {
            'tire__serial_number': ['exact', 'icontains'],
            'expert': ['exact'],
            'requires_immediate_attention': ['exact'],
            'condition_rating': ['exact', 'gte', 'lte'],
        }