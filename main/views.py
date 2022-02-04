from distutils.log import error
import email
from email import message
from genericpath import exists
from re import template
from django.conf import settings
from email.message import EmailMessage
from urllib import response
from flask import request
from matplotlib.style import context
from verify_email.email_handler import send_verification_email
# from readline import write_history_file
from tracemalloc import start
from unicodedata import category
from django import http
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required

from django.db.models.base import Model
from django.http.response import Http404
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm #add this
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from  django.views.decorators.csrf import csrf_protect
from django.db import IntegrityError
from django.urls import reverse_lazy
from .models import *
from .forms import *
from django.http import JsonResponse
import datetime
import threading

from django_email_verification import send_email
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes,  force_text
from main.utils import generate_token
from django.core.mail import EmailMessage


UserModel = get_user_model()

class EmailThread(threading.Thread):		#creating email thread
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)
    def run(self):
        self.email.send()

def user_email_verification(request, user, subject, templateForMail, *message):
    current_site = get_current_site(request)
    email_body = render_to_string(templateForMail, {
        'user': user.email,
		'message': message,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.email)),
        'token': generate_token.make_token(user)
    })
    email_message = EmailMessage(subject=subject, body=email_body, from_email=settings.EMAIL_HOST_USER, to=[user.email])
    if True:
        EmailThread(email_message).start()

def confirmation_mail(request, user, subject, templateForMail, name):
	current_site = get_current_site(request)
	email_body = render_to_string(templateForMail, {
        'user': user.email,
        'domain': current_site,
		'name': name
    })
	email_message = EmailMessage(subject=subject, body=email_body, from_email=settings.EMAIL_HOST_USER, to=[user.email])
	email_message.content_subtype = 'html'
	if True:
		EmailThread(email_message).start()




def activate_user(request, uidb64, token):
	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(email=uid)
	except Exception as err:
		print(err)
		pass
		
	tokenStatus, timedout = generate_token.check_token(user, token)
	if not tokenStatus and timedout:								#registered and not verified in time 
		#send email 
		templateForMail = 'accounts/active_email.html'
		subject = "Activate Your Account"
		user_email_verification(request, user, subject, templateForMail, )
		#redirect to new html error message
		return render(request, "accounts/token-timedout.html", {})

	if user and tokenStatus and not timedout:
		user.is_active = True
		user.is_email_verified = True
		user.save()
		staff = Staff.objects.get(user_obj=user)
		subject = "Account Activated"
		templateName = 'accounts/activation-complete.html'
		confirmation_mail(request, user, subject, templateName, staff.name)
		messages.add_message(request, messages.SUCCESS, 'Email verified, you can now login')
		return redirect('main:login')
	
	if not tokenStatus:
		return render(request, 'accounts/activation-link-failed.html', {"user": user})
	
def register_request(request):
	if request.method == "POST":
			# check for @thapar.edu			
		email=request.POST['email']
		res=email.split('@')[1]
		if res!='thapar.edu':
			messages.error(request, "Please enter you thapar email id")
			return redirect("main:register")

		try:
			alreadyExist = User.objects.get(email=email)
			if(alreadyExist):
				messages.error(request, "This email is already registered, please try loggin in")
				return redirect('main:login')
		except User.DoesNotExist or Exception as err:
			pass

		password = request.POST['password1']
		confirmPassword = request.POST['password2']
		if password != confirmPassword:
			messages.error(request, "Passwords not same")
			return redirect("main:register")

		# function to check whether entered password is strong or not .... return true or false 
		# if false then return to register with a message
		# ---here ----


		# user = User.objects.
		name=request.POST['name']
		category1=request.POST['category']
		designation=request.POST['designation']
		agency=request.POST['agency']
		mobile_number=request.POST['mobile_number']

		Cat=Category.objects.get(category=category1)
		Des=Designation.objects.get(designation=designation)
		Agen=Agency.objects.get(agency=agency)
		

		if designation == 'System Analyst' or designation == 'Lab Supervisor':
			user = User.objects.create_superuser(email, confirmPassword, is_active=False)
			user.is_active = False
			subject = "Activate Your Account"
			templateForMail = 'accounts/active_email.html'
			messageForEmail = "activate your email"
			user_email_verification(request, user, subject, templateForMail, messageForEmail)
			messages.add_message(request, messages.SUCCESS,'We sent you an email to verify your account')

		else:
			user = User.objects.create_user(email, password, is_active=False)
			user.is_active = False
			subject = "Activate Your Account"
			templateForMail = 'accounts/active_email.html'
			messageForEmail = "activate your email"
			user_email_verification(request, user, subject, templateForMail, messageForEmail)
			messages.add_message(request, messages.SUCCESS,'We sent you an email to verify your account')

		staff,was_created=Staff.objects.get_or_create(user_obj=user, name=name,email=email,mobile_number= mobile_number,category=Cat,designation=Des,agency=Agen)
		staff.save()

		year = datetime.datetime.now().year 
		totalLeavesCurrYear = TotalLeaves.objects.filter(year=year).all()
		for leave in totalLeavesCurrYear:
			userLeavesTaken, was_created = UserLeavesTaken.objects.get_or_create(
				staff=staff,
				leave_taken=leave
			)
			userLeavesTaken.save()
		return redirect("main:login")

		# else:
		# 	print("invalid credentials")
		# 	messages.error(request, "Invalid Credentials")
		# 	return redirect("main:register")
	else:
		form = SignupForm()
		return render(request, "accounts/register.html", {"form": form})

def login_request(request):
	if request.method == "POST":
		email = request.POST['email']
		password = request.POST['password']
		res=email.split('@')[1]
		if res!='thapar.edu':
			messages.error(request, "Please enter you thapar email id")
			return redirect('main:login')
		try:
			user = User.objects.get(email=email)
			if not user.is_email_verified:
				messages.error(request, "Your email is not verified, please verify using the link provided in mail")
				return redirect('main:login')
			if not user.check_password(password):
				messages.error(request, "Entered password is not correct, try again")
				return redirect('main:login')
			
			if not user.is_loggedIn:
				user.is_loggedIn = True
				user.save()
				staff = Staff.objects.get(email=user.email)
				messages.success(request, f"Welcome {staff.name}")
				login(request, user)
				return redirect("main:user_profile")

		except User.DoesNotExist:
			current_site = get_current_site(request)
			messages.error(request, f"This email is not registered. Please signup first: <a href='http://{current_site}/accounts/signup'>click here</a>")
			user = None
			return redirect('main:login')

	return render(request, "accounts/login.html", )

