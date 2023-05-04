from django import forms
from .models import File, SupportedExtension, Folder


class FileForm(forms.ModelForm):
    folder = forms.ModelChoiceField(queryset=Folder.objects.all(),
                                    required=False)
    class Meta:
        model = File
        fields = ('file', 'description', 'folder')
        widgets = {
            'file': forms.FileInput(attrs={'class': 'dragAndUploadManual',
                                           'id': 'myDragElement',
                                           'multiple': True}),
            'description': forms.TextInput(attrs={'cols': '30',
                                    'rows': '3',
                                    'placeholder': 'Describe your bakcup files.',
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