from apps.tire.models import Tire
from django import forms


class TireForm(forms.ModelForm):
    class Meta:
        model = Tire
        fields = ['title', 'serial_number', 'brand', 'model', 'compound', 
                 'pattern', 'size', 'category', 'working_hours', 'status', 
                 'owner', 'purchase_date', 'tread_depth']  # Added tread_depth
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'compound': forms.TextInput(attrs={'class': 'form-control'}),
            'pattern': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'working_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'owner': forms.Select(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tread_depth': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',  # Allows decimal values
                'min': '0'     # Minimum value as per your model validator
            }),
        }