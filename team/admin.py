from django.contrib import admin
from team.models import Team, Membership, Invitation


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
admin.site.register(Team, TeamAdmin)
admin.site.register(Membership, MembershipAdmin)
