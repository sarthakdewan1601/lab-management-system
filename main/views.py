import threading
import datetime
from django.conf import settings
from email.message import EmailMessage
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
import threading
import datetime
import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes,  force_text
from main.utils import generate_token, getNumberOfDays, checkLeaveAvailability
from django.core.mail import EmailMessage

from .models import *
from .forms import *
from .filters import *


UserModel = get_user_model()

class EmailThread(threading.Thread):		#creating email thread
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)
    def run(self):
        self.email.send()

def get_notifications(id):
	current_user=Staff.objects.get(id=id)
	designation=current_user.designation.designation
	notifications=[]
	
	if designation == 'Lab Technician':
		notification = Notification.objects.filter(notification_type='TECH',isActive=True,checked=False).order_by('-time').all()
		notifications.extend(notification)

	receiver=str(current_user.id) +' '+current_user.name
	notification = Notification.objects.filter(reciever=receiver,isActive=True,checked=False).order_by('-time').all()
	notifications.extend(notification)

	if designation == 'System Analyst' or designation == 'Lab Supervisor':
		notification=Notification.objects.filter(reciever='admin',isActive=True,checked=False).order_by('-time').all()
		notifications.extend(notification)
	return len(notifications)

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
		# print("Yooo")
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(email=uid)
	except Exception as err:
		print(err)
		pass
	# print(user)
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
		# print(name, category1, designation, agency, mobile_number)
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
			print("in login_request")
			user = User.objects.get(email=email)
			if not user.is_email_verified:
				messages.error(request, "Your email is not verified, please verify using the link provided in mail")
				return redirect('main:login')
			if not user.check_password(password):
				messages.error(request, "Entered password is not correct, try again")
				return redirect('main:login')
			
			# if request.session.session_key:
			# 	return redirect('main:user_profile')
			else:
				user.save()
				staff = Staff.objects.get(email=user.email)
				messages.success(request, f"Welcome {staff.name}")
				login(request, user)
				print("hi,we are logged in")
				return redirect("main:user_profile")

		except User.DoesNotExist:
			print("some error occured")
			current_site = get_current_site(request)
			messages.error(request, f"This email is not registered. Please signup first")
			user = None
			return redirect('main:login')

	return render(request, "accounts/login.html", )

@login_required
def logout_request(request, id):
	staff = Staff.objects.get(id=id)
	userEmail = staff.email
	user = User.objects.get(email=userEmail)
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
					if request.session.session_key:
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
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		a = User.objects.get(email=request.user)
		print(a)
		return render(request, "admin/dashboard.html", {"staff":staff,'notification_count':notification_count,})

	staff = Staff.objects.get(user_obj=request.user)
	userLabs = Lab.objects.filter(staff=staff).order_by('id').all()
	return render(request, "home.html", {'userLabs': userLabs, "staff":staff, 'messages': messages.get_messages(request),'notification_count':notification_count,})

	# except:
	# 	tech = Technician.objects.get(tech_id=request.user.username)
	# 	complaints = Complaint.objects.all()
	# 	context = { "complaints": complaints}
	# 	return render(request, "tech_dashboard.html", context)

@login_required
def user_profile_details(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	return render(request, "userProfiles/user_profile.html", {'staff':staff,'notification_count':notification_count,})

@login_required
def user_profile(request):
	# print("sarthak")
	userEmail = request.user.email
	staff = Staff.objects.get(email=userEmail)
	notification_count=get_notifications(staff.id)
	print(notification_count)

	if staff.category.category == "Lab Staff":
		# print("hi")
		# for admin 
		print(staff.designation.designation)
		if staff.designation.designation == "System Analyst" or staff.designation.designation == "Lab Supervisor":
			# labs = Lab.objects.get().all()
			#notifications=Notification.objects.filter(reciever='admin').all()
			return render(request, "admin/dashboard.html", {"staff":staff,'notification_count':notification_count,})

		
		if staff.designation.designation == "Lab Associate":
			pass

		
		if staff.designation.designation == "Lab Attendant":
			staff_1 = Staff.objects.get(user_obj=request.user)
			userLabs = Lab.objects.filter(staff=staff).order_by('id').all()

			#leaves=Leaves.objects.get(staff=staff)
			context = {
				'userLabs' : userLabs,
				'staff'	: staff_1,
				'notification_count':notification_count,
			}
			return render(request, 'userProfiles/lab_attendent.html',context)
			# pass
			
		if staff.designation.designation == "Lab Technician":
			print("Hello")
			staff = Staff.objects.get(user_obj=request.user)			
			complaints = Complaint.objects.filter(isActive=True).all()
			current_notifications = Notification.objects.filter(reciever='Lab Technician').order_by('id').all()



			context = { 
				"staff":staff,
				"complaints": complaints,
				"notifications": current_notifications,
				'notification_count':notification_count,
			}
			return redirect('main:viewcomplaints')
			
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
			'notification_count':notification_count,
		}
		return render(request,"userProfiles/faculty.html",context)
		

@login_required
def editProfile(request, pk):
	staff = Staff.objects.get(id=pk)	
		
	if request.user.is_staff:
		admin=Staff.objects.get(user_obj=request.user)
		notification_count=get_notifications(admin.id)
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
				"agency":agency,
				'notification_count':notification_count,
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
			notification_count=get_notifications(staff.id)
			context = {
				"staff": staff,
				'notification_count':notification_count,
			}
			return render(request, "userProfiles/edit_profile.html", context)


@login_required
def userLeaves(request):
	staff = Staff.objects.get(user_obj=request.user)	
	notification_count=get_notifications(staff.id)
	year = datetime.datetime.now().year
	leavesThisYear = TotalLeaves.objects.filter(year=year).all()
	
	userLeavesTaken = UserLeavesTaken.objects.filter(staff=staff)
	
	# print(userLeavesTaken)
	context = {
		"staff":staff,
		"totalLeaves" : leavesThisYear,
		"year": year,
		"userLeavesTaken":userLeavesTaken,
		'notification_count':notification_count,
	}
	return render(request, "leaves/leaves.html", context)

