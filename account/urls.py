from django.urls import path

app_name = 'account'

from account.views import (
    RegisterView,
    login_view,
    logout_view,
    account_view,
    # edit_account_view,
    crop_image,
    CustomPasswordChangeView,
    # add_member_to_team,
    send_invitation,
    accept_invitation,
    create_team,
    team_detail,
    GuestRegisterView,
    cancel_invitation,
account_security,
account_billing,
team_list
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='RegisterView'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', account_view, name="account_profile"),
    path('security/', account_security, name="account_security"),
    path('billing/', account_billing, name="account_billing"),
    # path('edit/<user_id>/', edit_account_view, name="account_edit"),
    path('edit/cropImage/', crop_image, name="account_crop_image"),

    path('password_change/', CustomPasswordChangeView.as_view(),
         name='password_change'),

    # path('add_member/', add_member_to_team, name='add_member'),
    path('send_invitation/', send_invitation, name='send_invitation'),
    path('accept_invitation/<uuid:code>/', accept_invitation,
         name='accept_invitation'),
    path('teams/', team_list, name='team_list'),
    path('teams/create_team/', create_team, name='create_team'),
    path('teams/<str:team_id>/detail/', team_detail, name='team_detail'),
    path('guest_register/<uuid:code>/', GuestRegisterView.as_view(),
         name='guest_register'),
    path('cancel_invitation/<uuid:code>/', cancel_invitation, name='cancel_invitation'),


]
