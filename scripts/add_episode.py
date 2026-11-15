"""Registra (ou atualiza) um episódio e regera feed.xml e index.html.

Uso:
  python3 scripts/add_episode.py --number 2 --title "..." --description "..." [--mp3 audio/ep-002.mp3]
  python3 scripts/add_episode.py --number 2 --spotify-url https://open.spotify.com/episode/...

O MP3 precisa estar em audio/ep-NNN.mp3 (servido pelo GitHub Pages).
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from mutagen.mp3 import MP3

ROOT = Path(__file__).resolve().parent.parent
p = argparse.ArgumentParser()
p.add_argument("--number", type=int, required=True)
p.add_argument("--title")
p.add_argument("--description")
p.add_argument("--spotify-url")
p.add_argument("--published-at", help="ISO 8601; padrão: agora")
a = p.parse_args()

show = json.loads((ROOT / "podcast.json").read_text(encoding="utf-8"))
tag = f"ep-{a.number:03d}"
mp3 = ROOT / "audio" / f"{tag}.mp3"
eps = json.loads((ROOT / "episodes.json").read_text(encoding="utf-8"))
cur = next((e for e in eps if e["tag"] == tag), None)

if cur is None:
    if not (a.title and a.description and mp3.exists()):
        sys.exit(f"episódio novo exige --title, --description e o arquivo {mp3}")
    cur = {"number": a.number, "tag": tag, "guid": f"{show['repo']}/{tag}"}
    eps.append(cur)

if mp3.exists():
    cur["audio_url"] = f"{show['site']}audio/{tag}.mp3"
    cur["length"] = mp3.stat().st_size
    cur["duration"] = MP3(str(mp3)).info.length
if a.title:
    cur["title"] = a.title.strip()
if a.description:
    cur["description"] = a.description.strip()
if a.spotify_url:
    cur["spotify_url"] = a.spotify_url
cur["published_at"] = a.published_at or cur.get("published_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
cur.setdefault("spotify_url", None)

eps.sort(key=lambda e: e["number"])
(ROOT / "episodes.json").write_text(json.dumps(eps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
subprocess.run([sys.executable, str(ROOT / "scripts" / "build_feed.py")], check=True)
print(json.dumps(cur, ensure_ascii=False, indent=2))
