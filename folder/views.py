from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponseBadRequest, \
    HttpResponseRedirect, HttpResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy

from dj_dastore.decorator import user_is_subscriber
from .forms import FolderCreateForm, FolderEditForm
from .models import Folder
from extbackup.models import File
from extbackup.forms import FileForm


@method_decorator(user_passes_test(user_is_subscriber), name='dispatch')
class FolderCreateView(BSModalCreateView):
    template_name = 'folder/folder_create.html'
    form_class = FolderCreateForm
    success_message = 'Success: Folder was created.'

    def get_initial(self):
        initial = super().get_initial()
        parent_folder_id = self.request.GET.get('id')
        if parent_folder_id:
            initial['parent_folder_id'] = parent_folder_id
        return initial

    def get_success_url(self):
        parent_folder_id = self.request.GET.get('id')
        if parent_folder_id:
            return reverse('folder:folder_list') + '?id=' + parent_folder_id
        else:
            return reverse('folder:folder_list')


@method_decorator(user_passes_test(user_is_subscriber), name='dispatch')
class FolderUpdateView(BSModalUpdateView):
    model = Folder
    template_name = 'folder/folder_update.html'
    form_class = FolderEditForm
    success_message = 'Success: Folder was renamed.'

    def form_valid(self, form):
        folder = form.save(commit=False)
        if folder.user != self.request.user:
            messages.error(self.request, "Permission denied")
            return redirect('folder:folder_list')
        return super().form_valid(form)

    def get_success_url(self):
        parent_folder_id = self.request.GET.get('id')
        if parent_folder_id:
            return reverse('folder:folder_list') + '?id=' + parent_folder_id
        else:
            return reverse('folder:folder_list')

    # def get_success_url(self):
    #     print("YES")
    #     folder = self.get_object()
    #     print("folder")
    #     print(folder.parent.pk)
    #     if folder.parent is not None:
    #         return reverse('folder:folder_list') + '?id=' + str(folder.parent.pk)
    #     else:
    #         return reverse('folder:folder_list')

# class FolderCreateView(View):
#     template_name = 'folder/folder_create.html'
#
#     def get(self, request, *args, **kwargs):
#         parent_folder_id = request.GET.get('parent_folder_id', None)
#         print('Parent Folder ID:', parent_folder_id)
#         form = FolderCreateForm(initial={'parent_folder_id': parent_folder_id})
#         context = {
#             'form': form,
#             'submit_url': reverse('folder:folder_create'),
#             'add_folder': reverse('folder:folder_create'),
#         }
#         return render(request, self.template_name, context)
#
#     def post(self, request, *args, **kwargs):
#         form = FolderCreateForm(request.POST)
#         if form.is_valid():
#             new_folder = form.save(commit=False)
#             new_folder.user = request.user
#             parent_folder_id = form.cleaned_data.get('parent_folder_id')
#             if parent_folder_id:
#                 new_folder.parent = Folder.objects.get(pk=parent_folder_id)
#             new_folder.save()
#             messages.success(request, "Folder created successfully")
#             return redirect("folder:folder_list")
#         else:
#             context = {
#                 'form': form,
#                 'submit_url': reverse('folder:folder_create'),
#                 'add_folder': reverse('folder:folder_create'),
#             }
#             return render(request, self.template_name, context)


@method_decorator(user_passes_test(user_is_subscriber), name='dispatch')
class FolderListView(View):
    template_name = 'folder/folder_list.html'

    def get(self, request, *args, **kwargs):
        pk = request.GET.get('id')
        add_folder_form = FolderCreateForm()
        # form_edit_folder = FolderEditForm()
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
            'add_folder_form': add_folder_form,
            # 'form_edit_folder': form_edit_folder,
            'custom_folder_list': queryset,
            'backup_list': file_query,
            # 'add_folder': reverse('folder:folder_create_with_parent', kwargs={
            #     'parent_folder_id': pk}) if pk else reverse(
            #     'folder:folder_create'),
            'parent_folder': parent_folder,
        }

        return render(request, self.template_name, context)





