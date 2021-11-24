from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from django.db.models.base import Model
from django.shortcuts import render, redirect
from .models import Lab,Computers,Complaint,Staff
from .forms import ComplaintForm
from .forms import NewUserForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm #add this
from django.contrib.auth import login, authenticate #add this

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


# def loginView(request):
#     if request.method =='POST':
#         loginForm= AuthenticationForm(data = request.POST)
#         if loginForm.is_valid():
#             user = loginForm.get_user()
#             login(request, user)
#             return redirect('main:home')
#     else:
#         loginForm = AuthenticationForm(request.POST)
    
#     return render(request, 'login.html', { 'loginForm': loginForm })


# def logoutView(request):
#     logout(request)
#     return redirect('main:login')


# def signUpView(request):
#     if request.method == "POST":
#         signUpForm = UserCreationForm(request.POST)
#         if signUpForm.is_valid():
#             user = signUpForm.save()
#             login(request, user)
#             return redirect('main:home')
#     else:
#         signUpForm = UserCreationForm()
#     return render(request, 'signup.html', {'SignupForm': signUpForm})


def register_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Registration successful.")
			return redirect("main:home")
		messages.error(request, "Unsuccessful registration. Invalid information.")
	form = NewUserForm()
	return render (request=request, template_name="register.html", context={"register_form":form})

def login_request(request):
	if request.method == "POST":
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				messages.info(request, f"You are now logged in as {username}.")
				return redirect("main:home")
			else:
				messages.error(request,"Invalid username or password.")
		else:
			messages.error(request,"Invalid username or password.")
	form = AuthenticationForm()
	return render(request=request, template_name="login.html", context={"login_form":form})

def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.")
   
	return redirect("main:login")