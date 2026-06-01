"""Views for appointments app — booking, management, review, chat."""

import json
from datetime import datetime, date, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View, TemplateView
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse

from .models import Appointment, Consultation, Review, ChatMessage
from .forms import (
    AppointmentBookingForm, ConsultationForm, ReviewForm,
    ChatMessageForm, RejectionForm, RescheduleProposalForm,
)
from schedules.models import TimeSlot
from doctors.models import DoctorProfile
from patients.models import PatientProfile
from accounts.mixins import PatientRequiredMixin, DoctorRequiredMixin
from notifications.models import Notification


class AppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'appointments/list.html'
    context_object_name = 'appointments'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related(
            'patient__user', 'doctor__user', 'time_slot', 'specialty',
            'proposed_time_slot',
        )
        status_filter = self.request.GET.get('status', '')
        if user.role == 'patient':
            qs = qs.filter(patient__user=user)
        elif user.role == 'doctor':
            qs = qs.filter(doctor__user=user)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Appointment.STATUS
        ctx['status_filter'] = self.request.GET.get('status', '')
        return ctx


class BookAppointmentView(PatientRequiredMixin, View):
    template_name = 'appointments/book.html'

    def get(self, request):
        doctor_id = request.GET.get('doctor_id')
        slot_id = request.GET.get('slot_id')
        doctor = get_object_or_404(DoctorProfile, pk=doctor_id) if doctor_id else None
        slot = get_object_or_404(TimeSlot, pk=slot_id, is_booked=False) if slot_id else None
        form = AppointmentBookingForm()
        return render(request, self.template_name, {'doctor': doctor, 'slot': slot, 'form': form})

    def post(self, request):
        doctor = get_object_or_404(DoctorProfile, pk=request.POST.get('doctor_id'))
        slot = get_object_or_404(TimeSlot, pk=request.POST.get('slot_id'), is_booked=False)
        patient = get_object_or_404(PatientProfile, user=request.user)
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.patient = patient
            appt.doctor = doctor
            appt.specialty = doctor.specialty
            appt.time_slot = slot
            appt.reason = form.cleaned_data['reason']
            appt.save()
            slot.is_booked = True
            slot.save()
            Notification.create_for_user(
                user=doctor.user,
                title="New Appointment Request",
                message=f"{patient.user.get_full_name()} requested an appointment on {slot.date} at {slot.start_time}.",
                notification_type='appointment',
                link=reverse('appointment_detail', kwargs={'pk': appt.pk}),
            )
            messages.success(request, "Appointment requested successfully! Waiting for doctor's response.")
            return redirect('appointment_detail', pk=appt.pk)
        return render(request, self.template_name, {'doctor': doctor, 'slot': slot, 'form': form})


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    model = Appointment
    template_name = 'appointments/detail.html'
    context_object_name = 'appointment'

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related(
            'patient__user', 'doctor__user', 'time_slot', 'proposed_time_slot',
        )
        if user.role == 'patient':
            return qs.filter(patient__user=user)
        elif user.role == 'doctor':
            return qs.filter(doctor__user=user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        appt = self.get_object()
        ctx['can_review'] = (
            appt.status == 'completed' and
            self.request.user.role == 'patient' and
            not hasattr(appt, 'review')
        )
        ctx['consultation_form'] = ConsultationForm()
        ctx['review_form'] = ReviewForm()
        ctx['chat_form'] = ChatMessageForm()
        ctx['rejection_form'] = RejectionForm()
        ctx['reschedule_form'] = RescheduleProposalForm()
        ctx['chat_messages'] = ChatMessage.objects.filter(
            Q(sender=appt.patient.user, recipient=appt.doctor.user) |
            Q(sender=appt.doctor.user, recipient=appt.patient.user)
        ).order_by('created_at')
        return ctx


class CancelAppointmentView(PatientRequiredMixin, View):
    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk, patient__user=request.user)
        if appt.can_be_cancelled_by_patient:
            appt.status = 'cancelled'
            appt.save()
            appt.time_slot.is_booked = False
            appt.time_slot.save()
            if appt.proposed_time_slot:
                appt.proposed_time_slot.is_booked = False
                appt.proposed_time_slot.save()
            link = reverse('appointment_detail', kwargs={'pk': appt.pk})
            Notification.create_for_user(
                user=appt.patient.user,
                title="Appointment Cancelled",
                message=f"You cancelled your appointment with Dr. {appt.doctor.user.get_full_name()} on {appt.time_slot.date}.",
                notification_type='appointment',
                link=link,
            )
            Notification.create_for_user(
                user=appt.doctor.user,
                title="Appointment Cancelled",
                message=f"{appt.patient.user.get_full_name()} cancelled their appointment on {appt.time_slot.date}.",
                notification_type='appointment',
                link=link,
            )
            messages.warning(request, "Appointment cancelled.")
        else:
            messages.error(request, "Cannot cancel — too close to appointment time.")
        return redirect('appointment_list')


