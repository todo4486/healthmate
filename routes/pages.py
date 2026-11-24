"""Page routes: every URL that returns an HTML page.

In templates, link to these as url_for("pages.<name>"), e.g. url_for("pages.home").

Which pages need sign-in is decided in each template (page_access) and
enforced in the browser by static/js/auth.js. The real protection for user
data is the Firestore security rules (firestore.rules), not these routes:
Flask never sees or stores user data.
"""

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, url_for

from services import library, symptom_engine

pages = Blueprint("pages", __name__)

# Main navigation, shown in the header and footer (in this order).
NAV_ITEMS = [
    {"endpoint": "pages.symptoms", "label": "Symptoms"},
    {"endpoint": "pages.assistant", "label": "Assistant"},
    {"endpoint": "pages.learn", "label": "Learn"},
    {"endpoint": "pages.habits", "label": "Habits"},
    {"endpoint": "pages.dashboard", "label": "Dashboard"},
]

# Habit categories. The id is also used as a CSS class for the colour dot.
# Must match CATEGORIES in static/js/habits-store.js and the list in firestore.rules.
HABIT_CATEGORIES = [
    {"id": "hydration", "label": "Hydration"},
    {"id": "sleep", "label": "Sleep"},
    {"id": "exercise", "label": "Exercise"},
    {"id": "nutrition", "label": "Nutrition"},
    {"id": "mental", "label": "Mental wellness"},
    {"id": "other", "label": "Other"},
]

# Content is read once when the app starts.
SYMPTOM_GUIDE = symptom_engine.GUIDE


# ---------- Public pages ----------

@pages.get("/")
def home():
    return render_template("index.html")


@pages.get("/symptoms")
def symptoms():
    return render_template("symptoms.html", guide=SYMPTOM_GUIDE)


@pages.get("/assistant")
def assistant():
    return render_template("assistant.html")


@pages.get("/learn")
def learn():
    return render_template(
        "learn.html",
        categories=library.CATEGORIES,
        counts=library.count_by_category(),
        articles=library.ARTICLES,
    )


@pages.get("/learn/topic/<category_id>")
def learn_category(category_id):
    category = library.category(category_id)
    if category is None:
        abort(404)
    return render_template(
        "learn_category.html",
        category=category,
        articles=library.articles_in(category_id),
        categories=library.CATEGORIES,
    )


@pages.get("/learn/<article_id>")
def learn_article(article_id):
    article = library.article(article_id)
    if article is None:
        abort(404)
    related = [item for item in library.articles_in(article["category"]) if item["id"] != article_id]
    return render_template(
        "article.html",
        article=article,
        category=library.category(article["category"]),
        related=related,
    )


@pages.get("/safety")
def safety():
    return render_template("safety.html")


# ---------- Account pages ----------

@pages.get("/login")
def login():
    return render_template("login.html")


@pages.get("/register")
def register():
    return render_template("register.html")


@pages.get("/reset-password")
def reset_password():
    return render_template("reset_password.html")


# ---------- Signed-in pages ----------

@pages.get("/dashboard")
def dashboard():
    return render_template("dashboard.html", symptom_labels=symptom_engine.labels())


@pages.get("/habits")
def habits():
    return render_template("habits.html", habit_categories=HABIT_CATEGORIES)


# ---------- System ----------

@pages.get("/healthz")
def healthz():
    # Used by the hosting platform to check the app is running.
    return jsonify(status="ok", app=current_app.config["SITE_NAME"])


@pages.get("/favicon.ico")
def favicon():
    # Some browsers ask for /favicon.ico even when the page names an SVG icon.
    return redirect(url_for("static", filename="img/logo.svg"), code=301)
