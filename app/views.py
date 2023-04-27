from django.shortcuts import render, redirect
from subscription_plan.models import SubscriptionPlan
from django.contrib import messages
from djstripe.models import Plan
from djstripe.models import Product, Price
from django.views.generic import View


class HomeView(View):
    def get(self, request):
        if request.user.is_authenticated and request.user.get_active_subscriptions:
            return redirect("accounts:account_profile", user_id=request.user.id)

        # Retrieve products and active prices
        products = Product.objects.all()
        print("products")
        print(products)
        plans = []
        for product in products:
            for price in Price.objects.filter(product=product, active=True):
                description = product.description.split(".")
                dict_ = {}
                for index, phrase in enumerate(description):
                    dict_[f"phrase_{index + 1}"] = phrase.strip() + "."
                plan = {
                    "id": price.id,
                    "product": product,
                    "amount": price.unit_amount / 100,
                    "description": dict_,
                    "interval": price.recurring["interval"],
                    "metadata": product.metadata
                }
                plans.append(plan)

        context = {
            "plans": plans
        }
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
