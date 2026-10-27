from django.core.validators import MinValueValidator
from django.db import models


class Plot(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Growing"
        RESTING = "resting", "Resting"

    name = models.CharField(max_length=80, unique=True)
    location = models.CharField(max_length=120, blank=True)
    area_sqft = models.PositiveIntegerField(default=24, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Planting(models.Model):
    class Status(models.TextChoices):
        GROWING = "growing", "Growing"
        READY = "ready", "Ready to harvest"
        HARVESTED = "harvested", "Harvested"

    crop = models.CharField(max_length=80)
    variety = models.CharField(max_length=80, blank=True)
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="plantings")
    planted_on = models.DateField()
    expected_harvest = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.GROWING)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["expected_harvest", "crop"]

    def __str__(self):
        return self.crop


class GardenTask(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    priority = models.CharField(max_length=8, choices=Priority.choices, default=Priority.MEDIUM)
    completed = models.BooleanField(default=False)
    plot = models.ForeignKey(
        Plot, on_delete=models.SET_NULL, related_name="tasks", null=True, blank=True
    )

    class Meta:
        ordering = ["completed", "due_date", "title"]

    def __str__(self):
        return self.title


class Harvest(models.Model):
    class Unit(models.TextChoices):
        LB = "lb", "lb"
        KG = "kg", "kg"
        BUNCHES = "bunches", "bunches"
        EACH = "each", "each"

    planting = models.ForeignKey(Planting, on_delete=models.CASCADE, related_name="harvests")
    harvested_on = models.DateField()
    quantity = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=8, choices=Unit.choices, default=Unit.LB)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-harvested_on", "-id"]

    def __str__(self):
        return f"{self.quantity} {self.get_unit_display()} of {self.planting.crop}"
