from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta
from doctors.models import DoctorProfile, Specialty
from patients.models import PatientProfile
from schedules.models import TimeSlot, Availability

User = get_user_model()


class AppointmentBookingTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(
            name="Cardiologie",
            keywords="coeur",
            icon="fa-heart",
        )
        self.doctor_user = User.objects.create_user(
            username="drbooking",
            password="TestPass123!",
            role="doctor",
            first_name="Doc",
            last_name="Tor",
        )
        self.doctor, _ = DoctorProfile.objects.get_or_create(
            user=self.doctor_user,
            defaults={
                "specialty": self.specialty,
                "consultation_fee": 100,
                "is_active": True,
            },
        )
        self.patient_user = User.objects.create_user(
            username="patbooking",
            password="TestPass123!",
            role="patient",
            first_name="Pat",
            last_name="Ient",
        )
        self.patient = PatientProfile.objects.get(user=self.patient_user)

    def _create_slot(self, is_booked=False):
        slot, _ = TimeSlot.objects.get_or_create(
            doctor=self.doctor,
            date=date.today() + timedelta(days=3),
            start_time=time(10, 0),
            defaults={"end_time": time(10, 30), "is_booked": is_booked},
        )
        return slot

    def test_booking_page_requires_login(self):
        response = self.client.get(reverse("book_appointment"))
        self.assertNotEqual(response.status_code, 200)

    def test_book_appointment_success(self):
        self.client.login(username="patbooking", password="TestPass123!")
        slot = self._create_slot()
        response = self.client.post(
            reverse("book_appointment"),
            {
                "doctor_id": self.doctor.pk,
                "slot_id": slot.pk,
                "reason": "Routine checkup",
            },
        )
        self.assertEqual(response.status_code, 302)
        slot.refresh_from_db()
        self.assertTrue(slot.is_booked)


class AppointmentCancellationTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name="Dermatologie", keywords="peau")
        self.doctor_user = User.objects.create_user(
            username="drcancel", password="TestPass123!", role="doctor"
        )
        self.doctor, _ = DoctorProfile.objects.get_or_create(
            user=self.doctor_user,
            defaults={"specialty": self.specialty, "is_active": True},
        )
        self.patient_user = User.objects.create_user(
            username="patcancel", password="TestPass123!", role="patient"
        )
        self.patient = PatientProfile.objects.get(user=self.patient_user)

    def _create_future_slot(self):
        slot, _ = TimeSlot.objects.get_or_create(
            doctor=self.doctor,
            date=date.today() + timedelta(days=7),
            start_time=time(14, 0),
            defaults={"end_time": time(14, 30), "is_booked": True},
        )
        return slot

    def test_cancel_future_appointment(self):
        from appointments.models import Appointment

        slot = self._create_future_slot()
        appt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            specialty=self.specialty,
            time_slot=slot,
            reason="Test",
            status="pending",
        )
        self.client.login(username="patcancel", password="TestPass123!")
        response = self.client.post(
            reverse("cancel_appointment", kwargs={"pk": appt.pk})
        )
        self.assertEqual(response.status_code, 302)
        appt.refresh_from_db()
        self.assertEqual(appt.status, "cancelled")


class ConflictPreventionTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name="ORL", keywords="oreille")
        self.doctor_user = User.objects.create_user(
            username="drconflict", password="TestPass123!", role="doctor"
        )
        self.doctor, _ = DoctorProfile.objects.get_or_create(
            user=self.doctor_user,
            defaults={"specialty": self.specialty, "is_active": True},
        )
        self.patient1_user = User.objects.create_user(
            username="pat1", password="TestPass123!", role="patient"
        )
        self.patient1 = PatientProfile.objects.get(user=self.patient1_user)
        self.patient2_user = User.objects.create_user(
            username="pat2", password="TestPass123!", role="patient"
        )
        self.patient2 = PatientProfile.objects.get(user=self.patient2_user)

    def test_cannot_double_book_same_slot(self):
        from appointments.models import Appointment

        slot, _ = TimeSlot.objects.get_or_create(
            doctor=self.doctor,
            date=date.today() + timedelta(days=5),
            start_time=time(9, 0),
            defaults={"end_time": time(9, 30), "is_booked": False},
        )
        self.assertFalse(slot.is_booked)

        # First booking — success
        Appointment.objects.create(
            patient=self.patient1,
            doctor=self.doctor,
            specialty=self.specialty,
            time_slot=slot,
            reason="First booking",
            status="confirmed",
        )
        slot.is_booked = True
        slot.save()

        # Second booking with same slot — should raise due to OneToOneField
        with self.assertRaises(Exception):
            Appointment.objects.create(
                patient=self.patient2,
                doctor=self.doctor,
                specialty=self.specialty,
                time_slot=slot,
                reason="Double booking attempt",
                status="confirmed",
            )
