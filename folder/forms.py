from django import forms
from .models import Folder


class FolderCreateForm(forms.ModelForm):
    parent_folder_id = forms.IntegerField(required=False,
                                          widget=forms.HiddenInput())

    class Meta:
        model = Folder
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={
                                    'placeholder': 'New Folder Name',
                                    'id': 'folderName',
                                    'class': 'form-control '
                                             'form-form shadow-none'}),
        }


class FolderEditForm(forms.ModelForm):
    folder_id = forms.IntegerField(required=False,
                                          widget=forms.HiddenInput())

    class Meta:
        model = Folder
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={
                                    'id': 'folderName',
                                    'class': 'form-control '
                                             'form-form shadow-none'}),
        }