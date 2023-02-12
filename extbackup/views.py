import ftplib

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View

from extbackup.forms import FileForm, ExtensionForm
from extbackup.models import File, SupportedExtension
from django.conf import settings
from django.core.files.storage import default_storage
from io import BytesIO
from datetime import datetime
import os
from storages.backends.ftp import FTPStorage
from django.http import FileResponse, JsonResponse, HttpResponseRedirect, \
    Http404, HttpResponseForbidden
import io
from urllib.request import urlopen
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
# import wget
import tempfile
import zipfile
from .key import key
from cryptography.fernet import Fernet


def encrypt_files(files):
    zip_file = BytesIO()
    with zipfile.ZipFile(zip_file, mode='w') as zf:
        for file in files:
            if file.content_type == "application/x-zip-compressed":
                folder_file = BytesIO(file.read())
                with zipfile.ZipFile(folder_file) as folder_zip:
                    for inner_file in folder_zip.infolist():
                        inner_file_data = folder_zip.read(inner_file)
                        encrypted = fernet_encrypt(inner_file_data)
                        zf.writestr(inner_file.filename + '_encrypted', encrypted)
            else:
                original = file.read()
                encrypted = fernet_encrypt(original)
                zf.writestr(file.name + '_encrypted', encrypted)
    zip_file.seek(0)
    return zip_file


def fernet_encrypt(data):
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data)
    return encrypted


def extract_zip_contents(zip_file_path):
    file_tree = {}
    with zipfile.ZipFile(zip_file_path) as zip_file:
        for inner_file in zip_file.infolist():
            path = inner_file.filename
            parts = path.split('/')
            parent = file_tree
            for part in parts[:-1]:
                if part not in parent:
                    parent[part.replace("_encrypted", "")] = {}
                parent = parent[part.replace("_encrypted", "")]
            if parts[-1] == '':
                continue
            parent[parts[-1].replace("_encrypted", "")] = None
    return file_tree


class UploadFilesView(View):
    def get(self, request):
        form = FileForm()
        return render(request, 'extbackup/upload.html', {'form': form})

    def post(self, request):
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')
            # Check if the file extension is supported
            for file in files:
                file_extension = file.name.split(".")[-1].lower()
                print("file_extension")
                print(file_extension)
                if not SupportedExtension.objects.filter(extension=file_extension).exists():
                    return JsonResponse({'data': f"File extension {file_extension} is not supported.", 'messages': [
                        {'level_tag': 'alert-danger', 'message': f"File extension {file_extension} is not supported."}]})

            # crypte files using Fernet encryption
            try:
                zip_file = encrypt_files(files)
                size = zip_file.tell()
                # zip_file.seek(0, 2)  # move to the end of the file
                # size = zip_file.tell()  # get the current position, which is the length of the file
                # zip_file.seek(0)  # reset the position to the beginning of the file
                # Check if the user has enough storage space
                user_account = request.user
                if user_account.subscription_plan is not None:
                    storage_limit = user_account.subscription_plan.storage_limit
                    storage_limit_gb = storage_limit * 1024 ** 3
                else:
                    storage_limit = 0
                size_conversion = size * 1024 ** 3
                if user_account.storage_usage + size_conversion > storage_limit_gb:

                    return JsonResponse(
                        {
                            'data': f"Storage limit of {storage_limit:.2f} GB has been reached.",
                            'messages': [
                                {'level_tag': 'alert-danger',
                                 'message': f"Storage limit of {storage_limit:.2f} GB has been reached."}]})
            except Exception as e:
                return JsonResponse({'error': str(e)})
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            file_name = f'uploads/upload_{request.user.username}' \
                        f'/save_{timestamp}_{request.user.username}.zip'
            try:
                saved_file = default_storage.save(file_name, zip_file)
                file_path = default_storage.path(saved_file)
                file_size = os.path.getsize(file_path)
                # extract the contents of the zip file
                try:
                    extracted_content = extract_zip_contents(file_path)
                except Exception as e:
                    return JsonResponse({'error': str(e)})
                # save the file in database
                saved_file_model = File(
                    user=request.user,
                    file=saved_file.split("/")[-1],  # name of the file without the path
                    description=form.cleaned_data['description'],
                    size=file_size,
                    content=extracted_content,
                )
                saved_file_model.save()
                request.user.storage_usage += file_size
                request.user.save()
                return JsonResponse({'data': 'Data uploaded', 'messages': [
                    {'level_tag': 'alert-success', 'message': 'Data uploaded'}]})
            except Exception as e:
                return JsonResponse({'error': str(e)})
        return JsonResponse({'error': 'Form is not valid'})


def backup_dashboard(request):
    files = File.objects.filter(user=request.user).order_by('-uploaded_at')
    zip_files = [(file.id, file.file.name, file.description, file.uploaded_at, file.size)
                 for file in files if file.file.name.endswith('.zip')]
    return render(request, 'extbackup/backup_dashboard.html',
                  {'zip_files': zip_files})


