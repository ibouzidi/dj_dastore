from hashlib import sha256

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, timedelta
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from account.forms import RegistrationForm
from account.models import Account
from dj_dastore.decorator import user_is_company, user_is_active_subscriber, \
    user_is_only_team_member
from team.forms import AddTeamForm
from team.models import Membership, Team, Invitation, RoleChoices


@user_is_company
def team_list(request, *args, **kwargs):
    context = {}
    user = request.user
    if hasattr(user, 'membership'):
        team = user.membership.team
        context = {
            'team': team,
        }
    return render(request, 'team/team_list.html', context)


@user_is_company
def create_team(request):
    if hasattr(request.user, 'membership'):
        messages.error(request, 'You can only create one team.')
        return redirect('team:team_list')
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
            Membership.objects.create(user=request.user, team=new_team,
                                      role=RoleChoices.LEADER)

            messages.success(request,
                             'Team has been successfully created.')
            return redirect('team:team_list')
    else:
        form = AddTeamForm()
    return render(request, 'team/create_team.html',
                  {'form': form})


@user_is_company
def team_detail(request, team_id):
    team = get_object_or_404(Team, team_id=team_id)

    if request.method == 'POST':
        form = AddTeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team has been successfully updated.')
            return redirect('team:team_detail', team_id=team_id)
    else:
        form = AddTeamForm(instance=team)

    team_members = team.memberships.all()  # updated line
    invitations = team.invitations.all()
    pending_invitations = invitations.filter(
        status=Invitation.InvitationStatusChoices.PENDING)

    context = {
        'form': form,
        'team_members': team_members,
        'team': team,
        'pending_invitations': pending_invitations,
    }

    return render(request, 'team/detail_team.html', context)


@method_decorator(user_is_only_team_member, name='dispatch')
class MembershipDetailView(View):
    def get(self, request):
        membership = Membership.objects.get(user=request.user)  # updated line
        context = {
            'membership': membership
        }
        return render(request, 'team/membership_detail.html', context)


@user_is_company
def send_invitation(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        selected_team_id = request.POST.get('team_id')

        team = Team.objects.filter(team_id=selected_team_id).first()
        print("team")
        print("team")
        print(team)
        membership = Membership.objects.filter(user=request.user, team=team,
                                               role=RoleChoices.LEADER).first()
        print("membership")
        print("membership")
        print(membership)
        if membership:
            print("yes if membership")
            if membership.user.is_team_leader:
                limit_users = membership.user.limit_users()
                # Total members across all team
                total_members_all_teams = \
                    membership.user.total_members_all_teams

                print("total_members_all_teams")
                print(total_members_all_teams)
                # Check if total members across all team exceeds the limit
                if total_members_all_teams >= int(limit_users):
                    messages.error(request, 'The team is already at capacity.')
                    return redirect('team:team_detail', team_id=team.team_id)

            existing_invitation = Invitation.objects.filter(
                email=email, team=team,
                status__in=[Invitation.InvitationStatusChoices.PENDING,
                            Invitation.InvitationStatusChoices.ACCEPTED]).first()
            if existing_invitation:
                messages.error(request,
                               'An invitation to this email has already '
                               'been sent or accepted.')
                return redirect('team:team_detail', team_id=team.team_id)
            else:
                # All checks pass, send invitation
                # Define the expiry date
                expiry_date = datetime.now() + timedelta(hours=24)
                # Create the invitation
                invitation = Invitation.objects.create(email=email,
                                                       team=team,
                                                       expiry_date=expiry_date,
                                                       sender=request.user
                                                       )
                signup_link = request.build_absolute_uri(reverse(
                    'team:invitation_landing', args=[invitation.code]))
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
                return redirect('team:team_detail', team_id=team.team_id)
        else:
            messages.error(request, 'You are not a team leader.')
    return render(request, 'account/account.html')


class InvitationLandingView(View):
    def get(self, request, code):
        try:
            invitation = Invitation.objects.get(code=code, status=Invitation.InvitationStatusChoices.PENDING)
            # Store the invitation ID in the session
            request.session['invitation_id'] = invitation.id
            return render(request, 'team/invitation_landing.html', {'invitation': invitation})
        except Invitation.DoesNotExist:
            messages.error(request, 'Invalid or expired invitation code.')
            return redirect('home')

    def post(self, request, code):
        try:
            invitation_id = request.session.get('invitation_id')
            invitation = Invitation.objects.get(id=invitation_id, status=Invitation.InvitationStatusChoices.PENDING)
            if invitation.code != code:
                messages.error(request, 'Invalid session.')
                return redirect('home')
            return redirect('team:guest_register', code=code)
        except Invitation.DoesNotExist:
            messages.error(request, 'Invalid or expired invitation code.')
            return redirect('home')


class GuestRegisterView(View):
    def get(self, request, code):
        form = RegistrationForm()
        try:
            invitation_id = request.session.get('invitation_id')
            invitation = Invitation.objects.get(id=invitation_id, code=code,
                                                status=Invitation.InvitationStatusChoices.PENDING)
            if invitation.expiry_date < datetime.now():
                messages.error(request, 'This invitation has expired.')
                return redirect('home')
            form = RegistrationForm(initial={'email': invitation.email})
            return render(request, 'team/guest_register.html', {'form': form})
        except Invitation.DoesNotExist:
            messages.error(request, 'Invalid or expired invitation code.')
            return redirect('home')

    def post(self, request, code):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                invitation = Invitation.objects.get(
                    code=code,
                    status=Invitation.InvitationStatusChoices.PENDING)

                # Ensure the email matches the invitation
                if form.cleaned_data.get('email').lower() != invitation.email:
                    messages.error(request,
                                   'Email does not match the invitation.')
                    return redirect('team:guest_register', code=code)

                leader_membership = Membership.objects.filter(
                    team=invitation.team, role=RoleChoices.LEADER).first()

                # Added this check
                if leader_membership.user.is_team_leader:
                    limit_users = leader_membership.user.limit_users()

                    # Check total members across all team lead by the user
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
        return render(request, 'team/guest_register.html', {'form': form})


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
    return redirect('team:team_detail', team_id=invitation.team.team_id)
