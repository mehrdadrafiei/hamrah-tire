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
from .forms import TireForm

@login_required
def tire_list_view(request):
    """View for listing all tires."""
    # Get all tires based on user role
    if request.user.role == 'ADMIN':
        tires = Tire.objects.all()
        can_edit = True
    elif request.user.role == 'MINER':
        tires = Tire.objects.filter(owner=request.user)
        can_edit = True
    else:  # TECHNICAL
        tires = Tire.objects.all()
        can_edit = False

    # Apply filters
    brand = request.GET.get('brand')
    if brand:
        tires = tires.filter(brand__icontains=brand)

    model = request.GET.get('model')
    if model:
        tires = tires.filter(model__icontains=model)

    status = request.GET.get('status')
    if status:
        tires = tires.filter(status=status)

    category = request.GET.get('category')
    if category:
        tires = tires.filter(category_id=category)

    # Pagination
    paginator = Paginator(tires, 10)
    page = request.GET.get('page')
    tires = paginator.get_page(page)

    context = {
        'tires': tires,
        'status_choices': Tire.STATUS_CHOICES,
        'categories': TireCategory.objects.all(),
        'can_edit': can_edit,
        'user_role': request.user.role
    }
    return render(request, 'tire/tire_list.html', context)

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

@login_required
@role_required(['ADMIN'])
def tire_add_view(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'You do not have permission to add tires.')
        return redirect('tire_list')
    if request.method == 'POST':
        form = TireForm(request.POST)
        if form.is_valid():
            tire = form.save(commit=False)
            tire.created_by = request.user
            tire.save()
            messages.success(request, 'Tire added successfully.')
            return redirect('tire_list')
    else:
        form = TireForm(initial={'purchase_date': timezone.now().date()})  # Set default date
    
    return render(request, 'tire/tire_form.html', {
        'form': form,
        'title': 'Add New Tire',
        'submit_text': 'Add Tire'
    })

@login_required
@role_required(['ADMIN'])
def tire_edit_view(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'You do not have permission to edit tires.')
        return redirect('tire_list')
    tire = get_object_or_404(Tire, pk=pk)
    if request.method == 'POST':
        form = TireForm(request.POST, instance=tire)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tire "{tire.title}" has been updated successfully.')
            return redirect('tire_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TireForm(instance=tire)
    
    return render(request, 'tire/tire_form.html', {
        'form': form,
        'tire': tire,
        'title': f'Edit Tire - {tire.title}',
        'submit_text': 'Save Changes'
    })

@login_required
@role_required(['ADMIN'])
@ensure_csrf_cookie
def tire_delete_view(request, pk):
    if request.method == 'POST':
        try:
            tire = get_object_or_404(Tire, pk=pk)
            tire_title = tire.title
            tire.delete()
            messages.success(request, f'Tire "{tire_title}" has been deleted successfully.')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': 'Unable to delete tire. It may be referenced by other items.'
            }, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)

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
    context = {
        'trainings': trainings,
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
            training.uploaded_by = request.user
            training.save()
            messages.success(request, 'Training video added successfully.')
            return redirect('training_list')
    else:
        form = TrainingForm()

    return render(request, 'training/admin/training_form.html', {
        'form': form,
        'title': 'Add Training Video'
    })

@login_required
@role_required(['ADMIN'])
def training_edit_view(request, pk):
    training = get_object_or_404(Training, pk=pk)
    if request.method == 'POST':
        form = TrainingForm(request.POST, instance=training)
        if form.is_valid():
            form.save()
            messages.success(request, 'Training video updated successfully.')
            return redirect('training_list')
    else:
        form = TrainingForm(instance=training)

    return render(request, 'training/admin/training_form.html', {
        'form': form,
        'training': training,
        'title': 'Edit Training Video'
    })

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