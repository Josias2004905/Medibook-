"""URL patterns for patients app."""

from django.urls import path
from . import views

urlpatterns = [
    path('profile/edit/', views.PatientProfileUpdateView.as_view(), name='patient_profile_edit'),
]
