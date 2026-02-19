import requests
from django.conf import settings

def enviar_mensaje_telegram(channel_id, titulo, contenido):
    token = settings.TELEGRAM_BOT_TOKEN

    mensaje = f"<b>📢 {titulo}</b>\n\n{contenido[:200]}..."
    if len(contenido) > 200:
        mensaje += "\n\n<i>(Leer más en la web)</i>"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": mensaje,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")