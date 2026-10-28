from datetime import date, timedelta

from django.core.management.base import BaseCommand

from garden.models import ErrorCode, FAQ, GardenTask, Harvest, Planting, Plot


FAQS = [
    ("How do I create a PlotPal account?", "Choose Create account on the sign-in page, enter a username and password, and submit the form.", "account signup register"),
    ("How do I add a garden bed?", "Sign in, open Garden beds, and choose Add a garden bed. Enter a name and optional location and area.", "bed plot add garden"),
    ("How do I record a planting?", "Sign in, open What’s growing, choose Plan a planting, select a garden bed, and enter the crop and planting date.", "planting crop seeds"),
    ("How do I add a garden task?", "Choose Add a task on the overview or open the To-do list and add a title, due date, and priority.", "task to-do todo create"),
    ("How do I mark a task complete?", "Select the checkbox next to an open task. The task status is updated immediately.", "complete finish done checklist"),
    ("How do I record a harvest?", "Open Harvest journal and choose Log a harvest. Select the planting, date, quantity, and unit.", "harvest produce log quantity"),
    ("Can I edit or remove a garden entry?", "Use the edit link on an entry to update it. The entry form also provides an option to remove it.", "edit delete remove change"),
    ("How do I check an error code?", "Open Error codes or ask the assistant to explain a code such as 404, 429, or PP-001.", "error code help troubleshoot"),
    ("What happens if the assistant cannot answer?", "PlotPal creates a support ticket in the SQL database and shows its ticket number in the chat.", "support ticket contact unknown"),
    ("Does PlotPal work on a phone?", "Yes. The navigation, garden pages, and assistant widget adapt to narrow mobile screens.", "mobile responsive phone tablet"),
    ("Why is live weather unavailable?", "The weather page uses Open-Meteo with a short timeout. If the provider cannot be reached, PlotPal displays a soil-check watering tip.", "weather forecast open-meteo timeout"),
    ("Where is my garden information stored?", "Garden entries and support tickets are stored in the configured SQL database. Chat conversations and feedback use MongoDB when MONGODB_URI is configured.", "data database privacy storage"),
]

ERROR_CODES = [
    ("400", "Bad request", "The request was incomplete or contained data the site could not process.", "Check the form fields, correct any invalid values, and submit again."),
    ("401", "Sign in required", "This request needs an authenticated account.", "Sign in to PlotPal, then retry the action."),
    ("403", "Request not allowed", "The server understood the request but will not allow it.", "Refresh the page and check that you have permission to perform the action."),
    ("404", "Page not found", "The address does not match a page on this site.", "Check the URL or return to the help page. The custom 404 page can open the assistant."),
    ("429", "Too many requests", "The site is receiving requests too quickly.", "Wait briefly before trying again."),
    ("500", "Server error", "Something unexpected happened while the server handled the request.", "Try again shortly. If the issue continues, ask the assistant to create a support ticket."),
    ("503", "Service unavailable", "The site or one of its services is temporarily unavailable.", "Wait a moment and retry. A third-party outage may resolve on its own."),
    ("PP-001", "Support answer not found", "The assistant could not find a matching FAQ or known error-code explanation.", "A support ticket is created automatically so the question can be followed up."),
]


class Command(BaseCommand):
    help = "Create a small sample garden for a fresh PlotPal installation."

    def handle(self, *args, **options):
        for index, (question, answer, keywords) in enumerate(FAQS, start=1):
            FAQ.objects.get_or_create(
                question=question,
                defaults={"answer": answer, "keywords": keywords, "sort_order": index},
            )
        for index, (code, title, explanation, suggestion) in enumerate(ERROR_CODES, start=1):
            ErrorCode.objects.get_or_create(
                code=code,
                defaults={
                    "title": title,
                    "explanation": explanation,
                    "suggestion": suggestion,
                    "sort_order": index,
                },
            )
        today = date.today()
        bed, _ = Plot.objects.get_or_create(
            name="The Sunny Patch",
            defaults={"location": "North corner", "area_sqft": 32, "status": Plot.Status.ACTIVE},
        )
        herb_bed, _ = Plot.objects.get_or_create(
            name="Little Herb Garden",
            defaults={"location": "By the fence", "area_sqft": 16, "status": Plot.Status.ACTIVE},
        )
        tomato, _ = Planting.objects.get_or_create(
            crop="Tomatoes",
            plot=bed,
            defaults={
                "variety": "Sun Gold",
                "planted_on": today - timedelta(days=42),
                "expected_harvest": today + timedelta(days=16),
            },
        )
        Planting.objects.get_or_create(
            crop="Sweet basil",
            plot=herb_bed,
            defaults={
                "variety": "Genovese",
                "planted_on": today - timedelta(days=21),
                "expected_harvest": today + timedelta(days=28),
            },
        )
        Planting.objects.get_or_create(
            crop="Zucchini",
            plot=bed,
            defaults={
                "variety": "Green Star",
                "planted_on": today - timedelta(days=35),
                "expected_harvest": today + timedelta(days=9),
                "status": Planting.Status.READY,
            },
        )
        GardenTask.objects.get_or_create(
            title="Water the sunny patch",
            defaults={
                "due_date": today,
                "priority": GardenTask.Priority.HIGH,
                "plot": bed,
            },
        )
        GardenTask.objects.get_or_create(
            title="Check leaves for little visitors",
            defaults={
                "due_date": today + timedelta(days=1),
                "priority": GardenTask.Priority.MEDIUM,
                "plot": bed,
            },
        )
        GardenTask.objects.get_or_create(
            title="Pick a few basil leaves",
            defaults={
                "due_date": today + timedelta(days=2),
                "priority": GardenTask.Priority.LOW,
                "plot": herb_bed,
            },
        )
        Harvest.objects.get_or_create(
            planting=tomato,
            harvested_on=today - timedelta(days=1),
            defaults={"quantity": 1.5, "unit": Harvest.Unit.LB},
        )
        self.stdout.write(self.style.SUCCESS("Sample garden data is ready."))
