from django import forms
from .models import File, SupportedExtension, Folder


class FileForm(forms.ModelForm):
    parent_folder_id = forms.IntegerField(required=False,
                                          widget=forms.HiddenInput())

    class Meta:
        model = File
        fields = ('file', 'description')
        widgets = {
            'file': forms.FileInput(attrs={'class': 'dragAndUploadManual',
                                           'id': 'myDragElement',
                                           'multiple': True}),
            'description': forms.TextInput(attrs={'cols': '30',
                                    'rows': '3',
                                    'placeholder': 'Describe Your Backup',
                                    'class': 'form-control '
                                             'form-form shadow-none',
                                                  'id': 'file-description'}),

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