from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import send_mail, BadHeaderError
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from two_factor.signals import user_verified
from two_factor.utils import default_device

from account.forms import RegistrationForm, AccountAuthenticationForm, \
    AccountUpdateForm
from account.models import Account
from .calc_storage_limit import calculate_storage_usage
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
import os
import cv2
import json
import base64
import requests
from django.core import files

from subscription_plan.models import SubscriptionPlan

TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"


def register_view(request, plan_name, *args, **kwargs):
    user = request.user
    if user.is_authenticated:
        messages.info(request,
                      "You are already authenticated as " + str(user.email))
        return redirect('subscription_plan:subscription_plan_index')

    try:
        # Retrieve the selected plan
        plan = SubscriptionPlan.objects.get(name__iexact=plan_name)
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, f'The plan with {plan_name} does not exit.')
        return redirect('subscription_plan:subscription_plan_index')
    if not plan_name:
        return redirect('subscription_plan:subscription_plan_index')
    context = {}
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create a new Account instance
            account = Account.objects.create_user(
                email=form.cleaned_data.get('email').lower(),
                password=form.cleaned_data.get('password1'),
                subscription_plan=plan,
                username=form.cleaned_data.get('username'),
            )
            account.save()

            # Authenticate and log in the new user
            user = authenticate(email=account.email,
                                password=form.cleaned_data.get('password1'))
            login(request, user)

            # Redirect to the desired page
            destination = kwargs.get("next")
            if destination:
                return redirect(destination)
            return redirect('home')
        else:
            context['registration_form'] = form
            context['plan'] = plan

    else:
        form = RegistrationForm()
        context['plan'] = plan
        context['registration_form'] = form
    return render(request, 'account/register.html', context)


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You are now logged out.")
    return redirect("home")


def login_view(request, *args, **kwargs):
    context = {}

    user = request.user
    if user.is_authenticated and user_verified(request):
        messages.info(request, "You are already logged in.")
        return redirect("home")

    destination = get_redirect_if_exists(request)
    print("destination: " + str(destination))

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
        form = AccountAuthenticationForm()

    context['login_form'] = form

    return render(request, "account/login.html", context)


def get_redirect_if_exists(request):
    redirect = None
    if request.GET:
        if request.GET.get("next"):
            redirect = str(request.GET.get("next"))
    return redirect

@login_required
def account_view(request):
    print("default_device(request.user)")
    print(default_device(request.user))
    context = {}
    try:
        account = request.user
    except:
        messages.error(request, "No user logged in.")
        return redirect("login")  # redirect to your login view

    context['id'] = account.id
    context['username'] = account.username
    context['first_name'] = account.first_name
    context['last_name'] = account.last_name
    context['phone'] = account.phone
    context['address'] = account.address
    context['number'] = account.number
    context['city'] = account.city
    context['zip'] = account.zip
    context['email'] = account.email
    context['profile_image'] = account.profile_image
    context['subscription_plan'] = account.subscription_plan

    context['is_self'] = True

    storage_used, storage_limit, storage_limit_unit, storage_limit_used \
        = calculate_storage_usage(account)
    # Store the values in the context dictionary
    context['storage_used'] = storage_used
    context['storage_limit'] = storage_limit
    context['storage_limit_unit'] = storage_limit_unit
    context['storage_used_unit'] = storage_limit_used

    context['default_device'] = default_device(
        request.user) if request.user.is_authenticated else None
    return render(request, "account/account.html", context)


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
def edit_account_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("account:login")
    user_id = kwargs.get("user_id")
    account = get_object_or_404(Account, pk=user_id)
    if account.pk != request.user.pk:
        messages.warning(request, "You cannot edit someone else's profile.")
        return redirect("account:account_profile")
    context = {}
    if request.POST:
        form = AccountUpdateForm(request.POST, request.FILES,
                                 instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request,
                             'Your account has be successfully updated.')
            return redirect("account:account_profile")
        else:
            form = AccountUpdateForm(request.POST, instance=request.user,
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
            }
        )
        context['form'] = form
    context[
        'DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request, "account/edit_account.html", context)


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
