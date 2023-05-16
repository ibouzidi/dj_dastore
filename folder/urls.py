from django.urls import path
from . import views


app_name = 'folder'

urlpatterns = [
    path('create/', views.FolderCreateView.as_view(), name='folder_create'),
    path('', views.FolderListView.as_view(), name='folder_list'),
    path('create/<int:parent_folder_id>/', views.FolderCreateView.as_view(), name='folder_create_with_parent'),
    # path('delete_backup/', views.DeleteFolderView.as_view(),
    #      name='delete_folder_view'),
    path('folder_rename/', views.RenameFolderView.as_view(), name='folder_rename'),
    path('edit_form/', views.get_folder_edit_form, name='get_folder_edit_form'),

]
