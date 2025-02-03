from django.utils import timezone
from django.shortcuts import render
from django.shortcuts import render, redirect

from apps.accounts.decorators import role_required
from apps.accounts.models import User
from apps.accounts.views import get_critical_issues, get_inspection_status, get_recent_activities, get_system_alerts
from apps.tire.models import RepairRequest, TechnicalReport, Tire
from django.db.models import Count, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required


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

@login_required
@role_required(['TECHNICAL'])
def technical_dashboard(request):
    """Technical-specific dashboard view."""
    today = timezone.now().date()
    context = {
        'user': request.user,
        'critical_issues': TechnicalReport.objects.filter(
            requires_immediate_attention=True,
            resolved=False
        ).count(),
        'pending_repairs': RepairRequest.objects.filter(status='PENDING').count(),
        'todays_inspections': TechnicalReport.objects.filter(
            inspection_date__date=today
        ).count(),
        'total_inspections': TechnicalReport.objects.count(),
        'critical_issues_list': TechnicalReport.objects.filter(
            requires_immediate_attention=True,
            resolved=False
        ).select_related('tire').order_by('-inspection_date')[:5],
        'recent_inspections': TechnicalReport.objects.select_related('tire').order_by('-inspection_date')[:10],
        'available_tires': Tire.objects.filter(status='IN_USE')
    }
    return render(request, 'dashboard/technical_dashboard.html', context)
