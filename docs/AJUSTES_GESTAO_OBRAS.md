# Ajustes do sistema Gestão de Obras (para enviar ao GPT)

Envie em ETAPAS. Só passe para a próxima depois de conferir a anterior.

---------------------------------------------------------------------
## ETAPA 1 — Erros e regras de pagamento (copie tudo abaixo)
---------------------------------------------------------------------

Corrija o sistema "Gestão de Obras" sem remover nenhuma função existente. Ao final, entregue o sistema completo e a lista do que mudou.

### A) Erros a corrigir

1. Valor com ponto vira 100x maior ("12.50" é salvo como 1250). Use UMA função para todos os campos de dinheiro (despesa, diária, parcela, adiantamento):

```js
function parseMoney(v){
  let s = String(v ?? '').trim().replace(/[^\d.,-]/g, '');
  if (!s) return NaN;
  const lastC = s.lastIndexOf(','), lastP = s.lastIndexOf('.');
  if (lastC > -1 && lastP > -1) {            // 1.250,50  ou  1,250.50
    const dec = lastC > lastP ? ',' : '.';
    s = dec === ',' ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
  } else if (lastC > -1) {                   // 12,50  ou  1,250
    s = /,\d{1,2}$/.test(s) ? s.replace(',', '.') : s.replace(/,/g, '');
  } else if (lastP > -1) {                   // 12.50  ou  1.250
    if (!/\.\d{1,2}$/.test(s)) s = s.replace(/\./g, '');
  }
  return Math.round(parseFloat(s) * 100) / 100;
}
// Testes: "12.50"→12.5  "12,50"→12.5  "1.250,50"→1250.5  "1,250.50"→1250.5  "1.250"→1250  "150"→150
```
Guarde dinheiro em CENTAVOS (inteiro) para evitar erro de arredondamento.

2. Pagamento em duplicidade. Um trabalhador só pode ter UM lançamento por turno (manhã ou tarde) por dia, em UMA obra. Ao marcar em outra obra, avise em qual obra ele já está e pergunte se quer transferir:

```js
function existeTurno(trabalhadorId, data, turno, obraIdAtual){
  return lancamentos.find(l => l.trabalhadorId===trabalhadorId && l.data===data
         && l.turno===turno && l.obraId!==obraIdAtual);
}
```

3. Mudar a diária NÃO pode alterar períodos já lançados ou pagos. Grave no próprio lançamento o `valorDiaria` e a `funcao` do momento da criação, e calcule os totais usando esses valores gravados (nunca o valor atual do cadastro). Ao editar o cadastro, pergunte se quer aplicar aos lançamentos ainda NÃO pagos do período atual.

4. Excluir trabalhador/obra faz os lançamentos sumirem dos totais. Troque por "Inativar". Inativos não aparecem para novos lançamentos, mas continuam nos relatórios. Só permita excluir de verdade se não houver nenhum lançamento.

5. O botão "Pago" vale para o período inteiro mesmo com filtro de obra. Faça a baixa por lançamento (trabalhador + obra + período), com data, forma de pagamento, observação e usuário.

6. Despesas precisam de situação: "A pagar", "Pago" e "Reembolsar". Inclua despesas no "Pendente de pagamento" do Fechamento e do Financeiro, não só mão de obra.

7. RDO: criar RDO em data que já existe sobrescreve sem avisar. Avise e abra o existente. A numeração do RDO deve ser gravada na criação (não recalculada). Permita remover uma foto isolada.

### B) Ciclo de pagamento e forma de remuneração (configuráveis)

IGNORE qualquer regra de "período fixo de 10 dias". O período é configuração de cada trabalhador.

**Ciclo de pagamento**
- Opções: Semanal (segunda a domingo); A cada 10 dias (1–10, 11–20, 21–fim do mês); Quinzenal (1–15 e 16–fim do mês); Mensal; Personalizado (a cada N dias a partir de uma data de início).
- Existe um ciclo PADRÃO da empresa (tela Configurações, só Administrador). Cada trabalhador usa o padrão ou tem o seu próprio no cadastro.
- Mudar o ciclo vale só para períodos futuros. Períodos fechados ou pagos não mudam.

```js
function periodoDe(data, ciclo, inicioPersonalizado){
  const d = new Date(data+'T12:00'), y=d.getFullYear(), m=d.getMonth(), dia=d.getDate();
  const iso = x => x.toISOString().slice(0,10);
  const fimMes = new Date(y,m+1,0).getDate();
  if (ciclo.tipo==='10dias'){ const a=dia<=10?1:dia<=20?11:21, b=dia<=10?10:dia<=20?20:fimMes;
      return {ini:iso(new Date(y,m,a,12)), fim:iso(new Date(y,m,b,12))}; }
  if (ciclo.tipo==='quinzenal'){ const a=dia<=15?1:16, b=dia<=15?15:fimMes;
      return {ini:iso(new Date(y,m,a,12)), fim:iso(new Date(y,m,b,12))}; }
  if (ciclo.tipo==='mensal') return {ini:iso(new Date(y,m,1,12)), fim:iso(new Date(y,m,fimMes,12))};
  if (ciclo.tipo==='semanal'){ const seg=new Date(d); seg.setDate(dia-((d.getDay()+6)%7));
      const dom=new Date(seg); dom.setDate(seg.getDate()+6); return {ini:iso(seg), fim:iso(dom)}; }
  // personalizado: a cada ciclo.dias a partir de inicioPersonalizado
  const base=new Date(inicioPersonalizado+'T12:00'), n=Math.floor((d-base)/864e5/ciclo.dias);
  const ini=new Date(base); ini.setDate(base.getDate()+n*ciclo.dias);
  const fim=new Date(ini); fim.setDate(ini.getDate()+ciclo.dias-1);
  return {ini:iso(ini), fim:iso(fim)};
}
```

