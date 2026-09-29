"""Classifica o objeto de uma licitação como relevante para a Jotak ou não."""
import re
import unicodedata


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto.lower()).strip()


# Produtos que a Jotak faz (lista informada pelo dono).
PRODUTOS = {
    "Banner / lona": r"\bbanners?\b|\blonas?\b",
    "Camisa": r"\bcamisas?\b|\bcamisetas?\b",
    "Bandeira": r"\bbandeiras?\b(?! (?:de )?(?:cartao|tarifaria))",
    "Faixa em lona": r"\bfaixas? (?:em|de) (?:lona|tecido|pvc)\b",
    "Crachá": r"\bcrachas?\b",
    "Placa PS": r"\bplacas? (?:de )?(?:ps|poliestireno|sinalizacao|identificacao)\b",
    "Adesivo vinil": r"\badesivos?\b|\bvinil\b|\badesivagem\b",
}

# Termos próximos do ramo: entram como "talvez" para revisão humana.
PROXIMOS = {
    "Plotagem": r"\bplotagem\b|\bplotter\b",
    "Comunicação visual": r"\bcomunicacao visual\b|\bidentificacao visual\b",
    "Impressão gráfica": r"\bimpressao grafica\b|\bservicos? graficos?\b|\bmaterial grafico\b",
    "Uniforme": r"\buniformes?\b",
}

# Ruído conhecido: só rebaixa "talvez", nunca um produto da lista.
EXCLUSOES = [
    r"\bassessoria de imprensa\b",
    r"\bmidias sociais\b",
    r"\bproducao audiovisual\b",
    r"\bbandeira (?:de )?(?:cartao|tarifaria)\b",
]


def classificar(objeto: str) -> tuple[str, list[str]]:
    """Retorna ('relevante' | 'talvez' | 'descartar', termos encontrados)."""
    t = normalizar(objeto)
    achados = [n for n, rx in PRODUTOS.items() if re.search(rx, t)]
    if achados:
        return "relevante", achados
    achados = [n for n, rx in PROXIMOS.items() if re.search(rx, t)]
    if achados and not any(re.search(rx, t) for rx in EXCLUSOES):
        return "talvez", achados
    return "descartar", []
