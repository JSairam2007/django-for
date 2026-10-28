from django.contrib import admin

from .models import ErrorCode, FAQ, GardenTask, Harvest, Planting, Plot, SupportTicket


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


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "sort_order")
    search_fields = ("question", "answer", "keywords")


@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "sort_order")
    search_fields = ("code", "title", "explanation")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "name", "email", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("question", "name", "email")
