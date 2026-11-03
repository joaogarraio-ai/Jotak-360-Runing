# JOTAK IMPRESSOS — ENTREGA PARA CONTINUIDADE NO CLAUDE

## Pedido do proprietário
Finalizar o site oficial da JOTAK Impressos & Comunicação Visual, SEM nomes ChatGPT/GPT/Lovable na marca ou no domínio, com logomarca ORIGINAL (não redesenhar, esticar ou substituir), cores vermelho, grafite, branco e preto, fotos e efeitos bonitos, funcionamento em celular e computador. NÃO ALTERAR o JOTAK GESTÃO 360 ou seus dados.

## Qual versão abrir
- `SITE_PUBLICAVEL/index.html`: a versão MAIS COMPLETA visualmente, com seis fotos ILUSTRATIVAS de serviços e animações/zoom/galeria; orçamento pelo WhatsApp sem preços públicos. É estática e adequada para Cloudflare Pages.
- `VERSAO_EMAIL_EM_DESENVOLVIMENTO/index.html`: outra versão com formulário apontável para Apps Script e botão WhatsApp, mas ainda NÃO integrada/validada e sem as fotos novas. Usar APENAS como referência para migrar o formulário ao site principal.
- `VERSAO_EMAIL_EM_DESENVOLVIMENTO/Codigo.gs`: Google Apps Script preparado para lançar pedidos em planilha e enviar aviso ao Gmail; teste deu erro de ID de planilha. NÃO CONSIDERAR PRODUÇÃO.
- `LOGO_ORIGINAL_JOTAK.png` e `.pdf`: fontes oficiais. O site publicável também possui `assets/logo-jotak.png`.

## Dados comerciais confirmados
Domínio de propriedade do cliente, no Registro.br: `jotakimpressos.com.br`.
Endereço de teste Cloudflare Pages: `https://jotak-impressos.pages.dev`.
A versão de teste já estava publicada; arquivos deste pacote NÃO foram comprovadamente enviados como nova implantação.
Conta destino de notificações: `jotakimpressos@gmail.com`.
WhatsApp comercial: `+55 75 98106-5204`.
Instagram usado no site: `@jotakimpressosgrafica`.
Local: Coração de Maria, BA, atende Feira de Santana e região.

## Requisitos funcionais (não confundir planejamento com funcionamento)
1. Mostrar produtos de comunicação visual, lonas/banners, adesivos, perfurados, rótulos/etiquetas, camisas/DTF, impressos gráficos, placas e fachadas.
2. Galeria com fotos e efeitos; as fotos atuais são ilustrativas geradas, não trabalhos comprovados da empresa. Trocar depois por fotos reais.
3. Formulário: nome, telefone/WhatsApp, e-mail opcional, produto, medidas, quantidade, detalhes, futura anexação de arte. SEM EXIBIR PREÇOS.
4. Uma única solicitação deverá ser gravada em um sistema de pedidos e notificar `jotakimpressos@gmail.com`; WhatsApp deve ser alternativa de contato, mas NÃO afirmar que pedidos são gravados quando ainda não forem.
5. Integração com Gestão 360 é FUTURA e DEPENDE de autorização explícita, API e separação de permissões. NÃO alterar diretamente os dados nem a interface do Gestão 360 sem aprovação. Link de referência: https://jotak-gestao.joaogarraio.chatgpt.site
6. Evitar spam e abuso do endpoint de e-mails, validar dados, limitar frequência e garantir proteção contra injeção em planilha. Não publicar endpoint sem revisar riscos.
7. Dados coletados: incluir informação de privacidade/LGPD compatível com o fluxo real.
8. Só anunciar sucesso se backend confirmar o armazenamento; proteger contra pedidos duplicados; testar fluxo de ponta a ponta.

## Pendências técnicas concretas
- Apps Script foi implantado inicialmente com acesso `Somente eu`; clientes públicos não podem submeter no estado atual.
- Ao executar `testarOrcamentoJotak`, houve `Exception: Illegal spreadsheet id or key`. Corrigir copiando o ID diretamente do documento do Google e verificando autorização/acesso; NÃO presumir que o identificador mostrado em capturas foi transcrito corretamente.
- O código possui permissões amplas para Sheets e e-mail; revisar antes de abrir ao público.
- O formulário na pasta de desenvolvimento ainda tem `COLE_AQUI_URL_DO_GOOGLE_APPS_SCRIPT`; logo não há envio automático funcional.
- O site principal com fotos ainda envia somente ao WhatsApp. Não prometer recebimento Gmail ou integração Gestão 360.
- Fotos do site são representações ilustrativas e não imagens de serviços reais da JOTAK.
- Conectar domínio personalizado `www.jotakimpressos.com.br` via CNAME: nome `www`, destino `jotak-impressos.pages.dev`, mantendo DNS no Registro.br. Antes de alterar, conferir conflitos e os demais registros DNS. Verificar HTTPS e a configuração do domínio sem www separadamente.

## Publicação Cloudflare
O site principal é estático, com `index.html` na raiz e pasta `assets/`. Compactar somente o CONTEÚDO de `SITE_PUBLICAVEL` para publicar no Cloudflare Pages `jotak-impressos`. A publicação exige acesso autorizado à conta Cloudflare. NÃO criar outro projeto, a menos que seja necessário e aprovado.

## Identidade
Manter fielmente as proporções, o K branco em círculo vermelho, as letras JOTA cinza/grafite, swoosh vermelho e subtítulo 'IMPRESSOS & COMUNICAÇÃO VISUAL'. Não modificar a marca original.

## Pedido prioritário ao Claude
1. Abrir `SITE_PUBLICAVEL/index.html` e auditar visual, responsividade, navegação, imagens e efeitos.
2. Incorporar fluxo de formulário consistente, seguro e testado, preferindo salvar pedido antes de enviar e-mail; NÃO usar frontend para acessar contas privadas diretamente.
3. Preparar instruções claras de publicação na Cloudflare e configuração DNS no Registro.br, com checkpoint antes de mudanças irreversíveis.
4. Reportar claramente o que foi implementado, o que ficou pendente e como testar.
