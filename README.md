# PlotPal

**Live website:** [https://plotpal.onrender.com](https://plotpal.onrender.com)

**GitHub repository:** [JSairam2007/django-for](https://github.com/JSairam2007/django-for)

**Individual task title:** PlotPal — Community Garden Assistant

PlotPal is a responsive Django community-garden website with planting, task, bed, and harvest pages. Its help center contains SQL-backed FAQs and error-code explanations, and the assistant answers from that content, explains supported codes, and creates a SQL support ticket when it cannot find an answer.

## Assessment features

- Responsive garden dashboard and collection pages, plus public FAQ, error-code, and weather pages.
- Assistant widget on the dashboard, public pages, sign-in/sign-up pages, and custom 404/500 pages.
- Twelve seeded FAQs and eight seeded error codes: `400`, `401`, `403`, `404`, `429`, `500`, `503`, and `PP-001`.
- FAQ/error-code/support-ticket data stored in the configured SQL database.
- Chat logs and ratings stored in MongoDB when `MONGODB_URI` is configured.
- Optional OpenAI-compatible answer generation grounded in the matched FAQ or error-code record. Without an AI key, the assistant returns the matching database answer.
- Custom 404 and 500 pages with an “Ask the assistant” action.
- Request logging to the application log and a `/health/` JSON health check.
- Open-Meteo weather integration with a five-second timeout and a garden-care fallback.
- API keys and database credentials are read from environment variables, not source files.

## Configure Render

This repository includes a Render Blueprint in `render.yaml`. After applying it, set these values in the Render service’s environment:

1. `MONGODB_URI` — a MongoDB Atlas connection URI. This is required to persist chat logs and feedback in MongoDB.
2. `OPENAI_API_KEY` — optional; add a valid API key to enable generated responses. The assistant still answers from SQL-backed FAQ/error-code data without it.

Never put either value in GitHub or commit them to the repository. `MONGODB_DATABASE` defaults to `plotpal`; the AI model and endpoint also have safe defaults in the Blueprint.

The Render startup command applies database migrations and safely upserts the sample garden, FAQ, and error-code records.

## Run locally on Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000`, create an account, and explore the help center. To test MongoDB locally, set `MONGODB_URI` in the environment before starting the server.

## Routes and checks

- `/faq/` — database-backed FAQ page
- `/errors/` — supported error-code guide
- `/weather/` — current conditions and fallback advice
- `/health/` — SQL, MongoDB, and assistant-configuration health check
- `/admin/` — manage FAQs, error codes, and support tickets

Run the automated checks with:

```powershell
python manage.py check
python manage.py test
```

To verify the custom not-found page, open a URL such as `https://plotpal.onrender.com/this-page-does-not-exist/`. Test the mobile layout using a phone or browser device emulation.

## Proposed improvement

Add email notifications and a private customer-facing ticket history so visitors can follow up on assistant-created support requests.
