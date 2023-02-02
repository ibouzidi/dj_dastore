from django.urls import path
from . import views

app_name = 'extbackup'

urlpatterns = [
    path('', views.upload_files,name='upload_files'),
    path('dashboard/', views.backup_dashboard, name="backup_dashboard"),
    # path('backups/delete/<str:filetext>', views.delete_zip_file,name="delete_zip_file"),
    path('delete/<int:file_id>', views.delete_zip_file, name='delete_zip_file'),
    path('download/<int:file_id>', views.download_zip_file,
         name="download_zip_file"),
]
