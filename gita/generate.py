"""Writes the full lesson for one verse (all 10 website sections + the reel script) using the Claude API."""
import json, re, time
from .common import CONFIG, CHAPTERS, VERSES, verse_by_order, vid, content_path, load_json, save_json, env

SYSTEM = """You are a warm, careful teacher who explains the Bhagavad Gita to children (age 7-14) and ordinary families.
You write in simple, vivid English, faithful to the traditional meaning of the verse. You never invent
events that are not in the Mahabharata or the Gita. When a verse is a list of names or a battlefield
description (common in Chapter 1), you still find an honest, gentle lesson in it (for example: preparation,
teamwork, the cost of anger, how fear feels) without stretching the meaning.
Stories must be either well-known traditional stories (Mahabharata, Ramayana, Puranas, Panchatantra,
Jataka, true stories of well-known Indian figures) told in your own words, or original stories about ordinary children.
Use Indian children's names and everyday Indian settings in the examples.
Use typographic apostrophes (’) and quotes (“ ”) in English text.
Return ONLY valid JSON, no markdown fences, no comments."""

SCHEMA = """{
 "theme": "short catchy title of the lesson, max 8 words",
 "icon": "one emoji that fits the verse",
 "storyIcon": "one emoji that fits the story",
 "hindi": "simple Hindi meaning in Devanagari, 1-3 sentences",
 "english": "clear English meaning, 1-3 sentences",
 "deeper": ["3 short paragraphs explaining the deeper meaning; may use <b> and <i>"],
 "words": [["Sanskrit word in Devanagari", "IAST transliteration", "English meaning"]],
 "background": ["2 short paragraphs: what happened just before this verse, with verse references like (2.11)"],
 "lessons": [["5 items: short bold lesson title", "one-sentence explanation"]],
 "examples": [["emoji", "short title", "8 items: 1-3 sentence example from a child's life today"]],
 "story": {"title": "...", "paras": ["4 short paragraphs"], "moral": "Lesson: ..."},
 "quiz": [{"q": "question", "o": ["4 options"], "a": 0, "x": "one-line explanation"}],
 "reel": {
   "hook": "a 1-sentence question or surprising line for the first 3 seconds of a reel, max 14 words",
   "example_index": 0,
   "lesson": "the single takeaway in one short sentence, max 16 words",
   "quiz_index": 0,
   "caption": "Instagram/YouTube caption, 2-4 short lines, friendly, with 1-2 emojis, no hashtags"
 }
}"""

def _context(order):
    """Meanings of the previous 3 verses, so the background section stays continuous."""
    prev = []
    for o in range(max(1, order - 3), order):
        v = verse_by_order(o)
        c = load_json(content_path(v)) if v else None
        if c:
            prev.append(f'{v["ch"]}.{v["v"]}: {c["english"]}')
    return "\n".join(prev) or "(none yet)"

def _validate(d):
    need = {"theme": str, "icon": str, "storyIcon": str, "hindi": str, "english": str, "deeper": list,
            "words": list, "background": list, "lessons": list, "examples": list, "story": dict, "quiz": list, "reel": dict}
    for k, t in need.items():
        assert isinstance(d.get(k), t), f"field {k} missing or wrong type"
    assert len(d["examples"]) == 8, "need exactly 8 examples"
    assert len(d["quiz"]) == 4, "need exactly 4 quiz questions"
    for q in d["quiz"]:
        assert len(q["o"]) == 4 and 0 <= q["a"] < 4, "bad quiz question"
    assert all(len(e) == 3 for e in d["examples"])
    assert all(len(w) == 3 for w in d["words"])
    assert len(d["story"]["paras"]) >= 3
    for k in ("hook", "lesson", "caption"):
        assert d["reel"].get(k), f"reel.{k} missing"
    d["reel"]["example_index"] = int(d["reel"].get("example_index", 0)) % 8
    d["reel"]["quiz_index"] = int(d["reel"].get("quiz_index", 0)) % 4

def generate(order, force=False):
    v = verse_by_order(order)
    path = content_path(v)
    if path.exists() and not force:
        return load_json(path)
    import anthropic
    client = anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY"))
    prompt = f"""Write the lesson for Bhagavad Gita chapter {v["ch"]} ({CHAPTERS[str(v["ch"])]}), verse {v["v"]}.
This is verse {order} of {len(VERSES)} in a daily series for kids and families.

Speaker line (if any): {v["speaker"] or "none"}
Sanskrit:
{chr(10).join(v["sanskrit"])}
Transliteration:
{chr(10).join(v["translit"])}

Meanings of the verses just before this one (for continuity):
{_context(order)}

Return JSON exactly in this shape (8 examples, 4 quiz questions, 5 lessons, every word of the verse in "words"):
{SCHEMA}"""
    last_err = None
    for attempt in range(3):
        msg = client.messages.create(model=CONFIG["claude_model"], max_tokens=8000, system=SYSTEM,
                                     messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in msg.content if b.type == "text")
        text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
        try:
            d = json.loads(text)
            _validate(d)
            break
        except Exception as e:
            last_err = e
            print(f"  attempt {attempt+1} failed: {e}")
            time.sleep(3)
    else:
        raise RuntimeError(f"Could not generate verse {vid(v)}: {last_err}")
    d = {"id": vid(v), "order": order, "ch": v["ch"], "v": v["v"], "chName": CHAPTERS[str(v["ch"])],
         "speaker": v["speaker"], "sanskrit": v["sanskrit"], "translit": v["translit"], **d,
         "approved": not CONFIG["require_approval"], "source": f"generated with {CONFIG['claude_model']}"}
    save_json(path, d)
    print(f"  wrote {path.name}")
    return d
