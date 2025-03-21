import ast
import csv
import random
from bootstrap_modal_forms.generic import BSModalDeleteView
from cryptography.fernet import Fernet
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
# from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views import View
from dj_dastore.decorator import dev, user_is_subscriber, \
    user_is_active_subscriber
from extbackup.forms import FileForm
from extbackup.models import File
from django.core.files.storage import default_storage
from datetime import datetime, timedelta
import os
import zipfile
from django.http import FileResponse, JsonResponse, HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from folder.models import Folder
from .tools import extract_file_contents, calculate_storage_remaining, \
    fernet_encrypt, calculate_file_hash
from django.contrib.auth.decorators import login_required
from io import BytesIO
from .key import key


@method_decorator(user_is_active_subscriber, name='dispatch')
class BackupUploadView(View):
    def post(self, request):
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')
            try:
                file_contents = extract_file_contents(files)
            except Exception as e:
                return JsonResponse({'error': str(e)})

            # Check remaining storage limit for all files combined
            user_account = request.user
            storage_limit = user_account.storage_limit \
                if user_account.storage_limit else 0
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

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rand_num = random.randint(1000, 9999)
            folder_name = f'uploads/upload_{request.user.username}' \
                          f'/backup_{timestamp}_{rand_num}'

            total_size = 0
            for file in files:
                with file.open() as original:
                    encrypted_content = fernet_encrypt(original.read())

                encrypted_file_name = f'{folder_name}/{file.name}_encrypted'
                default_storage.save(
                    encrypted_file_name,
                    BytesIO(encrypted_content))
                # encrypted_file_path = default_storage.path(encrypted_file)
                # encrypted_file_size = os.path.getsize(encrypted_file_path)
                encrypted_file_size = len(encrypted_content)

                total_size += encrypted_file_size

            request.user.storage_usage += total_size
            request.user.save()
            parent_folder_id = request.POST.get('parent_folder_id')
            folder_instance = None
            if parent_folder_id:
                folder_instance = get_object_or_404(Folder,
                                                    pk=parent_folder_id)
            print("parent_folder_id")
            print(parent_folder_id)
            new_file = File(
                user=request.user,
                name=folder_name.split("/")[-1],
                file=folder_name.split("/")[-1],
                folder=folder_instance,
                description=form.cleaned_data['description'],
                size=total_size,
                content=file_contents,
            )
            new_file.save()

            return JsonResponse({'message': 'Data uploaded !'}, status=200)
        return JsonResponse({'message': 'Form is not valid'}, status=400)


# @method_decorator(user_is_active_subscriber, name='dispatch')
# class BackupDashboardView(View):
#     def get(self, request):
#         try:
#             folders = File.objects.filter(user=request.user) \
#                 .order_by('-uploaded_at') \
#                 .values_list('id', 'file', 'description', 'uploaded_at', 'size')
#         except Exception as e:
#             messages.error("An error occurred: {}".format(str(e)))
#             return render(request, 'extbackup/backup_dashboard.html',
#                           {'folders': folders})
#         return render(request, 'extbackup/backup_dashboard.html',
#                       {'folders': folders})


