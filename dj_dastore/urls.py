from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_view
from django.views.generic import RedirectView
from two_factor.urls import urlpatterns as tf_urls
import app.views
from account import views

from app.views import (
    home_screen_view
)

localized_patterns  = [
    # path('', HomeView.as_view(), name='HomeView'),
    path('set_language/', app.views.set_language, name='set_language'),
    path('contact/', app.views.contact_view, name='contact_view'),
    path("subscriptions/", include("subscriptions.urls")),
    path('backup/', include('extbackup.urls')),
    path('folder/', include('folder.urls')),
    path('log/', include('log.urls')),
    path('', home_screen_view, name='home'),
    path('admin_panel/', admin.site.urls),
    path('', include(tf_urls)),
    path('account/', include('account.urls')),
    path('account/team/', include('team.urls')),

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
    localized_patterns += static(settings.STATIC_URL,
                                 document_root=settings.STATIC_ROOT)
    localized_patterns += static(settings.MEDIA_URL,
                                 document_root=settings.MEDIA_ROOT)

handler403 = 'app.views.handle403'
handler404 = 'app.views.handle404'
handler500 = 'app.views.handle500'

urlpatterns = [
    path('', RedirectView.as_view(url='/en/'), name='root_redirect'),
    # path('set_language/', app.views.set_language, name='set_language'),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    re_path(r'^rosetta/', include('rosetta.urls')),

]

urlpatterns += i18n_patterns(*localized_patterns)