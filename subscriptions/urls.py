from django.urls import path
from . import views

app_name = "subscriptions"


urlpatterns = [
    path("plan/", views.SubListView.as_view(), name="SubListView"),
    path("create-session/", views.CreateCheckoutSession.as_view(), name="CreateCheckoutSession"),
    path('cancel/confirm/', views.CancelConfirmView.as_view(), name='CancelConfirmView'),
    path("success/", views.SuccessView.as_view(), name="SuccessView"),
    path("cancelled/", views.CancelView.as_view(), name="CancelView"),
    # path("cancel_subscription/", views.CancelSubscriptionView.as_view(), name="CancelSubscriptionView"),
    path("set_selected_plan/", views.set_selected_plan, name="set_selected_plan"),  # add this line
    # path("change-subscription/", views.ChangeSubscriptionView.as_view(), name="ChangeSubscriptionView"),
    path('account/billing/portal/', views.customer_portal,
         name='customer_portal'),
]