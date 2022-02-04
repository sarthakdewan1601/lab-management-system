from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name='main'

urlpatterns = [
    # auth paths
    # add account/ in front of these urls
    path("accounts/signup/", views.register_request, name="register"),
    path('accounts/email-confirmation/<uidb64>/<token>', views.activate_user, name='active_email'),
    path("accounts/login/", views.login_request, name="login"),
    path("accounts/logout/<id>", views.logout_request, name= "logout_request"),
    path('accounts/password-reset/', views.passwordResetView, name="passwordReset"),
    path('accounts/password-reset/<uidb64>/<token>/', views.passwordResetConfirmView, name="passwordResetConfirm"),
    path('accounts/password-reset/<token>/<id>', views.passwordResetForm, name="passwordResetForm"),
    path('accounts/password-change/<id>', views.passwordChange, name="passwordChange"),
 
    # user paths
    path('', views.home, name='home'),
    path('profile/user-profile/' ,views.user_profile, name='user_profile'),
    path('profile/user-profile-details/',views.user_profile_details, name='userProfileDetails'),
    path('profile/edit-profile/<pk>',views.editProfile, name='editProfile'),
    path('complaint/<pk>',views.complaint, name='complaint'),
    path("lab/<pk>", views.lab, name='lab'),
    path("add/<pk>",views.add_devices,name='add_devices'),
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
    path('profile/viewprevleaves/',views.viewprevleaves,name='viewprevleaves'),
    path('profile/viewcourses/',views.viewcourses,name='viewcourses'),
    path('profile/viewgroups/',views.viewgroups,name='viewgroups'),
    path('profile/viewclasses/',views.viewfacultyclasses,name='viewfacultyclasses'),
    path('profile/viewfacultytimetable/',views.viewfacultytimetable,name='viewfacultytimetable'),
    path('profile/viewitemsalloted/',views.viewinventory,name='viewinventory'),

    # admin paths
    path('admin-dashboard/staff-members-list/', views.adminStaff, name='adminStaff'),
    path('admin-dashboard/view-inventory/<id>',views.adminviewinventory,name='adminviewinventory'),
    path('admin-dashboard/view-inventory/approveDeviceRequest/<pk>',views.approveDeviceRequest,name='approveDeviceRequest'),
    path('admin-dashboard/view-inventory/declineDeviceRequest/<pk>',views.declineDeviceRequest,name='declineDeviceRequest'),
    path('admin-dashboard/current-year-leaves/', views.adminLeaves, name='adminLeaves'),
    path('admin-dashboard/current-year-leaves/new-leave-form', views.newLeave, name='newLeave'),
    path('admin-dashboard/current-year-leaves/leave/<pk>', views.adminEditLeave, name='adminEditLeave'),
    path('admin-dashboard/current-year-leaves/remove-leave/<pk>', views.removeLeave, name='removeLeave'),
    path('admin-dashboard/labs-list/', views.adminLabs, name='adminLabs'),
    path('admin-dashboard/complaints-list/', views.adminComplaints, name='adminComplaints'),
    path('admin-dashboard/faculty-details',views.ViewFacultyDetails,name='adminfacultydetails'),
    path('admin-dashboard/faculty-details/admin-view-groups/<id>',views.adminviewgroups,name='adminviewgroups'),
    path('admin-dashboard/faculty-details/admin-view-courses/<id>',views.adminviewcourses,name='adminviewcourses'),
    path('admin-dashboard/faculty-details/admin-view-group-courses/<id>',views.adminviewgroupcourses,name='adminviewgroupcourses'),
    path('admin-dashboard/faculty-details/admin-view-group-courses/add-group-course/<id>',views.adminaddgroupcourse,name='adminaddgroupcourse'),
    path('admin-dashboard/faculty-details/admin-view-classes/<id>',views.adminviewclasses,name='adminviewclasses'),
    path('admin-dashboard/faculty-details/admin-view-groups/delete-group/<id>',views.admindeletegroup,name='admindeletegroup'),
    path('admin-dashboard/faculty-details/admin-view-courses/delete-courses/<id>',views.admindeletecourses,name='admindeletecourses'),
    path('admin-dashboard/faculty-details/admin-view-courses/add-course/<id>',views.adminaddcourses,name='adminaddcourses'),
    path('admin-dashboard/faculty-details/admin-view-courses/add-group/<id>',views.adminaddgroup,name='adminaddgroup'),
    path('admin-dashboard/faculty-details/admin-view-courses/add-faculty-class/<id>',views.adminaddfacultyclass,name='adminaddfacultyclass'),
    path('admin-dashboard/faculty-details/admin-view-courses/update-faculty-class/<id><pk>',views.adminupdatefacultyclass,name='adminupdatefacultyclass'),
    path('admin-dashboard/faculty-details/admin-view-courses/delete-class/<id>',views.admindeleteclass,name='admindeleteclass'),
    path('admin-dashboard/faculty-details/admin-view-courses/delete-faculty-class/<id>',views.admindeletefacultyclass,name='admindeletefacultyclass'),
    #timetable paths
    path('viewlabtimetable/<id>',views.viewtimetable_wrtlab,name='viewtimetable_wrtlab'),
    path('viewlabclasses/<id>',views.viewLabClasses,name='viewLabClasses'),
    path('add_class/<id>',views.add_classes,name = 'add_classes'),
    path('ajax/load-courses/', views.load_courses, name='ajax_load_courses'), # AJAX
    path('ajax/load-groups/', views.load_groups, name='ajax_load_groups'),
    path('ajax/load-group-courses/', views.load_groupcourses, name='ajax_load_groupcourses'), # AJAX
    path('updateclass/<pk>_<id>/', views.update_class, name='update_class'),

    #inventory paths
    path('allotdevices/<id>',views.allotdevices,name='allotdevices'),
    path('ajax/load-devices/<id>', views.loaddevices, name='ajax_load_devices'), # AJAX
    path('return-devices/<id>',views.devicesreturnrequest,name='devicesreturnrequest'),

]
