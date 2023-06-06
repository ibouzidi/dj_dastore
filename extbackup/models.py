from audioop import reverse

from django.db import models

from folder.models import Folder
# from storages.backends.ftp import FTPStorage
from account.models import Account

# fs = FTPStorage()


class File(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True, blank=True)
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.CASCADE, related_name='files')
    size = models.PositiveIntegerField(default=0)
    file = models.FileField(upload_to='uploads/')
    content = models.JSONField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


