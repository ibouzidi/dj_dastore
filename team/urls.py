from django.urls import path
from . import views

app_name = 'team'

urlpatterns = [
    # Teams & Member Management
    path('send_invitation/', views.send_invitation, name='send_invitation'),
    path('', views.team_list, name='team_list'),
    path('create/', views.create_team, name='create_team'),
    path('<str:team_id>/detail/', views.team_detail, name='team_detail'),
    path('membership_detail/', views.MembershipDetailView.as_view(),
         name='membership_detail'),
    path('invitation/<uuid:code>/', views.InvitationLandingView.as_view(),
         name='invitation_landing'),
    path('guest_register/<uuid:code>/', views.GuestRegisterView.as_view(),
         name='guest_register'),
    path('cancel_invitation/<uuid:code>/', views.cancel_invitation,
         name='cancel_invitation'),
]
