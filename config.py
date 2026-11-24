"""Application settings.

Values come from environment variables so the same code runs locally and in
production. HealthMate stores no user data on the server and uses no Flask
sessions, so no secret key or database settings are needed.

Environment variables
---------------------
APP_ENV    "development" (default) or "production". Production turns on
           HTTPS-only headers and trusts the hosting platform's proxy.
LOG_LEVEL  "INFO" (default), or "DEBUG" / "WARNING".
"""

import os


class Config:
    SITE_NAME = "HealthMate"

    APP_ENV = os.getenv("APP_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # Reject request bodies larger than 16 KB. Our JSON APIs only need a few
    # hundred bytes, so anything bigger is a mistake or misuse.
    MAX_CONTENT_LENGTH = 16 * 1024

    # Browsers must check with the server before reusing a cached CSS or JS
    # file. Unchanged files get a quick "304 Not Modified" reply, and changed
    # files are downloaded straight away, so visitors never see old code.
    SEND_FILE_MAX_AGE_DEFAULT = 0

    # Smaller JSON replies.
    JSON_SORT_KEYS = False


class TestConfig(Config):
    TESTING = True
    APP_ENV = "testing"
