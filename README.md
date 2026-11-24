# HealthMate

A simple, professional wellness web application, built as a college project.

HealthMate helps people build healthier habits, explore general symptom
guidance and find trustworthy wellness information in one place.

> **HealthMate gives general educational information only.** It does not
> diagnose conditions and does not replace a qualified healthcare
> professional. In an emergency in India, call **112**.

---

## Features

| Feature | Who can use it | What it does |
|---|---|---|
| **Symptom Guide** | Everyone | A six-step form (warning signs first). Returns one of three levels (*Self-care*, *See a doctor*, *Urgent care*) with the reasons, next steps and when to get help sooner. Signed-in users can choose to save the result. |
| **Wellness Assistant** | Everyone | A chat window with **pre-written answers** on sleep, stress, activity, eating and hydration. Possible emergencies get safety guidance instead. Not AI. Nothing is stored. |
| **Health Library** | Everyone | 13 short articles in 6 categories, each with its own page. |
| **Safety Center** | Everyone | Indian emergency numbers (112, 108, Tele-MANAS 14416), warning signs and what to do. Linked from every page. |
| **Accounts** | Everyone | Sign up and log in with email or Google, reset password, log out. |
| **Habit Tracker** | Signed-in users | Add, tick off, untick and delete daily habits in 6 categories. Today's progress bar. |
| **Dashboard** | Signed-in users | Today's numbers, habits (tickable), recent saved symptom checks, quick actions. |

## Technology

| Part | Technology |
|---|---|
| Server | Python 3.11, Flask 3.1, gunicorn |
| Pages | Jinja2 templates, one CSS file, vanilla JavaScript (ES modules, no build step) |
| Accounts | Firebase Authentication (email/password and Google) |
| Database | Google Cloud Firestore |
| Hosting | Render (web service) |
| Tests | pytest |

No front-end framework, no npm, no server database.

## Architecture

```
            Browser (HTML, CSS, JavaScript)
             │                         │
   pages and /api/ calls          sign-in and user data
             ▼                         ▼
    Flask on Render              Firebase (Google)
    - renders pages              - Authentication
    - /api/symptom-check         - Firestore database,
    - /api/assistant               protected by firestore.rules
    - stores nothing
```

* **Flask is stateless.** It serves pages and runs the two rule engines
  (Symptom Guide and Assistant) in Python. It never sees passwords or user data.
* **The browser talks directly to Firebase** for sign-in and to read and write
  the user's own habits and saved checks.
* **Firestore security rules** (`firestore.rules`) are the real protection:
  Google's servers check every read and write, so a user can only ever access
  `users/{their own id}/…`.

### Data stored in Firestore

```
users/{uid}                       displayName (first name), createdAt
users/{uid}/habits/{id}           name, category, createdAt
users/{uid}/habitLogs/{date}      completed: [habit ids], updatedAt     (one per day)
users/{uid}/symptomChecks/{id}    symptoms, duration, severity, ageGroup, level, createdAt
```

Symptom descriptions, warning-sign answers and assistant chats are **never** stored.

### Project structure

```
healthmate/
├── app.py                 Builds the Flask app (settings, blueprints, security)
├── config.py              Settings from environment variables
├── security.py            Security headers and Content-Security-Policy
├── content.py             Loads JSON files from data/
├── gunicorn.conf.py       Production web server settings
├── render.yaml            Render deployment settings
├── firestore.rules        Firestore security rules (publish in Firebase)
├── routes/
│   ├── pages.py           Every HTML page
│   ├── api.py             /api/symptom-check and /api/assistant
│   └── errors.py          404 / 405 / 413 / 500 pages (JSON for /api/)
├── services/
│   ├── symptom_engine.py  Symptom Guide rules (safety first)
│   ├── assistant.py       Wellness Assistant answers
│   ├── text_safety.py     Spots possible emergency words in free text
│   └── library.py         Health Library content
├── data/                  All content as JSON (safety info, library, symptoms, assistant)
├── templates/             Jinja2 pages and partials
├── static/
│   ├── css/main.css       Design system and all styles
│   └── js/                One small module per job (see comments in each file)
├── tests/                 Automated tests (pytest)
└── docs/                  Deployment guide and QA report
```

---

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

Open http://127.0.0.1:5050. Port 5050 is used because macOS often reserves 5000.

The site works straight away. Sign-in, the Dashboard and the Habit Tracker
need Firebase (next section).

> Content in `data/*.json` is read when the server starts. After editing a
> JSON file, stop and start the server to see the change.

## Environment variables

