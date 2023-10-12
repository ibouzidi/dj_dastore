import datetime
import hashlib
import json
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import View, TemplateView
from django.http.response import JsonResponse
from djstripe.models import Customer, Plan, Product, Price
from djstripe import webhooks
from djstripe.models import Subscription, Invoice
from django.contrib import messages
import stripe
from django.contrib.auth.models import Group
from account.models import Account
from dj_dastore.decorator import user_is_active_subscriber
from team.models import RoleChoices, Team

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
        # print(plans)

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
        custom_price = data.get("custom_price")
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON request body"}, status=400)

    # Validate plan_id
    if not Price.objects.filter(id=plan_id).exists():
        return JsonResponse({"error": "Invalid plan_id"}, status=400)

    # Validate custom_storage_price_id if provided
    if custom_storage_price_id and not Price.objects.filter(id=custom_storage_price_id).exists():
        return JsonResponse({"error": "Invalid custom_storage price_id"}, status=400)

    # Store the plan_id in the session by default
    request.session["plan_id"] = plan_id

    # If there's a custom_storage_price_id, store it in the session, overwriting the plan_id
    if custom_storage_price_id:
        request.session["plan_id"] = custom_storage_price_id
        request.session["custom_storage"] = custom_storage_price_id

    # Store the custom price in the session if provided
    if custom_price:
        request.session["custom_price"] = custom_price

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
        user.groups.remove(old_group)
    except Group.DoesNotExist:
        print(f"Old group does not exist: {old_group_name}")

    try:
        new_group = Group.objects.get(name=new_group_name)
        user.groups.add(new_group)
    except Group.DoesNotExist:
        print(f"New group does not exist: {new_group_name}")


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


# def validate_portal_access(request, token):
#     # Retrieve the user's session token.
#     stored_token = request.session.get('portal_access_token')
#
#     if stored_token and token == stored_token:
#         # Display the customer portal.
#         return render(request, 'account/account_billing.html')
#
#     # Redirect to an error page or show an error message.
#     return render(request, 'account/account_billing.html')


def manage_user_status_and_group(user, is_active, target_group_name,
                                 source_group_name=None):
    print(f"Managing user {user.id}...")
    user.is_active = is_active
    user.save()
    print(f"User active status set to {is_active}")

    target_group = Group.objects.get(name=target_group_name)
    source_group = Group.objects.get(name=source_group_name) if source_group_name else None

    # Remove from source group if present
    if source_group:
        if user.groups.filter(name=source_group_name).exists():
            print(f"Removing user from {source_group_name}")
            user.groups.remove(source_group)
        else:
            print(f"User not in {source_group_name}")

    # Add to target group if not already present
    if not user.groups.filter(name=target_group_name).exists():
        print(f"Adding user to {target_group_name}")
        user.groups.add(target_group)
    else:
        print(f"User already in {target_group_name}")

    print(f"User groups: {user.groups.all()}")


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
                    # Retrieve the price (previously plan)
                    # and set the user's storage limit
                    plan_id = line['plan']['id']
                    print("plan_id")
                    print(plan_id)
                    price = get_object_or_404(Price, id=plan_id)
                    # Get storage_limit from Price's metadata
                    user.storage_limit = int(price.metadata[
                                                 "storage_limit"])
                    test = price.metadata["storage_limit"]
                    print("test metadata ")
                    print(test)
                    # Add the user to the 'Active Subscribers' group
                    manage_user_status_and_group(user, True,
                                                 'g_active_subscribers',
                                                 'g_inactive_subscribers')

    return


@webhooks.handler("customer.subscription.updated")
def subscription_updated_event_listener(event, **kwargs):
    # Retrieve subscription and customer details from the event object
    subscription_data = event.data["object"]
    customer_id = subscription_data["customer"]

    # Retrieve the Stripe customer
    customer = stripe.Customer.retrieve(customer_id)

    # Retrieve the user ID from the customer's metadata
    user_id = customer.metadata.get("user_id")

    # Fetch the corresponding user from your database
    user_account = Account.objects.filter(id=user_id).first()

    if user_account:
        # Update the Account object's plan_id and storage_limit
        # based on the new subscription details
        new_plan_id = subscription_data["items"]["data"][0]["price"]["id"]
        user_account.plan_id = new_plan_id

        # Assuming you have price metadata that contains the new storage limit
        new_storage_limit = stripe.Price.retrieve(new_plan_id).metadata.get(
            "storage_limit")
        if new_storage_limit:
            user_account.storage_limit = int(new_storage_limit)

        # # Reactivate the user account
        # Move user to 'Active Subscribers' group
        manage_user_status_and_group(user_account, True,
                                     'g_active_subscribers',
                                     'g_inactive_subscribers')

        print(f"Subscription updated for user: {user_account.username}")

        # If the user is a team leader, also activate the team members
        if user_account.is_team_leader:
            leader_teams = Team.objects.filter(
                memberships__user=user_account,
                memberships__role=RoleChoices.LEADER.value)

            for team in leader_teams:
                team_members = Account.objects.filter(
                    teams=team).exclude(id=user_account.id)

                for member in team_members:
                    # Move team members to 'Active Subscribers' group
                    manage_user_status_and_group(member, True,
                                                 'g_active_team_member',
                                                 'g_inactive_team_member')
                    print(f"Subscription also reactivated "
                          f"for team member: {member.username}")

    else:
        print("No corresponding user found in the database.")


