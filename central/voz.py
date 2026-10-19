"""Narração local de um roteiro, sem créditos.

Gera uma fala por cena (campo `say` do roteiro), junta tudo em `narracao.wav` e calcula
onde cada cena começa. Esses tempos alimentam o `*_TIMES` e as `LINES` da composição
no Remotion, então o vídeo fica sincronizado com a voz de verdade.

Uso:
  python central/voz.py roteiros/2026-10-21-teste-ideia.json --saida audio/teste-ideia
  python central/voz.py roteiro.json --motor chatterbox --ref marca/voz-mateus.wav --saida audio/x
  python central/voz.py roteiro.json --motor teste --saida audio/x   # sem modelo, só para testar o fluxo

Motores:
  kokoro      Apache-2.0, roda bem em CPU, vozes pt-br prontas (pm_alex, pm_santa, pf_dora), sem clonagem.
  chatterbox  MIT, clona a voz a partir de --ref (5 a 10 s de fala limpa). CPU funciona, só é mais lento.
  teste       Tons no lugar da voz, com a duração estimada da fala. Serve para testar mixagem e tempos.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

PAUSA = 0.22  # respiro entre cenas, em segundos


def falas(roteiro: Path) -> list[str]:
    cenas = json.loads(roteiro.read_text(encoding="utf-8"))["scenes"]
    textos = [c.get("say", "").strip() for c in cenas]
    if not all(textos):
        sys.exit("Toda cena precisa do campo 'say' com a fala.")
    return textos


def motor_kokoro(voz: str, velocidade: float):
    from kokoro import KPipeline

    pipe = KPipeline(lang_code="p")  # 'p' = português do Brasil

    def gerar(texto: str):
        partes = [audio for _, _, audio in pipe(texto, voice=voz, speed=velocidade)]
        return np.concatenate([np.asarray(p, dtype=np.float32) for p in partes]), 24000

    return gerar


def motor_chatterbox(ref: str | None, dispositivo: str, expressao: float, cfg: float):
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    if dispositivo == "auto":
        # O PyTorch para AMD (ROCm) também responde por torch.cuda.
        dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    modelo = ChatterboxMultilingualTTS.from_pretrained(device=dispositivo)

    def gerar(texto: str):
        wav = modelo.generate(texto, language_id="pt", audio_prompt_path=ref, exaggeration=expressao, cfg_weight=cfg)
        return wav.squeeze().detach().cpu().numpy().astype(np.float32), modelo.sr

    return gerar


def motor_teste():
    def gerar(texto: str):
        sr = 24000
        dur = 0.35 + len(texto) / 15  # ~15 caracteres por segundo de fala
        t = np.arange(int(dur * sr)) / sr
        tom = 0.25 * np.sin(2 * np.pi * 220 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))
        return tom.astype(np.float32), sr

    return gerar


def aparar(audio: np.ndarray, sr: int, limiar_db: float = -42) -> np.ndarray:
    """Corta o silêncio do começo e do fim, deixando 40 ms de folga."""
    janela = max(1, int(sr * 0.01))
    n = len(audio) // janela
    if n == 0:
        return audio
    rms = np.sqrt(np.mean(audio[: n * janela].reshape(n, janela) ** 2, axis=1) + 1e-12)
    ativo = np.where(20 * np.log10(rms) > limiar_db)[0]
    if len(ativo) == 0:
        return audio
    folga = int(sr * 0.04)
    ini = max(0, ativo[0] * janela - folga)
    fim = min(len(audio), (ativo[-1] + 1) * janela + folga)
    return audio[ini:fim]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roteiro", type=Path)
    ap.add_argument("--saida", type=Path, required=True, help="pasta onde ficam as falas, a narração e os tempos")
    ap.add_argument("--motor", choices=["kokoro", "chatterbox", "teste"], default="kokoro")
    ap.add_argument("--voz", default="pm_alex", help="voz do kokoro (pm_alex, pm_santa, pf_dora)")
    ap.add_argument("--velocidade", type=float, default=1.1, help="velocidade do kokoro")
    ap.add_argument("--ref", help="áudio de referência para clonar a voz (chatterbox)")
    ap.add_argument("--dispositivo", default="cpu", help="cpu, cuda ou auto (chatterbox)")
    ap.add_argument("--expressao", type=float, default=0.5, help="exaggeration do chatterbox")
    ap.add_argument("--cfg", type=float, default=0.5, help="cfg_weight do chatterbox (menor = fala mais pausada)")
    ap.add_argument("--cauda", type=float, default=0.8, help="segundos de vídeo depois da última fala")
    ap.add_argument("--nome", default="X", help="prefixo da constante TS impressa no fim (ex.: TESTE)")
    a = ap.parse_args()

    textos = falas(a.roteiro)
    if a.motor == "kokoro":
        gerar = motor_kokoro(a.voz, a.velocidade)
    elif a.motor == "chatterbox":
        gerar = motor_chatterbox(a.ref, a.dispositivo, a.expressao, a.cfg)
    else:
        gerar = motor_teste()

    a.saida.mkdir(parents=True, exist_ok=True)
    trechos, linhas, t, sr_final = [], [], 0.0, None
    for i, texto in enumerate(textos, 1):
        audio, sr = gerar(texto)
        if sr_final is None:
            sr_final = sr
        elif sr != sr_final:
            sys.exit("O motor devolveu taxas de amostragem diferentes entre cenas.")
        audio = aparar(audio, sr)
        sf.write(a.saida / f"cena{i}.wav", audio, sr)
        dur = len(audio) / sr
        linhas.append({"from": round(t, 2), "to": round(t + dur, 2), "text": texto})
        trechos += [audio, np.zeros(int(PAUSA * sr), dtype=np.float32)]
        t += dur + PAUSA
        print(f"cena {i}: {dur:5.2f}s  {texto[:60]}")

    narracao = np.concatenate(trechos[:-1])  # sem a pausa depois da última fala
    sf.write(a.saida / "narracao.wav", narracao, sr_final)

    fim = linhas[-1]["to"]
    tempos = {f"s{i}": l["from"] for i, l in enumerate(linhas[1:], 1)}
    tempos.update({"end": fim, "total": round(fim + a.cauda, 2)})
    (a.saida / "tempos.json").write_text(
        json.dumps({"motor": a.motor, "tempos": tempos, "linhas": linhas}, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(f"\nnarração: {a.saida / 'narracao.wav'} ({len(narracao) / sr_final:.2f}s)")
    print("Cole na composição (ajuste os *grifos* nas LINES):")
    ts = json.dumps(tempos).replace('"', "")
    print(f"export const {a.nome}_TIMES = {ts};")


if __name__ == "__main__":
    from status import trabalhando
    with trabalhando("produtor-video", "narração"):
        main()
