from django.db import models
from django.conf import settings


class Subscription(models.Model):
    """
    Subscription model

    Inherits: models.Model
    model that establishes relationship between customer and it's stripe id
    """
    status = models.CharField(max_length=200, default='trial')
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,)
    stripeCustomerId = models.CharField(max_length=255, default='')
    stripeSubscriptionId = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.user.username
