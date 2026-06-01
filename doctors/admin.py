"""Admin configuration for doctors app."""

from django.contrib import admin
from .models import DoctorProfile, Specialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name', 'keywords']


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'experience_years', 'consultation_fee', 'is_active', 'rating']
    list_filter = ['specialty', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    list_editable = ['is_active']