class DoctorCancelAppointmentView(DoctorRequiredMixin, View):
    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk, doctor__user=request.user)
        if appt.status in ('pending', 'confirmed'):
            appt.status = 'cancelled'
            appt.save()
            appt.time_slot.is_booked = False
            appt.time_slot.save()
            if appt.proposed_time_slot:
                appt.proposed_time_slot.is_booked = False
                appt.proposed_time_slot.save()
            link = reverse('appointment_detail', kwargs={'pk': appt.pk})
            Notification.create_for_user(
                user=appt.doctor.user,
                title="Appointment Cancelled",
                message=f"You cancelled the appointment with {appt.patient.user.get_full_name()} on {appt.time_slot.date}.",
                notification_type='appointment',
                link=link,
            )
            Notification.create_for_user(
                user=appt.patient.user,
                title="Appointment Cancelled",
                message=f"Dr. {appt.doctor.user.get_full_name()} cancelled your appointment on {appt.time_slot.date}.",
                notification_type='appointment',
                link=link,
            )
            messages.warning(request, "Appointment cancelled.")
        else:
            messages.error(request, "Cannot cancel appointment at this stage.")
        return redirect('appointment_detail', pk=pk)


class ConfirmAppointmentView(DoctorRequiredMixin, View):
    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk, doctor__user=request.user)
        if appt.status == 'pending':
            appt.status = 'confirmed'
            appt.save()
            Notification.create_for_user(
                user=appt.patient.user,
                title="Appointment Confirmed",
                message=f"Your appointment with Dr. {appt.doctor.user.get_full_name()} on {appt.time_slot.date} at {appt.time_slot.start_time} is confirmed.",
                notification_type='appointment',
                link=reverse('appointment_detail', kwargs={'pk': appt.pk}),
            )
            messages.success(request, "Appointment confirmed.")
        return redirect('appointment_detail', pk=pk)


class CompleteAppointmentView(DoctorRequiredMixin, View):
    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk, doctor__user=request.user)
        form = ConsultationForm(request.POST)
        if form.is_valid() and appt.status == 'confirmed':
            c = form.save(commit=False)
            c.appointment = appt
            c.save()
            appt.status = 'completed'
            appt.save()
            Notification.create_for_user(
                user=appt.patient.user,
                title="Appointment Completed",
                message=f"Your appointment with Dr. {appt.doctor.user.get_full_name()} is complete.",
                notification_type='appointment',
                link=reverse('appointment_detail', kwargs={'pk': appt.pk}),
            )
            messages.success(request, "Appointment marked as completed.")
        else:
            messages.error(request, "Please fill in the consultation form correctly.")
        return redirect('appointment_detail', pk=pk)


class ReviewCreateView(PatientRequiredMixin, View):
    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk, patient__user=request.user, status='completed')
        if hasattr(appt, 'review'):
            messages.warning(request, "Already reviewed.")
            return redirect('appointment_detail', pk=pk)
        form = ReviewForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.appointment = appt
            r.patient = appt.patient
            r.doctor = appt.doctor
            r.save()
            messages.success(request, "Review submitted. Thank you!")
        return redirect('appointment_detail', pk=pk)


# ── New: Reject Appointment ──

