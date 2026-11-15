"""Adiciona (ou atualiza) um episódio em episodes.json a partir de um release publicado.

Uso: python scripts/add_episode.py <tag> <arquivo_mp3_local>
Variáveis: RELEASE_JSON (payload do release, vindo do evento do GitHub).
"""
import json
import os
import sys
from pathlib import Path

from mutagen.mp3 import MP3

ROOT = Path(__file__).resolve().parent.parent
tag, mp3_path = sys.argv[1], sys.argv[2]
release = json.loads(os.environ["RELEASE_JSON"])
show = json.loads((ROOT / "podcast.json").read_text(encoding="utf-8"))

asset = next(a for a in release["assets"] if a["name"].endswith(".mp3"))
number = int(tag.split("-")[-1])
title = release["name"] or f"Episódio {number}"
description = (release.get("body") or "").strip() or title

guid = f"{show['repo']}/{tag}"
all_eps = json.loads((ROOT / "episodes.json").read_text(encoding="utf-8"))
previous = next((e for e in all_eps if e["guid"] == guid), {})
episodes = [e for e in all_eps if e["guid"] != guid]

episodes.append({
    "number": number,
    "tag": tag,
    "guid": guid,
    "title": title,
    "description": description,
    "audio_url": asset["browser_download_url"],
    "length": asset["size"],
    "duration": MP3(mp3_path).info.length,
    "published_at": previous.get("published_at") or release["published_at"],
    "release_url": release["html_url"],
    "spotify_url": previous.get("spotify_url"),
})
episodes.sort(key=lambda e: e["number"])
(ROOT / "episodes.json").write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"episódio {number} registrado: {title}")
