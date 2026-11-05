"""Gita Pathshala daily pipeline.

  python run_daily.py daily            # what GitHub Actions runs every morning
  python run_daily.py generate 94      # write the lesson for verse #94 (2.47) only
  python run_daily.py preview 94       # make the video for verse #94 into out/, no posting
  python run_daily.py site             # rebuild site/verses.js
  python run_daily.py status           # which day it is and what's ready
"""
import sys, datetime
from gita.common import CONFIG, TOTAL, day_number, today, verse_by_order, load_content, load_state, save_state, vid
from gita import generate, render, site

def ensure_ahead(day):
    """Write lessons for today and the next `buffer_days` days."""
    for order in range(max(1, day), min(TOTAL, day + CONFIG["buffer_days"]) + 1):
        v = verse_by_order(order)
        if not load_content(v):
            print(f"Writing lesson for day {order} (Gita {v['ch']}.{v['v']})")
            generate.generate(order)

def publish(day):
    state = load_state()
    rec = state["posted"].get(str(day), {})
    v = verse_by_order(day)
    c = load_content(v)
    if not c:
        raise SystemExit(f"No content for day {day}")
    if CONFIG["require_approval"] and not c.get("approved"):
        print(f"Day {day} ({vid(v)}) is not approved yet — set \"approved\": true in content/{vid(v)}.json. Skipping.")
        return
    video = render.render(c, day)
    errors = []
    if CONFIG["youtube"]["enabled"] and not rec.get("youtube"):
        try:
            from gita import youtube
            rec["youtube"] = youtube.upload(video, c, day)
        except Exception as e:
            errors.append(f"YouTube: {e}")
    if CONFIG["instagram"]["enabled"] and not rec.get("instagram"):
        try:
            from gita import instagram
            rec["instagram"] = instagram.upload(video, c, day)
        except Exception as e:
            errors.append(f"Instagram: {e}")
    rec.update({"id": vid(v), "date": str(today())})
    state["posted"][str(day)] = rec
    save_state(state)
    site.build()
    if errors:
        raise SystemExit("Some uploads failed (the run can be retried safely):\n  " + "\n  ".join(errors))

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    day = day_number()
    if cmd == "daily":
        if day < 1:
            print(f"Series starts on {CONFIG['start_date']}; preparing the first lessons.")
            ensure_ahead(1); site.build(); return
        if day > TOTAL:
            print("All verses are done! 🎉"); return
        ensure_ahead(day)
        publish(day)
    elif cmd == "generate":
        generate.generate(int(sys.argv[2]), force="--force" in sys.argv)
    elif cmd == "preview":
        order = int(sys.argv[2])
        generate.generate(order)
        render.render(load_content(verse_by_order(order)), order)
    elif cmd == "site":
        site.build()
    elif cmd == "status":
        v = verse_by_order(day) if 1 <= day <= TOTAL else None
        print(f"Today is {today()}, day {day} of {TOTAL}" + (f" → Gita {v['ch']}.{v['v']}" if v else ""))
        for o in range(max(1, day), min(TOTAL, day + CONFIG["buffer_days"]) + 1):
            c = load_content(verse_by_order(o))
            print(f"  day {o}: {'ready' if c else 'not written yet'}" + (" (approved)" if c and c.get("approved") else ""))
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
