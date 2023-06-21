from django.urls import path
from . import views
app_name = 'account'

urlpatterns = [

    # Account General Management
    path('register/', views.RegisterView.as_view(), name='RegisterView'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.account_view, name="account_profile"),
    path('security/', views.account_security, name="account_security"),
    # path('edit/<user_id>/', edit_account_view, name="account_edit"),
    path('edit/cropImage/', views.crop_image, name="account_crop_image"),

    path('password_change/', views.CustomPasswordChangeView.as_view(),
         name='password_change'),

    # Subscriptions Management
    path('billing/', views.account_billing, name="account_billing"),

    # Teams & Memeber Management
    path('send_invitation/', views.send_invitation, name='send_invitation'),
    path('teams/', views.team_list, name='team_list'),
    path('teams/create_team/', views.create_team, name='create_team'),
    path('teams/<str:team_id>/detail/', views.team_detail, name='team_detail'),
    path('guest_register/<uuid:code>/', views.GuestRegisterView.as_view(),
         name='guest_register'),
    path('cancel_invitation/<uuid:code>/', views.cancel_invitation,
         name='cancel_invitation'),
]
