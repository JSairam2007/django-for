import json
import logging

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db import connection
from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import HarvestForm, GardenTaskForm, PlantingForm, PlotForm
from .models import ErrorCode, FAQ, GardenTask, Harvest, Planting, Plot, SupportTicket
from .observability import mongo_health, store_mongo_document
from .services import answer_question, get_weather

logger = logging.getLogger(__name__)


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("garden:login")

    active_plantings = Planting.objects.exclude(status=Planting.Status.HARVESTED)
    context = {
        "plot_count": Plot.objects.count(),
        "active_plantings": active_plantings.count(),
        "task_count": GardenTask.objects.filter(completed=False).count(),
        "harvest_count": Harvest.objects.count(),
        "plots": Plot.objects.all()[:4],
        "plantings": active_plantings.select_related("plot")[:5],
        "tasks": GardenTask.objects.filter(completed=False).select_related("plot")[:5],
        "harvests": Harvest.objects.select_related("planting")[:4],
    }
    return render(request, "garden/dashboard.html", context)


def faq_page(request):
    return render(request, "garden/faq.html", {"faqs": FAQ.objects.all()})


def error_codes_page(request):
    return render(request, "garden/error_codes.html", {"error_codes": ErrorCode.objects.all()})


def weather_page(request):
    return render(request, "garden/weather.html", {"weather": get_weather()})


@require_POST
def chat(request):
    if request.content_type != "application/json":
        return JsonResponse({"error": "Send the message as JSON."}, status=400)
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "The chat request is not valid JSON."}, status=400)

    message = payload.get("message", "") if isinstance(payload, dict) else ""
    conversation_id = payload.get("conversation_id", "") if isinstance(payload, dict) else ""
    if not isinstance(message, str) or not message.strip():
        return JsonResponse({"error": "Please enter a question."}, status=400)
    message = message.strip()
    if len(message) > 1000:
        return JsonResponse({"error": "Please keep your question under 1,000 characters."}, status=400)

    answer = answer_question(message)
    ticket = None
    if answer is None:
        user = request.user
        ticket = SupportTicket.objects.create(
            name=user.get_username() if user.is_authenticated else "",
            email=user.email if user.is_authenticated else "",
            question=message,
        )
        answer = (
            "I couldn’t find a reliable answer in the help articles, so I created "
            f"support ticket #{ticket.pk}. Our team can follow up when contact details are available."
        )

    log_saved = store_mongo_document("chat_logs", {
        "conversation_id": str(conversation_id)[:80],
        "question": message,
        "answer": answer,
        "ticket_id": ticket.pk if ticket else None,
        "user_id": request.user.pk if request.user.is_authenticated else None,
    })
    return JsonResponse({
        "answer": answer,
        "ticket_id": ticket.pk if ticket else None,
        "log_saved": log_saved,
    })


@require_POST
def chat_feedback(request):
    if request.content_type != "application/json":
        return JsonResponse({"error": "Send feedback as JSON."}, status=400)
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "The feedback request is not valid JSON."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Feedback must be a JSON object."}, status=400)
    rating = payload.get("rating")
    if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
        return JsonResponse({"error": "Choose a rating from 1 to 5."}, status=400)
    feedback = str(payload.get("feedback", "")).strip()
    if len(feedback) > 1000:
        return JsonResponse({"error": "Feedback must be 1,000 characters or fewer."}, status=400)

    saved = store_mongo_document("chat_feedback", {
        "rating": rating,
        "feedback": feedback,
        "conversation_id": str(payload.get("conversation_id", ""))[:80],
    })
    if not saved:
        return JsonResponse({"error": "Feedback storage is unavailable. Please try again later."}, status=503)
    return JsonResponse({"saved": True})


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        logger.exception("Health check could not reach the SQL database.")
        return JsonResponse({"status": "unhealthy", "database": "unavailable"}, status=503)
    mongodb_status = mongo_health()
    return JsonResponse({
        "status": "ok" if mongodb_status == "ok" else "degraded",
        "database": "ok",
        "mongodb": mongodb_status,
    })


def page_not_found(request, exception):
    return render(request, "404.html", status=404)


def server_error(request):
    return render(request, "500.html", status=500)


