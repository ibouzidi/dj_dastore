import uuid
from django.conf import settings
from django.db import models


class RoleChoices(models.TextChoices):
    LEADER = 'LEADER', 'Leader'
    MEMBER = 'MEMBER', 'Member'


class Team(models.Model):
    """
    A Team, with members.
    """
    team_name = models.CharField(max_length=100)
    team_id = models.CharField(max_length=15, unique=True, null=True)
    # subscription = models.ForeignKey(
    #     'djstripe.Subscription', null=True, blank=True,
    #     on_delete=models.SET_NULL,
    #     help_text="The team's Stripe Subscription object, if it exists"
    # )

    def is_leader(self, user):
        return self.memberships.filter(user=user,
                                       role=RoleChoices.LEADER).exists()

    def member_count(self):
        return self.memberships.count()

    def __str__(self):
        return self.team_name


class Membership(models.Model):
    """
    A user's team membership
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='membership')
    team = models.ForeignKey(Team, on_delete=models.CASCADE,
                             related_name='memberships')
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
    storage_limit = models.PositiveIntegerField(null=True, blank=True)

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations',
    )

    class InvitationStatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        CANCELLED_MEMBER = 'CANCELLED_MEMBER', 'Cancelled by Member'
        CANCELLED_LEADER = 'CANCELLED_LEADER', 'Cancelled by Leader'

    status = models.CharField(max_length=20,
                              choices=InvitationStatusChoices.choices,
                              default=InvitationStatusChoices.PENDING)