@login_required
def requestleave(request):
	staff= Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.method == 'POST':
		form=request.POST
		# form data
		applicant=form['applicant']
		leaveSelection=form['leaveSelection']
		fromDate=form['fromDate']
		substitute=form['substitute']
		reason=form['reason']

		# processed data
		year=datetime.datetime.now().year
		month=datetime.datetime.now().month
		leave_type=TotalLeaves.objects.get(id=leaveSelection)
		substituteName = Staff.objects.get(id=substitute)
		multipleLeaves = None
		try:
			multipleLeaves = form['multipleLeaveCheckbox']
		except Exception as e:
			print(e)

		if multipleLeaves is not None:
			toDate=form['toDate']
			countOfLeaves = getNumberOfDays(fromDate, toDate)
			leaveAvailability, leaveAvailabilityCount, leaveAvailabilityMessage = checkLeaveAvailability(leave_type, staff, countOfLeaves)
			if leaveAvailability:
				fromDateMonth = fromDate.split("-")[1]
				userstatus,wascreated=UserLeaveStatus.objects.get_or_create(staff=staff,leave_type=leave_type,from_date=fromDate,to_date=toDate, reason=reason,substitute=substituteName, month=fromDateMonth, year=year)
				userstatus.save()
				##notification
				customMessage1 = staff.name + " requested for leave"
				notification, was_created = Notification.objects.get_or_create(
					sender=staff, 
					reciever=str(substituteName.id)+' '+substituteName.name, 
					message=customMessage1,
					notification_type = 'LEAVE',
					taskId = userstatus.id
				)
				notification.save()
				# print(notification)
				customMessage2 = "your request for " + leave_type.LeaveName + " leave is placed"
				notification, was_created = Notification.objects.get_or_create(
					sender=staff, 
					reciever=str(staff.id) + ' ' + staff.name, 
					message=customMessage2,
					notification_type = 'LEAVE',
					taskId=userstatus.id
				) 
				# print(notification)
				notification.save()
				return redirect('main:userLeaves')
			else:
				messages.error(request, f'You cannot take more than {leaveAvailabilityCount} leaves of this type')
				return redirect("main:requestleave")

		else:
			leaveAvailability, leaveAvailabilityCount, leaveAvailabilityMessage = checkLeaveAvailability(leave_type, staff, 1)
			if leaveAvailability:
				year=datetime.datetime.now().year
				fromDateMonth = fromDate.split("-")[1]
				userstatus,wascreated=UserLeaveStatus.objects.get_or_create(staff=staff, leave_type=leave_type, from_date=fromDate, to_date=fromDate, reason=reason, substitute=substituteName, month=fromDateMonth, year=year)
				userstatus.save()
				##notification

				customMessage1 = staff.name + " requested for leave"
				notification, was_created = Notification.objects.get_or_create(
					sender=staff, 
					reciever=str(substituteName)+' '+substituteName.name, 
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
				return redirect('main:userLeaves')
			else:
				messages.error(request, f'You cannot take leave')
				return redirect("main:requestleave")

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
		substitutes = Staff.objects.exclude(name=staff.name).all()
		context={
			'staff':staff,
			'totalLeavesCurrYear': totalLeavesCurrYear,
			'substitutes': substitutes,
			'notification_count':notification_count,
		}
	
		return render(request,"leaves/leaverequest.html",context)

@login_required
def checkLeaveStatus(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	# print(staff)

	pendingRequests = UserLeaveStatus.objects.filter(staff=staff).order_by("-id")
	# get all the pending requests 
	context = {
		'staff':staff,
		"pendingRequests": pendingRequests,
		'notification_count':notification_count,
	}
	return render(request, "leaves/leaveRequestStatus.html", context)

@login_required
def checkLeaveStatusId(request, pk):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	leaveRequest = UserLeaveStatus.objects.get(id=pk)
	getTotalLeaveDays = 1
	if leaveRequest.to_date:
		getTotalLeaveDays = getNumberOfDays(leaveRequest.from_date, leaveRequest.to_date)

	context = {
		'staff':staff,
		'leaveRequest':leaveRequest,
		'getTotalLeaveDays': getTotalLeaveDays,
		'notification_count':notification_count,
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
	notification_count=get_notifications(staff.id)
	#for admin
	if request.user.is_staff:
		#return HttpResponse(201)
		context={
			'staff':staff,
			'notification_count':notification_count,
		}
		return render(request,'admin/adminLeaveApproval.html',context)

	# get leaves in which current user is substitute

	leaves = UserLeaveStatus.objects.filter(substitute=staff).order_by("-from_date")
	context = {
		'staff':staff,
		"leaves": leaves,
		'notification_count':notification_count,
	}
	return render(request, 'leaves/leaveapproval.html', context)

@login_required
def adminApprovedLeaves(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		approvedleaves=UserLeaveStatus.objects.filter(substitute_approval=True,admin_approval=True,rejected=False)
		context={
			'staff':staff,
			"approvedleaves":approvedleaves,
			'notification_count':notification_count,
		}
		return render(request,'admin/adminApprovedLeaves.html',context)
	else:
		return render(request,'pagenotfound.html',{})

@login_required
def adminRequestedLeaves(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		requestedleaves=UserLeaveStatus.objects.filter(substitute_approval=True,admin_approval=False,rejected=False)
		context={
			'staff':staff,
			"requestedleaves":requestedleaves,
			'notification_count':notification_count,
		}
		return render(request,'admin/adminRequestedLeaves.html',context)
	else:
		return render(request,'pagenotfound.html',{})

@login_required
def adminRejectedLeaves(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		rejectedleaves=UserLeaveStatus.objects.filter(substitute_approval=True,admin_approval=False,rejected=True)
		print(rejectedleaves)
		context={
			'staff':staff,
			"rejectedleaves":rejectedleaves,
			'notification_count':notification_count,
		}
		return render(request,'admin/adminRejectedLeaves.html',context)
	else:
		return render(request,'pagenotfound.html',{})

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
			message="Your " + str(leave.leave_type.LeaveName) + " leave application was approved by admin",
			notification_type="LEAVE_ACCEPTED",
			taskId=str(leave.id)
		)
		notification.save()

		
		# 1) ki user leaves taken hai uss user ka usko update 
		userleavetaken = UserLeavesTaken.objects.get(staff=leave.staff,leave_taken=leave.leave_type)
		getTotalLeaveDays = 1
		if leave.to_date:
			getTotalLeaveDays = getNumberOfDays(leave.from_date, leave.to_date)
		
		userleavetaken.count += getTotalLeaveDays
		userleavetaken.save()
		
		return redirect("main:adminRequestedLeaves")

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
		existingNotification = Notification.objects.filter(taskId = leave.id, notification_type="LEAVE")
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

@login_required
def viewprevleaves(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	all_leaves=UserLeaveStatus.objects.filter(staff=staff,rejected=False,admin_approval=True,substitute_approval=True)
	context={
		'staff':staff,
		'all_leaves':all_leaves,
		'notification_count':notification_count,
	}
	return render(request,"leaves/viewprevleaves.html",context)

@login_required	
def complaint(request, pk):
	device = Devices.objects.get(id=pk)
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.method == 'POST':
		form = ComplaintForm(request.POST)
		if form.is_valid():
			dev = device
			dev.is_working=False
			dev.save()
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
			room=device.room
			if room.is_lab and device.in_inventory==False:
				labid=Lab.objects.get(lab=device.room).id
				return redirect("main:lab",labid)
			else:
				return redirect("main:viewinventory")

	else:   #get
		form = ComplaintForm()

		context={
			'staff':staff,
			'form': form,
			'name': device.name.category, 
			'id': device.device_id,
			'notification_count':notification_count,
		}
		return render(request, 'Complaints/complaints.html', context)




@login_required
def view_complaints(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	active_complaints = Complaint.objects.filter(isActive = True).order_by('-created_at')
	resolved_complaints=Complaint.objects.filter(isActive = False).order_by('-created_at')
	# userLabs = Lab.objects.filter(staff=staff).order_by('id').all()
	# # complaint -> device
	# deviceNo = Complaint.objects.filter(complaint = complaint)	
	context = {
		'staff':staff,
		'active_complaints' : active_complaints,
		'resolved_complaints' :resolved_complaints,
		'notification_count':notification_count,
	}
	return render(request,'Complaints/view_complaints.html', context)

@login_required
def notifications(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)		
	designation = staff.designation.designation
	notifications=[]
	
	if designation == 'Lab Technician':
		notification = Notification.objects.filter(notification_type='TECH',isActive=True).order_by('-time').all()
		notifications.extend(notification)

	receiver=str(staff.id) +' '+staff.name
	notification = Notification.objects.filter(reciever=receiver,isActive=True).order_by('-time').all()
	notifications.extend(notification)

	if request.user.is_staff:
		notification=Notification.objects.filter(reciever='admin',isActive=True).order_by('-time').all()
		notifications.extend(notification)
	# count=len(notifications)

	# third type notificatoin baad mein okay? create another if condition
	
	return render(request, "Notifications/notifications.html", {"notifications": notifications, "staff":staff,'notification_count':notification_count,})

@login_required
def handleNotification(request, pk):							# get notification and userleavestatus objects  # compare and render 
													
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)	 	# current user		
	notification = Notification.objects.get(id=pk)
	# print(notification.notification_type)
	# print(notification.isActive)
	if notification.isActive==False:
		return redirect('main:notification')

	# notification.isActive=False
	notification.checked = True
	
	notification.save()
	taskId = notification.taskId
	
	# reciever_id= int(notification.reciever.split(' ')[0])

	# get notification get leave from that notification
	# display that leave

	# leave = UserLeaveStatus.objects.get(id=taskId, )
	same = False
	if notification.notification_type == 'LEAVE' or notification.notification_type == 'LEAVE_ACCEPTED' or notification.notification_type == 'LEAVE_REJECTED':
		leave = UserLeaveStatus.objects.get(id=taskId)
		print('hi')
		if staff == leave.substitute:
			same = True
		return render(request, "Notifications/leaveRequestStatusNotification.html", {"leave":leave, "notification":notification, "staff":staff, "same":same,'notification_count':notification_count,})

	if notification.notification_type == 'TECH':
		complaint = Complaint.objects.get(id=taskId)
		return render(request, 'Notifications/complaintNotification.html', {"complaint":complaint,"staff":staff,'notification_count':notification_count,})


	if notification.notification_type== 'TECH_RESOLVE':
		complaint=Complaint.objects.get(id=taskId)
		context={
			'staff':staff,
			'complaint':complaint,
			'notification_count':notification_count,
		}
		return render(request,'Notifications/resolvedcomplaintstatus.html',context)
	if notification.notification_type == 'INVENTORY' and notification.reciever=='admin':
		fac=Staff.objects.get(id=taskId)
		inventory_devices=StaffInventory.objects.filter(staff=fac)
		inventory_devices_to_return=StaffInventory.objects.filter(staff=fac,is_requested_for_return=True)
		return render(request,"admin/adminviewinventory.html",{"staff":staff,"inventorystaff":fac,"devices":inventory_devices,"devicestoreturn":inventory_devices_to_return,'notification_count':notification_count,})

	if notification.notification_type == 'INVENTORY' :
		fac=Staff.objects.get(id=taskId)
		return redirect('main:viewinventory')

	

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
	notification_count=get_notifications(staff.id)
	lab = Lab.objects.get(id=pk)
	devices=Devices.objects.filter(room=lab.lab).order_by("id").all()
	context = {
		'staff':staff,
		'devices': devices,
		'labid': pk,
		'lab': lab,
		'notification_count':notification_count,
	}
	return render(request, "Labs/lab.html", context)

@login_required
def add_devices(request, pk):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	lab=Lab.objects.get(id=pk)
	room=lab.lab
	# print('hi')
	if request.method == 'POST':
		form = NewComputerForm(request.POST)
		print('hi')
		# print(form.is_valid()
		if form.is_valid():
			# print('hi again')
			deviceid=form.cleaned_data['device_id']
			name = form.cleaned_data['name']
			name=CategoryOfDevice.objects.get(category=name)
			description = form.cleaned_data['description']
			device, was_created=Devices.objects.get_or_create(device_id=deviceid,name = name, description = description,room=room)
			device.save()
			return redirect('main:lab',pk=lab.id)
		else:
			messages.error(request, "This Device Already exists")
			form = NewComputerForm()

			context = {
				'staff': staff,
				'form': form,
				'labid':lab,
				'notification_count':notification_count,
			}
			return render(request, 'Labs/add_computer.html', context)
	else:
		form = NewComputerForm()
		context={
			'staff': staff,
			'form': form,
			'labid':lab,
			'notification_count':notification_count,
		}
		return render(request, 'Labs/add_computer.html', context)

@login_required
def resolveConflict(request, pk):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	complaint = Complaint.objects.get(id=pk)
	resolver=Staff.objects.get(user_obj=request.user)
	if request.method == 'POST':
		complaint.work_Done=request.POST['workdone']
		complaint.isActive=False
		complaint.who_resolved=resolver
		complaint.save()
		device=Devices.objects.get(id=complaint.device.id)
		complaints=Complaint.objects.filter(device=device,isActive=True)
		if(len(list(complaints))==0):
			device.is_working=True
		device.save()
		notification = Notification.objects.get(taskId=complaint.id, reciever='Lab Technician')
		# notification.isActive = False
		notification.expired=True

		notification_resolve, was_created = Notification.objects.get_or_create(
				sender=staff, 
				reciever=str(complaint.created_by.id)+" " + complaint.created_by.name, 
				message="Complaint, " + '"' +complaint.complaint + '"' + ', complaintID:'+str(complaint.id) +", has been resolved",
				notification_type = 'TECH_RESOLVE',
				taskId=complaint.id
			)			

		notification.save()
		notification_resolve.save()

		if request.user.is_staff:
			return redirect("main:adminComplaints")

		else:
			return redirect("main:user_profile")
		
	else:   
		admin_status = request.user.is_staff
		context={
			"staff":staff,
			'complaint':complaint,
			'admin_status': admin_status,
			'notification_count':notification_count,
		}
		return render(request, 'admin/adminResolveComplaint.html', context)

def viewdevicecomplaints(request,id):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	device=Devices.objects.get(id=id)
	active_compaints=Complaint.objects.filter(device=device,isActive=True,created_by=staff)
	resolved_complaints=Complaint.objects.filter(device=device,isActive=False,created_by=staff)
	context={
		'staff':staff,
		'device':device,
		'notification_count':notification_count,
		'active_complaints':active_compaints,
		'resolved_complaints':resolved_complaints,
	}
	return render(request,'Complaints/viewdevicecomplaints.html',context)



	 

@login_required
def adminStaff(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		staffs = Staff.objects.all().order_by('-designation')
		
		return render(request, "admin/adminStaffs.html", {"staffs":staffs, "staff":staff,'notification_count':notification_count,})
	else:
		return render(request, "pagenotfound.html")

def adminLabs(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		labs=Lab.objects.all()
		return render(request, "admin/adminLabs.html", {"labs": labs, "staff":staff,'notification_count':notification_count,})
	else:
		return render(request, "pagenotfound.html")

def adminComplaints(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		return render(request, "admin/adminComplaints.html", {"staff":staff,'notification_count':notification_count,})
	else:
		return render(request, "pagenotfound.html")

def adminactivecomplaints(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		activecompliants=Complaint.objects.filter(isActive=True)
		return render(request, "admin/adminactiveComplaints.html", {"complaints":activecompliants,"staff":staff,'notification_count':notification_count,})
	else:
		return render(request, "pagenotfound.html")


def adminresolvedcomplaints(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		resolvedcompliants=Complaint.objects.filter(isActive=False)
		return render(request, "admin/adminresolvedcomplaints.html", {"complaints":resolvedcompliants,"staff":staff,'notification_count':notification_count,})
	else:
		return render(request, "pagenotfound.html")




@login_required
def adminLeaves(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		year = datetime.datetime.now().year
		leavesThisYear = TotalLeaves.objects.filter(year=year).all()

		context = {
			"staff":staff,
			"leavesThisYear": leavesThisYear,
			'notification_count':notification_count,
		}

		return render(request, "admin/adminLeaves.html", context)
	else:
		return render(request, "pagenotfound.html")

@login_required
def newLeave(request):
	if not request.user.is_staff:
		return render(request, "pagenotfound.html")

	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
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
		return render(request, "admin/addLeaveForm.html", {"form":form, "staff":staff,'notification_count':notification_count,})


@login_required
def leaveUsersHistory(request):
	if not request.user.is_staff:
		return render(request, "pagenotfound.html")
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	year = datetime.datetime.now().year
	leave_types = TotalLeaves.objects.filter(year=year)
	# allLeavesTaken = UserLeavesTaken.objects.all();  # count
	# allLeavesStatus = UserLeaveStatus.objects.all(); # date


	if request.method == "POST":
		form = request.POST
		# print(form)
		monthForm = form["month"]
		year = form["year"]
		type = form['leaveType']
		download=''
		try:
			download = form['download']
		except:
			pass
		
		all = "------"
		leaveType = ''
		allLeavesStatus = None
		if type == '':
			all = "All"
			leaveType = TotalLeaves.objects.all()
			allLeavesStatus = UserLeaveStatus.objects.filter(month=monthForm, year=year).order_by("-id")
		else:
			leaveType = TotalLeaves.objects.get(id=type)
			all = leaveType.LeaveName
			allLeavesStatus = UserLeaveStatus.objects.filter(month=monthForm, year=year, leave_type=leaveType).order_by("-id")


		leaves = []
		for leave in allLeavesStatus:
			if leave.admin_approval:
				leaves.append(leave)

		# make query set

		currLeaveCount = []
		for leave in leaves:
			array = {};
			currUser = leave.staff
			currType = leave.leave_type
			leaveTakenObj = UserLeavesTaken.objects.get(staff=currUser, leave_taken=currType)
			# currLeaveCount.append(leaveTakenObj)
			totalLeavesAssigned = leave.leave_type.count
			totalLeavesTakenOfThisType = leaveTakenObj.count
			leavesThisMonth = UserLeaveStatus.objects.filter(
				staff=currUser, 
				month=monthForm,
				leave_type=currType,
				admin_approval=True	
			)
			countDays = 0
			for a in leavesThisMonth:
				countDays += getNumberOfDays(a.from_date, a.to_date)
			days=[]
			for x in leavesThisMonth:
				if x.from_date==x.to_date:
					start=int(str(x.from_date)[-2:])
					if start not in days:
						days.append(start)
				else:
					start=int(str(x.from_date)[-2:])
					end=int(str(x.to_date)[-2:])
					while start<=end:
						if start not in days:
							days.append(start)
						start+=1

			# print(days)
			s=""
			for i in days:
				s+=str(i)+','
			s=s[:-1]


			array['leaveTakenObj'] = leaveTakenObj
			array['totalLeavesAssigned']=totalLeavesAssigned
			array['totalLeavesTakenOfThisType']=totalLeavesTakenOfThisType
			array['leavesThisMonth'] = countDays
			array['days']=s
			currLeaveCount.append(array)

		if download:
			response = HttpResponse(content_type='text/csv')

			writer = csv.writer(response)
			writer.writerow(['Name', 'Designation', 'Leave Type', 'Total Leaves','Total Leaves Taken','Leaves Taken this month','Leave Days'])

			for x in currLeaveCount:
				arr=[]
				arr.append(x['leaveTakenObj'].staff.name)
				arr.append(x['leaveTakenObj'].staff.designation.designation)
				arr.append(x['leaveTakenObj'].leave_taken.LeaveName)
				arr.append(x['totalLeavesAssigned'])
				arr.append(x['totalLeavesTakenOfThisType'])
				arr.append(x['leavesThisMonth'])
				arr.append(x['days'])
				writer.writerow(arr)

			response['Content-Disposition'] = 'attachment; filename="leaves_this_month.csv"'

			return response
			
			

		defaultParams = {
			'year':year,
			'month':str(monthForm),
			'leavee': all
		}
		context = {
			"staff":staff,
			'notification_count':notification_count,
			"leaves": leaves,
			"leave_types": leave_types,
			"defaultParams": defaultParams,
			"leaveObjs": currLeaveCount,
		}
		return render(request, "admin/adminLeavesHistory.html", context)

	else:
		year=datetime.datetime.now().year
		month=datetime.datetime.now().month

		allLeavesTaken = UserLeavesTaken.objects.all();  # count
		allLeavesStatus = UserLeaveStatus.objects.filter(month=month, year=year).order_by("-id")

		leaves = []
		for leave in allLeavesStatus:
			if leave.admin_approval:
				leaves.append(leave)
		context = {
			"staff":staff,
			'notification_count':notification_count,
			"leaves": leaves,
			"leave_types": leave_types
		}
		return render(request, "admin/adminLeavesHistory.html", context)

@login_required
def adminEditLeave(request, pk):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.user.is_staff:
		leave = TotalLeaves.objects.get(id=pk)
		if request.method == "POST":
			count = request.POST['leaveCount']
			leave.count = count
			leave.save()
			##
			return redirect('main:adminLeaves')
		else:
			return render(request, "admin/adminEditLeaveForm.html", {"staff":staff, "leave":leave,'notification_count':notification_count,})
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
@login_required
def viewtimetable_wrtlab(request,id):
	lab=Lab.objects.get(id=id)
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	classes=Class.objects.filter(lab=id)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_cl=[]
	for cl in classes:
		if cl.faculty_group_course.group.groups.group_year==year and cl.faculty_group_course.group.groups.semester_type==sem:
			curr_cl.append(cl)
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
		'classes':curr_cl,
		'staff':staff,
		'timeslots':timeslots,
		'time':time,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/timetable_wrtlab.html',context)


##2->add krna hia admin ke through:->
#jb admin editkrega:->
#professor->courses->display hoye
@login_required
def viewLabClasses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	classes=Class.objects.filter(lab=id)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_cl=[]
	for cl in classes:
		if cl.faculty_group_course.group.groups.group_year==year and cl.faculty_group_course.group.groups.semester_type==sem:
			curr_cl.append(cl)
	context={
		'staff':staff,
		'classes':curr_cl,
		'labid':id,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/viewLabClasses.html',context)

@login_required
def add_classes(request,id):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	form = AddClassForm()
	lab=Lab.objects.get(id=id)
	if request.method == 'POST':
		form = AddClassForm(request.POST)
		if form.is_valid():
			# print(form)
			faculty=form.cleaned_data['faculty']
			# print(faculty.name)
			# faculty=Staff.objects.get(id=faculty)
			group_course=form.cleaned_data['faculty_group_course']
			# print(group.faculty)
			# group=FacultyGroups.objects.get(id=group)
			day=form.cleaned_data['day']
			starttime=form.cleaned_data['starttime']
			tools_used=form.cleaned_data['tools_used']
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
			activity,was_created= Class.objects.get_or_create(lab=lab,faculty=faculty,faculty_group_course=group_course,day=day,starttime=starttime,endtime=endtime,tools_used=tools_used)
			activity.save()
			return redirect('main:viewLabClasses', id=id)
	return render(request, 'Timetable/addclass.html', {'form': form, "staff":staff,'notification_count':notification_count,})

@login_required
def load_courses(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty_id = request.GET.get('faculty_id')
	# print(faculty_id)
	courses = FacultyCourse.objects.filter(faculty_id=faculty_id).all()
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_courses=[]
	for course in courses:
		if course.course.course_year==year and course.course.semester_type==sem:
			curr_courses.append(course)
	
	return render(request, 'TimeTable/course_dropdown_list_option.html', {'courses': curr_courses, "staff":staff,'notification_count':notification_count,})
	# return JsonResponse((x), safe=False)

@login_required
def load_groups(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty_id = request.GET.get('faculty_id')
	groups = FacultyGroups.objects.filter(faculty_id=faculty_id).all()
	# print(groups)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_groups=[]
	for group in groups:
		if group.groups.group_year==year and group.groups.semester_type==sem:
			curr_groups.append(group)
	return render(request, 'TimeTable/group_dropdown_list_option.html', {'groups': curr_groups, "staff":staff,'notification_count':notification_count,})
	# return JsonResponse(list(groups.values('id', 'name')), safe=False)

@login_required
def load_groupcourses(request):
	staff = Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty_id = request.GET.get('faculty_id')
	groupcourses = GroupCourse.objects.filter(faculty_id=faculty_id).all()
	# print(groups)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_gp=[]
	for gc in groupcourses:
		if gc.group.groups.group_year==year and gc.group.groups.semester_type==sem:
			curr_gp.append(gc)
	return render(request, 'TimeTable/groupcourse_dropdown_list_option.html', {'groupcourse': curr_gp, "staff":staff,'notification_count':notification_count,})
	# return JsonResponse(list(groups.values('id', 'name')), safe=False)

@login_required
def update_class(request, pk,id):
		staff = Staff.objects.get(user_obj=request.user)
		notification_count=get_notifications(staff.id)
		classes = get_object_or_404(Class, pk=pk)
		lab=Lab.objects.get(id=id)
		form = AddClassForm(instance=classes)
		if request.method == 'POST':
			form = AddClassForm(request.POST, instance=classes)
			if form.is_valid():
				faculty=form.cleaned_data['faculty']
				# print(faculty.name)
				# faculty=Staff.objects.get(id=faculty)
				fgc=form.cleaned_data['faculty_group_course']
				# print(course.faculty)
				# course=FacultyCourse.objects.get(id=course)
				# print(group.faculty)
				# group=FacultyGroups.objects.get(id=group)
				day=form.cleaned_data['day']
				starttime=form.cleaned_data['starttime']
				tools_used=form.cleaned_data['tools_used']

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
				classes.faculty_group_course=fgc
				classes.day=day
				classes.starttime=starttime
				classes.endtime=endtime
				classes.tools_used=tools_used
				classes.save()
				return redirect('main:viewLabClasses', id=id)
		return render(request, 'Timetable/addclass.html', {'form': form, "staff": staff,'notification_count':notification_count,})

@login_required
def viewgroups(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	groups=FacultyGroups.objects.filter(faculty=staff)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_groups=[]
	for group in groups:
		if group.groups.group_year==year and group.groups.semester_type==sem:
			curr_groups.append(group)
	context={
		'staff':staff,
		'groups':curr_groups,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/viewgroups.html',context)

@login_required
def viewcourses(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	courses=FacultyCourse.objects.filter(faculty=staff)
	# print(courses)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	
	curr_courses=[]
	for course in courses:
		if course.course.course_year==year and course.course.semester_type==sem:
			curr_courses.append(course)
	context={
		'staff':staff,
		'courses':curr_courses,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/viewcourses.html',context)

@login_required
def viewfacultyclasses(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	classes=Class.objects.filter(faculty=staff)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_cl=[]
	for cl in classes:
		if cl.faculty_group_course.group.groups.group_year==year and cl.faculty_group_course.group.groups.semester_type==sem:
			curr_cl.append(cl)
	context={
		'staff':staff,
		'classes':curr_cl,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/viewfacultyclasses.html',context)


@login_required
def addFaculty(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	if request.method == "POST":
		form = request.POST
		name = form['name']
		email = form['email']
		mobile_number = form['mobile_number']
		designation = form['designation']
		agency = form['agency']
		initials = form['initials']
		password = 'Qwerty!@#$%pass@123'
		agen = Agency.objects.get(agency=agency)
		cat = Category.objects.get(category="Faculty")
		des = Designation.objects.get(designation=designation)
		user = User.objects.create_user(email, password, is_active=True)
		user.is_email_verified=True
		user.save()
		staff, was_created = Staff.objects.get_or_create(user_obj=user, name=name, email=email, mobile_number=mobile_number, designation=des, agency=agen, category=cat, initials=initials)
		staff.save()
		return redirect("main:adminfacultydetails")
	else:
		return render(request, "admin/addFaculty.html", {'staff':staff,'notification_count':notification_count,})

@login_required
def ViewFacultyDetails(request):
	admin=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(admin.id)
	if admin.designation.designation == 'Lab Attendant' or request.user.is_staff:
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
			'notification_count':notification_count,
		}
		return render(request,"admin/adminfacultydetails.html",context)
	else:
		return render(request, "pagenotfound.html", {})

@login_required
def viewfacultytimetable(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty=Staff.objects.get(id=id)
	classes=Class.objects.filter(faculty=faculty)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_cl=[]
	for cl in classes:
		if cl.faculty_group_course.group.groups.group_year==year and cl.faculty_group_course.group.groups.semester_type==sem:
			curr_cl.append(cl)
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
		'classes':curr_cl,
		'staff':staff,
		'timeslots':timeslots,
		'time':time,
		'faculty':faculty,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/timetable_wrtfaculty.html',context)
	# return render(request,'',context)

@login_required
def adminviewgroups(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)	
	faculty=Staff.objects.get(id=id)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	groups=FacultyGroups.objects.filter(faculty=faculty)
	curr_groups=[]
	for group in groups:
		if group.groups.group_year==year and group.groups.semester_type==sem:
			curr_groups.append(group)
	context={
		'staff':staff,
		'groups':curr_groups,
		'faculty' : faculty,
		'notification_count':notification_count,
	}
	return render(request,'admin/adminviewgroups.html',context)

@login_required
def adminviewcourses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty=Staff.objects.get(id=id)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	courses=FacultyCourse.objects.filter(faculty=faculty)
	curr_courses=[]
	for course in courses:
		if course.course.course_year==year and course.course.semester_type==sem:
			curr_courses.append(course)
	context={
		'staff':staff,
		'courses':curr_courses,
		'faculty':faculty,	
		'notification_count':notification_count,	
	}
	return render(request,'admin/adminviewcourses.html',context)

@login_required
def adminviewgroupcourses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty=Staff.objects.get(id=id)
	groupcourses=GroupCourse.objects.filter(faculty=faculty)
	# print(groups)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_gp=[]
	for gc in groupcourses:
		if gc.group.groups.group_year==year and gc.group.groups.semester_type==sem:
			curr_gp.append(gc)
	context={
		'staff':staff,
		'groupcourses':curr_gp,
		'faculty':faculty,	
		'notification_count':notification_count,	
	}
	return render(request,'admin/adminviewgroupcourses.html',context)

@login_required
def adminaddgroupcourse(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	fac=Staff.objects.get(id=id)
	form=AddGroupCourseForm()
	if request.method=='POST':
		form=AddGroupCourseForm(request.POST)
		if form.is_valid():
			faculty=form.cleaned_data['faculty']
			print(faculty.name)
			# faculty=Staff.objects.get(id=faculty)
			course=form.cleaned_data['course']
			print(course.course.course_id)
			# course=FacultyCourse.objects.get(id=course)
			group=form.cleaned_data['group']
			gc,was_created=GroupCourse.objects.get_or_create(faculty=faculty,course=course,group=group)
			gc.save()
			return redirect('main:adminviewgroupcourses' ,id=id)
	
	context={
		'staff':staff,
		'fac':fac,
		'form':form,
		'notification_count':notification_count,
	}
	return render(request,'admin/adminaddgroupcourse.html',context)

@login_required
def adminviewclasses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty=Staff.objects.get(id=id)
	classes=Class.objects.filter(faculty=faculty)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_cl=[]
	for cl in classes:
		if cl.faculty_group_course.group.groups.group_year==year and cl.faculty_group_course.group.groups.semester_type==sem:
			curr_cl.append(cl)
	context={
		'staff':staff,
		'classes':curr_cl,
		'faculty':faculty,
		'notification_count':notification_count,
	}
	return render(request,'admin/adminviewclasses.html',context)

@login_required
def admindeletegroup(request,id):
	group=FacultyGroups.objects.get(id=id)
	facid=group.faculty.id
	group.delete()
	return redirect('main:adminviewgroups',id=facid)

@login_required
def admindeletecourses(request,id):
	course=FacultyCourse.objects.get(id=id)
	# print(course)
	facid=course.faculty.id
	# print(facid)
	course.delete()
	return redirect('main:adminviewcourses',id=facid)

@login_required
def admindeletegroupcourse(request,id):
	gc=GroupCourse.objects.get(id=id)
	# print(course)
	facid=gc.faculty.id
	# print(facid)
	gc.delete()
	return redirect('main:adminviewgroupcourses',id=facid)

@login_required
def admindeleteclass(request,id):
	classes=Class.objects.get(id=id)
	labid=classes.lab.id
	classes.delete() 
	return redirect('main:viewLabClasses',id=labid)

@login_required
def admindeletefacultyclass(request,id):
	classes=Class.objects.get(id=id)
	facid=classes.faculty.id
	classes.delete() 
	return redirect('main:adminviewclasses',id=facid)

@login_required	
def adminaddcourses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
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
	return render(request,'admin/adminaddfacultycourses.html',{'form' : form, "staff":staff,'notification_count':notification_count,})
		# return HttpResponse('202')

@login_required
def adminaddgroup(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
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
	return render(request,'admin/adminaddfacultygroups.html',{'form' : form, "staff":staff,'notification_count':notification_count,})
		# return HttpResponse('202')

@login_required
def adminaddfacultyclass(request,id):
	faculty=Staff.objects.get(id=id)
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	form=AddFacultyClassForm(faculty)
	if request.method == 'POST':
		form=AddFacultyClassForm(faculty,request.POST)
		if form.is_valid():
			# print("yay")
			lab=form.cleaned_data['lab']
			fgc=form.cleaned_data['faculty_group_course']
			day=form.cleaned_data['day']
			starttime=form.cleaned_data['starttime']
			tools_used=form.cleaned_data['tools_used']
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
			activity,was_created= Class.objects.get_or_create(lab=lab,faculty=faculty,faculty_group_course=fgc,day=day,starttime=starttime,endtime=endtime,tools_used=tools_used)
			activity.save()
			return redirect('main:adminviewclasses', id=id)
	context={
		'staff':staff,
		'form':form,
		'faculty':faculty,
		'notification_count':notification_count,
	}
	return render(request,'admin/adminaddfacultyclasses.html',context)


@login_required
def adminupdatefacultyclass(request,id,pk):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
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
			faculty_group_course=form.cleaned_data['faculty_group_course']
			# print(course.faculty)
			day=form.cleaned_data['day']
			starttime=form.cleaned_data['starttime']
			tools_used=form.cleaned_data['tools_used']
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
			classes.faculty_group_course=faculty_group_course
			classes.day=day
			classes.starttime=starttime
			classes.endtime=endtime
			classes.tools_used=tools_used
			classes.save()
			return redirect('main:adminviewclasses', id=id)
	return render(request, 'admin/adminaddfacultyclasses.html', {'staff':staff,'form': form,'notification_count':notification_count,})

@login_required
def viewinventory(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	inventory=StaffInventory.objects.filter(staff=staff).order_by('id')
	active_inventory=[i for i in inventory if i.device.is_working==True]
	inactive_inventory=[i for i in inventory if i.device.is_working==False]
	# print(len(inventory))
	context={
		'staff':staff,
		'inventory':inventory,
		'notification_count':notification_count,
	}
	return render(request,'inventory.html',context)

@login_required
def adminviewinventory(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	fac=Staff.objects.get(id=id)
	inventory_devices=StaffInventory.objects.filter(staff=fac)
	inventory_devices_to_return=StaffInventory.objects.filter(staff=fac,is_requested_for_return=True)
	return render(request,"admin/adminviewinventory.html",{"staff":staff,"inventorystaff":fac,"devices":inventory_devices,"devicestoreturn":inventory_devices_to_return,'notification_count':notification_count,})

@login_required
def loaddevices(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	room=Room.objects.get(id=id)
	# print(room.room_id)
	name_id = request.GET.get('name_id')
	name=CategoryOfDevice.objects.get(id=name_id)
	# print(name.category)
	X=[]
	devices=Devices.objects.filter(name=name,room=None,in_inventory=False)
	# print(devices)
	X.extend(devices)
	devices=Devices.objects.filter(name=name,room=room,in_inventory=False)
	# print(devices)
	X.extend(devices)
	# print(X)
	return render(request, 'inventory/devices_dropdown_list_option.html', {'devices':X, "staff":staff,'notification_count':notification_count,})

@login_required
def allotdevices(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	fac=Staff.objects.get(id=id)
	form=AllotDevicesForm()
	if request.method == 'POST':
		form = AllotDevicesForm(request.POST)
		# print(form)
		if form.is_valid():
			name=form.cleaned_data['name']
			device=form.cleaned_data['device']
			created=timezone.now()
			# print(created)
			dev=Devices.objects.get(id=device.id)
			dev.in_inventory=True
			dev.room=fac.room
			dev.save()
			print(created)
			devices,was_created=StaffInventory.objects.get_or_create(staff=fac,device=dev,date_added=created,is_requested_for_return=False)
			devices.save()
			request='Assign'
			log,was_created=Inventory_log.objects.get_or_create(request_type=request,staff=fac,device_id=dev.device_id,device_name=dev.name.category,date=datetime.datetime.now())
			log.save()
			return redirect('main:adminviewinventory', id=id)
		
	return render(request,'inventory/allotdevices.html',{'form':form,'staff':staff,'inventorystaff':fac,'notification_count':notification_count,})

@login_required
def devicesreturnrequest(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	inventory=StaffInventory.objects.filter(staff=staff,is_requested_for_return=False)
	if request.method=='POST':
		devices=request.POST.getlist('devices')
		for device in devices:
			dev_id=device.split('/')[0]
			inventory_device=StaffInventory.objects.get(id=dev_id)
			inventory_device.is_requested_for_return=True
			inventory_device.save()
		customMessage2 = "your request for Return of devices is placed"
		notification, was_created = Notification.objects.get_or_create(
			sender=staff, 
			reciever=str(staff.id) + ' ' + staff.name, 
			message=customMessage2,
			notification_type = 'INVENTORY',
			taskId=staff.id,
			time=datetime.datetime.now(),
		) 
		notification.save()
		customMessage = staff.name + " requested to Return some devices"
		notification, was_created = Notification.objects.get_or_create(
			sender=staff,  
			reciever='admin', 
			message=customMessage,
			notification_type = 'INVENTORY',
			taskId=staff.id,
			time=datetime.datetime.now(),
		) 
		notification.save()
		return redirect('main:viewinventory')
	
	context={
		'staff':staff,
		'devices':inventory,
		'notification_count':notification_count,
	}
	return render(request,'inventory/return_request.html',context)

@login_required
def approveDeviceRequest(request,pk):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	inventory_device=StaffInventory.objects.get(id=pk)
	fac=inventory_device.staff
	device=inventory_device.device
	device.room=None
	device.in_inventory=False
	device.save()
	request='Return'
	log,was_created=Inventory_log.objects.get_or_create(request_type=request,staff=fac,device_id=device.device_id,device_name=device.name.category,date=datetime.datetime.now())
	log.save()
	inventory_device.delete()
	customMessage="Device with id-> "+device.device_id+" is returned" 
	notification, was_created = Notification.objects.get_or_create(
			sender=staff,  
			reciever=str(fac.id)+" "+fac.name, 
			message=customMessage,
			notification_type ='INVENTORY',
			taskId=staff.id,
			time=datetime.datetime.now(),
		) 
	notification.save()
	return redirect('main:adminviewinventory',id=fac.id)

@login_required
def declineDeviceRequest(request,pk):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	inventory_device=StaffInventory.objects.get(id=pk)
	fac=inventory_device.staff
	device=inventory_device.device
	inventory_device.is_requested_for_return=False
	inventory_device.save()
	customMessage="Your Request to return Device with id-> "+device.device_id+" is declined" 
	notification, was_created = Notification.objects.get_or_create(
			sender=staff,  
			reciever=str(fac.id)+" "+fac.name, 
			message=customMessage,
			notification_type = 'INVENTORY',
			taskId=staff.id,
			time=datetime.datetime.now(),
		) 
	notification.save()
	return redirect('main:adminviewinventory',id=fac.id)

@login_required
def adminviewrooms(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	rooms=Room.objects.all()
	myFilter = filterRoom(request.GET,queryset=rooms)
	rooms=myFilter.qs
	context={
		'staff':staff,
		'rooms':rooms,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'admin/adminviewrooms.html',context)

@login_required
def adminaddroom(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	form=NewRoomForm
	if request.method == 'POST':
		form=NewRoomForm(request.POST)
		if form.is_valid:
			form.save()
			return redirect('main:adminviewrooms')
	context={
		'staff':staff,
		'form':form,
		'notification_count':notification_count,
	}
	return render(request,'admin/addroom.html',context)

@login_required
def admineditroom(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	room_instance=Room.objects.get(id=id)
	form=NewRoomForm(instance=room_instance)
	if request.method == 'POST':
		form=NewRoomForm(request.POST,instance=room_instance)
		if form.is_valid:
			form.save()
			return redirect('main:adminviewrooms')
	context={
		'staff':staff,
		'form':form,
		'notification_count':notification_count,
	}
	return render(request,'admin/addroom.html',context)

@login_required
def viewallcourses(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	courses=Course.objects.all()
	myFilter = filterCourse(request.GET,queryset=courses)
	courses=myFilter.qs
	context={
		'staff':staff,
		'courses':courses,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'admin/viewcourses.html',context)

@login_required
def adminaddcourse(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	form=NewCourseForm
	if request.method == 'POST':
		form=NewCourseForm(request.POST)
		if form.is_valid:
			form.save()
			return redirect('main:viewallcourses')
	context={
		'staff':staff,
		'form':form,
		'notification_count':notification_count,
	}
	return render(request,'admin/addcourse.html',context)

@login_required
def admineditcourse(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	course_instance=Course.objects.get(id=id)
	form=NewCourseForm(instance=course_instance)
	if request.method == 'POST':
		form=NewCourseForm(request.POST,instance=course_instance)
		if form.is_valid:
			form.save()
			return redirect('main:viewallcourses')
	context={
		'staff':staff,
		'form':form,
		'notification_count':notification_count,
	}
	return render(request,'admin/addcourse.html',context)
	
@login_required
def viewallgroups(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	groups=Groups.objects.all()
	myFilter = filterGroup(request.GET,queryset=groups)
	groups=myFilter.qs
	context={
		'staff':staff,
		'groups':groups,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'admin/viewgroups.html',context)

@login_required
def addgroup(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	form=NewGroupForm
	if request.method == 'POST':
		form=NewGroupForm(request.POST)
		if form.is_valid:
			form.save()
			return redirect('main:viewallgroups')
	context={
		'staff':staff,
		'form':form,
		'notification_count':notification_count,
	}
	return render(request,'admin/addgroup.html',context)

@login_required	
def admineditgroup(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	group_instance=Groups.objects.get(id=id)
	form=NewGroupForm(instance=group_instance)
	if request.method == 'POST':
		form=NewGroupForm(request.POST,instance=group_instance)
		if form.is_valid:
			form.save()
			return redirect('main:viewallgroups')
	context={
		'staff':staff,
		'form':form,
		'notification_count':notification_count,
	}
	return render(request,'admin/addgroup.html',context)

@login_required
def adminaddlab(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	form=NewLabForm
	if request.method == 'POST':
		form=NewLabForm(request.POST)
		if form.is_valid:
			form.save()
			return redirect('main:adminLabs')
	context={
		'staff':staff,
		'form':form,
		'notification_count':notification_count,
	}
	return render(request,'admin/addlab.html',context)

@login_required
def load_prev_assigned_offices(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	room_id=request.GET.get('room_id')
	room=Room.objects.get(id=room_id)
	all_staffs=Staff.objects.all()
	already_assigned_staffs=[st for st in all_staffs if st.room == room]
	print(already_assigned_staffs)
	message=''
	if len(already_assigned_staffs)>0:
		message='This room is already alloted to '
		for i in already_assigned_staffs:
			message+=i.name + ','
		message=message[:-1]	
	print(message)
	return HttpResponse(message)

@login_required		
def adminassignoffice(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	all_staffs=Staff.objects.all()
	staffs=Staff.objects.filter(room=None)
	rooms=Room.objects.all()
	myFilter = filterRoom(request.GET,queryset=rooms)
	rooms=myFilter.qs
	if request.method == 'POST':
		selected_staff=request.POST['selected_staff']
		selected_staff=Staff.objects.get(id=selected_staff)
		office_id=request.POST['office']
		office=Room.objects.get(id=office_id)
		selected_staff.room=office
		selected_staff.save()
 
		return redirect('main:adminassignoffice')
	context={
		'staff':staff,
		'staffs':staffs,
		'rooms':rooms,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'admin/assignoffice.html',context)

@login_required
def viewallfacultycourses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty=Staff.objects.get(id=id)
	courses=Course.objects.all()
	myFilter = filterCourse(request.GET,queryset=courses)
	courses=myFilter.qs
	all_faculty_courses=FacultyCourse.objects.filter(faculty=faculty)
	faculty_courses=[fc for fc in all_faculty_courses if fc.course in courses]
	
	context={
		'staff':staff,
		'faculty':faculty,
		'faculty_courses':faculty_courses,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/viewallfacultycourses.html',context)

@login_required
def viewallfacultygroups(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty=Staff.objects.get(id=id)
	groups=Groups.objects.all()
	myFilter = filterGroup(request.GET,queryset=groups)
	groups=myFilter.qs
	all_faculty_groups=FacultyGroups.objects.filter(faculty=faculty)
	faculty_groups=[fc for fc in all_faculty_groups if fc.groups in groups]
	
	context={
		'staff':staff,
		'faculty':faculty,
		'faculty_groups':faculty_groups,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/viewallfacultygroups.html',context)

@login_required
def viewgroupcourses(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	groupcourses=GroupCourse.objects.filter(faculty=staff)
	# print(groups)
	current_date = datetime.datetime.now()
	year=int(current_date.strftime("%Y"))
	month=int(current_date.strftime("%m"))
	sem=""
	if int(month)<=6:
		sem="EVEN"
	else:
		sem="ODD"
	curr_gp=[]
	print(groupcourses)
	for gc in groupcourses:
		if gc.group.groups.group_year==year and gc.group.groups.semester_type==sem and gc.course.course.course_year==year and gc.course.course.semester_type==sem:
			curr_gp.append(gc)
	print(curr_gp)
	context={
		'staff':staff,
		'groupcourses':curr_gp,		
		'notification_count':notification_count,
	}
	return render(request,'Timetable/viewgroupcourses.html',context)

@login_required
def viewallfacultygroupcourses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty=Staff.objects.get(id=id)
	courses=Course.objects.all()
	myFilter = filterGroupCourse(request.GET,queryset=courses)
	courses=myFilter.qs
	all_faculty_courses=FacultyCourse.objects.filter(faculty=faculty)
	faculty_courses=[fc for fc in all_faculty_courses if fc.course in courses]
	all_faculty_groupcourses=GroupCourse.objects.filter(faculty=faculty)
	# print(all_faculty_groupcourses)
	faculty_groupcourses=[gc for gc in all_faculty_groupcourses if gc.course in faculty_courses]
	
	context={
		'staff':staff,
		'faculty':faculty,
		'faculty_groupcourses':faculty_groupcourses,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/viewallfacultygroupcourses.html',context)

@login_required
def viewallfacultyclasses(request,id):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	faculty=Staff.objects.get(id=id)
	courses=Course.objects.all()
	myFilter = filterGroupCourse(request.GET,queryset=courses)
	courses=myFilter.qs
	all_faculty_courses=FacultyCourse.objects.filter(faculty=faculty)
	faculty_courses=[fc for fc in all_faculty_courses if fc.course in courses]
	all_faculty_groupcourses=GroupCourse.objects.filter(faculty=faculty)
	# print(all_faculty_groupcourses)
	faculty_groupcourses=[gc for gc in all_faculty_groupcourses if gc.course in faculty_courses]
	all_faculty_classes=Class.objects.filter(faculty=faculty)
	faculty_classes=[cl for cl in all_faculty_classes if cl.faculty_group_course in faculty_groupcourses]
	
	context={
		'staff':staff,
		'faculty':faculty,
		'faculty_classes':faculty_classes,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'Timetable/viewallfacultyclasses.html',context)
	
def adminviewbranches(request):
	if request.user.is_staff:
		staff=Staff.objects.get(user_obj=request.user)
		notification_count=get_notifications(staff.id)
		branches=Branches.objects.all()
		context={
			'staff':staff,
			'notification_count':notification_count,
			'branches':branches,
		}
		return render(request,'admin/adminviewbranches.html',context)
	else:
		return render(request,'pagenotfound.html')

def adminaddbranch(request):
	if request.user.is_staff:
		staff=Staff.objects.get(user_obj=request.user)
		notification_count=get_notifications(staff.id)
		form=NewBranchForm
		if request.method == 'POST':
			form=NewBranchForm(request.POST)
			if form.is_valid:
				form.save()
				return redirect('main:adminviewbranches')
		context={
			'staff':staff,
			'notification_count':notification_count,
			'form':form,
		}
		return render(request,'admin/adminaddbranch.html',context)
	else:
		return render(request,'pagenotfound.html')

def admineditbranch(request,id):
	if request.user.is_staff:
		staff=Staff.objects.get(user_obj=request.user)
		notification_count=get_notifications(staff.id)
		branch_instance=Branches.objects.get(id=id)
		form=NewBranchForm(instance=branch_instance)
		if request.method == 'POST':
			form=NewBranchForm(request.POST,instance=branch_instance)
			if form.is_valid:
				form.save()
				return redirect('main:adminviewbranches')
		context={
			'staff':staff,
			'form':form,
			'notification_count':notification_count,
		}
		return render(request,'admin/adminaddbranch.html',context)
	else:
		return render(request,'pagenotfound.html')

def adminviewTypeOfDevices(request):
	if request.user.is_staff:
		staff=Staff.objects.get(user_obj=request.user)
		notification_count=get_notifications(staff.id)
		tod=CategoryOfDevice.objects.all()
		context={
			'staff':staff,
			'notification_count':notification_count,
			'tod':tod,
		}
		return render(request,'admin/adminviewTypeOfDevices.html',context)
	else:
		return render(request,'pagenotfound.html')
	

def adminaddTypeOfDevice(request):
	if request.user.is_staff:
		staff=Staff.objects.get(user_obj=request.user)
		notification_count=get_notifications(staff.id)
		form=NewTypeOfDeviceForm
		if request.method == 'POST':
			form=NewTypeOfDeviceForm(request.POST)
			if form.is_valid:
				form.save()
				return redirect('main:adminviewTypeOfDevices')
		context={
			'staff':staff,
			'notification_count':notification_count,
			'form':form,
		}
		return render(request,'admin/adminaddTypeOfDevice.html',context)
	else:
		return render(request,'pagenotfound.html')

def admineditTypeOfDevice(request,id):
	if request.user.is_staff:
		staff=Staff.objects.get(user_obj=request.user)
		notification_count=get_notifications(staff.id)
		tod_instance=CategoryOfDevice.objects.get(id=id)
		form=NewTypeOfDeviceForm(instance=tod_instance)
		if request.method == 'POST':
			form=NewTypeOfDeviceForm(request.POST,instance=tod_instance)
			if form.is_valid:
				form.save()
				return redirect('main:adminviewTypeOfDevices')
		context={
			'staff':staff,
			'form':form,
			'notification_count':notification_count,
		}
		return render(request,'admin/adminaddTypeOfDevice.html',context)
	else:
		return render(request,'pagenotfound.html')

def adminviewdevices(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	context={
		'staff':staff,
		'notification_count':notification_count,
	}
	return render(request,'admin/adminviewdevices.html',context)
	
def adminview_warehouse_devices(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	devices=Devices.objects.filter(room=None)
	myFilter = filterWarehouseDevices(request.GET,queryset=devices)
	devices=myFilter.qs
	context={
		'staff':staff,
		'devices':devices,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'admin/adminview_warehouse_devices.html',context)
	
def adminview_assigned_devices(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	all_devices=Devices.objects.all()
	devices=Devices.objects.filter(room=None)
	assigned_devices=[dev for dev in all_devices if dev not in devices]
	assigned_devices=Devices.objects.filter(id__in={instance.id for instance in assigned_devices})
	myFilter = filterAssignedDevices(request.GET,queryset=assigned_devices)
	assigned_devices=myFilter.qs
	context={
		'staff':staff,
		'devices':assigned_devices,
		'myFilter':myFilter,
		'notification_count':notification_count,
	}
	return render(request,'admin/adminview_assigned_devices.html',context)

def adminadd_device(request):
		if request.user.is_staff:
			staff=Staff.objects.get(user_obj=request.user)
			notification_count=get_notifications(staff.id)
			form=NewDeviceForm
			if request.method == 'POST':
					form=NewDeviceForm(request.POST)
					if form.is_valid:
						form.save()
						return redirect('main:adminview_assigned_devices')
			context={
					'staff':staff,
					'notification_count':notification_count,
					'form':form,
			}
			return render(request,'admin/adminadd_assigned_devices.html',context)
		else:
			return render(request,'pagenotfound.html')

def viewinventorylogs(request):
	staff=Staff.objects.get(user_obj=request.user)
	notification_count=get_notifications(staff.id)
	inventorylogs=Inventory_log.objects.filter(staff=staff)
	context={
		'staff':staff,
		'notification_count':notification_count,
	    'inventorylogs':inventorylogs,				
	}
	return render(request,'inventory/viewinventorylogs.html',context)

def admineditstaffprofile(request,id):
	if request.user.is_staff:
		staff = Staff.objects.get(id=id)	
		admin=Staff.objects.get(user_obj=request.user)
		notification_count=get_notifications(admin.id)
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
				"agency":agency,
				'notification_count':notification_count,
			}
			return render(request, "admin/admineditstaffprofile.html", context)		
	else:
		return render(request,'pagenotfound.html',{})