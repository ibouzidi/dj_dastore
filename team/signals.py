import datetime
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from log.models import Log
from team.models import Team, Membership, Invitation


@receiver(post_save, sender=Membership)
def post_save_membership(sender, instance, created, **kwargs):
    if created:
        log = Log(
            user=instance.user.email,
            appli='Team',
            action='CREATE',
            description=f'Membership created. User: {instance.user.username}, '
                        f'Team: {instance.team.team_name}, '
                        f'Role: {instance.get_role_display()}',
            date_open=datetime.datetime.now().strftime('%Y-%m-%d')
        )
    else:
        log = Log(
            user=instance.user.email,
            appli='Team',
            action='UPDATE',
            description=f'Membership updated. User: {instance.user.username}, '
                        f'Team: {instance.team.team_name}, '
                        f'Role: {instance.get_role_display()}',
            date_open=datetime.datetime.now().strftime('%Y-%m-%d')
        )
    log.save()


@receiver(pre_delete, sender=Membership)
def pre_delete_membership(sender, instance, **kwargs):
    log = Log(
        user=instance.user.email,
        appli='Team',
        action='DELETE',
        description=f'Membership deleted. User: {instance.user.username}, '
                    f'Team: {instance.team.team_name}, '
                    f'Role: {instance.get_role_display()}',
        date_open=datetime.datetime.now().strftime('%Y-%m-%d')
    )
    log.save()


@receiver(post_save, sender=Invitation)
def post_save_invitation(sender, instance, created, **kwargs):
    if created:
        log = Log(
            user=instance.sender.email,
            appli='Team',
            action='CREATE',
            description=f'Invitation sent to {instance.email} '
                        f'for team {instance.team.team_name} '
                        f'by {instance.sender.username}',
            date_open=datetime.datetime.now().strftime('%Y-%m-%d')
        )
    else:
        log = Log(
            user=instance.sender.email,
            appli='Team',
            action='UPDATE',
            description=f'Invitation updated for {instance.email} '
                        f'for team {instance.team.team_name} '
                        f'by {instance.sender.username}',
            date_open=datetime.datetime.now().strftime('%Y-%m-%d')
        )
    log.save()


@receiver(pre_delete, sender=Invitation)
def pre_delete_invitation(sender, instance, **kwargs):
    log = Log(
        user=instance.sender.email,
        appli='Team',
        action='DELETE',
        description=f'Invitation for {instance.email} '
                    f'to team {instance.team.team_name} '
                    f'cancelled by {instance.sender.username}',
        date_open=datetime.datetime.now().strftime('%Y-%m-%d')
    )
    log.save()