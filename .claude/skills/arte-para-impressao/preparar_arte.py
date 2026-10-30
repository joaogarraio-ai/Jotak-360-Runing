#!/usr/bin/env python3
"""Diagnostica e prepara arte de baixa resolução para impressão (Jotak Gráfica)."""
import argparse
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

Image.MAX_IMAGE_PIXELS = 600_000_000

# produto -> (DPI recomendado, DPI mínimo aceitável)
PRODUTOS = {
    "banner": (100, 50), "faixa": (100, 50), "lona": (100, 50),
    "adesivo": (200, 100), "placa": (150, 100),
    "cracha": (300, 200), "camiseta": (200, 150), "papelaria": (300, 200),
}


def dpi_efetivo(img, largura_cm, altura_cm):
    return min(img.width / (largura_cm / 2.54), img.height / (altura_cm / 2.54))


def veredito(dpi, minimo, recomendado):
    if dpi >= recomendado:
        return "OK"
    if dpi >= minimo:
        return "Aceitável (vai ampliar, risco leve de suavização)"
    if dpi >= minimo * 0.5:
        return "Baixo (ampliação grande, bordas e texto vão sofrer)"
    return "Crítico (refazer a arte ou pedir arquivo melhor)"


def reforcar_texto(img, fator):
    """Suaviza a escadinha dos pixels e restaura bordas nítidas (arte chapada)."""
    img = img.filter(ImageFilter.GaussianBlur(radius=max(0.6, fator * 0.45)))
    a = np.asarray(img).astype(np.float32) / 255.0
    a = np.clip((a - 0.5) * 2.2 + 0.5, 0, 1)  # curva S: afina a transição das bordas
    return Image.fromarray((a * 255).astype(np.uint8))


def com_sangria(img, mm, dpi):
    px = round(mm / 25.4 * dpi)
    return ImageOps.expand(img, 0) if px <= 0 else Image.fromarray(
        np.pad(np.asarray(img), ((px, px), (px, px), (0, 0)), mode="symmetric"))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("arquivo")
    p.add_argument("--largura-cm", type=float, required=True)
    p.add_argument("--altura-cm", type=float, required=True)
    p.add_argument("--produto", choices=PRODUTOS, default="banner")
    p.add_argument("--dpi", type=int, help="DPI alvo (padrão: recomendado do produto)")
    p.add_argument("--texto", action="store_true", help="reforça bordas de texto/logos")
    p.add_argument("--sangria-mm", type=float, default=0)
    p.add_argument("--cmyk", action="store_true")
    p.add_argument("--diagnostico", action="store_true", help="só analisa, não grava")
    p.add_argument("--saida", help=".pdf, .tif ou .png")
    a = p.parse_args()

    img = Image.open(a.arquivo)
    if img.mode in ("RGBA", "LA", "P"):
        fundo = Image.new("RGB", img.size, "white")
        fundo.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = fundo
    img = img.convert("RGB")

    recomendado, minimo = PRODUTOS[a.produto]
    dpi_alvo = a.dpi or recomendado
    antes = dpi_efetivo(img, a.largura_cm, a.altura_cm)
    print(f"Arquivo: {img.width}x{img.height}px | Tamanho final: {a.largura_cm}x{a.altura_cm} cm ({a.produto})")
    print(f"DPI efetivo atual: {antes:.0f} (recomendado {recomendado}, mínimo {minimo})")
    print(f"Veredito: {veredito(antes, minimo, recomendado)}")
    if a.diagnostico:
        return 0
    if not a.saida:
        p.error("informe --saida (ou use --diagnostico)")

    alvo = (round(a.largura_cm / 2.54 * dpi_alvo), round(a.altura_cm / 2.54 * dpi_alvo))
    prop_orig, prop_alvo = img.width / img.height, alvo[0] / alvo[1]
    if abs(prop_orig - prop_alvo) > 0.02:
        print(f"AVISO: proporção da arte ({prop_orig:.2f}) difere do tamanho final ({prop_alvo:.2f}); "
              "será recortada ao centro.", file=sys.stderr)
    fator = max(alvo[0] / img.width, alvo[1] / img.height)
    if fator > 1:
        # amplia em duas etapas p/ reduzir artefatos; Lanczos preserva melhor as bordas
        if fator > 2:
            img = img.resize((round(img.width * 2), round(img.height * 2)), Image.LANCZOS)
            fator /= 2
        img = img.resize((round(img.width * fator), round(img.height * fator)), Image.LANCZOS)
    img = ImageOps.fit(img, alvo, Image.LANCZOS)
    if a.texto and antes < dpi_alvo:
        img = reforcar_texto(img, max(1.0, dpi_alvo / max(antes, 1)))
    elif not a.texto:
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    if a.sangria_mm:
        img = com_sangria(img, a.sangria_mm, dpi_alvo)
    if a.cmyk:
        img = img.convert("CMYK")

    ext = a.saida.lower().rsplit(".", 1)[-1]
    kw = {"resolution": dpi_alvo}
    if ext == "pdf":
        img.save(a.saida, "PDF", **kw)
    elif ext in ("tif", "tiff"):
        img.save(a.saida, compression="tiff_lzw", dpi=(dpi_alvo, dpi_alvo))
    else:
        if a.cmyk:
            p.error("PNG não suporta CMYK; use .tif ou .pdf")
        img.save(a.saida, dpi=(dpi_alvo, dpi_alvo))
    print(f"Gerado: {a.saida} ({img.width}x{img.height}px a {dpi_alvo} DPI)")
    print("Lembrete: texto importante deve ser refeito em vetor; ampliar não cria detalhe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
