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


from account.models import Account

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class SubListView(View):
    def get(self, request):
        if request.user.is_authenticated and \
                request.user.get_active_subscriptions:
            messages.info(request, "You're already subscribed! "
                          "Thank you for your continued support.")
            return redirect("account:account_profile")

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

        # Retrieve the plan
        plan = stripe.Plan.retrieve(plan_id)
        user = Account.objects.get(id=user_id)

        customer = Customer.objects.filter(subscriber=user).first()

        if not customer:
            customer_data = stripe.Customer.create(email=user.email)
            customer = Customer.sync_from_stripe_data(customer_data)
            customer.subscriber = user
            customer.save()

        # get the trial period
        trial_period_days = plan['trial_period_days']

        subscription_data = {
            "items": [
                {
                    "plan": plan_id,
                }
            ],
            "metadata": {
                "user_id": user.id,
            }
        }

        if trial_period_days:
            subscription_data.update({
                "trial_period_days": trial_period_days,
                "trial_settings": {
                    "end_behavior": {
                        "missing_payment_method": "cancel"
                    }
                }
            })

        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            payment_method_collection="if_required",
            subscription_data=subscription_data,
            success_url="http://localhost:8000/subscriptions/success/",
            cancel_url="http://localhost:8000/subscriptions/cancelled/",
        )
        return redirect(session.url)


class SuccessView(View):
    def get(self, request):
        messages.success(request, "Subscription successfull !")
        return redirect("account:login")


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
            return redirect("home")
        else:
            # Update the session with the free plan ID and
            # redirect to the CreateCheckoutSession view
            free_plan_id = 'price_1N1TMcJWztZpQABxdveM1RvB'
            request.session['plan_id'] = free_plan_id
            return redirect('subscriptions:CreateCheckoutSession')


@webhooks.handler("payment_intent.succeeded")
def payment_intent_succeeded_event_listener(event, **kwargs):
    invoice_id = event.data["object"]["invoice"]

    invoice = stripe.Invoice.retrieve(invoice_id)
    lines = invoice.get("lines", [])

    if lines:
        for line in lines['data']:
            if line['type'] == 'subscription':
                user_id = line["metadata"].get("user_id", None)
                user = Account.objects.filter(id=user_id).first()
                if user:
                    user.is_active = True
                    # Retrieve the plan and set the user's storage limit
                    plan_id = line['plan']['id']
                    plan = get_object_or_404(Plan, id=plan_id)
                    # plan = stripe.Plan.retrieve(plan_id)
                    print("plan")
                    print(plan)
                    print("plan.metadata")
                    print(plan.product.metadata["storage_limit"])
                    user.storage_limit = plan.product.metadata["storage_limit"]
                    user.save()
    return
