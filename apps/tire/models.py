from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from django.core.validators import URLValidator

class TireCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tire_categories'
        verbose_name_plural = 'Tire Categories'

    def __str__(self):
        return self.name

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
    title = models.CharField(max_length=100, blank=True)
    pattern = models.CharField(max_length=100, blank=True)
    compound = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=50, unique=True)
    model = models.CharField(max_length=100)
    brand = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=100)
    purchase_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tires')
    working_hours = models.IntegerField(default=0)
    tread_depth = models.FloatField(validators=[MinValueValidator(0)])
    category = models.ForeignKey(TireCategory, on_delete=models.SET_NULL, null=True, blank=True)

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
    resolved = models.BooleanField(default=False)  # Add this field

    class Meta:
        db_table = 'technical_reports'

class TrainingCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'training_categories'
        verbose_name_plural = 'Training Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Training(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TrainingCategory, on_delete=models.CASCADE, related_name='trainings')
    video_url = models.URLField(validators=[URLValidator()])
    thumbnail_url = models.URLField(validators=[URLValidator()], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'trainings'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

class TrainingRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_requests')
    category = models.ForeignKey(TrainingCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_training_requests'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'training_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

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


