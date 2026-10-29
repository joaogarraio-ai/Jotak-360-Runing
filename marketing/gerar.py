"""Gera os cards (PNG) e vídeos (MP4) de redes sociais da Jotak Impressos.

Uso:  python3 marketing/gerar.py
Saída: marketing/cards/*.png (1080x1350)  e  marketing/videos/*.mp4 (1080x1920)

Edite CONTACTO e CIDADE abaixo e volte a correr o script.
"""
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

CONTACTO = "WhatsApp: (00) 00000-0000"   # <- troque pelo seu contacto
CIDADE = "Sua cidade"                    # <- troque pela sua cidade
MARCA = "JOTAK"
SUB = "IMPRESSOS"

FONTS = "/usr/share/fonts/opentype/inter/Inter-"
BG = (11, 11, 18)
C, M, Y = (0, 183, 235), (236, 0, 140), (255, 230, 0)
WHITE, GREY = (255, 255, 255), (160, 165, 180)

AQUI = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(AQUI, "cards")
VIDEOS = os.path.join(AQUI, "videos")


def font(peso, tam):
    return ImageFont.truetype(f"{FONTS}{peso}.otf", int(tam))


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def seg(t, ini, dur=0.5):
    """Progresso 0..1 (suavizado) de uma animação que começa em `ini`."""
    return ease((t - ini) / dur)


def mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def fundo(w, h):
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img, "RGBA")
    # manchas de cor CMYK desfocadas à mão (círculos translúcidos)
    for cx, cy, r, cor in ((0.1, 0.05, 0.55, C), (0.95, 0.4, 0.5, M), (0.2, 1.0, 0.6, Y)):
        for i in range(12):
            rr = int(r * w * (1 - i / 12))
            d.ellipse((cx * w - rr, cy * h - rr, cx * w + rr, cy * h + rr), fill=cor + (7,))
    return img


def texto(d, xy, s, f, cor=WHITE, anchor="mm", alpha=1.0, sombra=False):
    if alpha <= 0:
        return
    cor = mix(BG, cor, alpha) if alpha < 1 else cor
    if sombra:
        d.text((xy[0] + 4, xy[1] + 6), s, font=f, fill=(0, 0, 0), anchor=anchor)
    d.text(xy, s, font=f, fill=cor, anchor=anchor)


def ajustar(d, s, peso, tam, larg):
    while d.textlength(s, font=font(peso, tam)) > larg:
        tam -= 2
    return font(peso, tam)


def logo(d, cx, cy, esc=1.0, alpha=1.0):
    texto(d, (cx, cy), MARCA, font("Black", 110 * esc), WHITE, alpha=alpha)
    texto(d, (cx, cy + 82 * esc), SUB, font("Bold", 38 * esc), GREY, alpha=alpha)
    for i, cor in enumerate((C, M, Y, (30, 30, 30))):
        x = cx + (i - 1.5) * 44 * esc
        y = cy + 135 * esc
        r = 14 * esc
        d.ellipse((x - r, y - r, x + r, y + r), fill=mix(BG, cor, alpha), outline=(90, 90, 100) if i == 3 else None)


def botao(d, cx, cy, s, larg, cor=Y, alpha=1.0, tam=44):
    h = tam * 2
    d.rounded_rectangle((cx - larg / 2, cy - h / 2, cx + larg / 2, cy + h / 2), radius=h / 2, fill=mix(BG, cor, alpha))
    texto(d, (cx, cy), s, font("ExtraBold", tam), (20, 20, 20), alpha=alpha)


def barras_cmyk(d, x, y, w, h, prog=1.0):
    seg_w = w / 4
    for i, cor in enumerate((C, M, Y, (25, 25, 30))):
        d.rectangle((x + i * seg_w, y, x + i * seg_w + seg_w * prog, y + h), fill=cor)


# ───────────────────────── CARDS 1080x1350 ─────────────────────────

W, H = 1080, 1350


def card_base(titulo_linhas, destaque, cor, extra=None, cta="Peça o seu orçamento grátis"):
    img = fundo(W, H)
    d = ImageDraw.Draw(img)
    barras_cmyk(d, 0, 0, W, 18)
    logo(d, W / 2, 150, 0.8)
    y = 430
    for linha in titulo_linhas:
        f = ajustar(d, linha, "Black", 120, W - 140)
        texto(d, (W / 2, y), linha, f, WHITE, sombra=True)
        y += 130
    f = ajustar(d, destaque, "Black", 130, W - 240)
    d.rounded_rectangle((70, y - 20, W - 70, y + 150), radius=30, fill=cor)
    texto(d, (W / 2, y + 65), destaque, f, (15, 15, 20) if cor in (Y, C) else WHITE)
    y += 225
    if extra:
        for e in extra:
            texto(d, (W / 2, y), e, font("SemiBold", 46), GREY)
            y += 62
    botao(d, W / 2, 1175, cta, 880)
    texto(d, (W / 2, 1265), f"{CONTACTO}  |  {CIDADE}", font("SemiBold", 36), GREY)
    barras_cmyk(d, 0, H - 18, W, 18)
    return img


