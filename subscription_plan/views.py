from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from subscription_plan.forms import SubscriptionPlanForm
from subscription_plan.models import SubscriptionPlan


class SubscriptionPlanListView(ListView):
    model = SubscriptionPlan
    ordering = ['price']
    template_name = 'subscription_plan/subscription_plan_index.html'


class SubscriptionPlanCreateView(CreateView):
    model = SubscriptionPlan
    template_name = 'subscription_plan/subscription_plan_form.html'
    form_class = SubscriptionPlanForm
    success_url = reverse_lazy('subscription_plan:subscription_plan_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Add any additional processing here, such as sending an email or
        # logging the action.
        return response


class SubscriptionPlanUpdateView(UpdateView):
    model = SubscriptionPlan
    template_name = 'subscription_plan/subscription_plan_form.html'
    form_class = SubscriptionPlanForm
    success_url = reverse_lazy('subscription_plan:subscription_plan_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Add any additional processing here, such as sending an email or
        # logging the action.
        return response


class SubscriptionPlanDeleteView(DeleteView):
    model = SubscriptionPlan
    success_url = reverse_lazy('subscription_plan:subscription_plan_list')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
