from calendar import month
from email.headerregistry import Group
from typing import BinaryIO
from xml.dom import ValidationErr
from django import forms
from django.db import models
from django.db.models import fields
from django.forms.fields import ChoiceField
from .models import *
from django.contrib.auth.forms import  AuthenticationForm, UserCreationForm, UserChangeForm
from django.contrib.auth.password_validation import validate_password

# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.conf import settings
import datetime
from django.forms import ModelForm
from datetime import date

User = get_user_model()

# class ComplaintResolveFrom(forms.Form):
#     WorkDone=forms.Textarea(widget=forms.Textarea(attrs={'placeholder': 'Enter Workdone'}))

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ['email',]

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['email']


class ComplaintForm(forms.Form):
    complaint=forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter complaint'}))

class NewComputerForm(forms.ModelForm):
    # device_id = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Device ID'}))
    # device_name = forms.ChoiceField(widget=forms.TextInput(attrs={'placeholder': 'Enter Device Name'}))
    # description = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter description of the device'}))
    class Meta:
        model = Devices
        fields = ['device_id','name','description']

class AddCourseForm(forms.ModelForm):

    class Meta:
        model = FacultyCourse
        fields = ['faculty','course']
    def __init__(self,*args, **kwargs):
        # print(faculty)
        super().__init__(*args, **kwargs)
        current_date = datetime.datetime.now()
        year=int(current_date.strftime("%Y"))
        month=int(current_date.strftime("%m"))
        sem=""
        if int(month)<=6:
            sem="EVEN"
        else:
            sem="ODD"

        self.fields['course'].queryset = Course.objects.filter(course_year=year,semester_type=sem)

class AddGroupForm(forms.ModelForm):

    class Meta:
        model = FacultyGroups
        fields = ['faculty','groups']
    def __init__(self,*args, **kwargs):
        # print(faculty)
        super().__init__(*args, **kwargs)
        current_date = datetime.datetime.now()
        year=int(current_date.strftime("%Y"))
        month=int(current_date.strftime("%m"))
        sem=""
        if int(month)<=6:
            sem="EVEN"
        else:
            sem="ODD"

        self.fields['groups'].queryset = Groups.objects.filter(group_year=year,semester_type=sem)

class AddGroupCourseForm(forms.ModelForm):
    class Meta:
        model = GroupCourse
        fields = ['faculty',"course","group"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = FacultyCourse.objects.none()
        self.fields['group'].queryset = FacultyGroups.objects.none()


        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['course'].queryset = FacultyCourse.objects.filter(faculty_id=faculty_id)
                self.fields['group'].queryset = FacultyGroups.objects.filter(faculty_id=faculty_id)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            self.fields['course'].queryset = FacultyCourse.objects.filter(faculty_id=self.instance.faculty)
            self.fields['group'].queryset = FacultyGroups.objects.filter(faculty_id=self.instance.faculty)

class EditProfileForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder':'Full Name'}))
    mobile_number = forms.IntegerField(required=True, widget=forms.TextInput(attrs={'placeholder':'Mobile Number'}))


class SignupForm(UserCreationForm):
    name=forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder':'Full Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder':'Email'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}), validators=[validate_password])
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    mobile_number=forms.IntegerField(required=True, widget=forms.TextInput(attrs={'placeholder':'Mobile Number'}))

        
    class Meta:
        model = User
        fields = ("email", "password1", "password2", "name", "mobile_number")
        



class AddNewLeave(forms.ModelForm):
    class Meta:
        model = TotalLeaves
        fields = '__all__'


# class ComplaintNotification(forms.Form):
#     sender=forms.CharField(settings.AUTH_USER_MODEL)
#     receiver=forms.CharField(widget=forms.CharField(attrs={'placeholder': 'Enter complaint'}))



# class LeaveNotification(forms.Form):
#     sender = forms.CharField(settings.AUTH_USER_MODEL)
#     reciever = 

# class LeaveForm(forms.ModelForm):

#     year = datetime.datetime.now().year
#     currentYearLeaves = TotalLeaves.objects.filter(year=year).all()
#     CHOICES=[]
#     i=0
#     for leave in currentYearLeaves:
#         # print('aaaa')
#         print(leave.LeaveName)
#         tup=()
#         tup+=(i,)
#         tup+=(leave.LeaveName,)
#         CHOICES.append(tup)
#         i+=1
#     type_of_leave=forms.ChoiceField(choices=CHOICES)
#     class Meta:
#         model = UserLeaveStatus
#         # fields = ("staff", "leavetype",  "date", "reason", "substitute")
#         fields = ("staff", "type_of_leave", "date_time", "reason", "substitute")

# class EditProfileForm(ModelForm):
#         class Meta:
#             model = User
#             fields = (
#                  'email',
#                  'first_name',
#                  'last_name'
#                 )
# class ProfileForm(ModelForm):
#          class Meta:
#             model = Staff
#             fields = ('name','mobile_number','email', 'category', 'designation', 'agency') #Note that we didn't mention user field here.



    
class AddClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['faculty',"faculty_group_course","day","starttime","tools_used"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty_group_course'].queryset = GroupCourse.objects.none()

        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['faculty_group_course'].queryset = GroupCourse.objects.filter(faculty_id=faculty_id)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            self.fields['faculty_group_course'].queryset = GroupCourse.objects.filter(faculty_id=self.instance.faculty)

class AddFacultyClassForm(forms.ModelForm):
    class Meta:
        model=Class
        fields = ['lab',"faculty_group_course","day","starttime","tools_used"]
    def __init__(self, faculty,*args, **kwargs):
        super().__init__(*args, **kwargs)
        groupcourses=GroupCourse.objects.filter(faculty=faculty)
        current_date = datetime.datetime.now()
        year=int(current_date.strftime("%Y"))
        month=int(current_date.strftime("%m"))
        sem=""
        if int(month)<=6:
            sem="EVEN"
        else:
            sem="ODD"
        curr_gp=[]
        for gc in groupcourses:
            if gc.group.groups.group_year==year and gc.group.groups.semester_type==sem:
                curr_gp.append(gc)
        self.fields['faculty_group_course'].queryset = GroupCourse.objects.filter(id__in={instance.id for instance in curr_gp})

class AllotDevicesForm(forms.ModelForm):
    name=forms.ModelChoiceField(queryset=CategoryOfDevice.objects.all())
    class Meta:
        model=StaffInventory
        fields=['device']
    field_order=['name','device']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['device'].queryset = Devices.objects.none()
        name_id=self.data.get('name')
        # print(name_id)
        self.fields['device'].queryset = Devices.objects.filter(name_id=name_id,in_inventory=False)
        
    

