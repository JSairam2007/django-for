from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import HarvestForm, GardenTaskForm, PlantingForm, PlotForm
from .models import GardenTask, Harvest, Planting, Plot


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
