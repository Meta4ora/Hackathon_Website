# blog/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),  # Change 'authorization' to 'login'
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
]