"""URL patterns for appointments app."""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.AppointmentListView.as_view(), name='appointment_list'),
    path('book/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('<int:pk>/cancel/', views.CancelAppointmentView.as_view(), name='cancel_appointment'),
    path('<int:pk>/doctor-cancel/', views.DoctorCancelAppointmentView.as_view(), name='doctor_cancel_appointment'),
    path('<int:pk>/confirm/', views.ConfirmAppointmentView.as_view(), name='confirm_appointment'),
    path('<int:pk>/complete/', views.CompleteAppointmentView.as_view(), name='complete_appointment'),
    path('<int:pk>/review/', views.ReviewCreateView.as_view(), name='create_review'),
    path('<int:pk>/reject/', views.RejectAppointmentView.as_view(), name='reject_appointment'),
    path('<int:pk>/propose-reschedule/', views.ProposeRescheduleView.as_view(), name='propose_reschedule'),
    path('<int:pk>/accept-reschedule/', views.AcceptRescheduleView.as_view(), name='accept_reschedule'),
    path('<int:pk>/cancel-proposal/', views.CancelProposalView.as_view(), name='cancel_proposal'),
    path('<int:pk>/send-message/', views.SendMessageView.as_view(), name='send_message'),
    path('inbox/', views.InboxView.as_view(), name='inbox'),
    path('conversation/<int:user_id>/', views.ConversationView.as_view(), name='conversation'),
]
