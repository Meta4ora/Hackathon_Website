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
    path('register_mentor/', views.register_mentor, name='register_mentor'),
    path('api/generate_summary/', views.generate_summary, name='generate_summary'),
    path('api/get_tables/', views.get_tables, name='get_tables'),
    path('api/get_tables_and_views/', views.get_tables_and_views, name='get_tables_and_views'),
    path('api/get_views/', views.get_views, name='get_views'),
    path('api/get_table_data/', views.get_table_data, name='get_table_data'),
    path('api/save_table_data/', views.save_table_data, name='save_table_data'),
    path('api/get_table_fields/', views.get_table_fields, name='get_table_fields'),
    path('api/add_record/', views.add_record, name='add_record'),
]