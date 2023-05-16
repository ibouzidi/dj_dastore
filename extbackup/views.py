import ast
import csv
import random
import magic
from cryptography.fernet import Fernet
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
# from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views import View
from dj_dastore.decorator import dev
from extbackup.forms import FileForm
from extbackup.models import File
from django.core.files.storage import default_storage
from datetime import datetime, timedelta
import os
import zipfile
from django.http import FileResponse, JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from folder.models import Folder
from .tools import extract_file_contents, calculate_storage_remaining, \
    fernet_encrypt, calculate_file_hash
from django.contrib.auth.decorators import login_required
from io import BytesIO
from .key import key


@method_decorator(login_required, name='dispatch')
class BackupUploadView(View):
    def post(self, request):
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')
            try:
                file_contents = extract_file_contents(files)
            except Exception as e:
                return JsonResponse({'error': str(e)})

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rand_num = random.randint(1000, 9999)
            folder_name = f'uploads/upload_{request.user.username}' \
                          f'/backup_{timestamp}_{rand_num}'

            total_size = 0
            for file in files:
                with file.open() as original:
                    encrypted_content = fernet_encrypt(original.read())

                encrypted_file_name = f'{folder_name}/{file.name}_encrypted'
                encrypted_file = default_storage.save(encrypted_file_name,
                                                      BytesIO(
                                                          encrypted_content))
                encrypted_file_path = default_storage.path(encrypted_file)
                encrypted_file_size = os.path.getsize(encrypted_file_path)

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


@method_decorator(login_required, name='dispatch')
class BackupDashboardView(View):
    def get(self, request):
        try:
            folders = File.objects.filter(user=request.user) \
                .order_by('-uploaded_at') \
                .values_list('id', 'file', 'description', 'uploaded_at', 'size')
        except Exception as e:
            messages.error("An error occurred: {}".format(str(e)))
            return render(request, 'extbackup/backup_dashboard.html',
                          {'folders': folders})
        return render(request, 'extbackup/backup_dashboard.html',
                      {'folders': folders})


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


@login_required
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


# def traverse_content_tree(content, parent_path=""):
#     for name, node in content.items():
#         path = parent_path + "/" + name if parent_path else name
#         if 'hash' in node:
#             yield path, node
#         else:
#             yield from traverse_content_tree(node, path)


@method_decorator(login_required, name='dispatch')
class DeleteBackupsView(View):
    def post(self, request, *args, **kwargs):
        file_id = request.POST.get('file_id')
        custom_folder_id = request.POST.get('custom_folder_id')
        ftp_storage = default_storage
        deleted_folders = []

        try:
            if file_id:
                file = File.objects.get(id=file_id)
                if file.user == request.user:
                    # If we're deleting a file, delete it from storage and database
                    self.delete_file(file, ftp_storage)
                    deleted_folders.append(file.name)
                else:
                    messages.error(request, "Cannot delete someone else's files")
                    return redirect('folder:folder_list')
            elif custom_folder_id:
                folder = Folder.objects.get(id=custom_folder_id)
                if folder.user == request.user:
                    # If we're deleting a custom folder, recursively delete all child folders and files
                    self.delete_folder(folder, ftp_storage, deleted_folders)
                else:
                    messages.error(request, "Cannot delete someone else's folders")
                    return redirect('folder:folder_list')
            else:
                messages.error(request, "File or Folder ID is missing")
                return redirect('folder:folder_list')
        except (File.DoesNotExist, Folder.DoesNotExist):
            messages.error(request, "File or Folder not found")
            return redirect('folder:folder_list')
        except PermissionError:
            messages.error(request, "Cannot delete a file or folder that is used or open by another process")
            return redirect('folder:folder_list')
        if deleted_folders:
            messages.success(request, f"Folders {', '.join(deleted_folders)} deleted successfully")
        return redirect('folder:folder_list')

    def delete_folder(self, folder, storage, deleted_folders):
        # Delete all child folders recursively
        for child_folder in folder.children.all():
            self.delete_folder(child_folder, storage, deleted_folders)

        # Delete all files in this folder
        for file in folder.files.all():
            self.delete_file(file, storage)

        # Delete the folder from the database
        deleted_folders.append(folder.name)
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


@login_required
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
    return render(request, 'extbackup/view_zip_content.html', {'tree': tree})


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


