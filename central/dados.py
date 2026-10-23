"""Onde o Ciello OS guarda os dados do usuário, e o banco local da rede social.

Hoje tudo mora na pasta do assistente (clonada do GitHub). No produto instalado, o programa fica em
"Arquivos de Programas" e os dados em %LOCALAPPDATA%\\Ciello: basta definir CIELLO_DADOS e nenhum módulo
novo precisa mudar. Os dados nunca dependem de um provedor externo: o que vem do Metricool, Instagram,
YouTube ou TikTok é copiado para cá, então desconectar um provedor não apaga histórico nem trabalho.
"""
import os
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent  # onde está o programa


def pasta_dados() -> Path:
    return Path(os.environ.get("CIELLO_DADOS") or RAIZ)


def estado(*partes) -> Path:
    """Arquivo dentro de estado/ (fora do git), criando a pasta."""
    p = pasta_dados() / "estado"
    p.mkdir(parents=True, exist_ok=True)
    return p.joinpath(*partes)


# versão -> comandos. Só acrescente versões novas no fim: o banco de quem já usa sobe sozinho.
MIGRACOES = {
    1: """
    CREATE TABLE publicacoes (rede TEXT, id_ext TEXT, post TEXT DEFAULT '', data TEXT, tipo TEXT DEFAULT '', texto TEXT DEFAULT '',
      url TEXT DEFAULT '', views REAL, alcance REAL, curtidas REAL, comentarios REAL, compartilhamentos REAL, salvamentos REAL,
      tempo_medio_s REAL, fonte TEXT DEFAULT '', atualizado_em TEXT, PRIMARY KEY (rede, id_ext));
    CREATE TABLE metricas_dia (rede TEXT, id_ext TEXT, dia TEXT, views REAL, alcance REAL, curtidas REAL, comentarios REAL,
      compartilhamentos REAL, salvamentos REAL, tempo_medio_s REAL, PRIMARY KEY (rede, id_ext, dia));
    CREATE TABLE perfil (rede TEXT, dia TEXT, seguidores REAL, alcance REAL, engajadas REAL, fonte TEXT DEFAULT '', PRIMARY KEY (rede, dia));
    CREATE TABLE comentarios (rede TEXT, id_ext TEXT, publicacao TEXT DEFAULT '', autor TEXT DEFAULT '', texto TEXT DEFAULT '', data TEXT,
      categoria TEXT DEFAULT '', estado TEXT DEFAULT 'novo', resposta TEXT DEFAULT '', respondido_em TEXT DEFAULT '', fonte TEXT DEFAULT '',
      PRIMARY KEY (rede, id_ext));
    CREATE TABLE envios (post TEXT, rede TEXT, estado TEXT, quando TEXT, via TEXT DEFAULT '', id_ext TEXT DEFAULT '', url TEXT DEFAULT '',
      erro TEXT DEFAULT '', tentativas INTEGER DEFAULT 0, atualizado_em TEXT, PRIMARY KEY (post, rede));
    CREATE TABLE avaliacoes (rede TEXT, id_ext TEXT, dia TEXT, multiplicador REAL, veredito TEXT, PRIMARY KEY (rede, id_ext));
    CREATE TABLE sincronizacoes (provedor TEXT, quando TEXT, ok INTEGER, mensagem TEXT, novos INTEGER DEFAULT 0);
    """,
}


def banco(caminho: Path | None = None) -> sqlite3.Connection:
    """Abre o banco local (estado/ciello.db) já na versão mais nova."""
    con = sqlite3.connect(caminho or estado("ciello.db"))
    con.row_factory = sqlite3.Row
    versao = con.execute("PRAGMA user_version").fetchone()[0]
    for v in sorted(MIGRACOES):
        if v > versao:
            con.executescript(MIGRACOES[v])
            con.execute(f"PRAGMA user_version = {v}")
    con.commit()
    return con
