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
   - `--texto` afina bordas de texto/logos sem mudar as cores. Com `--foto x0,y0,x1,y1` (frações) a região do rosto/foto recebe só realce leve e fica fiel ao original. Não use em fotos puras.
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

## Método "fundo limpo + texto em vetor" (melhor resultado para banner/faixa)

Usado no caso Isabela Sampaio (1600x800 px -> PDF 108x54 cm). Referência em `refazer_em_vetor/`:
1. `step1.py` — apaga texto/logo/ícones do fundo (preenchimento suave) e guarda as máscaras.
2. `build.py` — refaz o texto de fonte conhecida (Poppins, via Google Fonts) como **curvas**,
   **vetoriza** (potrace) o que usa fonte exclusiva (manuscrito, logo, ícones) e monta o PDF:
   fundo ampliado 4x + camada vetorial por cima.
- Dependências: `pip install opencv-python-headless fonttools potracer reportlab`.
- É um fluxo guiado: as caixas de texto e as fontes ficam no código, ajuste por arte.
- Sempre compare antes/depois ampliado (pdftocairo -r 300) antes de entregar.
- Fonte exclusiva não existe no PC: não "adivinhe" outra; vetorize o desenho original.