**Forma de remuneração** (por trabalhador e por contrato)
- DIÁRIA: manhã = 1/2, tarde = 1/2, dia completo = 1. Valor gravado em cada lançamento.
- EMPREITA: contrato com trabalhador, obra, descrição, valor total, início e previsão de término. Pagamentos em parcelas/medições (data, valor, % executado, observação). Mostrar sempre: total contratado, total pago, saldo e % pago. Avisar se a soma das parcelas passar do contrato. Não depende do ciclo: cada parcela entra no Financeiro na data lançada.
- POR METRO/UNIDADE: serviço, unidade (m², m, un), valor unitário, quantidade medida por lançamento.
- O mesmo trabalhador pode ter diária numa obra e empreita em outra.

**Telas**
- Fechamento e Financeiro agrupam por ciclo (ex.: "Quinzenal 16/10 a 31/10" e "10 dias 21/10 a 31/10"), cada grupo com seus totais (a pagar, pago, pendente) e navegação própria.
- "Fechar período" funciona por ciclo e trava os lançamentos daquele período. Só o Administrador reabre, com motivo.
- Recibo e lista de assinaturas por trabalhador e período.

### C) Testes obrigatórios (me diga o resultado de cada um)
- Digitar 12.50, 12,50 e 1.250,50 em despesa e diária.
- Lançar o mesmo trabalhador no mesmo turno em duas obras (deve bloquear/avisar).
- Mudar a diária e conferir que o período antigo não mudou.
- Inativar um trabalhador com lançamentos e conferir que o histórico continua.
- Dar baixa num lançamento de uma obra e conferir que os da outra continuam "A pagar".
- Criar dois RDOs na mesma data (deve avisar).
- 3 trabalhadores com ciclos diferentes (semanal, 10 dias, quinzenal) lançados nos mesmos dias: cada um no seu período.
- Empreita de R$ 10.000: pagar 30%, 30%, 20% e conferir saldo de R$ 2.000. Tentar parcela de R$ 3.000 e ver o aviso.

---------------------------------------------------------------------
## ETAPA 2 — Login e banco de dados online
---------------------------------------------------------------------

- Login com e-mail e senha. Perfis: Administrador (tudo); Encarregado (lança diárias, despesas e RDO só das obras dele; NÃO vê valor da diária dos outros nem chave PIX); Financeiro (vê e dá baixa; não edita diárias).
- Dados num banco online compartilhado (Supabase ou Firebase), não no navegador.
- REGRAS DE ACESSO no banco (Row Level Security no Supabase / Security Rules no Firebase) que respeitem os perfis. Esconder o botão na tela NÃO basta: o banco precisa recusar a leitura.
- Nenhuma chave secreta no código do navegador (só a chave pública/anon). Me mostre onde as chaves ficam.
- Fotos de notas e RDO no armazenamento de arquivos (storage), reduzidas a no máximo 1600 px.
- Registro de quem criou/alterou cada lançamento, com data e hora. Alterar ou excluir lançamento pago exige motivo.
- Exportar tudo (JSON) e importar, com resumo e confirmação.

---------------------------------------------------------------------
## ETAPA 3 — RDO, recibos e exportações
---------------------------------------------------------------------

- RDO completo: obra, data, número, clima manhã/tarde, condição do terreno, equipe presente (das diárias do dia), equipamentos e materiais, serviços executados, ocorrências, fotos, responsável. Alerta de dias úteis sem RDO por obra. PDF com fotos e campo de assinatura; PDF de vários RDOs do período.
- Recibo do trabalhador em PDF (nome, obra, período, dias, valor, forma de pagamento, assinatura) e lista de assinaturas do período.
- Anexar comprovante PIX na baixa.
- Exportação do financeiro em .xlsx ou .csv de verdade (não HTML renomeado), uma linha por pagamento: favorecido, CPF, forma, chave PIX, obra, período, valor, situação.
- Cadastro do trabalhador com CPF, telefone, tipo de chave PIX e validação; avisar PIX sem chave no Financeiro.
- Faltas, horas extras (percentual configurável), adiantamentos, vales e descontos abatidos no líquido a pagar.

---------------------------------------------------------------------
## ETAPA 4 — Orçamento, notas e uso offline
---------------------------------------------------------------------

- Orçamento por obra (mão de obra e materiais) x gasto real, com alerta em 80% e 100%.
- Leitura de QR/código e de XML/HTML de nota: preencher fornecedor, CNPJ, número, data e valor para conferência; avisar nota repetida pela chave de acesso.
- Uso offline no celular: salvar localmente e sincronizar depois, mostrando o que está pendente.
- Busca e filtros em todas as telas (obra, trabalhador, período, situação).
