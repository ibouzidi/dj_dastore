from django.shortcuts import render
from subscription_plan.models import SubscriptionPlan


def home_screen_view(request):
	list_sub = SubscriptionPlan.objects.all().order_by('price')
	context = {'list_sub': list_sub}
	return render(request, "app/home.html", context)