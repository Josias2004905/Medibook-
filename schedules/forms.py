"""Forms for schedules app."""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Availability, DoctorLeave


class AvailabilityForm(forms.ModelForm):
    """Form for setting doctor weekly availability."""

    class Meta:
        model = Availability
        fields = ('day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active')
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'slot_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'max': 120}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'day_of_week',
            Row(Column('start_time', css_class='col-md-4'),
                Column('end_time', css_class='col-md-4'),
                Column('slot_duration', css_class='col-md-4')),
            'is_active',
            Submit('submit', 'Save Availability', css_class='btn btn-primary mt-3'),
        )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned


class DoctorLeaveForm(forms.ModelForm):
    """Form for recording a doctor leave period."""

    class Meta:
        model = DoctorLeave
        fields = ('start_date', 'end_date', 'reason')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('start_date', css_class='col-md-6'), Column('end_date', css_class='col-md-6')),
            'reason',
            Submit('submit', 'Add Leave', css_class='btn btn-warning mt-3'),
        )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and start > end:
            raise forms.ValidationError("End date must be after start date.")
        return cleaned
