"""Dashboard views for patient, doctor, and admin roles."""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from datetime import date, timedelta

from accounts.mixins import PatientRequiredMixin, DoctorRequiredMixin, AdminRequiredMixin
from appointments.models import Appointment
from doctors.models import DoctorProfile, Specialty
from patients.models import PatientProfile
from notifications.models import Notification
from schedules.models import DoctorLeave
from schedules.utils import generate_slots_for_date


class PatientDashboardView(PatientRequiredMixin, TemplateView):
    """Dashboard for patients — upcoming/past appointments + notifications."""
    template_name = 'dashboard/patient.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patient = self.request.user.patient_profile
        all_appts = Appointment.objects.filter(patient=patient).select_related(
            'doctor__user', 'time_slot', 'specialty'
        )
        today = date.today()
        ctx['upcoming'] = all_appts.filter(
            time_slot__date__gte=today,
            status__in=['pending', 'confirmed']
        ).order_by('time_slot__date')[:5]
        ctx['past'] = all_appts.filter(
            Q(status='completed') | Q(time_slot__date__lt=today)
        ).order_by('-time_slot__date')[:5]
        ctx['cancelled'] = all_appts.filter(status='cancelled').order_by('-updated_at')[:5]
        ctx['notifications'] = Notification.objects.filter(
            user=self.request.user, is_read=False
        )[:5]
        ctx['total_appointments'] = all_appts.count()
        ctx['patient'] = patient
        return ctx


class DoctorDashboardView(DoctorRequiredMixin, TemplateView):
    """Dashboard for doctors — today's schedule, stats, patient list."""
    template_name = 'dashboard/doctor.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        today = date.today()
        all_appts = Appointment.objects.filter(doctor=doctor).select_related(
            'patient__user', 'time_slot'
        )
        ctx['today_appointments'] = all_appts.filter(
            time_slot__date=today
        ).order_by('time_slot__start_time')
        ctx['pending_requests'] = all_appts.filter(
            status='pending'
        ).order_by('-created_at')[:10]
        ctx['upcoming'] = all_appts.filter(
            time_slot__date__gt=today, status='confirmed'
        ).order_by('time_slot__date')[:5]
        ctx['total'] = all_appts.count()
        ctx['confirmed'] = all_appts.filter(status='confirmed').count()
        ctx['completed'] = all_appts.filter(status='completed').count()
        ctx['cancelled'] = all_appts.filter(status='cancelled').count()
        ctx['pending'] = all_appts.filter(status='pending').count()
        ctx['notifications'] = Notification.objects.filter(
            user=self.request.user, is_read=False
        )[:5]
        ctx['doctor'] = doctor
        ctx['active_leaves'] = DoctorLeave.objects.filter(
            doctor=doctor, end_date__gte=today
        ).order_by('start_date')
        # Generate today's slots
        generate_slots_for_date(doctor, today)
        return ctx


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Admin dashboard — platform-wide statistics."""
    template_name = 'dashboard/admin.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_patients'] = PatientProfile.objects.count()
        ctx['total_doctors'] = DoctorProfile.objects.filter(is_active=True).count()
        ctx['total_appointments'] = Appointment.objects.count()
        ctx['appointments_by_status'] = Appointment.objects.values('status').annotate(
            count=Count('id')
        )
        ctx['appointments_by_specialty'] = Appointment.objects.values(
            'specialty__name'
        ).annotate(count=Count('id')).order_by('-count')[:8]
        ctx['top_doctors'] = DoctorProfile.objects.filter(
            is_active=True
        ).order_by('-rating')[:5]
        ctx['recent_appointments'] = Appointment.objects.select_related(
            'patient__user', 'doctor__user', 'time_slot'
        ).order_by('-created_at')[:10]
        return ctx
