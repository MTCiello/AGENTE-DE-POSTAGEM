"""Narração local de um roteiro, sem créditos.

Gera uma fala por cena (campo `say` do roteiro), junta tudo em `narracao.wav` e calcula
onde cada cena começa. Esses tempos alimentam o `*_TIMES` e as `LINES` da composição
no Remotion, então o vídeo fica sincronizado com a voz de verdade.

Uso:
  python central/voz.py roteiros/2026-10-21-teste-ideia.json --saida audio/teste-ideia     # motor e voz escolhidos no Estúdio de Voz
  python central/voz.py --texto "Oi, tudo bem?" --saida estado/voz/teste.wav       # uma frase só (o Estúdio de Voz usa)
  python central/voz.py roteiro.json --motor chatterbox --ref marca/minha-voz.wav --saida audio/x
  python central/voz.py roteiro.json --motor teste --saida audio/x   # sem modelo, só para testar o fluxo

Motores:
  kokoro      Apache-2.0, roda bem em CPU, vozes pt-br prontas (pm_alex, pm_santa, pf_dora), sem clonagem.
  chatterbox  MIT, clona a voz a partir de --ref (5 a 10 s de fala limpa). CPU funciona, só é mais lento.
  voicestudio o app VoiceStudio (AGPL-3.0, programa separado) aberto no PC: usa a API local dele (MCP em
              127.0.0.1:3900/mcp/). Só o áudio gerado vem para cá; nenhum código dele entra no assistente.
  teste       Tons no lugar da voz, com a duração estimada da fala. Serve para testar mixagem e tempos.

Sem --motor, vale a voz escolhida no Estúdio de Voz do Ciello OS (estado/voz.json); sem escolha, kokoro.
"""
import argparse
import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

PAUSA = 0.22  # respiro entre cenas, em segundos
RAIZ = Path(__file__).resolve().parent.parent
PREFERENCIA = RAIZ / "estado" / "voz.json"  # a voz escolhida no Estúdio de Voz
AMOSTRA = RAIZ / "marca" / "minha-voz.wav"  # a sua voz para clonar (*.wav fica fora do git)
if not AMOSTRA.exists() and (RAIZ / "marca" / "voz-mateus.wav").exists():  # nome antigo (até a 1.0)
    (RAIZ / "marca" / "voz-mateus.wav").rename(AMOSTRA)
VOICESTUDIO = os.environ.get("VOICESTUDIO_URL", "http://127.0.0.1:3900")
MOTORES = ["kokoro", "chatterbox", "voicestudio", "teste"]
PADRAO = {"motor": "kokoro", "voz": "pm_alex", "velocidade": 1.1, "perfil": "", "expressao": 0.5, "cfg": 0.5}