class RejectAppointmentView(DoctorRequiredMixin, View):
    """Doctor rejects a pending appointment request with a reason."""

    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk, doctor__user=request.user)
        form = RejectionForm(request.POST)
        if form.is_valid() and appt.status == 'pending':
            appt.status = 'rejected'
            appt.rejection_reason = form.cleaned_data['rejection_reason']
            appt.save()
            appt.time_slot.is_booked = False
            appt.time_slot.save()
            link = reverse('appointment_detail', kwargs={'pk': appt.pk})
            Notification.create_for_user(
                user=appt.patient.user,
                title="Appointment Rejected",
                message=f"Dr. {appt.doctor.user.get_full_name()} has rejected your appointment request. Reason: {appt.rejection_reason}",
                notification_type='appointment',
                link=link,
            )
            Notification.create_for_user(
                user=appt.doctor.user,
                title="Appointment Rejected",
                message=f"You rejected {appt.patient.user.get_full_name()}'s appointment request. Reason: {appt.rejection_reason}",
                notification_type='appointment',
                link=link,
            )
            messages.warning(request, "Appointment request rejected.")
        return redirect('appointment_detail', pk=pk)


# ── New: Reschedule Proposal System ──

class ProposeRescheduleView(LoginRequiredMixin, View):
    """Either party proposes a new time slot for the appointment."""

    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk)
        if request.user not in (appt.patient.user, appt.doctor.user):
            messages.error(request, "Not your appointment.")
            return redirect('appointment_list')
        if appt.status not in ('pending', 'confirmed'):
            messages.error(request, "Cannot reschedule at this stage.")
            return redirect('appointment_detail', pk=pk)

        form = RescheduleProposalForm(request.POST)
        if form.is_valid():
            proposed_date = form.cleaned_data['proposed_date']
            proposed_start = form.cleaned_data['proposed_start_time']
            proposed_end = form.cleaned_data['proposed_end_time']

            if proposed_date <= date.today():
                messages.error(request, "Proposed date must be in the future.")
                return redirect('appointment_detail', pk=pk)

            if proposed_start >= proposed_end:
                messages.error(request, "Start time must be before end time.")
                return redirect('appointment_detail', pk=pk)

            slot, created = TimeSlot.objects.get_or_create(
                doctor=appt.doctor,
                date=proposed_date,
                start_time=proposed_start,
                defaults={
                    'end_time': proposed_end,
                    'is_booked': True,
                },
            )
            if not created and slot.is_booked:
                messages.error(request, "That time slot is already taken.")
                return redirect('appointment_detail', pk=pk)

            slot.is_booked = True
            slot.save()

            if appt.proposed_time_slot and appt.proposed_time_slot != slot:
                appt.proposed_time_slot.is_booked = False
                appt.proposed_time_slot.save()

            reason = form.cleaned_data.get('reason', '')
            appt.proposed_time_slot = slot
            appt.proposed_by = 'doctor' if request.user.role == 'doctor' else 'patient'
            appt.save()

            other_user = appt.patient.user if request.user.role == 'doctor' else appt.doctor.user
            who = "Doctor" if request.user.role == 'doctor' else "Patient"
            msg = f"{who} proposed a new time: {proposed_date} at {proposed_start}."
            if reason:
                msg += f" Reason: {reason}"
            Notification.create_for_user(
                user=other_user,
                title="Reschedule Proposal",
                message=msg,
                notification_type='appointment',
                link=reverse('appointment_detail', kwargs={'pk': appt.pk}),
            )
            messages.success(request, "Reschedule proposed. Waiting for the other party to accept.")
        else:
            messages.error(request, "Invalid form data.")
        return redirect('appointment_detail', pk=pk)


class AcceptRescheduleView(LoginRequiredMixin, View):
    """Accept the proposed reschedule, swapping the time slot."""

    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk)
        if request.user not in (appt.patient.user, appt.doctor.user):
            messages.error(request, "Not your appointment.")
            return redirect('appointment_list')

        if not appt.has_pending_proposal:
            messages.error(request, "No pending proposal to accept.")
            return redirect('appointment_detail', pk=pk)

        if appt.proposed_by == 'doctor' and request.user.role == 'doctor':
            messages.error(request, "Cannot accept your own proposal.")
            return redirect('appointment_detail', pk=pk)
        if appt.proposed_by == 'patient' and request.user.role == 'patient':
            messages.error(request, "Cannot accept your own proposal.")
            return redirect('appointment_detail', pk=pk)

        old_slot = appt.time_slot
        old_slot.is_booked = False
        old_slot.save()

        appt.time_slot = appt.proposed_time_slot
        appt.proposed_time_slot = None
        appt.proposed_by = ''
        if appt.status == 'pending':
            appt.status = 'confirmed'
        appt.save()

        other_user = appt.patient.user if request.user.role == 'doctor' else appt.doctor.user
        who = "Doctor" if request.user.role == 'doctor' else "Patient"
        Notification.create_for_user(
            user=other_user,
            title="Reschedule Accepted",
            message=f"{who} accepted the reschedule. New time: {appt.time_slot.date} at {appt.time_slot.start_time}.",
            notification_type='appointment',
            link=reverse('appointment_detail', kwargs={'pk': appt.pk}),
        )
        messages.success(request, "Reschedule accepted. The time slot has been updated.")
        return redirect('appointment_detail', pk=pk)


