# Como usar (passo a passo, do zero)

## 1. Instalar o Python (uma vez só)
**Windows**
1. Abra https://www.python.org/downloads/ e clique em "Download Python".
2. Abra o arquivo baixado. NA PRIMEIRA TELA, marque a caixa **"Add python.exe to PATH"** e clique em "Install Now".
3. Para testar: aperte a tecla Windows, digite `cmd`, Enter. Digite `python --version` e Enter. Deve aparecer a versão.

**Mac**: o mesmo site, instale o pacote. Teste no app "Terminal" com `python3 --version`.
**Celular**: não dá para rodar. Use a planilha `afiliados_ml.xlsx` (funciona no celular).

## 2. Baixar o projeto
No GitHub, abra o repositório, troque o seletor de branch para `claude/serene-dirac-gnb3b8`,
clique em **Code → Download ZIP**, e extraia a pasta (botão direito → Extrair tudo).

## 3. Abrir o terminal dentro da pasta
Abra a pasta extraída, clique na barra de endereço no topo, digite `cmd` e Enter.
Vai abrir uma janela preta já dentro da pasta certa.

## 4. Rodar
- Painel de ganhos: `python -m afiliados_ml` e abra http://127.0.0.1:8000 no navegador.
- Buscar produtos: `python -m afiliados_ml buscar "organizador de gaveta"`
- Gerar post: `python -m afiliados_ml post MLB123456789 --link SEU_LINK`
- Vigiar preço: `python -m afiliados_ml vigiar MLB123456789 --alvo 79,90`
- Ver quedas: `python -m afiliados_ml checar`

## 5. Telegram (opcional)
1. No Telegram, converse com **@BotFather**, mande `/newbot`, escolha um nome e guarde o TOKEN.
2. Crie um canal e adicione o robô como **administrador**.
3. No terminal (Windows), antes de usar:
   ```
   set TELEGRAM_BOT_TOKEN=seu_token
   set TELEGRAM_CHAT_ID=@nome_do_seu_canal
   ```
4. Use `--telegram` nos comandos: `python -m afiliados_ml post MLB123 --link SEU_LINK --telegram`
