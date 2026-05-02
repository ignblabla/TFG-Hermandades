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
    def test_construye_correctamente_la_url_con_el_token(self, mock_settings, mock_post):
        """
        Test: Construye correctamente la URL con el token

        Given: Un token específico almacenado en la configuración.
        When: Se llama al servicio de envío.
        Then: La URL de destino debe seguir el formato oficial de Telegram incluyendo el bot token.
        """
        token_fake = "999999:TEST_TOKEN"
        mock_settings.TELEGRAM_BOT_TOKEN = token_fake
        
        TelegramWebhookService._enviar_bienvenida(1, "Hermano")

        url_llamada = mock_post.call_args[0][0]
        self.assertEqual(url_llamada, f"https://api.telegram.org/bot{token_fake}/sendMessage")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_construye_correctamente_el_payload_chat_id_y_texto(self, mock_settings, mock_post):
        """
        Test: Construye correctamente el payload (chat_id y texto)

        Given: Un ID de chat y un nombre de hermano.
        When: Se ejecuta el envío de bienvenida.
        Then: El diccionario 'json' enviado en el POST debe contener las claves chat_id y text.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        chat_id = 555
        
        TelegramWebhookService._enviar_bienvenida(chat_id, "Juan")

        kwargs = mock_post.call_args[1]
        payload = kwargs.get('json')
        
        self.assertEqual(payload['chat_id'], chat_id)
        self.assertIn("Tu cuenta de la Hermandad ha sido vinculada", payload['text'])



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_usa_timeout_5_en_la_peticion(self, mock_settings, mock_post):
        """
        Test: Usa timeout=5 en la petición

        Given: Una ejecución normal del servicio.
        When: Se realiza la llamada a requests.post.
        Then: El parámetro timeout debe ser estrictamente 5 para evitar bloqueos del hilo.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        TelegramWebhookService._enviar_bienvenida(1, "Hermano")

        kwargs = mock_post.call_args[1]
        self.assertEqual(kwargs.get('timeout'), 5)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_inserta_correctamente_el_nombre_del_hermano_en_el_mensaje(self, mock_settings, mock_post):
        """
        Test: Inserta correctamente el nombre del hermano en el mensaje

        Given: Un nombre de hermano específico "Andrés".
        When: Se genera el texto del mensaje.
        Then: El nombre debe aparecer dentro del saludo inicial del texto enviado.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        nombre = "Andrés"
        
        TelegramWebhookService._enviar_bienvenida(1, nombre)

        kwargs = mock_post.call_args[1]
        texto_enviado = kwargs.get('json').get('text')
        self.assertIn(f"¡Hola {nombre}!", texto_enviado)



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



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_token_vacio(self, mock_settings, mock_post):
        """
        Test: Token vacío

        Given: Un token configurado como un string vacío.
        When: Se valida la presencia del token.
        Then: Debido a la evaluación booleana (if not token), el servicio debe ignorar la petición.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = ""
        
        TelegramWebhookService._enviar_bienvenida(123, "Hermano")

        mock_post.assert_not_called()



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_error_en_requests_post(self, mock_settings, mock_post):
        """
        Test: Error en requests.post

        Given: Un token válido pero un fallo de red o tiempo de espera agotado.
        When: Se ejecuta requests.post.
        Then: La excepción debe propagarse (ya que el método no tiene un try/except interno), 
            permitiendo que el llamador (procesar_actualizacion) la capture.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "valid_token"
        mock_post.side_effect = Exception("Connection error")

        with self.assertRaises(Exception) as context:
            TelegramWebhookService._enviar_bienvenida(123, "Hermano")
        
        self.assertEqual(str(context.exception), "Connection error")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_chat_id_es_none(self, mock_settings, mock_post):
        """
        Test: chat_id es None

        Given: Un chat_id con valor None.
        When: Se construye el payload.
        Then: La petición debe realizarse con el valor None en el campo chat_id del JSON.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        TelegramWebhookService._enviar_bienvenida(None, "Hermano")

        kwargs = mock_post.call_args[1]
        self.assertIsNone(kwargs['json']['chat_id'])



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_nombre_hermano_es_none(self, mock_settings, mock_post):
        """
        Test: nombre_hermano es None

        Given: Un nombre de hermano nulo.
        When: Se interpola el nombre en el f-string del mensaje.
        Then: El mensaje debe contener el texto "None" (comportamiento por defecto de Python) sin romper la ejecución.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        TelegramWebhookService._enviar_bienvenida(123, None)

        kwargs = mock_post.call_args[1]
        texto = kwargs['json']['text']
        self.assertIn("¡Hola None!", texto)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_token_con_formato_inesperado(self, mock_settings, mock_post):
        """
        Test: Token con formato inesperado

        Given: Un token que contiene caracteres extraños o espacios.
        When: Se construye la URL.
        Then: El servicio debe intentar realizar la petición con la URL resultante, delegando la validación del formato a la API de Telegram.
        """
        token_extraño = "token con espacios y @#$%^"
        mock_settings.TELEGRAM_BOT_TOKEN = token_extraño
        
        TelegramWebhookService._enviar_bienvenida(1, "Hermano")

        url_llamada = mock_post.call_args[0][0]
        self.assertEqual(url_llamada, f"https://api.telegram.org/bot{token_extraño}/sendMessage")



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_verificar_no_se_llama_a_requests_si_no_hay_token(self, mock_settings, mock_post):
        """
        Test: Verificar que no se llama a requests.post si no hay token

        Given: Un entorno donde el token de Telegram es None.
        When: Se intenta ejecutar el envío.
        Then: La ejecución debe detenerse en el guard clause inicial y el mock de requests no debe registrar llamadas.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = None
        
        TelegramWebhookService._enviar_bienvenida(1, "Hermano")

        mock_post.assert_not_called()



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_verificar_url_se_construye_exactamente_una_vez(self, mock_settings, mock_post):
        """
        Test: Verificar que la URL se construye exactamente una vez

        Given: Una configuración de token válida.
        When: Se procesa el envío de bienvenida.
        Then: Se debe realizar exactamente una petición POST a la API de Telegram.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        
        TelegramWebhookService._enviar_bienvenida(1, "Hermano")

        self.assertEqual(mock_post.call_count, 1)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_payload_con_caracteres_especiales_en_el_nombre(self, mock_settings, mock_post):
        """
        Test: Payload con caracteres especiales en el nombre

        Given: Un nombre de hermano con tildes, emojis o caracteres de escape ("José María 🌟").
        When: Se inserta en el f-string del payload.
        Then: El texto del mensaje debe contener el nombre íntegro y correctamente formateado.
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        nombre_complejo = "José María 🌟"
        
        TelegramWebhookService._enviar_bienvenida(1, nombre_complejo)

        kwargs = mock_post.call_args[1]
        texto = kwargs['json']['text']
        self.assertIn(f"¡Hola {nombre_complejo}!", texto)



    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.requests.post')
    @patch('api.servicios.papeleta_sitio.papeleta_telegram_service.settings')
    def test_verificar_no_se_retorna_nada(self, mock_settings, mock_post):
        """
        Test: Verificar que no se retorna nada (return implícito None)

        Given: Una ejecución exitosa del método.
        When: Finaliza la lógica de envío.
        Then: El resultado de la función debe ser estrictamente None, confirmando que es un método de "disparar y olvidar".
        """
        mock_settings.TELEGRAM_BOT_TOKEN = "token"
        
        resultado = TelegramWebhookService._enviar_bienvenida(1, "Hermano")

        self.assertIsNone(resultado)