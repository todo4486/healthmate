"""Security and quality checks across the whole site."""

import re
from pathlib import Path
from urllib.parse import urlparse

import pytest

from app import create_app
from config import Config, TestConfig

ROOT = Path(__file__).resolve().parent.parent


# ---------- Security headers ----------

def test_security_headers_on_pages_and_api(client):
    for response in [client.get("/"), client.post("/api/assistant", json={"message": "hi"})]:
        headers = response.headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
        assert "object-src 'none'" in headers["Content-Security-Policy"]


def test_csp_blocks_inline_scripts_except_our_own(client):
    response = client.get("/")
    policy = response.headers["Content-Security-Policy"]
    script_src = next(part for part in policy.split("; ") if part.startswith("script-src"))
    assert "'unsafe-inline'" not in script_src
    assert "'unsafe-eval'" not in script_src

    nonce = re.search(r"'nonce-([^']+)'", script_src).group(1)
    html = response.get_data(as_text=True)
    inline_scripts = re.findall(r"<script(?![^>]*\bsrc=)([^>]*)>", html)
    for attributes in inline_scripts:
        if "application/json" in attributes:
            continue  # data, never executed
        assert f'nonce="{nonce}"' in attributes


def test_nonce_changes_every_request(client):
    first = client.get("/").headers["Content-Security-Policy"]
    second = client.get("/").headers["Content-Security-Policy"]
    assert first != second


def test_hsts_only_in_production():
    assert "Strict-Transport-Security" not in create_app(TestConfig).test_client().get("/").headers

    class Production(Config):
        APP_ENV = "production"
    headers = create_app(Production).test_client().get("/").headers
    assert headers["Strict-Transport-Security"].startswith("max-age=")


def test_production_trusts_proxy_https_header():
    class Production(Config):
        APP_ENV = "production"
    app = create_app(Production)

    @app.get("/scheme-check")
    def scheme_check():
        from flask import request
        return request.scheme

    response = app.test_client().get("/scheme-check", headers={"X-Forwarded-Proto": "https"})
    assert response.get_data(as_text=True) == "https"


def test_debug_is_off_by_default():
    assert create_app(Config).debug is False


# ---------- Secrets and configuration ----------

def test_no_private_credentials_anywhere_in_the_project():
    patterns = ["BEGIN PRIVATE KEY", '"private_key"', "service_account", "client_secret"]
    for path in ROOT.rglob("*"):
        if path.is_dir() or any(part in {"venv", ".git", "__pycache__", ".pytest_cache", "tests"} for part in path.parts):
            continue
        if path.suffix not in {".py", ".js", ".json", ".html", ".css", ".md", ".txt", ".yaml", ".yml", ".rules"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            assert pattern not in text, f"{pattern!r} found in {path.relative_to(ROOT)}"


def test_gitignore_excludes_secrets_and_local_files():
    ignored = (ROOT / ".gitignore").read_text()
    for entry in ["venv/", ".env", "__pycache__/", "*serviceAccount*.json"]:
        assert entry in ignored


# ---------- Links ----------

def test_every_internal_link_on_every_page_works(client):
    """Visit every page, follow every internal link found, check nothing is broken."""
    to_visit, seen = ["/"], set()
    while to_visit:
        url = to_visit.pop()
        if url in seen:
            continue
        seen.add(url)
        response = client.get(url)
        assert response.status_code in (200, 301), f"{url} -> {response.status_code}"
        if "text/html" not in response.content_type:
            continue
        for href in re.findall(r'(?:href|src)="([^"#]+)', response.get_data(as_text=True)):
            parsed = urlparse(href)
            if parsed.scheme or parsed.netloc or href.startswith(("tel:", "mailto:")):
                continue
            to_visit.append(parsed.path + (f"?{parsed.query}" if parsed.query else ""))
    assert len(seen) > 25  # pages, articles, topics, static files


def test_favicon_redirects_to_logo(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 301
    assert response.headers["Location"].endswith("/static/img/logo.svg")


# ---------- XSS: user text is only ever inserted as text ----------

JS_FILES = sorted((ROOT / "static" / "js").glob("*.js"))


@pytest.mark.parametrize("path", JS_FILES, ids=lambda p: p.name)
def test_javascript_never_inserts_html_strings(path):
    code = path.read_text(encoding="utf-8")
    # innerHTML is only allowed to restore our own server-rendered markup.
    assert "innerHTML =" not in code and "insertAdjacentHTML" not in code, path.name
    assert "eval(" not in code and "document.write" not in code, path.name


def test_templates_never_disable_autoescaping():
    for template in (ROOT / "templates").rglob("*.html"):
        text = template.read_text(encoding="utf-8")
        assert "|safe" not in text.replace(" ", "") and "autoescape false" not in text, template.name
