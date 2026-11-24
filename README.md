# HealthMate

A simple wellness web application built as a college project. HealthMate offers
general symptom guidance, health education, a habit tracker, a rule-based
wellness assistant and safety information.

> HealthMate provides general educational information only. It does not
> diagnose conditions or replace a qualified healthcare professional.

## Technology

- **Backend:** Python 3.11, Flask
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Accounts and data:** Firebase Authentication, Google Firestore
- **Production server:** gunicorn

## Run it locally

You need Python 3.11 or newer.

**macOS / Linux**

```bash
python3 -m venv venv
venv/bin/pip install -r requirements-dev.txt
venv/bin/flask --app app run --debug --port 5050
```

**Windows (PowerShell)**

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\flask --app app run --debug --port 5050
```

Then open http://127.0.0.1:5050. (Port 5050 is used because macOS often
reserves port 5000.)

## Run the tests

```bash
venv/bin/python -m pytest -q
```

## Project structure

```
healthmate/
├── app.py              # Application factory and page routes
├── config.py           # Settings (from environment variables)
├── templates/          # HTML pages (Jinja2)
├── tests/              # Automated tests (pytest)
├── requirements.txt    # Production dependencies
└── requirements-dev.txt# Adds development tools (pytest)
```

More folders (`static/`, `services/`, `data/`, `docs/`) are added in later phases.

## Build progress

| Phase | Description | Status |
|---|---|---|
| 0 | Project foundation | Done |
| 1 | Design system, layout, static pages | Not started |
| 2 | Health Library | Not started |
| 3 | Symptom Guide | Not started |
| 4 | Wellness Assistant | Not started |
| 5 | Firebase Authentication | Not started |
| 6 | Firestore rules and Habit Tracker | Not started |
| 7 | Dashboard and symptom history | Not started |
| 8 | Hardening and polish | Not started |
| 9 | Deployment | Not started |
