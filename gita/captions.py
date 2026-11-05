from .common import CONFIG, TOTAL

def title(c, day):
    t = f'{c["theme"]} | Bhagavad Gita {c["ch"]}.{c["v"]} for Kids | Day {day} #Shorts'
    return t[:100]

def description(c, day):
    tags = " ".join("#" + h for h in CONFIG["hashtags"])
    return (f'{c["reel"]["caption"]}\n\n'
            f'📜 {" ".join(c["sanskrit"])}\n\n'
            f'🇬🇧 {c["english"]}\n'
            f'🇮🇳 {c["hindi"]}\n\n'
            f'Day {day} of {TOTAL} · Chapter {c["ch"]}, {c["chName"]}, Verse {c["v"]}\n'
            f'Full lesson, story and quiz: {CONFIG["site_url"]}#verse-{c["id"]}\n\n{tags}')
