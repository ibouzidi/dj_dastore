from django.db import models


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    sub_title = models.CharField(blank=True, max_length=100)
    popular = models.BooleanField(default=0)
    storage_limit = models.PositiveIntegerField()
    price = models.FloatField(default=0)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name
