from apps.tire.models import Tire
from apps.tire.models import Training, TrainingCategory, TrainingRequest
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


class TrainingCategoryForm(forms.ModelForm):
    class Meta:
        model = TrainingCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TrainingForm(forms.ModelForm):
    def clean_video_url(self):
        url = self.cleaned_data.get('video_url')
        if not url.startswith('https://www.aparat.com/'):
            raise forms.ValidationError("Only Aparat.com URLs are allowed.")
        return url

    class Meta:
        model = Training
        fields = ['title', 'description', 'category', 'video_url', 'thumbnail_url']
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