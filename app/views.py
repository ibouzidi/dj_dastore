from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import translation


def set_language(request):
    user_language = request.POST.get('language')
    next_url = request.POST.get('next', '/')  # Fallback to root if 'next' is not provided

    if user_language:
        translation.activate(user_language)
        request.session[translation.LANGUAGE_SESSION_KEY] = user_language
        request.session.modified = True

    return HttpResponseRedirect(next_url)


def home_screen_view(request):
    context = {}
    return render(request, "app/home.html", context)


def handle403(request, exception):
    messages.error(request, f'403 - You are not authorized to '
                            f'access to this web page')
    return render(request, 'app/error/403.html')


def handle404(request, exception):
    messages.error(request, f'404 - Are you lost?')
    return render(request, 'app/error/404.html')


def handle500(request):
    messages.error(request, f'500 - Oups, coffee break.')
    return render(request, 'app/error/500.html')
