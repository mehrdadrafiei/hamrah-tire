from rest_framework import serializers
from .models import Tire, Warranty, RepairRequest, TechnicalReport
from apps.accounts.serializers import UserBasicSerializer

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
    warranty_status = serializers.SerializerMethodField()
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Tire
        fields = ['id', 'serial_number', 'model', 'size', 'status', 'warranty_status', 'owner_username']

    def get_warranty_status(self, obj):
        warranty = obj.warranty if hasattr(obj, 'warranty') else None
        if not warranty:
            return "No Warranty"
        return "Active" if warranty.is_active else "Inactive"