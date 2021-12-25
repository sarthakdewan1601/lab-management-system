from django import forms
from django.forms.fields import ChoiceField
from .models import Designation, Staff
from django.contrib.auth.forms import  AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

class ComplaintForm(forms.Form):
    complaint=forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter complaint'}))

class NewComputerForm(forms.Form):
    computer_id=forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Computer ID'}))
    floor_id=forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Floor ID'}))


class LoginForm(forms.Form):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder':'Email'}))
    password = forms.CharField(required=True , widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    
    class Meta:
        model=User
        fields=['email', 'password']
        
# class LoginForm(AuthenticationForm):
#     username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
#     password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
#     class Meta:
#         model=User
#         fields=['username', 'password']

# class NewUserForm(UserCreationForm):
    # name=forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder':'Full Name'}))
    # email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'placeholder':'Email'}))
    # password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    # password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password Confirm'}))
    # mobile_number=forms.IntegerField(required=True, widget=forms.TextInput(attrs={'placeholder':'Mobile Number'}))
    # category=forms.ChoiceField(choices=CATEGORY)
#     Designation=forms.ChoiceField(choices=DESIGNATION)

#     class Meta:
#         model = User
#         fields = ("username", "name", "mobile_number","email", "password1", "password2", "type")

#     

#         user = super(NewUserForm, self).save(commit=False)
#         user.email = self.cleaned_data['email']

#         user_email = self.cleaned_data['email']
#         username = self.cleaned_data['username']
#         user_mobile = self.cleaned_data['mobile_number']
#         name = self.cleaned_data['name']
#         type=self.cleaned_data['type']
        
#         # participant, was_created=Participant.objects.get_or_create(email=user_email)
#         # selected_meetup.participant.add(participant)

        
#         staff,was_created=Staff.objects.get_or_create(staff_id=username, name=name,email=user_email,mobile_number= user_mobile, type=type)
#         staff.save()
        
#         if commit:
#             user.save()
#         return user


class SignupForm(UserCreationForm):
    name=forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder':'Full Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder':'Email'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    mobile_number=forms.IntegerField(required=True, widget=forms.TextInput(attrs={'placeholder':'Mobile Number'}))

        
    class Meta:
        model = User
        fields = ("email", "password1", "password2", "name", "mobile_number")
        
    def save(self, commit=True):
        # save user in user model fields email password
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        name= self.cleaned_data['name']

        user = super(UserCreationForm, self).save(commit=False)

        user.set_password(password)
        user.email = email
        user.username = name
        if commit:
          user.save()
        return user


        