@webhooks.handler("customer.subscription.deleted")
def subscription_cancelled_event_listener(event, **kwargs):
    # Retrieve customer and subscription ID
    subscription_id = event.data["object"]["id"]
    customer_id = event.data["object"]["customer"]

    # Retrieve the Stripe customer
    customer = stripe.Customer.retrieve(customer_id)

    # Retrieve the user ID from the customer's metadata
    user_id = customer.metadata.get("user_id")

    try:
        # Fetch corresponding user based on metadata's user_id
        user_account = Account.objects.get(id=user_id)

        if user_account:
            # Move leader to 'Inactive Subscribers' group
            manage_user_status_and_group(user_account, False,
                                         'g_inactive_subscribers',
                                         'g_active_subscribers')
            print(f"Subscription cancelled for user "
                  f"(Leader): {user_account.username}")

            # If the user is a team leader, handle the team members
            if user_account.is_team_leader:
                # Retrieve all teams the user is leader of through
                # the Membership model
                leader_teams = Team.objects.filter(
                    memberships__user=user_account,
                    memberships__role=RoleChoices.LEADER.value)

                for team in leader_teams:
                    # Retrieve all team members
                    team_members = Account.objects.filter(
                        teams=team).exclude(id=user_account.id)

                    # Loop through team members and set each
                    # to inactive and move to the inactive group
                    for member in team_members:
                        manage_user_status_and_group(member, False,
                                                     'g_inactive_team_member',
                                                     'g_active_team_member')
                        print(f"Subscription also cancelled "
                              f"for team member: {member.username}")

        else:
            print("No corresponding user found in the database.")

    except ObjectDoesNotExist:
        print("No corresponding user found in the database.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
# @webhooks.handler("customer.subscription.deleted")
# def subscription_cancelled_event_listener(event, **kwargs):
#     # Retrieve customer and subscription ID
#     subscription_id = event.data["object"]["id"]
#     customer_id = event.data["object"]["customer"]
#
#     # Retrieve the Stripe customer
#     customer = stripe.Customer.retrieve(customer_id)
#
#     # Retrieve the user ID from the customer's metadata
#     user_id = customer.metadata.get("user_id")
#
#     try:
#         # Fetch corresponding user based on metadata's user_id
#         user_account = Account.objects.filter(id=user_id).first()
#
#         if user_account:
#             # Update your own Subscription model here if needed
#             # For now, just demonstrating how to set the user's status to inactive
#
#             user_account.is_active = False  # Setting to inactive as an example
#             user_account.save()
#
#             # Move user to 'Inactive Subscribers' group
#             move_user_to_group(user_account, 'g_active_subscribers',
#                                'g_inactive_subscribers')
#
#             print(f"Subscription cancelled for user: {user_account.username}")
#         else:
#             print("No corresponding user found in the database.")
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")


# @webhooks.handler("customer.subscription.updated")
# def subscription_updated_event_listener(event, **kwargs):
#     # Retrieve subscription and customer details from the event object
#     subscription_data = event.data["object"]
#     customer_id = subscription_data["customer"]
#
#     # Retrieve the Stripe customer
#     customer = stripe.Customer.retrieve(customer_id)
#
#     # Retrieve the user ID from the customer's metadata
#     user_id = customer.metadata.get("user_id")
#
#     # Fetch the corresponding user from your database
#     user_account = Account.objects.filter(id=user_id).first()
#
#     if user_account:
#         # Update the Account object's plan_id and storage_limit based on the new subscription details
#         new_plan_id = subscription_data["items"]["data"][0]["price"]["id"]
#         user_account.plan_id = new_plan_id
#         # Assuming you have price metadata that contains the new storage limit
#         new_storage_limit = stripe.Price.retrieve(new_plan_id).metadata.get(
#             "storage_limit")
#         if new_storage_limit:
#             user_account.storage_limit = int(new_storage_limit)
#         user_account.save()
#
#         print(f"Subscription updated for user: {user_account.username}")
#     else:
#         print("No corresponding user found in the database.")


@webhooks.handler_all
def handle_all(event, **kwargs):
    print(f"Received event: {event.type}")
