from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views


from app.views import (
    home_screen_view
)

urlpatterns = [
    path('backup/', include('extbackup.urls')),
    path('', home_screen_view, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    # Password reset links (ref: https://github.com/django/django/blob/master/django/contrib/auth/views.py)
    path('accounts/reset/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