@login_required
def logout_request(request, id):
	staff = Staff.objects.get(id=id)
	userEmail = staff.email
	user = User.objects.get(email=userEmail)
	user.is_loggedIn = False
	user.save()
	logout(request)
	messages.info(request, "You have successfully logged out.")
	return redirect("main:login")

def passwordResetView(request):
	if request.method == "POST":
		try:
			email = request.POST['email']
			user = User.objects.get(email=email)

			if not user.is_email_verified:
				messages.error(request, "Your email is not verified, please verify your email first using the link provided in mail")
				return render(request, 'accounts/password_reset.html', {'messages': messages.get_messages(request)})
			else:
				subject="Reset Your Password"
				templateForMail = 'accounts/password_reset_sent.html'
				user_email_verification(request, user, subject, templateForMail, "password reset")
				messages.success(request, "Check your email and click the link to reset your password")
				return redirect('main:login')

		except AttributeError or User.DoesNotExist or Exception as err:
			print(err)
			messages.error(request, "Not a valid Email Id, Please register first")
			return redirect('main:register')
	else:
		return render(request, 'accounts/password_reset.html')

def passwordResetConfirmView(request, uidb64, token):
	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(email=uid)

		tokenStatus, timedout = generate_token.check_token(user, token)

		if not tokenStatus or timedout:
			#send email 
			templateForMail = 'accounts/active_email.html'
			subject = "Activate Your Account"
			user_email_verification(request, user, subject, templateForMail, )

			#redirect to new html error message
			return render(request, "accounts/token-timedout.html", {})

		if tokenStatus:
			user.is_email_verified = True
			return redirect('main:passwordResetForm', token=token, id=user.id)
		else:
			return render(request, "accounts/password-reset-failed.html")	

	except RuntimeError or Exception as err:
		print(err)
		messages.error(request, "User not found, click the link in the mail received")
		return render(request, "accounts/password-reset-failed.html")

def passwordResetForm(request, token, id):
	try:
		user = User.objects.get(id=id)
		print(user)
		if user and generate_token.check_token(user, token):
			staff = Staff.objects.get(email=user.email)
			if request.method == "POST":
				password = request.POST['password']
				passwordConfirm = request.POST['passwordConfirm']
				if password != passwordConfirm:
					messages.error(request, "Password not match")
					return redirect('main:passwordResetForm', token=token, id=user.id)
				else:
					user.set_password(password)
					user.save()
					staff = Staff.objects.get(user_obj=user)
					subject = "Password Update Successful"
					templateName = 'accounts/password_reset_done.html'
					confirmation_mail(request, user, subject, templateName, staff.name)
					
					messages.success(request, "Password updated successfully")
					if user.is_loggedIn:
						login(request, user)
						return redirect('main:user_profile')
					else:
						return redirect('main:login')
			else:	# get request
				return render(request, "accounts/password_reset_form.html", {"staff":staff, 'messages': messages.get_messages(request)})
		else:
			messages.error(request, "User not found, click the link in the mail received")
			return redirect('main:login')
	except ValueError or Exception as err:
		print(err)
		return render(request, "accounts/password-reset-failed.html")

@login_required
def	passwordChange(request, id):
	try:		
		staff = Staff.objects.get(id=id)
		user = User.objects.get(email=staff.email)
		token = generate_token.make_token(user)
		return redirect('main:passwordResetForm', token=token, id=user.id)
	except Exception as err:
		print(err)
		messages.error(request, "Something went wrong while changing your password")
		return redirect(request, 'main:user_profile')






@login_required
def home(request):
	staff=Staff.objects.get(user_obj=request.user)
	if request.user.is_staff:
		a = User.objects.get(email=request.user)
		print(a)
		return render(request, "admin/dashboard.html", {"staff":staff})

	staff = Staff.objects.get(user_obj=request.user)
	userLabs = Lab.objects.filter(staff=staff).order_by('id').all()
	return render(request, "home.html", {'userLabs': userLabs, "staff":staff, 'messages': messages.get_messages(request)})

	# except:
	# 	tech = Technician.objects.get(tech_id=request.user.username)
	# 	complaints = Complaint.objects.all()
	# 	context = { "complaints": complaints}
	# 	return render(request, "tech_dashboard.html", context)

def user_profile_details(request):
	staff=Staff.objects.get(user_obj=request.user)
	return render(request, "userProfiles/user_profile.html", {'staff':staff})

@login_required
def user_profile(request):
	userEmail = request.user.email
	print('user_email in user_profile:',userEmail)
	staff = Staff.objects.get(email=userEmail)
	#print(staff.designation)

	if staff.category.category == "Lab Staff":
		
		# for admin 

		if staff.designation.designation == "System Analyst" or staff.designation.designation == "Lab Supervisor":
			# labs = Lab.objects.get().all()
			#notifications=Notification.objects.filter(reciever='admin').all()
			return render(request, "admin/dashboard.html", {"staff":staff})

		
		if staff.designation.designation == "Lab Associate":
			pass

		
		if staff.designation.designation == "Lab Attendent":

			staff_1 = Staff.objects.get(user_obj=request.user)
			userLabs = Lab.objects.filter(staff=staff).order_by('id').all()

			#leaves=Leaves.objects.get(staff=staff)
			context = {
				'userLabs' : userLabs,
				'staff'	: staff_1,
			}
			return render(request, 'userProfiles/lab_attendent.html',context)
			# pass
			
		if staff.designation.designation == "Lab Technician":
			staff = Staff.objects.get(user_obj=request.user)			
			complaints = Complaint.objects.filter(isActive=True).all()
			current_notifications = Notification.objects.filter(reciever='Lab Technician').order_by('id').all()


			context = { 
				"staff":staff,
				"complaints": complaints,
				"notifications": current_notifications
			}
			return render(request, "userProfiles/Lab_technician.html", context)
			
			# complaint resolve form details
			# static-> device id, lab id, complaint, jisne complaint kri hai vo user, 
			# dynamic -> message kya problem thi
			# who resolved = staff (obv tech hoga koi) 			
			# that complaint -> isActive = False
			# notification remove isActive = False

	elif staff.category.category == "Office Staff":
		if staff.designation.designation == " Program Manager":
			pass
		if staff.designation.designation == " Program Coordinator":
			pass
		if staff.designation.designation == " Senior Assistant":
			pass
		if staff.designation.designation == " Skilled Helper":
			pass

	else:
		# print(request.user.is_active)
		context={
			'staff':staff,
		}
		return render(request,"userProfiles/faculty.html",context)
		

