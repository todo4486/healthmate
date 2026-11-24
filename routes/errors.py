"""Friendly error pages for the whole app.

Pages get a helpful HTML page; /api/ addresses get a short JSON message,
because they are called by JavaScript, not read by people.
"""

from flask import Blueprint, current_app, jsonify, render_template, request

errors = Blueprint("errors", __name__)

MESSAGES = {
    404: ("Page not found",
          "We couldn't find the page you were looking for. It may have moved, or the link may be wrong."),
    405: ("Not allowed", "That action isn't allowed on this page."),
    413: ("Too much data", "That request was too large. Please shorten it and try again."),
    500: ("Something went wrong",
          "Sorry, an unexpected error happened on our side. Please try again in a moment."),
}


def _respond(code):
    heading, text = MESSAGES[code]
    if request.path.startswith("/api/"):
        return jsonify(error=text), code
    return render_template("message.html", code=code, heading=heading, text=text), code


@errors.app_errorhandler(404)
def not_found(error):
    return _respond(404)


@errors.app_errorhandler(405)
def method_not_allowed(error):
    return _respond(405)


@errors.app_errorhandler(413)
def too_large(error):
    return _respond(413)


@errors.app_errorhandler(500)
def server_error(error):
    # Record the real problem for the developer; the visitor sees a calm message.
    current_app.logger.error("Server error on %s", request.path, exc_info=error)
    return _respond(500)
