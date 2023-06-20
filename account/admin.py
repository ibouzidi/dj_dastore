from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import Account, Team, Membership, Invitation


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
        ('Storage', {
            'fields': ('storage_usage', 'storage_limit',)
        }),
        # ('Teams', {
        #     'fields': ('member_teams',)
        # }),

    )

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1
    can_delete = False

class TeamAdmin(admin.ModelAdmin):
    inlines = (MembershipInline,)
    list_display = ('team_name',)
    search_fields = ('team_name',)

class MembershipAdmin(admin.ModelAdmin):
    list_display = ('team', 'user', 'role',)
    search_fields = ('team__name', 'user__username')

class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'team', 'created_at', 'status',)
    search_fields = ('email', 'team__team_name', 'status',)

admin.site.register(Invitation, InvitationAdmin)


admin.site.register(Account, AccountAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Membership, MembershipAdmin)