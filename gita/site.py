"""Writes site/verses.js with every verse posted so far. The site itself is site/index.html (GitHub Pages)."""
import json
from .common import ROOT, TOTAL, CONTENT, load_state, load_json

KEYS = ["id","order","ch","v","chName","speaker","sanskrit","translit","theme","icon","storyIcon","hindi","english",
        "deeper","words","background","lessons","examples","story","quiz"]

def build():
    posted = {int(k) for k in load_state()["posted"]}
    items = []
    for f in sorted(CONTENT.glob("*.json")):
        c = load_json(f)
        if posted and c["order"] not in posted:
            continue
        items.append({k: c.get(k) for k in KEYS})
    items.sort(key=lambda x: x["order"])
    (ROOT / "site" / "verses.js").write_text(
        "window.GITA_TOTAL=" + str(TOTAL) + ";\nwindow.GITA_VERSES=" + json.dumps(items, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"  site: {len(items)} verses in site/verses.js")
