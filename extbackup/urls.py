from django.urls import path
from . import views

app_name = 'extbackup'

urlpatterns = [
    path('', views.UploadFilesView.as_view(),name='upload_files'),
    path('dashboard/', views.backup_dashboard, name="backup_dashboard"),
    path('delete/<int:file_id>/', views.delete_zip_file, name='delete_zip_file'),
    path('download/<int:file_id>/', views.download_zip_file,
         name="download_zip_file"),
    path('view_content/<int:file_id>/', views.view_zip_content, name='view_zip_content'),
    path('refresh/', views.backup_refresh, name='backup_refresh'),
]
