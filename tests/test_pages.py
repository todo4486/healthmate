"""Checks that pages, shared layout, static files and error pages work."""

import re
from pathlib import Path

import pytest
from flask import url_for

from content import load_data
from routes.pages import NAV_ITEMS

ROOT = Path(__file__).resolve().parent.parent

# Every page, and who it is meant for (see page_access in the templates).
PAGES = {
    "/": "public",
    "/symptoms": "public",
    "/assistant": "public",
    "/learn": "public",
    "/safety": "public",
    "/login": "guest-only",
    "/register": "guest-only",
    "/reset-password": "public",
    "/dashboard": "private",
    "/habits": "private",
}


@pytest.mark.parametrize("url", PAGES)
def test_every_page_loads_with_shared_layout(client, url):
    response = client.get(url)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'class="site-header"' in html
    assert 'class="nav__emergency" href="/safety"' in html
    assert "Not a substitute for professional medical advice." in html
    assert "/static/js/auth.js" in html


@pytest.mark.parametrize("url, access", PAGES.items())
def test_page_access_is_marked(client, url, access):
    html = client.get(url).get_data(as_text=True)
    assert f'<body data-access="{access}">' in html


def test_private_pages_start_hidden_behind_a_loading_message(client):
    for url in ["/dashboard", "/habits"]:
        html = client.get(url).get_data(as_text=True)
        assert "data-auth-loading" in html
        assert "<div data-private-content hidden>" in html


def test_public_pages_are_not_hidden(client):
    html = client.get("/symptoms").get_data(as_text=True)
    assert "data-private-content" not in html


def test_landing_page_has_brief_wording_and_sections(client):
    html = client.get("/").get_data(as_text=True)
    text = " ".join(html.split())  # ignore line breaks in the template
    assert "Take care of your health, one day at a time." in text
    assert ("HealthMate helps you build healthier habits, explore general symptom guidance "
            "and access helpful wellness information in one simple place.") in text
    for section_id in ["features-title", "how-title", "benefits-title"]:
        assert f'id="{section_id}"' in html


def test_safety_page_lists_every_number_and_warning_sign(client):
    html = client.get("/safety").get_data(as_text=True)
    safety = load_data("safety.json")
    for item in safety["numbers"]:
        assert f'href="tel:{item["number"]}"' in html
    for sign in safety["warning_signs"]:
        assert sign["title"] in html


def test_symptom_form_lists_every_option_from_data(client):
    html = client.get("/symptoms").get_data(as_text=True)
    guide = load_data("symptom_guide.json")
    for group in ["symptoms", "durations", "severities", "age_groups"]:
        for item in guide[group]:
            assert f'value="{item["id"]}"' in html


def test_auth_pages_have_forms_and_password_toggles(client):
    login = client.get("/login").get_data(as_text=True)
    assert 'id="login-form"' in login and "data-password-toggle" in login
    assert "data-google-signin" in login

    register = client.get("/register").get_data(as_text=True)
    assert 'id="register-form"' in register
    assert register.count("data-password-toggle") == 2
    assert 'name="acknowledge"' in register


def test_current_page_is_marked_in_navigation(client):
    html = client.get("/learn").get_data(as_text=True)
    assert 'href="/learn" aria-current="page"' in html
    assert html.count('aria-current="page"') == 1


def test_every_navigation_link_opens_a_page(app, client):
    """Follow every link on the home page and check each page loads."""
    html = client.get("/").get_data(as_text=True)
    links = set(re.findall(r'href="(/[^"]*)"', html)) - {"/"}
    links = {link for link in links if not link.startswith("/static/")}

    with app.test_request_context():
        expected = {url_for(item["endpoint"]) for item in NAV_ITEMS}
    assert expected <= links, "every nav item should appear as a link"

    for link in sorted(links):
        assert client.get(link).status_code == 200, link


def test_health_check_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "app": "HealthMate"}


def test_every_script_and_stylesheet_used_by_pages_exists(client):
    for url in PAGES:
        html = client.get(url).get_data(as_text=True)
        for path in re.findall(r'(?:src|href)="(/static/[^"?]+)', html):
            assert client.get(path).status_code == 200, f"{url} uses missing {path}"


def test_unknown_page_shows_friendly_404(client):
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404
    assert b"Page not found" in response.data


def test_server_error_shows_friendly_500(app):
    # Make Flask show the 500 page instead of raising the error in tests.
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/boom")
    def boom():
        raise RuntimeError("test error")

    response = app.test_client().get("/boom")
    assert response.status_code == 500
    assert b"Something went wrong" in response.data


def test_safety_data_has_required_fields():
    safety = load_data("safety.json")
    assert any(item["urgent"] for item in safety["numbers"])
    assert all({"number", "label", "urgent"} <= item.keys() for item in safety["numbers"])
    assert all({"title", "detail"} <= sign.keys() for sign in safety["warning_signs"])
    assert safety["while_waiting"]


def test_templates_have_no_inline_styles():
    for template in (ROOT / "templates").rglob("*.html"):
        assert 'style="' not in template.read_text(encoding="utf-8"), template.name


def test_no_server_credentials_in_static_files():
    """Only the public web config may be in static/; never a private key."""
    for file in (ROOT / "static").rglob("*.js"):
        text = file.read_text(encoding="utf-8")
        assert "private_key" not in text, file.name
        assert "BEGIN PRIVATE KEY" not in text, file.name


def test_firestore_rules_limit_profiles_to_their_owner():
    rules = (ROOT / "firestore.rules").read_text(encoding="utf-8")
    assert "request.auth.uid == uid" in rules
    assert "match /users/{uid}" in rules
    assert "hasOnly(['displayName', 'createdAt'])" in rules
    assert "allow read, write: if true" not in rules


def test_test_config_is_used(app):
    assert app.config["TESTING"] is True
    assert app.config["APP_ENV"] == "testing"


def test_static_files_are_revalidated_not_cached_blindly(client):
    response = client.get("/static/js/auth.js")
    assert "no-cache" in response.headers.get("Cache-Control", "")


def test_each_script_is_loaded_from_one_url_only(client):
    """A module loaded from two different URLs would run twice (two copies)."""
    html = client.get("/login").get_data(as_text=True)
    assert "?v=" not in html


@pytest.mark.parametrize("url", ["/login", "/register", "/reset-password", "/symptoms", "/habits"])
def test_every_field_error_matches_a_field_name(client, url):
    """forms.js finds a field's error by the id "<field name>-error"."""
    html = client.get(url).get_data(as_text=True)
    names = set(re.findall(r'name="([^"]+)"', html))
    error_ids = re.findall(r'class="field-error" id="([^"]+)-error"', html)
    assert error_ids, "page should have field errors"
    for field in error_ids:
        assert field in names, f"{url}: #{field}-error has no field named {field!r}"
