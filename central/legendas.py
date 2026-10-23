"""Tempo real de cada palavra da narração, para a legenda karaokê.

Usa o faster-whisper na CPU (int8). Hoje o `Karaoke` estima o tempo de cada palavra pelo
tamanho dela; com este arquivo dá para cravar a legenda na fala.

Uso:
  python central/legendas.py audio/teste-ideia/narracao.wav
  -> grava audio/teste-ideia/palavras.json  [{"p": "Antes", "ini": 0.08, "fim": 0.31}, ...]
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", type=Path)
    ap.add_argument("--modelo", default="small", help="tiny, base, small, medium (maior = mais preciso e mais lento)")
    ap.add_argument("--texto", type=Path, help="tempos.json do voz.py, para o whisper acertar a grafia")
    a = ap.parse_args()

    from faster_whisper import WhisperModel

    dica = None
    tempos = a.texto or a.audio.with_name("tempos.json")
    if tempos.exists():
        dica = " ".join(l["text"] for l in json.loads(tempos.read_text(encoding="utf-8"))["linhas"])

    modelo = WhisperModel(a.modelo, device="cpu", compute_type="int8")
    segmentos, _ = modelo.transcribe(str(a.audio), language="pt", word_timestamps=True, initial_prompt=dica)
    palavras = [
        {"p": w.word.strip(), "ini": round(w.start, 2), "fim": round(w.end, 2)}
        for s in segmentos for w in (s.words or []) if w.word.strip()
    ]
    saida = a.audio.with_name("palavras.json")
    saida.write_text(json.dumps(palavras, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(palavras)} palavras -> {saida}")


if __name__ == "__main__":
    main()
