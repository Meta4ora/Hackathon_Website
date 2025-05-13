from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),             # Главная страница
    path('register/', views.register_view, name='register'),
]