"""Appointment, Consultation, Review, and ChatMessage models."""

from django.db import models
from accounts.models import User
from patients.models import PatientProfile
from doctors.models import DoctorProfile, Specialty
from schedules.models import TimeSlot


class Appointment(models.Model):
    """Core appointment linking patient, doctor, and time slot."""

    STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('rejected', 'Rejected'),
    ]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    time_slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE, related_name='appointment')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    notes = models.TextField(blank=True)
    proposed_by = models.CharField(max_length=20, blank=True)
    proposed_time_slot = models.ForeignKey(
        TimeSlot, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='proposed_appointments'
    )
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient} → Dr.{self.doctor} on {self.time_slot.date}"

    @property
    def can_be_cancelled_by_patient(self):
        """Patient can only cancel if appointment is > 2 hours away."""
        from datetime import datetime, timedelta
        slot_datetime = datetime.combine(self.time_slot.date, self.time_slot.start_time)
        now = datetime.now()
        return (slot_datetime - now) > timedelta(hours=2) and self.status in ('pending', 'confirmed')

    @property
    def has_pending_proposal(self):
        return bool(self.proposed_by and self.proposed_time_slot)


class Consultation(models.Model):
    """Post-appointment consultation record created by doctor."""

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='consultation')
    summary = models.TextField()
    prescription = models.TextField(blank=True)
    follow_up_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation for {self.appointment}"


class Review(models.Model):
    """Patient review of a completed appointment."""

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='reviews')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.patient} for {self.doctor} — {self.rating}★"

    def save(self, *args, **kwargs):
        """Update doctor rating after saving a review."""
        super().save(*args, **kwargs)
        self.doctor.update_rating()


class ChatMessage(models.Model):
    """Direct messaging between patients and doctors."""

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.content[:50]}"
