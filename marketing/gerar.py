"""Gera os cards (PNG) e vídeos (MP4) de redes sociais da Jotak Impressos.

Uso:  python3 marketing/gerar.py
Saída: marketing/cards/*.png (1080x1350)  e  marketing/videos/*.mp4 (1080x1920)

Edite CONTACTO, ENDERECO e os perfis abaixo e volte a correr o script.
"""
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

CONTACTO = "WhatsApp: (75) 98106-5204"
ENDERECO = "Praça Araújo Pinho, 45"
INSTAGRAM = "@jotakimpressosgrafica"
TIKTOK = "@jotakimpressos"
MARCA = "JOTA K"
SUB = "IMPRESSOS"

FONTS = "/usr/share/fonts/opentype/inter/Inter-"
BG = (11, 11, 18)
# Paleta da marca Jotak: vermelho, cinza, branco e preto
C, M, Y = (240, 16, 16), (105, 106, 108), (245, 245, 245)   # vermelho, cinza, branco
RED_ESCURO = (150, 0, 0)
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_branco.png")
_LOGO = None
WHITE, GREY = (255, 255, 255), (160, 165, 180)

AQUI = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(AQUI, "cards")
VIDEOS = os.path.join(AQUI, "videos")
STORIES = os.path.join(AQUI, "stories")


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
    for cx, cy, r, cor in ((0.1, 0.05, 0.55, RED_ESCURO), (0.95, 0.4, 0.5, (70, 70, 78)), (0.2, 1.0, 0.6, C)):
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


def contraste(cor):
    return (15, 15, 20) if cor == Y else WHITE


def logo(d, cx, cy, esc=1.0, alpha=1.0):
    """Cola o logótipo real da Jotak (PNG transparente) centrado perto de (cx, cy)."""
    global _LOGO
    if _LOGO is None:
        _LOGO = Image.open(LOGO_PATH).convert("RGBA")
    larg = int(620 * esc)
    im = _LOGO.resize((larg, int(_LOGO.height * larg / _LOGO.width)), Image.LANCZOS)
    if alpha < 1:
        im.putalpha(im.split()[3].point(lambda v: int(v * max(0.0, alpha))))
    d._image.paste(im, (int(cx - larg / 2), int(cy + 45 * esc - im.height / 2)), im)


def botao(d, cx, cy, s, larg, cor=Y, alpha=1.0, tam=44):
    h = tam * 2
    d.rounded_rectangle((cx - larg / 2, cy - h / 2, cx + larg / 2, cy + h / 2), radius=h / 2, fill=mix(BG, cor, alpha))
    texto(d, (cx, cy), s, font("ExtraBold", tam), (20, 20, 20), alpha=alpha)


def barras_cmyk(d, x, y, w, h, prog=1.0):
    seg_w = w / 4
    for i, cor in enumerate((C, RED_ESCURO, M, (25, 25, 30))):
        d.rectangle((x + i * seg_w, y, x + i * seg_w + seg_w * prog, y + h), fill=cor)


# ───────────────────────── CARDS 1080x1350 ─────────────────────────

W, H = 1080, 1350


def card_base(titulo_linhas, destaque, cor, extra=None, cta="Peça seu orçamento grátis", h=H):
    dy = (h - H) // 2          # no Story (1920) o conteúdo fica nas zonas seguras
    img = fundo(W, h)
    d = ImageDraw.Draw(img)
    barras_cmyk(d, 0, 0, W, 18)
    logo(d, W / 2, 150 + dy, 0.8)
    y = 430 + dy
    for linha in titulo_linhas:
        f = ajustar(d, linha, "Black", 120, W - 140)
        texto(d, (W / 2, y), linha, f, WHITE, sombra=True)
        y += 130
    f = ajustar(d, destaque, "Black", 130, W - 240)
    d.rounded_rectangle((70, y - 20, W - 70, y + 150), radius=30, fill=cor)
    texto(d, (W / 2, y + 65), destaque, f, contraste(cor))
    y += 225
    if extra:
        for e in extra:
            texto(d, (W / 2, y), e, font("SemiBold", 46), GREY)
            y += 62
    botao(d, W / 2, 1175 + dy, cta, 880)
    texto(d, (W / 2, 1255 + dy), f"{CONTACTO}  |  {ENDERECO}", ajustar(d, f"{CONTACTO}  |  {ENDERECO}", "SemiBold", 34, 980), GREY)
    texto(d, (W / 2, 1300 + dy), f"Instagram {INSTAGRAM}  |  TikTok {TIKTOK}", ajustar(d, f"Instagram {INSTAGRAM}  |  TikTok {TIKTOK}", "SemiBold", 28, 980), GREY)
    barras_cmyk(d, 0, h - 18, W, 18)
    return img


