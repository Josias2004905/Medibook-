"""URL patterns for dashboard app."""

from django.urls import path
from . import views

urlpatterns = [
    path('patient/', views.PatientDashboardView.as_view(), name='patient_dashboard'),
    path('doctor/', views.DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
]
