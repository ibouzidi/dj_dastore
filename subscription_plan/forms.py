from django import forms
from .models import SubscriptionPlan


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = ('name', 'storage_limit', 'price', 'description')
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Name of the plan',
                'class': 'form-control '
                         'form-form shadow-none'}),
            'storage_limit': forms.NumberInput(attrs={
                'placeholder': 'Storage limit (in GB)',
                'class': 'form-control form-form shadow-none'}),
            'price': forms.NumberInput(attrs={
                'placeholder': 'Price per month',
                'class': 'form-control form-form shadow-none'}),
            'description': forms.TextInput(attrs={
                'placeholder': 'Description, seperate with comma',
                'class': 'form-control form-form shadow-none'}),
        }

    # def clean(self):
    #     cleaned_data = super().clean()
    #     storage_limit = cleaned_data.get('storage_limit')
    #     # Convert the storage limit to bytes
    #     storage_limit = storage_limit * 1024 ** 3
    #     cleaned_data['storage_limit'] = storage_limit
    #     return cleaned_data
