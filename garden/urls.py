from django.urls import path

from . import views

app_name = "garden"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("faq/", views.faq_page, name="faq"),
    path("errors/", views.error_codes_page, name="error_codes"),
    path("weather/", views.weather_page, name="weather"),
    path("assistant/chat/", views.chat, name="chat"),
    path("assistant/feedback/", views.chat_feedback, name="chat_feedback"),
    path("accounts/login/", views.GardenLoginView.as_view(), name="login"),
    path("accounts/signup/", views.RegisterView.as_view(), name="signup"),
    path("accounts/logout/", views.GardenLogoutView.as_view(), name="logout"),
    path("garden/<str:collection_type>/", views.collection, name="collection"),
    path("garden/tasks/<int:pk>/toggle/", views.toggle_task, name="toggle_task"),
    path("garden/plots/add/", views.PlotCreateView.as_view(), name="plot_create"),
    path("garden/plots/<int:pk>/edit/", views.PlotUpdateView.as_view(), name="plot_edit"),
    path("garden/plots/<int:pk>/delete/", views.PlotDeleteView.as_view(), name="plot_delete"),
    path("garden/plantings/add/", views.PlantingCreateView.as_view(), name="planting_create"),
    path("garden/plantings/<int:pk>/edit/", views.PlantingUpdateView.as_view(), name="planting_edit"),
    path("garden/plantings/<int:pk>/delete/", views.PlantingDeleteView.as_view(), name="planting_delete"),
    path("garden/tasks/add/", views.TaskCreateView.as_view(), name="task_create"),
    path("garden/tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_edit"),
    path("garden/tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
    path("garden/harvests/add/", views.HarvestCreateView.as_view(), name="harvest_create"),
    path("garden/harvests/<int:pk>/edit/", views.HarvestUpdateView.as_view(), name="harvest_edit"),
    path("garden/harvests/<int:pk>/delete/", views.HarvestDeleteView.as_view(), name="harvest_delete"),
]
