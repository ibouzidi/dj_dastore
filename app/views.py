from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils import translation

from app.forms import ContactForm


# def set_language(request):
#     lang_code = request.GET.get('lang', 'en')  # default to English if no language is specified
#     translation.activate(lang_code)
#     request.session[translation.LANGUAGE_SESSION_KEY] = lang_code
#
#     next = request.GET.get('next', '/')
#     response = HttpResponseRedirect(next)
#
#     return response


def home_screen_view(request):
    context = {}
    return render(request, "app/home.html", context)


def contact_view(request):
    initial_data = {}
    if request.user.is_authenticated:
        initial_data = {
            'fname': request.user.first_name,
            'lname': request.user.last_name,
            'email': request.user.email,
        }
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Get form data
            fname = form.cleaned_data['fname']
            lname = form.cleaned_data['lname']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            context = {
                'fname': fname,
                'lname': lname,
                'message': message,
            }
            email_html_message = render_to_string('app/email_template.html',
                                                  context)
            msg = EmailMessage(subject, email_html_message, 'from@example.com',
                               [settings.EMAIL_HOST_USER], headers={'Reply-To': email})

            msg.content_subtype = "html"
            msg.send()
            # Redirect or show a success message
            messages.success(request, 'Email sent successfully')
            return redirect("contact_view")
    else:
        form = ContactForm(initial=initial_data)

    return render(request, 'app/contact.html', {'form': form})


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
