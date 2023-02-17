from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from accounts.forms import RegistrationForm, AccountAuthenticationForm, \
    AccountUpdateForm
from accounts.models import Account
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
        return HttpResponse(
            "You are already authenticated as " + str(user.email))

    if not plan_name:
        return redirect('subscription_plan:subscription_plan_index')
    context = {}
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Retrieve the selected plan
            plan = SubscriptionPlan.objects.get(name__iexact=plan_name)

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

    else:
        form = RegistrationForm()
        context['registration_form'] = form
    return render(request, 'accounts/register.html', context)


def logout_view(request):
    logout(request)
    return redirect("home")


def login_view(request, *args, **kwargs):
    context = {}

    user = request.user
    if user.is_authenticated:
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
                if destination:
                    return redirect(destination)
                return redirect("home")

    else:
        form = AccountAuthenticationForm()

    context['login_form'] = form

    return render(request, "accounts/login.html", context)


def get_redirect_if_exists(request):
    redirect = None
    if request.GET:
        if request.GET.get("next"):
            redirect = str(request.GET.get("next"))
    return redirect


def calculate_storage_usage(account):
    # Calculate storage limit based on subscription plan
    if account.subscription_plan is not None:
        storage_limit = account.subscription_plan.storage_limit * 1024 ** 3
    else:
        storage_limit = 0
    # Determine the unit for storage limit and usage (GB or MB)
    if storage_limit >= 1073741824:
        storage_limit = round(storage_limit / 1073741824, 2)
        storage_limit_unit = "GB"
    else:
        storage_limit = round(storage_limit / 1048576, 2)
        storage_limit_unit = "MB"

    if account.storage_usage >= 1073741824:
        storage_used = round(account.storage_usage / 1073741824, 2)
        storage_used_unit = "GB"
    else:
        storage_used = round(account.storage_usage / 1048576, 2)
        storage_used_unit = "MB"

    # Return the calculated values
    return storage_used, storage_limit, storage_limit_unit, storage_used_unit


def account_view(request, *args, **kwargs):
    context = {}
    user_id = kwargs.get("user_id")
    try:
        account = Account.objects.get(pk=user_id)
    except:
        return HttpResponse("Something went wrong.")
    if account:
        context['id'] = account.id
        context['username'] = account.username
        context['email'] = account.email
        context['profile_image'] = account.profile_image

        is_self = True
        user = request.user
        if user.is_authenticated and user != account:
            is_self = False
        elif not user.is_authenticated:
            is_self = False
        context['is_self'] = is_self

        storage_used, storage_limit, storage_limit_unit, storage_used_unit \
            = calculate_storage_usage(account)
        # # Store the values in the context dictionary
        context['storage_used'] = storage_used
        context['storage_limit'] = storage_limit
        context['storage_limit_unit'] = storage_limit_unit
        context['storage_used_unit'] = storage_used_unit

        return render(request, "accounts/account.html", context)


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


def edit_account_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    user_id = kwargs.get("user_id")
    account = Account.objects.get(pk=user_id)
    if account.pk != request.user.pk:
        return HttpResponse("You cannot edit someone elses profile.")
    context = {}
    if request.POST:
        form = AccountUpdateForm(request.POST, request.FILES,
                                 instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("accounts:account_view", user_id=account.pk)
        else:
            form = AccountUpdateForm(request.POST, instance=request.user,
                                     initial={
                                         "id": account.pk,
                                         "email": account.email,
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
                "username": account.username,
                "profile_image": account.profile_image,
            }
        )
        context['form'] = form
    context[
        'DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request, "accounts/edit_account.html", context)
