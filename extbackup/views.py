import ftplib

from django.contrib import messages
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

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


def upload_files(request):
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            zip_file = BytesIO()
            with zipfile.ZipFile(zip_file, mode='w') as zf:
                for file in request.FILES.getlist('file'):
                    # encrypt each file
                    fernet = Fernet(key)
                    original = file.read()
                    encrypted = fernet.encrypt(original)
                    # write into zip
                    zf.writestr(file.name + '_encrypted', encrypted)
                    file_data = File(user=request.user, file=file)
            zip_file.seek(0)
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            file_name = f'uploads/upload_{request.user.username}/save_{timestamp}_{request.user.username}.zip'
            saved_file = default_storage.save(file_name, zip_file)
            # Save the compressed file in the database model
            saved_file_model = File(
                user=request.user,
                file=saved_file.split("/")[-1],
                description=form.cleaned_data['description']
            )
            saved_file_model.save()
            return redirect('extbackup:upload_files')
    else:
        form = FileForm()
    return render(request, 'extbackup/upload.html', {'form': form})


def backup_dashboard(request):
    files = File.objects.filter(user=request.user)
    zip_files = [(file.id, file.file.name, file.description, file.uploaded_at)
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
    ftp_storage = FTPStorage()
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
