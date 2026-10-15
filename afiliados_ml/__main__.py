"""Uso:
  python -m afiliados_ml                       painel web (http://127.0.0.1:8000)
  python -m afiliados_ml buscar "organizador" [--min-vendidos 50] [--limite 30]
  python -m afiliados_ml post MLB123 --link SEU_LINK [--para whatsapp|instagram|tiktok]
  python -m afiliados_ml vigiar MLB123 --alvo 79,90
  python -m afiliados_ml checar                avisa quedas de preço (rode todo dia)
"""
import argparse

from . import alertas, comissao, ml_api, posts
from .db import conectar
from .importar import numero
from .ml_api import ErroML


def cmd_buscar(a):
    produtos = [p for p in ml_api.buscar(a.termo, a.limite) if p.vendidos >= a.min_vendidos]
    linhas = []
    cache = {}
    for p in produtos:
        cat = cache.setdefault(p.categoria_id, ml_api.categoria_raiz(p.categoria_id))
        direta, _ = comissao.estimar(p.preco, cat)
        linhas.append((direta, p, cat))
    linhas.sort(key=lambda x: -x[0])
    for direta, p, cat in linhas:
        print(f"{p.id} | {posts.brl(p.preco)} | comissão ~{posts.brl(direta)} | "
              f"{p.vendidos} vendidos | {cat}\n   {p.titulo}\n   {p.link}")
    if not linhas:
        print("Nada encontrado.")
    print("\nComissão estimada (venda direta) com percentuais NÃO oficiais: confira no painel do ML.")
    print("Gere o link de afiliado no painel do Mercado Livre antes de divulgar.")


def cmd_post(a):
    p = ml_api.item(ml_api.extrair_id(a.produto))
    print(posts.gerar(p, a.link, a.para))


def cmd_vigiar(a):
    print(alertas.adicionar(conectar(a.db), a.produto, numero(a.alvo)))


def cmd_checar(a):
    avisos = alertas.checar(conectar(a.db))
    print("\n".join(avisos) if avisos else "Nenhuma queda de preço.")


def cmd_servir(a):
    from .web import servir
    servir(a.db, a.porta)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--db", default="afiliados.db")
    ap.add_argument("--porta", type=int, default=8000)
    ap.set_defaults(f=cmd_servir)
    sub = ap.add_subparsers()
    s = sub.add_parser("buscar"); s.set_defaults(f=cmd_buscar)
    s.add_argument("termo"); s.add_argument("--limite", type=int, default=20)
    s.add_argument("--min-vendidos", type=int, default=0)
    s = sub.add_parser("post"); s.set_defaults(f=cmd_post)
    s.add_argument("produto"); s.add_argument("--link", required=True)
    s.add_argument("--para", default="whatsapp", choices=["whatsapp", "instagram", "tiktok"])
    s = sub.add_parser("vigiar"); s.set_defaults(f=cmd_vigiar)
    s.add_argument("produto"); s.add_argument("--alvo", required=True)
    s = sub.add_parser("checar"); s.set_defaults(f=cmd_checar)
    a = ap.parse_args()
    try:
        a.f(a)
    except (ErroML, ValueError) as ex:
        raise SystemExit(f"Erro: {ex}")


main()
