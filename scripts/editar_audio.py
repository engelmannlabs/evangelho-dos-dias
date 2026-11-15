"""Edição padrão de um episódio do Evangelho dos Dias.

1. Corta silêncios (pausas > 0,6 s viram 0,3 s) e acelera 1,2x.
2. Gera a trilha de fundo em 432 Hz (versão aprovada em 15/11/2026: acordes maiores
   Lá–Ré–Mi–Lá, notas longas e suaves, registro grave, bem baixa sob a voz).
3. Mixa: 5 s de trilha na abertura, trilha baixa durante a fala, 5 s de trilha no encerramento.
4. Exporta MP3 mono 64 kbps.

Uso: python3 scripts/editar_audio.py <audio_original> <saida.mp3> [--sem-trilha] [--limiar -35]
"""
import argparse
import json
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 44100
INTRO = 5.0
OUTRO = 5.0


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def duracao(path):
    return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)))


def gerar_trilha(fala_s, destino):
    """Trilha original afinada em A=432 Hz."""
    total = INTRO + fala_s + OUTRO
    n_total = int(total * SR)
    hz = lambda m: 432 * 2 ** ((m - 69) / 12)
    acordes = {"A": [57, 61, 64], "D": [50, 54, 57], "E": [52, 56, 59]}
    prog = ["A", "D", "E", "A"]
    compasso = 4.0
    tt = np.arange(n_total) / SR

    pad = np.zeros(n_total)
    for k in range(int(total / compasso) + 2):
        c = acordes[prog[k % 4]]
        s = k * compasso
        n0, n1 = int(max(0, s - 1.0) * SR), min(n_total, int((s + compasso + 1.0) * SR))
        if n0 >= n_total:
            break
        seg = tt[n0:n1] - s
        env = np.clip((seg + 1.0) / 2.0, 0, 1) * np.clip((compasso + 1.0 - seg) / 2.0, 0, 1)
        env = np.sin(env * np.pi / 2) ** 2
        for m, a in ((c[0], 0.45), (c[1], 0.4), (c[2], 0.35), (c[0] + 12, 0.25)):
            pad[n0:n1] += a * env * np.sin(2 * np.pi * hz(m) * tt[n0:n1])

    sinos = np.zeros(n_total)
    t0, i = 0.3, 0
    while t0 < total:
        c = acordes[prog[int(t0 / compasso) % 4]]
        m = [c[0] + 12, c[1] + 12, c[2] + 12, c[0] + 24][i % 4]
        n = int(3.0 * SR)
        x = np.arange(n) / SR
        env = (1 - np.exp(-x / 0.15)) * np.exp(-x / 1.2)
        tom = np.sin(2 * np.pi * hz(m) * x) + 0.15 * np.sin(2 * np.pi * 2 * hz(m) * x) * np.exp(-x / 0.6)
        s = int(t0 * SR)
        e = min(n_total, s + n)
        sinos[s:e] += 0.3 * env[: e - s] * tom[: e - s]
        t0 += 1.0
        i += 1

    mix = pad / np.max(np.abs(pad)) + 0.5 * sinos / np.max(np.abs(sinos))
    mix /= np.max(np.abs(mix))

    alto, baixo = 0.17, 0.037
    vol = np.full(n_total, baixo)
    a = int(INTRO * SR)
    vol[:a] = alto
    f = int(1.2 * SR)
    vol[:f] *= np.linspace(0, 1, f)
    d = int(2.0 * SR)
    vol[a : a + d] = np.linspace(alto, baixo, d)
    b = int((INTRO + fala_s) * SR)
    r = int(1.5 * SR)
    vol[b : b + r] = np.linspace(baixo, alto, r)
    vol[b + r :] = alto * np.linspace(1, 0, n_total - (b + r)) ** 1.5

    y = (mix * vol * 32767).astype(np.int16)
    bruto = Path(destino).with_suffix(".bruto.wav")
    with wave.open(str(bruto), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.tobytes())
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(bruto),
        "-af", "lowpass=f=1800,highpass=f=80,aecho=0.8:0.55:110|220:0.22|0.12", str(destino))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("entrada")
    p.add_argument("saida")
    p.add_argument("--sem-trilha", action="store_true")
    p.add_argument("--limiar", type=float, default=-35.0, help="limiar de silêncio em dB")
    a = p.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        fala = Path(tmp) / "fala.wav"
        lim = f"{a.limiar}dB"
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.entrada, "-af",
            f"silenceremove=start_periods=1:start_threshold={lim}:start_duration=0:stop_periods=-1:"
            f"stop_duration=0.6:stop_threshold={lim}:stop_silence=0.3:detection=rms,atempo=1.2",
            "-ac", "1", "-ar", str(SR), str(fala))
        fala_s = duracao(fala)
        enc = ["-ac", "1", "-c:a", "libmp3lame", "-b:a", "64k", "-id3v2_version", "3", a.saida]
        if a.sem_trilha:
            run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(fala), *enc)
        else:
            trilha = Path(tmp) / "trilha.wav"
            gerar_trilha(fala_s, trilha)
            ms = int(INTRO * 1000)
            run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(fala), "-i", str(trilha),
                "-filter_complex",
                f"[0:a]adelay={ms},apad=pad_dur={OUTRO}[v];[v][1:a]amix=inputs=2:duration=longest:normalize=0,"
                "alimiter=limit=0.95[m]", "-map", "[m]", *enc)

    print(json.dumps({
        "original_s": round(duracao(a.entrada), 1),
        "fala_editada_s": round(fala_s, 1),
        "final_s": round(duracao(a.saida), 1),
        "trilha": not a.sem_trilha,
    }))


if __name__ == "__main__":
    main()
