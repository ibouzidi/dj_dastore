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
    path('statistics/', views.account_storage_stat,
         name="account_storage_stat"),
    path('delete-account/', views.DeleteAccountView.as_view(),
         name='delete_account'),
    path('password_change/', views.CustomPasswordChangeView.as_view(),
         name='password_change'),

    # Subscriptions Management
    path('billing/', views.account_billing, name="account_billing"),
    path('stripe/portal/', views.customer_portal,
         name='customer_portal'),
]