@login_required
def editProfile(request, pk):
	staff = Staff.objects.get(id=pk)		
	if request.user.is_staff:
		admin=Staff.objects.get(user_obj=request.user)
		if request.method=="POST":
			form=request.POST
			name=form['name']
			designationId = form['designation']
			agencyId=form['agency']
			mobile_number=form['mobile_number']
			updatedAgency = Agency.objects.get(id=agencyId)
			updatedDesgination = Designation.objects.get(id=designationId)
			staff.name=name
			staff.designation=updatedDesgination
			staff.agency = updatedAgency
			staff.mobile_number=mobile_number
			staff.save()
			return redirect('main:adminStaff')
		else:
			category=Category.objects.get(category=staff.category)
			designations=Designation.objects.filter(category=category)
			designations=designations.exclude(designation=staff.designation)
			agency=Agency.objects.exclude(agency=staff.agency)
			context = {
				"staff": admin,
				"staff1": staff,
				"designations":designations,
				"agency":agency
			}
			return render(request, "userProfiles/edit_profile.html", context)
	else:
		if request.method == "POST":
			name = request.POST['name']
			mobile_number = request.POST['mobile_number']
			staff.name = name
			staff.mobile_number = mobile_number
			staff.save()
			return redirect('/')

		else:
			context = {
				"staff": staff
			}
			return render(request, "userProfiles/edit_profile.html", context)


@login_required
def userLeaves(request):
	staff = Staff.objects.get(user_obj=request.user)	
	year = datetime.datetime.now().year
	leavesThisYear = TotalLeaves.objects.filter(year=year).all()
	
	userLeavesTaken = UserLeavesTaken.objects.filter(staff=staff)
	
	# print(userLeavesTaken)
	context = {
		"staff":staff,
		"totalLeaves" : leavesThisYear,
		"year": year,
		"userLeavesTaken":userLeavesTaken,
	}
	return render(request, "leaves/leaves.html", context)

@csrf_protect
def requestleave(request):
	staff= Staff.objects.get(user_obj=request.user)

	if request.method == 'POST':
		# check kr ki jo leave request kri hai vo exceed toh nai h 
		# for eg ek year mein 8 casual 
		# cas -> 8 decline status 

		form=request.POST
		applicant=form['applicant']
		leaveSelection=form['leaveSelection']
		fromDate=form['fromDate']
		substitute=form['substitute']
		reason=form['reason']

		year=datetime.datetime.now().year
		leave_type=TotalLeaves.objects.get(id=leaveSelection)
		fromDateNumber = fromDate.split("-")[2]
		try:
			multipleLeaves = form['multipleLeaveCheckbox']
			toDate=form['toDate']
			todateNumber = toDate.split("-")[2]
			
			# total count of leaves , store it in models
			countOfLeaves = int(todateNumber) - int(fromDateNumber)
			
			
			userstatus,wascreated=UserLeaveStatus.objects.get_or_create(staff=staff,leave_type=leave_type,from_date=fromDate,to_date=toDate, reason=reason,substitute=substitute)
			userstatus.save()
			##notification

			customMessage1 = staff.name + " requested for leave"
			notification, was_created = Notification.objects.get_or_create(
				sender=staff, 
				reciever=str(substitute.id)+' '+substitute.name, 
				message=customMessage1,
				notification_type = 'LEAVE',
				taskId = userstatus.id
			)
			notification.save()

			customMessage2 = "your request for " + leave_type.LeaveName + " leave is placed"
			notification, was_created = Notification.objects.get_or_create(
				sender=staff, 
				reciever=str(staff.id) + ' ' + staff.name, 
				message=customMessage2,
				notification_type = 'LEAVE',
				taskId=userstatus.id
			)
			notification.save()
			return HttpResponse(200)

		except:
			# userstatus,wascreated=UserLeaveStatus.objects.get_or_create(staff=staff,leave_type=leave_type,from_date=fromDate, reason=reason,substitute=substitute)
			# userstatus.save()
			# ##notification

			# customMessage1 = staff.name + " requested for leave"
			# notification, was_created = Notification.objects.get_or_create(
			# 	sender=staff, 
			# 	reciever=str(substitute.id)+' '+substitute.name, 
			# 	message=customMessage1,
			# 	notification_type = 'LEAVE',
			# 	taskId = userstatus.id
			# )
			# notification.save()

			# customMessage2 = "your request for " + leave_type.LeaveName + " leave is placed"
			# notification, was_created = Notification.objects.get_or_create(
			# 	sender=staff, 
			# 	reciever=str(staff.id) + ' ' + staff.name, 
			# 	message=customMessage2,
			# 	notification_type = 'LEAVE',
			# 	taskId=userstatus.id
			# )
			# notification.save()


			return HttpResponse(200)

