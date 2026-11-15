# Evangelho dos Dias

Feed RSS e publicação automatizada do podcast **Evangelho dos Dias** (Família Dias).

- Feed: https://engelmannlabs.github.io/evangelho-dos-dias/feed.xml
- Página: https://engelmannlabs.github.io/evangelho-dos-dias/

## Fluxo

1. O MP3 editado é enviado ao branch `inbox` como `inbox/ep-NNN.mp3` (commit único, force-push).
2. `inbox.yml` cria o release `ep-NNN` em rascunho com o MP3 e grava `transcripts/ep-NNN.txt` em `main`.
3. Título e descrição entram em `episodes/ep-NNN.json` (`{"title", "description"}`) em `main`.
4. `publish.yml` publica o release, atualiza `episodes.json` e regera `docs/feed.xml`.
5. `spotify-link.yml` (a cada 30 min) encontra o episódio no Spotify e grava o link em `episodes.json` e no release.

Secrets: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`. Variável opcional: `SPOTIFY_SHOW_ID`.
