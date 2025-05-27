# blog/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('events/', views.events, name='events'),
    path('events/add/', views.add_event, name='add_event'),
    path('control_panel/', views.control_panel, name='control_panel'),
    path('register_mentor/', views.register_mentor, name='register_mentor'),  # Исправлено
]