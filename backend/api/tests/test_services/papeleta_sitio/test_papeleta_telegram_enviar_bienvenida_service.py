from unittest import TestCase
from unittest.mock import patch
from api.servicios.papeleta_sitio.papeleta_telegram_service import TelegramWebhookService

class TestEnviarBienvenida(TestCase):

    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_envia_correctamente_el_mensaje_cuando_hay_token(self, mock_settings, mock_post):
        """
        Test: Envía correctamente el mensaje cuando hay token

        Given: Un token de bot de Telegram configurado en los settings de Django.
        When: Se invoca el método _enviar_bienvenida con un chat_id y el nombre del hermano.
        Then: Se debe construir la URL correctamente y realizar una petición POST con el payload esperado y un timeout de 5 segundos.
        """
        chat_id_destino = 987654321
        nombre_prueba = "Alfonso"
        token_simulado = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

        mock_settings.TELEGRAM_BOT_TOKEN = token_simulado

        url_esperada = f"https://api.telegram.org/bot{token_simulado}/sendMessage"
        payload_esperado = {
            "chat_id": chat_id_destino,
            "text": f"✅ ¡Hola {nombre_prueba}! Tu cuenta de la Hermandad ha sido vinculada correctamente a Telegram. A partir de ahora recibirás aquí los comunicados."
        }

        TelegramWebhookService._enviar_bienvenida(chat_id_destino, nombre_prueba)

        mock_post.assert_called_once_with(
            url_esperada, 
            json=payload_esperado, 
            timeout=5
        )



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_no_hay_token_en_settings(self, mock_settings, mock_post):
        """
        Test: No hay token en settings

        Given: Un entorno donde TELEGRAM_BOT_TOKEN no está definido (None).
        When: Se intenta enviar la bienvenida.
        Then: El servicio debe retornar prematuramente y no intentar realizar ninguna petición HTTP.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = None
        
        TelegramWebhookService._enviar_bienvenida(123, "Hermano")

        mock_post.assert_not_called()