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
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('<user_id>/', account_view, name="account_view"),
    path('<user_id>/edit/', edit_account_view, name="account_edit"),
    path('edit/<user_id>/cropImage/', crop_image, name="crop_image"),

]