HealthMate needs **no secrets**. Optional settings (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Set to `production` on the live server: adds HTTPS-only (HSTS) headers and trusts the host's HTTPS proxy. |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO` or `WARNING`. |
| `PORT` | `8000` | Port gunicorn listens on. Render sets this automatically. |
| `WEB_CONCURRENCY` | `2` | Number of gunicorn worker processes. |

## Set up Firebase

All of these steps are done by you, in the Firebase console:
https://console.firebase.google.com

1. **Create a project** (e.g. `healthmate`). Google Analytics is not needed.
2. **Register a web app**: Project overview → `</>` (Web) → nickname → Register.
   Firebase Hosting is not needed.
3. **Copy the config** values `apiKey`, `authDomain`, `projectId` and `appId`
   into `static/js/firebase-config.js`. These are public identifiers, not
   secrets: every Firebase website exposes them.
4. **Turn on sign-in methods**: Build → Authentication → Get started →
   Sign-in method → enable **Email/Password**, and **Google** (choose a
   support email).
5. **Authorised domains**: Authentication → Settings → Authorized domains.
   `localhost` is there by default. Add `127.0.0.1`, your Render address
   (e.g. `healthmate-xxxx.onrender.com`) and your custom domain.
6. **Create Firestore**: Build → Firestore Database → Create database →
   location near your users (e.g. `asia-south1`, Mumbai) → **production mode**.
7. **Publish the rules**: Firestore Database → Rules → replace everything with
   the contents of `firestore.rules` → **Publish**.
   *The rules protect nothing until they are published.*
8. *(Recommended)* **Restrict the API key**: Google Cloud console → APIs &
   Services → Credentials → "Browser key (auto created by Firebase)" →
   Website restrictions → add `localhost`, `127.0.0.1`, your Render address
   and your domain.

Firestore creates the `users/...` collections automatically the first time
the app writes to them. No indexes need to be created.

## Testing

```bash
venv/bin/python -m pytest -q
```

213 automated tests cover every page and link, the Symptom Guide safety rules,
the Assistant, the Library, the APIs, input validation, security headers,
XSS protections and configuration. See `docs/QA_REPORT.md` for the full QA
results and the manual test checklist.

## Deployment and custom domain

HealthMate is deployed on **Render** as a Python web service. Firestore stays
the only database, so nothing is lost when the server restarts or redeploys.

The full step-by-step guide, including the domain setup, HTTPS checks, post-
deployment tests, checklist and rollback plan, is in
**[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**.

Short version:

1. Push this repository to GitHub.
2. Render → New → Blueprint → choose the repository (uses `render.yaml`).
3. Add the Render address to Firebase's authorised domains.
4. Render → Settings → Custom Domains → add your domain, then create the DNS
   records Render shows at your domain registrar.
5. Add the custom domain to Firebase's authorised domains.

## Limitations

* **The Symptom Guide is a short list of written rules, not a medical tool.**
  It can't examine anyone, doesn't know medical history and can be wrong. It
  is designed to err on the side of caution.
* **Free-text matching can't understand meaning.** "No chest pain" still
  triggers caution. This false alarm is deliberate: the text can only make
  a result more cautious, never less.
* **The Wellness Assistant** only knows its pre-written topics and does not
  understand language like an AI would.
* **Habits**: no history, streaks or reminders (left out on purpose). "Today"
  uses the device's own date and time zone.
* **Firestore rules can't limit how many habits a user creates.** The app limits
  it to 20, but a user who edits the JavaScript could create more (only in
  their own account).
* **Render's free plan sleeps** after 15 minutes without visitors; the next
  visit takes about a minute. Upgrade to a paid plan, or open the site a few
  minutes before a demo.
* **Emergency numbers are for India.**

## Security notes

* **No secrets in the code.** The Firebase web config is public by design. Never
  add a Firebase service-account key or any private credential.
* **Two layers of protection, with different jobs:**
  * *Page protection (browser).* `static/js/auth.js` hides the Dashboard and
    Habit Tracker from signed-out visitors. This improves the experience, but
    is **not** security, because anyone can change JavaScript in their browser.
  * *Data protection (server).* `firestore.rules` is enforced by Google for
    every request: owner-only access, allowed fields only, value checks.
* **XSS:** templates auto-escape, JavaScript only inserts user text with
  `textContent`, and a strict Content-Security-Policy blocks injected scripts.
* **Safe redirects:** the `?next=` address after login must be a page on this site.
* **Headers:** CSP, `X-Frame-Options: DENY`, `nosniff`, a strict referrer policy,
  and HSTS in production.
* **Minimal data:** only a first name; no free-text health descriptions;
  saving symptom results is opt-in, and saved results can be deleted.
