"""Slot generation utility for doctor schedules."""

from datetime import datetime, timedelta, date
from schedules.models import TimeSlot, Availability, DoctorLeave


def generate_slots_for_date(doctor, target_date: date):
    """
    Generate TimeSlot objects for a doctor on a specific date.

    Respects leave periods and existing slots (uses get_or_create to avoid duplicates).
    Returns a list of TimeSlot objects.
    """
    # Check if doctor is on leave for the target date
    if DoctorLeave.objects.filter(
        doctor=doctor,
        start_date__lte=target_date,
        end_date__gte=target_date
    ).exists():
        TimeSlot.objects.filter(doctor=doctor, date=target_date, is_booked=False).delete()
        return []

    day_of_week = target_date.weekday()
    availabilities = Availability.objects.filter(
        doctor=doctor,
        day_of_week=day_of_week,
        is_active=True
    )

    slots = []
    for availability in availabilities:
        current = datetime.combine(target_date, availability.start_time)
        end = datetime.combine(target_date, availability.end_time)
        duration = timedelta(minutes=availability.slot_duration)

        while current + duration <= end:
            slot, created = TimeSlot.objects.get_or_create(
                doctor=doctor,
                date=target_date,
                start_time=current.time(),
                defaults={
                    'end_time': (current + duration).time(),
                    'is_booked': False,
                }
            )
            slots.append(slot)
            current += duration

    return slots


def get_available_slots_for_week(doctor, start_date: date, days: int = 7):
    """Generate and return available (unbooked) slots for a date range."""
    all_slots = {}
    for i in range(days):
        target = start_date + timedelta(days=i)
        day_slots = generate_slots_for_date(doctor, target)
        available = [s for s in day_slots if not s.is_booked]
        if available:
            all_slots[target.isoformat()] = available
    return all_slots