# leave req-> nofitification to substi
#		   -> current user can check leave status
#          -> substitute confirm leave
#		   -> admin ke pass confirm leave 


	else:
		year = datetime.datetime.now().year  # 2022
		totalLeavesCurrYear = TotalLeaves.objects.filter(year=year).all()
		# check ki if any leave category is  > 0 then display
		userleavetaken=UserLeavesTaken.objects.filter(staff=staff)
		user_leaves_remaining=[]

		for leave in userleavetaken:
			if leave.count<leave.leave_taken.count:
				user_leaves_remaining.append(leave.leave_taken.LeaveName)
		totalLeavesCurrYear=[leaves for leaves in totalLeavesCurrYear if leaves.LeaveName in user_leaves_remaining]
		# print(user_leaves_remaining)
		# print(totalLeavesCurrYear)
		substitutes = Staff.objects.exclude(name=staff.name).all()
		# substitutes = Staff.objects.all()

		context={
			'staff':staff,
			'totalLeavesCurrYear': totalLeavesCurrYear,
			'substitutes': substitutes
		}
	
		return render(request,"leaves/leaverequest.html",context)
@login_required
def checkLeaveStatus(request):
	staff = Staff.objects.get(user_obj=request.user)
	# print(staff)

	pendingRequests = UserLeaveStatus.objects.filter(staff=staff).order_by("-id")
	# get all the pending requests 
	context = {
		'staff':staff,
		"pendingRequests": pendingRequests
	}
	return render(request, "leaves/leaveRequestStatus.html", context)

@login_required
def checkLeaveStatusId(request, pk):
	staff = Staff.objects.get(user_obj=request.user)
	leaveRequest = UserLeaveStatus.objects.get(id=pk)
	context = {
		'staff':staff,
		'leaveRequest':leaveRequest
	}
	return render(request, "leaves/leaveRequestStatusId.html", context)

# user cancels its posted leave
@login_required
def cancelLeaveRequest(request, pk): 
	# get object and delete from db
	leave = UserLeaveStatus.objects.get(id=pk)
	leave.delete()
	return redirect('main:checkLeaveStatus')

@login_required
def approveLeaves(request):
	staff=Staff.objects.get(user_obj=request.user)
	#for admin
	if request.user.is_staff:
		#return HttpResponse(201)
		requestedleaves=UserLeaveStatus.objects.filter(substitute_approval=True,admin_approval=False,rejected=False)
		approvedleaves=UserLeaveStatus.objects.filter(substitute_approval=True,admin_approval=True,rejected=False)
		rejectedleaves=UserLeaveStatus.objects.filter(substitute_approval=True,admin_approval=False,rejected=True)
	
		context={
			'staff':staff,
			"requestedleaves":requestedleaves,
			"approvedleaves":approvedleaves,
			"rejectedleaves":rejectedleaves
		}
		return render(request,'admin/adminLeaveApproval.html',context)

	# get leaves in which current user is substitute

	leaves = UserLeaveStatus.objects.filter(substitute=staff).order_by("-from_date")
	context = {
		'staff':staff,
		"leaves": leaves
	}
	return render(request, 'leaves/leaveapproval.html', context)


@login_required
def approveRequest(request, pk):
	# get leave
	if request.user.is_staff:
		sender=Staff.objects.get(user_obj=request.user)
		leave = UserLeaveStatus.objects.get(id=pk)
		leave.admin_approval = True
		leave.rejected = False
		leave.status = "Approved"
		leave.admin=sender 
		leave.save()
		notification_receiver = Staff.objects.get(id=leave.staff.id)
		notification, was_created = Notification.objects.get_or_create(
			sender=sender,
			reciever=str(notification_receiver.id) + " " + (notification_receiver.name),
			message="your " + str(leave.leave_type.LeaveName) + " leave application was approved by admin",
			notification_type="LEAVE_ACCEPTED",
			taskId=str(leave.id)
		)
		notification.save()

		
		# 1) ki user leaves taken hai uss user ka usko update 
		userleavetaken = UserLeavesTaken.objects.get(staff=leave.staff,leave_taken=leave.leave_type)
		userleavetaken.count += 1
		userleavetaken.save()
		
		return redirect("main:approveLeaves")

	leave = UserLeaveStatus.objects.get(id=pk)
	leave.substitute_approval = True
	leave.rejected = False
	leave.status = "Waiting for admin to respond, approved by " + str(leave.substitute.name)
	leave.save()

	
	notification_receiver = Staff.objects.get(id=leave.staff.id)
	notification, was_created = Notification.objects.get_or_create(
		sender=leave.substitute,
		reciever=str(notification_receiver.id) + " " + (notification_receiver.name),
		message="your " + str(leave.leave_type.LeaveName) + " leave application was approved by " + str(leave.substitute.name),
		notification_type="LEAVE_ACCEPTED",
		taskId=str(leave.id)
	)
	notification.save()

	return redirect("main:approveLeaves")

@login_required
def declineRequest(request, pk):
	sender=Staff.objects.get(user_obj=request.user)

	if request.user.is_staff:	
		leave = UserLeaveStatus.objects.get(id=pk)
		leave.admin_approval = False
		leave.rejected = True
		leave.status = "Declined by Admin " + str(sender.name) 
		leave.admin=sender
		leave.save()

		notification_receiver = Staff.objects.get(id=leave.staff.id)
		notification, was_created = Notification.objects.get_or_create(
			sender=sender,
			reciever=str(notification_receiver.id) + " " + (notification_receiver.name),
			message="your " + str(leave.leave_type.LeaveName) + " leave application was declined by admin",
			notification_type="LEAVE_REJECTED",
			taskId=str(leave.id)
		)
		notification.save()
		existingNotification = Notification.objects.get(taskId = leave.id, notification_type="LEAVE")
		existingNotification.isActive = False
		existingNotification.save()
		return redirect("main:approveLeaves")

	leave = UserLeaveStatus.objects.get(id=pk)
	notification_receiver = Staff.objects.get(id=leave.staff.id)
	leave.status = "Declined by " + str(leave.substitute.name)
	leave.rejected = True
	leave.save()
	notification, was_created = Notification.objects.get_or_create(
		sender = sender,
		reciever=str(notification_receiver.id) + " " + (notification_receiver.name),
		message="your " + str(leave.leave_type.LeaveName) + " leave application was declined by " + str(sender.name),
		notification_type="LEAVE_REJECTED",
		taskId = str(leave.id)
	)
	notification.save()
	existingNotification = Notification.objects.filter(taskId = leave.id, notification_type="LEAVE").all()
	for notification in existingNotification:
		notification.isActive = False
		notification.save()

	return redirect("main:approveLeaves")

