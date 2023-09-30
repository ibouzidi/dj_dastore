from django.urls import path
from . import views


app_name = 'footer'

urlpatterns = [
    path('terms_of_service', views.terms_of_service, name='Terms of Service'),
    path('about_us', views.about_us, name='About us'),
]
