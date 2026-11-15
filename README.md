# Evangelho dos Dias

Feed RSS do podcast **Evangelho dos Dias** (Família Dias), servido pelo GitHub Pages.

- Feed: https://engelmannlabs.github.io/evangelho-dos-dias/feed.xml
- Página: https://engelmannlabs.github.io/evangelho-dos-dias/

## Fluxo (operado pelo Claude)

1. `python3 scripts/editar_audio.py <original> audio/ep-NNN.mp3` corta silêncios, acelera 1,2x e adiciona a trilha de fundo em 432 Hz (5 s na abertura, baixa sob a voz, 5 s no encerramento); o MP3 (64 kbps mono) é enviado em `audio/ep-NNN.mp3`.
2. `transcribe.yml` grava `transcripts/ep-NNN.txt` (único passo no GitHub Actions).
3. O Claude escreve título e descrição e roda `python3 scripts/add_episode.py --number N --title ... --description ...`, que atualiza `episodes.json`, `feed.xml` e `index.html`.
4. O link do Spotify é gravado com `--spotify-url` quando o episódio aparece lá.
