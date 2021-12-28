from typing import cast
from django.db import models, reset_queries
from django.conf import settings
from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.expressions import Case
from django.db.models.fields import NullBooleanField
from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser
from django.conf import settings
from django.db import models
import string

# Create your models here.

# class AuthManager(BaseUserManager):
#     # email password -> chek for existing user in table return that user
#     def create_user(self, email, password=None):        
#         if not email:
#             raise ValueError("enter email id ")
#         user = self.model(email=self.normalize_email(email));

#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     # fucntions: to create admin and staff
#     def create_superuser(self, email, password):
#         user = self.create_user(email, password=password)
#         user.staff = True
#         user.admin = True
#         user.save(using=self._db)
#         return user

#     def create_staffuser(self, email, password):
#         user = self.create_user(email, password=password)
#         user.staff = True
#         user.save(using=self._db)
#         return user 


# class Auth(AbstractUser):
#     email = models.CharField(verbose_name='Email Id', max_length=255, unique=True)
#     is_active = models.BooleanField(default=True)
#     admin = models.BooleanField(default=False)
#     staff = models.BooleanField(default=False)
    
#     objects = AuthManager()

#     # default: email and password
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = []
    
#     class Meta(AbstractUser.Meta):
#         swappable = 'AUTH_USER_MODEL'

#     def __str__(self):
#         return self.email

#     @property
#     def is_staff(self):
#         return self.staff
    
#     @property
#     def is_admin(self):
#         return self.admin







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

    casual=models.IntegerField()    # 8
    special=models.IntegerField()   # 10
    restricted=models.IntegerField()# 2
    medical=models.IntegerField()   # 0
    earned=models.IntegerField()    # 0
    

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
    casual=models.IntegerField()
    special=models.IntegerField()
    restricted=models.IntegerField()
    medical=models.IntegerField()
    earned=models.IntegerField()

    # reset to zero 



class Complaint(models.Model):
    device=models.ForeignKey('Devices', on_delete=models.CASCADE,default=None)
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
