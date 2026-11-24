"""gunicorn settings (the production web server).

gunicorn reads this file automatically when started from the project folder:
    gunicorn app:app
"""

import os

# The hosting platform tells us which port to listen on.
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Two worker processes is plenty for a small app on a small server.
workers = int(os.getenv("WEB_CONCURRENCY", "2"))

# Give up on a request that takes longer than 30 seconds.
timeout = 30

# Send request and error logs to the console, where the platform collects them.
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
