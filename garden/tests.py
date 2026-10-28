import json
from datetime import date, timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import ErrorCode, FAQ, GardenTask, Plot, SupportTicket


class PlotPalTests(TestCase):
    def setUp(self):
        self.user = self.client.post(
            reverse("garden:signup"),
            {
                "username": "gardenfriend",
                "password1": "a-very-safe-passphrase-47",
                "password2": "a-very-safe-passphrase-47",
            },
        )
        call_command("seed_demo", verbosity=0)

    def test_signup_opens_dashboard(self):
        self.assertEqual(self.user.status_code, 302)
        self.assertRedirects(self.user, reverse("garden:dashboard"))
        self.assertContains(self.client.get(reverse("garden:dashboard")), "Garden beds")

    def test_dashboard_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("garden:dashboard"))
        self.assertRedirects(response, reverse("garden:login"))

    def test_create_plot_and_task(self):
        plot_response = self.client.post(
            reverse("garden:plot_create"),
            {
                "name": "Courtyard bed",
                "location": "By the gate",
                "area_sqft": 20,
                "status": Plot.Status.ACTIVE,
                "notes": "",
            },
        )
        self.assertRedirects(plot_response, reverse("garden:dashboard"))
        plot = Plot.objects.get(name="Courtyard bed")
        task_response = self.client.post(
            reverse("garden:task_create"),
            {
                "title": "Give seedlings a drink",
                "description": "",
                "due_date": (date.today() + timedelta(days=1)).isoformat(),
                "priority": GardenTask.Priority.MEDIUM,
                "plot": plot.pk,
            },
        )
        self.assertRedirects(task_response, reverse("garden:dashboard"))
        self.assertTrue(GardenTask.objects.filter(title="Give seedlings a drink", plot=plot).exists())

    def test_task_completion_requires_post_and_updates_task(self):
        plot = Plot.objects.create(name="North bed")
        task = GardenTask.objects.create(title="Water", due_date=date.today(), plot=plot)
        response = self.client.post(reverse("garden:toggle_task", args=[task.pk]))
        self.assertRedirects(response, reverse("garden:dashboard"))
        task.refresh_from_db()
        self.assertTrue(task.completed)

    def test_signup_page_shows_validation_errors(self):
        self.client.logout()
        response = self.client.post(
            reverse("garden:signup"),
            {"username": "short", "password1": "bad", "password2": "different"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please check the details below")

    def test_public_help_pages_show_chat_widget_and_mobile_viewport(self):
        self.client.logout()
        with patch("garden.views.get_weather", return_value={
            "available": False,
            "temperature": None,
            "description": "Weather unavailable",
            "advice": "Check the soil before watering.",
        }):
            for url in (
                reverse("garden:faq"),
                reverse("garden:error_codes"),
                reverse("garden:weather"),
                reverse("garden:login"),
                reverse("garden:signup"),
            ):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Ask the assistant")
                self.assertContains(response, 'name="viewport"')

    def test_faqs_and_eight_error_codes_are_seeded(self):
        self.assertGreaterEqual(FAQ.objects.count(), 10)
        self.assertEqual(
            set(ErrorCode.objects.values_list("code", flat=True)),
            {"400", "401", "403", "404", "429", "500", "503", "PP-001"},
        )

    def test_chat_answers_from_database_faq_and_logs_to_mongo(self):
        faq = FAQ.objects.get(question="How do I add a garden task?")
        with patch("garden.views.store_mongo_document", return_value=True) as store:
            response = self.client.post(
                reverse("garden:chat"),
                data=json.dumps({"message": "How do I add a garden task?", "conversation_id": "test"}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn(faq.answer, response.json()["answer"])
        self.assertTrue(response.json()["log_saved"])
        store.assert_called_once()

    def test_chat_explains_error_codes(self):
        response = self.client.post(
            reverse("garden:chat"),
            data=json.dumps({"message": "What does error 404 mean?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Page not found", response.json()["answer"])

    def test_unanswered_chat_creates_sql_support_ticket(self):
        with patch("garden.views.store_mongo_document", return_value=True):
            response = self.client.post(
                reverse("garden:chat"),
                data=json.dumps({"message": "Can PlotPal identify a comet in my telescope?"}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        ticket = SupportTicket.objects.get(pk=response.json()["ticket_id"])
        self.assertEqual(ticket.question, "Can PlotPal identify a comet in my telescope?")
        self.assertIn(f"#{ticket.pk}", response.json()["answer"])

    def test_feedback_is_saved_to_mongo(self):
        with patch("garden.views.store_mongo_document", return_value=True) as store:
            response = self.client.post(
                reverse("garden:chat_feedback"),
                data=json.dumps({"rating": 5, "conversation_id": "test"}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        store.assert_called_once()

    def test_unavailable_feedback_storage_is_reported(self):
        with patch("garden.views.store_mongo_document", return_value=False):
            response = self.client.post(
                reverse("garden:chat_feedback"),
                data=json.dumps({"rating": 5}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 503)

    def test_custom_404_has_assistant_action(self):
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Ask the assistant", status_code=404)
        self.assertContains(response, "name=\"viewport\"", status_code=404)

    def test_custom_500_has_assistant_action(self):
        from .views import server_error

        request = RequestFactory().get("/broken/")
        request.user = AnonymousUser()
        response = server_error(request)
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Ask the assistant", status_code=500)

    def test_weather_falls_back_when_provider_times_out(self):
        from .services import get_weather

        with patch("garden.services.urlopen", side_effect=TimeoutError):
            weather = get_weather()
        self.assertFalse(weather["available"])
        self.assertIn("soil", weather["advice"])

    def test_health_endpoint_checks_sql_database(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["database"], "ok")
