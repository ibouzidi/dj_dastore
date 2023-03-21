import csv
import magic
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, HttpResponse
# from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views import View
from dj_dastore.decorator import dev
from extbackup.forms import FileForm, ExtensionForm
from extbackup.models import File, SupportedExtension
from django.core.files.storage import default_storage
from datetime import datetime
import os
import zipfile
from django.http import FileResponse, JsonResponse
import io
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .tools import extract_zip_contents, decrypt_zip_file, encrypt_files, \
    calculate_storage_remaining
from django.contrib.auth.decorators import login_required


@method_decorator(login_required, name='dispatch')
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
            mime = magic.Magic(mime=True)
            for file in files:
                if os.path.exists(file.name):
                    mime_type = mime.from_file(file.name)
                    if not SupportedExtension.objects.filter(
                            extension=mime_type).exists():
                        unsupported_files.append(file.name)
                else:
                    print(f"{file.name} path does not exist")
            # Return error if any file extension is not supported
            if unsupported_files:
                return JsonResponse({
                    'message': f"File type is not supported for files: "
                             f"{', '.join(unsupported_files)}",
                }, status=400)

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
                return JsonResponse({'message': 'Data uploaded !', },
                                    status=200)
            except Exception as e:
                return JsonResponse({'message': str(e)}, status=400)
        return JsonResponse({'message': 'Form is not valid'}, status=400)


@login_required
def backup_dashboard(request):
    try:
        zip_files = File.objects.filter(user=request.user,
                                        file__endswith='.zip') \
            .order_by('-uploaded_at') \
            .values_list('id', 'file', 'description', 'uploaded_at', 'size')
    except Exception as e:
        messages.error("An error occurred: {}".format(str(e)))
        return render(request, 'extbackup/backup_dashboard.html',
                      {'zip_files': zip_files})
    return render(request, 'extbackup/backup_dashboard.html',
                  {'zip_files': zip_files})


@login_required
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


@method_decorator(login_required, name='dispatch')
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
                               "Cannot delete a zip file that is used "
                               "or open by another processus")
        if deleted_files:
            messages.success(request, "Zip files deleted successfully")
        return redirect('extbackup:backup_dashboard')


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
        extracted_content = extract_zip_contents(file_path)
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


@method_decorator(user_passes_test(dev), name='dispatch')
class SupportedExtensionListView(ListView):
    model = SupportedExtension
    ordering = ['-id']
    template_name = 'extension/extension_list.html'


@method_decorator(user_passes_test(dev), name='dispatch')
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


@method_decorator(user_passes_test(dev), name='dispatch')
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


@method_decorator(user_passes_test(dev), name='dispatch')
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


@method_decorator(user_passes_test(dev), name='dispatch')
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
