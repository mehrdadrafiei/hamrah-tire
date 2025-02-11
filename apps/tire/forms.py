from apps.tire.models import Training, TrainingCategory, TrainingRequest
from django import forms
from apps.tire.models  import TireModel, TireOrder, TireOrderItem, Tire

# forms.py
from django import forms
from django.core.validators import MinValueValidator
from .models import TireModel, TireOrder, TireOrderItem, Tire

class TireModelForm(forms.ModelForm):
    """Form for managing tire models in the catalog"""
    class Meta:
        model = TireModel
        fields = ['name', 'brand', 'pattern', 'size', 'description', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'pattern': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TireOrderForm(forms.ModelForm):
    """Form for creating a new tire order"""
    class Meta:
        model = TireOrder
        fields = ['owner', 'status', 'notes']
        widgets = {
            'owner': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit initial status choices for new orders
        if not self.instance.pk:
            self.fields['status'].choices = [
                ('PRE_ORDER', 'Pre-Order'),
                ('SUPPLIER_ORDER', 'Ordered from Supplier')
            ]

class TireOrderItemForm(forms.ModelForm):
    """Form for adding items to an order"""
    class Meta:
        model = TireOrderItem
        fields = ['tire_model', 'quantity']
        widgets = {
            'tire_model': forms.Select(attrs={
                'class': 'form-control',
                'data-live-search': 'true'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active tire models
        self.fields['tire_model'].queryset = TireModel.objects.filter(is_active=True)

class TireOrderItemFormSet(forms.BaseModelFormSet):
    """Formset for handling multiple order items at once"""
    def clean(self):
        if any(self.errors):
            return

        tire_models = []
        total_quantity = 0

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue

            tire_model = form.cleaned_data.get('tire_model')
            quantity = form.cleaned_data.get('quantity', 0)

            if tire_model:
                if tire_model in tire_models:
                    raise forms.ValidationError(
                        "Each tire model can only be added once to an order."
                    )
                tire_models.append(tire_model)
                total_quantity += quantity

        if total_quantity < 1:
            raise forms.ValidationError("Order must contain at least one tire.")

class TireForm(forms.ModelForm):
    """Form for managing individual tires"""
    class Meta:
        model = Tire
        fields = ['serial_number', 'tire_model', 'owner', 'status', 'tread_depth']
        widgets = {
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'tire_model': forms.Select(attrs={'class': 'form-control'}),
            'owner': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tread_depth': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1'
            }),
        }

    def clean_serial_number(self):
        serial_number = self.cleaned_data['serial_number']
        if Tire.objects.exclude(pk=self.instance.pk).filter(serial_number=serial_number).exists():
            raise forms.ValidationError("This serial number is already in use.")
        return serial_number
    
class SerialNumberEntryForm(forms.Form):
    """Dynamic form for entering serial numbers for each tire model in an order"""
    def __init__(self, order_item, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_item = order_item
        remaining_count = order_item.quantity - order_item.tire_set.count()
        
        for i in range(remaining_count):
            field_name = f'serial_number_{i}'
            self.fields[field_name] = forms.CharField(
                label=f'{order_item.tire_model} - Tire {i + 1}',
                max_length=100,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': f'Enter serial number for tire {i + 1}',
                    'data-tire-index': i,
                    'data-model-id': order_item.tire_model.id
                })
            )

    def clean(self):
        cleaned_data = super().clean()
        serial_numbers = [value for key, value in cleaned_data.items() 
                         if key.startswith('serial_number_')]
        
        # Check for duplicates within the form
        if len(serial_numbers) != len(set(serial_numbers)):
            raise forms.ValidationError("Duplicate serial numbers found")
        
        # Check if serial numbers already exist in database
        existing = Tire.objects.filter(serial_number__in=serial_numbers)
        if existing.exists():
            existing_serials = ', '.join(existing.values_list('serial_number', flat=True))
            raise forms.ValidationError(f"Serial numbers already exist: {existing_serials}")
        
        return cleaned_data



class TireStatusUpdateForm(forms.Form):
    """Form for updating status of multiple tires"""
    status = forms.ChoiceField(
        choices=Tire.TIRE_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tire_ids = forms.MultipleChoiceField(
        widget=forms.MultipleHiddenInput
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set choices for tire_ids based on available tires
        self.fields['tire_ids'].choices = [
            (tire.id, str(tire)) 
            for tire in Tire.objects.all()
        ]

class TrainingCategoryForm(forms.ModelForm):
    class Meta:
        model = TrainingCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TrainingForm(forms.ModelForm):
    STATUS_CHOICES = [
        (True, 'Active'),
        (False, 'Inactive')
    ]

    is_active = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Status",
        initial=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_video_url(self):
        url = self.cleaned_data.get('video_url')
        if not url.startswith('https://www.aparat.com/'):
            raise forms.ValidationError("Only Aparat.com URLs are allowed.")
        return url

    class Meta:
        model = Training
        fields = ['title', 'description', 'category', 'video_url', 'thumbnail_url', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.aparat.com/v/...'
            }),
            'thumbnail_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

class TrainingRequestForm(forms.ModelForm):
    class Meta:
        model = TrainingRequest
        fields = ['category', 'title', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }