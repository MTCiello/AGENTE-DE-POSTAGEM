"""Estúdio de Voz do Ciello OS: gravar a sua voz, testar frases, escolher a voz dos vídeos e ligar o VoiceStudio.

A gravação vem do microfone pela janela, é convertida pelo ffmpeg em marca/voz-mateus.wav (fora do git: *.wav) e
é a referência que o Chatterbox usa para clonar. Os testes rodam o central/voz.py em segundo plano (o Chatterbox
leva de segundos a minutos no processador) e ficam em estado/voz/testes/ para ouvir na janela.
A escolha (motor, voz, id no VoiceStudio) fica em estado/voz.json e vale para todos os vídeos novos.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

import voz

RAIZ = voz.RAIZ
PASTA = RAIZ / "estado" / "voz"
VOZES_KOKORO = [["pm_alex", "Alex (masculina)"], ["pm_santa", "Santa (masculina)"], ["pf_dora", "Dora (feminina)"]]
FORMATOS = (".webm", ".ogg", ".wav", ".mp3", ".m4a", ".opus")
TEXTO_PADRAO = "Oi, aqui é o Mateus, da Ciello. Hoje eu vou te mostrar três comandos de IA que respondem cliente por você."


def instalado(modulo) -> bool:
    try:
        return importlib.util.find_spec(modulo) is not None
    except (ImportError, ValueError):
        return False


def duracao(arq: Path) -> float | None:
    try:
        return round(voz.sf.info(str(arq)).duration, 1)
    except (RuntimeError, OSError):
        return None


def estado() -> dict:
    testes = sorted((PASTA / "testes").glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)[:8]
    return {"preferencia": voz.preferencia(),
            "amostra": {"existe": voz.AMOSTRA.exists(), "duracao": duracao(voz.AMOSTRA) if voz.AMOSTRA.exists() else None,
                        "quando": dt.datetime.fromtimestamp(voz.AMOSTRA.stat().st_mtime).strftime("%d/%m %H:%M") if voz.AMOSTRA.exists() else ""},
            "motores": {"kokoro": instalado("kokoro"), "chatterbox": instalado("chatterbox"), "voicestudio": voz.voicestudio_no_ar()},
            "ffmpeg": bool(shutil.which("ffmpeg")), "vozes_kokoro": VOZES_KOKORO, "texto_padrao": TEXTO_PADRAO,
            "testes": [{"arquivo": t.name, "duracao": duracao(t), "quando": dt.datetime.fromtimestamp(t.stat().st_mtime).strftime("%d/%m %H:%M"),
                        "motor": t.stem.split("-")[-1]} for t in testes]}


def salvar_amostra(nome, dados: bytes) -> dict:
    """A gravação da janela (webm/ogg do navegador, ou um arquivo de áudio) vira marca/voz-mateus.wav, mono 24 kHz."""
    ext = Path(str(nome or "")).suffix.lower() or ".webm"
    if ext not in FORMATOS:
        return {"ok": False, "saida": f"Formato {ext} não serve: use webm, ogg, wav, mp3 ou m4a."}
    bruto = PASTA / "amostras" / f"{dt.datetime.now():%Y-%m-%d-%H%M%S}{ext}"
    bruto.parent.mkdir(parents=True, exist_ok=True)
    bruto.write_bytes(dados)
    voz.AMOSTRA.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("ffmpeg"):
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(bruto), "-ac", "1", "-ar", "24000", str(voz.AMOSTRA)],
                           capture_output=True, text=True, timeout=120)
        if r.returncode:
            return {"ok": False, "saida": f"O ffmpeg não conseguiu ler a gravação: {r.stderr.strip()[-300:]}"}
    elif ext == ".wav":
        shutil.copy(bruto, voz.AMOSTRA)
    else:
        return {"ok": False, "saida": "Falta o ffmpeg para converter a gravação (rode o instalar.cmd)."}
    seg = duracao(voz.AMOSTRA) or 0
    dica = " Ficou curta: o ideal é de 10 a 20 segundos." if seg < 6 else ""
    return {"ok": True, "saida": f"Sua voz foi salva ({seg:.0f} s).{dica}", "duracao": seg}


def args_teste(dados: dict) -> tuple[list[str], str]:
    """Argumentos do voz.py para testar uma frase, só com valores conferidos. Devolve (args, arquivo de saída)."""
    texto = re.sub(r"\s+", " ", str(dados.get("texto") or TEXTO_PADRAO)).strip()[:400]
    motor = dados.get("motor") or voz.preferencia()["motor"]
    if motor not in voz.MOTORES:
        raise ValueError("motor inválido")
    nome = f"{dt.datetime.now():%Y%m%d-%H%M%S}-{motor}.wav"
    args = ["central/voz.py", f"--texto={texto}", f"--saida={PASTA / 'testes' / nome}", f"--motor={motor}"]
    if motor == "kokoro" and dados.get("voz"):
        if dados["voz"] not in [v for v, _ in VOZES_KOKORO]:
            raise ValueError("voz inválida")
        args.append(f"--voz={dados['voz']}")
    if motor == "voicestudio" and dados.get("perfil"):
        if not re.fullmatch(r"[\w.\-]{1,80}", str(dados["perfil"])):
            raise ValueError("id de voz inválido")
        args.append(f"--perfil={dados['perfil']}")
    return args, nome


def preferir(dados: dict) -> dict:
    pref = voz.preferencia()
    motor = dados.get("motor") or pref["motor"]
    if motor not in voz.MOTORES or motor == "teste":
        return {"ok": False, "saida": "motor inválido"}
    pref["motor"] = motor
    if dados.get("voz"):
        if dados["voz"] not in [v for v, _ in VOZES_KOKORO]:
            return {"ok": False, "saida": "voz inválida"}
        pref["voz"] = dados["voz"]
    if dados.get("perfil") is not None:
        if dados["perfil"] and not re.fullmatch(r"[\w.\-]{1,80}", str(dados["perfil"])):
            return {"ok": False, "saida": "id de voz inválido"}
        pref["perfil"] = str(dados["perfil"])
    if motor == "chatterbox" and not voz.AMOSTRA.exists():
        return {"ok": False, "saida": "Grave a sua voz antes de escolher o Chatterbox (ele clona a partir da gravação)."}
    voz.salvar_preferencia(pref)
    rotulo = {"kokoro": f"voz pronta {pref['voz']}", "chatterbox": "a sua voz (Chatterbox)", "voicestudio": "a voz do VoiceStudio"}[motor]
    return {"ok": True, "saida": f"Os vídeos novos vão sair com {rotulo}."}


def arquivo(nome: str) -> Path | None:
    """Um áudio que a janela pode tocar: a sua gravação ou um teste."""
    if nome == "amostra.wav":
        return voz.AMOSTRA if voz.AMOSTRA.exists() else None
    alvo = (PASTA / "testes" / Path(nome).name).resolve()
    return alvo if alvo.is_file() and alvo.suffix == ".wav" and alvo.parent == (PASTA / "testes").resolve() else None
