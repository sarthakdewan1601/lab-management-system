from django import http
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required

from django.db.models.base import Model
from django.shortcuts import render, redirect, HttpResponse
from .models import Lab,Devices,Complaint,Staff
from .forms import LoginForm, ComplaintForm, NewComputerForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm #add this

# Create your views here.

@login_required
def home(request):
	if request.user.is_staff:
		return render(request, "admin/dashboard.html", {})

	staff = Staff.objects.get(staff_id=request.user.username)
	userLabs = Lab.objects.filter(staff=staff).order_by('id').all()
	return render(request, "home.html", {'userLabs': userLabs})

	# except:
	# 	tech = Technician.objects.get(tech_id=request.user.username)
	# 	complaints = Complaint.objects.all()
	# 	context = { "complaints": complaints}
	# 	return render(request, "tech_dashboard.html", context)

@login_required
def complaint(request, pk):
	computer = Devices.objects.get(id=pk)
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

def add_computer(request,pk):
	lab=Lab.objects.get(id=pk)

	print(lab)
	if request.method == 'POST':
		form = NewComputerForm(request.POST)
		if form.is_valid():
			labid=lab
			compid=form.cleaned_data['computer_id']
			fid=form.cleaned_data['floor_id']
			computer, was_created=Devices.get_or_create(computer_id=compid,lab_id=labid,floor_id=fid)
			computer.save()
			
		return redirect("main:home")
	else:
		form = NewComputerForm()

		context={
			'form': form,
			'labid':lab,
		}
		return render(request, 'add_computer.html', context)
	
	
def register_request(request):
	# if request.method == "POST":
	# 	form = NewUserForm(request.POST)
	# 	if form.is_valid():
	# 		user = form.save()
	# 		login(request, user)
	# 		messages.success(request, "Registration successful.")
	# 		return redirect("main:home")
	# 	messages.error(request, "Unsuccessful registration. Invalid information.")
	# else:
	# 	form = NewUserForm()

	# return render (request=request, template_name="accounts/register.html", context={"register_form":form, 'messages':messages.get_messages(request)})
	return render (request=request, template_name="accounts/register.html", context={})


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
				messages.error(request,"No user found !!")
		else:
			messages.error(request, "Invalid Values. Please fill correctly")
	form = LoginForm()
	return render(request, "accounts/login.html", {"login_form":form, 'messages': messages.get_messages(request)})


def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.")
   
	return redirect("main:login")



def lab(request, pk):
	print(pk)
	computers = Computers.objects.filter(lab_id=pk).order_by('id').all()
	lab_id=Lab.objects.get(id=pk)
	print(computers)
	return render(request, "lab.html", {
				'computers': computers,
				'labid': pk,
				'labname':lab_id, })


def resolveConflict(request, pk):
	complaint = Complaint.objects.get(id=pk)
	complaint.isActive = False
	complaint.save()
	return redirect('main:home')


def adminStaff(request):
	staffs = Staff.objects.all()
	return render(request, "admin/adminStaffs.html", {"staffs":staffs})

def adminTechnicians(request):
	techs = Technician.objects.all()
	return render(request, "admin/adminTechnicians.html", {"techs": techs})

def adminLabs(request):
	labs=Lab.objects.all()
	return render(request, "admin/adminLabs.html", {"labs": labs})

def adminComplaints(request):
	complaints = Complaint.objects.all().order_by('id')
	return render(request, "admin/adminComplaints.html", {"complaints":complaints})

