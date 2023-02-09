from django.urls import path
from . import views
from .models import SupportedExtension

app_name = 'extbackup'

urlpatterns = [
    path('', views.UploadFilesView.as_view(),name='upload_files'),
    path('dashboard/', views.backup_dashboard, name="backup_dashboard"),
    path('delete/', views.DeleteZipFileView.as_view(), name='delete_zip_file'),
    path('download/<int:file_id>/', views.download_zip_file,
         name="download_zip_file"),
    path('view_content/<int:file_id>/', views.view_zip_content, name='view_zip_content'),
    path('refresh/', views.backup_refresh, name='backup_refresh'),


    path('extensions/', views.SupportedExtensionListView.as_view(), name='extension_list'),
    path('extensions/create/', views.SupportedExtensionCreateView.as_view(), name='extension_create'),
    path('extensions/<int:pk>/update/', views.SupportedExtensionUpdateView.as_view(), name='extension_update'),
    path('extensions/<int:pk>/delete/', views.SupportedExtensionDeleteView.as_view(), name='extension_delete'),
]
