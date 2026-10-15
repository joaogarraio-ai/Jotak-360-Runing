import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    url TEXT NOT NULL,
    campanha TEXT NOT NULL DEFAULT '',
    criado TEXT NOT NULL DEFAULT (date('now'))
);
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,            -- AAAA-MM-DD
    produto TEXT NOT NULL,
    campanha TEXT NOT NULL DEFAULT '',
    valor REAL NOT NULL DEFAULT 0,
    comissao REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pendente',   -- pendente | paga | cancelada
    chave TEXT UNIQUE              -- evita duplicar na importação
);
"""


def conectar(caminho: str = "afiliados.db") -> sqlite3.Connection:
    con = sqlite3.connect(caminho)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def resumo(con):
    """Totais por mês e por produto (cancelada não conta)."""
    por_mes = con.execute(
        "SELECT substr(data,1,7) mes, COUNT(*) vendas, SUM(valor) valor, SUM(comissao) comissao "
        "FROM vendas WHERE status!='cancelada' GROUP BY mes ORDER BY mes DESC").fetchall()
    por_produto = con.execute(
        "SELECT produto, COUNT(*) vendas, SUM(comissao) comissao "
        "FROM vendas WHERE status!='cancelada' GROUP BY produto ORDER BY comissao DESC LIMIT 10").fetchall()
    a_receber = con.execute(
        "SELECT COALESCE(SUM(comissao),0) FROM vendas WHERE status='pendente'").fetchone()[0]
    return por_mes, por_produto, a_receber


ALERTAS = """
CREATE TABLE IF NOT EXISTS alertas (
    item_id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    link TEXT NOT NULL DEFAULT '',
    alvo REAL NOT NULL,            -- avisa quando preço <= alvo
    ultimo_preco REAL
);
"""
_conectar = conectar


def conectar(caminho: str = "afiliados.db") -> sqlite3.Connection:  # noqa: F811
    con = _conectar(caminho)
    con.executescript(ALERTAS)
    return con
