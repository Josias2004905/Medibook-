"""Context processors for global template variables."""

from notifications.models import Notification


def unread_notifications_count(request):
    """Add unread notification count for authenticated users."""
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return {"unread_notifications_count": count}
    return {"unread_notifications_count": 0}
