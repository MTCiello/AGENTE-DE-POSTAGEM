"""Janela de Atualizações do Ciello OS (atalho "Atualizações do Ciello OS" no menu Iniciar).

Mostra a versão instalada, procura versão nova no GitHub (botão ou sozinha ao abrir o Ciello OS),
mostra o que mudou e instala com um clique. Os seus dados não são tocados (ver atualizacao.py).
"""
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atualizacao  # noqa: E402

AZUL, AZUL_ESCURO, MARFIM, OURO, CARVAO = "#263A59", "#18263C", "#F8F4E8", "#E0A81C", "#161616"
ICONE = Path(__file__).resolve().parent / "marca" / "ciello.ico"
CANAIS = {"estavel": "Estável (versões publicadas)", "teste": "Teste (última versão da branch de desenvolvimento)"}


class Janela:
    def __init__(self, raiz_tk, procurar_ja=False):
        self.tk = raiz_tk
        self.info = None
        raiz_tk.title("Atualizações do Ciello OS")
        raiz_tk.geometry("620x520")
        raiz_tk.minsize(520, 440)
        raiz_tk.configure(bg=MARFIM)
        try:
            raiz_tk.iconbitmap(default=str(ICONE))
        except tk.TclError:
            pass

        topo = tk.Frame(raiz_tk, bg=AZUL, height=86)
        topo.pack(fill="x")
        tk.Label(topo, text="CIELLO OS", bg=AZUL, fg=MARFIM, font=("Segoe UI Semibold", 18)).pack(anchor="w", padx=20, pady=(14, 0))
        self.versao = tk.Label(topo, bg=AZUL, fg=OURO, font=("Segoe UI", 10))
        self.versao.pack(anchor="w", padx=20, pady=(0, 14))

        corpo = tk.Frame(raiz_tk, bg=MARFIM)
        corpo.pack(fill="both", expand=True, padx=20, pady=14)
        self.status = tk.Label(corpo, bg=MARFIM, fg=CARVAO, font=("Segoe UI Semibold", 12), anchor="w", justify="left", wraplength=560)
        self.status.pack(fill="x")
        self.detalhe = tk.Label(corpo, bg=MARFIM, fg="#555", font=("Segoe UI", 9), anchor="w", justify="left")
        self.detalhe.pack(fill="x", pady=(2, 8))

        self.texto = tk.Text(corpo, height=12, wrap="word", relief="flat", bg="white", fg=CARVAO, font=("Consolas", 9), padx=8, pady=6)
        self.texto.pack(fill="both", expand=True)
        self.barra = ttk.Progressbar(corpo, mode="indeterminate")

        opcoes = tk.Frame(corpo, bg=MARFIM)
        opcoes.pack(fill="x", pady=(10, 0))
        cfg = atualizacao.config()
        self.auto = tk.BooleanVar(value=cfg["verificar_ao_abrir"])
        tk.Checkbutton(opcoes, text="Procurar sozinho ao abrir o Ciello OS", variable=self.auto, bg=MARFIM,
                       activebackground=MARFIM, command=self.mudou_auto).pack(side="left")
        self.canal = tk.StringVar(value=CANAIS[cfg["canal"]])
        combo = ttk.Combobox(opcoes, textvariable=self.canal, values=list(CANAIS.values()), state="readonly", width=34)
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>", self.mudou_canal)
        if atualizacao.eh_git():
            combo.configure(state="disabled")

        botoes = tk.Frame(corpo, bg=MARFIM)
        botoes.pack(fill="x", pady=(12, 0))
        self.bt_procurar = tk.Button(botoes, text="Procurar atualizações", command=self.procurar, bg=AZUL, fg=MARFIM,
                                     activebackground=AZUL_ESCURO, activeforeground=MARFIM, relief="flat", padx=14, pady=6)
        self.bt_procurar.pack(side="left")
        self.bt_aplicar = tk.Button(botoes, text="Atualizar agora", command=self.aplicar, bg=OURO, fg=CARVAO,
                                    activebackground="#C8921A", relief="flat", padx=14, pady=6, state="disabled")
        self.bt_aplicar.pack(side="left", padx=8)
        self.bt_pagina = tk.Button(botoes, text="Ver no GitHub", command=self.pagina, relief="flat", padx=10, pady=6)
        self.bt_pagina.pack(side="right")

        self.pintar_status()
        if procurar_ja:
            self.tk.after(300, self.procurar)

    # ------------------------------------------------------------ tela
    def pintar_status(self):
        s = atualizacao.resumo_status()
        canal = {"git": "pasta do Git", "estavel": "estável", "teste": "teste"}[s["canal"]]
        self.versao.configure(text=f"Versão instalada: {s['versao']}  ·  canal {canal}")
        ult = (s["ultima_verificacao"] or "").replace("T", " às ")[:19]
        self.detalhe.configure(text=f"Última verificação: {ult or 'nunca'}")
        c = s["consulta"]
        self.mostrar(c) if c else self.status.configure(text="Clique em Procurar atualizações.")

    def mostrar(self, info):
        self.info = info
        if info.get("erro"):
            self.status.configure(text=info["erro"], fg="#B5442F")
            self.bt_aplicar.configure(state="disabled")
            return
        if info.get("nova"):
            self.status.configure(text=f"Versão nova disponível: {info['versao']}  ·  {info.get('titulo', '')}", fg="#1F8A4C")
            self.bt_aplicar.configure(state="normal")
            self.escrever("O que mudou:\n\n" + (info.get("notas") or "(sem notas)"))
        else:
            self.status.configure(text="Você está na versão mais nova." if info.get("versao") else info.get("titulo", ""), fg=CARVAO)
            self.bt_aplicar.configure(state="disabled")

    def escrever(self, t, limpar=True):
        self.texto.configure(state="normal")
        if limpar:
            self.texto.delete("1.0", "end")
        self.texto.insert("end", t + ("" if limpar else "\n"))
        self.texto.see("end")

    def ocupado(self, sim):
        estado = "disabled" if sim else "normal"
        self.bt_procurar.configure(state=estado)
        if sim:
            self.bt_aplicar.configure(state="disabled")
            self.barra.pack(fill="x", pady=(8, 0))
            self.barra.start(12)
        else:
            self.barra.stop()
            self.barra.pack_forget()

    # ------------------------------------------------------------ ações
    def mudou_auto(self):
        atualizacao.salvar_config(verificar_ao_abrir=self.auto.get())

    def mudou_canal(self, _e=None):
        canal = next(k for k, v in CANAIS.items() if v == self.canal.get())
        atualizacao.salvar_config(canal=canal)
        self.procurar()

    def pagina(self):
        url = (self.info or {}).get("pagina") or f"https://github.com/{atualizacao.config()['repo']}/releases"
        webbrowser.open(url)

    def procurar(self):
        self.ocupado(True)
        self.status.configure(text="Procurando no GitHub...", fg=CARVAO)

        def trabalho():
            info = atualizacao.verificar()
            self.tk.after(0, lambda: (self.ocupado(False), self.pintar_status(), self.mostrar(info)))
        threading.Thread(target=trabalho, daemon=True).start()

    def aplicar(self):
        self.ocupado(True)
        self.status.configure(text="Atualizando... não feche esta janela.", fg=CARVAO)
        self.escrever("")
        info = self.info

        def avisar(linha):
            self.tk.after(0, lambda: self.escrever(str(linha), limpar=False))

        def trabalho():
            try:
                r = atualizacao.aplicar(info=info if info and info.get("canal") != "git" else None, avisar=avisar)
            except Exception as e:  # noqa: BLE001  qualquer falha vira mensagem na janela
                r = {"ok": False, "erro": f"A atualização não terminou: {e}. Nada dos seus dados foi tocado."}

            def fim():
                self.ocupado(False)
                self.pintar_status()
                if r.get("ok"):
                    self.status.configure(text=f"Pronto! Ciello OS {r.get('versao')}. Feche e abra o Ciello OS.", fg="#1F8A4C")
                    self.bt_aplicar.configure(state="disabled")
                else:
                    self.status.configure(text=r.get("erro", "Não deu certo."), fg="#B5442F")
            self.tk.after(0, fim)
        threading.Thread(target=trabalho, daemon=True).start()


def main():
    raiz_tk = tk.Tk()
    Janela(raiz_tk, procurar_ja="--procurar" in sys.argv)
    raiz_tk.mainloop()


if __name__ == "__main__":
    main()
