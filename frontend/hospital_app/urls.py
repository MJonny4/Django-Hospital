from django.urls import path
from . import views

app_name = 'hospital'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('switch-role/', views.switch_role, name='switch_role'),
    
    # Protected user pages
    path('profile/', views.profile, name='profile'),
    path('appointments/', views.appointments, name='appointments'),
    path('appointments/create/', views.create_appointment, name='create_appointment'),
    path('appointments/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('doctors/', views.doctors_list, name='doctors_list'),
    path('doctors/<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('availability/<int:doctor_id>/', views.check_availability, name='check_availability'),
    
    # Admin pages
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/create-patient/', views.admin_create_patient, name='admin_create_patient'),
    path('admin-panel/doctors/', views.admin_doctors, name='admin_doctors'),
    path('admin-panel/register-doctor/', views.admin_register_doctor, name='admin_register_doctor'),
    path('admin-panel/appointments/', views.admin_appointments, name='admin_appointments'),
    path('admin-panel/availability/', views.admin_availability, name='admin_availability'),
    
    # Doctor pages
    path('doctor-panel/', views.doctor_panel, name='doctor_panel'),
    path('doctor-panel/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor-panel/appointments/<int:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('doctor-panel/appointments/<int:appointment_id>/complete/', views.complete_appointment, name='complete_appointment'),
]