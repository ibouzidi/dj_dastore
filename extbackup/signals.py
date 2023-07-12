from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from account.views import convert_size
from extbackup.models import File
from log.models import Log
import datetime


@receiver(post_save, sender=File)
def receive_signal_file_post_save(sender, instance, created, **kwargs):
    if created:
        myreq = Log(
            user=f'{instance.user.email}',
            appli='Backup',
            action='CREATE',
            description=f'User: {instance.user.username}, '
                        f'Name: {instance.name}, '
                        f'Description: {instance.description}, '
                        f'Folder: {instance.folder}, '
                        f'Size: {convert_size(instance.size)[0]} '
                        f'{convert_size(instance.size)[1]}, '
                        f'Uploaded At: {instance.uploaded_at}',
            date_open=datetime.datetime.now().strftime('%Y-%m-%d')
        )
        myreq.save()


@receiver(pre_delete, sender=File)
def receive_signal_file_pre_delete(sender, instance, **kwargs):
    myreq = Log(
        user=f'{instance.user.email}',
        appli='Backup',
        action='DELETE',
        description=f'User: {instance.user.username}, '
             f'Name: {instance.name}, '
             f'Description: {instance.description}, '
             f'Folder: {instance.folder}, '
             f'Size: {convert_size(instance.size)[0]} '
             f'{convert_size(instance.size)[1]}, '
             f'Uploaded At: {instance.uploaded_at}',
        date_open=datetime.datetime.now().strftime('%Y-%m-%d')
    )
    myreq.save()