def gerar_cards():
    os.makedirs(CARDS, exist_ok=True)
    defs = {
        "01_cartoes_de_visita": (["CARTÕES", "DE VISITA"], "QUE IMPRESSIONAM", C,
                                 ["Papel premium, acabamento perfeito", "Entrega rápida"], "Peça o seu orçamento grátis"),
        "02_lonas_e_banners": (["LONAS E", "BANNERS"], "A SUA FACHADA EM DESTAQUE", M,
                               ["Alta resolução, cores vivas", "Resistentes ao sol e à chuva"], "Peça o seu orçamento grátis"),
        "03_tshirts_e_brindes": (["T-SHIRTS E", "BRINDES"], "COM O SEU LOGO", Y,
                                 ["Para a sua equipa, evento ou negócio", "Pedidos a partir de 1 unidade"], "Peça o seu orçamento grátis"),
        "04_autocolantes": (["AUTOCOLANTES", "E ETIQUETAS"], "SOB MEDIDA", C,
                            ["Qualquer forma, qualquer tamanho", "Ideais para embalagens e viaturas"], "Peça o seu orçamento grátis"),
        "05_flyers_e_catalogos": (["FLYERS E", "CATÁLOGOS"], "DIVULGUE O SEU NEGÓCIO", M,
                                  ["Do design à impressão", "Preços especiais para quantidades"], "Peça o seu orçamento grátis"),
        "06_sorteio": (["SORTEIO", "100 CARTÕES"], "GRÁTIS!", Y,
                       ["1. Siga as nossas 3 páginas", "2. Curta este post", "3. Marque 2 amigos"], "Participe agora"),
        "07_orcamento_gratis": (["SEU PROJETO", "IMPRESSO"], "ORÇAMENTO GRÁTIS", M,
                                ["Envie a sua ideia e respondemos já", "Atendimento rápido"], "Fale connosco"),
    }
    for nome, (linhas, dest, cor, extra, cta) in defs.items():
        card_base(linhas, dest, cor, extra, cta).save(os.path.join(CARDS, nome + ".png"))

    # card dica: 3 erros
    img = fundo(W, H)
    d = ImageDraw.Draw(img)
    barras_cmyk(d, 0, 0, W, 18)
    logo(d, W / 2, 150, 0.8)
    texto(d, (W / 2, 420), "3 ERROS AO ENVIAR", font("Black", 84), WHITE)
    texto(d, (W / 2, 515), "O FICHEIRO PARA IMPRESSÃO", font("Black", 62), Y)
    y = 660
    for n, (t, cor) in enumerate((("Resolução baixa (use 300 dpi)", C),
                                  ("Sem sangria (3 mm de margem)", M),
                                  ("Cores em RGB em vez de CMYK", Y)), 1):
        d.rounded_rectangle((70, y - 60, W - 70, y + 60), radius=30, fill=(28, 28, 40))
        d.ellipse((95, y - 45, 185, y + 45), fill=cor)
        texto(d, (140, y), str(n), font("Black", 60), (15, 15, 20))
        texto(d, (215, y), t, ajustar(d, t, "Bold", 44, 780), WHITE, anchor="lm")
        y += 150
    texto(d, (W / 2, 1100), "Guarde este post para depois!", font("SemiBold", 44), GREY)
    botao(d, W / 2, 1190, "Dúvidas? Fale connosco", 760, tam=40)
    texto(d, (W / 2, 1290), f"{CONTACTO}  |  {CIDADE}", font("SemiBold", 34), GREY)
    barras_cmyk(d, 0, H - 18, W, 18)
    img.save(os.path.join(CARDS, "08_dica_3_erros.png"))


# ───────────────────────── VÍDEOS 1080x1920 ─────────────────────────

VW, VH, FPS = 1080, 1920, 30


