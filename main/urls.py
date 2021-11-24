from django.urls import path, include
from . import views

app_name='main'

urlpatterns = [
    path('', views.home, name='home'),
    path('complaint/',views.complaint, name='complaint'),
    path("logout/", views.logout_request, name= "logout"),
    path("register/", views.register_request, name="register"),
    path("login/", views.login_request, name="login"),
]