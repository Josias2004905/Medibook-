"""Admin configuration for patients app."""

from django.contrib import admin
from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'blood_type', 'emergency_contact']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    list_filter = ['blood_type']
