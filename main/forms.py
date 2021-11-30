from django import forms
from django.forms.fields import ChoiceField
from .models import Staff, Technician
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class ComplaintForm(forms.Form):
    complaint=forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter complaint'}))

class NewComputerForm(forms.Form):
    computer_id=forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Computer ID'}))
    floor_id=forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter Floor ID'}))


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    class Meta:
        model=User
        fields=['username', 'password']

MEMBER = [
    ('SM', 'StaffMember'),
    ('TH', 'Technician')
]

class NewUserForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password Confirm'}))
    name=forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder':'Full Name'}))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'placeholder':'Email'}))  
    mobile_number=forms.IntegerField(required=True, widget=forms.TextInput(attrs={'placeholder':'Mobile Number'}))
    type=forms.ChoiceField(choices=MEMBER)

    class Meta:
        model = User
        fields = ("username", "name", "mobile_number","email", "password1", "password2", "type")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']

        user_email = self.cleaned_data['email']
        username = self.cleaned_data['username']
        user_mobile = self.cleaned_data['mobile_number']
        name = self.cleaned_data['name']
        type=self.cleaned_data['type']
        
        # participant, was_created=Participant.objects.get_or_create(email=user_email)
        # selected_meetup.participant.add(participant)

        if type == 'SM':
            staff,was_created=Staff.objects.get_or_create(staff_id=username, name=name,email=user_email,mobile_number= user_mobile, type=type)
            staff.save()
        else:
            technician,was_created = Technician.objects.get_or_create(tech_id=username, name=name, email=user_email, mobile_number=user_mobile)
            technician.save()

        if commit:
            user.save()
        return user