"""Tests for the Wellness Assistant answers (services/assistant.py)."""

import pytest

from services import assistant

SUGGESTED = {
    "How can I improve my sleep?": "sleep",
    "How can I manage stress?": "stress",
    "How can I stay physically active?": "activity",
    "What are some healthy eating habits?": "nutrition",
    "How can I improve my hydration?": "hydration",
}


@pytest.mark.parametrize("question, topic_id", SUGGESTED.items())
def test_every_suggested_question_gets_its_topic(question, topic_id):
    reply = assistant.answer(question)
    assert reply["kind"] == "topic"
    topic = next(t for t in assistant.DATA["topics"] if t["id"] == topic_id)
    assert reply["title"] == topic["title"]


@pytest.mark.parametrize("question, title", [
    ("i keep waking up at night", "Sleep"),
    ("I feel so ANXIOUS about my exams", "Stress and mental wellness"),
    ("how many glasses of water", "Hydration"),
    ("best breakfast foods?", "Healthy eating"),
])
def test_custom_questions(question, title):
    assert assistant.answer(question)["title"] == title


@pytest.mark.parametrize("message", [
    "I have chest pain right now",
    "my dad collapsed and is unresponsive",
    "I can't breathe",
    "Signs of a STROKE?",
    "she is having a seizure",
])
def test_possible_emergencies_get_safety_guidance_not_wellness_tips(message):
    reply = assistant.answer(message)
    assert reply["kind"] == "urgent"
    assert any("112" in paragraph for paragraph in reply["paragraphs"])
    assert reply["tips"] == []


def test_emergency_beats_a_topic_match():
    # Mentions sleep AND breathing trouble: safety must win.
    assert assistant.answer("I can't sleep because I can't breathe")["kind"] == "urgent"


@pytest.mark.parametrize("message", ["I want to kill myself", "thinking about self-harm"])
def test_crisis_messages_get_helpline(message):
    reply = assistant.answer(message)
    assert reply["kind"] == "crisis"
    assert any("14416" in paragraph for paragraph in reply["paragraphs"])


@pytest.mark.parametrize("message", [
    "what dose of paracetamol should I take",
    "do I have diabetes?",
    "which antibiotic is best",
])
def test_no_medicines_or_diagnosis(message):
    reply = assistant.answer(message)
    assert reply["kind"] == "medical"
    assert "can't suggest medicines" in reply["paragraphs"][0]


def test_unknown_question_says_so_and_lists_topics():
    reply = assistant.answer("what's the capital of France?")
    assert reply["kind"] == "fallback"
    assert "pre-written answers" in reply["paragraphs"][0]


def test_greeting():
    assert assistant.answer("Hello!")["title"] == "Hello"


def test_keep_fit_is_not_mistaken_for_a_seizure():
    assert assistant.answer("How can I keep fit?")["kind"] == "topic"


@pytest.mark.parametrize("message", [None, "", "    ", 42, ["sleep"], "x" * 501])
def test_invalid_messages_are_rejected(message):
    with pytest.raises(assistant.InvalidMessage):
        assistant.answer(message)


def test_500_characters_is_allowed():
    assert assistant.answer("sleep " + "a" * 494)["kind"] == "topic"


def test_every_reply_has_disclaimer_and_only_local_links():
    for message in [*SUGGESTED, "hello", "chest pain", "dose", "kill myself"]:
        reply = assistant.answer(message)
        assert "not medical advice" in reply["disclaimer"]
        if reply["link"]:
            assert reply["link"]["url"].startswith("/")


def test_every_topic_link_points_to_a_real_article(client):
    for topic in assistant.DATA["topics"]:
        assert client.get(topic["link"]["url"]).status_code == 200, topic["link"]["url"]