def card_dica(h=H):
    dy = (h - H) // 2
    img = fundo(W, h)
    d = ImageDraw.Draw(img)
    barras_cmyk(d, 0, 0, W, 18)
    logo(d, W / 2, 150 + dy, 0.8)
    texto(d, (W / 2, 420 + dy), "3 ERROS AO ENVIAR", font("Black", 84), WHITE)
    texto(d, (W / 2, 515 + dy), "O ARQUIVO PARA IMPRESSÃO", font("Black", 62), C)
    y = 660 + dy
    for n, (t, cor) in enumerate((("Resolução baixa (use 300 dpi)", C),
                                  ("Sem sangria (3 mm de margem)", M),
                                  ("Cores em RGB em vez de CMYK", Y)), 1):
        d.rounded_rectangle((70, y - 60, W - 70, y + 60), radius=30, fill=(28, 28, 40))
        d.ellipse((95, y - 45, 185, y + 45), fill=cor)
        texto(d, (140, y), str(n), font("Black", 60), contraste(cor))
        texto(d, (215, y), t, ajustar(d, t, "Bold", 44, 780), WHITE, anchor="lm")
        y += 150
    texto(d, (W / 2, 1100 + dy), "Guarde este post para depois!", font("SemiBold", 44), GREY)
    botao(d, W / 2, 1190 + dy, "Dúvidas? Fale conosco", 760, tam=40)
    texto(d, (W / 2, 1260 + dy), f"{CONTACTO}  |  {ENDERECO}", ajustar(d, f"{CONTACTO}  |  {ENDERECO}", "SemiBold", 34, 980), GREY)
    texto(d, (W / 2, 1305 + dy), f"Instagram {INSTAGRAM}  |  TikTok {TIKTOK}", ajustar(d, f"Instagram {INSTAGRAM}  |  TikTok {TIKTOK}", "SemiBold", 28, 980), GREY)
    barras_cmyk(d, 0, h - 18, W, 18)
    return img


def gerar_cards():
    os.makedirs(CARDS, exist_ok=True)
    os.makedirs(STORIES, exist_ok=True)
    defs = {
        "01_cartoes_de_visita": (["CARTÕES", "DE VISITA"], "QUE IMPRESSIONAM", C,
                                 ["Papel premium, acabamento perfeito", "Entrega rápida"], "Peça seu orçamento grátis"),
        "02_lonas_e_banners": (["LONAS E", "BANNERS"], "SUA FACHADA EM DESTAQUE", M,
                               ["Alta resolução, cores vivas", "Resistentes ao sol e à chuva"], "Peça seu orçamento grátis"),
        "03_tshirts_e_brindes": (["CAMISETAS E", "BRINDES"], "COM A SUA LOGO", Y,
                                 ["Para a sua equipe, evento ou negócio", "Pedidos a partir de 1 unidade"], "Peça seu orçamento grátis"),
        "04_autocolantes": (["ADESIVOS", "E ETIQUETAS"], "SOB MEDIDA", C,
                            ["Qualquer forma, qualquer tamanho", "Ideais para embalagens e viaturas"], "Peça seu orçamento grátis"),
        "05_flyers_e_catalogos": (["FLYERS E", "CATÁLOGOS"], "DIVULGUE O SEU NEGÓCIO", M,
                                  ["Do design à impressão", "Preços especiais para quantidades"], "Peça seu orçamento grátis"),
        "06_sorteio": (["SORTEIO", "100 CARTÕES"], "GRÁTIS!", Y,
                       ["1. Siga as nossas 3 páginas", "2. Curta este post", "3. Marque 2 amigos"], "Participe agora"),
        "07_orcamento_gratis": (["SEU PROJETO", "IMPRESSO"], "ORÇAMENTO GRÁTIS", M,
                                ["Envie sua ideia e respondemos já", "Atendimento rápido"], "Fale conosco"),
    }
    for nome, (linhas, dest, cor, extra, cta) in defs.items():
        card_base(linhas, dest, cor, extra, cta).save(os.path.join(CARDS, nome + ".png"))
        card_base(linhas, dest, cor, extra, cta, h=1920).save(os.path.join(STORIES, nome + "_story.png"))
    card_dica().save(os.path.join(CARDS, "08_dica_3_erros.png"))
    card_dica(1920).save(os.path.join(STORIES, "08_dica_3_erros_story.png"))


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


