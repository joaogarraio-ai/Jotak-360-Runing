"""Envio de mensagens por um robô do Telegram.

Configuração (variáveis de ambiente):
  TELEGRAM_BOT_TOKEN  token que o @BotFather te dá ao criar o robô
  TELEGRAM_CHAT_ID    @nome_do_canal (o robô precisa ser admin do canal) ou o id numérico do chat
"""
import json
import os
import urllib.error
import urllib.request


class ErroTelegram(Exception):
    pass


def _enviar(token: str, chat_id: str, texto: str) -> None:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": texto, "disable_web_page_preview": False}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except urllib.error.HTTPError as ex:
        raise ErroTelegram(f"Telegram respondeu {ex.code}: confira o token e se o robô é admin do canal") from ex
    except urllib.error.URLError as ex:
        raise ErroTelegram(f"sem conexão com o Telegram: {ex.reason}") from ex


def enviar(texto: str, chat_id: str | None = None, enviar_fn=_enviar) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        raise ErroTelegram("defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID (ou use --chat)")
    for i in range(0, len(texto), 4000):  # limite do Telegram: 4096 caracteres
        enviar_fn(token, chat, texto[i:i + 4000])
