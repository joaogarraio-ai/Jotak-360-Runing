/**
 * JOTAK Impressos - receptor isolado de pedidos do site.
 * Não acessa o Gestão 360. Grava na planilha ANTES de enviar e-mail e só
 * confirma sucesso ({ok:true}) se a gravação funcionou.
 *
 * Escopos necessários (mínimos): planilhas (somente a configurada) e envio de e-mail.
 * Prefira criar o script VINCULADO à planilha (Extensões > Apps Script) e usar
 * getActiveSpreadsheet(); se usar ID, copie-o da URL da planilha.
 */
const EMAIL_JOTAK = 'jotakimpressos@gmail.com';
const PLANILHA_ID = ''; // vazio = usa a planilha à qual este script está vinculado
const ABA = 'Pedidos';
const LIMITE_POR_TELEFONE_HORA = 5;
const LIMITE_GLOBAL_MINUTO = 20;

function clean(v, max) { return String(v == null ? '' : v).replace(/[\u0000-\u001F]/g, ' ').trim().slice(0, max); }
// Evita injeção de fórmulas na planilha
function safe(v) { v = String(v); return /^[=+\-@\t\r]/.test(v) ? "'" + v : v; }
function json(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

function planilha() {
  const ss = PLANILHA_ID ? SpreadsheetApp.openById(PLANILHA_ID) : SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error('Planilha não configurada');
  return ss.getSheetByName(ABA) || ss.insertSheet(ABA);
}

function doGet() { return json({ ok: true, servico: 'JOTAK pedidos' }); }

function doPost(e) {
  let lock;
  try {
    const p = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (clean(p.website, 100)) return json({ ok: true, protocolo: 'JT-0' }); // honeypot: finge sucesso ao robô
    const d = {
      id: clean(p.id, 64), nome: clean(p.nome, 100), telefone: clean(p.telefone, 40), email: clean(p.email, 120),
      produto: clean(p.produto, 120), quantidade: clean(p.quantidade, 10), largura: clean(p.largura, 20),
      altura: clean(p.altura, 20), unidade: clean(p.unidade, 10), detalhes: clean(p.detalhes, 2000)
    };
    const digits = d.telefone.replace(/\D/g, '');
    if (!d.id || !d.nome || digits.length < 10 || digits.length > 13 || !d.produto || !(Number(d.quantidade) > 0))
      return json({ ok: false, erro: 'dados_invalidos' });
    if (d.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)) return json({ ok: false, erro: 'email_invalido' });

    lock = LockService.getScriptLock();
    lock.waitLock(15000);
    const cache = CacheService.getScriptCache();

    // Duplicado (mesmo envio repetido): devolve o protocolo já emitido
    const dup = cache.get('id:' + d.id);
    if (dup) return json({ ok: true, protocolo: dup, duplicado: true });

    // Limites de frequência
    const kMin = 'g:' + Utilities.formatDate(new Date(), 'UTC', 'yyyyMMddHHmm');
    const nMin = Number(cache.get(kMin) || 0);
    const kTel = 't:' + digits.slice(-11) + ':' + Utilities.formatDate(new Date(), 'UTC', 'yyyyMMddHH');
    const nTel = Number(cache.get(kTel) || 0);
    if (nMin >= LIMITE_GLOBAL_MINUTO || nTel >= LIMITE_POR_TELEFONE_HORA) return json({ ok: false, erro: 'muitas_tentativas' });
    cache.put(kMin, String(nMin + 1), 120);
    cache.put(kTel, String(nTel + 1), 4000);

    const protocolo = 'JT-' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd-HHmmss') + '-' + String(Math.floor(Math.random() * 1000)).padStart(3, '0');
    const labels = ['Protocolo', 'Nome', 'WhatsApp', 'E-mail', 'Produto', 'Quantidade', 'Largura', 'Altura', 'Unidade', 'Detalhes'];
    const values = [protocolo, d.nome, d.telefone, d.email, d.produto, d.quantidade, d.largura, d.altura, d.unidade, d.detalhes];

    // 1) grava (obrigatório)
    const sh = planilha();
    if (sh.getLastRow() === 0) sh.appendRow(['Data', 'ID envio', ...labels, 'Status']);
    sh.appendRow([new Date(), d.id, ...values.map(safe), 'Novo']);
    cache.put('id:' + d.id, protocolo, 21600);

    // 2) avisa por e-mail (falha aqui não perde o pedido)
    try {
      MailApp.sendEmail({
        to: EMAIL_JOTAK,
        subject: 'Novo pedido no site JOTAK - ' + protocolo,
        body: labels.map((n, i) => n + ': ' + values[i]).join('\n') + '\n\nOrigem: site JOTAK Impressos'
      });
    } catch (mailErr) { console.error('email falhou', mailErr); }

    return json({ ok: true, protocolo: protocolo });
  } catch (err) {
    console.error(err);
    return json({ ok: false, erro: 'falha_interna' });
  } finally {
    if (lock) lock.releaseLock();
  }
}

/** Teste manual no editor: grava uma linha de teste e envia e-mail. */
function testarOrcamentoJotak() {
  const r = doPost({ postData: { contents: JSON.stringify({ id: 'teste-' + Date.now(), nome: 'Teste', telefone: '(75) 99999-9999', produto: 'Banner / Lona', quantidade: '1', detalhes: '=TESTE' }) } });
  console.log(r.getContent());
}
