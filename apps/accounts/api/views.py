from rest_framework import status, viewsets, views, generics
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserBasicSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordChangeSerializer,
    UserProfileUpdateSerializer
)
from .permissions import IsAdminOrSelf

User = get_user_model()

@extend_schema(tags=['Authentication'])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            username = request.data.get('username')
            user = User.objects.get(username=username)
            
            # Check if account is locked
            if user.account_locked_until and user.account_locked_until > timezone.now():
                return Response(
                    {'error': 'Account is temporarily locked. Please try again later.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if email is verified
            if not user.email_verified:
                return Response(
                    {'error': 'Email not verified. Please verify your email before logging in.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Reset failed login attempts on successful login
            user.reset_failed_login_attempts()
            
            # Record IP address
            user.last_login_ip = request.META.get('REMOTE_ADDR')
            user.save()
        else:
            # Record failed login attempt
            try:
                user = User.objects.get(username=request.data.get('username'))
                user.record_failed_login()
            except User.DoesNotExist:
                pass
            
        return response

@extend_schema(tags=['Authentication'])
class CustomTokenRefreshView(TokenRefreshView):
    """
    Takes a refresh type JSON web token and returns an access type JSON web
    token if the refresh token is valid.
    """
    pass

@extend_schema(tags=['Users'])
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    Admins can manage all users, while regular users can only view and update their own profiles.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrSelf]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update'] and not self.request.user.is_staff:
            return UserProfileUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user account (admin only)."""
        if not request.user.role == 'ADMIN':
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'user activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user account (admin only)."""
        if not request.user.role == 'ADMIN':
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'user deactivated'})

@extend_schema(tags=['Authentication'])
class EmailVerificationView(views.APIView):
    """
    API endpoint for email verification.
    Users receive a verification token via email after registration.
    """
    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        
        try:
            user = User.objects.get(email_verification_token=token)
            if user.verify_email(token):
                return Response({'message': 'Email verified successfully'})
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def resend(self, request):
        """Resend email verification token."""
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email, email_verified=False)
            token = user.generate_verification_token()
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            
            send_mail(
                'Verify your email',
                f'Please click this link to verify your email: {verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return Response({'message': 'Verification email sent'})
        except User.DoesNotExist:
            return Response(
                {'error': 'No unverified user found with this email'},
                status=status.HTTP_400_BAD_REQUEST
            )

@extend_schema(tags=['Authentication'])
class PasswordResetRequestView(views.APIView):
    """
    API endpoint for requesting a password reset.
    Sends a password reset token to the user's email.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            token = user.generate_password_reset_token()
            
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            send_mail(
                'Password Reset Request',
                f'Click here to reset your password: {reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return Response({'message': 'Password reset email sent'})
        except User.DoesNotExist:
            # Don't reveal that email doesn't exist
            return Response({'message': 'Password reset email sent'})

@extend_schema(tags=['Authentication'])
class PasswordResetConfirmView(views.APIView):
    """
    API endpoint for confirming a password reset.
    Users must provide the token received via email and their new password.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(password_reset_token=token)
            
            if not user.password_reset_sent_at or \
               (timezone.now() - user.password_reset_sent_at).days >= 1:
                return Response(
                    {'error': 'Password reset token has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(new_password)
            user.password_reset_token = ''
            user.password_reset_sent_at = None
            user.save()
            
            return Response({'message': 'Password reset successful'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )

@extend_schema(tags=['Users'])
class PasswordChangeView(views.APIView):
    """
    API endpoint for authenticated users to change their password.
    Requires the current password for verification.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'})