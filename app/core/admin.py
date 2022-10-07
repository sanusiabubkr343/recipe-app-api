import imp
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.
from core import models


# class UserAdmin(BaseUserAdmin):
#     """Define the admin pages for users"""

#     order = ["id"]
#     list_display = ["email", "name"]


admin.site.register(models.User)
