"""Admin configuration for schedules app."""

from django.contrib import admin
from .models import Availability, TimeSlot, DoctorLeave


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'get_day_of_week_display', 'start_time', 'end_time', 'slot_duration', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    search_fields = ['doctor__user__first_name', 'doctor__user__last_name']


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'start_time', 'end_time', 'is_booked']
    list_filter = ['is_booked', 'date']
    search_fields = ['doctor__user__first_name', 'doctor__user__last_name']
    date_hierarchy = 'date'


@admin.register(DoctorLeave)
class DoctorLeaveAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'start_date', 'end_date', 'reason']
    search_fields = ['doctor__user__first_name', 'doctor__user__last_name']
    date_hierarchy = 'start_date'
