from django.contrib import admin

# Register your models here.
from .models import Subscription

# registering subscription model to admin
admin.site.register(Subscription)