class RegisterView(View):
    template_name = "registration/signup.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("garden:dashboard")
        return render(request, self.template_name, {"form": UserCreationForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("garden:dashboard")
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("garden:dashboard")
        return render(request, self.template_name, {"form": form})


class GardenLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


class GardenLogoutView(LogoutView):
    next_page = reverse_lazy("garden:login")


class EntryCreateView(LoginRequiredMixin, CreateView):
    template_name = "garden/entry_form.html"
    success_url = reverse_lazy("garden:dashboard")


class EntryUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "garden/entry_form.html"
    success_url = reverse_lazy("garden:dashboard")


class EntryDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "garden/entry_confirm_delete.html"
    success_url = reverse_lazy("garden:dashboard")


class PlotCreateView(EntryCreateView):
    model = Plot
    form_class = PlotForm
    extra_context = {"page_title": "Add a garden bed", "eyebrow": "YOUR GARDEN"}


class PlotUpdateView(EntryUpdateView):
    model = Plot
    form_class = PlotForm
    extra_context = {"page_title": "Edit garden bed", "eyebrow": "YOUR GARDEN"}


class PlotDeleteView(EntryDeleteView):
    model = Plot
    extra_context = {"page_title": "Remove garden bed"}


class PlantingCreateView(EntryCreateView):
    model = Planting
    form_class = PlantingForm
    extra_context = {"page_title": "Plan a planting", "eyebrow": "GROWING"}


class PlantingUpdateView(EntryUpdateView):
    model = Planting
    form_class = PlantingForm
    extra_context = {"page_title": "Edit planting", "eyebrow": "GROWING"}


class PlantingDeleteView(EntryDeleteView):
    model = Planting
    extra_context = {"page_title": "Remove planting"}


class TaskCreateView(EntryCreateView):
    model = GardenTask
    form_class = GardenTaskForm
    extra_context = {"page_title": "Add a garden task", "eyebrow": "TO-DO LIST"}


class TaskUpdateView(EntryUpdateView):
    model = GardenTask
    form_class = GardenTaskForm
    extra_context = {"page_title": "Edit garden task", "eyebrow": "TO-DO LIST"}


class TaskDeleteView(EntryDeleteView):
    model = GardenTask
    extra_context = {"page_title": "Remove garden task"}


class HarvestCreateView(EntryCreateView):
    model = Harvest
    form_class = HarvestForm
    extra_context = {"page_title": "Log a harvest", "eyebrow": "HARVEST LOG"}


class HarvestUpdateView(EntryUpdateView):
    model = Harvest
    form_class = HarvestForm
    extra_context = {"page_title": "Edit harvest", "eyebrow": "HARVEST LOG"}


class HarvestDeleteView(EntryDeleteView):
    model = Harvest
    extra_context = {"page_title": "Remove harvest"}


def collection(request, collection_type):
    if not request.user.is_authenticated:
        return redirect("garden:login")

    collections = {
        "plots": {
            "title": "Your garden beds",
            "eyebrow": "THE GARDEN",
            "items": Plot.objects.all(),
            "add_url": "garden:plot_create",
        },
        "plantings": {
            "title": "What's growing",
            "eyebrow": "GROWING",
            "items": Planting.objects.select_related("plot").all(),
            "add_url": "garden:planting_create",
        },
        "tasks": {
            "title": "Garden to-do list",
            "eyebrow": "A LITTLE EACH DAY",
            "items": GardenTask.objects.select_related("plot").all(),
            "add_url": "garden:task_create",
        },
        "harvests": {
            "title": "Your harvest journal",
            "eyebrow": "GOOD THINGS GROW",
            "items": Harvest.objects.select_related("planting").all(),
            "add_url": "garden:harvest_create",
        },
    }
    page = collections.get(collection_type)
    if page is None:
        return redirect("garden:dashboard")
    return render(
        request,
        "garden/collection.html",
        {"collection_type": collection_type, **page},
    )


@require_POST
def toggle_task(request, pk):
    if not request.user.is_authenticated:
        return redirect("garden:login")
    task = get_object_or_404(GardenTask, pk=pk)
    task.completed = not task.completed
    task.save(update_fields=["completed"])
    return redirect(request.POST.get("next") or "garden:dashboard")
