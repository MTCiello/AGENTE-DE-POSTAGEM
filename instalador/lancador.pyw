"""Lançador do Ciello OS: é o que o ícone da área de trabalho e do menu Iniciar abre.

1. Se o Ciello OS já está aberto, só traz a janela de novo.
2. De tempos em tempos (padrão: 12 h) procura atualização no GitHub; se tiver, pergunta se quer atualizar.
3. Liga o servidor (central/escritorio/servidor.py) numa janela minimizada da barra de tarefas
   e abre o Ciello OS numa janela própria do Edge/Chrome. Fechar a janela do servidor desliga tudo.
"""
import os
import socket
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
import atualizacao  # noqa: E402

PORTA = 3200


def no_ar(porta=PORTA):
    try:
        with socket.create_connection(("127.0.0.1", porta), timeout=0.5):
            return True
    except OSError:
        return False


def python_console():
    return atualizacao.python_do_assistente(RAIZ)


def janela_do_app(url):
    """Mesma regra do servidor: Edge ou Chrome em modo app; senão, o navegador padrão."""
    candidatos = []
    for var in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            candidatos += [os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"),
                           os.path.join(base, "Google", "Chrome", "Application", "chrome.exe")]
    for exe in candidatos:
        if os.path.exists(exe):
            subprocess.Popen([exe, f"--app={url}", "--start-maximized"])
            return
    import webbrowser
    webbrowser.open(url)


def ligar_servidor():
    env = {**os.environ, "PYTHONUTF8": "1"}
    servidor = RAIZ / "central" / "escritorio" / "servidor.py"
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 7  # SW_SHOWMINNOACTIVE: fica minimizada na barra de tarefas
        cmd = f'title Ciello OS (feche esta janela para desligar) && "{python_console()}" "{servidor}"'
        subprocess.Popen(["cmd", "/c", cmd], cwd=RAIZ, env=env, startupinfo=si,
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        subprocess.Popen([python_console(), str(servidor)], cwd=RAIZ, env=env)


def perguntar_atualizacao():
    """Procura (sem travar por mais de 6 s) e pergunta. Sem internet, segue em frente calado."""
    if not atualizacao.hora_de_verificar():
        info = atualizacao.estado().get("ultima_consulta") or {}
    else:
        info = atualizacao.verificar(tempo=6)
    if not info.get("nova"):
        return
    raiz_tk = tk.Tk()
    raiz_tk.withdraw()
    try:
        raiz_tk.iconbitmap(default=str(AQUI / "marca" / "ciello.ico"))
    except tk.TclError:
        pass
    sim = messagebox.askyesno("Ciello OS", f"Tem versão nova do Ciello OS: {info.get('versao')}.\n\n"
                              f"{info.get('titulo', '')}\n\nQuer ver e atualizar agora?\n"
                              "(Os seus dados não são tocados.)", parent=raiz_tk)
    raiz_tk.destroy()
    if sim:
        exe = Path(sys.executable)
        subprocess.run([str(exe), str(AQUI / "atualizador.pyw")], cwd=RAIZ)


def main():
    if no_ar():
        janela_do_app(f"http://127.0.0.1:{PORTA}")
        return
    try:
        perguntar_atualizacao()
    except Exception:  # noqa: BLE001  atualização nunca impede o Ciello OS de abrir
        pass
    ligar_servidor()


if __name__ == "__main__":
    main()
