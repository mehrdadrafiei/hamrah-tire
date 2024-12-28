from rest_framework import serializers
from .models import Tire, Warranty, RepairRequest, TechnicalReport

class TireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tire
        fields = '__all__'

class WarrantySerializer(serializers.ModelSerializer):
    class Meta:
        model = Warranty
        fields = '__all__'

class RepairRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairRequest
        fields = '__all__'

class TechnicalReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalReport
        fields = '__all__'