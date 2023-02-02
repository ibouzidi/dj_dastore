from django.db import models
from storages.backends.ftp import FTPStorage
from accounts.models import Account

# fs = FTPStorage()


class File(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='uploads/')


