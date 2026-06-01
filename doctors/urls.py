"""URL patterns for doctors app."""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.DoctorListView.as_view(), name='doctor_list'),
    path('sphere/', views.DoctorSphereView.as_view(), name='doctor_sphere'),
    path('<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    path('profile/edit/', views.DoctorProfileUpdateView.as_view(), name='doctor_profile_edit'),
    # Specialty management (admin)
    path('specialties/', views.SpecialtyListView.as_view(), name='specialty_list'),
    path('specialties/add/', views.SpecialtyCreateView.as_view(), name='specialty_create'),
    path('specialties/<int:pk>/edit/', views.SpecialtyUpdateView.as_view(), name='specialty_edit'),
    path('specialties/<int:pk>/delete/', views.SpecialtyDeleteView.as_view(), name='specialty_delete'),
]
