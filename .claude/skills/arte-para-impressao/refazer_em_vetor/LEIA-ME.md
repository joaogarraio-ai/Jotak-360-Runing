# Pipeline de refação em vetor (exemplo: Isabela Sampaio, 1600x800 -> PDF 108x54 cm)
Rodar na ordem, na pasta de trabalho com `orig.webp` (arte) e `fonts/*.ttf` (Google Fonts, via raw.githubusercontent.com/google/fonts):
1. `python3 step1.py`  -> `bg_clean.png` + `masks.npz` (apaga texto/logo/ícones do fundo)
2. `python3 extra.py`  -> `bg_clean2.png` + `extra.npz` (blocos de cor chapada e traços finos)
3. `python3 build.py saida.pdf` -> PDF: fundo + vetores + texto em curvas

Tudo está parametrizado POR ARTE (caixas REG, LINES, REGS, cores, fontes): copie os scripts e ajuste.
Dependências: `pip install opencv-python-headless fonttools potracer reportlab pillow numpy`.
Lições: conferir sempre lado a lado (original x PDF a 300 dpi); regiões grandes demais pegam a foto
(rosto) — manter regiões justas; traço fino sobre bloco colorido precisa de tom + ajuste de curva.
