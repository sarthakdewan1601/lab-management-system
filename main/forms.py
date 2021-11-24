from django import forms
from . import models
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
        if commit:
            user.save()
        return user
