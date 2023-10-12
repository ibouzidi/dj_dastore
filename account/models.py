from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from django.utils import timezone
import datetime
from djstripe.models import Customer, Subscription
from team.models import RoleChoices


class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, password=None,
                    subscription_plan=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')

        user = self.model(
            email=self.normalize_email(email).lower(),
            username=username,
            # subscription_plan=subscription_plan,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


def get_profile_image_filepath(self, filename):
    return 'profile_images/' + str(self.pk) + '/profile_image.png'


def get_default_profile_image():
    return "dastore/default_user_icon.png"


class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(verbose_name='date joined')

    def save(self, *args, **kwargs):
        # gestion si date pas définie, on prend la date actuelle
        if not self.date_joined:
            self.date_joined = datetime.datetime.now()
        super().save(*args, **kwargs)
    first_name = models.CharField(max_length=20, blank=True)
    last_name = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    number = models.CharField(max_length=32, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    zip = models.CharField(max_length=30, null=True, blank=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    profile_image = models.ImageField(max_length=255,
                                      upload_to=get_profile_image_filepath,
                                      null=True, blank=True,
                                      default=get_default_profile_image)
    storage_usage = models.PositiveBigIntegerField(default=0)
    storage_limit = models.BigIntegerField(default=0)
    plan_id = models.CharField(max_length=255, null=True, blank=True)
    request_counts = models.PositiveIntegerField(default=0)
    last_request_timestamp = models.DateTimeField(null=True, blank=True)
    disable_date = models.DateTimeField(null=True, blank=True)

    teams = models.ManyToManyField(
        'team.Team',  # updated to reference the 'team' app
        through='team.Membership',
        through_fields=('user', 'team'),
        related_name='account_memberships'  # updated related_name here
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = MyAccountManager()

    def __str__(self):
        return self.username

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_profile_image_filename(self):
        return str(self.profile_image)[str(self.profile_image).index(
            'profile_images/' + str(self.pk) + "/"):]

    @property
    def avatar_url(self):
        if self.profile_image:
            if settings.MEDIA_URL.startswith('/media/'):
                return self.profile_image.url
            else:
                return settings.MEDIA_URL + self.get_profile_image_filename()
        else:
            return settings.STATIC_URL + 'dastore/default_user_icon.png'

    # @property
    # def profile_image_url(self):
    #     if self.profile_image:
    #         return self.profile_image.url
    #     else:
    #         return 'dastore/default_user_icon.png'

    # For checking permissions. to keep it simple all admin have ALL permissons
    def has_perm(self, perm, obj=None):
        return self.is_admin

    # Does this user have permission to view this app
    def has_module_perms(self, app_label):
        return True

    def update_rate_limit(self):
        if self.last_request_timestamp is None or self.last_request_timestamp < timezone.now() - datetime.timedelta(
                seconds=30):
            self.request_counts = 1
            self.last_request_timestamp = timezone.now()
            self.save()
            return True
        elif self.request_counts < 2:
            self.request_counts += 1
            self.last_request_timestamp = timezone.now()
            self.save()
            return True
        else:
            return False

    @property
    def customer(self):
        try:
            return Customer.objects.get(subscriber=self)
        except Customer.DoesNotExist:
            return None

    @property
    def get_active_subscriptions(self):
        customer = self.customer
        return customer.active_subscriptions if customer else []

    @property
    def get_active_plan(self):
        customer = self.customer
        return customer.active_subscriptions[
            0].plan if customer and customer.active_subscriptions else None

    @property
    def is_team_leader(self):
        if hasattr(self, 'membership'):
            return self.membership.role == RoleChoices.LEADER.value
        return False

    @property
    def total_members_all_teams(self):
        if hasattr(self, 'membership') and self.is_team_leader:
            return self.membership.team.member_count()
        return 0

    @property
    def is_company(self):
        active_plan = self.get_active_plan
        if active_plan is not None and active_plan.product.name == 'Customized':
            print("true")
            return True
        else:
            print("false")
            return False

    def limit_users(self):
        active_subscriptions = self.get_active_subscriptions
        if active_subscriptions:
            plan = active_subscriptions[0].plan
            return plan.product.metadata["limit_users"]
        else:
            return 0  # Default limit_users

    @property
    def has_teams(self):
        return self.teams.exists()