def viewprevleaves(request):
	staff=Staff.objects.get(user_obj=request.user)
	all_leaves=UserLeaveStatus.objects.filter(staff=staff,rejected=False,admin_approval=True,substitute_approval=True)
	context={
		'staff':staff,
		'all_leaves':all_leaves,
	}
	return render(request,"leaves/viewprevleaves.html",context)

@login_required	
def complaint(request, pk):
	device = Devices.objects.get(id=pk)
	staff=Staff.objects.get(user_obj=request.user)
	if request.method == 'POST':
		form = ComplaintForm(request.POST)
		if form.is_valid():
			dev = device
			complaint=form.cleaned_data['complaint']
			# staff=Staff.objects.get(user_obj=request.user)	
			complaint, was_created = Complaint.objects.get_or_create(
				created_by=staff,
				device=dev,
				complaint=complaint
			)
			complaint.save()

			notification, was_created = Notification.objects.get_or_create(
				sender=staff, 
				reciever="Lab Technician", 
				message="You have a new Notification in complaints",
				notification_type = 'TECH',
				taskId=complaint.id
			)			
			notification.save()
			labid=Lab.objects.get(lab=device.room).id
			
			return redirect("main:lab",labid)

	else:   #get
		form = ComplaintForm()

		context={
			'staff':staff,
			'form': form,
			'name': device.name.category, 
			'id': device.device_id
		}
		return render(request, 'Complaints/complaints.html', context)





def view_complaints(request):
	staff = Staff.objects.get(user_obj=request.user)
	active_complaints = Complaint.objects.filter(isActive = True).order_by('-date_created')
	resolved_complaints=Complaint.objects.filter(isActive = False).order_by('-date_created')
	# userLabs = Lab.objects.filter(staff=staff).order_by('id').all()
	# # complaint -> device
	# deviceNo = Complaint.objects.filter(complaint = complaint)	
	context = {
		'staff':staff,
		'active_complaints' : active_complaints,
		'resolved_complaints' :resolved_complaints,
	}
	return render(request,'Complaints/view_complaints.html', context)

@login_required
def notifications(request):
	staff = Staff.objects.get(user_obj=request.user)		
	designation = staff.designation.designation
	notifications=[]
	
	if designation == 'Lab Technician':
		notification = Notification.objects.filter(notification_type='TECH').order_by('-time').all()
		notifications.extend(notification)

	receiver=str(staff.id) +' '+staff.name
	notification = Notification.objects.filter(reciever=receiver).order_by('-time').all()
	notifications.extend(notification)

	if request.user.is_staff:
		notification=Notification.objects.filter(reciever=receiver).order_by('-time').all()
		notifications.extend(notification)


	# third type notificatoin baad mein okay? create another if condition
	
	return render(request, "Notifications/notifications.html", {"notifications": notifications, "staff":staff})

@login_required
def handleNotification(request, pk):							# get notification and userleavestatus objects  # compare and render 
													
	staff = Staff.objects.get(user_obj=request.user)	 	# current user		
	notification = Notification.objects.get(id=pk)
	taskId = notification.taskId
	
	# reciever_id= int(notification.reciever.split(' ')[0])

	# get notification get leave from that notification
	# display that leave

	# leave = UserLeaveStatus.objects.get(id=taskId, )
	same = False
	if notification.notification_type == 'LEAVE' or notification.notification_type == 'LEAVE_ACCEPTED' or notification.notification_type == 'LEAVE_REJECTED':
		leave = UserLeaveStatus.objects.get(id=taskId)
		if staff == leave.substitute:
			same = True
		return render(request, "Notifications/leaveRequestStatusNotification.html", {"leave":leave, "notification":notification, "staff":staff, "same":same})

	if notification.notification_type == 'TECH':
		complaint = Complaint.objects.get(id=taskId)
		return render(request, 'Notifications/complaintNotification.html', {"complaint":complaint,"staff":staff,})

	if notification.notification_type == 'TTC':
		pass
	

	return redirect("main:notification")

	
	# # jisne notification receice kro + jo leave mei substitute hai vooo	
	# notification_receiver = Staff.objects.get(id=reciever_id)

	# if notification.notification_type == "LEAVE":
	# 	if request.method == 'POST':
	# 		leaveRequest = UserLeaveStatus.objects.get(staff=notification_receiver, substitute=notification.sender, id=notification.taskId)
	# 		print(leaveRequest.substitute_approval)
	# 		# leaveRequest.status = " waiting for admin to respond"
	# 		# print(leaveRequest)
	# 		return HttpResponse(200)
	# 	else:
	# 		if notification_receiver==notification.sender:
	# 			# if same person gets notification
	# 			leaveRequest = UserLeaveStatus.objects.get(staff=notification_receiver, id=notification.taskId)
	# 			context= {
	# 				"staff": staff,
	# 				"notification" : notification, 
	# 				"leaves": leaveRequest,
	# 				"substitute": notification_receiver,
	# 			}
	# 			return render(request, "notificationConfirm.html", context)
	# 		else:
	# 			leaveRequest = UserLeaveStatus.objects.get(substitute=notification_receiver, id=notification.taskId)
	# 			context = {
	# 				"staff": staff,
	# 				"notification" : notification, 
	# 				"leaves": leaveRequest,
	# 				"substitute": notification_receiver,
	# 				}
	# 			return render(request, "notificationConfirm.html", context)
	
	# if notification.notification_type == "TECH":
	# 	return HttpResponse(202)



