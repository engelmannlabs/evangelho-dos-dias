"""Gera docs/feed.xml e docs/index.html a partir de podcast.json e episodes.json."""
import json
import html
from email.utils import format_datetime
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
show = json.loads((ROOT / "podcast.json").read_text(encoding="utf-8"))
episodes = json.loads((ROOT / "episodes.json").read_text(encoding="utf-8"))
episodes = sorted(episodes, key=lambda e: e["number"], reverse=True)


def rfc2822(iso):
    return format_datetime(datetime.fromisoformat(iso.replace("Z", "+00:00")))


def hms(seconds):
    s = int(round(seconds))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


items = []
for ep in episodes:
    items.append(f"""    <item>
      <title>{escape(ep['title'])}</title>
      <description><![CDATA[{ep['description']}]]></description>
      <itunes:summary><![CDATA[{ep['description']}]]></itunes:summary>
      <enclosure url="{escape(ep['audio_url'])}" length="{ep['length']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{escape(ep['guid'])}</guid>
      <pubDate>{rfc2822(ep['published_at'])}</pubDate>
      <itunes:duration>{hms(ep['duration'])}</itunes:duration>
      <itunes:episode>{ep['number']}</itunes:episode>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
      <itunes:image href="{escape(show['image'])}"/>
    </item>""")

last_build = rfc2822(episodes[0]["published_at"]) if episodes else format_datetime(datetime.now(timezone.utc))
explicit = "true" if show["explicit"] else "false"

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{escape(show['title'])}</title>
    <link>{escape(show['site'])}</link>
    <atom:link href="{escape(show['feed_url'])}" rel="self" type="application/rss+xml"/>
    <language>{show['language']}</language>
    <description><![CDATA[{show['description']}]]></description>
    <itunes:summary><![CDATA[{show['description']}]]></itunes:summary>
    <itunes:author>{escape(show['author'])}</itunes:author>
    <itunes:owner>
      <itunes:name>{escape(show['owner_name'])}</itunes:name>
      <itunes:email>{escape(show['owner_email'])}</itunes:email>
    </itunes:owner>
    <itunes:image href="{escape(show['image'])}"/>
    <image><url>{escape(show['image'])}</url><title>{escape(show['title'])}</title><link>{escape(show['site'])}</link></image>
    <itunes:category text="{escape(show['category'])}">
      <itunes:category text="{escape(show['subcategory'])}"/>
    </itunes:category>
    <itunes:explicit>{explicit}</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <lastBuildDate>{last_build}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""
(ROOT / "docs" / "feed.xml").write_text(feed, encoding="utf-8")

rows = "".join(
    f"<li><strong>#{e['number']} — {html.escape(e['title'])}</strong>"
    + (f" · <a href=\"{html.escape(e['spotify_url'])}\">Ouvir no Spotify</a>" if e.get("spotify_url") else "")
    + f"<br><audio controls preload=\"none\" src=\"{html.escape(e['audio_url'])}\"></audio></li>"
    for e in episodes
)
page = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(show['title'])}</title>
<link rel="alternate" type="application/rss+xml" href="{html.escape(show['feed_url'])}">
<style>body{{font-family:system-ui,sans-serif;max-width:680px;margin:2rem auto;padding:0 1rem;color:#222}}img{{width:200px;border-radius:12px}}li{{margin:1rem 0}}audio{{width:100%}}</style></head>
<body><img src="capa.jpg" alt="Capa"><h1>{html.escape(show['title'])}</h1><p>{html.escape(show['description'])}</p>
<p><a href="feed.xml">Feed RSS</a></p><ul>{rows}</ul></body></html>
"""
(ROOT / "docs" / "index.html").write_text(page, encoding="utf-8")
print(f"feed gerado com {len(episodes)} episódio(s)")