def exportar_video(nome, duracao, fn_frame):
    os.makedirs(VIDEOS, exist_ok=True)
    saida = os.path.join(VIDEOS, nome + ".mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
           "-t", str(duracao), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
           "-c:a", "aac", "-shortest", "-movflags", "+faststart", saida]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(duracao * FPS)):
        p.stdin.write(fn_frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()


def cena_base(t):
    img = fundo(VW, VH)
    d = ImageDraw.Draw(img)
    # barra CMYK a deslizar no topo
    barras_cmyk(d, 0, 0, VW, 20, seg(t, 0.0, 0.8))
    return img, d


def final_cta(d, t, ini, texto_cta="Peça o seu orçamento grátis"):
    k = seg(t, ini, 0.5)
    logo(d, VW / 2, 760, 1.5, k)
    botao(d, VW / 2, 1150, texto_cta, 900, alpha=k, tam=46)
    texto(d, (VW / 2, 1290), CONTACTO, font("Bold", 48), WHITE, alpha=seg(t, ini + 0.3, 0.5))
    texto(d, (VW / 2, 1360), CIDADE, font("SemiBold", 40), GREY, alpha=seg(t, ini + 0.4, 0.5))
    texto(d, (VW / 2, 1500), "Siga-nos: Instagram | TikTok | Facebook", font("SemiBold", 38), GREY,
          alpha=seg(t, ini + 0.6, 0.5))


def poster(w, h):
    p = Image.new("RGB", (w, h), (250, 250, 245))
    d = ImageDraw.Draw(p)
    d.rectangle((0, 0, w, h * 0.34), fill=M)
    d.ellipse((w * 0.55, -h * 0.05, w * 1.1, h * 0.28), fill=Y)
    d.ellipse((-w * 0.1, h * 0.15, w * 0.4, h * 0.45), fill=C)
    texto(d, (w / 2, h * 0.52), "A SUA MARCA", ajustar(d, "A SUA MARCA", "Black", 110, w - 80), (20, 20, 25))
    texto(d, (w / 2, h * 0.62), "EM DESTAQUE", ajustar(d, "EM DESTAQUE", "Black", 110, w - 80), M)
    barras_cmyk(d, 60, h * 0.72, w - 120, 36)
    texto(d, (w / 2, h * 0.84), "Impressão de alta qualidade", font("SemiBold", 40), (70, 70, 80))
    texto(d, (w / 2, h * 0.92), MARCA + " " + SUB, font("ExtraBold", 36), (20, 20, 25))
    return p


POSTER = None


def video_satisfying(t):
    global POSTER
    pw, ph = 760, 1080
    if POSTER is None:
        POSTER = poster(pw, ph)
    img, d = cena_base(t)
    texto(d, (VW / 2, 200), "ISTO NUNCA CANSA", font("Black", 90), WHITE, alpha=seg(t, 0.2))
    x0, y0 = (VW - pw) // 2, 330
    # sombra e papel
    d.rectangle((x0 + 14, y0 + 14, x0 + pw + 14, y0 + ph + 14), fill=(0, 0, 0))
    d.rectangle((x0, y0, x0 + pw, y0 + ph), fill=(235, 235, 230))
    prog = seg(t, 1.0, 4.5) if t < 5.5 else 1.0
    corte = int(ph * prog)
    if corte > 0:
        img.paste(POSTER.crop((0, 0, pw, corte)), (x0, y0))
    if prog < 1.0:
        yb = y0 + corte
        d.rectangle((x0 - 50, yb - 8, x0 + pw + 50, yb + 8), fill=C)
        d.rectangle((x0 - 50, yb - 3, x0 + pw + 50, yb + 3), fill=WHITE)
    texto(d, (VW / 2, 1520), "Impressão em tempo real", font("SemiBold", 48), GREY,
          alpha=seg(t, 0.8) * (1 - seg(t, 6.6, 0.4)))
    if t > 6.5:
        # tudo sai, entra CTA
        fade = seg(t, 6.5, 0.5)
        ov = Image.new("RGB", (VW, VH), BG)
        img = Image.blend(img, ov, fade)
        d = ImageDraw.Draw(img)
        final_cta(d, t, 7.0)
    return img


def video_servicos(t):
    img, d = cena_base(t)
    logo(d, VW / 2, 230, 1.0, seg(t, 0.1))
    texto(d, (VW / 2, 520), "O QUE IMPRIMIMOS", font("Black", 76), Y, alpha=seg(t, 0.5))
    itens = ["Cartões de visita", "Lonas e banners", "Autocolantes", "T-shirts e brindes", "Flyers e catálogos"]
    cores = [C, M, Y, C, M]
    for i, (it, cor) in enumerate(zip(itens, cores)):
        k = seg(t, 1.2 + i * 0.9, 0.5)
        if k <= 0:
            continue
        y = 700 + i * 150
        dx = (1 - k) * 700
        d.rounded_rectangle((90 + dx, y - 55, VW - 90 + dx, y + 55), radius=28, fill=(28, 28, 40))
        d.ellipse((120 + dx, y - 30, 180 + dx, y + 30), fill=cor)
        texto(d, (215 + dx, y), it, font("Bold", 56), WHITE, anchor="lm")
    if t > 7.0:
        fade = seg(t, 7.0, 0.5)
        img = Image.blend(img, Image.new("RGB", (VW, VH), BG), fade)
        d = ImageDraw.Draw(img)
        final_cta(d, t, 7.5)
    return img


def video_sorteio(t):
    img, d = cena_base(t)
    pulso = 1 + 0.04 * math.sin(t * 6)
    texto(d, (VW / 2, 330), "SORTEIO", font("Black", 190 * pulso), Y, alpha=seg(t, 0.1), sombra=True)
    texto(d, (VW / 2, 510), "100 CARTÕES DE VISITA", ajustar(d, "100 CARTÕES DE VISITA", "Black", 84, 980),
          WHITE, alpha=seg(t, 0.5))
    texto(d, (VW / 2, 665), "GRÁTIS!", font("Black", 130), M, alpha=seg(t, 0.8))
    passos = ["Siga as 3 páginas da Jotak", "Curta este vídeo", "Marque 2 amigos nos comentários"]
    for i, p in enumerate(passos):
        k = seg(t, 1.8 + i * 1.0, 0.5)
        if k <= 0:
            continue
        y = 900 + i * 170
        dx = (1 - k) * 600
        d.rounded_rectangle((80 + dx, y - 65, VW - 80 + dx, y + 65), radius=32, fill=(28, 28, 40))
        d.ellipse((110 + dx, y - 45, 200 + dx, y + 45), fill=(C, M, Y)[i])
        texto(d, (155 + dx, y), str(i + 1), font("Black", 60), (15, 15, 20))
        texto(d, (240 + dx, y), p, ajustar(d, p, "Bold", 46, 750), WHITE, anchor="lm")
    if t > 7.0:
        fade = seg(t, 7.0, 0.5)
        img = Image.blend(img, Image.new("RGB", (VW, VH), BG), fade)
        d = ImageDraw.Draw(img)
        final_cta(d, t, 7.5, "Participe agora!")
    return img


def video_dica(t):
    img, d = cena_base(t)
    texto(d, (VW / 2, 260), "ESTÁ A ENVIAR O", font("Black", 84), WHITE, alpha=seg(t, 0.1))
    texto(d, (VW / 2, 360), "FICHEIRO ERRADO?", font("Black", 100), Y, alpha=seg(t, 0.4))
    erros = [("1", "Resolução baixa", "Use 300 dpi", C),
             ("2", "Sem sangria", "Deixe 3 mm de margem", M),
             ("3", "Cores em RGB", "Converta para CMYK", Y)]
    for i, (n, t1, t2, cor) in enumerate(erros):
        k = seg(t, 1.5 + i * 1.8, 0.5)
        if k <= 0:
            continue
        y = 620 + i * 300
        dx = (1 - k) * 800
        d.rounded_rectangle((70 + dx, y - 120, VW - 70 + dx, y + 120), radius=40, fill=(28, 28, 40))
        d.ellipse((100 + dx, y - 80, 260 + dx, y + 80), fill=cor)
        texto(d, (180 + dx, y), n, font("Black", 110), (15, 15, 20))
        texto(d, (310 + dx, y - 30), t1, ajustar(d, t1, "Black", 66, 690), WHITE, anchor="lm")
        texto(d, (310 + dx, y + 45), t2, font("SemiBold", 46), cor, anchor="lm")
    if t > 8.0:
        fade = seg(t, 8.0, 0.5)
        img = Image.blend(img, Image.new("RGB", (VW, VH), BG), fade)
        d = ImageDraw.Draw(img)
        final_cta(d, t, 8.5, "Dúvidas? Fale connosco")
    return img


def gerar_videos():
    exportar_video("01_satisfying_impressao", 11, video_satisfying)
    exportar_video("02_o_que_imprimimos", 11, video_servicos)
    exportar_video("03_sorteio_100_cartoes", 11, video_sorteio)
    exportar_video("04_dica_3_erros", 12, video_dica)


if __name__ == "__main__":
    gerar_cards()
    gerar_videos()
    print("Pronto:", CARDS, VIDEOS)
