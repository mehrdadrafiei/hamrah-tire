from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrator'),
        ('MINER', 'Miner'),           # For users/mine panel
        ('TECHNICAL', 'Technical'),    # For technical panel
    )
    
    role = models.CharField(max_length=20, choices=ROLES)
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'users'