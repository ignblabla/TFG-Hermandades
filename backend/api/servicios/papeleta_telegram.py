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



    @staticmethod
    def notificar_papeleta_asignada(chat_id, nombre_hermano, nombre_acto, estado, nombre_puesto=None):
        """
        Envía un mensaje al hermano informándole del resultado del reparto.
        """
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://mi-web-frontend.onrender.com') 
        
        if not token or not chat_id:
            return
            
        url_papeletas = f"{frontend_url}/mis-papeletas-de-sitio"
        
        if estado == "ASIGNADA":
            mensaje = (
                f"🕊️ <b>¡Notificación de Reparto!</b>\n\n"
                f"Estimado/a {nombre_hermano},\n\n"
                f"El algoritmo de reparto para <b>{nombre_acto}</b> ha finalizado.\n"
                f"✅ Se le ha asignado el puesto: <b>{nombre_puesto}</b>.\n\n"
                f"Puede consultar y descargar su papeleta de sitio desde su perfil:\n"
                # f"<a href='{url_papeletas}'>➡️ Ver mis papeletas</a>"
                f"🔗 <i>Enlace para copiar en pruebas: {url_papeletas}</i>"
            )
        else:
            mensaje = (
                f"🕊️ <b>¡Notificación de Reparto!</b>\n\n"
                f"Estimado/a {nombre_hermano},\n\n"
                f"El algoritmo de reparto para <b>{nombre_acto}</b> ha finalizado.\n"
                f"❌ Lamentablemente, no ha sido posible asignarle ninguno de los puestos solicitados por criterio de antigüedad o disponibilidad.\n\n"
                f"Puede consultar el estado de su solicitud desde su perfil:\n"
                # f"<a href='{url_papeletas}'>➡️ Ver mis papeletas</a>"
                f"🔗 <i>Enlace para copiar en pruebas: {url_papeletas}</i>"
            )
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error enviando notificación de papeleta a {chat_id}: {e}")