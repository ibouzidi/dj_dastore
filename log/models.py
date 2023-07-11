from django.db import models


class Log(models.Model):
    user = models.CharField(max_length=200)
    appli = models.CharField(max_length=64)
    action = models.CharField(max_length=20)
    description = models.TextField(max_length=8000)
    date_open = models.DateTimeField(auto_now=True)
