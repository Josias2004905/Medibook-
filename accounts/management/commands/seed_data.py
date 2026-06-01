"""Management command to seed the database with initial data."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time, date, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with specialties, users, doctors, appointments"

    def handle(self, *args, **kwargs):
        self._create_specialties()
        self._create_admin()
        self._create_doctors()
        self._create_patients()
        self._create_availabilities()
        self._create_appointments()
        self.stdout.write(self.style.SUCCESS("Database seeded successfully"))

    def _create_specialties(self):
        from doctors.models import Specialty
        specialties_data = [
            {"name": "Cardiologie", "keywords": "coeur,arythmie,hypertension,infarctus,tachycardie", "icon": "fa-heart", "description": "Heart and cardiovascular system"},
            {"name": "Dermatologie", "keywords": "peau,boutons,acné,eczéma,psoriasis", "icon": "fa-hand", "description": "Skin, hair, and nail conditions"},
            {"name": "Pédiatrie", "keywords": "enfant,bébé,fièvre,nourrisson,vaccin", "icon": "fa-child", "description": "Medical care for infants, children, and adolescents"},
            {"name": "Gynécologie", "keywords": "femme,grossesse,menstruation,contraception", "icon": "fa-venus", "description": "Female reproductive health"},
            {"name": "Ophtalmologie", "keywords": "yeux,vision,vue,flou,lunettes,cataracte", "icon": "fa-eye", "description": "Eye and vision care"},
            {"name": "Dentisterie", "keywords": "dents,douleur,dentaire,caries,gencives", "icon": "fa-tooth", "description": "Oral health and dental care"},
            {"name": "ORL", "keywords": "oreille,nez,gorge,sinusite,angine,otite", "icon": "fa-ear-listen", "description": "Ear, nose, and throat"},
            {"name": "Neurologie", "keywords": "tête,migraine,mémoire,vertige,épilepsie", "icon": "fa-brain", "description": "Brain and nervous system"},
            {"name": "Radiologie", "keywords": "radio,scanner,IRM,imagerie,os,fracture", "icon": "fa-x-ray", "description": "Medical imaging and diagnostics"},
            {"name": "Médecine Générale", "keywords": "fièvre,fatigue,rhume,grippe,douleur", "icon": "fa-stethoscope", "description": "General primary care"},
        ]
        for spec in specialties_data:
            Specialty.objects.get_or_create(name=spec["name"], defaults=spec)
        self.stdout.write(f"Created {len(specialties_data)} specialties")

    def _create_admin(self):
        if User.objects.filter(email="admin@medibook.com").exists():
            return
        User.objects.create_superuser(
            username="admin",
            email="admin@medibook.com",
            password="Admin123!",
            first_name="Admin",
            last_name="User",
            role="admin",
        )
        self.stdout.write("Created admin user")

    def _create_doctors(self):
        from doctors.models import DoctorProfile, Specialty
        doctors_data = [
            {"first_name": "Sophie", "last_name": "Leroy", "username": "drleroy", "specialty": "Cardiologie", "bio": "Cardiologue avec 15 ans d'expérience en rythmologie.", "experience_years": 15, "fee": 120},
            {"first_name": "Marc", "last_name": "Dubois", "username": "drdubois", "specialty": "Dermatologie", "bio": "Dermatologue spécialisé en cancérologie cutanée.", "experience_years": 12, "fee": 100},
            {"first_name": "Julie", "last_name": "Petit", "username": "drpetit", "specialty": "Pédiatrie", "bio": "Pédiatre passionnée par la santé des enfants.", "experience_years": 10, "fee": 90},
            {"first_name": "Thomas", "last_name": "Moreau", "username": "drmoreau", "specialty": "Ophtalmologie", "bio": "Chirurgien ophtalmologue spécialiste de la cataracte.", "experience_years": 18, "fee": 130},
            {"first_name": "Camille", "last_name": "Bernard", "username": "drbernard", "specialty": "Médecine Générale", "bio": "Médecin généraliste à l'écoute de ses patients.", "experience_years": 8, "fee": 60},
        ]
        specialties = {s.name: s for s in Specialty.objects.all()}
        for doc in doctors_data:
            if User.objects.filter(username=doc["username"]).exists():
                continue
            user = User.objects.create_user(
                username=doc["username"],
                email=f"{doc['username']}@medibook.com",
                password=f"{doc['username']}123",
                first_name=doc["first_name"],
                last_name=doc["last_name"],
                role="doctor",
            )
            DoctorProfile.objects.update_or_create(
                user=user,
                defaults={
                    "specialty": specialties.get(doc["specialty"]),
                    "bio": doc["bio"],
                    "experience_years": doc["experience_years"],
                    "consultation_fee": doc["fee"],
                    "clinic_address": f"123 Rue de la Santé, Paris",
                    "is_active": True,
                    "rating": round(random.uniform(3.5, 5.0), 2),
                },
            )
        self.stdout.write(f"Created {len(doctors_data)} doctors")

    def _create_patients(self):
        from patients.models import PatientProfile
        patients_data = [
            {"first_name": "Alice", "last_name": "Martin", "username": "alice"},
            {"first_name": "Bob", "last_name": "Durand", "username": "bob"},
            {"first_name": "Claire", "last_name": "Lefevre", "username": "claire"},
            {"first_name": "David", "last_name": "Roux", "username": "david"},
            {"first_name": "Emma", "last_name": "Fournier", "username": "emma"},
            {"first_name": "Francois", "last_name": "Girard", "username": "francois"},
            {"first_name": "Gaelle", "last_name": "Bonnet", "username": "gaelle"},
            {"first_name": "Hugo", "last_name": "Lambert", "username": "hugo"},
            {"first_name": "Isabelle", "last_name": "Vincent", "username": "isabelle"},
            {"first_name": "Jerome", "last_name": "Gauthier", "username": "jerome"},
        ]
        for pat in patients_data:
            if User.objects.filter(username=pat["username"]).exists():
                continue
            user = User.objects.create_user(
                username=pat["username"],
                email=f"{pat['username']}@example.com",
                password="Patient123!",
                first_name=pat["first_name"],
                last_name=pat["last_name"],
                role="patient",
            )
            PatientProfile.objects.update_or_create(
                user=user,
                defaults={
                    "date_of_birth": timezone.now().date() - timedelta(days=random.randint(7000, 20000)),
                    "address": f"{random.randint(1, 200)} Avenue de la République, Paris",
                },
            )
        self.stdout.write(f"Created {len(patients_data)} patients")

    def _create_availabilities(self):
        from doctors.models import DoctorProfile
        from schedules.models import Availability
        doctors = DoctorProfile.objects.filter(is_active=True)
        count = 0
        for doctor in doctors:
            for day in range(5):
                _, created = Availability.objects.get_or_create(
                    doctor=doctor,
                    day_of_week=day,
                    start_time=time(9, 0),
                    defaults={
                        "end_time": time(17, 0),
                        "slot_duration": 30,
                        "is_active": True,
                    },
                )
                if created:
                    count += 1
        self.stdout.write(f"Created {count} availability rules")

    def _create_appointments(self):
        from doctors.models import DoctorProfile
        from patients.models import PatientProfile
        from appointments.models import Appointment
        from schedules.utils import generate_slots_for_date
        today = timezone.now().date()
        doctors = list(DoctorProfile.objects.filter(is_active=True))
        patients = list(PatientProfile.objects.all())
        if not doctors or not patients:
            return
        count = 0
        for i, doctor in enumerate(doctors):
            for day_offset in range(1, 6):
                target = today + timedelta(days=day_offset)
                slots = generate_slots_for_date(doctor, target)
                if slots:
                    patient = patients[i % len(patients)]
                    slot = slots[0]
                    if not hasattr(slot, "appointment"):
                        Appointment.objects.get_or_create(
                            time_slot=slot,
                            defaults={
                                "patient": patient,
                                "doctor": doctor,
                                "specialty": doctor.specialty,
                                "reason": f"Consultation de routine",
                                "status": "pending",
                            },
                        )
                        slot.is_booked = True
                        slot.save()
                        count += 1
        self.stdout.write(f"Created {count} sample appointments")
