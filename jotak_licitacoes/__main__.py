"""Uso: python -m jotak_licitacoes PASTA_COM_EMLS [-o relatorio.md] [--uf BA,SE]"""
import argparse
import re
from datetime import datetime
from pathlib import Path

from .filtro import classificar
from .leitores import ler_eml


def _data(o):
    try:
        return datetime.strptime(o.sessao, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pasta")
    ap.add_argument("-o", "--saida", default="relatorio.md")
    ap.add_argument("--uf", help="UFs separadas por vírgula (ex.: BA,SE); só vale para Licitanet")
    ap.add_argument("--incluir-vencidas", action="store_true")
    a = ap.parse_args()
    ufs = {u.strip().upper() for u in a.uf.split(",")} if a.uf else set()

    achadas, vistos = [], set()
    for f in sorted(Path(a.pasta).rglob("*.eml")):
        for o in ler_eml(f):
            chave = (o.fonte, o.id or o.orgao, o.objeto)
            if chave in vistos:
                continue
            vistos.add(chave)
            nivel, termos = classificar(o.objeto)
            if nivel == "descartar":
                continue
            uf = re.search(r"/([A-Z]{2})\b", o.orgao)
            if ufs and uf and uf[1] not in ufs:
                continue
            d = _data(o)
            if d and d < datetime.now() and not a.incluir_vencidas:
                continue
            achadas.append((nivel, d or datetime.max, o, termos))

    achadas.sort(key=lambda x: (x[0] != "relevante", x[1]))
    linhas = ["# Oportunidades para a Jotak Impressos", ""]
    for nivel, d, o, termos in achadas:
        marca = "RELEVANTE" if nivel == "relevante" else "talvez"
        sessao = o.sessao or "consultar no portal"
        linhas += [
            f"- **[{marca}] {o.fonte}** — {o.orgao} ({o.modalidade or 's/ modalidade'})",
            f"  - Sessão: {sessao}" + (f" · ID {o.id}" if o.id else ""),
            f"  - Objeto: {o.objeto}",
            f"  - Termos: {', '.join(termos)}",
        ]
    Path(a.saida).write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"{len(achadas)} oportunidades em {a.saida}")


main()
