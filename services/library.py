"""Health Library content, read from data/library.json.

The library is a plain JSON file, not a database or CMS: to add an article,
add an entry to the file with an existing category id.
"""

from content import load_data

_DATA = load_data("library.json")

CATEGORIES = _DATA["categories"]
ARTICLES = _DATA["articles"]

_CATEGORY_BY_ID = {category["id"]: category for category in CATEGORIES}
_ARTICLE_BY_ID = {article["id"]: article for article in ARTICLES}

# Catch mistakes in the JSON file when the app starts, not when a visitor clicks.
for _article in ARTICLES:
    if _article["category"] not in _CATEGORY_BY_ID:
        raise ValueError(f"Article {_article['id']!r} has unknown category {_article['category']!r}")
if len(_ARTICLE_BY_ID) != len(ARTICLES):
    raise ValueError("Two library articles share the same id")


def category(category_id):
    """The category with this id, or None."""
    return _CATEGORY_BY_ID.get(category_id)


def article(article_id):
    """The article with this id, or None."""
    return _ARTICLE_BY_ID.get(article_id)


def articles_in(category_id):
    return [item for item in ARTICLES if item["category"] == category_id]


def count_by_category():
    return {item["id"]: len(articles_in(item["id"])) for item in CATEGORIES}
