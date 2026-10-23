"""python -m unittest discover central/testes  (gerenciador de atualizações: instalador/atualizacao.py)"""
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "instalador"))
import atualizacao  # noqa: E402


def pacote(arquivos, prefixo="MTCiello-AGENTE-DE-POSTAGEM-abc1234/"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(prefixo, "")
        for nome, conteudo in arquivos.items():
            z.writestr(prefixo + nome, conteudo)
    return buf.getvalue()


BASE = {"VERSION": "1.1.0\n", "central/escritorio/servidor.py": "print('novo')\n"}


class TesteVersoes(unittest.TestCase):
    def test_compara_numeros_e_nao_texto(self):
        self.assertTrue(atualizacao.mais_nova("v1.10.0", "1.9.9"))
        self.assertFalse(atualizacao.mais_nova("v1.0.0", "1.0.0"))
        self.assertFalse(atualizacao.mais_nova("1.0", "1.0.0"))
        self.assertEqual(atualizacao.numeros("v2.3.1-beta"), (2, 3, 1))

    def test_protegidos(self):
        for rel in (".venv/x", "estado/a.json", "comercial/leads.csv", "financeiro/clientes.json", "founder/plano.md",
                    "reels/node_modules/a.js", "midia/estudio/r.mp4"):
            self.assertTrue(atualizacao.protegido(rel), rel)
        for rel in ("central/sdr.py", "financeiro/categorias.json", "founder/idea.md", "comercial/icp.json", "VERSION"):
            self.assertFalse(atualizacao.protegido(rel), rel)


class TesteAplicar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        (self.raiz / "central" / "escritorio").mkdir(parents=True)
        (self.raiz / "VERSION").write_text("1.0.0\n")
        (self.raiz / "central" / "escritorio" / "servidor.py").write_text("print('velho')\n")
        (self.raiz / "central" / "antigo.py").write_text("x = 1\n")
        (self.raiz / "comercial").mkdir()
        (self.raiz / "comercial" / "leads.csv").write_text("nome,telefone\nfulano,123\n")
        atualizacao.anotar_instalados(self.raiz)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ler_pacote_tira_a_pasta_do_github(self):
        arquivos = atualizacao.ler_pacote(pacote(BASE))
        self.assertEqual(set(arquivos), set(BASE))

    def test_ler_pacote_recusa_zip_que_nao_e_o_ciello(self):
        with self.assertRaises(ValueError):
            atualizacao.ler_pacote(pacote({"README.md": "oi"}))

    def test_ler_pacote_ignora_caminho_que_sobe_pasta(self):
        arquivos = atualizacao.ler_pacote(pacote({**BASE, "../fora.txt": "x"}, prefixo=""))
        self.assertNotIn("../fora.txt", arquivos)

    def test_instala_sem_tocar_nos_dados_e_apaga_o_que_saiu(self):
        novo = {**BASE, "comercial/leads.csv": "invasor", "central/novo.py": "y = 2\n"}
        r = atualizacao.instalar_pacote({k: v.encode() for k, v in novo.items()}, self.raiz, avisar=lambda *_: None)
        self.assertEqual((self.raiz / "VERSION").read_text(), "1.1.0\n")
        self.assertTrue((self.raiz / "central" / "novo.py").exists())
        self.assertFalse((self.raiz / "central" / "antigo.py").exists())
        self.assertIn("fulano", (self.raiz / "comercial" / "leads.csv").read_text())
        self.assertEqual(r["guardados"], [])

    def test_arquivo_editado_vai_para_o_backup(self):
        (self.raiz / "central" / "antigo.py").write_text("x = 'mexi'\n")
        r = atualizacao.instalar_pacote({k: v.encode() for k, v in BASE.items()}, self.raiz, avisar=lambda *_: None)
        self.assertEqual(r["guardados"], ["central/antigo.py"])
        self.assertIn("mexi", (Path(r["backup"]) / "central" / "antigo.py").read_text())

    def test_aplicar_canal_estavel(self):
        info = {"canal": "estavel", "versao": "1.1.0", "nova": True, "pacote": "https://exemplo/zip"}
        with mock.patch.object(atualizacao, "pedir", return_value=pacote(BASE)), \
                mock.patch.object(atualizacao, "eh_git", return_value=False):
            r = atualizacao.aplicar(atualizacao.PADRAO, self.raiz, avisar=lambda *_: None, info=info)
        self.assertTrue(r["ok"])
        self.assertEqual(r["versao"], "1.1.0")
        self.assertFalse(atualizacao.estado(self.raiz)["ultima_consulta"]["nova"])


class TesteConsulta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        (self.raiz / "VERSION").write_text("1.0.0\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_release_nova(self):
        release = {"tag_name": "v1.2.0", "name": "Ciello OS 1.2.0", "body": "- novidade", "zipball_url": "z",
                   "html_url": "h", "assets": [{"name": "CielloOS-Setup-1.2.0.exe", "browser_download_url": "e"}]}
        with mock.patch.object(atualizacao, "pedir", return_value=json.dumps(release).encode()), \
                mock.patch.object(atualizacao, "eh_git", return_value=False):
            info = atualizacao.verificar(atualizacao.PADRAO, self.raiz)
        self.assertTrue(info["nova"])
        self.assertEqual((info["versao"], info["instalador"]), ("1.2.0", "e"))
        self.assertFalse(atualizacao.hora_de_verificar(atualizacao.PADRAO, self.raiz))

    def test_sem_internet_vira_mensagem(self):
        with mock.patch.object(atualizacao, "pedir", side_effect=OSError("sem rede")), \
                mock.patch.object(atualizacao, "eh_git", return_value=False):
            info = atualizacao.verificar(atualizacao.PADRAO, self.raiz)
        self.assertFalse(info["nova"])
        self.assertIn("sem rede", info["erro"])

    def test_intervalo(self):
        self.assertTrue(atualizacao.hora_de_verificar(atualizacao.PADRAO, self.raiz))
        atualizacao.salvar_estado(self.raiz, ultima_verificacao="2026-10-23T10:00:00")
        import time
        base = time.mktime(time.strptime("2026-10-23T10:00:00", "%Y-%m-%dT%H:%M:%S"))
        self.assertFalse(atualizacao.hora_de_verificar(atualizacao.PADRAO, self.raiz, agora=base + 3600))
        self.assertTrue(atualizacao.hora_de_verificar(atualizacao.PADRAO, self.raiz, agora=base + 13 * 3600))
        self.assertFalse(atualizacao.hora_de_verificar({**atualizacao.PADRAO, "verificar_ao_abrir": False}, self.raiz))


if __name__ == "__main__":
    unittest.main()
