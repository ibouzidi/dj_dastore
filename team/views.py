from hashlib import sha256

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, timedelta
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from account.forms import RegistrationForm
from account.models import Account
from dj_dastore.decorator import user_is_company, user_is_active_subscriber, \
    user_is_only_team_member
from team.forms import AddTeamForm, InvitationForm
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

    remaining_invitations = 0
    if request.user.is_team_leader and request.user.is_company:
        remaining_invitations = int(request.user.limit_users()) - \
                                (request.user.total_members_all_teams +
                                 pending_invitations.count())

    form_inv = InvitationForm(initial={'team_id': team_id})

    context = {
        'form': form,
        'form_inv': form_inv,
        'team_members': team_members,
        'team': team,
        'pending_invitations': pending_invitations,
        'remaining_invitations': remaining_invitations,
    }

    return render(request, 'team/detail_team.html', context)


@method_decorator(user_is_only_team_member, name='dispatch')
class MembershipDetailView(View):
    def get(self, request):
        memberships = Membership.objects.filter(
            user=request.user)  # updated line
        context = {
            'memberships': memberships
        }
        return render(request, 'team/membership_detail.html', context)


@user_is_company
def fetch_leader_storage_limit(request):
    user = request.user
    response_data = {}

    # Check if the user is a leader
    if not user.is_team_leader:
        response_data['result'] = 'error'
        response_data['message'] = 'You are not a team leader.'
        return JsonResponse(response_data)

    # Check if the leader has a team
    if not user.has_teams:
        response_data['result'] = 'error'
        response_data['message'] = 'You do not have a team.'
        return JsonResponse(response_data)

    # Retrieve the active customer's storage limit
    active_subscriptions = user.get_active_subscriptions
    if active_subscriptions:
        storage_limit = user.storage_limit
        response_data['result'] = 'success'
        response_data['current_storage_limit'] = storage_limit
    else:
        response_data['result'] = 'error'
        response_data['message'] = 'No active subscription found.'

    return JsonResponse(response_data)


