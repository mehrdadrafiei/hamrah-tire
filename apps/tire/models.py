from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User

class Tire(models.Model):
    STATUS_CHOICES = (
        ('ORDERED', 'Ordered'),
        ('CURRENCY_ALLOCATION', 'Currency Allocation'),
        ('CUSTOMS_CLEARANCE', 'Customs Clearance'),
        ('WAREHOUSING', 'In Warehouse'),
        ('DELIVERED', 'Delivered to Customer'),
        ('IN_USE', 'In Use'),
        ('IN_REPAIR', 'In Repair'),
        ('DISPOSED', 'Disposed'),
    )
    
    serial_number = models.CharField(max_length=50, unique=True)
    model = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=100)
    purchase_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tires')
    working_hours = models.IntegerField(default=0)
    tread_depth = models.FloatField(validators=[MinValueValidator(0)])
    
    class Meta:
        db_table = 'tires'

class Warranty(models.Model):
    tire = models.OneToOneField(Tire, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    activation_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_warranties')
    
    class Meta:
        db_table = 'warranties'

class RepairRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    )
    
    tire = models.ForeignKey(Tire, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_repairs')
    completion_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'repair_requests'

class TechnicalReport(models.Model):
    tire = models.ForeignKey(Tire, on_delete=models.CASCADE)
    expert = models.ForeignKey(User, on_delete=models.CASCADE)
    inspection_date = models.DateTimeField()
    tread_depth = models.FloatField(validators=[MinValueValidator(0)])
    working_hours = models.IntegerField()
    condition_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    notes = models.TextField()
    requires_immediate_attention = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'technical_reports'

class Training(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField()
    upload_date = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'trainings'

class TrainingRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )
    
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_training_requests')
    completion_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'training_requests'

class TireSize(models.Model):
    width = models.IntegerField()
    aspect_ratio = models.IntegerField()
    diameter = models.IntegerField()
    standard_description = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'tire_sizes'
        unique_together = ('width', 'aspect_ratio', 'diameter')

class Alert(models.Model):
    ALERT_TYPES = (
        ('WORKING_HOURS', 'Working Hours Exceeded'),
        ('TREAD_DEPTH', 'Low Tread Depth'),
        ('WARRANTY_EXPIRY', 'Warranty Near Expiration'),
    )
    
    tire = models.ForeignKey(Tire, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    created_date = models.DateTimeField(auto_now_add=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'alerts'