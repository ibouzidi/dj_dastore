import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from django.utils import timezone
import datetime
from djstripe.models import Customer, Subscription


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


class Team(models.Model):
    """
    A Team, with members.
    """
    team_name = models.CharField(max_length=100)
    team_id = models.CharField(max_length=15, unique=True, null=True)
    total_members = models.IntegerField(default=0)
    member_accounts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Membership',
        through_fields=('team', 'user'),
        related_name='member_teams'
    )
    subscription = models.ForeignKey(
        'djstripe.Subscription', null=True, blank=True, on_delete=models.SET_NULL,
        help_text="The team's Stripe Subscription object, if it exists"
    )

    def is_leader(self, user):
        return self.memberships.filter(user=user,
                                       role=RoleChoices.LEADER).exists()

    def member_count(self):
        return Membership.objects.filter(team=self).count()

    def __str__(self):
        return self.team_name


class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(verbose_name='date joined',
                                       auto_now_add=True)
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
    storage_usage = models.BigIntegerField(default=0)
    storage_limit = models.BigIntegerField(default=0)
    plan_id = models.CharField(max_length=255, null=True, blank=True)
    request_counts = models.PositiveIntegerField(default=0)
    last_request_timestamp = models.DateTimeField(null=True, blank=True)

    teams = models.ManyToManyField(
        'Team',
        through='Membership',
        through_fields=('user', 'team'),
        related_name='memberships'  # added related_name here
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
        return self.user_teams.filter(role=RoleChoices.LEADER.value).exists()

    @property
    def is_company(self):
        active_plan = self.get_active_plan
        if active_plan and active_plan.product.name == 'Entreprise':
            return True
        else:
            return False

    def limit_users(self):
        active_subscriptions = self.get_active_subscriptions
        if active_subscriptions:
            plan = active_subscriptions[0].plan
            return plan.product.metadata["limit_users"]
        else:
            return 0  # Default limit_users

    @property
    def total_members_all_teams(self):
        memberships = self.user_teams.filter(role=RoleChoices.LEADER.value)
        total_members = sum(
            membership.team.member_count() for membership in memberships)
        return total_members


class RoleChoices(models.TextChoices):
    LEADER = 'LEADER', 'Leader'
    MEMBER = 'MEMBER', 'Member'


class Membership(models.Model):
    """
    A user's team membership
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='user_teams')
    team = models.ForeignKey(Team, on_delete=models.CASCADE,
                             related_name='team_members')
    role = models.CharField(max_length=100, choices=RoleChoices.choices)

    def __str__(self):
        return f'{self.user.username} - {self.team.team_name} - {self.get_role_display()}'
    # customer = models.ForeignKey(
    #     'djstripe.Customer', null=True, blank=True, on_delete=models.SET_NULL,
    #     help_text="The member's Stripe Customer object for this team, if it exists"
    # )


class Invitation(models.Model):
    email = models.EmailField()
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE,
                             related_name='invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    class InvitationStatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        CANCELLED_MEMBER = 'CANCELLED_MEMBER', 'Cancelled by Member'
        CANCELLED_LEADER = 'CANCELLED_LEADER', 'Cancelled by Leader'

    status = models.CharField(max_length=20,
                              choices=InvitationStatusChoices.choices,
                              default=InvitationStatusChoices.PENDING)
