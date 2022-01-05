
from django import http
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.db.models.base import Model
from django.shortcuts import render, redirect, HttpResponse
from .models import *
from .forms import LoginForm, ComplaintForm, NewComputerForm, SignupForm 
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm #add this
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
import datetime
from  django.views.decorators.csrf import csrf_protect
# Create your views here.

@login_required
def home(request):
	if request.user.is_staff:
		print(request.user.email)
		return render(request, "admin/dashboard.html", {})

	staff = Staff.objects.get(email=request.user.email)
	userLabs = Lab.objects.filter(staff=staff).order_by('id').all()
	return render(request, "home.html", {'userLabs': userLabs})

	# except:
	# 	tech = Technician.objects.get(tech_id=request.user.username)
	# 	complaints = Complaint.objects.all()
	# 	context = { "complaints": complaints}
	# 	return render(request, "tech_dashboard.html", context)

@login_required
def user_profile(request):
	# print(request.user)
	user_email=request.user.email
	#print(user_email)
	staff = Staff.objects.get(email=user_email)
	#print(staff.designation)

	if staff.category.category == "Lab Staff":
		
		# for admin 
		if staff.designation.designation == " System Analyst" or staff.designation.designation == "Lab Supervisor":
			# admin
			# labs = Lab.objects.get().all()
			#notifications=Notification.objects.filter(reciever='admin').all()
			return render(request, "admin/dashboard.html", {})

		
		if staff.designation.designation == "Lab Associate":
			pass

		
		if staff.designation.designation == "Lab Attendent":

			staff_1 = Staff.objects.get(email=request.user.email)
			userLabs = Lab.objects.filter(staff=staff).order_by('id').all()

			#leaves=Leaves.objects.get(staff=staff)
			context = {
				'userLabs' : userLabs,
				'staff'	: staff_1,
				#'leaves' : leaves,
			}
			return render(request, 'user profiles/lab_attendent.html',context)
			pass
			
			
		if staff.designation.designation == "Lab Technician":
			staff = Staff.objects.get(email=request.user.email)			
			complaints = Complaint.objects.all()
			current_notifications = Notification.objects.filter(reciever='Lab Technician').order_by('id').all()


			context = { 
				"complaints": complaints,
				"notifications": current_notifications
			}
			return render(request, "user profiles/Lab_technician.html", context)

	elif staff.category.category == "Office Staff":
		if staff.designation.designation == " Program Manager":
			pass
		if staff.designation.designation == " Program Coordinator":
			pass
		if staff.designation.designation == " Senior Assistant":
			pass
		if staff.designation.designation == " Skilled Helper":
			pass

	elif staff.category.category == "Faculty":
		if staff.designation.designation == " Professor":
			pass
		if staff.designation.designation == " Associate Professor":
			pass
		if staff.designation.designation == " Assistant Professor":
			pass
		
	else :
		if staff.designation.designation == " PHD":
			pass
		if staff.designation.designation == " ME":
			pass
		

@login_required
def userLeaves(request):
	staff = Staff.objects.get(email=request.user.email)	
	year = datetime.datetime.now().year
	leavesThisYear = TotalLeaves.objects.filter(year=year).all()
	
	userLeavesTaken = UserLeavesTaken.objects.filter(staff=staff)
	
	# print(userLeavesTaken)
	context = {
		"totalLeaves" : leavesThisYear,
		"year": year,
		"userLeavesTaken":userLeavesTaken,
	}
	return render(request, "leaves.html", context)

@csrf_protect
def requestleave(request):
	staff= Staff.objects.get(email=request.user.email)
	if request.method == 'POST':
		#request.POST
		form=request.POST
		applicant=form['applicant']
		leaveSelection=form['leaveSelection']
		date=form['date']
		substitute=form['substitute']
		reason=form['reason']

		year=datetime.datetime.now().year
		leave_type=TotalLeaves.objects.get(id=leaveSelection)
		
		substitute=Staff.objects.get(id=substitute)
		userstatus,wascreated=UserLeaveStatus.objects.get_or_create(staff=staff,leave_type=leave_type,date_time=date,reason=reason,substitute=substitute)
		userstatus.save()
		##notification

		customMessage1 = staff.name + " requested for leave"
		notification, was_created = Notification.objects.get_or_create(
			sender=staff, 
			reciever=str(substitute.id)+' '+substitute.name, 
			message=customMessage1,
			notification_type = 'LEAVE'
		)
		notification.save()

		customMessage2 = "your request for " + leave_type.LeaveName + " is placed"
		notification, was_created = Notification.objects.get_or_create(
			sender=staff, 
			reciever=str(staff.id)+' '+staff.name, 
			message=customMessage2,
			notification_type = 'LEAVE'
		)
		notification.save()

		return redirect("main:userLeaves")

# leave req-> nofitification to substi
#		   -> current user can check leave status
#          -> substitute confirm leave
#		   -> admin ke pass confirm leave 


	else:
		print("get")
		year = datetime.datetime.now().year
		totalLeavesCurrYear = TotalLeaves.objects.filter(year=year).all()
		substitutes = Staff.objects.exclude(name=staff.name).all()
		# substitutes = Staff.objects.all()

		context={
			'staff':staff,
			'totalLeavesCurrYear': totalLeavesCurrYear,
			'substitutes': substitutes
		}
	
		return render(request,"leaverequest.html",context)


