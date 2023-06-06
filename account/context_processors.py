from django.conf import settings
from two_factor.utils import default_device


def avatar(request):
    profile_image_url = None
    if request.user.is_authenticated:
        profile_image = request.user.profile.profile_image
        if profile_image:
            profile_image_url = profile_image.url
    return {'avatar_url': profile_image_url or settings.DEFAULT_AVATAR_URL}


def two_factor(request):
    return {
        'default_device': default_device(request.user) if
        request.user.is_authenticated else None}
