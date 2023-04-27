from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import View, TemplateView
from django.http.response import JsonResponse
from djstripe.models import Customer, Plan, Product, Price
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from djstripe import webhooks
from djstripe.models import Subscription
from django.contrib import messages
import stripe


from accounts.models import Account

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class SubListView(View):
    def get(self, request):
        if request.user.is_authenticated and \
                request.user.get_active_subscriptions:
            return redirect("accounts:account_profile",
                            user_id=request.user.id)

        # Retrieve products and active prices
        products = Product.objects.all()
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
        return render(request, "subscriptions/plan_list.html", context)


class CreateCheckoutSession(View):
    def get(self, request):
        user_id = request.session.get("user_id")
        plan_id = request.session.get("plan_id")

        if not user_id and not plan_id and request.user.is_authenticated:
            user_id = request.user.id
            plan_id = request.COOKIES.get("selectedPlan")

        user = Account.objects.get(id=user_id)

        customer = Customer.objects.filter(subscriber=user).first()

        if not customer:
            customer_data = stripe.Customer.create(email=user.email)
            customer = Customer.sync_from_stripe_data(customer_data)
            customer.subscriber = user
            customer.save()

        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            subscription_data={
                "items": [
                    {
                        "plan": plan_id,
                    }
                ],
                "metadata": {
                    "user_id": user.id,
                },
            },
            success_url="http://localhost:8000/subscriptions/success/",
            cancel_url="http://localhost:8000/subscriptions/cancelled/",
        )
        return redirect(session.url)


class SuccessView(View):
    def get(self, request):
        messages.success(request, "Subscription successfull !")
        return redirect("accounts:login")


class CancelView(View):
    def get(self, request):
        return redirect("subscriptions:CancelConfirmView")


class CancelConfirmView(View):
    def get(self, request):
        return render(request, 'subscriptions/sub_cancel_confirm.html')

    def post(self, request):
        user_id = request.session.get("user_id")
        user = Account.objects.get(id=user_id)
        customer, _ = Customer.objects.get_or_create(subscriber=user)

        if 'cancel' in request.POST:
            # Cancel the subscription
            messages.error(request, "Subscription canceled!")
            user.delete()  # Delete the user or disable the account as needed
            return redirect("HomeView")
        elif 'free_plan' in request.POST:
            # Switch to trial plan
            trial_plan_id = 'price_1N1TMcJWztZpQABxdveM1RvB'
            user.plan_id = trial_plan_id
            user.save()

            # Create a subscription with the free plan
            stripe_subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[
                    {
                        "plan": trial_plan_id,
                    }
                ],
            )
            # Save the subscription in your database
            subscription = Subscription.sync_from_stripe_data(
                stripe_subscription)
            subscription.customer = customer
            subscription.save()
            user.is_active = True
            user.save()

            messages.success(request, "You have successfully switched to the "
                                      "trial plan.")
            return redirect("HomeView")


class TrialPlanView(View):
    def get(self, request):
        user_id = request.session.get("user_id")
        print("user_id")
        print(user_id)
        user = Account.objects.get(id=user_id)
        print("customer before")

        # Create a Stripe customer if it doesn't exist
        customer = Customer.objects.filter(subscriber=user).first()
        print("customer")
        print(customer)
        if not customer:
            customer_data = stripe.Customer.create(email=user.email)
            customer = Customer.sync_from_stripe_data(customer_data)
            customer.subscriber = user
            customer.save()

        print("customer after")
        print(customer)
        # Create a subscription with the free plan
        stripe_subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[
                {
                    "plan": user.plan_id,
                }
            ],
        )

        # Save the subscription in your database
        subscription = Subscription.sync_from_stripe_data(stripe_subscription)
        subscription.customer = customer
        subscription.save()
        user.is_active = True
        user.save()
        messages.success(request, "You have successfully subscribed to "
                                  "the trial plan.")

        return redirect("HomeView")


@webhooks.handler("payment_intent.succeeded")
def payment_intent_succeeded_event_listener(event, **kwargs):
    invoice_id = event.data["object"]["invoice"]

    invoice = stripe.Invoice.retrieve(invoice_id)
    lines = invoice.get("lines", [])

    if lines:
        user_id = lines["data"][0]["metadata"].get("user_id", None)
        user = Account.objects.filter(id=user_id).first()
        if user:
            user.is_active = True
            user.save()
    return
