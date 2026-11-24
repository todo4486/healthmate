"""Application settings.

Values come from environment variables so the same code runs locally and in
production. HealthMate stores no user data on the server, so no secret key or
database settings are needed.
"""

import os


class Config:
    # Reject request bodies larger than 16 KB. Our JSON APIs only need a few
    # hundred bytes, so anything bigger is a mistake or misuse.
    MAX_CONTENT_LENGTH = 16 * 1024

    SITE_NAME = "HealthMate"

    # "development" locally, "production" on the live server.
    APP_ENV = os.getenv("APP_ENV", "development")


class TestConfig(Config):
    TESTING = True
    APP_ENV = "testing"
