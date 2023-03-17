from django.core.exceptions import PermissionDenied


# Check if user is authenticated
def authenticateduser(user):
    if user.is_authenticated:
        return True
    raise PermissionDenied


# DEV SECTION
def dev(user):
    if user.is_authenticated and "GG_APP-DEV" \
            in user.groups.values_list('name', flat=True):
        return True
    raise PermissionDenied
