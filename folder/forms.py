from django import forms
from .models import Folder


class FolderCreateForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ('name', 'parent')
        widgets = {
            'name': forms.TextInput(attrs={
                                    'placeholder': 'Name of folder',
                                    'class': 'form-control '
                                             'form-form shadow-none'}),
            'parent': forms.Select(attrs={
                                    'class': 'form-control '
                                             'form-form shadow-none'}),
        }