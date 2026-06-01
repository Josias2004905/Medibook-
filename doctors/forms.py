"""Forms for doctors app."""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import DoctorProfile, Specialty


class DoctorProfileForm(forms.ModelForm):
    """Form for updating doctor profile details."""

    class Meta:
        model = DoctorProfile
        fields = ('specialty', 'bio', 'experience_years', 'clinic_address', 'consultation_fee')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'clinic_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'specialty',
            Row(
                Column('experience_years', css_class='col-md-6'),
                Column('consultation_fee', css_class='col-md-6'),
            ),
            'bio',
            'clinic_address',
            Submit('submit', 'Update Profile', css_class='btn btn-primary mt-3'),
        )
        self.fields['specialty'].widget.attrs['class'] = 'form-select'


class SpecialtyForm(forms.ModelForm):
    """Admin form for creating/editing specialties."""

    class Meta:
        model = Specialty
        fields = ('name', 'description', 'keywords', 'icon')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'keywords': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. fa-heart'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            'description',
            'keywords',
            'icon',
            Submit('submit', 'Save Specialty', css_class='btn btn-primary mt-3'),
        )
