from django.contrib import admin

from .models import GardenTask, Harvest, Planting, Plot


@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "area_sqft", "status")
    list_filter = ("status",)
    search_fields = ("name", "location")


@admin.register(Planting)
class PlantingAdmin(admin.ModelAdmin):
    list_display = ("crop", "variety", "plot", "planted_on", "expected_harvest", "status")
    list_filter = ("status", "plot")
    search_fields = ("crop", "variety")


@admin.register(GardenTask)
class GardenTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "due_date", "priority", "completed", "plot")
    list_filter = ("completed", "priority")
    search_fields = ("title",)


@admin.register(Harvest)
class HarvestAdmin(admin.ModelAdmin):
    list_display = ("planting", "harvested_on", "quantity", "unit")
    list_filter = ("harvested_on",)