class CancelProposalView(LoginRequiredMixin, View):
    """Decline or cancel a pending reschedule proposal."""

    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk)
        if request.user not in (appt.patient.user, appt.doctor.user):
            messages.error(request, "Not your appointment.")
            return redirect('appointment_list')

        if not appt.has_pending_proposal:
            messages.error(request, "No pending proposal to cancel.")
            return redirect('appointment_detail', pk=pk)

        who_cancelled = request.user.role
        other_user = appt.patient.user if who_cancelled == 'doctor' else appt.doctor.user

        appt.proposed_time_slot.is_booked = False
        appt.proposed_time_slot.save()

        appt.proposed_time_slot = None
        appt.proposed_by = ''
        appt.save()

        Notification.create_for_user(
            user=other_user,
            title="Reschedule Declined",
            message=f"The proposed reschedule was declined.",
            notification_type='appointment',
            link=reverse('appointment_detail', kwargs={'pk': appt.pk}),
        )
        messages.info(request, "Reschedule proposal cancelled.")
        return redirect('appointment_detail', pk=pk)


# ── New: Chat / Messaging ──

class SendMessageView(LoginRequiredMixin, View):
    """Send a chat message on the appointment detail page."""

    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk)
        if request.user not in (appt.patient.user, appt.doctor.user):
            messages.error(request, "Not your appointment.")
            return redirect('appointment_list')

        recipient = appt.doctor.user if request.user == appt.patient.user else appt.patient.user
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            ChatMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=form.cleaned_data['content'],
            )
        return redirect('appointment_detail', pk=pk)


class InboxView(LoginRequiredMixin, TemplateView):
    """Show all conversations for the current user."""
    template_name = 'appointments/inbox.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        messages_sent = ChatMessage.objects.filter(sender=user).values_list('recipient', flat=True)
        messages_received = ChatMessage.objects.filter(recipient=user).values_list('sender', flat=True)
        other_user_ids = set(list(messages_sent) + list(messages_received))

        from accounts.models import User as UserModel
        conversations = []
        for other_id in other_user_ids:
            other = UserModel.objects.get(pk=other_id)
            last_msg = ChatMessage.objects.filter(
                Q(sender=user, recipient=other) | Q(sender=other, recipient=user)
            ).order_by('-created_at').first()
            unread = ChatMessage.objects.filter(
                sender=other, recipient=user, is_read=False
            ).count()
            conversations.append({
                'other_user': other,
                'last_message': last_msg,
                'unread_count': unread,
            })

        conversations.sort(key=lambda c: c['last_message'].created_at if c['last_message'] else datetime.min, reverse=True)
        ctx['conversations'] = conversations
        return ctx


class ConversationView(LoginRequiredMixin, TemplateView):
    """Show a conversation thread with a specific user."""
    template_name = 'appointments/chat.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        other_user_id = kwargs.get('user_id')

        from accounts.models import User as UserModel
        other_user = get_object_or_404(UserModel, pk=other_user_id)

        messages_qs = ChatMessage.objects.filter(
            Q(sender=user, recipient=other_user) | Q(sender=other_user, recipient=user)
        ).order_by('created_at')

        ChatMessage.objects.filter(
            sender=other_user, recipient=user, is_read=False
        ).update(is_read=True)

        ctx['other_user'] = other_user
        ctx['chat_messages'] = messages_qs
        ctx['chat_form'] = ChatMessageForm()
        return ctx

    def post(self, request, user_id):
        from accounts.models import User as UserModel
        other_user = get_object_or_404(UserModel, pk=user_id)
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            ChatMessage.objects.create(
                sender=request.user,
                recipient=other_user,
                content=form.cleaned_data['content'],
            )
        return redirect('conversation', user_id=user_id)
