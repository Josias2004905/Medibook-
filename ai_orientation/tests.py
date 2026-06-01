from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from ai_orientation.ai_engine import suggest_specialty

User = get_user_model()


class AIEngineTest(TestCase):
    def test_cardiac_symptoms_return_cardiologie(self):
        results = suggest_specialty("douleur thoracique palpitations essoufflement")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["specialty"], "Cardiologie")
        self.assertGreater(results[0]["confidence"], 0)

    def test_dental_pain_returns_dentisterie(self):
        results = suggest_specialty("j'ai mal aux dents caries douleur dentaire")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["specialty"], "Dentisterie")

    def test_skin_symptoms_return_dermatologie(self):
        results = suggest_specialty("boutons rougeurs acné peau qui gratte")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["specialty"], "Dermatologie")

    def test_empty_input_returns_medecine_generale(self):
        results = suggest_specialty("")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["specialty"], "Médecine Générale")
        self.assertEqual(results[0]["confidence"], 100.0)

    def test_whitespace_input_returns_medecine_generale(self):
        results = suggest_specialty("   ")
        self.assertEqual(results[0]["specialty"], "Médecine Générale")

    def test_returns_top_n_results(self):
        results = suggest_specialty("fièvre fatigue toux", top_n=2)
        self.assertLessEqual(len(results), 2)

    def test_all_results_have_positive_confidence(self):
        results = suggest_specialty("migraine vertige tête")
        for r in results:
            self.assertGreater(r["confidence"], 0)


class AIEndpointTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="aitester",
            password="TestPass123!",
            role="patient",
        )

    def test_orient_page_requires_login(self):
        response = self.client.get(reverse("ai_orientation"))
        self.assertEqual(response.status_code, 302)

    def test_orient_page_accessible_when_logged_in(self):
        self.client.login(username="aitester", password="TestPass123!")
        response = self.client.get(reverse("ai_orientation"))
        self.assertEqual(response.status_code, 200)

    def test_suggest_endpoint_returns_json(self):
        self.client.login(username="aitester", password="TestPass123!")
        response = self.client.post(
            reverse("ai_suggest"),
            {"symptoms": "douleur thoracique"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("suggestions", data)

    def test_suggest_endpoint_empty_input(self):
        self.client.login(username="aitester", password="TestPass123!")
        response = self.client.post(reverse("ai_suggest"), {"symptoms": ""})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_suggest_endpoint_get_method_returns_405(self):
        self.client.login(username="aitester", password="TestPass123!")
        response = self.client.get(reverse("ai_suggest"))
        self.assertEqual(response.status_code, 405)

    def test_suggest_result_includes_specialty_id_and_doctor_count(self):
        self.client.login(username="aitester", password="TestPass123!")
        response = self.client.post(
            reverse("ai_suggest"),
            {"symptoms": "douleur thoracique coeur"},
        )
        data = response.json()
        for s in data["suggestions"]:
            self.assertIn("specialty", s)
            self.assertIn("confidence", s)
            self.assertIn("doctor_count", s)
