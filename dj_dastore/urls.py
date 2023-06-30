from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_view
from two_factor.urls import urlpatterns as tf_urls
import app.views
from account import views

from app.views import (
    home_screen_view
)

urlpatterns = [
    # path('', HomeView.as_view(), name='HomeView'),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    path("subscriptions/", include("subscriptions.urls")),
    path('backup/', include('extbackup.urls')),
    path('folder/', include('folder.urls')),
    path('', home_screen_view, name='home'),
    path('admin_panel/', admin.site.urls),
    path('', include(tf_urls)),
    path('account/', include('account.urls')),
    path('team/', include('team.urls')),

    # Password reset links (ref: https://github.com/django/django/blob/master/django/contrib/auth/views.py)
    # path('account/reset/', include('django.contrib.auth.urls')),

    path('password_reset/', auth_view.PasswordResetView.as_view(
        template_name='password_reset/password_reset.html'),
         name='password_reset'),
    path('password_change_done/', auth_view.PasswordResetDoneView.as_view(
        template_name='password_reset/password_change_done.html'),
         name='password_change_done'),
    path('password_reset_done/', auth_view.PasswordResetDoneView.as_view(
        template_name='password_reset/password_reset_done.html'),
         name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/',
         auth_view.PasswordResetConfirmView.as_view(
             template_name='password_reset/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password_reset_complete/',
         auth_view.PasswordResetCompleteView.as_view(
             template_name='password_reset/password_reset_complete.html'),
         name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

handler403 = 'app.views.handle403'
handler404 = 'app.views.handle404'
handler500 = 'app.views.handle500'
