---
name: arte-para-impressao
description: Padrão da Jotak Gráfica para QUALQUER arte recebida (PNG/JPG/WebP, de ChatGPT, redes sociais, cliente) que tenha texto, logo, riscos ou vetores e vá para impressão. Refaz o arquivo como "feito na hora": fundo/foto originais limpos + texto, logos, ícones e traços em vetor (curvas) em PDF, sem pixel estourado. Use sempre que chegar arte com texto/baixa resolução, texto serrilhado, ou pergunta se o arquivo aguenta imprimir em certo tamanho.
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

## PADRÃO OBRIGATÓRIO: refazer em vetor (fundo limpo + vetores por cima)

Para toda arte com texto/logo/traços, o resultado final é um **PDF** com: (1) fundo e fotos originais
com tudo que é texto/grafismo removido, ampliados; (2) por cima, tudo refeito em vetor.

Regras do cliente (Jotak) — não negociáveis:
1. **Manter fiel ao original:** logos (nunca redesenhar nem trocar), cores/tonalidades, posições,
   proporções, o rosto e as fotos. Só melhora a definição.
2. **Texto:** olhar cada texto. Se a fonte é conhecida (ex.: Poppins, Montserrat — conferir lado a lado),
   digitar de novo com a fonte real e converter em curvas. Se a fonte é exclusiva (manuscrito, logotipo),
   **não trocar por outra parecida**: vetorizar o desenho original.
3. **Riscos, linhas, ícones, formas, blocos de cor chapada, corações etc.:** examinar um a um e
   vetorizar (potrace). Nada de grafismo fino ficando em raster se der para vetorizar.
4. **Foto/rosto:** só ampliação suave + realce leve (nada de IA que reinventa a pessoa).
5. **Cores:** amostrar do próprio arquivo; usar a mesma cor em todos os elementos do mesmo tipo.
6. **Conferir:** comparar original x PDF (pdftocairo -r 300) em cada região (texto, ícones, cantos,
   rosto). Não entregar com falhas visíveis (tracinhos soltos, linhas quebradas, bordas grossas).
7. Pedir o tamanho final (cm); gerar PDF nesse tamanho, com sangria se pedirem. Se a foto original é
   pequena, avisar o limite dela (texto/vetor ficam perfeitos, a foto não).
8. Entregar: PDF + resumo (o que virou vetor, o que ficou raster, riscos).

9. **Geometria limpa (exigência do cliente):** reta tem que ser reta, círculo tem que ser redondo,
   curva tem que ser suave com poucos pontos; ícones simétricos; sem pontos soltos no contorno.
   Gradiente de fundo é refeito liso (sem blocos/faixas). Foto ruim: reduzir ruído da pele de leve,
   sem alterar traços do rosto.

Fluxo técnico e scripts de referência: `refazer_em_vetor/` (ver `LEIA-ME.md`). São guiados por arte:
copiar para a pasta de trabalho e ajustar caixas, fontes e cores.
Para artes simples sem texto importante, o atalho `preparar_arte.py` (diagnóstico/ampliação) basta.

## LOGOMARCA = prioridade máxima (exigência do cliente)
- **Sempre pedir o logo original em vetor (AI/PDF/SVG/CDR) ou PNG grande antes de refazer a arte.** Se vier, usar o original, sem redesenhar.
- Sem original: `vec.unmix_two_inks` (separa as tintas, desfaz desfoque, limpa ilhas/frestas, suaviza contorno mantendo pontas de serifa). Avisar o cliente que é reconstrução de um logo pequeno e que o ideal é o arquivo original.
- Conferir o logo a 400 dpi lado a lado com o original antes de entregar.
