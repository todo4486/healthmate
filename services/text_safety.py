"""Spot words in free text that MIGHT describe an emergency.

This is deliberately one-directional: it can only ADD caution, never remove it.
It matches whole words and phrases and does not understand meaning, so
"I don't have chest pain" still matches "chest pain". For a health app a
false alarm is the safe kind of mistake; missing an emergency is not.
"""

import re
import unicodedata

from content import load_data

_PHRASES = load_data("urgent_phrases.json")


def normalise(text):
    """Lower-case, straighten quotes, drop control characters, squash spaces."""
    text = unicodedata.normalize("NFKC", str(text))
    text = text.replace("’", "'").replace("‘", "'")
    text = "".join(ch if ch.isprintable() else " " for ch in text)
    return " ".join(text.lower().split())


def _find(text, phrases):
    found = []
    for phrase in phrases:
        # (?<![a-z]) and (?![a-z]) = whole words only ("fit" won't match "benefit").
        if re.search(rf"(?<![a-z]){re.escape(phrase)}(?![a-z])", text):
            found.append(phrase)
    return found


def find_urgent_phrases(text):
    """Return {"emergency": [...], "crisis": [...]} phrases found in the text."""
    clean = normalise(text)
    return {
        "emergency": _find(clean, _PHRASES["emergency"]),
        "crisis": _find(clean, _PHRASES["crisis"]),
    }
