from django import forms
from .models import File, SupportedExtension


class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ('file', 'description',)
        widgets = {
            'file': forms.FileInput(attrs={'class': 'custom-file-input',
                                           'id': 'customFile',
                                           'onchange': 'previewFiles()',
                                           'multiple': True}),
            'description': forms.TextInput(attrs={'cols': '30',
                                    'rows': '3',
                                    'placeholder': 'Description',
                                    'class': 'form-control '
                                             'form-form shadow-none'}),
        }


class ExtensionForm(forms.ModelForm):
    class Meta:
        model = SupportedExtension
        fields = ('extension',)
        widgets = {
            'extension': forms.TextInput(attrs={
                                    'placeholder': 'Name of extension',
                                    'class': 'form-control '
                                             'form-form shadow-none'}),
        }