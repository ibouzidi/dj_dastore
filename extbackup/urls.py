from django.urls import path
from . import views


app_name = 'extbackup'

urlpatterns = [
    path('upload_files/', views.BackupUploadView.as_view(), name='upload_files'),
    path('delete_backup/file/<int:file_id>/',
         views.DeleteBackupsView.as_view(), name='delete_file_view'),
    path('download/<int:file_id>/', views.download_zip_file,
         name="download_zip_file"),
    path('view_content/<int:file_id>/', views.view_zip_content,
         name='view_zip_content'),
    path('refresh/', views.backup_refresh, name='backup_refresh'),
    path('check_file_hashes/<int:file_id>/', views.check_file_hashes,
         name='check_file_hashes'),
    path('delete_selected/', views.BulkDeleteBackupsView.as_view(),
         name='bulk_delete_view'),
]
