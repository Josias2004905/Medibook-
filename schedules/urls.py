"""URL patterns for schedules app."""

from django.urls import path
from . import views

urlpatterns = [
    path('availability/', views.AvailabilityListView.as_view(), name='availability_list'),
    path('availability/add/', views.AvailabilityCreateView.as_view(), name='availability_create'),
    path('availability/<int:pk>/edit/', views.AvailabilityUpdateView.as_view(), name='availability_edit'),
    path('availability/<int:pk>/delete/', views.AvailabilityDeleteView.as_view(), name='availability_delete'),
    path('leaves/', views.DoctorLeaveListView.as_view(), name='leave_list'),
    path('leaves/add/', views.DoctorLeaveCreateView.as_view(), name='leave_create'),
    path('leaves/<int:pk>/delete/', views.DoctorLeaveDeleteView.as_view(), name='leave_delete'),
    path('slots/', views.GetAvailableSlotsView.as_view(), name='get_slots'),
]