def final_cta(d, t, ini, texto_cta="Peça seu orçamento grátis"):
    k = seg(t, ini, 0.5)
    logo(d, VW / 2, 760, 1.5, k)
    botao(d, VW / 2, 1150, texto_cta, 900, alpha=k, tam=46)
    texto(d, (VW / 2, 1290), CONTACTO, font("Bold", 48), WHITE, alpha=seg(t, ini + 0.3, 0.5))
    texto(d, (VW / 2, 1360), "Praça Araújo Pinho, nº 45", font("SemiBold", 42), GREY, alpha=seg(t, ini + 0.4, 0.5))
    texto(d, (VW / 2, 1490), "Siga-nos", font("Bold", 40), WHITE, alpha=seg(t, ini + 0.6, 0.5))
    texto(d, (VW / 2, 1560), f"Instagram {INSTAGRAM}", font("SemiBold", 38), GREY, alpha=seg(t, ini + 0.7, 0.5))
    texto(d, (VW / 2, 1620), f"TikTok {TIKTOK}", font("SemiBold", 38), GREY, alpha=seg(t, ini + 0.8, 0.5))


def poster(w, h):
    p = Image.new("RGB", (w, h), (250, 250, 245))
    d = ImageDraw.Draw(p)
    d.rectangle((0, 0, w, h * 0.34), fill=C)
    d.ellipse((w * 0.55, -h * 0.05, w * 1.1, h * 0.28), fill=RED_ESCURO)
    d.ellipse((-w * 0.1, h * 0.15, w * 0.4, h * 0.45), fill=(40, 40, 46))
    texto(d, (w / 2, h * 0.52), "SUA MARCA", ajustar(d, "SUA MARCA", "Black", 110, w - 80), (20, 20, 25))
    texto(d, (w / 2, h * 0.62), "EM DESTAQUE", ajustar(d, "EM DESTAQUE", "Black", 110, w - 80), C)
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
    texto(d, (VW / 2, 520), "O QUE IMPRIMIMOS", font("Black", 76), C, alpha=seg(t, 0.5))
    itens = ["Cartões de visita", "Lonas e banners", "Adesivos", "Camisetas e brindes", "Flyers e catálogos"]
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
    texto(d, (VW / 2, 330), "SORTEIO", font("Black", 190 * pulso), C, alpha=seg(t, 0.1), sombra=True)
    texto(d, (VW / 2, 510), "100 CARTÕES DE VISITA", ajustar(d, "100 CARTÕES DE VISITA", "Black", 84, 980),
          WHITE, alpha=seg(t, 0.5))
    texto(d, (VW / 2, 665), "GRÁTIS!", font("Black", 130), C, alpha=seg(t, 0.8))
    passos = ["Siga as 3 páginas da Jotak", "Curta este vídeo", "Marque 2 amigos nos comentários"]
    for i, p in enumerate(passos):
        k = seg(t, 1.8 + i * 1.0, 0.5)
        if k <= 0:
            continue
        y = 900 + i * 170
        dx = (1 - k) * 600
        d.rounded_rectangle((80 + dx, y - 65, VW - 80 + dx, y + 65), radius=32, fill=(28, 28, 40))
        d.ellipse((110 + dx, y - 45, 200 + dx, y + 45), fill=(C, M, Y)[i])
        texto(d, (155 + dx, y), str(i + 1), font("Black", 60), contraste((C, M, Y)[i]))
        texto(d, (240 + dx, y), p, ajustar(d, p, "Bold", 46, 750), WHITE, anchor="lm")
    if t > 7.0:
        fade = seg(t, 7.0, 0.5)
        img = Image.blend(img, Image.new("RGB", (VW, VH), BG), fade)
        d = ImageDraw.Draw(img)
        final_cta(d, t, 7.5, "Participe agora!")
    return img


