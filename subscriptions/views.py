import datetime
import json

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import View, TemplateView
from django.http.response import JsonResponse
from djstripe.models import Customer, Plan, Product, Price
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from djstripe import webhooks
from djstripe.models import Subscription, Invoice
from django.contrib import messages
import stripe
from django.contrib.auth.models import Group

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
                plan = {
                    "id": price.id,
                    "product": product,
                    "amount": price.unit_amount / 100,
                    "description": product.description,
                    "interval": price.recurring["interval"],
                    "metadata": product.metadata
                }
                plans.append(plan)

        context = {
            "plans": plans
        }
        return render(request, "subscriptions/plan_list.html", context)

@csrf_exempt
@require_POST
def set_selected_plan(request):
    """
    Store the selected plan ID into Django's session.

    Expect a JSON object in the request body with this format:
    {
        "plan_id": "plan_id_here"
    }
    """
    # Parse the JSON request body
    try:
        data = json.loads(request.body)
        plan_id = data.get("plan_id")
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON request body"}, status=400)

    # Make sure the plan_id is valid
    if not Plan.objects.filter(id=plan_id).exists():
        return JsonResponse({"error": "Invalid plan_id"}, status=400)

    # Store the plan_id into Django's session
    request.session["plan_id"] = plan_id

    return JsonResponse({"status": "success"})


class CreateCheckoutSession(View):
    def get(self, request):
        user_id = request.session.get("user_id")
        plan_id = request.session.get("plan_id")

        if not user_id or not plan_id or request.user.is_authenticated:
            user_id = request.user.id
            plan_id = request.session.get("plan_id")
        print("plan_id")
        print(plan_id)
        # Retrieve the plan
        user = Account.objects.get(id=user_id)

        # Check if the user already has an active subscription
        if user.get_active_subscriptions:
            messages.error(request, 'You already have an active subscription.')
            return redirect("home")  # Or wherever you want to redirect

        customer = Customer.objects.filter(subscriber=user).first()

        if not customer:
            customer_data = stripe.Customer.create(email=user.email)
            customer = Customer.sync_from_stripe_data(customer_data)
            customer.subscriber = user
            customer.save()

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
        # Clean up the session and cookies after registration
        request.session.pop('user_id', None)
        request.session.pop('plan_id', None)
        response = redirect("account:login")
        messages.success(request, "Subscription successful!")
        response.delete_cookie('selectedPlan')
        return response


class CancelView(View):
    def get(self, request):
        return redirect("subscriptions:CancelConfirmView")


class CancelConfirmView(View):
    def get(self, request):
        return render(request, 'subscriptions/sub_cancel_confirm.html')

    def post(self, request):
        if 'cancel' in request.POST:
            user_id = request.session.get("user_id")
            if user_id:
                try:
                    user = Account.objects.get(id=user_id)
                    group = Group.objects.get(name='G_INACTIVE_SUBSCRIBERS')
                    user.groups.add(group)
                    messages.error(request, "Subscription canceled")
                except Account.DoesNotExist:
                    messages.error(request, "The user does not exist.")
            else:
                messages.error(request, "Sorry but the session has expired.")

            # Clean up the session and cookies after registration
            request.session.pop('user_id', None)
            request.session.pop('plan_id', None)
            response = redirect("home")
            response.delete_cookie('selectedPlan')
            return response

        elif 'return_checkout' in request.POST:
            user_id = request.session.get("user_id")
            plan_id = request.session.get("plan_id")
            if user_id and plan_id:
                return redirect('subscriptions:CreateCheckoutSession')
            else:
                messages.error(request,
                               "Sorry but the session has expired.")
                return redirect("home")
        else:
            return redirect("home")


def move_user_to_group(user, old_group_name, new_group_name):
    from django.contrib.auth.models import Group

    try:
        old_group = Group.objects.get(name=old_group_name)
        new_group = Group.objects.get(name=new_group_name)
        user.groups.remove(old_group)
        user.groups.add(new_group)
    except Group.DoesNotExist:
        print(f"Group does not exist: {old_group_name} or {new_group_name}")


class CancelSubscriptionView(View):
    def get(self, request):
        if len(request.user.get_active_subscriptions) > 0:
            stripe.Subscription.modify(
                request.user.get_active_subscriptions[0].id,
                cancel_at_period_end=True,
            )
            # Move user to 'Inactive Subscribers' group
            move_user_to_group(request.user, 'G_ACTIVE_SUBSCRIBERS',
                               'G_INACTIVE_SUBSCRIBERS')

            messages.success(request, "Subscription will be cancelled at"
                                      " the end of the billing period")
        return redirect("account:account_profile")


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
                    user.storage_limit = plan.product.metadata["storage_limit"]
                    # Add the user to the 'Active Subscribers' group
                    group = Group.objects.get(name='G_ACTIVE_SUBSCRIBERS')
                    user.groups.add(group)
                    user.save()
    return


@webhooks.handler("customer.subscription.deleted")
def subscription_cancelled_event_listener(event, **kwargs):
    subscription_id = event.data["object"]["id"]
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        user = subscription.user
        print("subscription.user")
        print("subscription.user")
        print("subscription.user")
        print(user)
        subscription.canceled_at = timezone.now()
        subscription.status = "cancelled"
        subscription.save()

        # Move user to 'Inactive Subscribers' group
        move_user_to_group(user, 'G_ACTIVE_SUBSCRIBERS', 'inactive_ubscribers')

    except Subscription.DoesNotExist:
        print("Subscription does not exist in the database")
    return