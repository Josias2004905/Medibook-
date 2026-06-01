"""Views for schedules app — availability, leave, and slot management."""

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from datetime import date, timedelta

from .models import Availability, DoctorLeave, TimeSlot
from .forms import AvailabilityForm, DoctorLeaveForm
from .utils import generate_slots_for_date
from accounts.mixins import DoctorRequiredMixin
from doctors.models import DoctorProfile


class AvailabilityListView(DoctorRequiredMixin, ListView):
    """List all availability rules for the current doctor."""
    model = Availability
    template_name = 'schedules/availability_list.html'
    context_object_name = 'availabilities'

    def get_queryset(self):
        return Availability.objects.filter(doctor=self.request.user.doctor_profile)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_leaves'] = DoctorLeave.objects.filter(
            doctor=self.request.user.doctor_profile,
            end_date__gte=date.today()
        ).order_by('start_date')
        return ctx


class AvailabilityCreateView(DoctorRequiredMixin, CreateView):
    """Create a new availability rule."""
    model = Availability
    form_class = AvailabilityForm
    template_name = 'schedules/availability_form.html'
    success_url = reverse_lazy('availability_list')

    def form_valid(self, form):
        form.instance.doctor = self.request.user.doctor_profile
        messages.success(self.request, "Availability added successfully.")
        return super().form_valid(form)


class AvailabilityUpdateView(DoctorRequiredMixin, UpdateView):
    """Edit an availability rule."""
    model = Availability
    form_class = AvailabilityForm
    template_name = 'schedules/availability_form.html'
    success_url = reverse_lazy('availability_list')

    def get_queryset(self):
        return Availability.objects.filter(doctor=self.request.user.doctor_profile)

    def form_valid(self, form):
        messages.success(self.request, "Availability updated.")
        return super().form_valid(form)


class AvailabilityDeleteView(DoctorRequiredMixin, DeleteView):
    """Delete an availability rule."""
    model = Availability
    template_name = 'schedules/availability_confirm_delete.html'
    success_url = reverse_lazy('availability_list')

    def get_queryset(self):
        return Availability.objects.filter(doctor=self.request.user.doctor_profile)


class DoctorLeaveListView(DoctorRequiredMixin, ListView):
    """List all leave records for the current doctor."""
    model = DoctorLeave
    template_name = 'schedules/leave_list.html'
    context_object_name = 'leaves'

    def get_queryset(self):
        return DoctorLeave.objects.filter(doctor=self.request.user.doctor_profile)


class DoctorLeaveCreateView(DoctorRequiredMixin, CreateView):
    """Create a new leave period."""
    model = DoctorLeave
    form_class = DoctorLeaveForm
    template_name = 'schedules/leave_form.html'
    success_url = reverse_lazy('leave_list')

    def form_valid(self, form):
        form.instance.doctor = self.request.user.doctor_profile
        response = super().form_valid(form)
        TimeSlot.objects.filter(
            doctor=form.instance.doctor,
            date__gte=form.instance.start_date,
            date__lte=form.instance.end_date,
            is_booked=False
        ).delete()
        messages.success(self.request, "Leave period added. Free slots during this period have been removed.")
        return response


class DoctorLeaveDeleteView(DoctorRequiredMixin, DeleteView):
    """Delete a leave period."""
    model = DoctorLeave
    template_name = 'schedules/leave_confirm_delete.html'
    success_url = reverse_lazy('leave_list')

    def get_queryset(self):
        return DoctorLeave.objects.filter(doctor=self.request.user.doctor_profile)


class GetAvailableSlotsView(View):
    """AJAX endpoint — returns available time slots for a doctor on a date."""

    def get(self, request):
        doctor_id = request.GET.get('doctor_id')
        date_str = request.GET.get('date')

        if not doctor_id or not date_str:
            return JsonResponse({'error': 'Missing doctor_id or date'}, status=400)

        try:
            from datetime import date as date_type
            target_date = date_type.fromisoformat(date_str)
            doctor = get_object_or_404(DoctorProfile, pk=doctor_id)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid date format'}, status=400)

        slots = generate_slots_for_date(doctor, target_date)
        data = [
            {
                'id': s.id,
                'start_time': s.start_time.strftime('%H:%M'),
                'end_time': s.end_time.strftime('%H:%M'),
                'is_booked': s.is_booked,
            }
            for s in slots
        ]
        return JsonResponse({'slots': data})