def video_dica(t):
    img, d = cena_base(t)
    texto(d, (VW / 2, 260), "ESTÁ ENVIANDO O", font("Black", 84), WHITE, alpha=seg(t, 0.1))
    texto(d, (VW / 2, 360), "ARQUIVO ERRADO?", font("Black", 100), C, alpha=seg(t, 0.4))
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
        texto(d, (180 + dx, y), n, font("Black", 110), contraste(cor))
        texto(d, (310 + dx, y - 30), t1, ajustar(d, t1, "Black", 66, 690), WHITE, anchor="lm")
        texto(d, (310 + dx, y + 45), t2, font("SemiBold", 46), cor, anchor="lm")
    if t > 8.0:
        fade = seg(t, 8.0, 0.5)
        img = Image.blend(img, Image.new("RGB", (VW, VH), BG), fade)
        d = ImageDraw.Draw(img)
        final_cta(d, t, 8.5, "Dúvidas? Fale conosco")
    return img



def sair_para_cta(img, t, ini, texto_cta):
    """Esmaece a cena atual e mostra o fecho com o contacto."""
    img = Image.blend(img, Image.new("RGB", (VW, VH), BG), seg(t, ini, 0.5))
    d = ImageDraw.Draw(img)
    final_cta(d, t, ini + 0.5, texto_cta)
    return img


def cartao_visita(w=640, h=360, cor=C, nome=MARCA):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=26, fill=(248, 248, 243))
    d.rounded_rectangle((0, 0, w * 0.32, h - 1), radius=26, fill=cor)
    d.rectangle((w * 0.2, 0, w * 0.32, h - 1), fill=cor)
    texto(d, (w * 0.16, h * 0.5), "K", font("Black", 150), WHITE)
    texto(d, (w * 0.40, h * 0.34), nome, font("Black", 54), (20, 20, 25), anchor="lm")
    texto(d, (w * 0.40, h * 0.50), "IMPRESSOS & COM. VISUAL", font("Bold", 24), (110, 110, 120), anchor="lm")
    d.rectangle((w * 0.40, h * 0.62, w * 0.92, h * 0.635), fill=(200, 200, 205))
    texto(d, (w * 0.40, h * 0.74), INSTAGRAM, ajustar(d, INSTAGRAM, "SemiBold", 28, 330), (70, 70, 80), anchor="lm")
    texto(d, (w * 0.40, h * 0.86), CONTACTO.replace("WhatsApp: ", ""), font("SemiBold", 28), (70, 70, 80), anchor="lm")
    return c


def colar_rotacionado(img, im, cx, cy, ang):
    r = im.rotate(ang, expand=True, resample=Image.BICUBIC)
    sombra = Image.new("RGBA", r.size, (0, 0, 0, 0))
    sombra.paste((0, 0, 0, 110), mask=r.split()[3])
    img.paste(sombra, (int(cx - r.width / 2 + 12), int(cy - r.height / 2 + 16)), sombra)
    img.paste(r, (int(cx - r.width / 2), int(cy - r.height / 2)), r)


