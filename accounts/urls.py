from django.urls import path

app_name = 'accounts'

from accounts.views import (
    RegisterView,
    login_view,
    logout_view,
    account_view,
    edit_account_view,
    crop_image
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='RegisterView'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('<user_id>/', account_view, name="account_profile"),
    path('edit/<user_id>/', edit_account_view, name="account_edit"),
    path('edit/<user_id>/cropImage/', crop_image, name="account_crop_image"),


]
