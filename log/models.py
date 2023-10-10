from django.utils import timezone
from django.db import models
import datetime


class Log(models.Model):
    user = models.CharField(max_length=200)
    appli = models.CharField(max_length=64)
    action = models.CharField(max_length=20)
    description = models.TextField(max_length=8000)
    date_open = models.DateTimeField()

    def save(self, *args, **kwargs):
        # gestion si date pas définie, on prend la date actuelle
        if not self.date_open:
            self.date_open = datetime.datetime.now()
        print(datetime.datetime.now())
        super().save(*args, **kwargs)
