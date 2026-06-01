"""Role-based access control mixins for class-based views."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


class PatientRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict view access to users with the 'patient' role."""

    def test_func(self):
        return self.request.user.role == 'patient'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Access restricted to patients only.")
        return redirect('dashboard')


class DoctorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict view access to users with the 'doctor' role."""

    def test_func(self):
        return self.request.user.role == 'doctor'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Access restricted to doctors only.")
        return redirect('dashboard')


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict view access to admin users or staff."""

    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Access restricted to administrators only.")
        return redirect('dashboard')
