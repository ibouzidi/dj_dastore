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
    add_member_to_team
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

    path('add_member/', add_member_to_team, name='add_member'),

]
