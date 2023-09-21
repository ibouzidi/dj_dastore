import datetime
import hashlib
import json
import secrets

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
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
from stripe.error import StripeError
from functools import cmp_to_key
from account.models import Account
from dj_dastore.decorator import user_is_active_subscriber

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class SubListView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.get_active_subscriptions or \
                    request.user.has_teams:
                messages.info(request,
                              "You're already subscribed! Thank you "
                              "for your continued support.")
                return redirect("account:account_profile")

        # Retrieve products and active prices
        products = Product.objects.all()
        plans = []
        enterprise_prices = []  # this will store multiple prices for Enterp

        for product in products:
            for price in Price.objects.filter(product=product, active=True):
                plan_data = {
                    "id": price.id,
                    "product": product,
                    "amount": price.unit_amount / 100,
                    "description": product.description,
                    "interval": price.recurring["interval"],
                    "metadata": product.metadata,
                    "storage_limit": price.metadata.get('storage_limit')
                }

                # Check if the product is an Customized product
                if product.name == "Customized":
                    enterprise_prices.append(plan_data)
                else:
                    plans.append(plan_data)

        if enterprise_prices:
            # if there are any Customized prices,
            # add just one instance to plans
            enterprise_data = enterprise_prices[0]
            enterprise_data["multi_prices"] = enterprise_prices
            plans.append(enterprise_data)

        # Custom sorting function
        def custom_sort_order(plan):
            order = {
                'Customized': 1,
                'Premium': 2,
                'Standard': 3
            }
            return order.get(plan['product'].name, 999)

        # Sort plans based on custom order
        plans.sort(key=custom_sort_order)

        context = {
            "plans": plans
        }
        print(plans)

        return render(request, "subscriptions/plan_list.html", context)


@csrf_exempt
@require_POST
def set_selected_plan(request):
    """
    Store the selected plan ID into Django's session.

    Expect a JSON object in the request body with this format:
    {
        "plan_id": "plan_id_here",
        "custom_storage": "price_id_here",
        "custom_price": "custom_price_here"
    }
    """
    # Parse the JSON request body
    try:
        data = json.loads(request.body)
        plan_id = data.get("plan_id")
        custom_storage_price_id = data.get("custom_storage")
        custom_price = data.get("custom_price")  # Extract the custom_price
        print("Received plan_id:", plan_id)
        print("Received custom_storage_price_id:", custom_storage_price_id)
        print("Received custom_price:", custom_price)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON request body"}, status=400)

    # Make sure the plan_id is valid
    if not Price.objects.filter(id=plan_id).exists():
        return JsonResponse({"error": "Invalid plan_id"}, status=400)

    # If there's a custom_storage_price_id, ensure it's a valid Price ID
    if custom_storage_price_id and not Price.objects.filter(
            id=custom_storage_price_id).exists():
        return JsonResponse({"error": "Invalid custom_storage price_id"},
                            status=400)

    print("Setting plan_id in session:", plan_id)
    # Store the plan_id and custom values into Django's session
    request.session["plan_id"] = custom_storage_price_id
    print("After setting, plan_id in session:", request.session.get("plan_id"))
    if custom_storage_price_id:
        request.session["custom_storage"] = custom_storage_price_id
    if custom_price:
        request.session[
            "custom_price"] = custom_price  # Store the custom price

    return JsonResponse({"status": "success"})


class CreateCheckoutSession(View):
    def get(self, request):
        user_id = request.session.get("user_id")
        price_id = request.session.get("plan_id")
        print("price_id")
        print(price_id)

        if not user_id or not price_id or request.user.is_authenticated:
            user_id = request.user.id
            price_id = request.session.get("plan_id")

        # Retrieve the user
        user = Account.objects.get(id=user_id)

        # Check if the user already has an active subscription
        if user.get_active_subscriptions:
            messages.error(request, 'You already have an active subscription.')
            return redirect("home")

        customer = Customer.objects.filter(subscriber=user).first()

        if not customer:
            customer_data = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user_id)})
            customer = Customer.sync_from_stripe_data(customer_data)
            customer.subscriber = user
            customer.save()
        print("price_id")
        print(price_id)
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[{  # Updated to 'line_items'
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=request.build_absolute_uri(
                reverse('subscriptions:SuccessView')),
            cancel_url=request.build_absolute_uri(
                reverse('subscriptions:CancelView')),
            # metadata={"user_id": user.id},
        )
        print("price_id")
        print(price_id)
        print("user checkout sessions")
        print(user)
        return redirect(session.url)


class SuccessView(View):
    def get(self, request):
        # Clean up the session and cookies after registration
        # request.session.pop('user_id', None)
        # request.session.pop('plan_id', None)
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
                    group = Group.objects.get(name='g_inactive_subscribers')
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


# class CancelSubscriptionView(View):
#     def get(self, request):
#         if len(request.user.get_active_subscriptions) > 0:
#             stripe.Subscription.modify(
#                 request.user.get_active_subscriptions[0].id,
#                 cancel_at_period_end=True,
#             )
#             # Move user to 'Inactive Subscribers' group
#             move_user_to_group(request.user, 'g_active_subscribers',
#                                'g_inactive_subscribers')
#
#             messages.success(request, "Subscription will be cancelled at"
#                                       " the end of the billing period")
#         return redirect("account:account_profile")

@user_is_active_subscriber
def customer_portal(request):
    # Authenticate your user.
    customer_id = request.user.customer.id

    # Generate a unique token based on user information.
    token = hashlib.sha256(
        f"{customer_id}{request.user.username}".encode()).hexdigest()

    # Store the token in the user's session for verification.

    # Create a session.
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=request.build_absolute_uri(
            reverse('account:account_billing')),
    )

    # Directly redirect the user to the validation endpoint.
    return redirect(session.url)


def validate_portal_access(request, token):
    # Retrieve the user's session token.
    stored_token = request.session.get('portal_access_token')

    if stored_token and token == stored_token:
        # Display the customer portal.
        return render(request, 'account/account_billing.html')

    # Redirect to an error page or show an error message.
    return render(request, 'account/account_billing.html')


@webhooks.handler("payment_intent.succeeded")
def payment_intent_succeeded_event_listener(event, **kwargs):
    invoice_id = event.data["object"]["invoice"]

    invoice = stripe.Invoice.retrieve(invoice_id)
    lines = invoice.get("lines", [])
    print("payment")
    if lines:
        for line in lines['data']:
            if line['type'] == 'subscription':
                customer = stripe.Customer.retrieve(invoice["customer"])
                user_id = customer.metadata.get("user_id")
                user = Account.objects.filter(id=user_id).first()
                print("user")
                print(user)
                if user:
                    user.is_active = True
                    # Retrieve the price (previously plan) and set the user's storage limit
                    plan_id = line['plan']['id']
                    print("plan_id")
                    print(plan_id)
                    price = get_object_or_404(Price, id=plan_id)
                    user.storage_limit = price.metadata[
                        "storage_limit"]  # Get storage_limit from Price's metadata
                    test = price.metadata["storage_limit"]
                    print("test metadata ")
                    print(test)
                    # Add the user to the 'Active Subscribers' group
                    group = Group.objects.get(name='g_active_subscribers')
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
        move_user_to_group(user, 'g_active_subscribers',
                           'g_inactive_subscribers')

    except Subscription.DoesNotExist:
        print("Subscription does not exist in the database")
    return
