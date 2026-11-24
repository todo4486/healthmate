"""HealthMate Flask application.

This file only builds the app: it loads settings, shares a few values with
every template, adds security headers and plugs in the route modules from
the routes/ folder. All user data lives in Firebase and is accessed from the
browser; Flask itself stores nothing.
"""

import logging
from datetime import date

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from content import load_data
from routes.api import api
from routes.errors import errors
from routes.pages import NAV_ITEMS, pages
from security import init_security


def create_app(config_class=Config):
    """Build and configure the Flask app (the "application factory" pattern).

    Tests call this with TestConfig; production uses the default Config.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    if app.config["APP_ENV"] == "production":
        # The hosting platform sits in front of the app and handles HTTPS.
        # This makes Flask trust its "the visitor used HTTPS" header.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Log to the console, where the hosting platform collects it.
    logging.basicConfig(level=app.config["LOG_LEVEL"],
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Content is read once at start-up, not on every request.
    safety_info = load_data("safety.json")

    @app.context_processor
    def inject_globals():
        # These values are available in every template.
        return {
            "site_name": app.config["SITE_NAME"],
            "nav_items": NAV_ITEMS,
            "safety": safety_info,
            "current_year": date.today().year,
        }

    init_security(app)
    app.register_blueprint(pages)
    app.register_blueprint(api)
    app.register_blueprint(errors)

    return app


# gunicorn and `flask run` both look for a module-level variable named `app`.
app = create_app()
