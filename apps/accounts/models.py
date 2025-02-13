from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrator'),
        ('MINER', 'Miner'),
        ('TECHNICAL', 'Technical'),
    )
    
    # Basic Information
    role = models.CharField(max_length=20, choices=ROLES)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    national_id = models.CharField(max_length=10, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Contact Information
    alternative_phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    
    # Work Information
    company_name = models.CharField(max_length=200, null=True, blank=True)
    job_title = models.CharField(max_length=200, null=True, blank=True)
    department = models.CharField(max_length=200, null=True, blank=True)
    
    # Social Media
    instagram = models.URLField(max_length=200, null=True, blank=True)
    twitter = models.URLField(max_length=200, null=True, blank=True)
    telegram = models.URLField(max_length=200, null=True, blank=True)
    youtube = models.URLField(max_length=200, null=True, blank=True)
    bale = models.URLField(max_length=200, null=True, blank=True)
    eitaa = models.URLField(max_length=200, null=True, blank=True)

    # Password reset fields
    password_reset_token = models.CharField(max_length=100, blank=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Session management and security
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
        
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_address(self):
        address_parts = [
            self.address,
            self.city,
            self.province,
            self.postal_code
        ]
        return ", ".join(part for part in address_parts if part)
    
    def generate_password_reset_token(self):
        self.password_reset_token = get_random_string(64)
        self.password_reset_sent_at = timezone.now()
        self.save()
        return self.password_reset_token

    # def verify_email(self, token):
    #     if (self.email_verification_token == token and 
    #         self.email_verification_sent_at and 
    #         (timezone.now() - self.email_verification_sent_at).days < 7):
    #         self.email_verified = True
    #         self.email_verification_token = ''
    #         self.save()
    #         return True
    #     return False

    def record_failed_login(self):
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)
        
        self.save()

    def reset_failed_login_attempts(self):
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save()