"""Views for doctors app — doctor listing, detail, profile management."""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from datetime import date, timedelta
from django.http import JsonResponse

from .models import DoctorProfile, Specialty
from .forms import DoctorProfileForm, SpecialtyForm
from accounts.mixins import DoctorRequiredMixin, AdminRequiredMixin
from schedules.utils import generate_slots_for_date


class DoctorListView(ListView):
    """Public view listing all active doctors with search and filter."""
    model = DoctorProfile
    template_name = 'doctors/list.html'
    context_object_name = 'doctors'
    paginate_by = 12

    def get_queryset(self):
        qs = DoctorProfile.objects.filter(is_active=True).select_related('user', 'specialty')
        q = self.request.GET.get('q', '')
        specialty = self.request.GET.get('specialty', '')
        if q:
            qs = qs.filter(
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(specialty__name__icontains=q) |
                Q(bio__icontains=q)
            )
        if specialty:
            qs = qs.filter(specialty__id=specialty)
        return qs.order_by('-rating')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['specialties'] = Specialty.objects.all()
        ctx['query'] = self.request.GET.get('q', '')
        ctx['selected_specialty'] = self.request.GET.get('specialty', '')
        return ctx


class DoctorDetailView(DetailView):
    """Public view with doctor profile and available slots for next 7 days."""
    model = DoctorProfile
    template_name = 'doctors/detail.html'
    context_object_name = 'doctor'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        doctor = self.get_object()
        today = date.today()
        # Pre-generate slots for next 7 days
        slots_by_date = {}
        for i in range(7):
            target = today + timedelta(days=i)
            day_slots = generate_slots_for_date(doctor, target)
            available = [s for s in day_slots if not s.is_booked]
            if available:
                slots_by_date[target] = available
        ctx['slots_by_date'] = slots_by_date
        ctx['reviews'] = doctor.reviews.select_related('patient__user').order_by('-created_at')[:5]
        return ctx


class DoctorProfileUpdateView(DoctorRequiredMixin, UpdateView):
    """Allow doctors to update their own profile."""
    model = DoctorProfile
    form_class = DoctorProfileForm
    template_name = 'doctors/profile_edit.html'
    success_url = reverse_lazy('doctor_dashboard')

    def get_object(self):
        return self.request.user.doctor_profile

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)


# --- Specialty CRUD (Admin only) ---

class SpecialtyListView(AdminRequiredMixin, ListView):
    model = Specialty
    template_name = 'doctors/specialty_list.html'
    context_object_name = 'specialties'


class SpecialtyCreateView(AdminRequiredMixin, CreateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = 'doctors/specialty_form.html'
    success_url = reverse_lazy('specialty_list')

    def form_valid(self, form):
        messages.success(self.request, "Specialty created successfully.")
        return super().form_valid(form)


class SpecialtyUpdateView(AdminRequiredMixin, UpdateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = 'doctors/specialty_form.html'
    success_url = reverse_lazy('specialty_list')

    def form_valid(self, form):
        messages.success(self.request, "Specialty updated.")
        return super().form_valid(form)


class SpecialtyDeleteView(AdminRequiredMixin, DeleteView):
    model = Specialty
    template_name = 'doctors/specialty_confirm_delete.html'
    success_url = reverse_lazy('specialty_list')


class DoctorSphereView(ListView):
    """Public view displaying doctors in an interactive 3D sphere layout."""
    model = DoctorProfile
    template_name = 'doctors/sphere.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        qs = DoctorProfile.objects.filter(is_active=True).select_related('user', 'specialty')
        # Order by rating to ensure consistent placement
        return qs.order_by('-rating')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Prepare doctor data for the JavaScript component
        doctor_data = []
        for doctor in ctx['doctors']:
            doctor_data.append({
                'id': doctor.id,
                'name': f"Dr. {doctor.user.get_full_name() or doctor.user.username}",
                'specialty': doctor.specialty.name if doctor.specialty else 'General',
                'bio': doctor.bio or 'Experienced specialist dedicated to quality patient care.',
                'src': doctor.user.profile_picture.url if doctor.user.profile_picture else '',
                'rating': float(doctor.rating) if doctor.rating else 0.0,
                'url': reverse_lazy('doctor_detail', kwargs={'pk': doctor.pk})
            })
        ctx['doctor_data'] = doctor_data
        return ctx
