from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required

from django.db.models.base import Model
from django.shortcuts import render, redirect, HttpResponse
from .models import Lab,Computers,Complaint,Staff
from .forms import NewUserForm, LoginForm, ComplaintForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm #add this
from django.contrib.auth import login, authenticate #add this

# Create your views here.

@login_required
def home(request):
	staff = Staff.objects.get(staff_id=request.user.username)
	userLabs = Lab.objects.filter(staff=staff).order_by('id').all()
	return render(request, "home.html", {'userLabs': userLabs})

@login_required
def complaint(request, pk):
	computer = Computers.objects.get(id=pk)
	if request.method == 'POST':
		# print(request.POST)
		# print(pk)
		form = ComplaintForm(request.POST)
		if form.is_valid():
			comp = computer
			complaint=form.cleaned_data['complaint']
			complaint, was_created=Complaint.objects.get_or_create(computer=comp,complaint=complaint,isActive=True)
			complaint.save()
			
		return redirect("main:home")
	else:
		form = ComplaintForm()

		context={
			'form': form,
			'computer': computer
		}
		return render(request, 'complaints.html', context)


def register_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Registration successful.")
			return redirect("main:home")
		messages.error(request, "Unsuccessful registration. Invalid information.")
	else:
		form = NewUserForm()
	return render (request=request, template_name="register.html", context={"register_form":form, 'messages':messages.get_messages(request)})

def login_request(request):
	if request.method == "POST":
		form = LoginForm(request, data=request.POST)
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
	form = LoginForm()
	return render(request=request, template_name="login.html", context={"login_form":form, 'messages':messages.get_messages(request)})

def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.")
   
	return redirect("main:login")



def lab(request, pk):
	computers = Computers.objects.filter(lab_id=pk).order_by('id').all()
	print(computers)
	return render(request, "lab.html", {'computers': computers})

