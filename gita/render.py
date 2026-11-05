"""Turns one verse's content into a vertical 1080x1920 video (YouTube Short + Instagram Reel)."""
import asyncio, json, random, shutil, subprocess, re
from pathlib import Path
from .common import CONFIG, ROOT, OUT, TOTAL, verse_by_order

PALETTES = [("#FF7A00","#E8457E","#A8320B"),("#2F6FE4","#0B8A92","#1A3F8F"),("#2E9E55","#0B8A92","#1B6034"),
            ("#7A3DC0","#E8457E","#4A2180"),("#E0503F","#FF7A00","#8E2219"),("#0B8A92","#2F6FE4","#08555B")]

def palette(order):
    return PALETTES[order % len(PALETTES)]

def short_url():
    return re.sub(r"^https?://|/$", "", CONFIG["site_url"])

def scenes(c, day):
    ex = c["examples"][c["reel"]["example_index"]]
    q = c["quiz"][c["reel"]["quiz_index"]]
    letters = "ABCD"
    nxt = verse_by_order(c["order"] + 1)
    return [
        ("hook", {"text": c["reel"]["hook"], "icon": c["icon"]},
         ("en", f'{c["reel"]["hook"]} Today’s verse: Bhagavad Gita, chapter {c["ch"]}, verse {c["v"]}.')),
        ("shloka", {"sanskrit": c["sanskrit"], "translit": c["translit"], "speaker": c.get("speaker")},
         ("sa", " ".join(l.replace("॥", "").replace("।", ",") for l in c["sanskrit"]))),
        ("meaning", {"text": c["english"]}, ("en", c["english"])),
        ("example", {"emoji": ex[0], "title": ex[1], "text": ex[2]}, ("en", f"For example. {ex[2]}")),
        ("lesson", {"text": c["reel"]["lesson"]}, ("en", c["reel"]["lesson"])),
        ("quiz", {"q": q["q"], "o": q["o"], "a": q["a"]},
         ("en", q["q"] + " " + " ".join(f"{letters[i]}: {o}." for i, o in enumerate(q["o"])) + " Comment your answer!")),
        ("answer", {"q": q["q"], "o": q["o"], "a": q["a"]}, ("en", f"The answer is {letters[q['a']]}. {q['x']}")),
        ("outro", {"next": f'{nxt["ch"]}.{nxt["v"]}' if nxt else "1.1", "url": short_url()},
         ("en", "Come back tomorrow for the next verse. Find the full lesson, story and quiz on our website.")),
    ]

async def _tts(text, voice, path, rate):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate).save(str(path))

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out)

def make_audio(kind, lang, text, path, vid):
    """Your own recording wins: put assets/voice/<verse-id>/<scene>.mp3 to use it instead of the robot voice."""
    own = ROOT / "assets" / "voice" / vid / f"{kind}.mp3"
    if own.exists():
        shutil.copy(own, path); return
    voice = CONFIG["voice_sanskrit"] if lang == "sa" else CONFIG["voice_english"]
    rate = "-25%" if lang == "sa" else "-5%"
    try:
        asyncio.run(_tts(text, voice, path, rate))
    except Exception as e:  # no network / TTS down: keep the video, make it silent but long enough to read
        secs = max(8 if kind == "shloka" else 3.5, len(text.split()) / 2.3)
        print(f"  TTS failed for {kind} ({e.__class__.__name__}); using {secs:.1f}s of silence")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{secs}", str(path)], check=True)

def render(c, day):
    from playwright.sync_api import sync_playwright
    work = OUT / c["id"]; work.mkdir(parents=True, exist_ok=True)
    c1, c2, c3 = palette(c["order"])
    base = {"brand": CONFIG["channel_name"], "day": day, "ch": c["ch"], "v": c["v"], "chName": c["chName"], "c1": c1, "c2": c2, "c3": c3}
    sc = scenes(c, day)
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1080, "height": 1920})
        page.goto((ROOT / "templates" / "reel.html").as_uri())
        for i, (kind, data, _) in enumerate(sc):
            page.evaluate("d => render(d)", {**base, **data, "kind": kind})
            page.wait_for_timeout(150)
            page.screenshot(path=str(work / f"{i:02d}.png"))
        b.close()
    clips = []
    for i, (kind, _, (lang, text)) in enumerate(sc):
        a = work / f"{i:02d}.mp3"
        make_audio(kind, lang, text, a, c["id"])
        d = duration(a) + (1.2 if kind in ("quiz", "shloka") else 0.6)
        clip = work / f"{i:02d}.mp4"
        frames = int(d * 30)
        vf = (f"scale=1188:-2,zoompan=z='min(zoom+0.0004,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30,"
              f"fade=t=in:st=0:d=0.25,fade=t=out:st={d-0.25:.2f}:d=0.25,format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(work / f"{i:02d}.png"), "-i", str(a),
                        "-filter_complex", f"[0:v]{vf}[v];[1:a]apad,atrim=0:{d:.2f},aresample=44100[a]",
                        "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                        "-c:a", "aac", "-b:a", "160k", str(clip)], check=True)
        clips.append(clip)
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{c_.name}'\n" for c_ in clips))
    joined = work / "joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)], check=True)
    final = OUT / f"day-{day:03d}-gita-{c['id']}.mp4"
    music = sorted((ROOT / "assets" / "music").glob("*.mp3"))
    if music:
        track = random.Random(c["order"]).choice(music)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), "-stream_loop", "-1", "-i", str(track),
                        "-filter_complex", f"[1:a]volume={CONFIG['music_volume']}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", str(final)], check=True)
    else:
        shutil.copy(joined, final)
    print(f"  video: {final.name} ({duration(final):.0f}s)")
    return final
