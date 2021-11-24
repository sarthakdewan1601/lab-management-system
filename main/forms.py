from django import forms
from . import models
from .models import Staff
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = models.Complaint
        fields = ['computer', 'complaint']

class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name=forms.CharField(required=True)
    mobile_number=forms.IntegerField(required=True)
    class Meta:
        model = User
        fields = ("username", "email", "password1","mobile_number","name", "password2")

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
