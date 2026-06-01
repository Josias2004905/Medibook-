"""Django signals to auto-create profiles on user creation."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create PatientProfile or DoctorProfile based on user role."""
    if not created:
        return

    if instance.role == 'patient':
        from patients.models import PatientProfile
        PatientProfile.objects.get_or_create(user=instance)
    elif instance.role == 'doctor':
        from doctors.models import DoctorProfile
        DoctorProfile.objects.get_or_create(user=instance)
