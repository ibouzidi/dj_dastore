from django.views import View
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import FolderCreateForm
from .models import Folder
from extbackup.models import File
from extbackup.forms import FileForm


class FolderCreateView(View):
    template_name = 'folder/folder_list.html'

    def get(self, request, *args, **kwargs):
        form = FolderCreateForm()
        context = {
            'form': form,
            'submit_url': reverse('folder:folder_create'),
            'add_folder': reverse('folder:folder_create'),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = FolderCreateForm(request.POST)
        if form.is_valid():
            new_folder = form.save(commit=False)
            new_folder.user = request.user
            parent_folder_id = form.cleaned_data.get('parent_folder_id')
            if parent_folder_id:
                new_folder.parent = Folder.objects.get(pk=parent_folder_id)
            new_folder.save()
            return redirect(reverse('folder:folder_list'))
        else:
            context = {
                'form': form,
                'submit_url': reverse('folder:folder_create'),
                'add_folder': reverse('folder:folder_create'),
            }
            return render(request, self.template_name, context)


class FolderListView(View):
    template_name = 'folder/folder_list.html'

    def get(self, request, *args, **kwargs):
        pk = request.GET.get('id')
        form_folder = FolderCreateForm()
        form_upload = FileForm()
        queryset = Folder.objects.filter(user=request.user)

        if pk:
            queryset = queryset.filter(parent__pk=pk)
        else:
            queryset = queryset.filter(parent=None)

        order_by = request.GET.get('sort')
        if order_by == 'time':
            queryset = queryset.order_by('-created_at')
        elif order_by == 'name':
            queryset = queryset.order_by('name')

        # file_query = File.objects.all()
        file_query = File.objects.filter(user=request.user) \
            .order_by('-uploaded_at') \
            .values_list('id', 'file', 'description', 'uploaded_at', 'size')
        if pk:
            file_query = file_query.filter(folder__pk=pk)
        else:
            file_query = file_query.filter(folder=None)

        if order_by == 'time':
            file_query = file_query.order_by('-created_at')
        elif order_by == 'name':
            file_query = file_query.order_by('name')

        parent_folder = []
        if pk:
            folder = Folder.objects.get(pk=pk)
            parent_folder.append({
                'text': folder.name,
                'link': reverse('folder:folder_list') + f'?id={folder.pk}',
            })
            while folder.parent:
                parent_folder.append({
                    'text': folder.parent.name,
                    'link': reverse('folder:folder_list') + f'?id={folder.parent.pk}',
                })
                folder = folder.parent
            parent_folder.reverse()

        context = {
            'form_upload': form_upload,
            'form_folder': form_folder,
            'folder_list': queryset,
            'file_list': file_query,
            'add_folder': reverse('folder:folder_create_with_parent', kwargs={
                'parent_folder_id': pk}) if pk else reverse(
                'folder:folder_create'),
            'parent_folder': parent_folder,
        }

        return render(request, self.template_name, context)
