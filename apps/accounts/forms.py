from django.utils import timezone
from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate
from .models import User
from apps.tire.models import Tire, RepairRequest, TechnicalReport
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail

class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Username'}
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password'}
    ))
    remember_me = forms.BooleanField(required=False)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError('Invalid username or password.')
            if not user.is_active:
                raise forms.ValidationError('This account is inactive.')
            if not user.email_verified:
                raise forms.ValidationError('Please verify your email address.')
            
        return self.cleaned_data

    def get_user(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        return authenticate(username=username, password=password)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 
                 'instagram', 'twitter', 'telegram', 'youtube', 'bale', 'eitaa']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Instagram profile URL'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'X/Twitter profile URL'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Telegram profile URL'}),
            'youtube': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'YouTube channel URL'}),
            'bale': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Bale profile URL'}),
            'eitaa': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Eitaa profile URL'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class RepairRequestForm(forms.ModelForm):
    class Meta:
        model = RepairRequest
        fields = ['tire', 'description']
        widgets = {
            'tire': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TechnicalReportForm(forms.ModelForm):
    class Meta:
        model = TechnicalReport
        fields = ['tire', 'tread_depth', 'working_hours', 'condition_rating', 
                 'notes', 'requires_immediate_attention']
        widgets = {
            'tire': forms.Select(attrs={'class': 'form-control'}),
            'tread_depth': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'working_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'condition_rating': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requires_immediate_attention': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )

    def save(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            token = user.generate_password_reset_token()
            
            # Send reset email
            reset_url = f"{settings.FRONTEND_URL}/accounts/password-reset/confirm/{token}/"
            send_mail(
                'Password Reset Request',
                f'Click here to reset your password: {reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            # Don't reveal whether a user exists
            pass

class PasswordResetConfirmForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
        help_text="At least 8 characters with numbers and letters"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Passwords don't match")
        
        try:
            validate_password(new_password)
        except forms.ValidationError as e:
            self.add_error('new_password', e)

        return cleaned_data

    def save(self, token):
        try:
            user = User.objects.get(password_reset_token=token)
            if not user.password_reset_sent_at or \
               (timezone.now() - user.password_reset_sent_at).days >= 1:
                raise forms.ValidationError('Password reset token has expired')
            
            user.set_password(self.cleaned_data['new_password'])
            user.password_reset_token = ''
            user.password_reset_sent_at = None
            user.save()
            
        except User.DoesNotExist:
            raise forms.ValidationError('Invalid reset token')
        