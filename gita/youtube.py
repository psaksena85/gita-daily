"""Uploads the video to YouTube with the YouTube Data API v3.
Note: videos uploaded from an API project that has not passed Google's API audit are locked to private.
See README → YouTube setup."""
from .common import CONFIG, env
from .captions import title, description

def upload(path, c, day):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    creds = Credentials(None, refresh_token=env("YT_REFRESH_TOKEN"), token_uri="https://oauth2.googleapis.com/token",
                        client_id=env("YT_CLIENT_ID"), client_secret=env("YT_CLIENT_SECRET"),
                        scopes=["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    cfg = CONFIG["youtube"]
    body = {
        "snippet": {"title": title(c, day), "description": description(c, day)[:4900],
                    "tags": CONFIG["hashtags"] + ["Bhagavad Gita", f"Gita {c['ch']}.{c['v']}", c["chName"]],
                    "categoryId": cfg["category_id"], "defaultLanguage": "en"},
        "status": {"privacyStatus": cfg["privacy"], "selfDeclaredMadeForKids": cfg["made_for_kids"]},
    }
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(path), mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    print(f"  YouTube: https://youtube.com/shorts/{resp['id']}")
    return resp["id"]
