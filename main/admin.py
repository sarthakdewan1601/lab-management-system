from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import *


class CurrentTypeLeavesInline(admin.TabularInline):
    model = CurrentTypeLeaves

class YearLeavesAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields':['publishDate'], }), ]
    inlines = [CurrentTypeLeavesInline]


# Register your models here.
admin.site.register(Devices)
admin.site.register(Complaint)
admin.site.register(Lab)
admin.site.register(Staff)
admin.site.register(Agency)
admin.site.register(Designation)
admin.site.register(Category)
admin.site.register(TotalLeaves)
admin.site.register(UserLeavesTaken)
admin.site.register(UserLeaveStatus)
admin.site.register(CategoryOfDevice)
admin.site.register(Notification)
# admin.site.register(YearLeaves)
# admin.site.register(CurrentTypeLeaves)
admin.site.register(YearLeaves, YearLeavesAdmin)