def video_cartoes(t):
    img, d = cena_base(t)
    texto(d, (VW / 2, 230), "CARTÕES DE VISITA", font("Black", 92), WHITE, alpha=seg(t, 0.1))
    texto(d, (VW / 2, 340), "QUE IMPRESSIONAM", font("Black", 92), C, alpha=seg(t, 0.4))
    cores = [C, M, C, WHITE, M]
    angs = [-12, 8, -5, 14, -2]
    for i in range(5):
        k = seg(t, 1.0 + i * 0.9, 0.6)
        if k <= 0:
            continue
        cx = VW / 2 + (1 - k) * (-900 if i % 2 else 900)
        cy = 620 + i * 190
        c = cartao_visita(cor=cores[i] if cores[i] != WHITE else (30, 30, 38))
        colar_rotacionado(img, c, cx, cy, angs[i] * k)
    d = ImageDraw.Draw(img)
    if t > 7.0:
        return sair_para_cta(img, t, 7.0, "Peça seu orçamento grátis")
    return img


def tshirt(d, cx, cy, esc, cor):
    pts = [(-150, -290), (150, -290), (330, -170), (250, -60), (170, -120),
           (170, 300), (-170, 300), (-170, -120), (-250, -60), (-330, -170)]
    d.polygon([(cx + x * esc + 12, cy + y * esc + 16) for x, y in pts], fill=(0, 0, 0))
    d.polygon([(cx + x * esc, cy + y * esc) for x, y in pts], fill=cor)
    esc_c = tuple(int(v * 0.7) for v in cor)
    d.ellipse((cx - 70 * esc, cy - 340 * esc, cx + 70 * esc, cy - 230 * esc), fill=esc_c)


def video_tshirt(t):
    img, d = cena_base(t)
    texto(d, (VW / 2, 230), "CAMISETAS PERSONALIZADAS", ajustar(d, "CAMISETAS PERSONALIZADAS", "Black", 84, 980),
          WHITE, alpha=seg(t, 0.1))
    texto(d, (VW / 2, 330), "COM A SUA LOGO", font("Black", 92), C, alpha=seg(t, 0.4))
    camisas = [(235, 235, 232), (30, 30, 40), C, M]
    idx = min(int(max(0, t - 3.0) / 1.2), 3) if t >= 3.0 else 0
    base = camisas[idx]
    cx, cy, esc = VW / 2, 1000, 1.45
    tshirt(d, cx, cy, esc, base)
    # logotipo estampado
    lc = (20, 20, 25) if sum(base) > 450 else WHITE
    k_logo = seg(t, 1.6, 0.4)
    peito = (cx, cy - 20)
    if k_logo > 0:
        d.ellipse((peito[0] - 90, peito[1] - 160, peito[0] + 90, peito[1] + 20), fill=C if base != C else RED_ESCURO)
        texto(d, (peito[0], peito[1] + 100), MARCA, font("Black", 96), lc)
        texto(d, (peito[0], peito[1] + 170), SUB, font("Bold", 34), lc)
    # prensa
    prensa_y = -300 + 330 * seg(t, 0.8, 0.8) - 330 * seg(t, 2.0, 0.8)
    if 0.8 <= t <= 3.0:
        d.rectangle((peito[0] - 190, peito[1] + prensa_y - 300, peito[0] + 190, peito[1] + prensa_y + 20), fill=(90, 95, 110))
        d.rectangle((peito[0] - 190, peito[1] + prensa_y + 20, peito[0] + 190, peito[1] + prensa_y + 40), fill=Y)
    legenda = "Qualquer cor. Qualquer logo." if t < 7 else ""
    texto(d, (VW / 2, 1560), legenda, font("SemiBold", 50), GREY, alpha=seg(t, 3.2) * (1 - seg(t, 6.6, 0.4)))
    if t > 7.0:
        return sair_para_cta(img, t, 7.0, "Peça seu orçamento grátis")
    return img


