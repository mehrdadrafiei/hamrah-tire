from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
from apps.accounts.decorators import role_required
from apps.tire.models import Tire, RepairRequest, TechnicalReport
from .models import User
from .forms import (
    UserLoginForm,
    UserProfileForm,
    CustomPasswordChangeForm,
    RepairRequestForm,
    TechnicalReportForm
)
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from .forms import PasswordResetRequestForm, PasswordResetConfirmForm
from django.contrib.auth import login
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import ensure_csrf_cookie

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

@ensure_csrf_cookie
def login_view(request):
    """Handle user login with template."""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            response = redirect_to_dashboard(user)
            
            # Set both cookies and localStorage
            response.set_cookie(
                'access_token',
                str(refresh.access_token),
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            response.set_cookie(
                'refresh_token',
                str(refresh),
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            
            # Add JavaScript to set localStorage items
            response.write('<script>')
            response.write(f'localStorage.setItem("access_token", "{str(refresh.access_token)}");')
            response.write(f'localStorage.setItem("user_role", "{user.role}");')
            response.write('</script>')
            
            if not form.cleaned_data.get('remember_me', False):
                request.session.set_expiry(0)
            
            return response
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def redirect_to_dashboard(user):
    if user.role == 'ADMIN':
        return redirect('admin_dashboard')
    elif user.role == 'MINER':
        return redirect('miner_dashboard')
    elif user.role == 'TECHNICAL':
        return redirect('technical_dashboard')
    return redirect('dashboard')

@login_required
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

@login_required
def profile_view(request):
    """User profile view and update."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Error updating profile.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def change_password_view(request):
    """Change password view for logged-in users."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


def get_recent_activities():
    """Get combined recent activities from different models."""
    activities = []
    
    # Add repair requests
    repair_requests = RepairRequest.objects.select_related(
        'tire', 'requested_by'
    ).order_by('-request_date')[:5]
    
    for request in repair_requests:
        activities.append({
            'timestamp': request.request_date,
            'user': request.requested_by.username,
            'action': 'Repair Request',
            'details': f'Tire: {request.tire.serial_number}'
        })
    
    # Add technical reports
    reports = TechnicalReport.objects.select_related(
        'tire', 'expert'
    ).order_by('-inspection_date')[:5]
    
    for report in reports:
        activities.append({
            'timestamp': report.inspection_date,
            'user': report.expert.username,
            'action': 'Technical Inspection',
            'details': f'Tire: {report.tire.serial_number}'
        })
    
    return sorted(activities, key=lambda x: x['timestamp'], reverse=True)

def get_system_alerts():
    """Get system alerts for admin dashboard."""
    alerts = []
    
    # Check for low tread depth
    critical_tires = Tire.objects.filter(tread_depth__lt=2.0)
    if critical_tires.exists():
        alerts.append({
            'level': 'danger',
            'message': f'{critical_tires.count()} tires have critically low tread depth'
        })
    
    # Check for overdue inspections
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    overdue_tires = Tire.objects.filter(
        Q(technicalreport__isnull=True) | 
        Q(technicalreport__inspection_date__lt=thirty_days_ago)
    ).distinct()
    if overdue_tires.exists():
        alerts.append({
            'level': 'warning',
            'message': f'{overdue_tires.count()} tires are due for inspection'
        })
    
    return alerts

def get_inspection_status(tires):
    """Calculate inspection status percentage for given tires."""
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_inspections = tires.filter(
        technicalreport__inspection_date__gte=thirty_days_ago
    ).distinct().count()
    total = tires.count()
    
    if total == 0:
        return "No tires assigned"
    
    percentage = (recent_inspections / total) * 100
    return f"{percentage:.1f}% up to date"

def get_critical_issues():
    """Get list of critical technical issues."""
    return TechnicalReport.objects.filter(
        requires_immediate_attention=True,
        resolved=False
    ).select_related('tire').order_by('-inspection_date')


def password_reset_view(request):
    """Request password reset view."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            try:
                form.save()  # This will trigger the email sending
                return redirect('password_reset_done')
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'accounts/password_reset_form.html', {'form': form})

def password_reset_done_view(request):
    """Display message after password reset request."""
    return render(request, 'accounts/password_reset_done.html')

def password_reset_confirm_view(request, token):
    """Confirm password reset view."""
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            try:
                form.save(token)
                return redirect('password_reset_complete')
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = PasswordResetConfirmForm()
    
    return render(request, 'accounts/password_reset_confirm.html', {
        'form': form,
        'token': token
    })

def password_reset_complete_view(request):
    """Display message after successful password reset."""
    return render(request, 'accounts/password_reset_complete.html')


@login_required
def notifications_view(request):
    if request.method == 'POST':
        # Handle notification preferences update
        return JsonResponse({'status': 'success'})
    return JsonResponse({'notifications': []})

@login_required
def messages_view(request):
    if request.method == 'POST':
        # Handle new message
        return JsonResponse({'status': 'success'})
    return JsonResponse({'messages': []})

def send_verification_email(user):
    """Helper function to send verification email."""
    token = user.generate_verification_token()
    # Change this line to match your URL pattern
    verification_url = f"{settings.FRONTEND_URL}/accounts/verify-email/{token}/"
    
    # Rest of the function remains the same
    context = {
        'username': user.username,
        'verification_url': verification_url
    }
    html_message = render_to_string('accounts/email/verify_email.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject='Verify Your Email - Hamrah Tire',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send verification email: {str(e)}")
        return False

def verify_email_view(request, token):
    """Handle email verification."""
    try:
        user = User.objects.get(email_verification_token=token)
        if user.verify_email(token):
            messages.success(request, 'Your email has been successfully verified. You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'The verification link has expired. Please request a new one.')
            return redirect('login')
    except User.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('login')
    
@role_required(['ADMIN'])
def user_list_view(request):
    """View for listing and managing users."""
    users = User.objects.all().order_by('-date_joined')
    # paginator = Paginator(users, 10)
    # page = request.GET.get('page')
    # users = paginator.get_page(page)
    return render(request, 'accounts/user_list.html', {'users': users})

@role_required(['ADMIN'])
def user_add_view(request):
    """View for adding new users."""
    if request.method == 'POST':
        try:
            # Create user
            user = User.objects.create_user(
                username=request.POST['username'],
                email=request.POST['email'],
                password=request.POST['password'],
                role=request.POST['role']
            )
            
            # Send verification email
            if send_verification_email(user):
                return JsonResponse({
                    'status': 'success',
                    'message': 'User created successfully. Verification email sent.'
                })
            else:
                return JsonResponse({
                    'status': 'warning',
                    'message': 'User created but failed to send verification email.'
                })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request'
    }, status=405)

@role_required(['ADMIN'])
def user_edit_view(request, user_id):
    """View for editing users."""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            old_email = user.email
            
            user.username = request.POST['username']
            user.email = request.POST['email']
            user.role = request.POST['role']
            
            # Only update password if provided
            new_password = request.POST.get('password')
            if new_password:
                user.set_password(new_password)
            
            # Check if email changed
            email_changed = old_email != user.email
            if email_changed:
                user.email_verified = False
            
            user.save()
            
            # Send new verification email if email changed
            if email_changed:
                if send_verification_email(user):
                    return JsonResponse({
                        'status': 'success',
                        'message': 'User updated and verification email sent.'
                    })
                else:
                    return JsonResponse({
                        'status': 'warning',
                        'message': 'User updated but failed to send verification email.'
                    })
            
            return JsonResponse({
                'status': 'success',
                'message': 'User updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
            
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request'
    }, status=405)

@role_required(['ADMIN'])
def user_activate_view(request, user_id):
    """View for activating users."""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            user.is_active = True
            user.save()
            return JsonResponse({
                'status': 'success',
                'message': 'User activated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request'
    }, status=405)

@role_required(['ADMIN'])
def user_deactivate_view(request, user_id):
    """View for deactivating users."""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            # Prevent deactivating the last admin
            if user.role == 'ADMIN' and User.objects.filter(role='ADMIN', is_active=True).count() <= 1:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot deactivate the last admin user'
                }, status=400)
            
            user.is_active = False
            user.save()
            return JsonResponse({
                'status': 'success',
                'message': 'User deactivated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request'
    }, status=405)

@role_required(['ADMIN'])
def resend_verification_email_view(request, user_id):
    """View for resending verification emails."""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            if user.email_verified:
                return JsonResponse({
                    'status': 'error',
                    'message': 'User email is already verified'
                }, status=400)
            
            if send_verification_email(user):
                return JsonResponse({
                    'status': 'success',
                    'message': 'Verification email sent successfully'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to send verification email'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request'
    }, status=405)