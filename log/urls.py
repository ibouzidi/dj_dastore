from django.urls import path
from . import views


app_name = 'log'

urlpatterns = [
    path('', views.dashboard, name='log_dashboard'),
    path('list/', views.log_list, name='log_list'),
    path('<int:pk>/', views.log_select, name='log_select'),
    path('list/export', views.log_export, name='log_export'),
    # path('delete/', log.log_delete, name='log_delete'),

]