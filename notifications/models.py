"""Notification model."""

from django.db import models
from accounts.models import User


class Notification(models.Model):
    """In-app notification for users."""

    TYPES = [
        ('appointment', 'Appointment'),
        ('reminder', 'Reminder'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=500, blank=True, help_text="URL to redirect to when clicked")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.user.username}"

    @classmethod
    def create_for_user(cls, user, title, message, notification_type='system', link=''):
        """Convenience method to create a notification."""
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
        )