@method_decorator(user_is_company, name='dispatch')
class SendInvitation(View):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = Team.objects.filter(
            id=self.kwargs['team_id']).first()
        return context

    def post(self, request, *args, **kwargs):
        form = InvitationForm(request.POST)
        response_data = {}

        if form.is_valid():
            email = form.cleaned_data['email']
            storage_limit = form.cleaned_data['storage_limit']
            selected_team_id = form.cleaned_data['team_id']

            if storage_limit <= 0 or int(storage_limit) != storage_limit:
                response_data['result'] = 'error'
                response_data['message'] = 'Invalid storage limit.'
                return JsonResponse(response_data)

            team = Team.objects.filter(team_id=selected_team_id).first()
            membership = Membership.objects.filter(user=request.user,
                                                   team=team,
                                                   role=RoleChoices.LEADER).first()
            if membership:

                # Step 1: Fetch the Leader's Available Storage
                leader_storage_limit = membership.user.storage_limit
                print("leader_storage_limit", leader_storage_limit)
                # Step 2: Check for Sufficient Storage
                if storage_limit > leader_storage_limit:
                    response_data['result'] = 'error'
                    response_data[
                        'message'] = 'Insufficient storage to send this invitation.'
                    return JsonResponse(response_data)
                # Step 3: Deduct Storage
                membership.user.storage_limit -= storage_limit
                membership.user.save()

                limit_users = membership.user.limit_users()
                if limit_users is None:
                    limit_users = 0

                total_members_in_team = team.memberships.count()

                # Count the number of pending invitations
                total_pending_invitations = Invitation.objects.filter(
                    team=team,
                    status=Invitation.InvitationStatusChoices.PENDING
                ).count()

                if total_members_in_team + + total_pending_invitations >= int(
                        limit_users):
                    response_data['result'] = 'error'
                    response_data[
                        'message'] = 'The team is already at capacity, ' \
                                     'including pending invitations'
                    return JsonResponse(response_data)

                existing_invitation = Invitation.objects.filter(
                    email=email, team=team,
                    status__in=[Invitation.InvitationStatusChoices.PENDING,
                                Invitation.InvitationStatusChoices.ACCEPTED]).first()

                if existing_invitation:
                    response_data['result'] = 'error'
                    response_data[
                        'message'] = 'An invitation to this email has ' \
                                     'already been sent or accepted.'
                    return JsonResponse(response_data)

                # All checks pass, send invitation
                expiry_date = timezone.now() + timedelta(hours=24)
                invitation = Invitation.objects.create(email=email,
                                                       team=team,
                                                       expiry_date=expiry_date,
                                                       sender=request.user,
                                                       storage_limit=storage_limit
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

                return JsonResponse({
                    'result': 'success',
                    'message': 'Invitation sent',
                    'new_invitation': {
                        'email': invitation.email,
                        'status': invitation.status.capitalize(),
                        'code': invitation.code
                    }
                })

            else:
                response_data['result'] = 'error'
                response_data['message'] = 'You are not a team leader.'
                return JsonResponse(response_data)

        else:
            return JsonResponse(
                {'result': 'error', 'message': 'Invalid input'})


class InvitationLandingView(View):
    def get(self, request, code):
        try:
            invitation = Invitation.objects.get(
                code=code, status=Invitation.InvitationStatusChoices.PENDING)
            # Store the invitation ID in the session
            request.session['invitation_id'] = invitation.id
            return render(request, 'team/invitation_landing.html',
                          {'invitation': invitation})
        except Invitation.DoesNotExist:
            messages.error(request, 'Invalid or expired invitation code.')
            return redirect('home')

    def post(self, request, code):
        try:
            invitation_id = request.session.get('invitation_id')
            invitation = Invitation.objects.get(
                id=invitation_id,
                status=Invitation.InvitationStatusChoices.PENDING)
            if invitation.code != code:
                messages.error(request, 'Invalid session.')
                return redirect('home')
            return redirect('team:guest_register', code=code)
        except Invitation.DoesNotExist:
            messages.error(request, 'Invalid or expired invitation code.')
            return redirect('home')


class GuestRegisterView(View):

    def _get_invitation(self, code):
        try:
            return Invitation.objects.get(
                code=code,
                status=Invitation.InvitationStatusChoices.PENDING
            )
        except Invitation.DoesNotExist:
            return None

    def _is_email_matching_invitation(self, form_email, invitation):
        return form_email.lower() == invitation.email.lower()

    def _is_team_full(self, leader):
        limit_users = leader.limit_users()
        total_members_all_teams = leader.total_members_all_teams
        return total_members_all_teams >= int(limit_users)

    def get(self, request, code):
        form = RegistrationForm()
        invitation = self._get_invitation(code)

        if not invitation:
            messages.error(request, 'Invalid or expired invitation code.')
            return redirect('home')

        if invitation.expiry_date < timezone.now():
            messages.error(request, 'This invitation has expired.')
            return redirect('home')

        form = RegistrationForm(initial={'email': invitation.email})
        return render(request, 'team/guest_register.html', {'form': form})

    def post(self, request, code):
        form = RegistrationForm(request.POST)
        if not form.is_valid():
            return render(request, 'team/guest_register.html', {'form': form})

        invitation = self._get_invitation(code)
        if not invitation:
            messages.error(request, 'Problem in accepting the invitation.')
            return redirect('account:login')

        if not self._is_email_matching_invitation(
                form.cleaned_data.get('email'), invitation):
            messages.error(request, 'Email does not match the invitation.')
            return redirect('team:guest_register', code=code)

        leader_membership = Membership.objects.filter(
            team=invitation.team, role=RoleChoices.LEADER
        ).first()
        if not leader_membership:
            # This is a fallback in case a leader membership isn't found.
            messages.error(request, 'Team leader not found.')
            return redirect('account:login')

        if self._is_team_full(leader_membership.user):
            messages.error(request, 'The team is already at capacity.')
            return redirect('account:login')

        storage_limit = invitation.storage_limit if leader_membership.user.get_active_subscriptions.exists() else 0

        account = Account.objects.create_user(
            email=form.cleaned_data.get('email').lower(),
            password=form.cleaned_data.get('password1'),
            username=form.cleaned_data.get('username'),
        )
        account.storage_limit = storage_limit
        account.is_active = True
        account.save()
        # Create membership and update invitation status
        Membership.objects.create(user=account, team=invitation.team,
                                  role=RoleChoices.MEMBER)
        invitation.status = Invitation.InvitationStatusChoices.ACCEPTED
        invitation.save()
        del request.session['invitation_id']

        # Update the total_members count of the team
        invitation.team.save()

        messages.success(request, 'Registration and team joining successful.')
        return redirect('account:login')


@user_is_company
@transaction.atomic
def cancel_invitation(request, code):
    invitation = get_object_or_404(Invitation, code=code)
    if request.user.is_team_leader and \
            invitation.status == Invitation.InvitationStatusChoices.PENDING:

        deducted_storage_limit = invitation.storage_limit

        invitation.status = Invitation.InvitationStatusChoices.CANCELLED_LEADER
        invitation.save()

        initial_storage_limit = request.user.storage_limit + \
                                deducted_storage_limit

        request.user.storage_limit = initial_storage_limit
        request.user.save()

        return JsonResponse({
            'result': 'success',
            'message': 'Invitation cancelled.',
            'updated_storage_limit': initial_storage_limit
        })
    else:
        return JsonResponse({
            'result': 'error',
            'message': 'You do not have permission to do that or '
                       'the invitation is not pending.'
        })
