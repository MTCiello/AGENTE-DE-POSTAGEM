"""Cofre das credenciais (tokens do Metricool, Instagram, YouTube, TikTok).

No Windows as senhas são cifradas com a DPAPI: só o seu usuário, neste PC, consegue abrir o arquivo
estado/cofre.json (copiar para outro PC não funciona, e é de propósito). Fora do Windows (testes, servidor)
elas ficam só codificadas, e a janela Conexões avisa. O cofre nunca vai para o git (estado/ é ignorado).
"""
import base64
import json
import sys

import dados


def _dpapi(dados_bytes: bytes, cifrar: bool) -> bytes:
    import ctypes
    from ctypes import wintypes

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    entrada = BLOB(len(dados_bytes), ctypes.cast(ctypes.create_string_buffer(dados_bytes, len(dados_bytes)), ctypes.POINTER(ctypes.c_char)))
    saida = BLOB()
    funcao = ctypes.windll.crypt32.CryptProtectData if cifrar else ctypes.windll.crypt32.CryptUnprotectData
    if not funcao(ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida)):
        raise OSError("DPAPI recusou (o cofre foi criado por outro usuário ou outro PC?)")
    try:
        return ctypes.string_at(saida.pbData, saida.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(saida.pbData)


def protegido() -> bool:
    return sys.platform == "win32"


def _fechar(texto: str) -> str:
    b = texto.encode("utf-8")
    return ("dpapi:" + base64.b64encode(_dpapi(b, True)).decode()) if protegido() else ("b64:" + base64.b64encode(b).decode())


def _abrir(guardado: str) -> str:
    tipo, _, corpo = guardado.partition(":")
    b = base64.b64decode(corpo)
    return (_dpapi(b, False) if tipo == "dpapi" else b).decode("utf-8")


def _arquivo():
    return dados.estado("cofre.json")


def _todos() -> dict:
    try:
        return json.loads(_arquivo().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ler(chave: str) -> dict:
    guardado = _todos().get(chave)
    if not guardado:
        return {}
    try:
        return json.loads(_abrir(guardado))
    except (OSError, ValueError):
        return {}


def guardar(chave: str, valores: dict):
    tudo = _todos()
    tudo[chave] = _fechar(json.dumps(valores, ensure_ascii=False))
    _arquivo().write_text(json.dumps(tudo, indent=1), encoding="utf-8")


def apagar(chave: str):
    tudo = _todos()
    if tudo.pop(chave, None) is not None:
        _arquivo().write_text(json.dumps(tudo, indent=1), encoding="utf-8")
