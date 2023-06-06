from django.shortcuts import render, redirect
from django.contrib import messages
from djstripe.models import Plan
from djstripe.models import Product, Price
from django.views.generic import View


def home_screen_view(request):
    list_sub = SubscriptionPlan.objects.all().order_by('price')
    context = {'list_sub': list_sub}
    return render(request, "app/home.html", context)


def handle403(request, exception):
    messages.error(request, f'403 - You are not authorized to '
                            f'access to this web page')
    return render(request, 'app/error/403.html')


def handle404(request, exception):
    messages.error(request, f'404 - Are you lost?')
    return render(request, 'app/error/404.html')


def handle500(request):
    messages.error(request, f'500 - Oups, coffee break.')
    return render(request, 'app/error/500.html')
