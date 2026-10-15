"""Acesso à API pública do Mercado Livre (Brasil).

Se a API devolver 401/403, gere um token no portal de desenvolvedores do Mercado Livre
e exporte ML_ACCESS_TOKEN antes de rodar.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

BASE = "https://api.mercadolibre.com"


class ErroML(Exception):
    pass


def _get(caminho: str, params: dict | None = None) -> dict:
    url = BASE + caminho + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    token = os.environ.get("ML_ACCESS_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as ex:
        dica = " (defina ML_ACCESS_TOKEN)" if ex.code in (401, 403) else ""
        raise ErroML(f"Mercado Livre respondeu {ex.code}{dica}") from ex
    except urllib.error.URLError as ex:
        raise ErroML(f"sem conexão com o Mercado Livre: {ex.reason}") from ex


@dataclass
class Produto:
    id: str
    titulo: str
    preco: float
    preco_antigo: float | None
    link: str
    categoria_id: str
    vendidos: int
    frete_gratis: bool

    @property
    def desconto(self) -> int:
        if self.preco_antigo and self.preco_antigo > self.preco:
            return round(100 * (1 - self.preco / self.preco_antigo))
        return 0


def _produto(d: dict) -> Produto:
    return Produto(
        id=d["id"], titulo=d.get("title") or d.get("name", ""), preco=float(d.get("price") or 0),
        preco_antigo=d.get("original_price"), link=d.get("permalink", ""),
        categoria_id=d.get("category_id", ""), vendidos=int(d.get("sold_quantity") or 0),
        frete_gratis=bool((d.get("shipping") or {}).get("free_shipping")))


def buscar(termo: str, limite: int = 20, get=_get) -> list[Produto]:
    dados = get("/sites/MLB/search", {"q": termo, "limit": limite})
    return [_produto(r) for r in dados.get("results", [])]


def item(item_id: str, get=_get) -> Produto:
    return _produto(get(f"/items/{item_id}"))


def categoria_raiz(categoria_id: str, get=_get) -> str:
    """Nome da categoria de topo (é ela que define a comissão)."""
    if not categoria_id:
        return ""
    caminho = get(f"/categories/{categoria_id}").get("path_from_root") or []
    return caminho[0]["name"] if caminho else ""


def extrair_id(texto: str) -> str:
    m = re.search(r"MLB-?(\d+)", texto.upper())
    if not m:
        raise ValueError("não achei um código MLB no link/texto")
    return "MLB" + m.group(1)
