from django.contrib import admin
from extbackup.models import File


class FileAdmin(admin.ModelAdmin):
    list_display = ('file', 'user', 'upload_date')
    search_fields = ('file', 'user__username')
    list_filter = ('upload_date',)


# Register your models here.
admin.site.register(File)