from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import GardenTask, Plot


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
