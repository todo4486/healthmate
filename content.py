"""Loads the app's content files from the data/ folder.

Text such as emergency numbers lives in JSON files instead of Python code,
so it is easy to read, review and change without touching the logic.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def load_data(filename):
    """Read one JSON file from the data/ folder."""
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        return json.load(file)
