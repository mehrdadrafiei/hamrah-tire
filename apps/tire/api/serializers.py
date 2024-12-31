from rest_framework import serializers
from ..models import Tire, Warranty, RepairRequest, TechnicalReport
from apps.accounts.api.serializers import UserBasicSerializer

class WarrantySerializer(serializers.ModelSerializer):
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = Warranty
        fields = '__all__'

class RepairRequestSerializer(serializers.ModelSerializer):
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = RepairRequest
        fields = '__all__'

class TechnicalReportSerializer(serializers.ModelSerializer):
    expert_username = serializers.CharField(source='expert.username', read_only=True)
    
    class Meta:
        model = TechnicalReport
        fields = '__all__'

class TireDetailSerializer(serializers.ModelSerializer):
    warranty = WarrantySerializer(read_only=True)
    repair_requests = RepairRequestSerializer(many=True, read_only=True, source='repairrequest_set')
    technical_reports = TechnicalReportSerializer(many=True, read_only=True, source='technicalreport_set')
    owner = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Tire
        fields = '__all__'

class TireListSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    category = serializers.SerializerMethodField()
    
    class Meta:
        model = Tire
        fields = [
            'id', 'title', 'serial_number', 'brand', 'model', 
            'compound', 'pattern', 'size', 'category', 
            'working_hours', 'status', 'owner_username'
        ]

    def get_category(self, obj):
        if obj.category:
            return {'id': obj.category.id, 'name': obj.category.name}
        return None