from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core import models


admin.site.register(models.User)
admin.site.register(models.Recipe)
admin.site.register(models.Tag)
