from django.urls import path, include
from . import views

app_name='main'

urlpatterns = [
    path('', views.home, name='home'),
    path('complaint/<pk>',views.complaint, name='complaint'),
    path("logout/", views.logout_request, name= "logout"),
    path("register/", views.register_request, name="register"),
    path("login/", views.login_request, name="login"),
    path("lab/<pk>", views.lab, name='lab'),
    path("add/<pk>",views.add_computer,name='add_computer'),
    path('complaint-resolve/<pk>', views.resolveConflict, name='resolveConflict'),
    path('staff-members-list', views.adminStaff, name='adminStaff'),
    path('technicians-list', views.adminTechnicians, name='adminTechnicians'),
    path('labs-list', views.adminLabs, name='adminLabs'),
    path('complaints-list', views.adminComplaints, name='adminComplaints')
]