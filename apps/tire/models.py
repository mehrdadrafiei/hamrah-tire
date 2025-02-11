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
    
class TireModel(models.Model):
    """Available tire models that can be ordered"""
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    pattern = models.CharField(max_length=100)
    compound = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey('TireCategory', on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    initial_tread_depth = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(0)],
        default=0  # You might want to set a more appropriate default value
    )
    class Meta:
        unique_together = ['brand', 'pattern', 'size']

    def __str__(self):
        return f"{self.brand} {self.pattern} {self.size}"

class TireOrder(models.Model):
    """Represents a bulk order of tires"""
    ORDER_STATUS_CHOICES = [
        ('PRE_ORDER', 'Pre-Order'),
        ('SUPPLIER_ORDER', 'Ordered from Supplier'),
        ('OCEAN_SHIPPING', 'Ocean Shipping'),
        ('IN_CUSTOMS', 'In Customs'),
        ('CUSTOMS_CLEARED', 'Customs Cleared'),
        ('SUPPLIER_WAREHOUSE', 'In Supplier Warehouse'),
        ('AWAITING_SERIAL_NUMBERS', 'Awaiting Serial Numbers'),
        ('READY_FOR_DELIVERY', 'Ready for Delivery'),
        ('SHIPPING_TO_CUSTOMER', 'Shipping to Customer'),
        ('DELIVERED', 'Delivered to Customer'),
    ]

    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=ORDER_STATUS_CHOICES, default='PRE_ORDER')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_orders')
    
    def __str__(self):
        return f"Order {self.id} - {self.owner.username} ({self.status})"

class TireOrderItem(models.Model):
    """Individual items within a tire order"""
    order = models.ForeignKey(TireOrder, on_delete=models.CASCADE, related_name='items')
    tire_model = models.ForeignKey(TireModel, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    cleared_quantity = models.PositiveIntegerField(default=0)  # For partial customs clearance
    
    def __str__(self):
        return f"{self.quantity}x {self.tire_model} ({self.order.status})"

class Tire(models.Model):
    """Represents actual physical tires owned by users"""
    TIRE_STATUS_CHOICES = [
        ('IN_WAREHOUSE', 'In Warehouse'),
        ('IN_USE', 'In Use'),
        ('DISPOSED', 'Disposed'),
    ]

    serial_number = models.CharField(max_length=100, unique=True)
    tire_model = models.ForeignKey(TireModel, on_delete=models.PROTECT)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    order_item = models.ForeignKey(TireOrderItem, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=TIRE_STATUS_CHOICES, default='IN_WAREHOUSE')
    purchase_date = models.DateField(auto_now_add=True)
    working_hours = models.PositiveIntegerField(default=0)
    tread_depth = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"{self.serial_number} - {self.tire_model}"

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


