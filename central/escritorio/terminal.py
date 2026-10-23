"""Terminal do Claude dentro do Ciello OS: o Claude Code roda num pseudo-terminal e a janela do OS (xterm.js) mostra.

  - Windows: pywinpty (ConPTY), instalado pelo instalar.cmd (central/requirements.txt)
  - Linux/macOS: o pty da biblioteca padrão (usado nos testes)

Cada terminal tem um id, guarda o fim da saída (para a janela reabrir mostrando o que já passou) e repassa o que sai
para quem está olhando (o WebSocket /terminal da janela). Fechar a janela encerra o processo.
"""
from __future__ import annotations

import itertools
import os
import shutil
import subprocess
import sys
import threading

GUARDAR = 200_000  # caracteres do fim da saída guardados por terminal
LINHAS, COLUNAS = 30, 110

# o comando do Claude Code; os testes trocam por um script falso
COMANDO_CLAUDE: list[str] | None = None
# modelos que a janela pode pedir (--model): o Gerente abre no sonnet e escolhe o modelo de cada etapa (gerente.md)
MODELOS = ("haiku", "sonnet", "opus")


def comando_claude(prompt: str | None = None, pular_permissoes: bool = False, modelo: str | None = None) -> list[str]:
    if COMANDO_CLAUDE:
        base = list(COMANDO_CLAUDE)
    else:
        claude = shutil.which("claude")
        if not claude:
            aviso = ("Claude Code não encontrado neste PC. Para instalar, abra o PowerShell e rode: "
                     "irm https://claude.ai/install.ps1 | iex   (depois feche e abra este terminal de novo)")
            return [sys.executable, "-c", f"print({aviso!r}); input('\\nEnter para fechar...')"]
        base = ["cmd.exe", "/c", claude] if claude.lower().endswith((".cmd", ".bat")) else [claude]
    if pular_permissoes:
        base.append("--dangerously-skip-permissions")
    if modelo in MODELOS:
        base += ["--model", modelo]
    if prompt:
        base.append(prompt)
    return base


class _Pty:
    """O mesmo jeitinho para Windows (pywinpty) e para Linux/macOS (pty)."""

    def __init__(self, argv, cwd, linhas, colunas):
        env = {**os.environ, "TERM": "xterm-256color", "PYTHONUTF8": "1", "FORCE_COLOR": "1"}
        if os.name == "nt":
            from winpty import PtyProcess  # pywinpty
            self.proc = PtyProcess.spawn(list(argv), cwd=str(cwd), env=env, dimensions=(linhas, colunas))
            self.windows = True
        else:
            import pty
            self.windows = False
            self.mestre, escravo = pty.openpty()
            self._tamanho(escravo, linhas, colunas)
            self.proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=escravo, stdout=escravo, stderr=escravo,
                                         start_new_session=True, close_fds=True)
            os.close(escravo)

    @staticmethod
    def _tamanho(fd, linhas, colunas):
        import fcntl
        import struct
        import termios
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", linhas, colunas, 0, 0))

    def ler(self) -> str | None:
        """Bloqueia até ter saída; None quando o processo acabou."""
        if self.windows:
            try:
                dados = self.proc.read(65536)
            except EOFError:
                return None
            return dados if dados or self.proc.isalive() else None
        try:
            dados = os.read(self.mestre, 65536)
        except OSError:
            return None
        return dados.decode("utf-8", "replace") if dados else None

    def escrever(self, texto: str):
        if self.windows:
            self.proc.write(texto)
        else:
            os.write(self.mestre, texto.encode("utf-8"))

    def redimensionar(self, linhas, colunas):
        if self.windows:
            self.proc.setwinsize(linhas, colunas)
        else:
            self._tamanho(self.mestre, linhas, colunas)

    def codigo(self):
        if self.windows:
            return None if self.proc.isalive() else (self.proc.exitstatus or 0)
        return self.proc.poll()

    def encerrar(self):
        try:
            if self.windows:
                self.proc.terminate(force=True)
            else:
                self.proc.terminate()
                try:
                    self.proc.wait(2)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                os.close(self.mestre)
        except OSError:
            pass


class Terminal:
    def __init__(self, tid, argv, cwd, titulo="", linhas=LINHAS, colunas=COLUNAS):
        self.id, self.titulo = tid, titulo
        self.saida = ""
        self.fim = None  # código de saída quando o processo acaba
        self.ouvintes = []
        self.trava = threading.Lock()
        self.pty = _Pty(argv, cwd, linhas, colunas)
        threading.Thread(target=self._ler, name=f"terminal-{tid}", daemon=True).start()

    def _ler(self):
        while (dados := self.pty.ler()) is not None:
            with self.trava:
                self.saida = (self.saida + dados)[-GUARDAR:]
                ouvintes = list(self.ouvintes)
            for o in ouvintes:
                o({"tipo": "saida", "dados": dados})
        codigo = self.pty.codigo()
        with self.trava:
            self.fim = 0 if codigo is None else codigo
            ouvintes = list(self.ouvintes)
        for o in ouvintes:
            o({"tipo": "fim", "codigo": self.fim})

    def ouvir(self, ouvinte):
        """Começa a mandar a saída para `ouvinte`, a partir do que já passou."""
        with self.trava:
            self.ouvintes.append(ouvinte)
            passado, fim = self.saida, self.fim
        if passado:
            ouvinte({"tipo": "saida", "dados": passado})
        if fim is not None:
            ouvinte({"tipo": "fim", "codigo": fim})

    def largar(self, ouvinte):
        with self.trava:
            if ouvinte in self.ouvintes:
                self.ouvintes.remove(ouvinte)

    def escrever(self, texto):
        if self.fim is None:
            self.pty.escrever(texto)

    def redimensionar(self, linhas, colunas):
        if self.fim is None and 2 <= linhas <= 500 and 10 <= colunas <= 1000:
            self.pty.redimensionar(int(linhas), int(colunas))

    def encerrar(self):
        self.pty.encerrar()


class Terminais:
    def __init__(self, cwd):
        self.cwd = cwd
        self.todos: dict[str, Terminal] = {}
        self.contador = itertools.count(1)
        self.trava = threading.Lock()

    def abrir(self, prompt=None, titulo="", pular_permissoes=False, modelo=None) -> Terminal:
        with self.trava:
            tid = str(next(self.contador))
        t = Terminal(tid, comando_claude(prompt, pular_permissoes, modelo), self.cwd, titulo)
        self.todos[tid] = t
        return t

    def get(self, tid) -> Terminal | None:
        return self.todos.get(str(tid))

    def fechar(self, tid):
        t = self.todos.pop(str(tid), None)
        if t:
            t.encerrar()

    def fechar_todos(self):
        for tid in list(self.todos):
            self.fechar(tid)