def decrypt_zip_file(file_data):
    fernet = Fernet(key)
    zip_file = BytesIO(file_data)
    with zipfile.ZipFile(zip_file, mode='r') as zf:
        new_zip_file = BytesIO()
        with zipfile.ZipFile(new_zip_file, mode='w') as new_zf:
            for file in zf.infolist():
                original = zf.read(file)
                decrypted = fernet.decrypt(original)
                new_zf.writestr(file.filename, decrypted)
    new_zip_file.seek(0)
    return new_zip_file


def download_zip_file(request, file_id):
    ftp_storage = default_storage
    zip_files = f'uploads/upload_{request.user.username}/'
    file = File.objects.get(pk=file_id)
    if ftp_storage.exists(zip_files + file.file.name):
        with ftp_storage.open(zip_files + file.file.name, 'rb') as f:
            file_data = f.read()
        decrypted_zip = decrypt_zip_file(file_data)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w") as zf:
            with zipfile.ZipFile(decrypted_zip, mode="r") as zf_decrypted:
                for info in zf_decrypted.infolist():
                    if "_encrypted" in info.filename:
                        new_file_name = info.filename.replace("_encrypted", "")
                    else:
                        new_file_name = info.filename
                    zf.writestr(new_file_name,
                                zf_decrypted.read(info.filename))
        zip_buffer.seek(0)
        response = FileResponse(zip_buffer, content_type='application/zip')
        response[
            'Content-Disposition'] = 'attachment; filename=' + file.file.name
        return response
    else:
        return HttpResponse("file not found")


class DeleteZipFileView(View):
    def post(self, request):
        ids = request.POST.getlist('ids')
        ftp_storage = default_storage
        deleted_files = []
        for file_id in ids:
            try:
                file = File.objects.get(id=file_id)
                if file.user == request.user:
                    zip_files = f'uploads/upload_{request.user.username}/'
                    ftp_storage.delete(zip_files + file.file.name)
                    file.delete()
                    file_size = file.size
                    request.user.storage_usage -= file_size
                    request.user.save()
                    deleted_files.append(file.file.name)
                else:
                    messages.error(request, "Cannot delete someone else's zip files")
                    return redirect('extbackup:backup_dashboard')
            except File.DoesNotExist:
                messages.error(request, "Zip file not found")
                return redirect('extbackup:backup_dashboard')
            except PermissionError:
                messages.error(request, "Cannot delete a zip file that is used or open by another processus")
        if deleted_files:
            messages.success(request, "Zip files deleted successfully")
        return redirect('extbackup:backup_dashboard')


# def build_tree(data, parent=None):
#     data = json.loads(data)
#     tree = defaultdict(list)
#     print(data)
#     for key, value in data.items():
#         print("key")
#         print(key)
#         print("value")
#         print(value)
#         if parent == key:
#             print("YES")
#             tree[parent].append(value)
#             print(tree)
#             print(data)
#             tree.update(build_tree(json.dumps(value), parent=key))
#     return tree

def build_tree(data, parent=None):
    tree = []
    for key, value in data.items():
        if not parent:
            node = {"name": key}
        else:
            node = {"name": key, "parent": parent}
        if isinstance(value, dict):
            node["children"] = build_tree(value, key)
        tree.append(node)
    return tree


def view_zip_content(request, file_id):
    try:
        file = File.objects.get(pk=file_id)
    except ObjectDoesNotExist:
        messages.error(request, "File not found")
        return redirect('extbackup:backup_dashboard')

    tree = build_tree(file.content)
    return render(request, 'extbackup/view_zip_content.html', {'tree': tree})


def backup_refresh(request):
    ftp_storage = default_storage
    zip_files_folder = f'uploads/upload_{request.user.username}/'
    actual_zip_files = ftp_storage.listdir(zip_files_folder)[1]
    for zip_file in actual_zip_files:
        file_path = os.path.join(zip_files_folder, zip_file)
        file_size = ftp_storage.size(file_path)
        File.objects.update_or_create(file=zip_file, user=request.user,
                                      defaults={'file': zip_file, 'size': file_size})
    # Check for files in model not in folder
    for file in File.objects.filter(user=request.user):
        if file.file not in actual_zip_files:
            file.delete()
    # Get updated zip files
    zip_files = [(file.id, file.file.name, file.description, file.uploaded_at, file.size)
                 for file in File.objects.filter(user=request.user).order_by('-uploaded_at')
                 if file.file.name.endswith('.zip')]
    return render(request, 'extbackup/backup_dashboard.html',
                  {'zip_files': zip_files})


class SupportedExtensionListView(ListView):
    model = SupportedExtension
    ordering = ['-id']
    template_name = 'extension/extension_list.html'


class SupportedExtensionCreateView(CreateView):
    model = SupportedExtension
    template_name = 'extension/extension_form.html'
    form_class = ExtensionForm
    success_url = reverse_lazy('extbackup:extension_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Add any additional processing here, such as sending an email or
        # logging the action.
        return response


class SupportedExtensionUpdateView(UpdateView):
    model = SupportedExtension
    template_name = 'extension/extension_form.html'
    form_class = ExtensionForm
    success_url = reverse_lazy('extbackup:extension_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Add any additional processing here, such as sending an email or
        # logging the action.
        return response


class SupportedExtensionDeleteView(DeleteView):
    model = SupportedExtension
    success_url = reverse_lazy('extbackup:extension_list')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
