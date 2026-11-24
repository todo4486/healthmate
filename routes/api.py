"""JSON API used by the browser: the Symptom Guide and the Wellness Assistant.

Both endpoints are stateless: they look at the request, apply written rules
and return an answer. Nothing is stored on the server.
"""

from flask import Blueprint, jsonify, request

from services import assistant, symptom_engine

api = Blueprint("api", __name__, url_prefix="/api")


def _json_body():
    """The request's JSON object, or None if it isn't valid JSON."""
    if not request.is_json:
        return None
    return request.get_json(silent=True)


@api.post("/symptom-check")
def symptom_check():
    try:
        answers = symptom_engine.validate(_json_body())
    except symptom_engine.InvalidAnswers as error:
        return jsonify(error=str(error)), 400
    return jsonify(symptom_engine.assess(answers))


@api.post("/assistant")
def ask_assistant():
    body = _json_body()
    message = body.get("message") if isinstance(body, dict) else None
    try:
        reply = assistant.answer(message)
    except assistant.InvalidMessage as error:
        return jsonify(error=str(error)), 400
    return jsonify(reply)

# Errors such as 404, 405 and 413 on /api/ addresses get JSON replies:
# see routes/errors.py.
