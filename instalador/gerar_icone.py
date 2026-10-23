"""Gera o ícone do Ciello OS (logo da Ciello sobre o azul da marca) e as imagens do assistente de instalação.

    python instalador/gerar_icone.py

Saídas em instalador/marca/: ciello.ico (16 a 256 px), ciello-256.png, assistente.bmp (lateral do instalador)
e assistente-pequeno.bmp (canto do instalador). Rode de novo só se a logo mudar.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = Path(__file__).resolve().parent / "marca"
AZUL = (38, 58, 89)          # Azul profundo #263A59
AZUL_ESCURO = (24, 38, 60)
MARFIM = (248, 244, 232)
OURO = (224, 168, 28)
LOGO = RAIZ / "marca" / "logo-simbolo-marfim.png"
FONTE = RAIZ / "gerador" / "fonts"


def logo(largura):
    im = Image.open(LOGO).convert("RGBA")
    im = im.crop(im.getbbox())
    return im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)


def quadrado(lado):
    """Fundo azul arredondado com a nuvem marfim e o ponto dourado no centro."""
    escala = 4  # desenha grande e reduz: borda lisa
    g = lado * escala
    im = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, g - 1, g - 1), radius=round(g * 0.22), fill=AZUL)
    lg = logo(round(g * (0.74 if lado <= 24 else 0.66)))
    im.alpha_composite(lg, ((g - lg.width) // 2, (g - lg.height) // 2 + round(g * 0.02)))
    return im.resize((lado, lado), Image.LANCZOS)


def fonte(tam):
    p = FONTE / "oswald-latin-600-normal.woff"
    return ImageFont.truetype(str(p), tam) if p.exists() else ImageFont.load_default()


def lateral(larg=164, alt=314):
    """Faixa da esquerda das telas de boas-vindas e de conclusão (Inno Setup: WizardImageFile)."""
    im = Image.new("RGB", (larg, alt), AZUL)
    d = ImageDraw.Draw(im)
    for y in range(alt):  # degradê suave para o azul escuro embaixo
        t = y / alt
        d.line([(0, y), (larg, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(AZUL, AZUL_ESCURO)))
    lg = logo(112)
    im.paste(lg, ((larg - lg.width) // 2, 96), lg)
    f = fonte(26)
    texto = "CIELLO"
    w = d.textlength(texto, font=f)
    d.text(((larg - w) / 2, 172), texto, font=f, fill=MARFIM)
    f2 = fonte(13)
    sub = "O S"
    w2 = d.textlength(sub, font=f2)
    d.text(((larg - w2) / 2, 210), sub, font=f2, fill=OURO)
    return im


def main():
    SAIDA.mkdir(exist_ok=True)
    tamanhos = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    grande = quadrado(256)
    grande.save(SAIDA / "ciello-256.png")
    grande.save(SAIDA / "ciello.ico", sizes=[(t, t) for t in tamanhos],
                append_images=[quadrado(t) for t in tamanhos if t != 256])
    lateral().save(SAIDA / "assistente.bmp")
    pequeno = Image.new("RGB", (55, 55), (255, 255, 255))
    q = quadrado(55)
    pequeno.paste(q, (0, 0), q)
    pequeno.save(SAIDA / "assistente-pequeno.bmp")
    print("Ícone e imagens em", SAIDA)


if __name__ == "__main__":
    main()
