from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Devices)
admin.site.register(Complaint)
admin.site.register(Lab)
admin.site.register(Staff)
admin.site.register(Agency)
admin.site.register(Designation)
admin.site.register(Category)
admin.site.register(Leaves)
admin.site.register(CategoryOfDevice)
# admin.site.register(Technician)