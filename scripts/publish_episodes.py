"""Para cada episodes/<tag>.json: publica o release (se rascunho), aplica título/descrição
e registra/atualiza o episódio em episodes.json. Requer gh autenticado e GH_REPO."""
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from mutagen.mp3 import MP3

ROOT = Path(__file__).resolve().parent.parent
REPO = os.environ["GH_REPO"]
show = json.loads((ROOT / "podcast.json").read_text(encoding="utf-8"))
registry = json.loads((ROOT / "episodes.json").read_text(encoding="utf-8"))
by_tag = {e["tag"]: e for e in registry}


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


for meta_file in sorted((ROOT / "episodes").glob("ep-*.json")):
    tag = meta_file.stem
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    title, description = meta["title"].strip(), meta["description"].strip()
    rel = json.loads(gh("release", "view", tag, "--json", "isDraft,assets,publishedAt,url,name,body"))
    asset = next(a for a in rel["assets"] if a["name"].endswith(".mp3"))
    current = by_tag.get(tag, {})

    notes = description
    if current.get("spotify_url"):
        notes += f"\n\n🎧 Spotify: {current['spotify_url']}"
    if rel["isDraft"] or rel["name"] != title or rel["body"].strip() != notes.strip():
        gh("release", "edit", tag, "--title", title, "--notes", notes, "--draft=false")
        rel = json.loads(gh("release", "view", tag, "--json", "isDraft,assets,publishedAt,url,name,body"))

    if current and current["length"] == asset["size"]:
        duration = current["duration"]
    else:
        with tempfile.TemporaryDirectory() as d:
            gh("release", "download", tag, "--pattern", asset["name"], "--dir", d)
            duration = MP3(str(Path(d) / asset["name"])).info.length

    by_tag[tag] = {
        "number": int(tag.split("-")[-1]),
        "tag": tag,
        "guid": f"{show['repo']}/{tag}",
        "title": title,
        "description": description,
        "audio_url": f"https://github.com/{REPO}/releases/download/{tag}/{asset['name']}",
        "length": asset["size"],
        "duration": duration,
        "published_at": current.get("published_at") or rel["publishedAt"] or datetime.now(timezone.utc).isoformat(),
        "release_url": rel["url"],
        "spotify_url": current.get("spotify_url"),
    }
    print(f"{tag}: {title}")

episodes = sorted(by_tag.values(), key=lambda e: e["number"])
(ROOT / "episodes.json").write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
