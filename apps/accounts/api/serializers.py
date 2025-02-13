from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import send_mail

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'first_name', 'last_name', 'role']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'phone',
            'is_active', 'email_verified', 'last_login'
        )
        read_only_fields = ['id', 'email_verified']


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'email', 'first_name', 'last_name', 'role',
            'company_name', 'job_title', 'department', 'employee_id',
            'address', 'city', 'province', 'postal_code',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')

        if phone and password:
            try:
                user = User.objects.get(phone=phone)
                if not user.check_password(password):
                    raise serializers.ValidationError('Invalid phone number or password.')
                if not user.is_active:
                    raise serializers.ValidationError('This account is inactive.')
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid phone number or password.')
        else:
            raise serializers.ValidationError('Must include "phone" and "password".')

        attrs['user'] = user
        return attrs

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role', 'phone')

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value


    def create(self, validated_data):
        # Create user
        user = User.objects.create_user(**validated_data)

        # Generate verification token
        token = user.generate_verification_token()

        # Send verification email
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        try:
            send_mail(
                subject='Verify your email',
                message=f'Please click this link to verify your email: {verification_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            print(f"Verification token for {user.username}: {token}")  # Debug line
        except Exception as e:
            print(f"Failed to send email: {str(e)}")  # Debug line

        return user

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for users to update their own profiles.
    Restricts which fields can be updated by non-admin users.
    """
    class Meta:
        model = User
        fields = ('email', 'phone')
        
    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        if data['current_password'] == data['new_password']:
            raise serializers.ValidationError({
                'new_password': "New password must be different from current password."
            })
        return data