"""Views for accounts app — registration, login, logout, profile."""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Count

from .forms import PatientRegistrationForm, UserProfileForm
from doctors.models import DoctorProfile, Specialty


def _doctor_sphere_data(doctors):
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
    return [
        {
            'name': s.name,
            'url': reverse('doctor_list') + f'?specialty={s.pk}',
        }
        for s in specialties
    ]


def index(request):
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
            if user.role == 'doctor':
                return redirect('doctor_dashboard')
            elif user.role == 'admin' or user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('patient_dashboard')
        messages.error(request, "Invalid username or password.")
        return render(request, self.template_name, {'username': username})


class CustomLogoutView(View):
    def post(self, request):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('index')

    def get(self, request):
        logout(request)
        return redirect('index')


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role == 'doctor':
            return redirect('doctor_dashboard')
        elif request.user.role == 'admin' or request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('patient_dashboard')


class ProfileUpdateView(LoginRequiredMixin, View):
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
