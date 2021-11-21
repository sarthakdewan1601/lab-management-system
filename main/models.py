from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
# Create your models here.
class Staff(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=20, blank=False, null=False)
    name=models.CharField(max_length=100)
    mobile_number=models.IntegerField()
    email=models.EmailField()

    def __str__(self):
        return self.name


class Complaint(models.Model):
    computer=models.ForeignKey('Computers', on_delete=models.CASCADE)
    complaint=models.TextField(blank=False)
    created_at=models.DateTimeField(auto_now_add=True)
    isActive=models.BooleanField()

    def __str__(self):
        return self.complaint[0:30]
   
class Lab(models.Model):
    Lab_id = models.CharField(max_length=10)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.Lab_id
    

class Computers(models.Model):
    computer_id=models.CharField(max_length=20, blank=False, null=False)
    lab_id=models.ForeignKey(Lab, on_delete=models.CASCADE)
    floor_id=models.CharField(max_length=10,blank=False, null=False)
    #staff=models.ForeignKey(Staff ,on_delete=models.CASCADE)

    def __str__(self):
        return self.computer_id




