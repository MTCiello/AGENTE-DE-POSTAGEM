"""WebSocket mínimo (RFC 6455) do lado do servidor, sobre o socket que o http.server já aceitou."""
import base64
import hashlib
import json
import socket
import struct
import threading

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
TEXTO, BINARIO, FECHAR, PING, PONG, CONTINUA = 0x1, 0x2, 0x8, 0x9, 0xA, 0x0
MAX_MENSAGEM = 16 * 1024 * 1024  # a tela só manda mensagens pequenas; o layout é a maior


def aceitar(handler):
    """Responde o pedido de upgrade do BaseHTTPRequestHandler e devolve a Conexao (ou None se não for WebSocket)."""
    chave = handler.headers.get("Sec-WebSocket-Key")
    if (handler.headers.get("Upgrade") or "").lower() != "websocket" or not chave:
        return None
    aceite = base64.b64encode(hashlib.sha1((chave + GUID).encode()).digest()).decode()
    handler.send_response(101, "Switching Protocols")
    handler.send_header("Upgrade", "websocket")
    handler.send_header("Connection", "Upgrade")
    handler.send_header("Sec-WebSocket-Accept", aceite)
    handler.end_headers()
    handler.wfile.flush()
    handler.close_connection = True
    return Conexao(handler.connection, handler.rfile)


class Conexao:
    def __init__(self, sock, leitor):
        self.sock, self.leitor = sock, leitor
        self.trava = threading.Lock()
        self.aberta = True
        sock.settimeout(None)

    def _ler(self, n):
        dados = self.leitor.read(n)
        if not dados or len(dados) < n:
            raise ConnectionError("fechou")
        return dados

    def _quadro(self):
        b1, b2 = self._ler(2)
        fim, op, mascara, tam = b1 & 0x80, b1 & 0x0F, b2 & 0x80, b2 & 0x7F
        if tam == 126:
            tam = struct.unpack(">H", self._ler(2))[0]
        elif tam == 127:
            tam = struct.unpack(">Q", self._ler(8))[0]
        if tam > MAX_MENSAGEM:
            raise ConnectionError("mensagem grande demais")
        chave = self._ler(4) if mascara else None
        corpo = bytearray(self._ler(tam)) if tam else bytearray()
        if chave:
            for i in range(len(corpo)):
                corpo[i] ^= chave[i % 4]
        return bool(fim), op, bytes(corpo)

    def receber(self):
        """Próxima mensagem de texto (str), ou None quando a conexão fecha."""
        partes, tipo = [], None
        try:
            while True:
                fim, op, corpo = self._quadro()
                if op == FECHAR:
                    self._enviar_quadro(FECHAR, corpo[:2])
                    return None
                if op == PING:
                    self._enviar_quadro(PONG, corpo)
                    continue
                if op == PONG:
                    continue
                if op in (TEXTO, BINARIO):
                    tipo, partes = op, [corpo]
                elif op == CONTINUA:
                    partes.append(corpo)
                if sum(map(len, partes)) > MAX_MENSAGEM:
                    raise ConnectionError("mensagem grande demais")
                if fim and tipo is not None:
                    dados = b"".join(partes)
                    if tipo == TEXTO:
                        return dados.decode("utf-8", "replace")
                    partes, tipo = [], None
        except (OSError, ConnectionError, ValueError):
            self.fechar()
            return None

    def _enviar_quadro(self, op, corpo: bytes):
        tam = len(corpo)
        if tam < 126:
            cab = struct.pack(">BB", 0x80 | op, tam)
        elif tam < 65536:
            cab = struct.pack(">BBH", 0x80 | op, 126, tam)
        else:
            cab = struct.pack(">BBQ", 0x80 | op, 127, tam)
        with self.trava:
            self.sock.sendall(cab + corpo)

    def enviar(self, mensagem: dict):
        if not self.aberta:
            return False
        try:
            self._enviar_quadro(TEXTO, json.dumps(mensagem, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
            return True
        except OSError:
            self.fechar()
            return False

    def fechar(self, codigo=None):
        if not self.aberta:
            return
        self.aberta = False
        try:
            if codigo:
                self._enviar_quadro(FECHAR, struct.pack(">H", codigo))
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
