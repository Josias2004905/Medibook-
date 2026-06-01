"""URL patterns for notifications app."""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/read/', views.MarkReadView.as_view(), name='mark_notification_read'),
    path('read-all/', views.MarkAllReadView.as_view(), name='mark_all_read'),
]