@login_required
def lab(request, pk):
	# list of all devices
	staff = Staff.objects.get(user_obj=request.user)
	lab = Lab.objects.get(id=pk)
	devices=Devices.objects.filter(room=lab.lab).order_by("id").all()
	context = {
		'staff':staff,
		'devices': devices,
		'labid': pk,
		'lab': lab,
	}
	return render(request, "Labs/lab.html", context)

@login_required
def add_devices(request, pk):
	staff = Staff.objects.get(user_obj=request.user)
	lab=Lab.objects.get(id=pk)
	room=lab.lab
	if request.method == 'POST':
		form = NewComputerForm(request.POST)
		if form.is_valid():
			deviceid=form.cleaned_data['device_id']
			name = form.cleaned_data['name']
			name=CategoryOfDevice.objects.get(category=name)
			description = form.cleaned_data['description']
			device, was_created=Devices.objects.get_or_create(device_id=deviceid,name = name, description = description,room=room)
			device.save()
			return redirect('main:lab',pk=lab.id)
	else:
		form = NewComputerForm()

		context={
			'staff': staff,
			'form': form,
			'labid':lab,
		}
		return render(request, 'Labs/add_computer.html', context)

@login_required
def resolveConflict(request, pk):
	staff = Staff.objects.get(user_obj=request.user)
	complaint = Complaint.objects.get(id=pk)
	resolver=Staff.objects.get(user_obj=request.user)
	if request.method == 'POST':
		complaint.work_Done=request.POST['workdone']
		complaint.isActive=False
		complaint.who_resolved=resolver
		complaint.save()
		notification = Notification.objects.get(taskId=complaint.id, reciever='Lab Technician')
		notification.isActive = False
		notification.save()
		if request.user.is_staff:
			return redirect("main:adminComplaints")

		else:
			return redirect("main:user_profile")
		
	else:   
		admin_status = request.user.is_staff
		context={
			"staff":staff,
			'complaint':complaint,
			'admin_status': admin_status
		}
		return render(request, 'admin/adminResolveComplaint.html', context)


def adminStaff(request):
	staff = Staff.objects.get(user_obj=request.user)
	if request.user.is_staff:
		staffs = Staff.objects.all().order_by('-designation')
		
		return render(request, "admin/adminStaffs.html", {"staffs":staffs, "staff":staff})
	else:
		return render(request, "pagenotfound.html")

def adminLabs(request):
	staff = Staff.objects.get(user_obj=request.user)
	if request.user.is_staff:
		labs=Lab.objects.all()
		return render(request, "admin/adminLabs.html", {"labs": labs, "staff":staff})
	else:
		return render(request, "pagenotfound.html")

def adminComplaints(request):
	staff = Staff.objects.get(user_obj=request.user)
	if request.user.is_staff:
		complaints = Complaint.objects.all().order_by('id')
		return render(request, "admin/adminComplaints.html", {"complaints":complaints, "staff":staff})
	else:
		return render(request, "pagenotfound.html")

@login_required
def adminLeaves(request):
	staff = Staff.objects.get(user_obj=request.user)
	if request.user.is_staff:
		year = datetime.datetime.now().year
		leavesThisYear = TotalLeaves.objects.filter(year=year).all()

		context = {
			"staff":staff,
			"leavesThisYear": leavesThisYear
		}

		return render(request, "admin/adminLeaves.html", context)
	else:
		return render(request, "pagenotfound.html")

@login_required
def newLeave(request):
	staff=Staff.objects.get(user_obj=request.user)
	if request.method == "POST":
		# create a new leave type and assign it to all the users with their initial count = 0
		form = AddNewLeave(request.POST)
		if form.is_valid():
			leaveName = form.cleaned_data['LeaveName']
			count = form.cleaned_data['count']
			year = form.cleaned_data['year']
			newLeave, was_created = TotalLeaves.objects.get_or_create(
				LeaveName=leaveName, 
				count=count, 
				year=year
			)
			newLeave.save()

			staffs = Staff.objects.all()
			for staff in staffs:
				userLeaveTaken, was_created = UserLeavesTaken.objects.get_or_create(
					staff=staff,
					leave_taken=newLeave,
				)
				userLeaveTaken.save()
			
			return redirect('main:adminLeaves')

	else:
		form = AddNewLeave()
		return render(request, "admin/addLeaveForm.html", {"form":form, "staff":staff})

@login_required
def adminEditLeave(request, pk):
	staff=Staff.objects.get(user_obj=request.user)
	if request.user.is_staff:
		leave = TotalLeaves.objects.get(id=pk)
		if request.method == "POST":
			count = request.POST['leaveCount']
			leave.count = count
			leave.save()
			return redirect('main:adminLeaves')
		else:
			return render(request, "admin/adminEditLeaveForm.html", {"staff":staff, "leave":leave})
	else:
		return render(request, "pagenotfound.html")

@login_required
def removeLeave(request, pk):
	staff = Staff.objects.get(user_obj=request.user)
	if request.user.is_staff:
		leave = TotalLeaves.objects.get(id=pk)
		leave.delete()
		return redirect('main:adminLeaves')
		
	else:
		return render(request, "pagenotfound.html", {"staff":staff})




##Views for timetalbes:->
# 1. viewtimetable  wrt lab
# 2. view timetable wrt professor
def viewtimetable_wrtlab(request,id):
	lab=Lab.objects.get(id=id)
	# print(id)
	# print(lab)
	staff=Staff.objects.get(user_obj=request.user)
	classes=Class.objects.filter(lab=id)
	# print(classes)
	weekdays=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
	timeslots=[]
	h=8
	m=0
	s=0
	time=[]
	while (h!=19) :
		start_time=datetime.time(h,m,s)
		m=m+50
		
		if m>=60:
			h+=1
			m=m%60
		end_time=datetime.time(h,m,s)
		timeslots.append(tuple((start_time,end_time)))
		time.append(start_time)
		# print(start_time , end_time)
		# if(classes[0].starttime==start_time):
		# 	print(classes[0])
		
	# print(timeslots[0][0],timeslots[0][1])
	context={
		'lab':lab,
		'weekdays':weekdays,
		'classes':classes,
		'staff':staff,
		'timeslots':timeslots,
		'time':time,
	}
	return render(request,'Timetable/timetable_wrtlab.html',context)


