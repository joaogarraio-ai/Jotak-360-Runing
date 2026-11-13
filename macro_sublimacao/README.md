# Jotak Sublimação: macros para CorelDRAW

São quatro macros que automatizam a produção de camisetas e uniformes sublimados dentro do CorelDRAW:

| Macro | O que faz |
|---|---|
| `GerarMoldesPorTamanho` | Aplica a arte em todos os tamanhos de molde (P, M, G, GG, infantil, baby look…), recorta a arte no formato de cada peça e entrega tudo já encaixado numa página **PRODUCAO**. |
| `GerarNomesENumeros` | Lê uma planilha (CSV) e gera uma peça por linha, com o nome e o número de cada pessoa, no tamanho certo, já encaixadas. |
| `EncaixarSelecao` | Organiza as peças selecionadas no papel e gira 90° quando compensa, para gastar menos papel. Funciona em rolo contínuo ou em folhas (A3, A4…). |
| `GerarMockups` | Coloca a arte nas fotos de camisa e, se você quiser, exporta um JPG de cada mockup para mandar ao cliente. |

Requisitos: **CorelDRAW X8 (2016) ou superior, no Windows**, com o VBA instalado. O VBA é instalado junto com o CorelDRAW por padrão.

---

## 1. Instalação (uma vez só)

1. No CorelDRAW, abra **Ferramentas › Scripts › Editor de scripts** (ou aperte `Alt+F11`).
2. Na árvore da esquerda, clique em **GlobalMacros**.
3. Em **Arquivo › Importar arquivo…**, importe os 4 arquivos desta pasta:
   `SubliComum.bas`, `SubliEncaixe.bas`, `SubliProducao.bas` e `SubliMockups.bas`.
4. Em **Depurar › Compilar GlobalMacros**, compile. Se nenhum erro aparecer, está pronto.
5. Salve com `Ctrl+S` e feche o editor.

Para rodar uma macro, use **Ferramentas › Scripts › Executar script** (`Alt+F8`) e escolha a macro. Também dá para criar um botão: **Ferramentas › Opções › Personalização › Comandos › Scripts** e arrastar a macro para uma barra de ferramentas.

---

## 2. Como preparar o arquivo do CorelDRAW

As macros encontram os objetos **pelo nome**. Para dar nome a um objeto, abra **Janela › Inspetores › Objetos** (o Gerenciador de Objetos), dê dois cliques no objeto e digite o nome.

### Página da arte (onde ficam os moldes)

| Objeto | Nome | Exemplo |
|---|---|---|
| Contorno de cada molde, um por tamanho | `MOLDE_<PEÇA>_<TAMANHO>` | `MOLDE_FRENTE_P`, `MOLDE_FRENTE_M`, `MOLDE_COSTAS_GG`, `MOLDE_MANGA_BL-M` |
| Arte de cada peça (agrupe antes de dar o nome) | `ARTE_<PEÇA>` | `ARTE_FRENTE`, `ARTE_COSTAS`, `ARTE_MANGA` |
| Texto do nome, dentro do grupo da arte | `TXT_NOME` | |
| Texto do número, dentro do grupo da arte | `TXT_NUMERO` | |

Regras:

- **Faça a arte em cima do molde M.** O tamanho base está definido em `TAMANHO_BASE` e pode ser alterado. Nos outros tamanhos, a macro aumenta ou diminui a arte na mesma proporção e na mesma posição relativa.
- O nome da peça não pode ter `_`. Para separar palavras, use `-`: `MANGA-ESQ`, não `MANGA_ESQ`.
- Os moldes e as artes precisam ficar soltos na página, sem estar dentro de outro grupo.
- Para usar moldes próprios, basta desenhar ou importar o contorno e dar o nome no padrão acima.
- Os moldes podem ficar sobrepostos (gradação encaixada, um dentro do outro) ou lado a lado. As duas formas funcionam.
- Os textos `TXT_NOME` e `TXT_NUMERO` precisam ser **texto artístico** (não convertido em curvas).

### Páginas de mockup

