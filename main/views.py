from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from django.db.models.base import Model
from django.shortcuts import render, redirect
from .models import Lab,Computers,Complaint,Staff
from .forms import ComplaintForm

# Create your views here.

def home(request):
    return render(request, "home.html", {})

def complaint(request):

    if request.method=='POST':
        pass
        # complaint_form=ComplaintForm(request.POST)
        # if complaint_form.is_valid():
        #     complaint_form.is_active=True

        #     complaint_form.save()
        # return redirect('/')
    else:
        form = ComplaintForm()
    
    return render(request, 'complaints.html', { 'form': form })


def loginView(request):
    if request.method =='POST':
        loginForm= AuthenticationForm(data = request.POST)
        if loginForm.is_valid():
            user = loginForm.get_user()
            login(request, user)
            return redirect('main:home')
    else:
        loginForm = AuthenticationForm(request.POST)
    
    return render(request, 'login.html', { 'loginForm': loginForm })


def logoutView(request):
    logout(request)
    return redirect('main:login')


def signUpView(request):
    if request.method == "POST":
        signUpForm = UserCreationForm(request.POST)
        if signUpForm.is_valid():
            user = signUpForm.save()
            login(request, user)
            return redirect('main:home')
    else:
        signUpForm = UserCreationForm()
    return render(request, 'signup.html', {'SignupForm': signUpForm})



   