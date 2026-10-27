# PlotPal

PlotPal is a community-garden dashboard for managing garden beds, planting plans, garden tasks, and harvest notes. It is built with Django and SQLite for local development, with PostgreSQL and WhiteNoise configured for Render.

## Run locally on Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000, create an account, and start tending your garden. The sample garden data is shared so the dashboard has something to explore.

## Deploy to Render

1. Push this project to a GitHub repository.
2. In Render, choose **New → Blueprint**, connect the repository, and apply the `render.yaml` blueprint.
3. Wait for the web service and PostgreSQL database to finish provisioning, then open the generated `onrender.com` address and create an account.

The blueprint creates a web service, provisions PostgreSQL, generates a production secret key, collects static assets, applies migrations, and loads sample garden records. The free PostgreSQL plan may have provider-specific limits or availability.

## Useful commands

```powershell
python manage.py test
python manage.py check
python manage.py createsuperuser
```

The Django admin is available at `/admin/` for the site administrator.
