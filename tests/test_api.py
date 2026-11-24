"""Tests for the JSON API (routes/api.py)."""

import pytest

VALID = {
    "warning_signs": [],
    "no_warning_signs": True,
    "symptoms": ["cough"],
    "details": "",
    "duration": "1_3_days",
    "severity": "mild",
    "age_group": "18_64",
}


def test_symptom_check_returns_structured_result(client):
    response = client.post("/api/symptom-check", json=VALID)
    assert response.status_code == 200
    data = response.get_json()
    for key in ["level", "heading", "summary", "reasons", "next_steps", "watch_for",
                "submitted", "disclaimer", "saveable"]:
        assert key in data
    assert data["submitted"]["symptoms"] == ["Cough"]


def test_symptom_check_chest_discomfort_is_urgent(client):
    data = client.post("/api/symptom-check", json=dict(VALID, symptoms=["chest_discomfort"])).get_json()
    assert data["level"] == "urgent"


@pytest.mark.parametrize("body", [
    {},
    {"symptoms": ["cough"]},
    dict(VALID, severity="extreme"),
])
def test_symptom_check_rejects_bad_answers_with_400(client, body):
    response = client.post("/api/symptom-check", json=body)
    assert response.status_code == 400
    assert response.get_json()["error"]


def test_symptom_check_rejects_non_json(client):
    response = client.post("/api/symptom-check", data="symptoms=cough",
                           content_type="application/x-www-form-urlencoded")
    assert response.status_code == 400


def test_symptom_check_rejects_broken_json(client):
    response = client.post("/api/symptom-check", data="{not json", content_type="application/json")
    assert response.status_code == 400


def test_symptom_check_echoes_text_as_data_not_html(client):
    data = client.post("/api/symptom-check",
                       json=dict(VALID, details="<script>alert(1)</script>")).get_json()
    # Returned as plain JSON text; the page inserts it with textContent.
    assert data["submitted"]["details"] == "<script>alert(1)</script>"
    assert client.post("/api/symptom-check", json=VALID).content_type == "application/json"


def test_assistant_answers(client):
    response = client.post("/api/assistant", json={"message": "How can I improve my sleep?"})
    assert response.status_code == 200
    assert response.get_json()["kind"] == "topic"


@pytest.mark.parametrize("body", [{}, {"message": ""}, {"message": "x" * 501}, {"message": 5}, ["hi"]])
def test_assistant_rejects_bad_messages(client, body):
    response = client.post("/api/assistant", json=body)
    assert response.status_code == 400
    assert response.get_json()["error"]


def test_api_get_is_not_allowed_and_answers_in_json(client):
    response = client.get("/api/assistant")
    assert response.status_code == 405
    assert response.is_json


def test_unknown_api_address_answers_in_json(client):
    response = client.post("/api/nothing-here", json={})
    assert response.status_code == 404
    assert response.is_json


def test_oversized_request_is_rejected(client):
    response = client.post("/api/assistant", json={"message": "a" * 20000})
    assert response.status_code == 413
    assert response.is_json