@user_is_active_subscriber
def check_file_hashes(request, file_id):
    user = request.user

    if not user.update_rate_limit():
        return JsonResponse({'message': 'Too Many Requests'}, status=429)

    # Define the rate limit time interval (e.g., 1 minute)
    rate_limit_interval = timedelta(seconds=30)

    # Get the current time
    current_time = datetime.now()

    # Check if the last request timestamp is stored in the session
    if 'last_request_timestamp' in request.session:
        last_request_timestamp = request.session['last_request_timestamp']
        last_request_time = datetime.fromisoformat(last_request_timestamp)

        # If the time elapsed since the last request is less than the rate limit interval, block the request
        if current_time - last_request_time < rate_limit_interval:
            return JsonResponse({
                'message': 'Rate limit exceeded. Please wait before trying again.'},
                status=429)

    # Update the last request timestamp in the session
    request.session['last_request_timestamp'] = current_time.isoformat()

    ftp_storage = default_storage
    folder_path = f'uploads/upload_{request.user.username}/'
    file = File.objects.get(pk=file_id)
    folder_name = file.file
    fernet = Fernet(key)

    if ftp_storage.exists(folder_path + str(folder_name)):
        def compare_hashes(file_tree, folder_path):
            all_hashes_match = True
            for file_name, file_info in file_tree.items():
                if isinstance(file_info, dict):
                    if 'hash' in file_info:
                        stored_hash = file_info['hash']
                        file_path = os.path.join(
                            folder_path, file_name + "_encrypted")
                        if ftp_storage.exists(file_path):
                            with ftp_storage.open(file_path, 'rb') as f:
                                file_data = f.read()
                                decrypted = fernet.decrypt(file_data)
                                calculated_hash = calculate_file_hash(
                                    BytesIO(decrypted))
                            print(
                                f"Checking hash for file {file_name}: "
                                f"stored({stored_hash}) "
                                f"vs calculated({calculated_hash})")

                            if stored_hash != calculated_hash:
                                all_hashes_match = False
                                print(f"Hash mismatch for file {file_name}: "
                                      f"stored({stored_hash}) "
                                      f"vs calculated({calculated_hash})")
                        else:
                            print(f"File not found: {file_name}")
                            all_hashes_match = False

                    if 'content' in file_info:
                        subfolder_path = os.path.join(folder_path, file_name)
                        all_hashes_match = all_hashes_match and compare_hashes(
                            file_info['content'], subfolder_path)

            return all_hashes_match

        result = compare_hashes(file.content, folder_path + str(folder_name))
        if result:
            return JsonResponse({'message': 'Integrity: OK'},
                                status=200)
        else:
            return JsonResponse({'message': 'Integrity: Mismatch'},
                                status=400)
    else:
        return HttpResponse("folder not found")


@user_is_active_subscriber
def download_zip_file(request, file_id):
    ftp_storage = default_storage
    folder_path = f'uploads/upload_{request.user.username}/'
    file = File.objects.get(pk=file_id)
    folder_name = file.file

    if ftp_storage.exists(folder_path + str(folder_name)):
        fernet = Fernet(key)
        new_zip_file = BytesIO()

        with zipfile.ZipFile(new_zip_file, mode='w') as new_zf:
            _, files = ftp_storage.listdir(folder_path + str(folder_name))
            for encrypted_file_name in files:
                encrypted_file_path = os.path.join(folder_path,
                                                   str(folder_name),
                                                   encrypted_file_name)
                if ftp_storage.exists(encrypted_file_path):
                    with ftp_storage.open(encrypted_file_path,
                                          'rb') as encrypted_file:
                        encrypted_data = encrypted_file.read()
                        decrypted = fernet.decrypt(encrypted_data)

                    new_file_name = encrypted_file_name.replace('_encrypted',
                                                                '')
                    new_zf.writestr(new_file_name, decrypted,
                                    compress_type=zipfile.ZIP_DEFLATED)
                else:
                    print(
                        f"Skipping file {encrypted_file_name}"
                        f"(not found in file tree)")

        new_zip_file.seek(0)
        response = FileResponse(new_zip_file, content_type='application/zip')
        response[
            'Content-Disposition'] = f'attachment; filename={folder_name}.zip'
        return response
    else:
        return HttpResponse("folder not found")


