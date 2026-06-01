"""Views for AI orientation — specialty suggestion from symptoms."""

from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .ai_engine import suggest_specialty
from doctors.models import DoctorProfile, Specialty


@method_decorator(login_required, name='dispatch')
class AIOrientationView(TemplateView):
    """Page with symptom input form and AJAX suggestion results."""
    template_name = 'ai_orientation/orient.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['specialties'] = Specialty.objects.all()
        return ctx


def get_suggestion(request):
    """AJAX endpoint — returns specialty suggestions based on symptom text."""
    if request.method == 'POST':
        text = request.POST.get('symptoms', '')
        if not text.strip():
            return JsonResponse({'error': 'Please describe your symptoms'}, status=400)
        suggestions = suggest_specialty(text)
        # Enrich with doctor count for each suggestion
        enriched = []
        for s in suggestions:
            specialty = Specialty.objects.filter(name=s['specialty']).first()
            doctor_count = DoctorProfile.objects.filter(
                specialty=specialty, is_active=True
            ).count() if specialty else 0
            enriched.append({
                'specialty': s['specialty'],
                'confidence': s['confidence'],
                'doctor_count': doctor_count,
                'specialty_id': specialty.pk if specialty else None,
            })
        return JsonResponse({'suggestions': enriched})
    return JsonResponse({'error': 'Invalid method'}, status=405)
