from django.urls import path
from . import views

app_name = 'subscription_plan'

urlpatterns = [
    path('', views.SubscriptionPlanListView.as_view(),
         name='subscription_plan_index'),
    path('subscription_plan/create/',
         views.SubscriptionPlanCreateView.as_view(),
         name='subscription_plan_create'),
    path('subscription_plan/<int:pk>/update/',
         views.SubscriptionPlanUpdateView.as_view(),
         name='subscription_plan_update'),
    path('subscription_plan/<int:pk>/delete/',
         views.SubscriptionPlanDeleteView.as_view(),
         name='subscription_plan_delete'),
]
