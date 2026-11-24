"""HealthMate Flask application.

Flask's job is small: serve the pages and (from Phase 3) answer two JSON APIs.
All user data lives in Firebase and is accessed from the browser.
"""

from flask import Flask, jsonify, render_template

from config import Config


def create_app(config_class=Config):
    """Build and configure the Flask app (the "application factory" pattern).

    Tests call this with TestConfig; production uses the default Config.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.context_processor
    def inject_site_name():
        # Makes {{ site_name }} available in every template.
        return {"site_name": app.config["SITE_NAME"]}

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/healthz")
    def healthz():
        # Used by the hosting platform to check the app is running.
        return jsonify(status="ok", app=app.config["SITE_NAME"])

    return app


# gunicorn and `flask run` both look for a module-level variable named `app`.
app = create_app()