def preferencia() -> dict:
    try:
        return {**PADRAO, **json.loads(PREFERENCIA.read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return dict(PADRAO)


def salvar_preferencia(pref: dict):
    PREFERENCIA.parent.mkdir(parents=True, exist_ok=True)
    PREFERENCIA.write_text(json.dumps({k: pref[k] for k in PADRAO if k in pref}, ensure_ascii=False, indent=1), encoding="utf-8")


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


class VoiceStudio:
    """Cliente mínimo do servidor MCP do VoiceStudio (Streamable HTTP, JSON-RPC). Só biblioteca padrão."""

    def __init__(self, url=None, espera=1800):
        self.url = (url or VOICESTUDIO).rstrip("/") + "/mcp/"
        self.espera, self.sessao, self.n = espera, None, 0

    def _post(self, corpo, espera=None):
        cab = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "X-OmniVoice-Client-Id": "ciello-os"}
        if self.sessao:
            cab["Mcp-Session-Id"] = self.sessao
        req = urllib.request.Request(self.url, json.dumps(corpo).encode(), cab, method="POST")
        with urllib.request.urlopen(req, timeout=espera or self.espera) as r:
            self.sessao = r.headers.get("Mcp-Session-Id") or self.sessao
            texto = r.read().decode("utf-8", "replace")
            tipo = r.headers.get("Content-Type", "")
        if not texto.strip():
            return None
        if "event-stream" in tipo:  # a resposta vem como eventos "data: {...}"
            msgs = [json.loads(l[5:]) for l in texto.splitlines() if l.startswith("data:") and l[5:].strip()]
            return next((m for m in msgs if m.get("id") == corpo.get("id")), msgs[-1] if msgs else None)
        return json.loads(texto)

    def _rpc(self, metodo, params=None, espera=None):
        if self.sessao is None and metodo != "initialize":
            self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                     "clientInfo": {"name": "ciello-os", "version": "1"}}, espera=20)
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, espera=20)
            self.sessao = self.sessao or ""
        self.n += 1
        r = self._post({"jsonrpc": "2.0", "id": self.n, "method": metodo, "params": params or {}}, espera)
        if not r or "error" in r:
            raise RuntimeError(f"VoiceStudio: {(r or {}).get('error', {}).get('message', 'sem resposta')}")
        return r["result"]

    def ferramenta(self, nome, args):
        res = self._rpc("tools/call", {"name": nome, "arguments": args})
        if res.get("isError"):
            textos = " ".join(c.get("text", "") for c in res.get("content", []))
            raise RuntimeError(f"VoiceStudio: {textos or 'erro'}")
        return res

    def esquema(self, nome) -> dict:
        for t in self._rpc("tools/list", espera=20).get("tools", []):
            if t.get("name") == nome:
                return (t.get("inputSchema") or {}).get("properties", {})
        return {}

    @staticmethod
    def _dados(res):
        """Os dados que a ferramenta devolveu: JSON no texto, conteúdo estruturado ou recurso embutido."""
        itens = [res.get("structuredContent")] if res.get("structuredContent") else []
        for c in res.get("content", []):
            if c.get("type") == "text":
                try:
                    itens.append(json.loads(c["text"]))
                except ValueError:
                    pass
            elif c.get("type") == "resource":
                itens.append(c.get("resource") or {})
            elif c.get("type") == "audio":
                itens.append({"wav_base64": c.get("data")})
        return itens

    def vozes(self) -> list[dict]:
        for d in self._dados(self.ferramenta("list_voices", {})):
            lista = d if isinstance(d, list) else d.get("voices") or d.get("profiles") if isinstance(d, dict) else None
            if isinstance(lista, list):
                return [{"id": str(v.get("profile_id") or v.get("id") or ""), "nome": v.get("name") or v.get("nome") or ""}
                        for v in lista if isinstance(v, dict)]
        return []

    def clonar(self, wav: Path, nome: str) -> str:
        props = self.esquema("clone_voice")
        campo = next((k for k in props if "base64" in k), None) or next((k for k in props if "audio" in k and "path" not in k), "ref_audio")
        args = {campo: base64.b64encode(wav.read_bytes()).decode()}
        if "name" in props or not props:
            args["name"] = nome
        for k in ("language", "lang"):
            if k in props:
                args[k] = "Portuguese"
        for d in self._dados(self.ferramenta("clone_voice", args)):
            if isinstance(d, dict) and (d.get("profile_id") or d.get("id")):
                return str(d.get("profile_id") or d.get("id"))
        raise RuntimeError("VoiceStudio não devolveu o id da voz clonada")

    def falar(self, texto: str, perfil: str = ""):
        args = {"text": texto}
        if perfil:
            args["profile_id"] = perfil
        for d in self._dados(self.ferramenta("generate_speech", args)):
            if not isinstance(d, dict):
                continue
            b64 = d.get("wav_base64") or d.get("blob")
            if b64:
                return sf.read(io.BytesIO(base64.b64decode(b64)), dtype="float32")
            if d.get("audio_url"):
                u = d["audio_url"] if d["audio_url"].startswith("http") else self.url[:-5] + d["audio_url"]
                with urllib.request.urlopen(u, timeout=120) as r:
                    return sf.read(io.BytesIO(r.read()), dtype="float32")
        raise RuntimeError("VoiceStudio não devolveu áudio")


def voicestudio_no_ar(url=None) -> bool:
    try:
        with urllib.request.urlopen((url or VOICESTUDIO).rstrip("/") + "/.well-known/voicestudio-speech", timeout=1.5):
            return True
    except urllib.error.HTTPError:
        return True  # respondeu: está aberto
    except (OSError, ValueError):
        return False


def motor_voicestudio(perfil: str):
    vs = VoiceStudio()

    def gerar(texto: str):
        audio, sr = vs.falar(texto, perfil)
        return (audio.mean(axis=1) if audio.ndim > 1 else audio).astype(np.float32), sr

    return gerar


def motor(nome: str, pref: dict):
    if nome == "kokoro":
        return motor_kokoro(pref["voz"], float(pref["velocidade"]))
    if nome == "chatterbox":
        ref = pref.get("ref") or (str(AMOSTRA) if AMOSTRA.exists() else None)
        return motor_chatterbox(ref, pref.get("dispositivo", "cpu"), float(pref["expressao"]), float(pref["cfg"]))
    if nome == "voicestudio":
        return motor_voicestudio(pref.get("perfil", ""))
    return motor_teste()


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
    ap.add_argument("roteiro", type=Path, nargs="?")
    ap.add_argument("--texto", help="gera só esta frase (sem roteiro) no arquivo --saida .wav")
    ap.add_argument("--saida", type=Path, help="pasta onde ficam as falas, a narração e os tempos (com --texto, o .wav)")
    ap.add_argument("--motor", choices=MOTORES, help="padrão: o escolhido no Estúdio de Voz (estado/voz.json)")
    ap.add_argument("--voz", help="voz do kokoro (pm_alex, pm_santa, pf_dora)")
    ap.add_argument("--velocidade", type=float, help="velocidade do kokoro")
    ap.add_argument("--ref", help="áudio de referência para clonar a voz (chatterbox; padrão: marca/minha-voz.wav)")
    ap.add_argument("--perfil", help="id da voz no VoiceStudio")
    ap.add_argument("--dispositivo", default="cpu", help="cpu, cuda ou auto (chatterbox)")
    ap.add_argument("--expressao", type=float, help="exaggeration do chatterbox")
    ap.add_argument("--cfg", type=float, help="cfg_weight do chatterbox (menor = fala mais pausada)")
    ap.add_argument("--cauda", type=float, default=0.8, help="segundos de vídeo depois da última fala")
    ap.add_argument("--nome", default="X", help="prefixo da constante TS impressa no fim (ex.: TESTE)")
    ap.add_argument("--clonar-voicestudio", metavar="NOME", help="clona marca/minha-voz.wav no VoiceStudio e passa a usar essa voz")
    ap.add_argument("--vozes-voicestudio", action="store_true", help="lista as vozes do VoiceStudio (JSON)")
    a = ap.parse_args()

    pref = preferencia()
    for k in ("motor", "voz", "velocidade", "ref", "perfil", "expressao", "cfg"):
        if getattr(a, k) is not None:
            pref[k] = getattr(a, k)
    pref["dispositivo"] = a.dispositivo

    if a.vozes_voicestudio:
        print(json.dumps(VoiceStudio(espera=30).vozes(), ensure_ascii=False))
        return
    if a.clonar_voicestudio:
        if not AMOSTRA.exists():
            sys.exit("Grave a sua voz antes (Estúdio de Voz → Gravar).")
        print("Clonando no VoiceStudio (na 1ª vez ele baixa o modelo, uns 2 GB)...", flush=True)
        perfil = VoiceStudio().clonar(AMOSTRA, a.clonar_voicestudio)
        salvar_preferencia({**pref, "motor": "voicestudio", "perfil": perfil})
        print(f"voz clonada no VoiceStudio: {perfil}. Os vídeos novos já saem com ela.")
        return
    if not a.saida or not (a.texto or a.roteiro):
        ap.error("informe o roteiro (ou --texto) e --saida")

    print(f"motor: {pref['motor']}" + (f" · voz {pref['voz']}" if pref["motor"] == "kokoro" else ""), flush=True)
    gerar = motor(pref["motor"], pref)

    if a.texto:
        audio, sr = gerar(a.texto.strip())
        a.saida.parent.mkdir(parents=True, exist_ok=True)
        sf.write(a.saida, aparar(audio, sr), sr)
        print(f"ok: {a.saida} ({len(audio) / sr:.1f}s)")
        return

    textos = falas(a.roteiro)
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
        json.dumps({"motor": pref["motor"], "tempos": tempos, "linhas": linhas}, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(f"\nnarração: {a.saida / 'narracao.wav'} ({len(narracao) / sr_final:.2f}s)")
    print("Cole na composição (ajuste os *grifos* nas LINES):")
    ts = json.dumps(tempos).replace('"', "")
    print(f"export const {a.nome}_TIMES = {ts};")


if __name__ == "__main__":
    from status import trabalhando
    with trabalhando("produtor-video", "narração"):
        main()
