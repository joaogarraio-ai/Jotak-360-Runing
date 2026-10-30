---
name: arte-para-impressao
description: Prepara arte de baixa resolução (ex.: imagens geradas por ChatGPT/IA) para impressão na Jotak Gráfica. Use quando o cliente mandar PNG/JPG pequeno, com texto serrilhado/pixelado/estourado, ou quando perguntarem se um arquivo "aguenta" imprimir em certo tamanho (banner, faixa, adesivo, crachá, placa, camiseta).
---

# Arte para impressão — Jotak Gráfica

Imagens de IA costumam vir com ~1024–2048 px e texto sem definição. Impressas em
banner/faixa ficam **reticuladas** (serrilhadas). Esta skill diagnostica e corrige o que dá.

## Passo a passo

1. **Pergunte o tamanho final** de impressão (cm) e o produto, se não souber.
2. **Diagnostique** (não altera nada):
   ```bash
   python .claude/skills/arte-para-impressao/preparar_arte.py ARQUIVO --largura-cm 300 --altura-cm 100 --diagnostico
   ```
   Mostra o DPI efetivo e o veredito (OK / Aceitável / Baixo / Crítico).
3. **Corrija**:
   ```bash
   python .claude/skills/arte-para-impressao/preparar_arte.py ARQUIVO --largura-cm 300 --altura-cm 100 --saida pronto.pdf
   ```
   Opções:
   - `--dpi N` DPI alvo (padrão: o recomendado do produto; use `--produto banner|faixa|adesivo|cracha|placa|camiseta`).
   - `--texto` reforça bordas de texto/logos (suaviza a escadinha dos pixels). Use em arte com cores chapadas e letras; **não** use em fotos.
   - `--sangria-mm 3` acrescenta sangria espelhando as bordas.
   - `--cmyk` converte para CMYK (aviso: conversão simples, sem perfil ICC).
   - Saída `.pdf`, `.tif` ou `.png`, já com o DPI e o tamanho físico gravados.

## Regras (seja honesto com o cliente)

- Aumentar resolução **não cria detalhe**. O script melhora a percepção, mas texto
  pequeno e rostos continuam limitados pelo original.
- **Melhor solução para texto:** refazer o texto como vetor (Illustrator/Corel/Canva em PDF)
  por cima da imagem ampliada. Sempre recomende isso quando o texto for importante
  (telefone, preço, nome).
- DPI de referência (olhando de longe se tolera menos): banner/faixa/lona 72–100,
  adesivo/placa 150–200, crachá/camiseta/papelaria 300.
- Se o veredito for **Crítico** (< 50% do DPI mínimo), avise que o resultado será
  borrado e peça arquivo melhor ou refação da arte.
- Sempre entregue um resumo: DPI antes → depois, o que foi feito e os riscos.
