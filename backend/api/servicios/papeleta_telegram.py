from django.core.signing import Signer, BadSignature
from django.contrib.auth import get_user_model
import requests
from django.conf import settings
import base64

User = get_user_model()

class TelegramWebhookService:
    @staticmethod
    def procesar_actualizacion(data):
        """
        Recibe el JSON del webhook de Telegram y busca el comando /start
        """
        try:
            message = data.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')

            if text.startswith('/start '):
                token_limpio = text.split(' ')[1] 
                
                padding = 4 - (len(token_limpio) % 4)
                token_base64 = token_limpio + ("=" * padding)
                
                signer = Signer()
                try:
                    token_decodificado = base64.urlsafe_b64decode(token_base64.encode()).decode()

                    user_id = signer.unsign(token_decodificado)
                    hermano = User.objects.get(id=user_id)

                    hermano.telegram_chat_id = str(chat_id)
                    hermano.save()

                    TelegramWebhookService._enviar_bienvenida(chat_id, hermano.nombre)
                    
                except (BadSignature, User.DoesNotExist, ValueError) as e:
                    print(f"Intento de vinculación fallido. Error: {e}")
                    
        except Exception as e:
            print(f"Error procesando webhook de Telegram: {e}")

    @staticmethod
    def _enviar_bienvenida(chat_id, nombre_hermano):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token:
            return
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"✅ ¡Hola {nombre_hermano}! Tu cuenta de la Hermandad ha sido vinculada correctamente a Telegram. A partir de ahora recibirás aquí los comunicados."
        }
        requests.post(url, json=payload, timeout=5)