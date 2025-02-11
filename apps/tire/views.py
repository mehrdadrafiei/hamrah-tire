from django.utils import timezone

from django.http import JsonResponse
from apps.tire.models import TechnicalReport, Tire
from django.contrib.auth.decorators import login_required
from apps.tire.models import Tire,TireCategory
from django.core.paginator import Paginator
from apps.accounts.decorators import role_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Training, TrainingCategory, TrainingRequest
from .forms import TrainingForm, TrainingCategoryForm
from .forms import (
    TireModelForm,
    TireOrderForm,
    TireOrderItemForm,
    TireOrderItemFormSet,
    SerialNumberEntryForm,
    TireForm,
    TireStatusUpdateForm
)
from .models import TireModel, TireOrder, TireOrderItem, Tire, RepairRequest
from django.forms import modelformset_factory
from django.db import transaction
from django.db.models import Count, F


# Tire Model Views (Catalog)
@login_required
@role_required(['ADMIN'])
def tire_model_list(request):
    """View for listing all available tire models"""
    tire_models = TireModel.objects.select_related('category').all()
    return render(request, 'tire/model_list.html', {
        'tire_models': tire_models
    })

@login_required
@role_required(['ADMIN'])
def tire_model_create(request):
    """View for creating a new tire model"""
    if request.method == 'POST':
        form = TireModelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tire model created successfully.')
            return redirect('model_list')
    else:
        form = TireModelForm()
    
    return render(request, 'tire/model_form.html', {
        'form': form,
        'title': 'Create Tire Model'
    })

@login_required
@role_required(['ADMIN'])
def tire_model_edit(request, pk):
    """View for editing an existing tire model"""
    tire_model = get_object_or_404(TireModel, pk=pk)
    if request.method == 'POST':
        form = TireModelForm(request.POST, instance=tire_model)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tire model updated successfully.')
            return redirect('model_list')
    else:
        form = TireModelForm(instance=tire_model)
    
    return render(request, 'tire/model_form.html', {
        'form': form,
        'title': 'Edit Tire Model'
    })

# Tire Order Views
@login_required
@role_required(['ADMIN'])
def order_list(request):
    """View for listing all tire orders"""
    orders = TireOrder.objects.select_related(
        'owner', 'created_by'
    ).prefetch_related(
        'items__tire_model'
    ).order_by('-order_date')
    
    return render(request, 'tire/order_list.html', {
        'orders': orders
    })

