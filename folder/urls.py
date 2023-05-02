from django.urls import path
from . import views


app_name = 'folder'

urlpatterns = [
    path('create/', views.FolderCreateView.as_view(), name='folder_create'),
    path('', views.FolderListView.as_view(), name='folder_list'),
]
