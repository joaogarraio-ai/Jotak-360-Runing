# Publicação do site JOTAK

## Estado atual (honesto)
- `site/` é estático, pronto para Cloudflare Pages. Sem `ENDPOINT`, o formulário só abre o WhatsApp com a mensagem pronta (nada é gravado).
- Com `ENDPOINT` preenchido, aparece o botão **Enviar pedido**, que grava na planilha e avisa `jotakimpressos@gmail.com`. O site só mostra "Pedido recebido" se o backend responder `ok:true`.
- **Não testado ponta a ponta** (requer sua conta Google). Siga o checklist abaixo. Gestão 360: nenhuma integração, nada foi alterado.
- Fotos são ilustrativas (aviso já está no site); troque por fotos reais em `site/assets/` mantendo os nomes.

## 1. Backend (Google Apps Script) — conta jotakimpressos@gmail.com
1. Crie uma planilha Google "Pedidos JOTAK". Em **Extensões > Apps Script**, cole `apps-script/Codigo.gs` (script vinculado: evita o erro "Illegal spreadsheet id"; deixe `PLANILHA_ID` vazio).
2. Execute `testarOrcamentoJotak` e autorize. Confirme: linha nova na aba `Pedidos` (a célula `=TESTE` deve aparecer como texto) e e-mail recebido.
3. **Implantar > Nova implantação > App da Web**: executar como *você*; acesso *Qualquer pessoa*. Copie a URL `/exec`.
4. Em `site/index.html`, preencha `const ENDPOINT='<URL /exec>'`.
5. Proteções incluídas: campo-isca anti-robô, validação, limite 5/h por telefone e 20/min global, deduplicação por ID de envio, escape de fórmulas, gravação antes do e-mail. Limite diário do MailApp ~100 e-mails/dia (conta gratuita).
6. Ao alterar o código, crie **nova versão** da implantação.

## 2. Cloudflare Pages (projeto existente `jotak-impressos`)
Faça upload do **conteúdo** de `site/` (index.html + assets/), não da pasta. Não crie outro projeto. Confirme em https://jotak-impressos.pages.dev.

## 3. Domínio no Registro.br (checkpoint antes de alterar)
1. Exporte/anote **todos** os registros DNS atuais (MX, TXT etc.) e verifique se já existe `www`.
2. No Cloudflare Pages > projeto > Custom domains, adicione `www.jotakimpressos.com.br`.
3. No Registro.br (DNS mantido lá): CNAME `www` → `jotak-impressos.pages.dev`. Não mexa em MX/TXT.
4. Aguarde propagação e confira HTTPS. O domínio sem www (`jotakimpressos.com.br`) é tratado à parte: CNAME na raiz não é permitido no Registro.br; use redirecionamento para `www` ou migre o DNS para a Cloudflare (decisão sua, afeta e-mail).

## 4. Teste ponta a ponta
1. Celular e PC: menu, galeria/lightbox, botão WhatsApp.
2. Enviar pedido real → mensagem com protocolo, linha na planilha, e-mail recebido.
3. Reenviar o mesmo envio rápido → sem duplicar. Marcar/desmarcar consentimento → bloqueia.
4. Desligar rede/URL errada → site mostra erro e oferece WhatsApp.

## Pendências
Anexo de arte (não implementado), fotos reais, integração Gestão 360 (só com sua autorização/API), aviso de privacidade/LGPD completo em página própria (hoje há só o texto de consentimento no formulário).
