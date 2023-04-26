from django.urls import path
from . import views


app_name = 'extbackup'

urlpatterns = [
    path('', views.BackupUploadView.as_view(), name='upload_files'),
    path('dashboard/', views.BackupDashboardView.as_view(),
         name="backup_dashboard"),
    path('delete/', views.DeleteBackupsView.as_view(),
         name='delete_backup_view'),
    path('download/<int:file_id>/', views.download_zip_file,
         name="download_zip_file"),
    path('view_content/<int:file_id>/', views.view_zip_content,
         name='view_zip_content'),
    path('refresh/', views.backup_refresh, name='backup_refresh'),
    path('check_file_hashes/<int:file_id>/', views.check_file_hashes,
         name='check_file_hashes'),


    path('extensions/', views.SupportedExtensionListView.as_view(),
         name='extension_list'),
    path('extensions/create/', views.SupportedExtensionCreateView.as_view(),
         name='extension_create'),
    path('extensions/delete/', views.SupportedExtensionDeleteAllView.as_view(),
         name='delete_all_extension'),
    path('extensions/<int:pk>/update/', views.SupportedExtensionUpdateView.as_view(),
         name='extension_update'),
    path('extensions/export/', views.SupportedExtensionExportView.as_view(),
         name='extension_export'),
]
