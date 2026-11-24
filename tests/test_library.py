"""Tests for the Health Library pages and content (services/library.py)."""

import pytest
from markupsafe import escape

from services import library

REQUIRED_CATEGORIES = {"Sleep", "Nutrition", "Physical activity", "Hydration",
                       "Mental wellness", "Preventive health"}


def test_all_six_required_categories_exist_and_have_articles():
    assert {category["title"] for category in library.CATEGORIES} == REQUIRED_CATEGORIES
    for category in library.CATEGORIES:
        assert library.articles_in(category["id"]), category["title"]


def test_library_home_lists_every_category_and_article(client):
    html = client.get("/learn").get_data(as_text=True)
    for category in library.CATEGORIES:
        assert f'href="/learn/topic/{category["id"]}"' in html
    for article in library.ARTICLES:
        assert f'href="/learn/{article["id"]}"' in html
        assert str(escape(article["title"])) in html


@pytest.mark.parametrize("category", library.CATEGORIES, ids=lambda c: c["id"])
def test_category_page_shows_only_its_articles(client, category):
    html = client.get(f"/learn/topic/{category['id']}").get_data(as_text=True)
    assert f"<h1>{category['title']}</h1>" in html
    for article in library.ARTICLES:
        link = f'href="/learn/{article["id"]}"'
        if article["category"] == category["id"]:
            assert link in html
        else:
            assert link not in html


@pytest.mark.parametrize("article", library.ARTICLES, ids=lambda a: a["id"])
def test_article_page_shows_all_sections_and_disclaimer(client, article):
    response = client.get(f"/learn/{article['id']}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert str(escape(article["title"])) in html
    for section in article["sections"]:
        assert str(escape(section["heading"])) in html
    assert "Educational information only." in html
    assert 'href="/learn/topic/' in html  # breadcrumb back to its category


def test_category_with_no_articles_shows_empty_state(client, monkeypatch):
    monkeypatch.setattr(library, "articles_in", lambda category_id: [])
    html = client.get("/learn/topic/sleep").get_data(as_text=True)
    assert "No articles here yet" in html


@pytest.mark.parametrize("url", ["/learn/not-an-article", "/learn/topic/not-a-topic", "/learn/topic/"])
def test_unknown_library_pages_are_404(client, url):
    assert client.get(url).status_code == 404


def test_content_avoids_diagnosis_and_medicine_advice():
    banned = ["diagnos", "paracetamol", "dose", " mg", "cure", "guarantee"]
    for article in library.ARTICLES:
        text = " ".join([article["summary"]] + [
            section.get("text", "") + " " + " ".join(section.get("tips", []))
            for section in article["sections"]
        ]).lower()
        for word in banned:
            assert word not in text, f"{article['id']}: {word!r}"
