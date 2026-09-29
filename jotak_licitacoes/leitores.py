"""Leitores dos e-mails de Licitanet (boletim) e Petronect (convites)."""
import email
import html
import re
from dataclasses import dataclass
from email import policy
from pathlib import Path


@dataclass
class Oportunidade:
    fonte: str
    objeto: str
    orgao: str = ""
    modalidade: str = ""
    sessao: str = ""  # dd/mm/aaaa hh:mm:ss, quando o e-mail informa
    id: str = ""


def texto_do_eml(caminho: Path) -> tuple[str, str, str]:
    """Retorna (remetente, assunto, corpo em texto puro)."""
    msg = email.message_from_bytes(caminho.read_bytes(), policy=policy.default)
    corpo = msg.get_body(preferencelist=("plain", "html"))
    texto = corpo.get_content() if corpo else ""
    if corpo is not None and corpo.get_content_type() == "text/html":
        texto = re.sub(r"(?is)<(script|style).*?</\1>", " ", texto)
        texto = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h\d)>", "\n", texto)
        texto = html.unescape(re.sub(r"<[^>]+>", " ", texto))
    texto = re.sub(r"[ \t\xa0]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n", texto)
    return str(msg.get("From", "")), str(msg.get("Subject", "")), texto


_BLOCO_LICITANET = re.compile(
    r"(?P<mod>[A-ZÀ-Ý ]+(?:ELETRÔNIC[AO]|PRESENCIAL)|CONCORRÊNCIA[A-ZÀ-Ý ]*|DISPENSA[A-ZÀ-Ý ]*)"
    r":\s*(?P<orgao>[^\n]+)\n\s*Inicio da Sess[ãa]o:\s*(?P<sessao>[\d/]+ [\d:]+)\s*\n"
    r"\s*Descri[çc][ãa]o do\(s\) objeto\(s\):\s*(?P<objeto>.+?)(?=\n\s*(?:[A-ZÀ-Ý ]+:\s|Caso necessite)|\Z)",
    re.S,
)


def ler_licitanet(texto: str) -> list[Oportunidade]:
    return [
        Oportunidade(
            fonte="Licitanet",
            modalidade=m["mod"].strip().title(),
            orgao=m["orgao"].strip(),
            sessao=m["sessao"],
            objeto=re.sub(r"\s+", " ", m["objeto"]).strip(),
        )
        for m in _BLOCO_LICITANET.finditer(texto)
    ]


def ler_petronect(assunto: str, texto: str) -> list[Oportunidade]:
    m = re.search(r"Oportunidade Publicada ID\s*(\d+)\s*-\s*(.+)", assunto, re.S)
    if not m:
        return []
    unidade = re.search(r'da\s+"+([^"]+)"+', texto)
    return [
        Oportunidade(
            fonte="Petronect (Petrobras)",
            id=m[1],
            objeto=re.sub(r"\s+", " ", m[2]).strip(),
            orgao=unidade[1].strip() if unidade else "Petrobras",
        )
    ]


def ler_eml(caminho: Path) -> list[Oportunidade]:
    remetente, assunto, texto = texto_do_eml(caminho)
    r = remetente.lower()
    if "petronect" in r:
        return ler_petronect(assunto, texto)
    if "licitanet" in r or "licitanet" in assunto.lower():
        return ler_licitanet(texto)
    return []
