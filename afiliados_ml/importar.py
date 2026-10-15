"""Importa CSV de vendas/comissões (relatório exportado do painel de afiliados)."""
import csv
import hashlib
import io
import re
import unicodedata
from datetime import datetime

# nome canônico -> variações possíveis de cabeçalho (já normalizadas)
ALIASES = {
    "data": {"data", "data da venda", "data do pedido", "date"},
    "produto": {"produto", "item", "titulo", "nome do produto", "product"},
    "campanha": {"campanha", "tag", "etiqueta", "campaign"},
    "valor": {"valor", "valor da venda", "preco", "total", "amount"},
    "comissao": {"comissao", "ganho", "ganhos", "comissao estimada", "commission"},
    "status": {"status", "situacao", "estado"},
}


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t or "")
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower().strip()


def numero(s: str) -> float:
    """Aceita 'R$ 1.234,56', '1234.56' e '12,5'."""
    s = re.sub(r"[^\d,.\-]", "", s or "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return float(s) if s not in ("", "-") else 0.0


def data_iso(s: str) -> str:
    s = (s or "").strip()[:10]
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError(f"data inválida: {s!r}")


def status_canonico(s: str) -> str:
    s = _norm(s)
    if any(p in s for p in ("cancel", "devolv", "reembols")):
        return "cancelada"
    if any(p in s for p in ("pag", "liberad", "conclu")):
        return "paga"
    return "pendente"


def importar_csv(con, texto: str) -> tuple[int, int]:
    """Retorna (novas, ignoradas por duplicidade/erro)."""
    amostra = texto[:2000]
    sep = ";" if amostra.count(";") > amostra.count(",") else ","
    leitor = csv.DictReader(io.StringIO(texto), delimiter=sep)
    mapa = {}
    for col in leitor.fieldnames or []:
        for canon, nomes in ALIASES.items():
            if _norm(col) in nomes:
                mapa[canon] = col
    faltando = {"data", "produto", "comissao"} - mapa.keys()
    if faltando:
        raise ValueError(f"colunas não encontradas: {', '.join(sorted(faltando))}")
    novas = ignoradas = 0
    for lin in leitor:
        try:
            g = lambda k: lin.get(mapa.get(k, ""), "") or ""
            d, prod = data_iso(g("data")), g("produto").strip()
            com, val = numero(g("comissao")), numero(g("valor"))
            st = status_canonico(g("status"))
        except ValueError:
            ignoradas += 1
            continue
        chave = hashlib.sha1(f"{d}|{prod}|{val}|{com}".encode()).hexdigest()
        cur = con.execute(
            "INSERT OR IGNORE INTO vendas(data,produto,campanha,valor,comissao,status,chave) "
            "VALUES(?,?,?,?,?,?,?)", (d, prod, g("campanha").strip(), val, com, st, chave))
        novas += cur.rowcount
        ignoradas += 1 - cur.rowcount
    con.commit()
    return novas, ignoradas