@login_required	
def complaint(request, pk):
	device = Devices.objects.get(id=pk)
	if request.method == 'POST':
		form = ComplaintForm(request.POST)
		if form.is_valid():
			dev = device
			complaint=form.cleaned_data['complaint']

			staff=Staff.objects.get(email=request.user.email)			
			notification, was_created = Notification.objects.get_or_create(
				sender=staff, 
				reciever="Lab Technician", 
				message="You have a new Notification in complaints",
				notification_type = 'TECH'
			)			
			notification.save()

			complaint, was_created=Complaint.objects.get_or_create(device=dev,complaint=complaint,isActive=True)
			complaint.save()
			
		return redirect("main:home")
	else:
		form = ComplaintForm()

		context={
			'form': form,
			'name': device.name.category, 
			'id': device.device_id
		}
		return render(request, 'complaints.html', context)

@login_required
def notifications(request):
	staff = Staff.objects.get(email=request.user.email)			
	designation = staff.designation.designation
	notifications=[]
	
	if designation == 'Lab Technician':
		notification = Notification.objects.filter(notification_type='TECH').order_by('-time').all()
		notifications.extend(notification)
	receiver=str(staff.id) +' '+staff.name
	notification = Notification.objects.filter(reciever=receiver, notification_type='LEAVE').order_by('-time').all()
	notifications.extend(notification)

	if request.user.is_staff:
		notification=Notification.objects.filter(reciever='admin', notification_type='LEAVE').order_by('-time').all()
		notifications.extend(notification)


	# third type notificatoin baad mein okay? create another if condition
	
	return render(request, "notifications.html", {"notifications": notifications})

@login_required
def notificationRequest(request, pk):
	staff = Staff.objects.get(email=request.user.email)			
	notification = Notification.objects.get(id=pk)
	reciever_id= int(notification.reciever.split(' ')[0])
	substitue = Staff.objects.get(id=reciever_id)
	leaveRequests = UserLeaveStatus.objects.filter(substitute=substitue).all()
	

	if notification.notification_type == "LEAVE":
		if request.method == 'POST':
			notification
		else:
			# if substitue==notification.sender:
			# 	context= {
			# 		"staff": staff,
			# 		"notification" : notification, 
			# 		"leaves": leaveRequests
			# 	}
			print(leaveRequests)
			context = {
				"staff": staff,
				"notification" : notification, 
				"leaves": leaveRequests,
				"substitute": substitue,
				}
			return render(request, "notificationConfirm.html", context)

	
	if notification.notification_type == "TECH":
		return HttpResponse(202)



@login_required
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
	if request.method == "POST":
		print(request.POST)
		form = SignupForm(request.POST)
		if form.is_valid():
			email=form.cleaned_data['email'] # check for @thapar.edu
			res=email.split('@')[1]
			if res!='thapar.edu':
				messages.error(request, "Please enter you thapar email id")
				return redirect("main:register")
			else:
				user = form.save()
				name=form.cleaned_data['name']
				category1=request.POST['category']
				designation=request.POST['designation']
				agency=request.POST['agency']
				mobile_number=form.cleaned_data['mobile_number']
				Cat=Category.objects.get(category=category1)
				Des=Designation.objects.get(designation=designation )
				Agen=Agency.objects.get(agency=agency)
				staff,was_created=Staff.objects.get_or_create(name=name,email=email,mobile_number= mobile_number,category=Cat,designation=Des,agency=Agen)

				if designation == 'System Analyst' or designation == 'Lab Supervisor':
					user = User.objects.get(email=email)
					print(user)
					user.is_staff = True
					user.is_admin = True
					user.save()

				staff.save()
				
				return redirect("main:login")
		else:
			messages.error(request, "some error")
			return redirect("main:register")
	else:
		form = SignupForm()
		return render (request=request, template_name="accounts/register.html", context={"form": form})


def login_request(request):
	if request.method == "POST":
		form = LoginForm(request.POST)
		if form.is_valid():
			email = form.cleaned_data['email']
			password = form.cleaned_data['password']
			res=email.split('@')[1]
			if res!='thapar.edu':
				messages.error(request, "Please enter you thapar email id")
				return HttpResponse(400)

			# user=ExtendedUserModelBackend.authenticate(username=email,password=password)
		#	print(res)
			UserModel = get_user_model()
		#	print(UserModel)
			try:
				user = UserModel.objects.get(email=email)
			except UserModel.DoesNotExist:
				user=None
			else:
				if user.check_password(password):
					#print("passes")
					pass
				else :
					messages.error(request, "Please enter a correct password")
					return redirect("main:login")

			if user is not None:
				login(request,user)
			#	print("logged in") 
				messages.success(request, f"You are successfully logged in as {email}")
				return redirect("main:user_profile")
				
	form = LoginForm()
	return render(request, "accounts/login.html", {"login_form":form, 'messages': messages.get_messages(request)})


def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.")
   
	return redirect("main:login")





@login_required
def lab(request, pk):
	# listof all devices
	
	lab = Lab.objects.filter(lab=pk).order_by('id').all()
	lab_id=Lab.objects.get(id=pk)

	devices=Devices.objects.filter(lab=pk).order_by("id").all()
	print(devices)
	return render(request, "lab.html", {
				'devices': devices,
				'labid': pk,
				'labname': lab
				})

@login_required
def resolveConflict(request, pk):
	complaint = Complaint.objects.get(id=pk)
	complaint.isActive = False
	complaint.save()
	return redirect('main:home')


def adminStaff(request):
	staffs = Staff.objects.all()
	return render(request, "admin/adminStaffs.html", {"staffs":staffs})

# def adminTechnicians(request):
# 	techs = Technician.objects.all()
# 	return render(request, "admin/adminTechnicians.html", {"techs": techs})

def adminLabs(request):
	labs=Lab.objects.all()
	return render(request, "admin/adminLabs.html", {"labs": labs})

def adminComplaints(request):
	complaints = Complaint.objects.all().order_by('id')
	return render(request, "admin/adminComplaints.html", {"complaints":complaints})

