import csv
import ftplib
import mimetypes

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
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
                        zf.writestr(inner_file.filename + '_encrypted',
                                    encrypted,
                                    compress_type=zipfile.ZIP_DEFLATED)
            else:
                original = file.read()
                encrypted = fernet_encrypt(original)
                zf.writestr(file.name + '_encrypted', encrypted,
                            compress_type=zipfile.ZIP_DEFLATED)
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


def calculate_storage_remaining(total_size, user_account, storage_limit):
    if user_account.subscription_plan is not None:
        storage_limit_gb = storage_limit * 1024 ** 3
    else:
        storage_limit_gb = 0
    size_conversion = total_size
    remaining_storage = storage_limit_gb - (user_account.storage_usage + size_conversion)
    return remaining_storage


class UploadFilesView(View):
    def get(self, request):
        form = FileForm()
        supported_extensions = list(
            SupportedExtension.objects.values_list('extension', flat=True))
        context = {'form': form, 'supported_extensions': supported_extensions}

        return render(request, 'extbackup/upload.html', context)

    def post(self, request):
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')
            # Check if any file extension is not supported
            unsupported_files = []
            for file in files:
                mime_type, encoding = mimetypes.guess_type(file.name)
                if not SupportedExtension.objects.filter(
                        extension=mime_type).exists():
                    unsupported_files.append(file.name)

            # Return error if any file extension is not supported
            if unsupported_files:
                return JsonResponse({
                    'error': f"File type is not supported for files: "
                             f"{', '.join(unsupported_files)}",
                })

            # Check remaining storage limit for all files combined
            user_account = request.user
            storage_limit = user_account.subscription_plan.storage_limit \
                if user_account.subscription_plan else 0
            total_size = sum(file.size for file in files)
            remaining_storage = calculate_storage_remaining(total_size,
                                                            user_account,
                                                            storage_limit)
            # Return error if storage limit is exceeded
            if remaining_storage < 0:
                return JsonResponse({
                    'message': f"Your plan storage limit of {storage_limit:.1f}"
                               f" GB has been reached.",
                }, status=400)
            # crypte files using Fernet encryption
            # and compress files to one zip file
            try:
                zip_file = encrypt_files(files)
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
                request.user.storage_usage += file_size
                request.user.save()
                # extract the contents of the zip file
                try:
                    extracted_content = extract_zip_contents(file_path)
                except Exception as e:
                    return JsonResponse({'error': str(e)})

                # save the file in database
                saved_file_model = File(
                    user=request.user,
                    # name of the file without the path
                    file=saved_file.split("/")[-1],
                    description=form.cleaned_data['description'],
                    size=file_size,
                    content=extracted_content,
                )
                saved_file_model.save()
                return JsonResponse({'message': 'Data uploaded !', }, status=200)
            except Exception as e:
                return JsonResponse({'message': str(e)}, status=400)
        return JsonResponse({'message': 'Form is not valid'}, status=400)


def backup_dashboard(request):
    try:
        zip_files = File.objects.filter(user=request.user, file__endswith='.zip')\
            .order_by('-uploaded_at')\
            .values_list('id', 'file', 'description', 'uploaded_at', 'size')
    except Exception as e:
        messages.error("An error occurred: {}".format(str(e)))
        return render(request, 'extbackup/backup_dashboard.html',
                      {'zip_files': zip_files})
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
                new_zf.writestr(file.filename, decrypted,
                                compress_type=zipfile.ZIP_DEFLATED)
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
                    messages.error(request,
                                   "Cannot delete someone else's zip files")
                    return redirect('extbackup:backup_dashboard')
            except File.DoesNotExist:
                messages.error(request, "Zip file not found")
                return redirect('extbackup:backup_dashboard')
            except PermissionError:
                messages.error(request,
                               "Cannot delete a zip file that is used or open by another processus")
        if deleted_files:
            messages.success(request, "Zip files deleted successfully")
        return redirect('extbackup:backup_dashboard')


def view_zip_content(request, file_id):
    try:
        file = File.objects.get(pk=file_id)
    except ObjectDoesNotExist:
        messages.error(request, "File not found")
        return redirect('extbackup:backup_dashboard')

    def build_tree(data, parent=None):
        tree = []
        for key, value in data.items():
            if not key:
                continue
            if not parent:
                node = {"name": key}
            else:
                node = {"name": key, "parent": parent}
            if isinstance(value, dict):
                node["children"] = build_tree(value, key)
            tree.append(node)
        return tree

    tree = build_tree(file.content)
    print(tree)
    return render(request, 'extbackup/view_zip_content.html', {'tree': tree})


def backup_refresh(request):
    sys_storage = default_storage
    zip_files_folder = f'uploads/upload_{request.user.username}/'
    print(os.path.abspath(zip_files_folder))
    actual_zip_files = sys_storage.listdir(zip_files_folder)[1]
    for zip_file in actual_zip_files:
        file_path = sys_storage.path(os.path.join(zip_files_folder, zip_file))
        file_size = sys_storage.size(file_path)
        extracted_content = extract_zip_contents(file_path)
        File.objects.update_or_create(file=zip_file, user=request.user,
                                      defaults={'file': zip_file,
                                                'size': file_size,
                                                'content':extracted_content})
    # Check for files in model not in folder
    for file in File.objects.filter(user=request.user):
        if file.file not in actual_zip_files:
            file.delete()
    # Get updated zip files
    zip_files = [(file.id, file.file.name, file.description, file.uploaded_at,
                  file.size, file.content)
                 for file in File.objects.filter(user=request.user).order_by(
            '-uploaded_at')
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = [{'url': reverse('extbackup:extension_list'),
                                  'label': 'Extensions'},
                                 {'url': '#', 'label': 'Create Extension'}]
        return context


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


class SupportedExtensionDeleteAllView(View):
    def post(self, request):
        ids = request.POST.getlist('ids')
        deleted_files = []
        for extension_id in ids:
            try:
                extension = SupportedExtension.objects.get(id=extension_id)
                deleted_files.append(extension.extension)
                extension.delete()
            except SupportedExtension.DoesNotExist:
                messages.error(request, "Extension not found")
                return redirect('extbackup:extension_list')
        if deleted_files:
            message = "Extension deleted successfully"
            messages.success(request, message)
        return redirect('extbackup:extension_list')


class SupportedExtensionExportView(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; ' \
                                          'filename="supported_extensions.csv"'

        # Get all the extensions
        supported_extension = SupportedExtension.objects.order_by('extension')

        # Write CSV headers
        writer = csv.writer(response)
        writer.writerow(['extension'])
        # Write CSV data
        for i in supported_extension:
            writer.writerow([i.extension])
        messages.success(request, "Extension exported with success.")
        return response

