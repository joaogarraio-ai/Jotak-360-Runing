# Pipeline de refação em vetor LIMPA (exemplo: Isabela Sampaio, 1600x800 -> PDF 108x54 cm)
Pasta de trabalho com `orig.webp` e `fonts/*.ttf` (Google Fonts via raw.githubusercontent.com/google/fonts).
1. `python3 step1.py`   -> `bg_clean.png`, `masks.npz` (apaga texto/logo/ícones do fundo)
2. `python3 extra.py`   -> `bg_clean2.png`, `extra.npz` (blocos de cor chapada e traços finos)
3. `python3 build2.py saida.pdf` -> PDF final (usa `vec.py` e partes de `build.py`)

Dependências: `pip install opencv-python-headless fonttools potracer reportlab scikit-image scipy`.

## Regra de ouro: GEOMETRIA ANTES DE TRAÇADO AUTOMÁTICO
Vetorização automática copia o ruído do JPEG (contornos tortos, pontos demais). Por isso, `vec.py`:
- Instagram/pino/WhatsApp: círculos, retângulos arredondados e tangentes ajustados (`build_instagram`, `build_pin`, `build_whatsapp`).
- Ícones de linha (dentes): simetrizados (`symmetrize`) + traçado suave (poucos nós).
- Blocos de cor chapada: círculo ajustado por mínimos quadrados (`fit_circle`), nunca contorno de pixels.
- Linhas finas: esqueleto -> spline suave -> poucos Béziers, espessura constante, quina por interseção de tangentes (`fit_stroke`).
- Linha reta = retângulo exato (divisória). Fundo: parede alisada (gradiente) + dither; foto só com redução leve de ruído.
- Letras de fonte conhecida: reescritas com a fonte em curvas; fonte exclusiva: traçado suave (F=6, realce de traços finos).
Tudo é por arte: ajustar caixas, cores, fontes. Conferir lado a lado (pdftocairo -r 300) antes de entregar.
