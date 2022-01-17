from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('email', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

# Register your models here.
admin.site.register(User, CustomUserAdmin)
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
