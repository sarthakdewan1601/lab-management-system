from typing import cast
from django.db import models, reset_queries
from django.conf import settings
from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.expressions import Case
# Create your models here.

class Agency(models.Model):
    agency = models.CharField(max_length = 200)
    
class Designation(models.Model):
    designation =models.CharField(max_length=400)

class Category(models.Model):
    category =models.CharField(max_length=400)


    
class Leaves(models.Model):
    staff_id=models.ForeignKey('Staff',on_delete=CASCADE)
    casual=models.IntegerField()
    special=models.IntegerField()
    restricted=models.IntegerField()
    medical=models.IntegerField()
    earned=models.IntegerField()

class Staff(models.Model):
    staff_id = models.CharField(max_length=20, blank=False, null=False)
    name=models.CharField(max_length=100)
    mobile_number=models.IntegerField()
    email=models.EmailField()
    category=models.ForeignKey('Category',on_delete=CASCADE)
    designation=models.ForeignKey('Designation',on_delete=CASCADE)
    agency = models.ForeignKey('Agency',on_delete=CASCADE)
    
    def __str__(self):
        return self.name

    # function to count leaves pending


class Complaint(models.Model):
    device=models.ForeignKey('Devices', on_delete=models.CASCADE)
    complaint=models.TextField(blank=False)
    created_at=models.DateTimeField(auto_now_add=True)
    isActive=models.BooleanField()
    work_Done=models.TextField(max_length=1024,blank=True)
    who_resolved = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL)      # if is_active == false toh who_resolved mein vo person daal do

    def __str__(self):
        return self.complaint[0:30]
   
class Lab(models.Model):
    lab = models.CharField(max_length=20, blank=False)
    name = models.CharField(max_length=255, blank=True)
    floor = models.CharField(max_length=10,blank=False, null=False)
    
    def __str__(self):
        return self.lab
    

class CategoryOfDevice(models.Model):
    category = models.CharField(max_length=100, null=False)

class Devices(models.Model):
    device_id = models.CharField(max_length=20, blank=False, null=False)
    name=models.ForeignKey("CategoryOfDevice",blank=False,null=False, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)

    def __str__(self):
        return self.device_id



# tech profile-> usne kitni complaints resolve kri uska count + which complaint
# leaves -> saare users -> profile-> leave count (casual leave: 8, special casual leve: 10, restricted leave: 2)