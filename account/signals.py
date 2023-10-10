from django.contrib.auth import user_logged_in, user_logged_out
from django.dispatch import receiver

from log.models import Log
import datetime
from django.http import HttpResponseRedirect
from django.conf import settings


@receiver(user_logged_in)
def receive_signal_accounts_login(sender, request, user, **kwargs):
    myreq = Log(
        user=f'{user.email}',
        appli='Accounts',
        action='LOGIN',
        description=f'Username: {user.username}, '
                     f'First name: {user.first_name}, '
                     f'Last name: {user.last_name}',
        date_open=datetime.datetime.now()
    )
    myreq.save()


@receiver(user_logged_out)
def receive_signal_accounts_logout(sender, request, user, **kwargs):
    if user:
        myreq = Log(
            user=f'{user.email}',
            appli='Accounts',
            action='LOGOUT',
            description=f'Username: {user.username}, '
                         f'First name: {user.first_name}, '
                         f'Last name: {user.last_name}',
            date_open=datetime.datetime.now()
        )
        myreq.save()