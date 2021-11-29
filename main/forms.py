from django import forms
from . import models
from .models import Staff
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class ComplaintForm(forms.Form):
    complaint=forms.CharField(max_length=1024)

class NewComputerForm(forms.Form):
    computer_id=forms.CharField(max_length=20)
    floor_id=forms.CharField(max_length=10)


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    class Meta:
        model=User
        fields=['username', 'password']


class NewUserForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password Confirm'}))
    name=forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder':'Full Name'}))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'placeholder':'Email'}))  
    mobile_number=forms.IntegerField(required=True, widget=forms.TextInput(attrs={'placeholder':'Mobile Number'}))
    class Meta:
        model = User
        fields = ("username", "name", "mobile_number","email", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user_email = self.cleaned_data['email']
        user_id = self.cleaned_data['username']
        user_mobile = self.cleaned_data['mobile_number']
        user_name = self.cleaned_data['name']
        
        # participant, was_created=Participant.objects.get_or_create(email=user_email)
        # selected_meetup.participant.add(participant)
        staff,was_created=Staff.objects.get_or_create(staff_id=user_id, name=user_name,email=user_email,mobile_number= user_mobile)
        #print(staff)
        # Staff.add(staff)
        staff.save()
        if commit:
            user.save()
        return user
