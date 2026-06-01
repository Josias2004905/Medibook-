"""Doctor and Specialty models."""

from django.db import models
from accounts.models import User


class Specialty(models.Model):
    """Medical specialty with AI keyword support."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    keywords = models.TextField(help_text="Comma-separated keywords for AI orientation")
    icon = models.CharField(max_length=50, blank=True)  # CSS icon class e.g. 'fa-heart'

    class Meta:
        verbose_name_plural = "Specialties"
        ordering = ['name']

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    """Extended profile for doctors."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.ForeignKey(
        Specialty, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors'
    )
    bio = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    clinic_address = models.TextField(blank=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"

    def update_rating(self):
        """Recalculate the doctor's average rating from reviews."""
        from appointments.models import Review
        reviews = Review.objects.filter(doctor=self)
        if reviews.exists():
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg, 2)
            self.save(update_fields=['rating'])
