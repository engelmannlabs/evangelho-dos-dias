"""Busca no Spotify os episódios ainda sem link e grava spotify_url em episodes.json.

Precisa dos secrets SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET.
Opcional: variável SPOTIFY_SHOW_ID (senão procura o show pelo nome e autor).
"""
import base64
import json
import os
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
show = json.loads((ROOT / "podcast.json").read_text(encoding="utf-8"))
episodes = json.loads((ROOT / "episodes.json").read_text(encoding="utf-8"))
pending = [e for e in episodes if not e.get("spotify_url")]
if not pending:
    print("nada pendente")
    sys.exit(0)

cid, secret = os.environ.get("SPOTIFY_CLIENT_ID"), os.environ.get("SPOTIFY_CLIENT_SECRET")
if not cid or not secret:
    print("secrets do Spotify ausentes; pulando")
    sys.exit(0)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def call(url, token=None, data=None):
    req = urllib.request.Request(url, data=data)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    else:
        req.add_header("Authorization", "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode())
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


token = call("https://accounts.spotify.com/api/token", data=b"grant_type=client_credentials")["access_token"]

show_id = os.environ.get("SPOTIFY_SHOW_ID") or show.get("spotify_show_id")
if not show_id:
    q = urllib.parse.quote(show["title"])
    found = call(f"https://api.spotify.com/v1/search?q={q}&type=show&market=BR&limit=20", token)
    for s in found["shows"]["items"]:
        if s and norm(s["name"]) == norm(show["title"]) and norm(show["author"]) in norm(s["publisher"]):
            show_id = s["id"]
            break
if not show_id:
    print("show ainda não encontrado no Spotify")
    sys.exit(0)

if show.get("spotify_show_id") != show_id:
    show["spotify_show_id"] = show_id
    show["spotify_show_url"] = f"https://open.spotify.com/show/{show_id}"
    (ROOT / "podcast.json").write_text(json.dumps(show, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

remote = []
url = f"https://api.spotify.com/v1/shows/{show_id}/episodes?market=BR&limit=50"
while url:
    page = call(url, token)
    remote += [e for e in page["items"] if e]
    url = page.get("next")

by_title = {norm(e["name"]): e for e in remote}
for ep in pending:
    hit = by_title.get(norm(ep["title"]))
    if hit:
        ep["spotify_url"] = hit["external_urls"]["spotify"]
        print(f"#{ep['number']} -> {ep['spotify_url']}")

(ROOT / "episodes.json").write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
