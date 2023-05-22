from bootstrap_modal_forms.mixins import CreateUpdateAjaxMixin
from django import forms
from .models import Folder
from bootstrap_modal_forms.forms import BSModalModelForm


class FolderCreateForm(BSModalModelForm):
    parent_folder_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Folder
        fields = ('name',)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.request.user
        parent_folder_id = self.cleaned_data.get('parent_folder_id')
        if parent_folder_id:
            instance.parent = Folder.objects.get(pk=parent_folder_id)
        if commit and (not self.request.is_ajax() or self.request.POST.get('asyncUpdate') == 'True'):
            instance.save()
        return instance


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