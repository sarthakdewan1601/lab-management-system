from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Computers)
admin.site.register(Complaint)
admin.site.register(Lab)
admin.site.register(Staff)
admin.site.register(Technician)