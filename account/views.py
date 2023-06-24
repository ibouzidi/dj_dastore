from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import send_mail, BadHeaderError
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from two_factor.signals import user_verified
from two_factor.utils import default_device
from django.views import View
from account.forms import RegistrationForm, AccountAuthenticationForm, \
    AccountUpdateForm, AddMemberForm, AddTeamForm
from account.models import Account, Team, Membership, RoleChoices, Invitation
from dj_dastore.decorator import user_is_subscriber, user_is_company, \
    user_is_active_subscriber
from .calc_storage_limit import calculate_storage_usage
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
import os
import cv2
import json
import base64
import requests
from django.core import files
from djstripe.models import Plan, Invoice
from djstripe.models import Product, Price

TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"


class RegisterView(View):
    def get(self, request):
        form = RegistrationForm()
        plan_id = request.session.get("plan_id")
        print("enregistrement compte")
        print(plan_id)
        if not plan_id:
            messages.info(request, 'Please select a plan before '
                                   'registering.')
            return redirect("home")

        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            messages.error(request, 'The selected plan does not exist.')
            return redirect("home")

        # You can still check if the plan's product is active
        if not plan.product.active:
            messages.error(request, 'The selected plan is not currently '
                                    'available.')
            return redirect("home")

        return render(request, 'account/register.html',
                      {'form': form, 'plan': plan})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            account = Account.objects.create_user(
                email=form.cleaned_data.get('email').lower(),
                password=form.cleaned_data.get('password1'),
                username=form.cleaned_data.get('username'),
            )
            account.is_active = False
            account.plan_id = request.session.get("plan_id")
            account.save()
            request.session["user_id"] = account.id
            return redirect('subscriptions:CreateCheckoutSession')
        return render(request, 'account/register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You are now logged out.")
    return redirect("home")


def login_view(request, *args, **kwargs):
    context = {}

    user = request.user
    if request.user.is_authenticated and request.user.get_active_subscriptions:
        return redirect("home")

    destination = get_redirect_if_exists(request)

    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email, password=password)

            if user:
                login(request, user)
                messages.success(request, "You are now logged in.")
                if destination:
                    return redirect(destination)
                return redirect("home")
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = AccountAuthenticationForm()

    context['login_form'] = form

    return render(request, "account/login.html", context)


def get_redirect_if_exists(request):
    redirect = None
    if request.GET:
        if request.GET.get("next"):
            redirect = str(request.GET.get("next"))
    return redirect


def save_temp_profile_image_from_base64String(imageString, user):
    # TODO: ne sauvegarde pas temporaiement le fichier
    INCORRECT_PADDING_EXCEPTION = "Incorrect padding"
    try:
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)
        if not os.path.exists(f'{settings.TEMP}/{user.pk}'):
            os.mkdir(f'{settings.TEMP}/{user.pk}')
        url = os.path.join(f'{settings.TEMP}', str(user.pk),
                           TEMP_PROFILE_IMAGE_NAME)
        storage = FileSystemStorage(location=url)
        image = base64.b64decode(imageString)
        with storage.open('', 'wb+') as destination:
            destination.write(image)
            destination.close()
        return url
    except Exception as e:
        # workaround for an issue I found
        if str(e) == INCORRECT_PADDING_EXCEPTION:
            imageString += "=" * ((4 - len(imageString) % 4) % 4)
            return save_temp_profile_image_from_base64String(imageString, user)
    return None


@login_required
def crop_image(request, *args, **kwargs):
    payload = {}
    user = request.user
    if request.POST and user.is_authenticated:
        try:
            imageString = request.POST.get("image")
            url = save_temp_profile_image_from_base64String(imageString, user)
            img = cv2.imread(url)

            cropX = int(float(str(request.POST.get("cropX"))))
            cropY = int(float(str(request.POST.get("cropY"))))
            cropWidth = int(float(str(request.POST.get("cropWidth"))))
            cropHeight = int(float(str(request.POST.get("cropHeight"))))
            if cropX < 0:
                cropX = 0
            if cropY < 0:  # There is a bug with cropperjs. y can be negative.
                cropY = 0
            crop_img = img[cropY:cropY + cropHeight, cropX:cropX + cropWidth]

            cv2.imwrite(url, crop_img)

            # delete the old image
            user.profile_image.delete()

            # Save the cropped image to user model
            user.profile_image.save("profile_image.png",
                                    files.File(open(url, 'rb')))
            user.save()

            payload['result'] = "success"
            payload['cropped_profile_image'] = user.profile_image.url

            # delete temp file
            os.remove(url)

        except Exception as e:
            print("exception: " + str(e))
            payload['result'] = "error"
            payload['exception'] = str(e)
    return HttpResponse(json.dumps(payload), content_type="application/json")


