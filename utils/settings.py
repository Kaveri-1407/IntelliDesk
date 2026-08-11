import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parents[1] / 'settings.json'

DEFAULTS = {
    'model': 'gpt-3.5-turbo',
    'automation_delay': 0.5,
    'screenshot_dir': str(Path(__file__).resolve().parents[1] / 'screenshots'),
    'safety_mode': 'strict',
    'theme': 'dark',
    'version': '0.1'
}


def load_settings():
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULTS)
        return DEFAULTS.copy()
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            s = json.load(f)
            merged = DEFAULTS.copy()
            merged.update(s)
            return merged
    except Exception:
        return DEFAULTS.copy()


def save_settings(s: dict):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(s, f, indent=2)
        return True
    except Exception:
        return False
