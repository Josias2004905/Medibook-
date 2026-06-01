"""Views for accounts app — registration, login, logout, profile."""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import UpdateView, TemplateView
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.db.models import Q

from .models import User
from .forms import PatientRegistrationForm, UserProfileForm
from doctors.models import DoctorProfile, Specialty
from django.db.models import Count


def _doctor_sphere_data(doctors):
    """Serialize featured doctors for the 3D sphere on the landing page."""
    items = []
    for d in doctors:
        user = d.user
        bio = d.bio or 'Experienced medical professional dedicated to exceptional patient care.'
        if len(bio) > 120:
            bio = bio[:117] + '...'
        items.append({
            'id': d.pk,
            'name': f'Dr. {user.get_full_name()}',
            'specialty': d.specialty.name if d.specialty else 'General Practice',
            'rating': float(d.rating),
            'fee': float(d.consultation_fee),
            'bio': bio,
            'url': reverse('doctor_detail', args=[d.pk]),
            'src': user.profile_picture.url if user.profile_picture else '',
            'initials': (
                f'{user.first_name[:1]}{user.last_name[:1]}'.upper()
                if user.first_name and user.last_name
                else (user.username[:2].upper() if user.username else 'DR')
            ),
        })
    return items


def _specialty_marquee_data(specialties):
    """Serialize specialties for the perspective marquee."""
    return [
        {
            'name': s.name,
            'url': reverse('doctor_list') + f'?specialty={s.pk}',
        }
        for s in specialties
    ]


def index(request):
    """Public landing page with featured doctors and specialties."""
    specialties = Specialty.objects.annotate(
        active_doctors_count=Count('doctors', filter=Q(doctors__is_active=True))
    ).all()
    marquee_specialties = specialties
    featured_doctors = DoctorProfile.objects.filter(is_active=True).select_related(
        'user', 'specialty'
    ).order_by('-rating')[:12]
    query = request.GET.get('q', '')
    specialty_filter = request.GET.get('specialty', '')

    if query or specialty_filter:
        doctors_qs = DoctorProfile.objects.filter(is_active=True).select_related('user', 'specialty')
        if query:
            doctors_qs = doctors_qs.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(specialty__name__icontains=query)
            )
        if specialty_filter:
            doctors_qs = doctors_qs.filter(specialty__id=specialty_filter)
        return render(request, 'doctors/list.html', {
            'doctors': doctors_qs,
            'specialties': Specialty.objects.all(),
            'query': query,
        })

    return render(request, 'index.html', {
        'specialties': specialties,
        'specialty_marquee_data': _specialty_marquee_data(marquee_specialties),
        'featured_doctors': featured_doctors,
        'doctor_sphere_data': _doctor_sphere_data(featured_doctors),
    })


class RegisterView(View):
    """Handles user registration (patient or doctor)."""
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = PatientRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to MediBook, {user.first_name or user.username}!")
            if user.role == 'doctor':
                return redirect('doctor_dashboard')
            return redirect('patient_dashboard')
        return render(request, self.template_name, {'form': form})


class CustomLoginView(View):
    """Login view with role-based redirect."""
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            # Role-based redirect
            if user.role == 'doctor':
                return redirect('doctor_dashboard')
            elif user.role == 'admin' or user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('patient_dashboard')
        messages.error(request, "Invalid username or password.")
        return render(request, self.template_name, {'username': username})


class CustomLogoutView(View):
    """Logout and redirect to home."""

    def post(self, request):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('index')

    def get(self, request):
        logout(request)
        return redirect('index')


class DashboardRedirectView(LoginRequiredMixin, View):
    """Redirects authenticated users to their role-specific dashboard."""

    def get(self, request):
        if request.user.role == 'doctor':
            return redirect('doctor_dashboard')
        elif request.user.role == 'admin' or request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('patient_dashboard')


class ProfileUpdateView(LoginRequiredMixin, View):
    """Allow users to update their profile."""
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = UserProfileForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        return render(request, self.template_name, {'form': form})
