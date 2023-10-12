import datetime
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from folder.models import Folder
from log.models import Log


@receiver(post_save, sender=Folder)
def receive_signal_folder_post_save(sender, instance, created, **kwargs):
    if created:
        myreq = Log(
            user=f'{instance.user.email}',
            appli='Folder',
            action='CREATE',
            description=f'Name: {instance.name}, Parent: {instance.parent}',
            date_open=datetime.datetime.now()
        )
        myreq.save()


@receiver(post_delete, sender=Folder)
def receive_signal_folder_post_delete(sender, instance, **kwargs):
    myreq = Log(
        user=f'{instance.user.email}',
        appli='Folder',
        action='DELETE',
        description=f'Name: {instance.name}, Parent: {instance.parent}',
        date_open=datetime.datetime.now()
    )
    myreq.save()
