"""Monta o reel final: vídeo + narração + trilha, tudo local com ffmpeg.

Substitui o `vidiq_compose`. A trilha abaixa sozinha enquanto a voz fala (ducking por
sidechain), os efeitos sonoros do vídeo são mantidos se existirem e o volume final é
nivelado em -14 LUFS, o padrão do Instagram e do TikTok.

Uso:
  python central/mixar.py midia/2026-10-21-teste-ideia.mp4 audio/teste-ideia/narracao.wav midia/final/teste-ideia.mp4
  python central/mixar.py video.mp4 narracao.wav saida.mp4 --trilha midia/trilhas/trilha-01.mp3 --inicio-trilha 18
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

TRILHA_PADRAO = Path(__file__).resolve().parent.parent / "midia" / "trilhas" / "trilha-01.mp3"


def sondar(arquivo: Path) -> tuple[float, bool]:
    """Duração do arquivo e se ele tem trilha de áudio."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(arquivo)],
        capture_output=True, text=True, check=True,
    ).stdout
    info = json.loads(out)
    return float(info["format"]["duration"]), any(s["codec_type"] == "audio" for s in info.get("streams", []))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("narracao", type=Path)
    ap.add_argument("saida", type=Path)
    ap.add_argument("--trilha", type=Path, default=TRILHA_PADRAO)
    ap.add_argument("--inicio-trilha", type=float, default=0.0, help="de onde a trilha começa (varie entre os reels)")
    ap.add_argument("--volume-trilha", type=float, default=0.4)
    ap.add_argument("--atraso-voz", type=float, default=0.1, help="segundos até a voz entrar")
    ap.add_argument("--sem-trilha", action="store_true")
    a = ap.parse_args()

    dur, tem_sfx = sondar(a.video)
    dur_voz, _ = sondar(a.narracao)
    if dur_voz + a.atraso_voz > dur:
        print(f"aviso: a narração ({dur_voz:.1f}s) passa do vídeo ({dur:.1f}s) e vai ser cortada. "
              "Atualize os *_TIMES da composição com o voz.py e renderize de novo.", file=sys.stderr)
    atraso = int(a.atraso_voz * 1000)
    entradas = ["-i", str(a.video), "-i", str(a.narracao)]
    fmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    filtros = [f"[1:a]{fmt},adelay={atraso}|{atraso}[voz]"]
    mix = ["[vozmix]"]

    if a.sem_trilha:
        filtros.append("[voz]anull[vozmix]")
    else:
        entradas += ["-i", str(a.trilha)]
        fade = max(0.0, dur - 1.5)
        filtros += [
            "[voz]asplit=2[vozmix][vozsc]",
            f"[2:a]atrim=start={a.inicio_trilha}:duration={dur},asetpts=PTS-STARTPTS,{fmt},"
            f"volume={a.volume_trilha},afade=t=in:d=0.4,afade=t=out:st={fade:.2f}:d=1.5[tri]",
            # A trilha cai uns 10 dB quando a voz entra e volta devagar nas pausas.
            "[tri][vozsc]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=400:makeup=1[triduck]",
        ]
        mix.append("[triduck]")

    if tem_sfx:
        filtros.append(f"[0:a]{fmt}[sfx]")
        mix.append("[sfx]")

    filtros.append(
        f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=longest,"
        f"apad,atrim=duration={dur},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[audio]"
    )

    a.saida.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", ";".join(filtros),
           "-map", "0:v", "-map", "[audio]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-t", f"{dur}", str(a.saida)]
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit("ffmpeg falhou")
    print("ok", a.saida)


if __name__ == "__main__":
    main()
