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
    cancel_invitation
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='RegisterView'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profiles/', account_view, name="account_profile"),
    # path('edit/<user_id>/', edit_account_view, name="account_edit"),
    path('edit/cropImage/', crop_image, name="account_crop_image"),

    path('password_change/', CustomPasswordChangeView.as_view(),
         name='password_change'),

    # path('add_member/', add_member_to_team, name='add_member'),
    path('send_invitation/', send_invitation, name='send_invitation'),
    path('accept_invitation/<uuid:code>/', accept_invitation,
         name='accept_invitation'),
    path('create_team/', create_team, name='create_team'),
    path('team_detail/<str:team_id>/', team_detail, name='team_detail'),
    path('guest_register/<uuid:code>/', GuestRegisterView.as_view(),
         name='guest_register'),
    path('cancel_invitation/<uuid:code>/', cancel_invitation, name='cancel_invitation'),


]
