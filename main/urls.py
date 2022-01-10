from django.urls import path, include
from . import views

app_name='main'

urlpatterns = [
    # user paths
    path("register/", views.register_request, name="register"),
    path("login/", views.login_request, name="login"),
    path("logout/", views.logout_request, name= "logout"),

    path('', views.home, name='home'),
    path('profile/',views.user_profile, name='user_profile'),

    # path('profile/edit-profile',views.UserEditView.as_view(), name='editProfile'),
    path('profile/edit-profile',views.editProfile, name='editProfile'),
    
    path('complaint/<pk>',views.complaint, name='complaint'),
    path("lab/<pk>", views.lab, name='lab'),
    path("add/<pk>",views.add_computer,name='add_device'),
    path('complaint-resolve/<pk>', views.resolveConflict, name='resolveConflict'),
    path('profile/leaves/', views.userLeaves, name="userLeaves"),
    path('profile/leaves/request-leaves', views.requestleave, name="requestleave"),
    path('profile/notifications/', views.notifications, name='notification'),
    path('profile/notification/<pk>', views.handleNotification, name="handleNotification"),
    path('profile/leaves/check-leave-status/', views.checkLeaveStatus, name='checkLeaveStatus'),
    path('profile/leaves/check-leave-status/<pk>' , views.checkLeaveStatusId, name="currleaveStatus"),
    path('profile/leaves/check-leave-status/cancel/<pk>', views.cancelLeaveRequest, name='cancelLeaveRequest'),
    path('profile/leaves/approve-leaves/', views.approveLeaves, name='approveLeaves'),
    path('profile/leaves/approve-leaves/approve/<pk>', views.approveRequest, name='approveRequest'),
    path('profile/leaves/approve-leaves/decline/<pk>', views.declineRequest, name='declineRequest'),
    path('profile/view_complaints/' , views.view_complaints, name="viewcomplaints"),
    path('profile/viewprevleaves',views.viewprevleaves,name='viewprevleaves'),

    # admin paths
    path('admin-dashboard/staff-members-list/', views.adminStaff, name='adminStaff'),
    path('admin-dashboard/current-year-leaves/', views.adminLeaves, name='adminLeaves'),
    path('admin-dashboard/current-year-leaves/new-leave-form', views.newLeave, name='newLeave'),
    path('admin-dashboard/labs-list/', views.adminLabs, name='adminLabs'),
    path('admin-dashboard/complaints-list/', views.adminComplaints, name='adminComplaints'),
    # path('resolvecomplaint', views.resolveConflict, name='resolveConflict')
]

    # path('profile/leaves/approve-leaves/adminapprove/<pk>', views.adminapproveRequest, name='adminapproveRequest'),
    # path('profile/leaves/approve-leaves/admindecline/<pk>', views.admindeclineRequest, name='admindeclineRequest'),