@method_decorator(user_is_active_subscriber, name='dispatch')
class BulkDownloadView(View):
    def post(self, request, *args, **kwargs):
        file_ids = self.request.POST.getlist('file_ids[]')
        folder_ids = self.request.POST.getlist('folder_ids[]')

        ftp_storage = default_storage
        user_folder_path = f'uploads/upload_{request.user.username}/'

        fernet = Fernet(key)
        new_zip_file = BytesIO()

        with zipfile.ZipFile(new_zip_file, mode='w') as new_zf:
            for file_id in file_ids:
                self.download_file(file_id, new_zf, ftp_storage,
                                   user_folder_path, fernet)

            for folder_id in folder_ids:
                folder = get_object_or_404(Folder, pk=folder_id)
                self.download_folder(folder, new_zf, ftp_storage,
                                     user_folder_path, fernet)

        new_zip_file.seek(0)
        # Check if any files were added to the zip
        with zipfile.ZipFile(new_zip_file) as zf:
            if not zf.filelist:
                # No files were added to the zip file.
                # Return an appropriate response.
                messages.error(request,
                               "This folder is empty.")
                return HttpResponseRedirect(reverse('folder:folder_list'))
        new_zip_file.seek(0)

        response = FileResponse(new_zip_file, content_type='application/zip')
        response[
            'Content-Disposition'] = f'attachment; filename=backup_files.zip'
        return response

    def download_file(self, file_id, new_zf, ftp_storage,
                      user_folder_path, fernet, folder_structure=""):
        file = File.objects.get(pk=file_id)
        folder_name = file.file

        if ftp_storage.exists(user_folder_path + str(folder_name)):
            _, files = ftp_storage.listdir(user_folder_path + str(folder_name))
            for encrypted_file_name in files:
                encrypted_file_path = os.path.join(user_folder_path,
                                                   str(folder_name),
                                                   encrypted_file_name)
                if ftp_storage.exists(encrypted_file_path):
                    with ftp_storage.open(encrypted_file_path,
                                          'rb') as encrypted_file:
                        encrypted_data = encrypted_file.read()
                        decrypted = fernet.decrypt(encrypted_data)

                    new_file_name = folder_structure + encrypted_file_name.replace(
                        '_encrypted', '')
                    new_zf.writestr(new_file_name, decrypted,
                                    compress_type=zipfile.ZIP_DEFLATED)
                else:
                    print(
                        f"Skipping file {encrypted_file_name}"
                        f"(not found in file tree)")

    def download_folder(self, folder, new_zf, ftp_storage, user_folder_path,
                        fernet, folder_structure=""):
        # First, check if the folder is empty
        if not folder.files.exists() and not folder.children.exists():
            print(f"Skipping folder {folder.name} (it's empty)")
            return
        # First, download all files in this folder
        new_folder_structure = folder_structure + folder.name + "/"
        for file in folder.files.all():
            self.download_file(file.pk, new_zf, ftp_storage, user_folder_path,
                               fernet, new_folder_structure)

        for child_folder in folder.children.all():
            self.download_folder(child_folder, new_zf, ftp_storage,
                                 user_folder_path, fernet,
                                 new_folder_structure)


# def traverse_content_tree(content, parent_path=""):
#     for name, node in content.items():
#         path = parent_path + "/" + name if parent_path else name
#         if 'hash' in node:
#             yield path, node
#         else:
#             yield from traverse_content_tree(node, path)

