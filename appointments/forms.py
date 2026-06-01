"""Forms for appointments app."""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from .models import Appointment, Consultation, Review, ChatMessage


class AppointmentBookingForm(forms.ModelForm):
    """Form for patients booking an appointment."""

    class Meta:
        model = Appointment
        fields = ('reason',)
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the reason for your visit...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'reason',
            Submit('submit', 'Confirm Booking', css_class='btn btn-success w-100 mt-3'),
        )


class ConsultationForm(forms.ModelForm):
    """Form for doctors to record consultation details."""

    class Meta:
        model = Consultation
        fields = ('summary', 'prescription', 'follow_up_date')
        widgets = {
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'prescription': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'summary',
            'prescription',
            'follow_up_date',
            Submit('submit', 'Save Consultation', css_class='btn btn-primary mt-3'),
        )


class ReviewForm(forms.ModelForm):
    """Form for patients to review a completed appointment."""

    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Share your experience...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('rating'),
            'comment',
            Submit('submit', 'Submit Review', css_class='btn btn-warning mt-3'),
        )


class ChatMessageForm(forms.ModelForm):
    """Form for sending a chat message."""

    class Meta:
        model = ChatMessage
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Type your message...',
                'style': 'resize:none;',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'content',
        )


class RejectionForm(forms.Form):
    """Form for doctor to reject an appointment with reason."""

    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explain why this appointment request is being rejected...',
        }),
        label='Reason for Rejection',
        required=True,
    )


class RescheduleProposalForm(forms.Form):
    """Form to propose a new time slot for an appointment."""

    proposed_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='New Date',
    )
    proposed_start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='New Start Time',
    )
    proposed_end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='New End Time',
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for rescheduling...',
        }),
        label='Reason for Change',
        required=False,
    )