##2->add krna hia admin ke through:->
#jb admin editkrega:->
#professor->courses->display hoye

def viewLabClasses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	classes=Class.objects.filter(lab=id)
	# print(classes)
	context={
		'staff':staff,
		'classes':classes,
		'labid':id,
	}
	return render(request,'Timetable/viewLabClasses.html',context)

def add_classes(request,id):
	staff = Staff.objects.get(user_obj=request.user)
	form = AddClassForm()
	lab=Lab.objects.get(id=id)
	if request.method == 'POST':
		form = AddClassForm(request.POST)
		if form.is_valid():
			# print(form)
			faculty=form.cleaned_data['faculty']
			# print(faculty.name)
			# faculty=Staff.objects.get(id=faculty)
			course=form.cleaned_data['course']
			# print(course.faculty)
			# course=FacultyCourse.objects.get(id=course)
			group=form.cleaned_data['group']
			# print(group.faculty)
			# group=FacultyGroups.objects.get(id=group)
			day=form.cleaned_data['day']
			starttime=form.cleaned_data['starttime']

			h=starttime.hour
			m=starttime.minute
			m=m+50
			if(m>=60):
				m=m%60
				h+=1
			m=m+50
			if(m>=60):
				m=m%60
				h+=1
			s=0
			endtime=datetime.time(h,m,s)
			activity,was_created= Class.objects.get_or_create(lab=lab,faculty=faculty,course=course,group=group,day=day,starttime=starttime,endtime=endtime)
			activity.save()
			return redirect('main:viewLabClasses', id=id)
	return render(request, 'Timetable/addclass.html', {'form': form, "staff":staff})

def load_courses(request):
	staff = Staff.objects.get(user_obj=request.user)
	faculty_id = request.GET.get('faculty_id')
	# print(faculty_id)
	courses = FacultyCourse.objects.filter(faculty_id=faculty_id).all()
	# print(courses)
	return render(request, 'TimeTable/course_dropdown_list_option.html', {'courses': courses, "staff":staff})
	# return JsonResponse((x), safe=False)

def load_groups(request):
	staff = Staff.objects.get(user_obj=request.user)
	faculty_id = request.GET.get('faculty_id')
	groups = FacultyGroups.objects.filter(faculty_id=faculty_id).all()
	# print(groups)
	return render(request, 'TimeTable/group_dropdown_list_option.html', {'groups': groups, "staff":staff})
	# return JsonResponse(list(groups.values('id', 'name')), safe=False)

def update_class(request, pk,id):
		staff = Staff.objects.get(user_obj=request.user)
		classes = get_object_or_404(Class, pk=pk)
		lab=Lab.objects.get(id=id)
		form = AddClassForm(instance=classes)
		if request.method == 'POST':
			form = AddClassForm(request.POST, instance=classes)
			if form.is_valid():
				faculty=form.cleaned_data['faculty']
				# print(faculty.name)
				# faculty=Staff.objects.get(id=faculty)
				course=form.cleaned_data['course']
				# print(course.faculty)
				# course=FacultyCourse.objects.get(id=course)
				group=form.cleaned_data['group']
				# print(group.faculty)
				# group=FacultyGroups.objects.get(id=group)
				day=form.cleaned_data['day']
				starttime=form.cleaned_data['starttime']

				h=starttime.hour
				m=starttime.minute
				m=m+50
				if(m>=60):
					m=m%60
					h+=1
				m=m+50
				if(m>=60):
					m=m%60
					h+=1
				s=0
				endtime=datetime.time(h,m,s)
				# activity,was_created= Class.objects.get_or_create(lab=lab,faculty=faculty,course=course,group=group,day=day,starttime=starttime,endtime=endtime)
				classes.lab=lab
				classes.faculty=faculty
				classes.course=course
				classes.group=group
				classes.day=day
				classes.starttime=starttime
				classes.endtime=endtime
				classes.save()
				return redirect('main:viewLabClasses', id=id)
		return render(request, 'Timetable/addclass.html', {'form': form, "staff": staff})

def viewgroups(request):
	staff=Staff.objects.get(user_obj=request.user)
	groups=FacultyGroups.objects.filter(faculty=staff)
	context={
		'staff':staff,
		'groups':groups,
	}
	return render(request,'Timetable/viewgroups.html',context)

def viewcourses(request):
	staff=Staff.objects.get(user_obj=request.user)
	courses=FacultyCourse.objects.filter(faculty=staff)
	# print(courses)
	context={
		'staff':staff,
		'courses':courses,
	}
	return render(request,'Timetable/viewcourses.html',context)

def viewfacultyclasses(request):
	staff=Staff.objects.get(user_obj=request.user)
	classes=Class.objects.filter(faculty=staff)
	context={
		'staff':staff,
		'classes':classes,
	}
	return render(request,'Timetable/viewfacultyclasses.html',context)

def ViewFacultyDetails(request):
	admin=Staff.objects.get(user_obj=request.user)
	c1=Category.objects.get(category='Faculty')
	c2=Category.objects.get(category='Student')
	staff=[]
	staff1=Staff.objects.filter(category=c1)
	staff2=Staff.objects.filter(category=c2)
	staff.extend(staff1)
	staff.extend(staff2)
	# groups=FacultyGroups.objects.filter(faculty=staff)
	# classes = Class.objects.filter(faculty = staff).
	context={
		'staff':admin,
		'faculty':staff,
	}
	return render(request,"admin/adminfacultydetails.html",context)

def viewfacultytimetable(request):
	staff=Staff.objects.get(user_obj=request.user)
	classes=Class.objects.filter(faculty=staff)
	weekdays=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
	timeslots=[]
	h=8
	m=0
	s=0
	time=[]
	while (h!=19) :
		start_time=datetime.time(h,m,s)
		m=m+50
		
		if m>=60:
			h+=1
			m=m%60
		end_time=datetime.time(h,m,s)
		timeslots.append(tuple((start_time,end_time)))
		time.append(start_time)
		# print(start_time , end_time)
		# if(classes[0].starttime==start_time):
		# 	print(classes[0])
		
	# print(timeslots[0][0],timeslots[0][1])
	context={
		'lab':lab,
		'weekdays':weekdays,
		'classes':classes,
		'staff':staff,
		'timeslots':timeslots,
		'time':time,
	}
	return render(request,'Timetable/timetable_wrtfaculty.html',context)
	# return render(request,'',context)


