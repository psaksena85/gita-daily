# Gita Pathshala — one Bhagavad Gita verse every day, fully automatic

Every morning this project:

1. **Writes the lesson** for the next verse with Claude (Hindi + English meaning, deeper meaning, word-by-word,
   background, life lessons, 8 kids’ examples, a story and a 4-question quiz). It writes a few days ahead so you can check it first.
2. **Makes a 60–80 second vertical video** (hook → Sanskrit chant → meaning → example → lesson → quiz → answer → follow).
3. **Posts it** as a YouTube Short and an Instagram Reel, with title, caption and hashtags.
4. **Adds the verse to your website** (GitHub Pages), which grows by one verse a day.

It goes in order: day 1 = verse 1.1, day 2 = 1.2 … day 701 = 18.78
(701 because the dataset includes the extra opening verse of Chapter 13 found in some editions).

Everything runs free on GitHub Actions. The only running cost is the Claude API for writing each lesson.

---

## Setup (about 1 hour, once)

### 1. Put the project on GitHub
1. Create a free account at github.com, then a **new public repository** called `gita-daily`.
2. Upload all the files from this folder (drag and drop works on the repo page).
3. Edit `config.json`: set `start_date` (day 1) and replace `YOUR-GITHUB-USERNAME` in `site_url`.
4. Repo → **Settings → Pages** → Source: **GitHub Actions**.

### 2. Claude API key (writes the lessons)
Get a key at console.anthropic.com → API Keys. Add it in your repo:
**Settings → Secrets and variables → Actions → New repository secret** → name `ANTHROPIC_API_KEY`.

### 3. YouTube
1. Go to console.cloud.google.com → create a project → **APIs & Services → Library** → enable **YouTube Data API v3**.
2. **OAuth consent screen**: External, add yourself as a test user.
3. **Credentials → Create credentials → OAuth client ID → Desktop app** → download the JSON.
4. On your computer: `pip install google-auth-oauthlib` then `python scripts/get_youtube_token.py client_secret.json`.
5. Add the three printed values as secrets: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.

> ⚠️ **Important:** Google locks videos uploaded through a new, unverified API project as **private**.
> To post publicly you must request an audit (search “YouTube API Services audit and quota extension form”).
> Until it’s approved, the videos still upload (privately) — you can make them public by hand in YouTube Studio,
> or set `"youtube": {"enabled": false}` and download the daily video from the Actions tab instead.
> Also set your OAuth consent screen to **In production**, or the refresh token expires after 7 days.

### 4. Instagram
1. Your Instagram account must be a **Professional** account (Creator or Business).
2. At developers.facebook.com create an app → add the **Instagram** product → **API setup with Instagram login**.
3. Add your Instagram account, generate an access token with `instagram_business_basic` and
   `instagram_business_content_publish`, and copy your Instagram user ID.
4. Add secrets `IG_ACCESS_TOKEN` and `IG_USER_ID`.
5. Tokens last 60 days. The bot refreshes it every day; to save the refreshed token automatically, also add a
   GitHub personal access token (fine-grained, this repo, “Secrets: read and write”) as `GH_PAT`.
   Without it, generate a fresh token roughly every 50 days.

### 5. Start it
Repo → **Actions** → enable workflows → **Daily Gita verse → Run workflow**.
After that it runs by itself every day at 6:00 AM India time (change the `cron` line in `.github/workflows/daily.yml`).

---

## Checking content before it goes live
Lessons are written `buffer_days` (default 3) days early into `content/<chapter>-<verse>.json`.
Open the file on GitHub, click ✏️, fix anything, commit. For full control set `"require_approval": true` —
then a verse only posts after you change `"approved": false` to `true`.
AI can make mistakes with scripture, so please do read them, or have someone you trust read them.

## Making it sound like you
- **Your own voice:** record mp3s into `assets/voice/<verse-id>/` (see the README there). A real chant sounds far better.
- **Background music:** add mp3s to `assets/music/` (only music you’re allowed to use).
- The default computer voices use the free `edge-tts` package (Microsoft’s neural voices, unofficial). Change
  `voice_english` / `voice_sanskrit` in `config.json`.

## Try it on your computer
```
pip install -r requirements.txt && python -m playwright install chromium
python run_daily.py preview 94     # makes out/day-094-gita-2-47.mp4 (needs ffmpeg)
python run_daily.py status
```

## What’s inside
| Path | What it does |
|---|---|
| `run_daily.py` | the daily routine |
| `gita/generate.py` | writes lessons with Claude |
| `gita/render.py`, `templates/reel.html` | makes the video |
| `gita/youtube.py`, `gita/instagram.py` | posting |
| `site/index.html` | the website; `site/verses.js` is rebuilt daily |
| `data/gita.json` | Sanskrit text + transliteration of all verses (from github.com/gita/gita, public domain) |
| `content/` | one lesson per verse (5 are already written: 2.14, 2.47, 3.21, 4.7, 6.5) |
| `data/state.json` | what has been posted |

Fonts: Baloo 2 and Tiro Devanagari Sanskrit, SIL Open Font License (see `assets/fonts`).
