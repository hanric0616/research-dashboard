import json
import os
from config import BRIEFINGS_FILE


def load_briefings() -> dict:
    if os.path.exists(BRIEFINGS_FILE):
        with open(BRIEFINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_briefing(date_str: str, key: str, content):
    data = load_briefings()
    if date_str not in data:
        data[date_str] = {}
    data[date_str][key] = content
    with open(BRIEFINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
