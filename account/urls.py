from django.urls import path

app_name = 'account'

from account.views import (
    register_view,
    login_view,
    logout_view,
    account_view,
    edit_account_view,
    crop_image,
    CustomPasswordChangeView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='RegisterView'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profiles/', account_view, name="account_profile"),
    path('edit/<user_id>/', edit_account_view, name="account_edit"),
    path('edit/<user_id>/cropImage/', crop_image, name="account_crop_image"),

    path('password_change/', CustomPasswordChangeView.as_view(),
         name='password_change'),

]
