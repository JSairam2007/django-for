from django import forms

from .models import GardenTask, Harvest, Planting, Plot


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class PlotForm(StyledModelForm):
    class Meta:
        model = Plot
        fields = ["name", "location", "area_sqft", "status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class PlantingForm(StyledModelForm):
    class Meta:
        model = Planting
        fields = ["crop", "variety", "plot", "planted_on", "expected_harvest", "status", "notes"]
        widgets = {
            "planted_on": forms.DateInput(attrs={"type": "date"}),
            "expected_harvest": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        planted_on = cleaned_data.get("planted_on")
        expected_harvest = cleaned_data.get("expected_harvest")
        if planted_on and expected_harvest and expected_harvest < planted_on:
            self.add_error("expected_harvest", "Harvest date must be on or after the planting date.")
        return cleaned_data


class GardenTaskForm(StyledModelForm):
    class Meta:
        model = GardenTask
        fields = ["title", "description", "due_date", "priority", "plot"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class HarvestForm(StyledModelForm):
    class Meta:
        model = Harvest
        fields = ["planting", "harvested_on", "quantity", "unit", "notes"]
        widgets = {"harvested_on": forms.DateInput(attrs={"type": "date"})}
