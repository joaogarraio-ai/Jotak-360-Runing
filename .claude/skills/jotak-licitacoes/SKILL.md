---
name: jotak-licitacoes
description: Triagem de licitações para a Jotak Impressos (banner/lona, camisa, bandeira, faixa, crachá, placa PS, adesivo vinil; plotagem e comunicação visual como "talvez"). Use quando o utilizador colar um boletim Licitanet, um convite Petronect, um objeto de licitação, ou indicar uma pasta de e-mails .eml e quiser saber o que interessa à Jotak.
---

# Triagem de licitações da Jotak

O código está em `jotak_licitacoes/` na raiz do repositório. Corre tudo a partir da raiz.

## 1. Pasta de e-mails (.eml)

```bash
python -m jotak_licitacoes PASTA -o relatorio.md [--uf BA,SE] [--incluir-vencidas]
```

Lê os boletins Licitanet e os convites Petronect, remove duplicados, descarta o que não
interessa e as sessões já vencidas, e escreve `relatorio.md` com os RELEVANTES primeiro
(ordenados pela data da sessão) e depois os "talvez". Mostra ao utilizador o resumo do relatório.

## 2. Texto colado (boletim Licitanet ou objeto solto)

Grava o texto num ficheiro temporário no scratchpad e corre:

```bash
python - CAMINHO <<'PY'
import sys
from pathlib import Path
from jotak_licitacoes.filtro import classificar
from jotak_licitacoes.leitores import ler_licitanet
texto = Path(sys.argv[1]).read_text(encoding="utf-8")
ops = ler_licitanet(texto)
if ops:
    for o in ops:
        print(classificar(o.objeto), "|", o.orgao, "|", o.sessao, "|", o.objeto)
else:
    for linha in filter(str.strip, texto.splitlines()):
        print(classificar(linha), "|", linha)
PY
```

Para um convite Petronect colado, usa `ler_petronect(assunto, corpo)`.

## Como responder

- Responde em português, agrupando assim: **Relevante**, **Talvez (rever)**, e o número de descartados.
- Em cada item: órgão, data da sessão (ou "consultar no portal"), objeto e os termos encontrados.
- O "talvez" é para uma pessoa decidir. Não o promovas a relevante por tua conta.
  Um objeto que é comprar ou fazer manutenção de um plotter (aparelho, cartuchos, papel)
  não é serviço da Jotak: assinala-o como provável falso positivo.

## Alterar o filtro

As listas `PRODUTOS`, `PROXIMOS` e `EXCLUSOES` estão em `jotak_licitacoes/filtro.py`.
Os padrões são aplicados a texto já normalizado (minúsculas, sem acentos), por isso escreve-os
sem acentos e inclui os plurais. Depois de cada alteração, junta um caso a `tests/test_jotak.py`
e corre `python -m unittest -q tests.test_jotak`.
