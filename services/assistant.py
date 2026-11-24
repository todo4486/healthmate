"""Wellness Assistant: pre-written answers, chosen by simple rules. NOT AI.

How a question is answered, in order:
1. Safety first: if the message mentions a possible emergency or crisis
   (see text_safety.py), reply with safety guidance instead of a normal answer.
2. If it asks about medicines, diagnosis or treatment, explain that the
   assistant can't help with that and suggest a doctor or pharmacist.
3. Otherwise pick the topic in data/assistant_topics.json whose keywords
   appear most often in the question.
4. If nothing matches, say so and list the topics it can help with.

Nothing is stored: each question is answered and then forgotten.
"""

import re

from content import load_data
from services.text_safety import find_urgent_phrases, normalise

DATA = load_data("assistant_topics.json")
MAX_MESSAGE_LENGTH = 500

DISCLAIMER = ("This is general wellness information from HealthMate's pre-written guide, "
              "not medical advice.")


class InvalidMessage(ValueError):
    """The message is missing, empty or too long."""


def _words(text):
    return re.findall(r"[a-z0-9']+", text)


def _mentions(text, phrase):
    return re.search(rf"(?<![a-z]){re.escape(phrase)}(?![a-z])", text) is not None


def _reply(kind, title, paragraphs, tips=None, link=None):
    return {
        "kind": kind,
        "title": title,
        "paragraphs": paragraphs,
        "tips": tips or [],
        "link": link,
        "disclaimer": DISCLAIMER,
    }


def _emergency_reply():
    return _reply(
        "urgent",
        "This could need urgent help",
        [
            "Your message mentions something that could be a medical emergency. I can't assess it, "
            "and you shouldn't wait for a chat answer.",
            "If this is happening now, call 112, or 108 for an ambulance, or go to the nearest "
            "emergency department.",
        ],
        link={"url": "/safety", "label": "Open the Safety Center"},
    )


def _crisis_reply():
    return _reply(
        "crisis",
        "You don't have to face this alone",
        [
            "It sounds like you might be going through something really difficult. Please reach out to "
            "someone now.",
            "Call Tele-MANAS on 14416 (free, confidential, 24/7) to talk to a trained counsellor. If you "
            "are in immediate danger, call 112.",
            "If you can, tell someone you trust how you are feeling.",
        ],
        link={"url": "/safety", "label": "Open the Safety Center"},
    )


def _medical_reply():
    return _reply(
        "medical",
        "I can't help with medicines or diagnosis",
        [
            "I can only share general wellness information, so I can't suggest medicines, doses or "
            "treatments, or tell you what condition you might have.",
            "A doctor or pharmacist can give you advice that is right for you. If you have symptoms, "
            "the Symptom Guide can help you decide where to get help.",
        ],
        link={"url": "/symptoms", "label": "Open the Symptom Guide"},
    )


def _topic_reply(topic):
    paragraphs = list(topic["answer"]) + [topic["see_doctor"]]
    return _reply("topic", topic["title"], paragraphs, topic["tips"], topic["link"])


def _fallback_reply(greeting=False):
    titles = ", ".join(topic["title"].lower() for topic in DATA["topics"])
    opening = ("Hello! " if greeting else "Sorry, I don't have an answer for that. ")
    return _reply(
        "fallback",
        "Hello" if greeting else "I'm not sure about that one",
        [
            f"{opening}I use a small set of pre-written answers, so I can only help with: {titles}.",
            "Try asking something like “How can I sleep better?” or “How much water should I drink?”",
        ],
        link={"url": "/learn", "label": "Browse the Health Library"},
    )


def best_topic(text):
    """The topic with the most matching keywords, or None if nothing matches."""
    words = _words(text)
    best, best_score = None, 0
    for topic in DATA["topics"]:
        score = sum(1 for word in words if word in topic["keywords"])
        if score > best_score:
            best, best_score = topic, score
    return best


def answer(message):
    """Answer one message. Raises InvalidMessage for empty or overly long input."""
    if not isinstance(message, str) or not message.strip():
        raise InvalidMessage("Please type a question.")
    if len(message) > MAX_MESSAGE_LENGTH:
        raise InvalidMessage(f"Please keep your question under {MAX_MESSAGE_LENGTH} characters.")

    text = normalise(message)

    alerts = find_urgent_phrases(text)
    if alerts["crisis"]:
        return _crisis_reply()
    if alerts["emergency"]:
        return _emergency_reply()

    if any(_mentions(text, phrase) for phrase in DATA["medical_words"]):
        return _medical_reply()

    topic = best_topic(text)
    if topic:
        return _topic_reply(topic)

    greeting = any(_mentions(text, phrase) for phrase in DATA["greetings"])
    return _fallback_reply(greeting=greeting)
