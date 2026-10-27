from datetime import date, timedelta

from django.core.management.base import BaseCommand

from garden.models import GardenTask, Harvest, Planting, Plot


class Command(BaseCommand):
    help = "Create a small sample garden for a fresh PlotPal installation."

    def handle(self, *args, **options):
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
