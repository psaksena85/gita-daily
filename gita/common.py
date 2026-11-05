import json, datetime, os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUT = ROOT / "out"

def load_json(p, default=None):
    p = Path(p)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))

def save_json(p, data):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

CONFIG = load_json(ROOT / "config.json")
VERSES = load_json(ROOT / "data" / "gita.json")
CHAPTERS = load_json(ROOT / "data" / "chapters.json")
TOTAL = len(VERSES)
STATE_PATH = ROOT / "data" / "state.json"

def today():
    return datetime.datetime.now(ZoneInfo(CONFIG["timezone"])).date()

def day_number(date=None):
    """Day 1 = start_date. Returns the verse order to post on that date."""
    start = datetime.date.fromisoformat(CONFIG["start_date"])
    return ((date or today()) - start).days + 1

def verse_by_order(order):
    return next((v for v in VERSES if v["order"] == order), None)

def vid(v):
    return f'{v["ch"]}-{v["v"]}'

def content_path(v):
    return CONTENT / f"{vid(v)}.json"

def load_content(v):
    return load_json(content_path(v))

def load_state():
    return load_json(STATE_PATH, {"posted": {}})

def save_state(s):
    save_json(STATE_PATH, s)

def env(name, required=True):
    val = os.environ.get(name, "").strip()
    if required and not val:
        raise SystemExit(f"Missing environment variable / GitHub secret: {name}")
    return val