def adminviewgroups(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	faculty=Staff.objects.get(id=id)
	groups=FacultyGroups.objects.filter(faculty=faculty)
	context={
		'staff':staff,
		'groups':groups,
		'faculty' : faculty,
	}
	return render(request,'admin/adminviewgroups.html',context)

def adminviewcourses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	faculty=Staff.objects.get(id=id)
	courses=FacultyCourse.objects.filter(faculty=faculty)
	context={
		'staff':staff,
		'courses':courses,
		'faculty':faculty,		
	}
	return render(request,'admin/adminviewcourses.html',context)

def adminviewclasses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	faculty=Staff.objects.get(id=id)
	classes=Class.objects.filter(faculty=faculty)
	context={
		'staff':staff,
		'classes':classes,
		'faculty':faculty,
	}
	return render(request,'admin/adminviewclasses.html',context)

def admindeletegroup(request,id):
	group=FacultyGroups.objects.get(id=id)
	facid=group.faculty.id
	group.delete()
	return redirect('main:adminviewgroups',id=facid)

def admindeletecourses(request,id):
	course=FacultyCourse.objects.get(id=id)
	print(course)
	facid=course.faculty.id
	print(facid)
	course.delete()
	return redirect('main:adminviewcourses',id=facid)
	
def adminaddcourses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	faculty = Staff.objects.get(id = id)
	form = AddCourseForm()
	if request.method == 'POST':
		form = AddCourseForm(request.POST)
		if form.is_valid():
			faculty=form.cleaned_data['faculty']
			course=form.cleaned_data['course']
			course,wascreated=FacultyCourse.objects.get_or_create(faculty=faculty,course=course)
			course.save()
			return redirect('main:adminviewcourses', id=id)
			# return HttpResponse(202)
	return render(request,'admin/adminaddfacultycourses.html',{'form' : form, "staff":staff})
		# return HttpResponse('202')

def adminaddgroup(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	faculty = Staff.objects.get(id = id)
	form = AddGroupForm()
	if request.method == 'POST':
		form = AddGroupForm(request.POST)
		if form.is_valid():
			faculty=form.cleaned_data['faculty']
			group=form.cleaned_data['groups']
			group,wascreated=FacultyGroups.objects.get_or_create(faculty=faculty,groups = group)
			group.save()
			return redirect('main:adminviewgroups', id=id)
			# return HttpResponse(202)
	return render(request,'admin/adminaddfacultygroups.html',{'form' : form, "staff":staff})
		# return HttpResponse('202')


def adminaddfacultyclass(request,id):
	faculty=Staff.objects.get(id=id)
	staff=Staff.objects.get(user_obj=request.user)
	form=AddFacultyClassForm(faculty)
	if request.method == 'POST':
		form=AddFacultyClassForm(faculty,request.POST)
		if form.is_valid():
			print("yay")
			lab=form.cleaned_data['lab']
			course=form.cleaned_data['course']
			group=form.cleaned_data['group']
			day=form.cleaned_data['day']
			starttime=form.cleaned_data['starttime']
			h=starttime.hour
			m=starttime.minute
			m=m+50
			if(m>=60):
				m=m%60
				h+=1
			m=m+50
			if(m>=60):
				m=m%60
				h+=1
			s=0
			endtime=datetime.time(h,m,s)
			activity,was_created= Class.objects.get_or_create(lab=lab,faculty=faculty,course=course,group=group,day=day,starttime=starttime,endtime=endtime)
			activity.save()
			return redirect('main:adminviewclasses', id=id)
	context={
		'staff':staff,
		'form':form,
		'faculty':faculty,
	}
	return render(request,'admin/adminaddfacultyclasses.html',context)



def adminupdatefacultyclass(request,id,pk):
	staff=Staff.objects.get(user_obj=request.user)
	classes = get_object_or_404(Class, pk=pk)
	faculty=Staff.objects.get(id=id)
	form = AddFacultyClassForm(faculty,instance=classes)
	if request.method == 'POST':
		form = AddFacultyClassForm(faculty,request.POST, instance=classes)
		if form.is_valid():
			print(form)
			lab=form.cleaned_data['lab']
			# print(faculty.name)
			# faculty=Staff.objects.get(id=faculty)
			course=form.cleaned_data['course']
			# print(course.faculty)
			# course=FacultyCourse.objects.get(id=course)
			group=form.cleaned_data['group']
			# print(group.faculty)
			# group=FacultyGroups.objects.get(id=group)
			day=form.cleaned_data['day']
			starttime=form.cleaned_data['starttime']

			h=starttime.hour
			m=starttime.minute
			m=m+50
			if(m>=60):
				m=m%60
				h+=1
			m=m+50
			if(m>=60):
				m=m%60
				h+=1
			s=0
			endtime=datetime.time(h,m,s)
			# activity,was_created= Class.objects.get_or_create(lab=lab,faculty=faculty,course=course,group=group,day=day,starttime=starttime,endtime=endtime)
			classes.lab=lab
			classes.faculty=faculty
			classes.course=course
			classes.group=group
			classes.day=day
			classes.starttime=starttime
			classes.endtime=endtime
			classes.save()
			return redirect('main:adminviewclasses', id=id)
	return render(request, 'admin/adminaddfacultyclasses.html', {'staff':staff,'form': form})

def viewinventory(request):
	staff=Staff.objects.get(user_obj=request.user)
	inventory=StaffInventory.objects.filter(staff=staff).order_by('id')
	print(inventory)
	context={
		'staff':staff,
		'inventory':inventory,
	}
	return render(request,'inventory.html',context, {"staff":staff})

