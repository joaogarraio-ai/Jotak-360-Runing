"""Painel web local (somente biblioteca padrão)."""
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from .db import conectar, resumo
from .importar import data_iso, importar_csv, numero

e = html.escape
CSS = ("body{font-family:system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}"
       "table{border-collapse:collapse;width:100%;margin:.5rem 0}td,th{border-bottom:1px solid #ddd;"
       "padding:.4rem;text-align:left}input,textarea,select{margin:.2rem 0;padding:.3rem}"
       "nav a{margin-right:1rem}.k{font-size:1.6rem;font-weight:700}")


def brl(v):
    return "R$ " + f"{v or 0:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pagina(corpo, aviso=""):
    return (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
            f"<style>{CSS}</style><h1>Afiliado Mercado Livre</h1>"
            "<nav><a href=/>Resumo</a><a href=/links>Links</a><a href=/vendas>Vendas</a>"
            f"<a href=/importar>Importar CSV</a></nav><p><b>{e(aviso)}</b></p>{corpo}")


def tabela(cab, linhas):
    th = "".join(f"<th>{e(c)}</th>" for c in cab)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in linhas)
    return f"<table><tr>{th}</tr>{tr}</table>"


def render(con, caminho, aviso=""):
    if caminho == "/links":
        ls = con.execute("SELECT * FROM links ORDER BY id DESC").fetchall()
        form = ("<form method=post action=/links><input name=titulo placeholder=Título required>"
                "<input name=url placeholder='Link de afiliado' required size=40>"
                "<input name=campanha placeholder=Campanha/tag><button>Salvar</button></form>")
        return pagina(form + tabela(["Título", "Campanha", "Link"], [
            (e(l["titulo"]), e(l["campanha"]), f"<a href='{e(l['url'])}'>{e(l['url'])}</a>") for l in ls]), aviso)
    if caminho == "/vendas":
        vs = con.execute("SELECT * FROM vendas ORDER BY data DESC, id DESC LIMIT 200").fetchall()
        form = ("<form method=post action=/vendas><input name=data type=date required>"
                "<input name=produto placeholder=Produto required><input name=valor placeholder=Valor>"
                "<input name=comissao placeholder=Comissão required>"
                "<select name=status><option>pendente<option>paga<option>cancelada</select>"
                "<button>Adicionar</button></form>")
        return pagina(form + tabela(["Data", "Produto", "Valor", "Comissão", "Status"], [
            (v["data"], e(v["produto"]), brl(v["valor"]), brl(v["comissao"]), v["status"]) for v in vs]), aviso)
    if caminho == "/importar":
        return pagina("<p>Cole o conteúdo do CSV exportado do painel de afiliados (colunas: data, produto, "
                      "comissão; opcionais: valor, status, campanha).</p><form method=post action=/importar>"
                      "<textarea name=csv rows=12 cols=80></textarea><br><button>Importar</button></form>", aviso)
    por_mes, por_prod, a_receber = resumo(con)
    total = sum(m["comissao"] or 0 for m in por_mes)
    corpo = (f"<p>Comissão total<br><span class=k>{brl(total)}</span> &nbsp; A receber (pendente)<br>"
             f"<span class=k>{brl(a_receber)}</span></p><h3>Por mês</h3>"
             + tabela(["Mês", "Vendas", "Valor vendido", "Comissão"], [
                 (m["mes"], m["vendas"], brl(m["valor"]), brl(m["comissao"])) for m in por_mes])
             + "<h3>Top produtos</h3>"
             + tabela(["Produto", "Vendas", "Comissão"], [
                 (e(p["produto"]), p["vendas"], brl(p["comissao"])) for p in por_prod]))
    return pagina(corpo, aviso)


def tratar_post(con, caminho, f):
    c = lambda k: f.get(k, [""])[0].strip()
    if caminho == "/links":
        con.execute("INSERT INTO links(titulo,url,campanha) VALUES(?,?,?)", (c("titulo"), c("url"), c("campanha")))
        con.commit()
        return "Link salvo."
    if caminho == "/vendas":
        con.execute("INSERT INTO vendas(data,produto,valor,comissao,status) VALUES(?,?,?,?,?)",
                    (data_iso(c("data")), c("produto"), numero(c("valor")), numero(c("comissao")), c("status")))
        con.commit()
        return "Venda registrada."
    if caminho == "/importar":
        n, i = importar_csv(con, f.get("csv", [""])[0])
        return f"{n} vendas novas importadas, {i} ignoradas (duplicadas ou inválidas)."
    return ""


def servir(db="afiliados.db", porta=8000):
    class H(BaseHTTPRequestHandler):
        def _enviar(self, corpo):
            b = corpo.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            con = conectar(db)
            self._enviar(render(con, self.path.split("?")[0]))

        def do_POST(self):
            con = conectar(db)
            dados = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            try:
                aviso = tratar_post(con, self.path, parse_qs(dados))
            except ValueError as ex:
                aviso = f"Erro: {ex}"
            self._enviar(render(con, self.path, aviso))

        def log_message(self, *a):
            pass

    print(f"Painel em http://127.0.0.1:{porta}  (Ctrl+C para sair)")
    HTTPServer(("127.0.0.1", porta), H).serve_forever()
