from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import Account


class AccountAdmin(UserAdmin):
    ordering = ('-date_joined',)
    list_display = ('email', 'username', 'date_joined', 'last_login',
                    'is_admin', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username')
    readonly_fields = ('id', 'date_joined', 'last_login')

    # filter_horizontal = ('groups', 'user_permissions',)
    list_filter = ('is_active', 'is_staff', 'is_superuser',)
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('email',)
        }),
        ('Fundamental Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser',)
        }),
        ('Important Dates', {
            'fields': (('date_joined', 'last_login'),)
        }),
        ('Group Permissions', {
            'fields': ('groups', 'user_permissions',)
        }),
        ('Avatar', {
            'fields': ('profile_image',)
        }),
        ('Storage Usage', {
            'fields': ('storage_usage',)
        }),
        ('Subscription Plan', {
            'fields': ('subscription_plan',)
        }),
    )


admin.site.register(Account, AccountAdmin)