def video_lona(t):
    img, d = cena_base(t)
    depois = t >= 4.0
    texto(d, (VW / 2, 220), "DEPOIS" if depois else "ANTES", font("Black", 130), C if depois else GREY)
    # fachada
    d.rectangle((60, 420, VW - 60, 1560), fill=(48, 48, 62))
    d.rectangle((120, 980, 480, 1450), fill=(25, 30, 45))      # montra
    d.rectangle((600, 980, 960, 1450), fill=(25, 30, 45))
    d.rectangle((510, 1100, 570, 1560), fill=(20, 20, 28))     # porta
    d.rectangle((60, 1560, VW - 60, 1620), fill=(30, 30, 38))
    # letreiro simples (antes)
    d.rectangle((120, 520, VW - 120, 760), fill=(110, 110, 118))
    texto(d, (VW / 2, 640), "LOJA", font("Bold", 100), (80, 80, 88))
    # lona nova a descer
    k = seg(t, 3.0, 1.2) if depois or t >= 3.0 else 0
    if k > 0:
        y0 = int(-400 + (520 + 400) * k)
        d.rectangle((90, y0, VW - 90, y0 + 280), fill=C)
        d.ellipse((VW - 380, y0 - 60, VW - 60, y0 + 220), fill=RED_ESCURO)
        d.ellipse((60, y0 + 60, 320, y0 + 320), fill=(40, 40, 46))
        texto(d, (VW / 2, y0 + 105), "SUA LOJA", font("Black", 120), WHITE, sombra=True)
        texto(d, (VW / 2, y0 + 205), "AQUI O SEU NOME EM DESTAQUE", font("Bold", 36), WHITE)
    texto(d, (VW / 2, 1740), "Lonas e banners sob medida", font("SemiBold", 48), GREY, alpha=seg(t, 4.8))
    if t > 7.5:
        return sair_para_cta(img, t, 7.5, "Peça seu orçamento grátis")
    return img


def video_orcamento(t):
    img, d = cena_base(t)
    texto(d, (VW / 2, 230), "COMO PEDIR SEU", font("Black", 90), WHITE, alpha=seg(t, 0.1))
    texto(d, (VW / 2, 340), "ORÇAMENTO", font("Black", 130), C, alpha=seg(t, 0.4))
    passos = [("1", "Envie sua ideia", "Pelo WhatsApp ou na loja", C),
              ("2", "Receba o orçamento", "Grátis e sem compromisso", M),
              ("3", "Aprove o design", "Mostramos a prova antes", Y),
              ("4", "Receba o pedido", "Rápido, com qualidade", C)]
    d.rectangle((178, 640, 182, 640 + 3 * 250 * min(1.0, max(0.0, (t - 1.0) / 5.0))), fill=(70, 70, 90))
    for i, (n, t1, t2, cor) in enumerate(passos):
        k = seg(t, 1.0 + i * 1.3, 0.5)
        if k <= 0:
            continue
        y = 640 + i * 250
        dx = (1 - k) * 700
        d.ellipse((115 + dx, y - 65, 245 + dx, y + 65), fill=cor)
        texto(d, (180 + dx, y), n, font("Black", 80), contraste(cor))
        texto(d, (300 + dx, y - 28), t1, ajustar(d, t1, "Black", 62, 680), WHITE, anchor="lm")
        texto(d, (300 + dx, y + 40), t2, font("SemiBold", 42), cor, anchor="lm")
    if t > 8.0:
        return sair_para_cta(img, t, 8.0, "Fale conosco agora")
    return img


def gerar_videos():
    exportar_video("01_satisfying_impressao", 11, video_satisfying)
    exportar_video("02_o_que_imprimimos", 11, video_servicos)
    exportar_video("03_sorteio_100_cartoes", 11, video_sorteio)
    exportar_video("04_dica_3_erros", 12, video_dica)
    exportar_video("05_cartoes_de_visita", 11, video_cartoes)
    exportar_video("06_tshirts_personalizadas", 11, video_tshirt)
    exportar_video("07_lona_antes_depois", 11, video_lona)
    exportar_video("08_como_pedir_orcamento", 12, video_orcamento)


if __name__ == "__main__":
    gerar_cards()
    gerar_videos()
    print("Pronto:", CARDS, VIDEOS)
