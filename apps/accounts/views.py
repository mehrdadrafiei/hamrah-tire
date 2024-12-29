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
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from .forms import PasswordResetRequestForm, PasswordResetConfirmForm
from django.contrib.auth import login, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import ensure_csrf_cookie

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
def dashboard_view(request):
    """Main dashboard view that redirects to role-specific dashboards."""
    user = request.user
    
    if user.role == 'ADMIN':
        return admin_dashboard(request)
    elif user.role == 'MINER':
        return miner_dashboard(request)
    elif user.role == 'TECHNICAL':
        return technical_dashboard(request)
    
    messages.error(request, 'Invalid user role.')
    return redirect('logout')

@login_required
@role_required(['ADMIN'])
def admin_dashboard(request):
    """Admin-specific dashboard view."""
    context = {
        'total_users': User.objects.count(),
        'active_tires': Tire.objects.filter(status='IN_USE').count(),
        'pending_repairs': RepairRequest.objects.filter(status='PENDING').count(),
        'monthly_reports': TechnicalReport.objects.filter(
            inspection_date__month=timezone.now().month
        ).count(),
        'recent_activities': get_recent_activities(),
        'system_alerts': get_system_alerts(),
        'user_distribution': User.objects.values('role').annotate(count=Count('id')),
        'tire_status_distribution': Tire.objects.values('status').annotate(count=Count('id'))
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@role_required(['MINER'])
def miner_dashboard(request):
    """Miner-specific dashboard view."""
    user_tires = Tire.objects.filter(owner=request.user)
    
    context = {
        'user': request.user,
        'active_tires': user_tires.filter(status='IN_USE').count(),
        'pending_repairs': RepairRequest.objects.filter(
            tire__in=user_tires, 
            status='PENDING'
        ).count(),
        'active_warranties': user_tires.filter(
            warranty__is_active=True
        ).count(),
        'inspection_status': get_inspection_status(user_tires),
        'tires': user_tires.select_related('warranty'),
        'repair_requests': RepairRequest.objects.filter(
            tire__in=user_tires
        ).order_by('-request_date')[:10]
    }
    return render(request, 'dashboard/miner_dashboard.html', context)

@role_required(['TECHNICAL'])
def technical_dashboard(request):
    """Technical-specific dashboard view."""
    context = {
        'user': request.user,
        'critical_issues': TechnicalReport.objects.filter(
            requires_immediate_attention=True,
            resolved=False
        ).count(),
        'pending_repairs': RepairRequest.objects.filter(status='PENDING').count(),
        'todays_inspections': TechnicalReport.objects.filter(
            inspection_date__date=timezone.now().date()
        ).count(),
        'total_inspections': TechnicalReport.objects.count(),
        'critical_issues_list': get_critical_issues(),
        'recent_inspections': TechnicalReport.objects.order_by('-inspection_date')[:10],
        'available_tires': Tire.objects.filter(status='IN_USE')
    }
    return render(request, 'dashboard/technical_dashboard.html', context)

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
    """Change password view."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changed successfully.')
            return redirect('dashboard')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})

@user_passes_test(lambda u: u.role == 'ADMIN')
def user_list_view(request):
    """View for listing all users (admin only)."""
    users = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 10)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
def tire_list_view(request):
    """View for listing tires based on user role."""
    user = request.user
    if user.role == 'ADMIN':
        tires = Tire.objects.all()
    elif user.role == 'MINER':
        tires = Tire.objects.filter(owner=user)
    else:  # TECHNICAL
        tires = Tire.objects.filter(status='IN_USE')
    
    paginator = Paginator(tires, 10)
    page = request.GET.get('page')
    tires = paginator.get_page(page)
    return render(request, 'tire/tire_list.html', {'tires': tires})

@login_required
def tire_detail_view(request, pk):
    """Detailed view of a tire."""
    tire = get_object_or_404(Tire, pk=pk)
    if request.user.role == 'MINER' and tire.owner != request.user:
        messages.error(request, 'You do not have permission to view this tire.')
        return redirect('tire_list')
        
    context = {
        'tire': tire,
        'repair_requests': tire.repairrequest_set.all().order_by('-request_date'),
        'technical_reports': tire.technicalreport_set.all().order_by('-inspection_date'),
        'warranty': getattr(tire, 'warranty', None)
    }
    return render(request, 'tire/tire_detail.html', context)

# Helper functions
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