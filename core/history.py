import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

HISTORY_FILE = Path(__file__).resolve().parents[1] / 'history.json'


def load_history() -> List[Dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_history(entry: Dict):
    hs = load_history()
    hs.insert(0, entry)
    # truncate to latest 500 entries
    hs = hs[:500]
    # sanitize entries before saving
    for e in hs:
        if 'actions' in e:
            for a in e['actions']:
                # remove sensitive keys
                for k in list(a.keys()):
                    if any(s in k.lower() for s in ('password', 'pwd', 'otp', 'token', 'secret', 'key')):
                        a[k] = '<redacted>'
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(hs, f, indent=2)


def add_entry(command: str, actions: List[Dict], result: str, status: str, input_type: str = 'Text', intent: str = None, confidence: float = None, task_plan: List[Dict] = None):
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'input_type': input_type,
        'command': command,
        'intent': intent,
        'confidence': confidence,
        'task_plan': task_plan or actions,
        'actions': actions,
        'result': result,
        'status': status
    }
    save_history(entry)


def clear_history():
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
