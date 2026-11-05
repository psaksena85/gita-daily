"""Publishes the video as an Instagram Reel (Instagram API with Instagram Login).
Uses resumable upload, so the video does not need to be hosted anywhere public."""
import os, time, subprocess, requests
from .common import CONFIG, env
from .captions import description

def _base():
    return f'https://graph.instagram.com/{CONFIG["instagram"]["api_version"]}'

def refresh_token():
    """Long-lived tokens last 60 days; refreshing daily keeps them alive.
    If GH_PAT is set, the new token is written back to the IG_ACCESS_TOKEN GitHub secret."""
    tok = env("IG_ACCESS_TOKEN")
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": tok}, timeout=60)
    if r.ok and r.json().get("access_token"):
        new = r.json()["access_token"]
        days = r.json().get("expires_in", 0) // 86400
        print(f"  Instagram token refreshed (valid ~{days} days)")
        if os.environ.get("GH_PAT") and new != tok:
            subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "--body", new],
                           env={**os.environ, "GH_TOKEN": os.environ["GH_PAT"]}, check=False)
        return new
    print(f"  Instagram token refresh skipped: {r.text[:200]}")
    return tok

def upload(path, c, day):
    tok = refresh_token()
    ig = env("IG_USER_ID")
    caption = description(c, day).replace(" #Shorts", "")[:2150]
    r = requests.post(f"{_base()}/{ig}/media", data={"media_type": "REELS", "upload_type": "resumable",
                      "caption": caption, "share_to_feed": str(CONFIG["instagram"]["share_to_feed"]).lower(),
                      "access_token": tok}, timeout=60)
    r.raise_for_status()
    cid = r.json()["id"]
    data = open(path, "rb").read()
    r = requests.post(f'https://rupload.facebook.com/ig-api-upload/{CONFIG["instagram"]["api_version"]}/{cid}',
                      headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(len(data))},
                      data=data, timeout=600)
    r.raise_for_status()
    for _ in range(60):  # wait up to ~10 minutes for Instagram to process the video
        s = requests.get(f"{_base()}/{cid}", params={"fields": "status_code,status", "access_token": tok}, timeout=60).json()
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram could not process the video: {s}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram processing timed out")
    r = requests.post(f"{_base()}/{ig}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60)
    r.raise_for_status()
    mid = r.json()["id"]
    print(f"  Instagram: published media {mid}")
    return mid
