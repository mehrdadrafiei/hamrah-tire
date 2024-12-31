from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from django.utils import timezone

class User(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrator'),
        ('MINER', 'Miner'),           # For users/mine panel
        ('TECHNICAL', 'Technical'),    # For technical panel
    )
    
    role = models.CharField(max_length=20, choices=ROLES)
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Password reset fields
    password_reset_token = models.CharField(max_length=100, blank=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Session management and security
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    instagram = models.URLField(max_length=200, blank=True)
    twitter = models.URLField(max_length=200, blank=True) 
    telegram = models.URLField(max_length=200, blank=True)
    youtube = models.URLField(max_length=200, blank=True)
    bale = models.URLField(max_length=200, blank=True)
    eitaa = models.URLField(max_length=200, blank=True)

    class Meta:
        db_table = 'users'
    
    def generate_verification_token(self):
        self.email_verification_token = get_random_string(64)
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token

    def generate_password_reset_token(self):
        self.password_reset_token = get_random_string(64)
        self.password_reset_sent_at = timezone.now()
        self.save()
        return self.password_reset_token

    def verify_email(self, token):
        if (self.email_verification_token == token and 
            self.email_verification_sent_at and 
            (timezone.now() - self.email_verification_sent_at).days < 7):
            self.email_verified = True
            self.email_verification_token = ''
            self.save()
            return True
        return False

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