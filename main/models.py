from typing import cast
from django.db import models, reset_queries
from django.conf import settings
from django.db.models.aggregates import Count
from django.db.models.base import Model
from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.expressions import Case
from django.db.models.fields import NullBooleanField
from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser
from django.conf import settings
from django.db import models
import string
from polymorphic.models import PolymorphicModel



class Agency(models.Model):
    agency = models.CharField(max_length = 200)

    def __str__(self):
        return self.agency
    
class Designation(models.Model):
    category=models.ForeignKey("Category",on_delete = CASCADE)
    designation =models.CharField(max_length=400)

    def __str__(self):
        return self.designation +" ("+  self.category.category+")"

class Category(models.Model):               # faculty, lab staff, office staff, student
    category =models.CharField(max_length=400)

    def __str__(self):
        return self.category
    

class Staff(models.Model):
    # staff_id = models.CharField(max_length=20, blank=False, null=False)
    name=models.CharField(max_length=100)
    mobile_number=models.IntegerField()
    email=models.EmailField()
    category=models.ForeignKey('Category',on_delete=CASCADE)
    designation=models.ForeignKey('Designation',on_delete=CASCADE)
    agency = models.ForeignKey('Agency',on_delete=CASCADE)
    
    def __str__(self):
        return self.name

    # function to count leaves pending


# done 

class TotalLeaves(models.Model):
    # admin access + isme ki saari leaves total
    LeaveName = models.CharField(max_length=100, blank=True)
    count = models.IntegerField(default=0)
    year = models.IntegerField(default=2021)

    def __str__(self):
        return self.LeaveName + "("+ str(self.year) + ")"


    # casual=models.IntegerField()    # 8
    # special=models.IntegerField()   # 10
    # restricted=models.IntegerField()# 2
    # medical=models.IntegerField()   # 0
    # earned=models.IntegerField()    # 0
    

# usne leave leli
class UserLeaveStatus(models.Model):
    staff=models.ForeignKey('Staff', on_delete=CASCADE, related_name='user')
    leave_type=models.CharField(max_length=255, )
    date_time=models.DateTimeField()    # jis din chahiye
    reason = models.TextField()
    substitute=models.ForeignKey('Staff', blank=None, on_delete=CASCADE, related_name='Substitute')
    substitute_reply = models.BooleanField(default=False)               # field -> substitute ka
    approval = models.BooleanField(default=False)                       # field -> admin ka

# 2 admin, adjustment
# adjustment sbse phle vo verify
# after verification -> admin 
# admin approve



class UserLeavesTaken(models.Model):
    # get object of staff after admin verification
    staff=models.ForeignKey('Staff',on_delete=CASCADE)
    # casual=models.IntegerField()
    # special=models.IntegerField()
    # restricted=models.IntegerField()
    # medical=models.IntegerField()
    # earned=models.IntegerField()
    leave_taken = models.ForeignKey('TotalLeaves',on_delete=CASCADE)
    count=models.IntegerField(default=0)



class Complaint(models.Model):
    device=models.ForeignKey('Devices', on_delete=models.CASCADE,default=None)
    complaint=models.TextField(blank=False)
    created_at=models.DateTimeField(auto_now_add=True)
    isActive=models.BooleanField(default=True)
    work_Done=models.TextField(max_length=1024,blank=True)
    who_resolved = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL)      # if is_active == false toh who_resolved mein vo person daal do

    def __str__(self):
        return self.complaint[0:30]
   
class Lab(models.Model):
    lab = models.CharField(max_length=20, blank=False)
    name = models.CharField(max_length=255, blank=True)
    floor = models.CharField(max_length=10,blank=False, null=False)
    staff = models.ForeignKey("Staff", on_delete=SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.lab
    

class CategoryOfDevice(models.Model):
    category = models.CharField(max_length=100, null=False)

    def __str__(self):
        return self.category

class Devices(models.Model):
    device_id = models.CharField(max_length=20, blank=False, null=False)
    name=models.ForeignKey("CategoryOfDevice",blank=False,null=False, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)

    def __str__(self):
        return self.device_id +" "+ "(" + self.lab.lab + ")"



# tech profile-> usne kitni complaints resolve kri uska count + which complaint
# leaves -> saare users -> profile-> leave count (casual leave: 8, special casual leve: 10, restricted leave: 2)


# email address se register
# email, password confirm password, mobile no, category(faculty, lab staff, office staff, student), designation , agency
# lab (system analys, lab sup, lab aasso, lab tech, lab attendant)
# student (phd, me)
# faulty (prof, assoc proff, assis proff)

# agency: lab/office (regular, adhoc, )



# sender (ek banda)
# reciever (either ek banda or a group-> desigination)
# active status
# time (jis din notification crate hui)
# text message
# type of notification

# leave, technician, time table change vala access

NOTIFICATION_FIELDS = [
    ('LEAVE', 'Leave'),
    ('TECH', 'Technician'),
    ('TTC', 'Time Table Change')
]

class Notification(models.Model):
    sender = models.ForeignKey(Staff, blank=False, on_delete=CASCADE)
    reciever = models.CharField(max_length=255, blank=False)
    isActive = models.BooleanField(default=True)
    time = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_FIELDS, default='LEAVE')

    def __str__(self) -> str:
        return str(self.time) + " " +  self.notification_type

    #  add count notifications function here


# tab -> click -> query -> display

# tech -> click -> query -> technician -> display

# lab tech -> filter from staff ? 

# 3 forms 
# -> leave regarding -> ek band vo dusre ko tag krega reciever fields -> user list 
# -> complaint -> group notify -> reciever -> designation list
# -> baad mein krte 