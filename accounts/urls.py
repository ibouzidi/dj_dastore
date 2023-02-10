from django.urls import path

app_name = 'accounts'

from accounts.views import (
    register_view,
    login_view,
    logout_view,
    account_view,
    edit_account_view,
    crop_image
)

urlpatterns = [
    path('register/plan/<str:plan_name>/', register_view, name='register_with_plan'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('<user_id>/', account_view, name="account_profile"),
    path('edit/<user_id>/', edit_account_view, name="account_edit"),
    path('edit/<user_id>/cropImage/', crop_image, name="account_crop_image"),

]
