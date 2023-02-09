import jsonfield as jsonfield
from django.db import models
# from storages.backends.ftp import FTPStorage
from accounts.models import Account

# fs = FTPStorage()


class SupportedExtension(models.Model):
    extension = models.CharField(max_length=10)

    def __str__(self):
        return self.extension


class File(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, null=True, blank=True)
    size = models.PositiveIntegerField(default=0)
    file = models.FileField(upload_to='uploads/')
    # existingPath = models.CharField(unique=True, max_length=100, null=True)
    # eof = models.BooleanField()
    content = jsonfield.JSONField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # def save(self, *args, **kwargs):
    #     self.size = self.file.size
    #     super().save(*args, **kwargs)


