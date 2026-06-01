"""Views for patients app."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages

from .models import PatientProfile
from accounts.mixins import PatientRequiredMixin


class PatientProfileUpdateView(PatientRequiredMixin, UpdateView):
    """Allow patients to update their own patient profile."""
    model = PatientProfile
    fields = ('date_of_birth', 'blood_type', 'emergency_contact', 'address')
    template_name = 'patients/profile_edit.html'
    success_url = reverse_lazy('patient_dashboard')

    def get_object(self):
        return self.request.user.patient_profile

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['date_of_birth'].widget.input_type = 'date'
        for field in form.fields.values():
            field.widget.attrs['class'] = 'form-control'
        return form

    def form_valid(self, form):
        messages.success(self.request, "Medical profile updated.")
        return super().form_valid(form)
