import ftplib

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views import View

from extbackup.forms import FileForm
from extbackup.models import File
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
                        fernet = Fernet(key)
                        encrypted = fernet.encrypt(inner_file_data)
                        zf.writestr(inner_file.filename + '_encrypted', encrypted)
            else:
                fernet = Fernet(key)
                original = file.read()
                encrypted = fernet.encrypt(original)
                zf.writestr(file.name + '_encrypted', encrypted)
    zip_file.seek(0)
    return zip_file


class UploadFilesView(View):
    def get(self, request):
        form = FileForm()
        return render(request, 'extbackup/upload.html', {'form': form})

    def post(self, request):
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')
            # crypte files using Fernet encryption
            zip_file = encrypt_files(files)
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            file_name = f'uploads/upload_{request.user.username}' \
                        f'/save_{timestamp}_{request.user.username}.zip'
            saved_file = default_storage.save(file_name, zip_file)
            file_path = default_storage.path(saved_file)
            file_size = os.path.getsize(file_path)
            # save the file in database
            saved_file_model = File(
                user=request.user,
                file=saved_file.split("/")[-1], # name of the file without the path
                description=form.cleaned_data['description'],
                size=file_size,
            )
            saved_file_model.save()
            return JsonResponse({'data':'Data uploaded'})
        return JsonResponse({'data':'Something went wrong!!'})


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


def delete_zip_file(request, file_id):
    ftp_storage = FTPStorage()
    try:
        file = File.objects.get(pk=file_id)
        if file.user == request.user:
            zip_files = f'uploads/upload_{request.user.username}/'
            ftp_storage.delete(zip_files + file.file.name)

            file.delete()
            messages.success(request, "Zip file deleted successfully")
            # TODO: remove empty folders
            # folder_path = os.path.dirname(
            #     os.path.join(zip_files, file.file.name))
            # folder_contents = ftp_storage.listdir(zip_files)
            # if not folder_contents:
            #     os.rmdir(folder_path)
            # return redirect('extbackup:backup_dashboard')
        else:
            messages.error(request, "Cannot delete someone else's zip files")
            return redirect('extbackup:backup_dashboard')
    except File.DoesNotExist:
        messages.error(request, "Zip file not found")
        return redirect('extbackup:backup_dashboard')


def view_zip_content(request, file_id):
    ftp_storage = default_storage
    zip_files = f'uploads/upload_{request.user.username}/'
    try:
        file = File.objects.get(pk=file_id)
    except ObjectDoesNotExist:
        messages.error(request, "File not found")
        return redirect('extbackup:backup_dashboard')
    if ftp_storage.exists(zip_files + file.file.name):
        try:
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
            with zipfile.ZipFile(zip_buffer) as zf:
                zip_content = zf.namelist()
            return render(request, 'extbackup/view_zip_content.html',
                          {'zip_content': zip_content})
        except Exception as e:
            return HttpResponse(f"An error occured: {e}", status=500)
    else:
        messages.error(request, "file not found")
        return redirect('extbackup:backup_dashboard')

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
                 for file in File.objects.filter(user=request.user) if file.file.name.endswith('.zip')]
    return render(request, 'extbackup/backup_dashboard.html',
                  {'zip_files': zip_files})