@login_required
@role_required(['ADMIN'])
def order_create(request):
    """View for creating a new tire order with multiple items"""
    OrderItemFormSet = modelformset_factory(
        TireOrderItem,
        form=TireOrderItemForm,
        formset=TireOrderItemFormSet,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        order_form = TireOrderForm(request.POST)
        formset = OrderItemFormSet(request.POST, queryset=TireOrderItem.objects.none())
        
        if order_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    order = order_form.save(commit=False)
                    order.created_by = request.user
                    order.save()
                    
                    for form in formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                            item = form.save(commit=False)
                            item.order = order
                            item.save()
                    
                messages.success(request, 'Tire order created successfully.')
                return redirect('order_list')
            except Exception as e:
                messages.error(request, f'Error creating order: {str(e)}')
    else:
        order_form = TireOrderForm()
        formset = OrderItemFormSet(queryset=TireOrderItem.objects.none())
    
    return render(request, 'tire/order_form.html', {
        'order_form': order_form,
        'formset': formset,
        'title': 'Create Tire Order'
    })

@login_required
@role_required(['ADMIN'])
def order_detail(request, pk):
    """View for viewing order details and updating status"""
    order = get_object_or_404(TireOrder, pk=pk)
    items = order.items.select_related('tire_model').prefetch_related('tire_set').all()
    
    # Check if all items need serial numbers
    needs_serials = False
    if order.status == 'SUPPLIER_WAREHOUSE':
        needs_serials = items.annotate(
            tire_count=Count('tire')
        ).filter(tire_count__lt=F('quantity')).exists()
        if needs_serials:
            messages.warning(
                request, 
                'Serial numbers need to be added before this order can be delivered.'
            )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(TireOrder.ORDER_STATUS_CHOICES):
            # Special handling for status transitions
            if new_status == 'SUPPLIER_WAREHOUSE':
                order.status = 'AWAITING_SERIAL_NUMBERS'
                messages.info(request, 'Please add serial numbers for the tires.')
            else:
                order.status = new_status
            
            order.save()
            messages.success(request, 'Order status updated successfully.')
            
            # Redirect to serial number entry if needed
            if order.status == 'AWAITING_SERIAL_NUMBERS':
                return redirect('order_serial_numbers', pk=order.pk)
    
    return render(request, 'tire/order_detail.html', {
        'order': order,
        'items': items,
        'needs_serials': needs_serials
    })

@login_required
@role_required(['ADMIN'])
def order_serial_numbers(request, pk):
    """View for managing serial numbers for an order"""
    order = get_object_or_404(TireOrder, pk=pk)
    
    # Ensure order is in correct status
    if order.status not in ['AWAITING_SERIAL_NUMBERS', 'READY_FOR_DELIVERY']:
        messages.error(request, 'Serial numbers can only be added when tires are in warehouse.')
        return redirect('order_detail', pk=order.pk)
    
    # Get all order items that still need serial numbers
    incomplete_items = []
    complete_items = []
    
    for item in order.items.all():
        existing_count = item.tire_set.count()
        if existing_count < item.quantity:
            incomplete_items.append({
                'item': item,
                'form': SerialNumberEntryForm(item) if request.method == 'GET' else 
                       SerialNumberEntryForm(item, request.POST),
                'existing_count': existing_count,
                'remaining_count': item.quantity - existing_count
            })
        else:
            complete_items.append({
                'item': item,
                'tires': item.tire_set.all()
            })
    
    if request.method == 'POST':
        form_valid = True
        to_create = []
        
        try:
            with transaction.atomic():
                for item_data in incomplete_items:
                    form = item_data['form']
                    if form.is_valid():
                        order_item = form.order_item
                        
                        # Create Tire objects for each serial number
                        for field_name, serial_number in form.cleaned_data.items():
                            if field_name.startswith('serial_number_'):
                                to_create.append(Tire(
                                    serial_number=serial_number,
                                    tire_model=order_item.tire_model,
                                    owner=order.owner,
                                    order_item=order_item,
                                    status='IN_WAREHOUSE',
                                    tread_depth=order_item.tire_model.initial_tread_depth
                                ))
                    else:
                        form_valid = False
                
                if form_valid:
                    # Bulk create all tires
                    Tire.objects.bulk_create(to_create)
                    
                    # Check if all items now have their serial numbers
                    all_complete = not order.items.annotate(
                        tire_count=Count('tire')
                    ).filter(tire_count__lt=F('quantity')).exists()
                    
                    if all_complete:
                        order.status = 'READY_FOR_DELIVERY'
                        order.save()
                        messages.success(request, 'All serial numbers added. Order is ready for delivery.')
                        return redirect('order_detail', pk=order.pk)
                    else:
                        messages.success(request, f'{len(to_create)} serial numbers added successfully.')
                        return redirect('order_serial_numbers', pk=order.pk)
                
        except Exception as e:
            messages.error(request, f'Error saving serial numbers: {str(e)}')
    
    return render(request, 'tire/order_serial_numbers.html', {
        'order': order,
        'incomplete_items': incomplete_items,
        'complete_items': complete_items
    })

@login_required
@role_required(['ADMIN'])
def order_mark_ready(request, pk):
    """Mark an order as ready for delivery after all serial numbers are added"""
    order = get_object_or_404(TireOrder, pk=pk)
    
    # Check if all items have their serial numbers
    incomplete_items = order.items.annotate(
        tire_count=Count('tire')
    ).filter(tire_count__lt=F('quantity'))
    
    if incomplete_items.exists():
        messages.error(request, 'Cannot mark as ready: Some tires are missing serial numbers.')
        return redirect('order_serial_numbers', pk=order.pk)
    
    order.status = 'READY_FOR_DELIVERY'
    order.save()
    messages.success(request, 'Order marked as ready for delivery.')
    return redirect('order_detail', pk=order.pk)

# Individual Tire Management Views
@login_required
def tire_list(request):
    """View for listing all tires"""
    # Filter based on user role
    if request.user.role == 'ADMIN':
        tires = Tire.objects.all()
    else:
        tires = Tire.objects.filter(owner=request.user)
        
    tires = tires.select_related(
        'tire_model',
        'owner',
        'order_item__order'
    ).order_by('-purchase_date')
    
    return render(request, 'tire/tire_list.html', {
        'tires': tires
    })

@login_required
def tire_detail(request, pk):
    """View for viewing detailed tire information"""
    tire = get_object_or_404(Tire, pk=pk)
    
    # Check permissions
    if request.user.role != 'ADMIN' and tire.owner != request.user:
        messages.error(request, "You don't have permission to view this tire.")
        return redirect('tire_list')
    
    # Get tire history
    inspections = tire.technicalreport_set.all().order_by('-inspection_date')
    repairs = tire.repairrequest_set.all().order_by('-request_date')
    
    return render(request, 'tire/tire_detail.html', {
        'tire': tire,
        'inspections': inspections,
        'repairs': repairs
    })

@login_required
@role_required(['ADMIN'])
def tire_status_update(request):
    """View for updating status of multiple tires"""
    if request.method == 'POST':
        form = TireStatusUpdateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    status = form.cleaned_data['status']
                    tire_ids = form.cleaned_data['tire_ids']
                    
                    updated = Tire.objects.filter(id__in=tire_ids).update(status=status)
                    messages.success(request, f'Successfully updated {updated} tires.')
                    
                    # Record status change in history if needed
                    # This could be implemented with a separate TireStatusHistory model
                    
                return JsonResponse({'success': True, 'updated_count': updated})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        return JsonResponse({'error': 'Invalid form data'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def tire_dashboard(request):
    """Dashboard view showing tire statistics and status"""
    user = request.user
    
    # Base queryset
    if user.role == 'ADMIN':
        tires = Tire.objects.all()
    else:
        tires = Tire.objects.filter(owner=user)
    
    # Calculate statistics
    stats = {
        'total_tires': tires.count(),
        'in_warehouse': tires.filter(status='IN_WAREHOUSE').count(),
        'in_use': tires.filter(status='IN_USE').count(),
        'disposed': tires.filter(status='DISPOSED').count(),
        'pending_inspections': tires.filter(
            status='IN_USE'
        ).exclude(
            technicalreport__inspection_date__gte=timezone.now() - timezone.timedelta(days=30)
        ).count()
    }
    
    # Get recent activities
    recent_inspections = TechnicalReport.objects.filter(
        tire__in=tires
    ).select_related('tire', 'expert').order_by('-inspection_date')[:5]
    
    recent_repairs = RepairRequest.objects.filter(
        tire__in=tires
    ).select_related('tire', 'requested_by').order_by('-request_date')[:5]
    
    return render(request, 'tire/tire_dashboard.html', {
        'stats': stats,
        'recent_inspections': recent_inspections,
        'recent_repairs': recent_repairs
    })

@login_required
@role_required(['ADMIN'])
def export_tire_data(request):
    """View for exporting tire data to Excel"""
    from openpyxl import Workbook
    from django.http import HttpResponse
    from datetime import datetime
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Tire Data"
    
    # Headers
    headers = [
        'Serial Number', 'Model', 'Brand', 'Size', 'Owner',
        'Status', 'Purchase Date', 'Working Hours', 'Tread Depth',
        'Order Reference'
    ]
    ws.append(headers)
    
    # Data
    tires = Tire.objects.select_related(
        'tire_model',
        'owner',
        'order_item__order'
    ).all()
    
    for tire in tires:
        ws.append([
            tire.serial_number,
            tire.tire_model.name,
            tire.tire_model.brand,
            tire.tire_model.size,
            tire.owner.username,
            tire.get_status_display(),
            tire.purchase_date,
            tire.working_hours,
            float(tire.tread_depth),
            f'Order #{tire.order_item.order.id}' if tire.order_item else 'N/A'
        ])
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=tires_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    wb.save(response)
    return response


@login_required
@role_required(['ADMIN'])
def tire_categories_view(request):
    """View for listing tire categories (all users can view, only admin can modify)."""
    if request.method == 'POST' and request.user.role == 'ADMIN':
        category_id = request.POST.get('category_id')
        if category_id:  # Edit existing category
            category = get_object_or_404(TireCategory, id=category_id)
            category.name = request.POST.get('name')
            category.description = request.POST.get('description')
            category.save()
            messages.success(request, 'Category updated successfully.')
        else:  # Add new category
            TireCategory.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description')
            )
            messages.success(request, 'Category added successfully.')
        return redirect('tire_categories')

    categories = TireCategory.objects.all().order_by('name')
    return render(request, 'tire/categories.html', {
        'categories': categories,
        'can_edit': request.user.role == 'ADMIN'
    })

# Tire Category Views
@login_required
@role_required(['ADMIN'])
def category_delete_view(request, pk):
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    if request.method == 'POST':
        category = get_object_or_404(TireCategory, pk=pk)
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)

@login_required
@role_required(['TECHNICAL', 'ADMIN'])
def report_list_view(request):
    """View for listing all technical reports."""
    reports = TechnicalReport.objects.select_related('tire', 'expert').order_by('-inspection_date')

    context = {
        'reports': reports,
        'tires': Tire.objects.all(),
        'title': 'Technical Reports'
    }
    return render(request, 'tire/report_list.html', context)

# ------------------------------
# ---- Training Admin Views ----
# ------------------------------

@login_required
@role_required(['ADMIN'])
def training_list_view(request):
    trainings = Training.objects.select_related('category', 'uploaded_by').all()
    form = TrainingForm()  # Add this line to provide form for modal

    context = {
        'trainings': trainings,
        'form': form,
        'categories': TrainingCategory.objects.all()
    }
    return render(request, 'training/admin/training_list.html', context)

@login_required
@role_required(['ADMIN'])
def training_add_view(request):
    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            training = form.save(commit=False)
            training.is_active = form.cleaned_data['is_active'] == 'True'
            training.uploaded_by = request.user
            training.uploaded_by = request.user
            training.save()
            messages.success(request, 'Training video added successfully.')
            return redirect('training_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TrainingForm()

    context = {
        'form': form,
        'title': 'Add Training Video'
    }
    return render(request, 'training/admin/training_form.html', context)

@login_required
@role_required(['ADMIN'])
def training_edit_view(request, pk):
    training = get_object_or_404(Training, pk=pk)

    if request.method == 'POST':
        form = TrainingForm(request.POST, instance=training)
        if form.is_valid():
            training = form.save(commit=False)
            training.is_active = form.cleaned_data['is_active'] == 'True'
            training.save()
            messages.success(request, 'Training video updated successfully.')
            return redirect('training_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TrainingForm(instance=training)

    context = {
        'form': form,
        'training': training,
        'title': 'Edit Training Video'
    }
    return render(request, 'training/admin/training_form.html', context)

@login_required
@role_required(['ADMIN'])
def training_delete_view(request, pk):
    training = get_object_or_404(Training, pk=pk)
    if request.method == 'POST':
        training.delete()
        messages.success(request, 'Training video deleted successfully.')
        return redirect('training_list')
    return redirect('training_list')

@login_required
@role_required(['ADMIN'])
def training_category_list_view(request):
    if request.method == 'POST':
        form = TrainingCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('training_category_list')
    else:
        form = TrainingCategoryForm()

    categories = TrainingCategory.objects.all()
    return render(request, 'training/admin/category_list.html', {
        'categories': categories,
        'form': form
    })

@login_required
@role_required(['ADMIN'])
def training_category_edit_view(request, pk):
    category = get_object_or_404(TrainingCategory, pk=pk)
    if request.method == 'POST':
        form = TrainingCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('training_category_list')
    else:
        form = TrainingCategoryForm(instance=category)

    return render(request, 'training/admin/category_form.html', {
        'form': form,
        'category': category
    })

@login_required
@role_required(['ADMIN'])
def training_category_delete_view(request, pk):
    category = get_object_or_404(TrainingCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('training_category_list')
    return redirect('training_category_list')

@login_required
@role_required(['ADMIN'])
def training_request_list_view(request):
    requests = TrainingRequest.objects.select_related('user', 'category').all()
    return render(request, 'training/admin/request_list.html', {
        'requests': requests
    })

@login_required
@role_required(['ADMIN'])
def training_request_update_view(request, pk):
    training_request = get_object_or_404(TrainingRequest, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')

        if status in dict(TrainingRequest.STATUS_CHOICES):
            training_request.status = status
            training_request.notes = notes
            if status in ['APPROVED', 'REJECTED']:
                training_request.approved_by = request.user
                training_request.approved_at = timezone.now()
            training_request.save()

            messages.success(request, f'Request status updated to {status}')
        else:
            messages.error(request, 'Invalid status')

    return redirect('training_request_list')