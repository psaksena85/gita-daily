"""Run this ONCE on your own computer to get a YouTube refresh token.

  pip install google-auth-oauthlib
  python scripts/get_youtube_token.py path/to/client_secret.json

A browser window opens; sign in with the Google account that owns your channel.
Copy the three values it prints into GitHub → Settings → Secrets and variables → Actions."""
import sys, json
from google_auth_oauthlib.flow import InstalledAppFlow

secrets = sys.argv[1] if len(sys.argv) > 1 else "client_secret.json"
flow = InstalledAppFlow.from_client_secrets_file(secrets, scopes=["https://www.googleapis.com/auth/youtube.upload"])
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
info = json.load(open(secrets))
info = info.get("installed") or info.get("web")
print("\nAdd these as GitHub secrets:\n")
print("YT_CLIENT_ID     =", info["client_id"])
print("YT_CLIENT_SECRET =", info["client_secret"])
print("YT_REFRESH_TOKEN =", creds.refresh_token)
