"""Security headers added to every response.

Content-Security-Policy (CSP) tells the browser which sources it may load
scripts, styles and connections from. If someone managed to inject a
<script> into a page, the browser would refuse to run it.

Allowed outside our own site, and why:
  www.gstatic.com          Firebase JavaScript SDK files
  apis.google.com          Google sign-in helper script (used by Firebase)
  *.googleapis.com         Firebase Authentication and Firestore servers
  *.firebaseapp.com        Firebase sign-in pages and helper frame
  accounts.google.com      Google sign-in
"""

import secrets

from flask import g

FIREBASE_SCRIPTS = "https://www.gstatic.com https://apis.google.com"
FIREBASE_CONNECT = ("https://*.googleapis.com https://*.firebaseio.com "
                    "https://*.firebaseapp.com https://www.gstatic.com")
FIREBASE_FRAMES = "https://*.firebaseapp.com https://accounts.google.com https://apis.google.com"


def csp_nonce():
    """A random value, new for every page, that marks our own inline script as allowed."""
    if "csp_nonce" not in g:
        g.csp_nonce = secrets.token_urlsafe(16)
    return g.csp_nonce


def init_security(app):
    @app.context_processor
    def inject_nonce():
        return {"csp_nonce": csp_nonce}

    @app.after_request
    def add_security_headers(response):
        policy = "; ".join([
            "default-src 'self'",
            f"script-src 'self' 'nonce-{csp_nonce()}' {FIREBASE_SCRIPTS}",
            "style-src 'self'",
            "img-src 'self' data: https://*.googleusercontent.com",
            f"connect-src 'self' {FIREBASE_CONNECT}",
            f"frame-src {FIREBASE_FRAMES}",
            "font-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ])
        headers = response.headers
        headers["Content-Security-Policy"] = policy
        headers["X-Content-Type-Options"] = "nosniff"       # don't guess file types
        headers["X-Frame-Options"] = "DENY"                  # no embedding in other sites
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Lets the Google sign-in popup talk back to this page.
        headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
        if app.config.get("APP_ENV") == "production":
            # Browsers must use HTTPS for this site for the next year.
            headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
