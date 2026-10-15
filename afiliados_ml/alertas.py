"""Vigia de preço: avisa quando o produto chega no preço-alvo ou cai desde a última checagem."""
from .ml_api import _get, extrair_id, item


def adicionar(con, texto: str, alvo: float, get=_get) -> str:
    p = item(extrair_id(texto), get)
    con.execute("INSERT OR REPLACE INTO alertas(item_id,titulo,link,alvo,ultimo_preco) VALUES(?,?,?,?,?)",
                (p.id, p.titulo, p.link, alvo, p.preco))
    con.commit()
    return f"Vigiando {p.titulo} (agora R$ {p.preco:.2f}, alvo R$ {alvo:.2f})"


def checar(con, get=_get) -> list[str]:
    avisos = []
    for a in con.execute("SELECT * FROM alertas").fetchall():
        p = item(a["item_id"], get)
        motivo = None
        if p.preco <= a["alvo"]:
            motivo = f"chegou no alvo (R$ {a['alvo']:.2f})"
        elif a["ultimo_preco"] and p.preco < a["ultimo_preco"]:
            motivo = f"caiu de R$ {a['ultimo_preco']:.2f}"
        if motivo:
            avisos.append(f"📉 {p.titulo}: R$ {p.preco:.2f} - {motivo}\n   {p.link}")
        con.execute("UPDATE alertas SET ultimo_preco=? WHERE item_id=?", (p.preco, p.id))
    con.commit()
    return avisos