1. Crie uma página com nome começando por **MOCKUP**, por exemplo `MOCKUP 1 - Frente`. Clique com o botão direito na aba da página e escolha **Renomear página**.
2. Coloque a foto da camisa.
3. Desenhe sobre a foto uma forma no lugar onde a estampa deve aparecer e dê o nome `AREA_FRENTE`. Para as costas, use `AREA_COSTAS`, e assim por diante. A forma pode ser o próprio contorno da camisa.
4. Opcional: para a estampa ganhar as dobras do tecido, coloque por cima uma cópia da foto com transparência no modo **Multiplicar**.

---

## 3. Planilha de nomes e números

Faça a planilha no Excel e salve em **Arquivo › Salvar como › CSV (separado por ponto e vírgula)**. Veja o modelo em [`exemplo_nomes.csv`](exemplo_nomes.csv):

```
NOME;NUMERO;TAMANHO;QTD
João;10;M;1
Maria;7;BL-P;1
Pedro;9;GG;2
```

- **TAMANHO** é obrigatória e precisa ser igual ao final do nome do molde (`M` → `MOLDE_FRENTE_M`).
- **NOME**, **NUMERO** e **QTD** são opcionais. Sem QTD, a macro gera 1 peça por linha.
- A primeira linha precisa ter os nomes das colunas. Acento e maiúsculas não importam.
- O arquivo pode ser salvo em ANSI (o padrão do Excel) ou UTF-8. O separador pode ser `;`, `,` ou tab.

---

## 4. Configuração

Os ajustes ficam no topo de `SubliComum.bas`. No editor de scripts, abra o módulo e altere os valores:

| Opção | Padrão | Para que serve |
|---|---|---|
| `TAMANHO_BASE` | `"M"` | Tamanho do molde em que a arte foi feita. |
| `LARGURA_ROLO_MM` | `1600` | Largura útil do papel. |
| `ALTURA_MAX_MM` | `0` | `0` = rolo contínuo. Para folha A3, use largura `297` e altura `420`. |
| `ESPACO_MM` | `5` | Espaço entre as peças. |
| `MARGEM_MM` | `10` | Margem da página. |
| `PERMITIR_GIRO` | `True` | Deixa o encaixe girar as peças 90°. |
| `ESCALA_PROPORCIONAL` | `True` | `True` não distorce a arte. `False` estica igual ao molde. |
| `NOMES_EM_MAIUSCULAS` | `True` | Converte os nomes da planilha para MAIÚSCULAS. |
| `DPI_MOCKUP` | `150` | Resolução dos JPG de mockup. |

---

## 5. Bom saber

- **Tudo se desfaz com um `Ctrl+Z`.** Cada macro conta como um único passo no desfazer.
- **O arquivo original não é alterado.** As macros criam páginas novas (`PRODUCAO`, `ENCAIXE`). Se já existir uma página com esse nome, a nova recebe um número (`PRODUCAO 2`…).
- O **encaixe usa o retângulo de cada peça**, não o contorno exato. Peças muito tortas, como mangas raglan, podem deixar sobras entre si. Em testes com frente, costas e mangas, o aproveitamento num rolo de 1,60 m ficou em torno de 90%.
- **Os mockups são substituídos a cada rodada.** O que a macro gerou recebe o prefixo `GERADO_` e é trocado quando você roda de novo.
- Os JPG dos mockups vão para a pasta `mockups` ao lado do arquivo `.cdr`. O arquivo precisa estar salvo antes.
- Os nomes das peças geradas seguem o padrão `PECA_<PEÇA>_<TAMANHO>_<NOME>_<NÚMERO>`. Isso ajuda a achar e conferir cada uma no Gerenciador de Objetos.

### Se der erro

- **"Não encontrei nenhuma arte"**: a arte não está com nome `ARTE_...` ou está dentro de outro grupo.
- **"Não achei o molde base"**: falta o molde `MOLDE_<PEÇA>_M`, ou a arte não está em cima de nenhum molde daquela peça.
- **"Não existe o molde MOLDE_FRENTE_XG"**: a planilha pede um tamanho que não foi desenhado.
- **Erro de compilação ao importar**: confira se os 4 arquivos `.bas` foram importados no mesmo projeto (GlobalMacros).
