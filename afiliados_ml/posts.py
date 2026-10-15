"""Gera texto pronto de divulgação a partir de um produto + seu link de afiliado."""
from .ml_api import Produto


def brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _linhas(p: Produto) -> tuple[str, str]:
    preco = f"*{brl(p.preco)}*"
    if p.desconto:
        preco = f"~{brl(p.preco_antigo)}~ por {preco} ({p.desconto}% OFF)"
    frete = "🚚 Frete grátis" if p.frete_gratis else ""
    return preco, frete


def gerar(p: Produto, link: str, plataforma: str = "whatsapp") -> str:
    preco, frete = _linhas(p)
    if plataforma == "whatsapp":
        partes = [f"🔥 *{p.titulo}*", preco, frete, f"👉 {link}",
                  "⚠️ Preço e estoque podem mudar a qualquer momento. Link de afiliado."]
    elif plataforma == "instagram":
        partes = [f"🔥 {p.titulo}", preco.replace("*", "").replace("~", ""), frete,
                  "👉 Link na bio / no grupo de ofertas", "#publi #achadinhos #mercadolivre #ofertas"]
    elif plataforma == "tiktok":
        sem = preco.replace("*", "").replace("~", "")
        partes = [f"LEGENDA: {p.titulo[:60]} por {brl(p.preco)} 🔥 #publi #achadinhos #mercadolivre",
                  "ROTEIRO: (0-3s) gancho com o preço · (3-20s) mostre o produto em uso · "
                  "(20-25s) 'link na bio'", f"NA TELA: {sem}"]
    else:
        raise ValueError("plataforma deve ser whatsapp, instagram ou tiktok")
    return "\n".join(x for x in partes if x)
