from functools import wraps
from django.core.exceptions import PermissionDenied


# Check if user is authenticated
def authenticateduser(user):
    if user.is_authenticated:
        return True
    raise PermissionDenied


# DEV SECTION
def dev(user):
    if user.is_authenticated and user.is_admin:
        return True
    raise PermissionDenied


def user_is_subscriber(user):
    if user.is_authenticated and user.get_active_subscriptions:
        return True
    elif user.is_authenticated and \
            "g_admin" in user.groups.values_list('name', flat=True):
        return True
    elif user.is_authenticated and \
            "g_dev" in user.groups.values_list('name', flat=True):
        return True
    raise PermissionDenied


# def user_is_company(user):
#     if user.is_authenticated and \
#             user.get_active_subscriptions and \
#             "g_company" in user.groups.values_list('name', flat=True):
#         return True
#     elif user.is_authenticated and \
#             "g_admin" in user.groups.values_list('name', flat=True):
#         return True
#     elif user.is_authenticated and \
#             "g_dev" in user.groups.values_list('name', flat=True):
#         return True
#     raise PermissionDenied


def user_is_active_subscriber(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        active_plan = user.get_active_plan
        if active_plan or user.has_teams:
            return view_func(request, *args, **kwargs)
        elif user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return _wrapped_view


def user_is_only_team_member(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        active_plan = user.get_active_plan
        member_of_any_team = user.has_teams
        if member_of_any_team and not active_plan:
            return view_func(request, *args, **kwargs)
        elif user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return _wrapped_view


def user_is_company(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        print("user")
        print("user")
        print(user)
        if user.is_company or user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return _wrapped_view
# def group_required(group_name):
#     def decorator(view_func):
#         def _wrapped_view(request, *args, **kwargs):
#             if request.user.is_authenticated and \
#                     group_name in \
#                     request.user.groups.values_list('name', flat=True):
#                 return view_func(request, *args, **kwargs)
#             else:
#                 raise PermissionDenied
#         return _wrapped_view
#     return decorator


# def email_matches_invitation(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         if request.method == 'POST':
#             form = RegistrationForm(request.POST)
#             if form.is_valid():
#                 provided_email = form.cleaned_data.get('email').lower()
#                 invitation_id = request.session.get('invitation_id')
#                 try:
#                     invitation = Invitation.objects.get(
#                         id=invitation_id,
#                         status=Invitation.InvitationStatusChoices.PENDING)
#                     if provided_email != invitation.email:
#                         return HttpResponseForbidden('The provided email '
#                                                      'does not match the '
#                                                      'invitation.')
#                 except Invitation.DoesNotExist:
#                     return HttpResponseForbidden('No valid invitation found '
#                                                  'for provided email.')
#         return view_func(request, *args, **kwargs)
#     return _wrapped_view