@login_required
def account_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("account:login")
    user_id = request.user.pk
    account = get_object_or_404(Account, pk=user_id)
    if account.pk != request.user.pk:
        messages.warning(request, "You cannot edit someone else's profile.")
        return redirect("account:account_profile")
    context = {}
    if request.POST:
        form = AccountUpdateForm(request.POST, request.FILES,
                                 instance=request.user)
        if form.is_valid():
            print("VALID")
            form.save()
            messages.success(request,
                             'Your account has be successfully updated.')
            return redirect("account:account_profile")
        else:
            print("NON VALID")
            form = AccountUpdateForm(request.POST, instance=request.user,
                                     initial={
                                         "id": account.pk,
                                         "profile_image": account.profile_image,
                                     }
                                     )
            context['form'] = form
    else:
        form = AccountUpdateForm(
            initial={
                "id": account.pk,
                "email": account.email,
                "first_name": account.first_name,
                "last_name": account.last_name,
                "address": account.address,
                "phone": account.phone,
                "city": account.city,
                "zip": account.zip,
                "number": account.number,
                "username": account.username,
                "profile_image": account.profile_image,
            }, instance=request.user
        )
        context['form'] = form
    context[
        'DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE

    storage_used, storage_limit, storage_limit_unit, storage_limit_used \
        = calculate_storage_usage(account)
    # Store the values in the context dictionary
    context['storage_used'] = storage_used
    context['storage_limit'] = storage_limit
    context['storage_limit_unit'] = storage_limit_unit
    context['storage_used_unit'] = storage_limit_used

    return render(request, "account/account.html", context)


@login_required
def account_security(request, *args, **kwargs):
    context = {'default_device': default_device(
        request.user) if request.user.is_authenticated else None}

    return render(request, 'account/account_security.html', context)


@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeView(PasswordChangeView):
    # template_name = 'account/password_change.html'

    def clean_old_password(self):
        old_password = super().clean_old_password()
        print('Old password cleaned data:', old_password)
        return old_password

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.is_ajax():
            return JsonResponse({'result': 'success'}, status=200)
        else:
            return response

    def form_invalid(self, form):
        print('Form errors:', form.errors)
        response = super().form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response


@user_is_active_subscriber
def account_billing(request, *args, **kwargs):
    context = {}
    customer = request.user.customer
    if customer:
        invoices = Invoice.objects.filter(customer=customer)
        context['invoices'] = invoices

    return render(request, 'account/account_billing.html', context)


@user_is_company
def team_list(request, *args, **kwargs):
    context = {}
    # Retrieve all the teams of the current user
    user = request.user
    memberships = Membership.objects.filter(user=user)

    context['teams'] = []

    for membership in memberships:
        team = membership.team
        team_members = Membership.objects.filter(team=team).exclude(user=user)
        context['teams'].append({
            'team': team,
            'team_members': team_members
        })

    return render(request, 'account/teams/team_list.html', context)


@user_is_company
def create_team(request):
    if request.method == 'POST':
        form = AddTeamForm(request.POST)
        if form.is_valid():
            team_name = form.cleaned_data.get('team_name')
            team_id = form.cleaned_data.get('team_id')

            # Create a new team
            new_team = Team(team_name=team_name, team_id=team_id)

            # Retrieve the active subscription of the leader
            leader_subscriptions = request.user.get_active_subscriptions

            if leader_subscriptions:
                new_team.subscription = leader_subscriptions[0]

            # Save the new team instance
            new_team.save()

            # Create a new membership for the team leader
            Membership.objects.create(user=request.user, team=new_team, role=RoleChoices.LEADER)

            messages.success(request,
                             'Team has been successfully created and '
                             'leader\'s subscription assigned to the team.')
            return redirect('account:account_profile')
    else:
        form = AddTeamForm()
    return render(request, 'account/teams/create_team.html',
                  {'form': form})


@user_is_company
def team_detail(request, team_id):
    team = get_object_or_404(Team, team_id=team_id)
    if request.method == 'POST':
        form = AddTeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team has been successfully updated.')
            return redirect('account:team_detail', team_id=team_id)
    else:
        form = AddTeamForm(instance=team)

    # Get team members
    team_members = team.team_members.all()

    invitations = team.invitations.all()

    pending_invitations = invitations.filter(
        status=Invitation.InvitationStatusChoices.PENDING)
    # cancelled_invitations_member = invitations.filter(
    #     status=Invitation.InvitationStatusChoices.CANCELLED_MEMBER)
    # cancelled_invitations_leader = invitations.filter(
    #     status=Invitation.InvitationStatusChoices.CANCELLED_LEADER)
    # accepted_invitations = invitations.filter(
    #     status=Invitation.InvitationStatusChoices.ACCEPTED)

    return render(request, 'account/teams/detail_team.html', {
        'form': form,
        'team_members': team_members,
        'team': team,
        'pending_invitations': pending_invitations,
    })


@user_is_company
def cancel_invitation(request, code):
    invitation = get_object_or_404(Invitation, code=code)
    if request.user.is_team_leader and \
            invitation.status == Invitation.InvitationStatusChoices.PENDING:
        invitation.status = Invitation.InvitationStatusChoices.CANCELLED_LEADER
        invitation.save()
        messages.success(request, 'Invitation cancelled.')
    else:
        messages.error(request, 'You do not have permission to do that or '
                                'the invitation is not pending.')
    return redirect('account:team_detail', team_id=invitation.team.team_id)


@user_is_company
def send_invitation(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        selected_team_id = request.POST.get('team_id')

        team = Team.objects.filter(team_id=selected_team_id).first()
        membership = Membership.objects.filter(user=request.user, team=team,
                                               role=RoleChoices.LEADER).first()

        if membership:
            if membership.user.is_team_leader:
                limit_users = membership.user.limit_users()
                # Total members across all teams
                total_members_all_teams = \
                    membership.user.total_members_all_teams

                print("total_members_all_teams")
                print(total_members_all_teams)
                # Check if total members across all teams exceeds the limit
                if total_members_all_teams >= int(limit_users):
                    messages.error(request, 'The team is already at capacity.')
                    return render(request, 'account/account.html')

            existing_invitation = Invitation.objects.filter(
                email=email, team=team,
                status=Invitation.InvitationStatusChoices.ACCEPTED).first()

            if existing_invitation:
                messages.error(
                    request,
                    'An invitation to this email has already been sent.')
            else:
                # All checks pass, send invitation
                # Define the expiry date
                expiry_date = datetime.now() + timedelta(hours=24)
                # Create the invitation
                invitation = Invitation.objects.create(email=email, team=team,
                                                       expiry_date=expiry_date)
                signup_link = request.build_absolute_uri(reverse(
                    'account:guest_register', args=[invitation.code]))
                leader_email = membership.user.email
                send_mail(
                    'Invitation to join a Team',
                    f'You are invited by {leader_email} to join the team : '
                    f'{team.team_name}.'
                    f'Click here to accept the invitation: sign up here: '
                    f'{signup_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
                messages.success(request, 'Invitation sent.')
        else:
            messages.error(request, 'You are not a team leader.')
    return render(request, 'account/account.html')


class GuestRegisterView(View):
    def get(self, request, code):
        form = RegistrationForm()
        try:
            invitation = Invitation.objects.get(
                code=code, status=Invitation.InvitationStatusChoices.PENDING)
            if invitation.expiry_date < datetime.now():
                messages.error(request, 'This invitation has expired.')
                return redirect('home')
            request.session['invitation_id'] = invitation.id
            return render(request, 'account/guest_register.html',
                          {'form': form})
        except Invitation.DoesNotExist:
            messages.error(request, 'Invalid or expired invitation code.')
            return redirect('home')

    def post(self, request, code):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                invitation = Invitation.objects.get(
                    id=request.session['invitation_id'])

                leader_membership = Membership.objects.filter(
                    team=invitation.team, role=RoleChoices.LEADER).first()

                # Added this check
                if leader_membership.user.is_team_leader:
                    limit_users = leader_membership.user.limit_users()

                    # Check total members across all teams lead by the user
                    total_members_all_teams = leader_membership.user.total_members_all_teams

                    if total_members_all_teams >= int(limit_users):
                        messages.error(request,
                                       'The team is already at capacity.')
                        return redirect('account:login')

                leader_active_subscriptions = \
                    leader_membership.user.get_active_subscriptions

                if leader_active_subscriptions.exists():
                    leader_plan = leader_active_subscriptions[0].plan
                    storage_limit = leader_plan.product.metadata[
                        "storage_limit"]
                else:
                    storage_limit = 0

                # Create user account with specified storage limit
                account = Account.objects.create_user(
                    email=form.cleaned_data.get('email').lower(),
                    password=form.cleaned_data.get('password1'),
                    username=form.cleaned_data.get('username'),
                )
                # storage_limit is str class
                if isinstance(storage_limit, str):
                    try:
                        account.storage_limit = int(storage_limit)
                    except ValueError:
                        account.storage_limit = 0
                else:
                    account.storage_limit = 0
                account.is_active = True
                account.save()

                # Create membership and update invitation status
                Membership.objects.create(user=account, team=invitation.team,
                                          role=RoleChoices.MEMBER)
                invitation.status = Invitation.InvitationStatusChoices.ACCEPTED
                invitation.save()
                del request.session['invitation_id']

                # Update the total_members count of the team
                invitation.team.total_members += 1
                invitation.team.save()

                messages.success(request,
                                 'Registration and team joining successful.')
            except Invitation.DoesNotExist:
                messages.error(request, 'Problem in accepting the invitation.')
            return redirect('account:login')
        return render(request, 'account/guest_register.html', {'form': form})