@method_decorator(user_is_active_subscriber, name='dispatch')
class DeleteBackupsView(SuccessMessageMixin, BSModalDeleteView):
    # We'll set the model dynamically based on the item to delete.
    model = None
    template_name = 'extbackup/folder_delete.html'
    success_message = 'Success: Item was deleted.'
    success_url = reverse_lazy('folder:folder_list')

    def get_object(self):
        if 'file_id' in self.kwargs:
            self.model = File
            return get_object_or_404(File, pk=self.kwargs['file_id'])
        elif 'folder_id' in self.kwargs:
            self.model = Folder
            return get_object_or_404(Folder, pk=self.kwargs['folder_id'])

    def delete(self, request, *args, **kwargs):
        ftp_storage = default_storage
        deleted_items = []

        self.object = self.get_object()
        # Save parent folder id before deleting the object
        if isinstance(self.object, Folder):
            self.parent_id = self.object.parent.pk if self.object.parent else None
        elif isinstance(self.object, File):
            self.parent_id = self.object.folder.pk if self.object.folder else None

        if self.object.user != request.user:
            messages.error(request, "Cannot delete someone else's items")
            return super().delete(request, *args, **kwargs)

        if isinstance(self.object, Folder):
            self.delete_folder(self.object, ftp_storage, deleted_items)
        elif isinstance(self.object, File):
            self.delete_file(self.object, ftp_storage)
            deleted_items.append(self.object.name)

        if deleted_items:
            messages.success(request, f"Items {', '.join(deleted_items)} "
                                      f"deleted successfully")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.parent_id:
            return reverse('folder:folder_list') + '?id=' + str(self.parent_id)
        else:
            return reverse('folder:folder_list')

    def delete_folder(self, folder, storage, deleted_items):
        for child_folder in folder.children.all():
            self.delete_folder(child_folder, storage, deleted_items)
        for file in folder.files.all():
            self.delete_file(file, storage)
        deleted_items.append(folder.name)
        folder.delete()

    def delete_file(self, file, storage):
        # Delete the file from storage
        folder_path = f'uploads/upload_{file.user.username}/{file.file.name}/'
        folder_files = storage.listdir(folder_path)[1]
        for folder_file in folder_files:
            storage.delete(f'{folder_path}{folder_file}')
        storage.delete(folder_path)

        # Update user storage usage and delete the File object
        file.user.storage_usage -= file.size
        file.user.save()
        file.delete()


@method_decorator(user_is_active_subscriber, name='dispatch')
class BulkDeleteBackupsView(View):
    def post(self, request, *args, **kwargs):
        file_ids = self.request.POST.getlist('file_ids[]')
        folder_ids = self.request.POST.getlist('folder_ids[]')

        files = File.objects.filter(id__in=file_ids, user=request.user)
        folders = Folder.objects.filter(id__in=folder_ids, user=request.user)

        ftp_storage = default_storage
        deleted_items = []

        for file in files:
            self.delete_file(file, ftp_storage)
            deleted_items.append(file.name)

        for folder in folders:
            self.delete_folder(folder, ftp_storage, deleted_items)

        if deleted_items:
            messages.success(request, f"Items deleted successfully")

        return HttpResponseRedirect(reverse('folder:folder_list'))

    def delete_folder(self, folder, storage, deleted_items):
        for child_folder in folder.children.all():
            self.delete_folder(child_folder, storage, deleted_items)
        for file in folder.files.all():
            self.delete_file(file, storage)
        deleted_items.append(folder.name)
        folder.delete()

    def delete_file(self, file, storage):
        folder_path = f'uploads/upload_{file.user.username}/{file.file.name}/'
        folder_files = storage.listdir(folder_path)[1]
        for folder_file in folder_files:
            storage.delete(f'{folder_path}{folder_file}')
        storage.delete(folder_path)
        file.user.storage_usage -= file.size
        file.user.save()
        file.delete()


@user_is_active_subscriber
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
            if key == 'hash':  # Skip the hash
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
    return render(request, 'extbackup/view_zip_content.html', {'tree': tree,
                                                               'file': file})


@user_passes_test(dev)
def backup_refresh(request):
    sys_storage = default_storage
    zip_files_folder = f'uploads/upload_{request.user.username}/'
    print(os.path.abspath(zip_files_folder))
    actual_zip_files = sys_storage.listdir(zip_files_folder)[1]
    for zip_file in actual_zip_files:
        file_path = sys_storage.path(os.path.join(zip_files_folder, zip_file))
        file_size = sys_storage.size(file_path)
        extracted_content = extract_file_contents(file_path)
        File.objects.update_or_create(file=zip_file, user=request.user,
                                      defaults={'file': zip_file,
                                                'size': file_size,
                                                'content': extracted_content})
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


