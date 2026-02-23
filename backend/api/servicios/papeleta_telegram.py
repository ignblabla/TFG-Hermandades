from django.core.signing import Signer, BadSignature
from django.contrib.auth import get_user_model
import requests
from django.conf import settings

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

            # Si el mensaje empieza por '/start ' significa que viene del Deep Link
            if text.startswith('/start '):
                # Extraemos el token que va después del espacio
                token = text.split(' ')[1] 
                
                signer = Signer()
                try:
                    # Desciframos el ID del hermano
                    user_id = signer.unsign(token)
                    hermano = User.objects.get(id=user_id)
                    
                    # Guardamos el chat_id
                    hermano.telegram_chat_id = str(chat_id)
                    hermano.save()

                    # Opcional: Enviarle un mensaje dándole la bienvenida
                    TelegramWebhookService._enviar_bienvenida(chat_id, hermano.nombre)
                    
                except (BadSignature, User.DoesNotExist):
                    # El token ha sido manipulado o el usuario no existe
                    print(f"Intento de vinculación fallido con token: {token}")
                    
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