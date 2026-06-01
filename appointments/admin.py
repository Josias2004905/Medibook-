"""Admin configuration for appointments app."""

from django.contrib import admin
from .models import Appointment, Consultation, Review


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'specialty', 'get_date', 'status', 'created_at']
    list_filter = ['status', 'specialty']
    search_fields = [
        'patient__user__first_name', 'patient__user__last_name',
        'doctor__user__first_name', 'doctor__user__last_name',
    ]
    date_hierarchy = 'created_at'
    list_editable = ['status']

    def get_date(self, obj):
        return obj.time_slot.date
    get_date.short_description = 'Date'
    get_date.admin_order_field = 'time_slot__date'


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'follow_up_date', 'created_at']
    search_fields = ['appointment__patient__user__first_name', 'appointment__doctor__user__first_name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['patient__user__first_name', 'doctor__user__first_name']
