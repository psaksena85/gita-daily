"""One-time helper: turns the public-domain verse dataset (github.com/gita/gita, The Unlicense)
into data/gita.json. Only the Sanskrit text and transliteration are used; all meanings,
stories and quizzes are written fresh by the content generator."""
import json, re, sys, urllib.request

SRC = "https://raw.githubusercontent.com/gita/gita/main/data/verse.json"

def clean(v):
    lines = [l.strip() for l in v["text"].split("\n") if l.strip()]
    speaker = None
    if lines and lines[0].endswith("उवाच"):
        speaker = lines.pop(0)
    out = []
    for i, l in enumerate(lines):
        l = re.sub(r"[।|]+\s*[\d.]+\s*[।|]*\s*$", "", l).strip()   # drop "।।2.47।।"
        l = l.rstrip("।").strip()
        out.append(l + (" ॥" if i == len(lines) - 1 else " ।"))
    tl = [l.strip() for l in v["transliteration"].split("\n") if l.strip()]
    if speaker and tl and tl[0].endswith("uvācha"):
        tl.pop(0)
    return {
        "order": v["verse_order"], "ch": v["chapter_number"], "v": v["verse_number"],
        "speaker": speaker, "sanskrit": out, "translit": tl,
    }

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    raw = json.load(open(path)) if path else json.load(urllib.request.urlopen(SRC))
    verses = sorted((clean(v) for v in raw), key=lambda x: x["order"])
    json.dump(verses, open("data/gita.json", "w"), ensure_ascii=False, indent=1)
    print(f"Wrote {len(verses)} verses to data/gita.json")
