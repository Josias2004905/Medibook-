"""URL patterns for AI orientation app."""

from django.urls import path
from . import views

urlpatterns = [
    path('orient/', views.AIOrientationView.as_view(), name='ai_orientation'),
    path('suggest/', views.get_suggestion, name='ai_suggest'),
]
