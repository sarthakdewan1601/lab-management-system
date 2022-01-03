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
    path('complaint/<pk>',views.complaint, name='complaint'),
    path("lab/<pk>", views.lab, name='lab'),
    path("add/<pk>",views.add_computer,name='add_device'),
    path('complaint-resolve/<pk>', views.resolveConflict, name='resolveConflict'),
    path('notifications/', views.notifications, name='notification'),
    
    # admin paths
    path('staff-members-list', views.adminStaff, name='adminStaff'),
    # path('technicians-list', views.adminTechnicians, name='adminTechnicians'),
    path('labs-list', views.adminLabs, name='adminLabs'),
    path('complaints-list', views.adminComplaints, name='adminComplaints')
]