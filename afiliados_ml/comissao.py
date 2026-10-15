"""Estimativa de comissão por categoria.

ATENÇÃO: percentuais copiados de um blog (Hunterhub), NÃO do Mercado Livre, e outros blogs
divergem. Confira no painel de afiliados e ajuste aqui (ou crie comissoes.json).
Formato do JSON: [["palavra-chave", direta, indireta], ...]  ex.: [["beleza", 0.16, 0.08]]
"""
import json
import os
import unicodedata

TABELA = [
    (("beleza", "calcados", "roupas", "bolsas", "esportes", "fitness"), 0.16, 0.08),
    (("alimentos", "bebidas"), 0.0, 0.0),
    (("celulares", "eletronicos", "informatica", "eletrodomesticos", "cameras", "audio"), 0.05, 0.025),
    (("casa", "moveis", "decoracao", "bebes", "brinquedos", "hobbies", "ferramentas", "construcao",
      "games", "joias", "relogios", "livros", "veiculos"), 0.12, 0.06),
]
PADRAO = (0.12, 0.06)  # "Mais categorias"


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t or "")
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def _tabela(caminho="comissoes.json"):
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return [((k,), d, i) for k, d, i in json.load(f)]
    return TABELA


def taxa(categoria: str, caminho="comissoes.json") -> tuple[float, float]:
    n = _norm(categoria)
    for palavras, direta, indireta in _tabela(caminho):
        if any(p in n for p in palavras):
            return direta, indireta
    return PADRAO


def estimar(preco: float, categoria: str, caminho="comissoes.json") -> tuple[float, float]:
    d, i = taxa(categoria, caminho)
    return round(preco * d, 2), round(preco * i, 2)
