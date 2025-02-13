from django.utils import timezone
from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from .models import User
from apps.tire.models import Tire, RepairRequest, TechnicalReport
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

User = get_user_model()

class UserLoginForm(forms.Form):
    phone = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Phone Number'}
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password'}
    ))
    remember_me = forms.BooleanField(required=False)

    def clean(self):
        phone = self.cleaned_data.get('phone')
        password = self.cleaned_data.get('password')
        
        if phone and password:
            try:
                user = User.objects.get(phone=phone)
                if not user.check_password(password):
                    raise forms.ValidationError('Invalid phone number or password.')
                if not user.is_active:
                    raise forms.ValidationError('This account is inactive.')
            except User.DoesNotExist:
                raise forms.ValidationError('Invalid phone number or password.')
            
        return self.cleaned_data

class UserAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Leave empty if not changing.'
    )

    class Meta:
        model = User
        fields = [
            'phone', 'email', 'password', 'role', 'is_active',
            'first_name', 'last_name', 'national_id', 'birth_date',
            'alternative_phone', 'address', 'city', 'province', 'postal_code',
            'company_name', 'job_title', 'department', 'employee_id', 'hire_date',
            'instagram', 'twitter', 'telegram', 'youtube', 'bale', 'eitaa'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'alternative_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube': forms.URLInput(attrs={'class': 'form-control'}),
            'bale': forms.URLInput(attrs={'class': 'form-control'}),
            'eitaa': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.exclude(pk=self.instance.pk).filter(phone=phone).exists():
            raise forms.ValidationError('This phone number is already in use.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'alternative_phone',
            'address', 'city', 'province', 'postal_code',
            'instagram', 'twitter', 'telegram', 'youtube', 'bale', 'eitaa'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'alternative_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube': forms.URLInput(attrs={'class': 'form-control'}),
            'bale': forms.URLInput(attrs={'class': 'form-control'}),
            'eitaa': forms.URLInput(attrs={'class': 'form-control'})
        }

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
        